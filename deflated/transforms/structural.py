"""
T2 structural transforms: shorter equivalent statements and expressions, so all of them are semantics-preserving.

No pass changes the inside of a string or char literal. Comments are only changed by `RemoveComments`, which deletes
the auto-generated ones. The passes work on the segments from `scan`, the statements from `split_statements` or the
tokens from `ctokenize`, which all keep literals and comments whole. The passes have no type information, so a pass
skips any rewrite it cannot prove safe. A missed rewrite only costs size; a wrong one changes the program.
"""

from __future__ import annotations

import re
from bisect import bisect_left
from collections import Counter, defaultdict
from itertools import accumulate, groupby
from typing import DefaultDict, List, NamedTuple, Optional, Set, Tuple

from .base import Tier, Transform
from .ctokens import (
    CINT,
    CLOSER_FOR,
    CTRL_KW,
    IDENT,
    NONVALUE_KW,
    OPENER_FOR,
    STMT_KW,
    CToken,
    apply_edits,
    ctokenize,
    first_top_level,
    has_top_level_token,
    is_value_before,
    iter_depth,
    match_delimiter,
    match_delimiter_backward,
    split_statements,
    token_texts,
    top_level_indices,
)
from .lexer import SegmentType, iter_code_matches, map_code, scan, strip_comments

# The assignment operators: a side effect wherever they appear.
_ASSIGN_OPS = frozenset({"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="})

# Words that only name a type, so a `(...)` group holding one is a cast.
_TYPE_WORDS = frozenset(
    "int char long short void unsigned signed float double bool "
    "uint ulong ushort uchar byte sbyte undefined "
    "size_t wchar_t".split()
)

# One leading goto label such as `LABEL_3:` (not C++ `::`); group 1 is its name.
_LABEL_PREFIX = re.compile(r"\s*(?P<label>[A-Za-z_]\w*)\s*:(?!:)\s*")


def _is_cast(group_texts: List[str]) -> bool:
    """
    True if the token texts `group_texts` inside a `(...)` can only be a type: names followed by `*`s, with a known type
    word or at least one `*` (`(int)`, `(undefined4 *)`). `(x)` may be a variable and `(x * y)` is an expression, so
    neither counts.
    """
    name_count = 0
    while name_count < len(group_texts) and IDENT.fullmatch(group_texts[name_count]):
        name_count += 1
    stars = group_texts[name_count:]
    if name_count == 0 or any(text != "*" for text in stars):
        return False
    return bool(stars) or any(text in _TYPE_WORDS for text in group_texts)


def _split_leading_labels(statement: str) -> Tuple[str, str]:
    """
    Split `statement` into its leading `label:` prefixes and the rest: `"L1: L2: x = 1;"` -> `("L1: L2: ", "x = 1;")`.

    `case` and `default` labels stay attached, so a `switch` body is never split.
    """
    prefix_length = 0
    while (label_match := _LABEL_PREFIX.match(statement, prefix_length)) is not None and label_match.group(
        "label"
    ) not in (
        "case",
        "default",
    ):
        prefix_length = label_match.end()
    return statement[:prefix_length], statement[prefix_length:]


class NormalizeFlagTemps(Transform):
    """
    Rename Binary Ninja's flag temporaries from `cond:N` to `condN` (also `cond:12_1` -> `cond12_1`), in code only.

    The `:` is not legal C, and a statement starting with `cond:1 = ...` looks like the goto label `cond:` to
    `cfg-canon`, which would drop it. The pass runs first, so no later pass sees the colon. At T3 `compress-names`
    shortens `condN` like any other flag temporary.
    """

    id = "flag-temps"
    tier = Tier.T2_STRUCTURAL
    description = "Normalize Binary Ninja colon-flag temporaries into plain identifiers."

    _FLAG_TEMP = re.compile(r"\bcond:(\d+(?:_\d+)?)")

    def apply(self, code: str) -> str:
        """Return `code` with every `cond:N` in code renamed to `condN`."""
        return map_code(code, lambda text: self._FLAG_TEMP.sub(r"cond\1", text))


class RemoveComments(Transform):
    """
    Remove auto-generated comments, but keep decompiler warning banners.

    Address comments (`/* 0x4011a0 */`) and Hex-Rays' storage-location notes (`// rax`, `// [rsp+8h]`, `BYREF`) say
    nothing about what the program does, so removing them is lossless for our tasks (they would still help binary
    diffing or ABI recovery). Warning banners (`/* WARNING: Could not recover jumptable... */`) say the decompilation
    is unreliable, so they stay until `RemoveWarningComments` at T4.
    """

    id = "comments"
    tier = Tier.T2_STRUCTURAL
    description = "Remove auto-generated address and storage-location comments, keeping warning banners."

    def apply(self, code: str) -> str:
        """Return `code` without its auto-generated comments."""
        return strip_comments(code, keep_warnings=True)


class CoalesceDeclarations(Transform):
    """
    Merge the uninitialized declarations of one type in a run of declarations into one statement per type.

    The same type need not be adjacent: `int iVar1; ulong uVar2, uVar3; int iVar4;` -> `int iVar1, iVar4; ulong uVar2,
    uVar3;`. Only plain declarators (`*`s and a name) are merged: without an initializer, their order does not matter.
    Initialized declarations (`int x = f();`), arrays and function pointers are left alone.
    """

    id = "decl-coalesce"
    tier = Tier.T2_STRUCTURAL
    description = "Merge same-type uninitialized declarations into one statement."

    # A mergeable declaration: a type, a comma list of declarators (`*`s and a name), then `;`. The `;` anchors the
    # last declarator, so the lazy type takes multi-word types (`unsigned int`). `=`, `[` and `(` never match, so
    # initializers, arrays and function pointers are excluded.
    _DECL = re.compile(
        r"^(?P<lead>\s*)"
        r"(?P<type>[A-Za-z_][A-Za-z0-9_ ]*?)[ \t]+"
        r"(?P<decls>\**\s*[A-Za-z_]\w*(?:[ \t]*,[ \t]*\**\s*[A-Za-z_]\w*)*)"
        r"[ \t]*;[ \t]*$"
    )

    # First words that start a statement, not a type.
    _NON_TYPES = NONVALUE_KW

    def _match_decl(self, piece: str) -> Optional[re.Match]:
        """Return the match if `piece` is a mergeable declaration whose first word is not a keyword, else None."""
        decl_match = self._DECL.match(piece)
        if decl_match and decl_match.group("type").split()[0] in self._NON_TYPES:
            return None
        return decl_match

    def apply(self, code: str) -> str:
        """Return `code` with every run of declarations merged into one statement per type."""
        pieces = split_statements(code)
        decl_matches = [self._match_decl(piece) for piece in pieces]
        transformed_pieces: List[str] = []
        for is_decl_run, group in groupby(zip(pieces, decl_matches), key=lambda pair: pair[1] is not None):
            run_pieces, run_matches = zip(*group)
            if is_decl_run:
                transformed_pieces.append(self._consolidate(list(run_matches), list(run_pieces)))
            else:
                transformed_pieces.extend(run_pieces)
        return "".join(transformed_pieces)

    @staticmethod
    def _consolidate(run_matches: List[re.Match], original_declarations: List[str]) -> str:
        """
        Return the declarations of `run` merged into one statement per type, or `originals` unchanged if no two of them
        share a type.
        """
        declarators_by_type: DefaultDict[str, List[str]] = defaultdict(list)
        for decl_match in run_matches:
            type_name = re.sub(r"\s+", " ", decl_match.group("type").strip())
            declarators = [re.sub(r"\s+", "", declarator) for declarator in decl_match.group("decls").split(",")]
            declarators_by_type[type_name].extend(declarators)
        if len(declarators_by_type) == len(run_matches):  # nothing merges; leave the run verbatim
            return "".join(original_declarations)
        indent = run_matches[0].group("lead")
        separator = indent if "\n" in indent else " "
        merged = [f"{type_name} {', '.join(declarators)};" for type_name, declarators in declarators_by_type.items()]
        return indent + separator.join(merged)


class DropSingleStatementBraces(Transform):
    """
    Remove the braces of a control block that holds one simple statement: `if (c) { x = 1; }` -> `if (c) x = 1;`.

    Works for `if`, `else`, `for`, `while` and `do`.
    These blocks keep their braces:
        * Other blocks: function, struct and enum bodies, initializers, plain scope blocks and `switch` bodies.
        * A body that starts with a control keyword: in `if (a) { if (b) f(); } else g();` the `else` would move to the
          inner `if`.
        * A body that is a declaration: `if (c) int x;` is not valid C. Without types, `a * b;` may declare `b`, so it
          counts as one too.
        * A body with braces in it, such as a compound literal `x = (T){1};`.

    Strippable blocks never contain braces, so all pairs from one scan are disjoint and are removed right to left in
    a single pass.
    """

    id = "brace-elision"
    tier = Tier.T2_STRUCTURAL
    description = "Drop braces around a single-statement control block (if/else/for/while/do)."

    def apply(self, code: str) -> str:
        """
        Return `code` with the braces of every strippable control block replaced by spaces. One pass is enough:
        unwrapping an inner block never makes the outer one strippable, since the outer body then starts with a control
        keyword.
        """
        for open_offset, close_offset in sorted(self._strippable_pairs(code), reverse=True):
            # Replace each brace with a space so its neighbours cannot merge: `else{x` must not become `elsex`.
            code = code[:open_offset] + " " + code[open_offset + 1 : close_offset] + " " + code[close_offset + 1 :]
        return code

    def _strippable_pairs(self, code: str) -> List[Tuple[int, int]]:
        """
        Return the offsets of the `{` and `}` of every control block that holds one simple statement.

        Braces are matched on the C tokens, so a brace in a string or comment is ignored and `_is_control_block` can
        look back past whitespace and comments (`if (c) /* x */ {`). Pairs are listed in the order of their `}`.
        """
        # A comment is one opaque token; drop it so the token before a `{` is the code in front of it.
        tokens = [token for token in ctokenize(code) if not token.text.startswith(("//", "/*"))]
        open_indices: List[int] = []
        pairs: List[Tuple[int, int]] = []
        for index, token in enumerate(tokens):
            if token.text == "{":
                open_indices.append(index)
            elif token.text == "}" and open_indices:
                open_index = open_indices.pop()
                if not self._is_control_block(tokens, open_index):
                    continue
                if self._single_simple(tokens[open_index + 1 : index]):
                    pairs.append((tokens[open_index].start, token.start))
        return pairs

    @staticmethod
    def _is_control_block(tokens: List[CToken], brace_index: int) -> bool:
        """True if the `{` at `tokens[brace_index]` opens a control block."""
        if brace_index == 0:
            return False
        before = tokens[brace_index - 1].text
        if before == ")":
            paren_index = match_delimiter_backward(tokens, brace_index - 1)
            if paren_index is None or paren_index == 0:
                return False
            # `switch` is left out: a body with a `case` label needs its braces (`switch(x)case 1:...` is invalid C)
            return tokens[paren_index - 1].text in {"if", "for", "while"}
        return before in {"else", "do"}

    def _single_simple(self, body: List[CToken]) -> bool:
        """True if the tokens `body` are one statement that is neither a control statement nor a declaration."""
        texts = [token.text for token in body]
        # Braces mean a nested block or a brace expression (`(T){1}`); skip rather than reason about them.
        if not texts or texts[-1] != ";" or "{" in texts or "}" in texts:
            return False
        if has_top_level_token(body, 0, len(body) - 1, frozenset({";"})):
            return False  # more than one statement
        # Skip leading goto labels (`L: if (b) ...;`), or a labeled inner `if` would pass the dangling-else check.
        first = 0
        while (
            IDENT.fullmatch(texts[first])
            and texts[first] not in ("case", "default")
            and texts[first + 1] == ":"
            and texts[first + 2] != ":"  # not C++ `::`
        ):
            first += 2
        if texts[first] in CTRL_KW:
            return False
        # `if (c) int x;` is not valid C.
        return texts[first] in STMT_KW or not self._looks_like_declaration(texts[first:])

    def _looks_like_declaration(self, texts: List[str]) -> bool:
        """
        True if the statement `texts` may be a declaration: a type, any `*` or `&`, then a name (`int x, y;`) or a
        pointer in parentheses (`int (*fp)(int);`). The type may have `ns::` parts, `<...>` arguments, or one `(...)`
        right after its first word (`typeof(x) y;`).

        Without types, `a * b;` also reads as a declaration; that only keeps braces that could have gone.
        """
        if not IDENT.fullmatch(texts[0]):
            return False
        index = 1
        while index is not None:
            if texts[index : index + 2] == [":", ":"] and IDENT.fullmatch(texts[index + 2]):
                index += 3
            elif texts[index] == "<" or (index == 1 and texts[index] == "(" and texts[index + 1] != "*"):
                index = self._skip_group(texts, index)
            else:
                break
        if index is None:
            return False  # `a < b;` is a comparison
        while texts[index] in ("*", "&"):
            index += 1
        if texts[index : index + 2] != ["(", "*"]:
            return bool(IDENT.fullmatch(texts[index]))
        # `(*name)(` or `(*name)[`; `f(*p);` is a call.
        index += 2
        while texts[index] == "*":
            index += 1
        return bool(IDENT.fullmatch(texts[index])) and texts[index + 1 : index + 3] in ([")", "("], [")", "["])

    @staticmethod
    def _skip_group(texts: List[str], index: int) -> Optional[int]:
        """Return the index after the `>` or `)` that closes the `<` or `(` at `texts[index]`, or None if none does."""
        depth_change = {"<": 1, ">": -1, ">>": -2} if texts[index] == "<" else {"(": 1, ")": -1}
        depth = 0
        for close in range(index, len(texts)):
            depth += depth_change.get(texts[close], 0)
            if depth <= 0:
                return close + 1
        return None


class CompoundAssignment(Transform):
    """
    Fold `a = a OP b;` into `a OP= b;` (`iVar1 = iVar1 + iVar4;` -> `iVar1 += iVar4;`).

    The right side must start with exactly the tokens of the target, so `a->b` or `a + +b` is never read as `a`
    followed by an operator. The target is evaluated once instead of twice, so it may not contain `++`, `--`, an
    assignment or a call: `*(int *)(p + i * 4)` folds, `*p++` and `a[i += 1]` do not. The rest of the right side must
    bind tighter than OP (see `_remainder_safe`), since the fold regroups it.
    """

    id = "compound-assign"
    tier = Tier.T2_STRUCTURAL
    description = "Fold an expanded assignment into compound form."

    # Binary operators with a compound-assignment form (`a = a OP b` -> `a OP= b`).
    _COMPOUND_OPS = frozenset({"+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>"})

    # C precedence levels (smaller binds tighter); levels 1-2 (postfix/unary) are omitted, see `_remainder_safe`.
    _PRECEDENCE = {
        "*": 3,
        "/": 3,
        "%": 3,
        "+": 4,
        "-": 4,
        "<<": 5,
        ">>": 5,
        "<": 6,
        "<=": 6,
        ">": 6,
        ">=": 6,
        "==": 7,
        "!=": 7,
        "&": 8,
        "^": 9,
        "|": 10,
        "&&": 11,
        "||": 12,
        "?": 13,
        ":": 13,
        ",": 14,
    }

    # Operators that may repeat in a folded chain `a = a OP b OP c`: associative for every type. `+` and `*` are not,
    # since float rounding depends on grouping and the pass cannot tell a float from an int.
    _ASSOCIATIVE_OPS = frozenset({"&", "|", "^"})

    # Operators that may stand in front of an operand.
    _PREFIX_OPS = frozenset({"-", "+", "*", "&", "!", "~", "++", "--"})

    def apply(self, code: str) -> str:
        """Return `code` with every foldable `a = a OP b;` written as `a OP= b;`."""
        code = self._fold_for_increments(code)
        return "".join(self._rewrite(piece) for piece in split_statements(code))

    def _rewrite(self, piece: str) -> str:
        """Return `piece` in compound form if it is a foldable `a = a OP b;`, else unchanged."""
        statement_match = re.fullmatch(r"(\s*)(.*);(\s*)", piece, re.DOTALL)
        if statement_match is None:
            return piece
        indent, statement, trailing = statement_match.groups()
        folded = self._fold(statement)
        return piece if folded is None else f"{indent}{folded};{trailing}"

    def _fold_for_increments(self, code: str) -> str:
        """
        Return `code` with the increment of every `for` header folded: `for (i = 0; i < n; i = i + 1)` ->
        `for (i = 0; i < n; i += 1)`. `split_statements` does not split inside `(...)`, so `_rewrite` never sees it.
        """
        tokens = ctokenize(code)
        edits: List[Tuple[int, int, str]] = []
        for index, token in enumerate(tokens):
            if token.text != "for" or index + 1 >= len(tokens) or tokens[index + 1].text != "(":
                continue
            close_index = match_delimiter(tokens, index + 1)
            if close_index is None:
                continue
            # The two `;` of the header, at its own depth.
            semicolons = top_level_indices(tokens, index + 2, close_index, {";"})
            if semicolons is None or len(semicolons) != 2:
                continue
            # The increment clause without its surrounding whitespace, which stays untouched.
            start, end = tokens[semicolons[1]].end, tokens[close_index].start
            clause = code[start:end]
            start += len(clause) - len(clause.lstrip())
            end = max(start, end - (len(clause) - len(clause.rstrip())))
            folded = self._fold(code[start:end])
            if folded is not None:
                edits.append((start, end, folded))
        return apply_edits(code, edits)

    def _fold(self, statement: str) -> Optional[str]:
        """
        Return `statement` (without its `;`) in compound form if it is a foldable `a = a OP b`, else None. Leading
        `case`, `default` and goto labels are kept in front.
        """
        tokens = ctokenize(statement)
        tokens = tokens[self._labels_end(tokens) :]
        if not tokens:
            return None
        labels = statement[: tokens[0].start]

        assign_index = self._assign_index(tokens)
        lhs_texts = token_texts(tokens, 0, assign_index) if assign_index > 0 else []
        rhs_tokens = tokens[assign_index + 1 :]
        op_index = len(lhs_texts)  # the right side repeats the target, then OP
        if not (
            len(rhs_tokens) > op_index + 1  # the target, OP and a non-empty remainder
            and rhs_tokens[op_index].text in self._COMPOUND_OPS  # the token after the repeated target is OP
            and [token.text for token in rhs_tokens[:op_index]] == lhs_texts  # the right side starts with the target
            and self._pure_lvalue(lhs_texts)  # False for an empty target, so no `=` stops here
            and self._remainder_safe(rhs_tokens[op_index].text, rhs_tokens[op_index + 1 :])
        ):
            return None

        operator = rhs_tokens[op_index]
        lhs = statement[tokens[0].start : tokens[assign_index].start].strip()
        remainder = statement[operator.end :].strip()
        return f"{labels}{lhs} {operator.text}= {remainder}"

    @staticmethod
    def _labels_end(tokens: List[CToken]) -> int:
        """Return the index of the first token after the leading `case`, `default` and goto labels."""
        index = 0
        while index + 1 < len(tokens):
            if tokens[index].text == "case":
                # The `:` ending the label is the first one at depth 0 that closes no `?` and is not half of a `::`.
                # After a stray closer which `:` is top level is unknown, so the label is not skipped.
                open_questions = 0
                colon_index = None
                after_double_colon = False
                for inner, text, depth in iter_depth(tokens, index + 1):
                    if depth < 0:
                        break
                    if after_double_colon:
                        after_double_colon = False  # the second `:` of a `::`
                    elif depth == 0 and text == "?":
                        open_questions += 1
                    elif depth == 0 and text == ":":
                        if inner + 1 < len(tokens) and tokens[inner + 1].text == ":":
                            after_double_colon = True
                        elif open_questions:
                            open_questions -= 1
                        else:
                            colon_index = inner
                            break
                if colon_index is None:
                    break
                index = colon_index + 1
            elif (
                IDENT.fullmatch(tokens[index].text)  # a goto label or `default`
                and tokens[index + 1].text == ":"
                and not (index + 2 < len(tokens) and tokens[index + 2].text == ":")  # not `::`
            ):
                index += 2
            else:
                break
        return index

    @staticmethod
    def _assign_index(tokens: List[CToken]) -> int:
        """Return the index of the first top-level `=` token, or -1."""
        assign_index = first_top_level(tokens, 0, None, {"="})
        return -1 if assign_index is None else assign_index

    @staticmethod
    def _pure_lvalue(lhs_texts: List[str]) -> bool:
        """
        True if the target `lhs_texts` has no `++`, `--`, assignment or call, so evaluating it once instead of twice is
        the same.
        """
        if not lhs_texts or any(text in ("++", "--") or text in _ASSIGN_OPS for text in lhs_texts):
            return False
        for left, right in zip(lhs_texts, lhs_texts[1:]):
            if right == "(" and re.fullmatch(r"[A-Za-z_]\w*", left):
                return False  # a name followed by `(` is a call
        return lhs_texts[0] in ("*", "(") or bool(re.fullmatch(r"[A-Za-z_]\w*", lhs_texts[0]))

    def _remainder_safe(self, operator: str, remainder_tokens: List[CToken]) -> bool:
        """
        True if `a OP= rem` means the same as `a = a OP rem`, where OP is `operator` and rem is `remainder_tokens`.

        The fold regroups `a OP rem` as `a OP (rem)`. That is only the same if every top-level binary operator in `rem`
        binds tighter than OP, or is OP itself and associative: `a - b - c` and `a * b + c` do not fold. A unary
        operator (one where no operator is expected) belongs to its operand, and `->` and `.` are not split on.
        After a cast `(T)` an operand follows, so `-` in `(int)-b` is unary; `(x)-b` is not a cast (see `_is_cast`).
        """
        expects_operator = False
        # For each open bracket: its index, and whether it stood where an operand was expected (a possible cast).
        open_brackets: List[Tuple[int, bool]] = []
        for index, text, depth in iter_depth(remainder_tokens):
            if depth < 0:
                return False  # a stray closer: which operators are top level is unknown
            if text in CLOSER_FOR:  # an opener
                open_brackets.append((index, not expects_operator))
                expects_operator = False
            elif text in OPENER_FOR:  # a closer, which always has its opener on the stack here
                open_index, operand_position = open_brackets.pop()
                group_texts = [inner.text for inner in remainder_tokens[open_index + 1 : index]]
                expects_operator = not (text == ")" and operand_position and _is_cast(group_texts))
            elif not expects_operator and text in self._PREFIX_OPS:
                pass  # a prefix operator; its operand follows
            elif depth == 0 and expects_operator and text in self._PRECEDENCE:
                binds_tighter = self._PRECEDENCE[text] < self._PRECEDENCE[operator]
                if not (binds_tighter or (text == operator and operator in self._ASSOCIATIVE_OPS)):
                    return False
                expects_operator = False
            else:
                expects_operator = True
        return True


class RedundantCastElision(Transform):
    """
    Remove the outer one of two identical adjacent casts: `(T)(T)x` -> `(T)x`.

    The group must be a type by `_is_cast` (names followed by `*`s, with a known type word or a `*`), so calls like
    `(x)(x)`, `(*fp)(*fp)` and `f(a * b)(a * b)` are never touched. Other redundant casts (a cast to the operand's own
    type) need type information.
    """

    id = "cast-elision"
    tier = Tier.T2_STRUCTURAL
    description = "Collapse stacked identical casts."

    def apply(self, code: str) -> str:
        """
        Return `code` with the outer cast of every identical cast pair removed.

        One tokenization is enough: removing `(T)` from `(A)(T)(T)` makes `(A)` touch the second `(T)`, but if `A` is
        `T` it was a duplicate already, so a chain `(T)(T)(T)x` loses all but the last cast in one pass.
        """
        for start, end in reversed(self._dup_casts(ctokenize(code))):
            code = code[:start] + code[end:]
        return code

    @staticmethod
    def _dup_casts(tokens: List[CToken]) -> List[Tuple[int, int]]:
        """Offsets of every redundant cast `(T)` directly followed by `(T)`, left to right and non-overlapping."""
        cuts: List[Tuple[int, int]] = []
        token_count = len(tokens)
        for index in range(token_count):
            if cuts and tokens[index].start < cuts[-1][1]:
                continue
            if tokens[index].text != "(":
                continue
            first_close = match_delimiter(tokens, index)
            if first_close is None or first_close + 1 >= token_count or tokens[first_close + 1].text != "(":
                continue
            second_close = match_delimiter(tokens, first_close + 1)
            if second_close is None:
                continue
            first_type = token_texts(tokens, index + 1, first_close)
            second_type = token_texts(tokens, first_close + 2, second_close)
            if first_type and first_type == second_type and _is_cast(first_type):
                # The first `(T)` is the redundant one; the whitespace up to the second `(T)` goes with it.
                cuts.append((tokens[index].start, tokens[first_close + 1].start))
        return cuts


class InlineSingleUseTemps(Transform):
    """
    Inline a temporary whose only use is the next `return`: `uVar1 = f(); return uVar1;` -> `return f();`.

    The declaration `undefined8 uVar1;` is removed too. The fold only fires when the name occurs exactly as often as
    the assignment, the return and at most one uninitialized declaration account for, counted over the whole input, so
    a name reused in another function blocks it. The declaration only counts if it is in the same function as the
    assignment, so a global (declared at file scope or `extern`) is never folded: its store is observable. The two
    statements are adjacent, so nothing is reordered even if `f()` has side effects. The store converts to the
    temporary's type, so if that differs from the function's return type the fold keeps it as a cast: `return (T)f();`.
    Runs before `decl-coalesce`, so the declaration is still its own statement.
    """

    id = "inline-temps"
    tier = Tier.T2_STRUCTURAL
    description = "Inline a single-use spill temporary into its return."

    # `=(?!=)`, so `x == y;` is not read as an assignment.
    _ASSIGN = re.compile(r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=(?!=)\s*(?P<expr>.+);\s*$", re.S)
    _RETURN = re.compile(r"^\s*return\s+(?P<name>[A-Za-z_]\w*)\s*;(?P<trail>\s*)$", re.S)
    _DECL = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_ ]*\s+\**(?P<name>[A-Za-z_]\w*)\s*;\s*$")
    # A function header `<return type> <name>(`; the return type is group 1.
    _HEADER = re.compile(r"^\s*(?P<ret_type>.*?)\b[A-Za-z_]\w*\s*\(", re.S)
    # Header words that are not part of the return type.
    _HEADER_NOISE = frozenset({"static", "inline", "extern", "__cdecl", "__stdcall", "__fastcall", "__thiscall"})
    # Declaration words that are not part of the temp's type, so they stay out of the cast.
    _STORAGE_CLASS = frozenset({"static", "register"})

    def apply(self, code: str) -> str:
        """Return `code` with every single-use temporary inlined into its `return`."""
        name_counts: Counter = self._name_counts(code)
        pieces = split_statements(code)
        # Offsets into `code`, taken before any piece is rewritten.
        piece_starts = list(accumulate((len(piece) for piece in pieces), initial=0))[:-1]
        enclosing_blocks = self._enclosing_blocks(code, piece_starts)
        decl_indices_by_name = self._declarations(pieces)
        removed_pieces: Set[int] = set()  # indices of the declarations and returns a fold makes redundant

        index = 0
        while index < len(pieces) - 1:
            assign_match = self._ASSIGN.match(pieces[index])
            return_match = self._RETURN.match(pieces[index + 1])
            if not (assign_match and return_match and assign_match.group("name") == return_match.group("name")):
                index += 1
                continue
            name, expr = assign_match.group("name"), assign_match.group("expr")
            # A declaration in another block (a global) does not count, so its name occurs once too often.
            decl_indices = [
                decl_index
                for decl_index in decl_indices_by_name.get(name, [])
                if enclosing_blocks[decl_index] == enclosing_blocks[index]
            ]
            if len(decl_indices) > 1 or not self._is_single_use(name, expr, name_counts[name] - len(decl_indices)):
                index += 1
                continue
            value = expr.strip()
            if decl_indices:
                removed_pieces.add(decl_indices[0])
                temp_type = self._temp_type(pieces[decl_indices[0]])
                value = self._converted(value, temp_type, self._return_type(code, piece_starts[index]))
            pieces[index] = f"{assign_match.group('indent')}return {value};{return_match.group('trail')}"
            removed_pieces.add(index + 1)
            index += 2
        return "".join(piece for index, piece in enumerate(pieces) if index not in removed_pieces)

    @staticmethod
    def _name_counts(code: str) -> Counter:
        """Count each identifier in the code segments of `code`, so names in strings and comments are not counted."""
        return Counter(m.group(0) for m in iter_code_matches(scan(code), IDENT))

    def _declarations(self, pieces: List[str]) -> DefaultDict[str, List[int]]:
        """
        Return the indices of the single-name, uninitialized declarations in `pieces`, by declared name.

        The first word must not be a keyword, or `return x;` would declare `x`. Storing to and loading from a
        `volatile` temp or an `extern` global is observable. Not recording its declaration makes the use count wrong,
        which blocks the fold.
        """
        decl_indices_by_name: DefaultDict[str, List[int]] = defaultdict(list)
        for index, piece in enumerate(pieces):
            decl_match = self._DECL.match(piece)
            if decl_match is None:
                continue
            words = piece.split()
            if words[0] not in NONVALUE_KW and "volatile" not in words and "extern" not in words:
                decl_indices_by_name[decl_match.group("name")].append(index)
        return decl_indices_by_name

    @staticmethod
    def _is_single_use(name: str, expr: str, use_count: int) -> bool:
        """
        True if `name = expr;` can fold into `return name;`: `name` occurs in nothing but those two statements, which
        `use_count` (its occurrences outside its declaration) shows, and `expr` stays the same value once returned.
        """
        # Look for a self-reference in code only, like the counts, so `f("uVar1")` does not block the fold.
        expr_code = "".join(text for seg_type, text in scan(expr) if seg_type == SegmentType.CODE)
        expr_tokens = ctokenize(expr)
        return (
            use_count == 2
            and not re.search(r"\b" + re.escape(name) + r"\b", expr_code)
            # `x = a, g();` is `(x = a), g();`: returning the whole right side would return `g()`.
            and not has_top_level_token(expr_tokens, 0, len(expr_tokens), frozenset({","}))
        )

    def _temp_type(self, declaration: str) -> str:
        """Return the type in `declaration`, without storage-class words: `static char *p;` -> `char *`."""
        type_text = declaration[: self._DECL.match(declaration).start("name")]
        return " ".join(word for word in type_text.split() if word not in self._STORAGE_CLASS)

    def _converted(self, value: str, temp_type: str, return_type: Optional[str]) -> str:
        """
        Return `value` as the temp holds it. The store into the temp converts to its type: keep that as a cast unless
        the function returns the same type anyway.
        """
        if return_type is not None and self._squash(return_type) == self._squash(temp_type):
            return value
        return f"({temp_type}){self._as_operand(value)}"

    @staticmethod
    def _enclosing_blocks(code: str, offsets: List[int]) -> List[Optional[int]]:
        """
        For each of the ascending `offsets`, return the id of the outermost `{...}` block (usually a function body)
        that contains it, or None if it is at file scope. Blocks nested inside a body share the body's id, so two
        ids are equal exactly when the offsets sit in the same body. After a stray `}` the enclosing block is
        unknown, so each offset there gets a negative id of its own that equals no other.
        """
        tokens = ctokenize(code)
        # The id of the outermost block still open after each token, or None at file scope.
        block_after_token: List[Optional[int]] = []
        outer_block_id = -1
        for _, text, depth in iter_depth(tokens, openers="{"):
            if depth < 0:
                break  # a stray `}`: the enclosing block of everything from here on is unknown
            if text == "{" and depth == 0:
                outer_block_id += 1
            block_after_token.append(outer_block_id if text == "{" or depth > 0 else None)
        token_starts = [token.start for token in tokens]
        blocks: List[Optional[int]] = []
        for position, offset in enumerate(offsets):
            before = bisect_left(token_starts, offset)  # the number of tokens that start before `offset`
            if before > len(block_after_token):
                blocks.append(-1 - position)  # past a stray `}`: an id of its own, equal to no other
            else:
                blocks.append(block_after_token[before - 1] if before else None)
        return blocks

    def _return_type(self, code: str, offset: int) -> Optional[str]:
        """Return the declared return type of the function whose body contains `offset`, or None if not found."""
        # `header` is the text before the top-level `{` that is still open, so it is the enclosing function's at any
        # depth; a top-level `}` or `;` ends the previous item, and the next header starts after it.
        tokens = ctokenize(code)
        header_start = 0
        header: Optional[str] = None
        for index, text, depth in iter_depth(tokens, openers="{"):
            if tokens[index].start >= offset:
                break
            if depth != 0:
                continue
            if text == "{":
                header = code[header_start : tokens[index].start]
            elif text in ("}", ";"):
                header_start, header = tokens[index].end, None
        if header is None:
            return None
        header = "\n".join(line for line in strip_comments(header).splitlines() if not line.lstrip().startswith("#"))
        header_match = self._HEADER.match(header)
        if header_match is None:
            return None
        words = [
            word
            for word in re.split(r"(\W)", header_match.group("ret_type"))
            if word.strip() and word not in self._HEADER_NOISE
        ]
        return " ".join(words) or None

    @staticmethod
    def _squash(text: str) -> str:
        """Return `text` without whitespace, so `char *` and `char*` compare equal."""
        return re.sub(r"\s+", "", text)

    @staticmethod
    def _as_operand(expr: str) -> str:
        """Return `expr` as a cast operand: unchanged if it is one token or a call, else parenthesised."""
        tokens = ctokenize(expr)
        if len(tokens) == 1:
            return expr
        if (
            len(tokens) >= 3
            and IDENT.fullmatch(tokens[0].text)
            and tokens[1].text == "("
            and match_delimiter(tokens, 1) == len(tokens) - 1
        ):
            return expr
        return f"({expr})"


class _Branch(NamedTuple):
    """Token spans `(start, end)` of a then or else branch `LV = VALUE;`, plus where the branch ends."""

    lvalue: Tuple[int, int]
    value: Tuple[int, int]
    after: int  # index of the token after the branch
    end_offset: int  # character offset where the branch ends


class _IfElse(NamedTuple):
    """Token spans `(start, end)` of a matched `if (C) LV = A; else LV = B;`, plus where the else branch ends."""

    cond: Tuple[int, int]
    lvalue: Tuple[int, int]
    then_value: Tuple[int, int]
    else_value: Tuple[int, int]
    after: int  # index of the token after the else branch
    end_offset: int  # character offset where the else branch ends


class TernaryFromIfElse(Transform):
    """
    Fold `if (C) LV = A; else LV = B;` into `LV = C ? A : B;`, with braced or bare branches.

    Both branches must be one plain assignment to the same (token-identical) `LV`. Both forms evaluate `C` and `LV`
    once and one of `A` and `B`, but only the if runs `C` before `LV`. So the fold is refused when:

    * `C` has a side effect (`++`, `--`, assignment, call), unless `LV` is a name that `C` does not use;
    * `LV` has a call;
    * `LV` has `++`, `--` or an assignment, and `C` shares a name with it or reads memory through `*`, `->` or `[`;
    * `C`, `A` or `B` has a top-level `?`, `,` or assignment, which would regroup once inlined (`if (a = b) ...` must
      not become `x = a = b ? 1 : 2`, nor `else x = y += 1` become `x = c ? 1 : y += 1`).
    """

    id = "ternary"
    tier = Tier.T2_STRUCTURAL
    description = "Fold a same-target if/else assignment into a ternary."

    # Top-level `?`, `,` or assignment in the condition or a branch would regroup once inlined; `==` still folds.
    _TERNARY_UNSAFE = frozenset({"?", ","}) | _ASSIGN_OPS
    # Tokens through which a condition may read memory that an update in the lvalue changes.
    _INDIRECT = frozenset({"*", "->", "["})

    def apply(self, code: str) -> str:
        """
        Return `code` with every foldable if/else written as a ternary. One pass is enough: a folded branch holds a
        top-level `?`, which `_TERNARY_UNSAFE` rejects, so a fold never enables an enclosing one.
        """
        return apply_edits(code, self._folds(code))

    def _folds(self, code: str) -> List[Tuple[int, int, str]]:
        """Return all non-overlapping if/else -> ternary rewrites, left to right."""
        tokens = ctokenize(code)
        ternary_edits: List[Tuple[int, int, str]] = []
        index = 0
        while index < len(tokens):
            match = self._match_if_else(tokens, index)
            if match is None or not self._is_safe(tokens, match):
                index += 1
                continue
            ternary_edits.append((tokens[index].start, match.end_offset, self._ternary(code, tokens, match)))
            index = match.after  # skip the folded region, so folds stay disjoint
        return ternary_edits

    def _match_if_else(self, tokens: List[CToken], index: int) -> Optional[_IfElse]:
        """
        If `tokens[index:]` starts with `if (C) LV = A; else LV = B;` (braced or bare branches, the same `LV`), return
        its spans, else None.
        """
        if tokens[index].text != "if" or index + 1 >= len(tokens) or tokens[index + 1].text != "(":
            return None
        cond_start = index + 2
        cond_end = match_delimiter(tokens, index + 1)  # the `)` after the condition
        if cond_end is None or cond_end <= cond_start:  # need a non-empty condition
            return None
        then_branch = self._branch(tokens, cond_end + 1)
        if then_branch is None:
            return None
        if then_branch.after >= len(tokens) or tokens[then_branch.after].text != "else":
            return None
        else_branch = self._branch(tokens, then_branch.after + 1)
        if else_branch is None:
            return None
        if token_texts(tokens, *then_branch.lvalue) != token_texts(tokens, *else_branch.lvalue):
            return None
        return _IfElse(
            (cond_start, cond_end),
            then_branch.lvalue,
            then_branch.value,
            else_branch.value,
            else_branch.after,
            else_branch.end_offset,
        )

    def _is_safe(self, tokens: List[CToken], match: _IfElse) -> bool:
        """True if `match` can be written as a ternary without regrouping or reordering anything."""
        if any(
            has_top_level_token(tokens, start, end, self._TERNARY_UNSAFE)
            for start, end in (match.cond, match.then_value, match.else_value)
        ):
            return False
        cond_start, cond_end = match.cond
        lv_start, lv_end = match.lvalue
        # The if runs the condition before the lvalue; `LV = C ? A : B` does not fix their order. An update in the
        # lvalue can only reach the condition through a shared name or memory read via `*`, `->`, `[`.
        shared = self._identifiers(tokens, cond_start, cond_end) & self._identifiers(tokens, lv_start, lv_end)
        lv_is_name = lv_end - lv_start == 1 and IDENT.fullmatch(tokens[lv_start].text)
        cond_reads_memory = any(token.text in self._INDIRECT for token in tokens[cond_start:cond_end])
        return not (
            (self._has_side_effect(tokens, cond_start, cond_end) and (shared or not lv_is_name))
            or self._has_call(tokens, lv_start, lv_end)
            or (self._has_update(tokens, lv_start, lv_end) and (shared or cond_reads_memory))
        )

    def _ternary(self, code: str, tokens: List[CToken], match: _IfElse) -> str:
        """Return `LV = C ? A : B;` for `match`."""
        lvalue, condition, then_value, else_value = (
            self._text(code, tokens, span) for span in (match.lvalue, match.cond, match.then_value, match.else_value)
        )
        return f"{lvalue} = {condition} ? {then_value} : {else_value};"

    @staticmethod
    def _text(code: str, tokens: List[CToken], span: Tuple[int, int]) -> str:
        """The source text of the tokens `tokens[span[0]:span[1]]`."""
        start, end = span
        return code[tokens[start].start : tokens[end - 1].end].strip()

    @staticmethod
    def _parse_assign(tokens: List[CToken], start: int, end: int) -> Optional[Tuple[int, int, int, int]]:
        """
        If `tokens[start:end]` is one assignment `LV = RHS` (with an optional `;`), return the token spans
        `(lv_start, lv_end, rhs_start, rhs_end)`, else None.
        """
        if end > start and tokens[end - 1].text == ";":
            end -= 1
        # Exactly one top-level `=` and no `;`: not more than one statement, and not a chained assignment.
        top_level = top_level_indices(tokens, start, end, {";", "="})
        if top_level is None or len(top_level) != 1 or tokens[top_level[0]].text != "=":
            return None
        assign_index = top_level[0]
        if assign_index == start or assign_index + 1 >= end:
            return None
        return start, assign_index, assign_index + 1, end

    def _branch(self, tokens: List[CToken], start: int) -> Optional[_Branch]:
        """
        Parse the then or else branch, braced or not, that starts at token `start`. Return None unless it is one
        complete assignment.
        """
        if start >= len(tokens):
            return None
        if tokens[start].text == "{":
            last = match_delimiter(tokens, start)
            if last is None:
                return None
            spans = self._parse_assign(tokens, start + 1, last)
        else:
            last = first_top_level(tokens, start, None, {";"})
            if last is None:
                return None
            spans = self._parse_assign(tokens, start, last)
        if spans is None:
            return None
        lv_start, lv_end, value_start, value_end = spans
        return _Branch((lv_start, lv_end), (value_start, value_end), last + 1, tokens[last].end)

    @staticmethod
    def _has_update(tokens: List[CToken], start: int, end: int) -> bool:
        """True if `tokens[start:end]` holds `++`, `--` or an assignment, at any depth."""
        return any(token.text in ("++", "--") or token.text in _ASSIGN_OPS for token in tokens[start:end])

    @staticmethod
    def _has_call(tokens: List[CToken], start: int, end: int) -> bool:
        """
        True if `tokens[start:end]` holds a call, at any depth: `name(`, `tab[0](` or `(*fp)(`.

        `sizeof(` and casts are not calls; a `(...)` group before `(` is a callee only if it starts with `*`, which a
        type never does. `(fp)(x)` cannot be told from a cast and is not counted.
        """
        for index in range(start + 1, end):
            if tokens[index].text != "(":
                continue
            before = tokens[index - 1].text
            if before != ")" and is_value_before(before):
                return True
            if before == ")":
                opener = match_delimiter_backward(tokens, index - 1, start)
                if opener is not None and tokens[opener + 1].text == "*":
                    return True
        return False

    def _has_side_effect(self, tokens: List[CToken], start: int, end: int) -> bool:
        """True if `tokens[start:end]` holds `++`, `--`, an assignment or a call, at any depth."""
        return self._has_update(tokens, start, end) or self._has_call(tokens, start, end)

    @staticmethod
    def _identifiers(tokens: List[CToken], start: int, end: int) -> Set[str]:
        """The identifiers in `tokens[start:end]`, keywords excluded."""
        return {
            token.text for token in tokens[start:end] if IDENT.fullmatch(token.text) and token.text not in NONVALUE_KW
        }


class CanonicalizeControlFlow(Transform):
    """
    Remove gotos and labels that do nothing.

    * A `goto X;` directly followed by the label `X:` is removed: control falls through to `X` anyway.
    * A label `X:` that no `goto X` refers to is removed, but the statement it labels stays.

    Turning gotos into structured control flow would need a control-flow graph and is out of scope.
    """

    id = "cfg-canon"
    tier = Tier.T2_STRUCTURAL
    description = "Remove no-op gotos and unreferenced labels."

    _GOTO = re.compile(r"^\s*goto\s+(?P<label>[A-Za-z_]\w*)\s*;\s*$")
    # One label in a prefix from `_split_leading_labels`, with the whitespace after it.
    _LABEL_NAME = re.compile(r"(?P<label>[A-Za-z_]\w*)\s*:\s*")

    def apply(self, code: str) -> str:
        """
        Return `code` without dead gotos and unused labels.
        """
        code = self._drop_dead_jumps(code)
        code = self._drop_unreferenced_labels(code)
        return code

    def _drop_dead_jumps(self, code: str) -> str:
        """
        Return `code` without the `goto X;` statements whose next kept statement is labeled `X:`.
        """
        # Right to left, so a goto is compared with the next statement that is kept: in `goto A; goto B; B: A: x;` both
        # gotos go in one pass.
        kept_pieces: List[str] = []
        next_labels: Set[str] = set()  # labels directly in front of the next kept statement
        for piece in reversed(split_statements(code)):
            labels, statement = _split_leading_labels(piece)
            names = set(self._LABEL_NAME.findall(labels))
            goto_match = self._GOTO.match(statement)
            if goto_match and goto_match.group("label") in next_labels:
                # Drop the goto. Its own labels now stand in front of the next statement.
                kept_pieces.append(labels)
                next_labels |= names
            else:
                kept_pieces.append(piece)
                next_labels = names
        return "".join(reversed(kept_pieces))

    # A label is referenced by `goto X` or by GCC's label address `&&X` (computed goto). `&&` is also logical AND, but
    # counting such an operand as a reference only keeps a dead label, never drops a live one.
    _LABEL_REF = re.compile(r"\bgoto\s+([A-Za-z_]\w*)|&&\s*([A-Za-z_]\w*)")

    def _drop_unreferenced_labels(self, code: str) -> str:
        """
        Return `code` without the labels that no `goto` or `&&` refers to.
        """
        referenced = {
            name for ref_match in iter_code_matches(scan(code), self._LABEL_REF) for name in ref_match.groups() if name
        }
        transformed_pieces: List[str] = []
        for piece in split_statements(code):
            # Check every leading label, not only the first: in `B: A: x;` both may be unused.
            labels, statement = _split_leading_labels(piece)
            kept_labels = self._LABEL_NAME.sub(
                lambda label_match: label_match.group(0) if label_match.group("label") in referenced else "", labels
            )
            transformed_pieces.append(kept_labels + statement)
        return "".join(transformed_pieces)


class MinimizeIntegerLiterals(Transform):
    """
    Write a hex integer literal in decimal when that is shorter: `0x10` -> `16`, `0xff` -> `255`.

    Decompilers print every integer in hex, so the hex form is their habit, not analyst signal, and the value does not
    change. A literal stays hex when decimal is no shorter (`0xffffff`, `0xffffffff`), so wide masks keep their hex
    form. Only values up to `0x7fffffff` are converted, so the type stays the same: above that, hex would be
    `unsigned int` but decimal `long`. A suffix stays attached (`0x10u` -> `16u`). Fewer characters do not guarantee
    fewer tokens for every tokenizer, but for typical LLM tokenizers they do.
    """

    id = "int-minform"
    tier = Tier.T2_STRUCTURAL
    description = "Re-spell a hex literal in decimal when shorter."

    _INT_MAX = 0x7FFFFFFF

    def apply(self, code: str) -> str:
        """
        Return `code` with every hex literal written in decimal where that is shorter and keeps the type.
        """
        edits: List[Tuple[int, int, str]] = []
        for token in ctokenize(code):
            # A hex-float literal (`0x1f.0p3`) is one token and never matches.
            int_match = CINT.fullmatch(token.text)
            if int_match is None or int_match.group("digits")[:2] not in ("0x", "0X"):
                continue
            hex_digits, suffix = int_match.group("digits", "suffix")
            value = int(hex_digits, 16)
            if value > self._INT_MAX:
                continue  # wider than int: decimal would change the literal's type
            decimal = str(value)
            if len(decimal) < len(hex_digits):
                edits.append((token.start, token.end, decimal + suffix))
        return apply_edits(code, edits)


class DerefOffsetToIndex(Transform):
    """
    Rewrite `*(p + N)` as `p[N]`, which means the same in C for any pointer `p` and integer `N`.

    The `*` must be a dereference, not a multiply, so the token before it must not be a value: `a * (b + c)` stays,
    `= *(p + 4)` is rewritten. The token after `)` must not be a postfix operator (`.`, `->`, `(`, `[`, `++`, `--`),
    which binds tighter than prefix `*`. The base must be a name or `&name` (written `(&x)[N]`), and `N` an integer
    literal.

    What `N` counts depends on the decompiler. Ghidra always casts the sum (`*(uint *)(param_1 + 0x18)`), which this
    pass skips. Hex-Rays types the base, so `*(this + 6)` on a `_DWORD *this` becomes `this[6]` with the same meaning.
    Binary Ninja writes a subscript for an element index and the add for a byte offset, so on its output `arg1[0x18]`
    looks like an element index although it is a byte offset. The `std::string` capacity check at `0x402FA0` in the
    examples is `*(this + 6)` in Hex-Rays and `*(arg1 + 0x18)` in Binary Ninja. The program stays the same; only that
    hint is lost.
    """

    id = "deref-offset"
    tier = Tier.T2_STRUCTURAL
    description = "Rewrite a dereferenced pointer-add as a subscript."

    # Postfix operators bind tighter than prefix `*`, so a rewrite before one would regroup the expression.
    _BLOCK_AFTER = frozenset({".", "->", "(", "[", "++", "--"})

    def apply(self, code: str) -> str:
        """
        Return `code` with every safe `*(p + N)` rewritten as `p[N]`.
        """
        tokens = ctokenize(code)
        token_count = len(tokens)
        edits: List[Tuple[int, int, str]] = []
        index = 0
        while index < token_count:
            if tokens[index].text == "*" and index + 1 < token_count and tokens[index + 1].text == "(":
                previous = tokens[index - 1].text if index > 0 else None
                # A `*` after a value (`a * (b + c)`, `1.5 * (a + 4)`, `i++ * (p + 4)`) is a multiply.
                if not is_value_before(previous):
                    close = match_delimiter(tokens, index + 1)
                    if close is not None:
                        replacement = self._index_form(token_texts(tokens, index + 2, close))
                        after = tokens[close + 1].text if close + 1 < token_count else None
                        if replacement is not None and after not in self._BLOCK_AFTER:
                            edits.append((tokens[index].start, tokens[close].end, replacement))
                            index = close + 1
                            continue
            index += 1
        return apply_edits(code, edits)

    @staticmethod
    def _index_form(inner: List[str]) -> Optional[str]:
        """
        Return `name[N]` for the inner tokens `name + N` or `& name + N`, else None.
        """
        if (
            len(inner) == 3
            and IDENT.fullmatch(inner[0])
            and inner[0] not in NONVALUE_KW
            and inner[1] == "+"
            and CINT.fullmatch(inner[2])
        ):
            return f"{inner[0]}[{inner[2]}]"
        if (
            len(inner) == 4
            and inner[0] == "&"
            and IDENT.fullmatch(inner[1])
            and inner[1] not in NONVALUE_KW
            and inner[2] == "+"
            and CINT.fullmatch(inner[3])
        ):
            return f"(&{inner[1]})[{inner[3]}]"
        return None


class DropTrailingReturn(Transform):
    """
    Remove a `return;` that is the last statement of a function body, since control falls off the end anyway.

    Ghidra ends every `void` function with one. The `return;` must be followed directly by the `}` that closes the
    function; one at the end of a loop or `if` body leaves the function early and stays. It must also be a statement
    of its own, not the unbraced body of `if`, `else` or a loop, or the statement of a label.
    """

    id = "drop-trailing-return"
    tier = Tier.T2_STRUCTURAL
    description = "Drop a redundant trailing return at the end of a function body."

    def apply(self, code: str) -> str:
        """
        Return `code` without the redundant `return;` at the end of each function body.
        """
        tokens = ctokenize(code)
        edits: List[Tuple[int, int, str]] = []
        for index, text, depth in iter_depth(tokens, openers="{"):
            # A function body closes with a `}` at depth 0. If it ends in `return ;`, that return is redundant, unless
            # it is the unbraced body of `if (c)`, `else`, `for (...)` or `while (...)`, or of a label
            # (`done: return; }`). Dropping it would leave `if (c) }` or `done: }`, so it must follow `;`, `{` or `}`.
            if (
                text == "}"
                and depth == 0
                and index >= 3
                and tokens[index - 1].text == ";"
                and tokens[index - 2].text == "return"
                and tokens[index - 3].text in (";", "{", "}")
            ):
                edits.append((tokens[index - 2].start, tokens[index - 1].end, ""))
        return apply_edits(code, edits)
