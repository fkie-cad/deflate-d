"""
T2 structural transforms: shorter equivalent statements and expressions, so all of them are semantics-preserving.

No pass changes the inside of a string or char literal. Comments are only changed by `RemoveComments`, which deletes
the auto-generated ones. The passes work on the segments from `scan`, the statements from `split_statements` or the
tokens from `ctokenize`, which all keep literals and comments whole. The passes have no type information, so a pass
skips any rewrite it cannot prove safe. A missed rewrite only costs size; a wrong one changes the program.
"""

from __future__ import annotations

import re
from collections import defaultdict
from itertools import groupby
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

from .base import Tier, Transform
from .ctokens import (
    CINT,
    CNUMBER,
    CToken,
    ctokenize,
    has_top_level_token,
    match_delimiter,
    split_statements,
    word_before,
)
from .lexer import SegmentType, scan, strip_comments

# Keywords that start a control statement, so a block body starting with one is not a single simple statement.
_CTRL_KW = frozenset({"if", "for", "while", "do", "switch", "else"})

# Statement keywords that are not types, so `<kw> ...;` is never read as a declaration. The C++ ones matter too:
# `delete p;` has the `type name;` shape.
_STMT_KW = frozenset(
    {"return", "goto", "break", "continue", "case", "default", "sizeof", "typedef"}
    | {"delete", "throw", "new", "co_return", "co_yield", "co_await", "using", "namespace"}
)

# A local declaration: `int x;`, `int x[3];` or `int x = 1;`. It starts with two or more words (`type [*]name`), which
# an assignment or any other expression statement never does.
_DECL = re.compile(r"^[A-Za-z_][A-Za-z0-9_ ]*\s+\**[A-Za-z_]\w*(?:\s*\[[^\];]*\])*\s*(?:=[^;]*)?;$")

# Binary operators with a compound-assignment form (`a = a OP b` -> `a OP= b`).
_COMPOUND_OPS = frozenset("+ - * / % & | ^ << >>".split())

# One leading goto label such as `LABEL_3:` (not C++ `::`); group 1 is its name.
_LABEL_PREFIX = re.compile(r"\s*([A-Za-z_]\w*)\s*:(?!:)\s*")

# C binary-operator precedence (smaller binds tighter). `compound-assign` uses it to check that `a = a OP rest` ->
# `a OP= rest` does not regroup `rest`.
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

# Operators that may repeat in a folded chain `a = a OP b OP c`, because they are associative for every operand type.
# Only the bitwise ones qualify. `+` and `*` also apply to floats, where `(a+b)+c` and `a+(b+c)` round differently, and
# the pass cannot tell a float from an int. `a = a + b` and `a = a + b*c` still fold: neither regroups.
_ASSOCIATIVE_OPS = frozenset({"&", "|", "^"})


def _split_leading_labels(statement: str) -> Tuple[str, str]:
    """
    Split `statement` into its leading `label:` prefixes and the rest: `"L1: L2: x = 1;"` -> `("L1: L2: ", "x = 1;")`.

    `case` and `default` labels stay attached, so a `switch` body is never split.
    """
    prefix_length = 0
    while (label_match := _LABEL_PREFIX.match(statement, prefix_length)) is not None and label_match.group(1) not in (
        "case",
        "default",
    ):
        prefix_length = label_match.end()
    return statement[:prefix_length], statement[prefix_length:]


def _strip_leading_labels(statement: str) -> str:
    """Return `statement` without its leading goto labels (see `_split_leading_labels`)."""
    return _split_leading_labels(statement)[1]


def _squash(text: str) -> str:
    """Return `text` without whitespace, so `char *` and `char*` compare equal."""
    return re.sub(r"\s+", "", text)


def _looks_like_decl(statement: str, first_word: str) -> bool:
    """
    True if `statement`, whose first word is `first_word`, is a local declaration, which C does not allow as a control
    body.
    """
    if first_word in _CTRL_KW or first_word in _STMT_KW:
        return False
    return bool(_DECL.match(statement))


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
        return "".join(
            (self._FLAG_TEMP.sub(r"cond\1", text) if seg_type == SegmentType.CODE else text)
            for seg_type, text in scan(code)
        )


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
    _NON_TYPES = _STMT_KW | _CTRL_KW

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

    Works for `if`, `else`, `for`, `while` and `do`. These blocks keep their braces:

    * Other blocks: function, struct and enum bodies, initializers, plain scope blocks and `switch` bodies.
    * A body that starts with a control keyword: in `if (a) { if (b) f(); } else g();` the `else` would move to the
      inner `if`.
    * A body that is a declaration: `if (c) int x;` is not valid C.

    Strippable blocks never contain braces, so all pairs from one scan are disjoint and are removed right to left in
    a single pass.
    """

    id = "brace-elision"
    tier = Tier.T2_STRUCTURAL
    description = "Drop braces around a single-statement control block (if/else/for/while/do)."

    def apply(self, code: str) -> str:
        """
        Return `code` with the braces of every strippable control block replaced by spaces.
        """
        # One pass is enough: unwrapping an inner block never makes the outer one strippable, since the outer body then
        # starts with a control keyword.
        for open_offset, close_offset in sorted(self._strippable_pairs(code), reverse=True):
            # Replace each brace with a space so its neighbours cannot merge: `else{x` must not become `elsex`.
            code = code[:open_offset] + " " + code[open_offset + 1 : close_offset] + " " + code[close_offset + 1 :]
        return code

    def _strippable_pairs(self, code: str) -> List[Tuple[int, int]]:
        """
        Return the offsets of the `{` and `}` of every control block that holds one simple statement.
        """
        # Non-whitespace code characters and their offsets. Strings and comments are skipped, so their braces are
        # ignored.
        characters: List[str] = []
        offsets: List[int] = []
        offset = 0
        for seg_type, text in scan(code):
            if seg_type == SegmentType.CODE:
                for character in text:
                    if not character.isspace():
                        characters.append(character)
                        offsets.append(offset)
                    offset += 1
            else:
                offset += len(text)

        open_indices: List[int] = []
        pairs: List[Tuple[int, int]] = []
        for index, character in enumerate(characters):
            if character == "{":
                open_indices.append(index)
            elif character == "}" and open_indices:
                open_index = open_indices.pop()
                if not self._is_control_block(characters, open_index):
                    continue
                open_offset, close_offset = offsets[open_index], offsets[index]
                if self._single_simple(code[open_offset + 1 : close_offset]):
                    pairs.append((open_offset, close_offset))
        return pairs

    @staticmethod
    def _is_control_block(characters: List[str], brace_index: int) -> bool:
        """
        True if the `{` at `characters[brace_index]` opens a control block.
        """
        if brace_index == 0:
            return False
        if characters[brace_index - 1] == ")":
            depth, paren_index = 0, brace_index - 1
            while paren_index >= 0:
                if characters[paren_index] == ")":
                    depth += 1
                elif characters[paren_index] == "(":
                    depth -= 1
                    if depth == 0:
                        break
                paren_index -= 1
            if paren_index < 0:
                return False
            # `characters` has no whitespace, so `else if` reads as `elseif`, which is treated like `if`. `switch` is
            # left out: a body with a `case` label needs its braces (`switch(x)case 1:...` is invalid C), and
            # `_single_simple` keeps labels attached.
            return word_before(characters, paren_index) in {"if", "for", "while", "elseif"}
        return word_before(characters, brace_index) in {"else", "do"}

    @staticmethod
    def _single_simple(body: str) -> bool:
        """
        True if `body` is one statement that is neither a control statement nor a declaration.
        """
        code_only = "".join(text for seg_type, text in scan(body) if seg_type == SegmentType.CODE)
        if "{" in code_only or "}" in code_only:
            return False
        statement = code_only.strip()
        if not statement:
            return False
        depth = semicolons = 0
        ends_with_semicolon = False
        last_index = len(statement) - 1
        for index, character in enumerate(statement):
            if character in "([":
                depth += 1
            elif character in ")]":
                depth = max(0, depth - 1)
            elif character == ";" and depth == 0:
                semicolons += 1
                ends_with_semicolon = index == last_index
        if semicolons != 1 or not ends_with_semicolon:
            return False
        # Skip leading goto labels (`LABEL_3: if (b) ...;`) to find the first real word. Otherwise a labeled inner `if`
        # would pass the dangling-else check, lose its braces, and an outer `else` would bind to it.
        unlabeled = _strip_leading_labels(statement)
        word_match = re.match(r"[A-Za-z_]\w*", unlabeled)
        first_word = word_match.group(0) if word_match else ""
        if first_word in _CTRL_KW:
            return False
        return not _looks_like_decl(unlabeled, first_word)


class CompoundAssignment(Transform):
    """
    Fold `a = a OP b;` into `a OP= b;` (`iVar1 = iVar1 + iVar4;` -> `iVar1 += iVar4;`).

    The right side must start with exactly the tokens of the target, so `a->b` or `a + +b` is never read as `a`
    followed by an operator. The target is evaluated once instead of twice, so it may not contain `++`, `--` or a
    call: `*(int *)(p + i * 4)` folds, `*p++` does not. The rest of the right side must bind tighter than OP (see
    `_remainder_safe`), since the fold regroups it.
    """

    id = "compound-assign"
    tier = Tier.T2_STRUCTURAL
    description = "Fold an expanded assignment into compound form."

    def apply(self, code: str) -> str:
        """
        Return `code` with every foldable `a = a OP b;` written as `a OP= b;`.
        """
        return "".join(self._rewrite(piece) for piece in split_statements(code))

    def _rewrite(self, piece: str) -> str:
        """
        Return `piece` in compound form if it is a foldable `a = a OP b;`, else unchanged.
        """
        stripped = piece.rstrip()
        if not stripped.endswith(";"):
            return piece
        indent_length = len(piece) - len(piece.lstrip())
        indent = piece[:indent_length]
        trailing = piece[len(stripped) :]
        statement = stripped[indent_length:-1]  # the statement without leading whitespace and `;`

        # Set leading goto labels aside and put them back in front of the result.
        labels, assignment = _split_leading_labels(statement)

        tokens = ctokenize(assignment)
        assign_index = self._assign_index(tokens)
        if assign_index <= 0:  # no top-level `=`, or nothing to its left
            return piece
        lhs_texts = [token.text for token in tokens[:assign_index]]
        if not self._pure_lvalue(lhs_texts):
            return piece

        rhs_tokens = tokens[assign_index + 1 :]
        lhs_length = len(lhs_texts)
        if len(rhs_tokens) <= lhs_length or [token.text for token in rhs_tokens[:lhs_length]] != lhs_texts:
            return piece
        operator = rhs_tokens[lhs_length].text
        if operator not in _COMPOUND_OPS:
            return piece
        if not self._remainder_safe(operator, rhs_tokens[lhs_length + 1 :]):
            return piece
        remainder = assignment[rhs_tokens[lhs_length].end :].strip()
        if not remainder:
            return piece

        lhs = assignment[: tokens[assign_index].start].strip()
        return f"{indent}{labels}{lhs} {operator}= {remainder};{trailing}"

    @staticmethod
    def _remainder_safe(operator: str, remainder_tokens: List[CToken]) -> bool:
        """
        True if `a OP= rem` means the same as `a = a OP rem`, where OP is `operator` and rem is `remainder_tokens`.

        The fold regroups `a OP rem` as `a OP (rem)`. That is only the same if every top-level binary operator in `rem`
        binds tighter than OP, or is OP itself and associative: `a - b - c` and `a * b + c` do not fold. A unary
        operator (one not after an operand) belongs to its operand, and `->` and `.` are not split on.
        """
        depth = 0
        after_operand = False
        for token in remainder_tokens:
            if token.text in ("(", "[", "{"):
                depth += 1
                after_operand = False
            elif token.text in (")", "]", "}"):
                depth -= 1
                after_operand = True
            elif depth == 0 and after_operand and token.text in _PRECEDENCE:
                binds_tighter = _PRECEDENCE[token.text] < _PRECEDENCE[operator]
                if not (binds_tighter or (token.text == operator and operator in _ASSOCIATIVE_OPS)):
                    return False
                after_operand = False
            else:
                after_operand = True
        return True

    @staticmethod
    def _assign_index(tokens: List[CToken]) -> int:
        """
        Return the index of the first top-level `=` token, or -1.
        """
        depth = 0
        for index, token in enumerate(tokens):
            if token.text in ("(", "[", "{"):
                depth += 1
            elif token.text in (")", "]", "}"):
                depth = max(0, depth - 1)
            elif token.text == "=" and depth == 0:
                return index
        return -1

    @staticmethod
    def _pure_lvalue(lhs_texts: List[str]) -> bool:
        """
        True if the target `lhs_texts` has no `++`, `--` or call, so evaluating it once instead of twice is the same.
        """
        if not lhs_texts or "++" in lhs_texts or "--" in lhs_texts:
            return False
        for left, right in zip(lhs_texts, lhs_texts[1:]):
            if right == "(" and re.fullmatch(r"[A-Za-z_]\w*", left):
                return False  # a name followed by `(` is a call
        return lhs_texts[0] in ("*", "(") or bool(re.fullmatch(r"[A-Za-z_]\w*", lhs_texts[0]))


class RedundantCastElision(Transform):
    """
    Remove the outer one of two identical adjacent casts: `(T)(T)x` -> `(T)x`.

    The type must contain a `*` or a known type word and must not start with `*`, so calls like `(x)(x)` and
    `(*fp)(*fp)` are never touched. Other redundant casts (a cast to the operand's own type) need type information.
    """

    id = "cast-elision"
    tier = Tier.T2_STRUCTURAL
    description = "Collapse stacked identical casts."

    _TYPE_WORDS = frozenset(
        "int char long short void unsigned signed float double bool "
        "uint ulong ushort uchar byte sbyte undefined "
        "size_t wchar_t".split()
    )

    def apply(self, code: str) -> str:
        """
        Return `code` with the outer cast of every identical cast pair removed.
        """
        # One tokenization is enough: removing `(T)` from `(A)(T)(T)` makes `(A)` touch the second `(T)`, but if `A` is
        # `T` it was a duplicate already, so a chain `(T)(T)(T)x` loses all but the last cast here.
        for start, end in reversed(self._dup_casts(ctokenize(code))):
            code = code[:start] + code[end:]
        return code

    def _dup_casts(self, tokens: List[CToken]) -> List[Tuple[int, int]]:
        """
        Offsets of every redundant cast `(T)` directly followed by `(T)`, left to right and non-overlapping.
        """
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
            first_type = [token.text for token in tokens[index + 1 : first_close]]
            second_type = [token.text for token in tokens[first_close + 2 : second_close]]
            if first_type and first_type == second_type and self._type_like(first_type):
                # The first `(T)` is the redundant one.
                cuts.append((tokens[index].start, tokens[first_close].end))
        return cuts

    @classmethod
    def _type_like(cls, type_texts: List[str]) -> bool:
        """
        True if the token texts `type_texts` inside a `(...)` group can only be a type.
        """
        # A type never starts with `*`; `(*fp)` is a dereferenced function pointer.
        if type_texts[0] == "*" or "," in type_texts or "?" in type_texts:
            return False
        return "*" in type_texts or any(text in cls._TYPE_WORDS for text in type_texts)


class InlineSingleUseTemps(Transform):
    """
    Inline a temporary whose only use is the next `return`: `uVar1 = f(); return uVar1;` -> `return f();`.

    The declaration `undefined8 uVar1;` is removed too. The fold only fires when the name occurs exactly as often as
    the assignment, the return and at most one uninitialized declaration account for, counted over the whole input, so
    a name reused in another function blocks it. The two statements are adjacent, so nothing is reordered even if
    `f()` has side effects. The store converts to the temporary's type, so if that differs from the function's return
    type the fold keeps it as a cast: `return (T)f();`. Runs before `decl-coalesce`, so the declaration is still its
    own statement.
    """

    id = "inline-temps"
    tier = Tier.T2_STRUCTURAL
    description = "Inline a single-use spill temporary into its return."

    _ASSIGN = re.compile(r"^(\s*)([A-Za-z_]\w*)\s*=\s*(.+);\s*$", re.S)
    _RETURN = re.compile(r"^\s*return\s+([A-Za-z_]\w*)\s*;(\s*)$", re.S)
    _DECL = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_ ]*\s+\**(?P<name>[A-Za-z_]\w*)\s*;\s*$")
    # A function header `<return type> <name>(`; the return type is group 1.
    _HEADER = re.compile(r"^\s*(.*?)\b[A-Za-z_]\w*\s*\(", re.S)
    # Header words that are not part of the return type.
    _HEADER_NOISE = frozenset({"static", "inline", "extern", "__cdecl", "__stdcall", "__fastcall", "__thiscall"})

    def apply(self, code: str) -> str:
        """
        Return `code` with every single-use temporary inlined into its `return`.
        """
        name_counts: Dict[str, int] = {}
        for seg_type, text in scan(code):
            if seg_type == SegmentType.CODE:
                for name_match in re.finditer(r"[A-Za-z_]\w*", text):
                    name_counts[name_match.group(0)] = name_counts.get(name_match.group(0), 0) + 1

        pieces = split_statements(code)
        piece_count = len(pieces)
        keep = [True] * piece_count

        # Single-name declarations by name. The first word must not be a keyword, or `return x;` would declare `x`.
        decl_indices_by_name: DefaultDict[str, List[int]] = defaultdict(list)
        for index, piece in enumerate(pieces):
            decl_match = self._DECL.match(piece)
            # Storing to and loading from a `volatile` temp is observable. Not recording its declaration makes the use
            # count wrong, which blocks the fold.
            if decl_match and piece.split()[0] not in (_STMT_KW | _CTRL_KW) and "volatile" not in piece.split():
                decl_indices_by_name[decl_match.group("name")].append(index)

        index = 0
        while index < piece_count - 1:
            assign_match = self._ASSIGN.match(pieces[index])
            return_match = self._RETURN.match(pieces[index + 1])
            if (
                keep[index]
                and keep[index + 1]
                and assign_match
                and return_match
                and assign_match.group(2) == return_match.group(1)
            ):
                name, expr = assign_match.group(2), assign_match.group(3)
                decl_indices = decl_indices_by_name.get(name, [])
                expected_count = 2 + (1 if len(decl_indices) == 1 else 0)
                # Look for a self-reference in code only, like the counts above, so `f("uVar1")` does not block the
                # fold.
                expr_code = "".join(text for seg_type, text in scan(expr) if seg_type == SegmentType.CODE)
                if (
                    name_counts.get(name, 0) == expected_count
                    and len(decl_indices) <= 1
                    and not re.search(r"\b" + re.escape(name) + r"\b", expr_code)
                ):
                    value = expr.strip()
                    if decl_indices:
                        # The store into the temp converts to its type: keep that as a cast unless the function returns
                        # the same type anyway.
                        declaration = pieces[decl_indices[0]]
                        temp_type = declaration[: self._DECL.match(declaration).start("name")].strip()
                        return_type = self._return_type(code, sum(len(piece) for piece in pieces[:index]))
                        if return_type is None or _squash(return_type) != _squash(temp_type):
                            value = f"({temp_type}){self._as_operand(value)}"
                    pieces[index] = f"{assign_match.group(1)}return {value};{return_match.group(2)}"
                    keep[index + 1] = False
                    if decl_indices:
                        keep[decl_indices[0]] = False
                    index += 2
                    continue
            index += 1
        return "".join(piece for index, piece in enumerate(pieces) if keep[index])

    @classmethod
    def _return_type(cls, code: str, offset: int) -> Optional[str]:
        """
        Return the declared return type of the function whose body contains `offset`, or None if not found.
        """
        depth, header_start = 0, 0
        header: Optional[str] = None
        for token in ctokenize(code):
            if token.start >= offset:
                break
            if token.text == "{":
                if depth == 0:
                    header = code[header_start : token.start]
                depth += 1
            elif token.text == "}":
                depth -= 1
                if depth == 0:
                    header_start, header = token.end, None
            elif token.text == ";" and depth == 0:
                header_start = token.end
        if depth != 1 or header is None:
            return None
        header = "\n".join(line for line in strip_comments(header).splitlines() if not line.lstrip().startswith("#"))
        header_match = cls._HEADER.match(header)
        if header_match is None:
            return None
        words = [
            word for word in re.split(r"(\W)", header_match.group(1)) if word.strip() and word not in cls._HEADER_NOISE
        ]
        return " ".join(words) or None

    @staticmethod
    def _as_operand(expr: str) -> str:
        """
        Return `expr` as a cast operand: unchanged if it is one token or a call, else parenthesised.
        """
        tokens = ctokenize(expr)
        if len(tokens) == 1:
            return expr
        if (
            len(tokens) >= 3
            and _IDENT_RX.match(tokens[0].text)
            and tokens[1].text == "("
            and match_delimiter(tokens, 1) == len(tokens) - 1
        ):
            return expr
        return f"({expr})"


# Helpers for `TernaryFromIfElse`, on the tokens from `ctokenize`.
def _parse_assign(tokens: List[CToken], start: int, end: int) -> Optional[Tuple[int, int, int, int]]:
    """
    If `tokens[start:end]` is one assignment `LV = RHS` (with an optional `;`), return the token spans
    `(lv_start, lv_end, rhs_start, rhs_end)`, else None.
    """
    if end > start and tokens[end - 1].text == ";":
        end -= 1
    depth, assign_index = 0, None
    for index in range(start, end):
        text = tokens[index].text
        if text in "([{":
            depth += 1
        elif text in ")]}":
            depth -= 1
        elif depth == 0 and text == ";":
            return None  # more than one statement
        elif depth == 0 and text == "=":
            if assign_index is not None:
                return None  # chained assignment
            assign_index = index
    if assign_index is None or assign_index == start or assign_index + 1 >= end:
        return None
    return start, assign_index, assign_index + 1, end


def _branch(tokens: List[CToken], start: int) -> Optional[Tuple[Optional[Tuple[int, int, int, int]], int, int]]:
    """
    Parse the then or else branch, braced or not, that starts at token `start`.

    Return `(spans, after, end)`: `spans` from `_parse_assign`, or None if the branch is not exactly one assignment;
    `after` is the index of the token after the branch and `end` the offset where it ends. Return None if there is no
    complete branch.
    """
    token_count = len(tokens)
    if start >= token_count:
        return None
    if tokens[start].text == "{":
        close = match_delimiter(tokens, start)
        if close is None:
            return None
        return _parse_assign(tokens, start + 1, close), close + 1, tokens[close].end
    depth, index = 0, start
    while index < token_count:
        text = tokens[index].text
        if text in "([{":
            depth += 1
        elif text in ")]}":
            depth -= 1
        elif depth == 0 and text == ";":
            return _parse_assign(tokens, start, index), index + 1, tokens[index].end
        index += 1
    return None


# Top-level tokens that block the fold in the condition or a branch: `?` and `,` would regroup once inlined, and so
# would a bare `=` in the condition (`if (a = b) ...`), which binds looser than `?:`. `==` is its own token and folds.
_TERNARY_UNSAFE = frozenset({"?", ",", "="})
_ASSIGN_OPS = frozenset({"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="})
# The condition may not hold a top-level compound assignment either, for the same reason.
_COND_UNSAFE = _TERNARY_UNSAFE | _ASSIGN_OPS
# Tokens through which a condition may read memory that an update in the lvalue changes.
_INDIRECT = frozenset({"*", "->", "["})


def _has_update(tokens: List[CToken], start: int, end: int) -> bool:
    """
    True if `tokens[start:end]` holds `++`, `--` or an assignment, at any depth.
    """
    return any(token.text in ("++", "--") or token.text in _ASSIGN_OPS for token in tokens[start:end])


def _has_call(tokens: List[CToken], start: int, end: int) -> bool:
    """
    True if `tokens[start:end]` holds a call, at any depth: `name(`, `tab[0](` or `(*fp)(`.

    `sizeof(` and casts are not calls; a `(...)` group before `(` is a callee only if it starts with `*`, which a type
    never does. `(fp)(x)` cannot be told from a cast and is not counted.
    """
    for index in range(start + 1, end):
        if tokens[index].text != "(":
            continue
        before = tokens[index - 1].text
        if before == "]" or (_IDENT_RX.match(before) and before not in _NONVALUE_KW):
            return True
        if before == ")":
            opener = _open_paren(tokens, start, index - 1)
            if opener is not None and tokens[opener + 1].text == "*":
                return True
    return False


def _open_paren(tokens: List[CToken], start: int, close: int) -> Optional[int]:
    """
    Return the index of the `(` that matches the `)` at `close`, searching back to `start`, or None.
    """
    depth = 0
    for index in range(close, start - 1, -1):
        if tokens[index].text == ")":
            depth += 1
        elif tokens[index].text == "(":
            depth -= 1
            if depth == 0:
                return index
    return None


def _has_side_effect(tokens: List[CToken], start: int, end: int) -> bool:
    """
    True if `tokens[start:end]` holds `++`, `--`, an assignment or a call, at any depth.
    """
    return _has_update(tokens, start, end) or _has_call(tokens, start, end)


def _identifiers(tokens: List[CToken], start: int, end: int) -> Set[str]:
    """
    The identifiers in `tokens[start:end]`, keywords excluded.
    """
    return {token.text for token in tokens[start:end] if _IDENT_RX.match(token.text) and token.text not in _NONVALUE_KW}


class TernaryFromIfElse(Transform):
    """
    Fold `if (C) LV = A; else LV = B;` into `LV = C ? A : B;`, with braced or bare branches.

    Both branches must be one plain assignment to the same (token-identical) `LV`. Both forms evaluate `C` and `LV`
    once and one of `A` and `B`, but only the if runs `C` before `LV`. So the fold is refused when:

    * `C` has a side effect (`++`, `--`, assignment, call), unless `LV` is a name that `C` does not use;
    * `LV` has a call;
    * `LV` has `++`, `--` or an assignment, and `C` shares a name with it or reads memory through `*`, `->` or `[`;
    * `C`, `A` or `B` has a top-level `?` or `,`, or `C` a top-level assignment, which would regroup once inlined
      (`if (a = b) ...` must not become `x = a = b ? 1 : 2`).

    Known gap (CODE_REVIEW 1.5): `?:` converts `A` and `B` to a common type before the store, so branches of different
    types (`-1` and `1u`) can change the stored value. Without type information this is not detected.
    """

    id = "ternary"
    tier = Tier.T2_STRUCTURAL
    description = "Fold a same-target if/else assignment into a ternary."

    def apply(self, code: str) -> str:
        """
        Return `code` with every foldable if/else written as a ternary.
        """
        # Collect every disjoint fold in one tokenization and apply them right to left, so earlier offsets stay valid.
        # A folded branch holds a top-level `?`, which `_TERNARY_UNSAFE` rejects, so a fold never enables an enclosing
        # one and one pass is enough.
        for start, end, replacement in reversed(self._folds(code)):
            code = code[:start] + replacement + code[end:]
        return code

    def _folds(self, code: str) -> List[Tuple[int, int, str]]:
        """
        Return all non-overlapping if/else -> ternary rewrites, left to right.
        """
        tokens = ctokenize(code)
        token_count = len(tokens)
        folds: List[Tuple[int, int, str]] = []
        index = 0
        while index < token_count:
            if tokens[index].text != "if" or index + 1 >= token_count or tokens[index + 1].text != "(":
                index += 1
                continue
            cond_start = index + 2
            cond_end = match_delimiter(tokens, index + 1)  # the `)` after the condition
            if cond_end is None or cond_end <= cond_start:  # need a non-empty condition
                index += 1
                continue
            then_branch = _branch(tokens, cond_end + 1)
            if not then_branch or then_branch[0] is None:
                index += 1
                continue
            then_spans, after_then, _ = then_branch
            if after_then >= token_count or tokens[after_then].text != "else":
                index += 1
                continue
            else_branch = _branch(tokens, after_then + 1)
            if not else_branch or else_branch[0] is None:
                index += 1
                continue
            else_spans, after_else, fold_end = else_branch

            lv_start, lv_end, then_start, then_end = then_spans
            else_lv_start, else_lv_end, else_start, else_end = else_spans
            if [token.text for token in tokens[lv_start:lv_end]] != [
                token.text for token in tokens[else_lv_start:else_lv_end]
            ]:
                index += 1
                continue
            if (
                has_top_level_token(tokens, cond_start, cond_end, _COND_UNSAFE)
                or has_top_level_token(tokens, then_start, then_end, _TERNARY_UNSAFE)
                or has_top_level_token(tokens, else_start, else_end, _TERNARY_UNSAFE)
            ):
                index += 1
                continue
            # The if runs the condition before the lvalue; `LV = C ? A : B` does not fix their order. An update in
            # the lvalue can only reach the condition through a shared name or memory read via `*`, `->`, `[`.
            shared = _identifiers(tokens, cond_start, cond_end) & _identifiers(tokens, lv_start, lv_end)
            lv_is_name = lv_end - lv_start == 1 and _IDENT_RX.match(tokens[lv_start].text)
            cond_reads_memory = any(token.text in _INDIRECT for token in tokens[cond_start:cond_end])
            if (
                (_has_side_effect(tokens, cond_start, cond_end) and (shared or not lv_is_name))
                or _has_call(tokens, lv_start, lv_end)
                or (_has_update(tokens, lv_start, lv_end) and (shared or cond_reads_memory))
            ):
                index += 1
                continue

            condition = code[tokens[cond_start].start : tokens[cond_end - 1].end].strip()
            lvalue = code[tokens[lv_start].start : tokens[lv_end - 1].end].strip()
            then_value = code[tokens[then_start].start : tokens[then_end - 1].end].strip()
            else_value = code[tokens[else_start].start : tokens[else_end - 1].end].strip()
            folds.append((tokens[index].start, fold_end, f"{lvalue} = {condition} ? {then_value} : {else_value};"))
            index = after_else  # skip the folded region, so folds stay disjoint
        return folds


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

    _GOTO = re.compile(r"^\s*goto\s+([A-Za-z_]\w*)\s*;\s*$")
    # One label in a prefix from `_split_leading_labels`, with the whitespace after it.
    _LABEL_NAME = re.compile(r"([A-Za-z_]\w*)\s*:\s*")

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
            if goto_match and goto_match.group(1) in next_labels:
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
            name
            for seg_type, text in scan(code)
            if seg_type == SegmentType.CODE
            for ref_match in self._LABEL_REF.finditer(text)
            for name in ref_match.groups()
            if name
        }
        transformed_pieces: List[str] = []
        for piece in split_statements(code):
            # Check every leading label, not only the first: in `B: A: x;` both may be unused.
            labels, statement = _split_leading_labels(piece)
            kept_labels = self._LABEL_NAME.sub(
                lambda label_match: label_match.group(0) if label_match.group(1) in referenced else "", labels
            )
            transformed_pieces.append(kept_labels + statement)
        return "".join(transformed_pieces)


# An identifier, and the keywords that may stand before a unary `*` and are never an operand value. (Numbers are
# matched with `CINT`.)
_IDENT_RX = re.compile(r"^[A-Za-z_]\w*$")
_NONVALUE_KW = _CTRL_KW | _STMT_KW


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

    _HEX = re.compile(r"(0[xX][0-9a-fA-F]+)([uUlL]*|[uU]?i(?:8|16|32|64))")
    _INT_MAX = 0x7FFFFFFF

    def apply(self, code: str) -> str:
        """
        Return `code` with every hex literal written in decimal where that is shorter and keeps the type.
        """
        edits: List[Tuple[int, int, str]] = []
        for token in ctokenize(code):
            # A hex-float literal (`0x1f.0p3`) is one token and never matches.
            hex_match = self._HEX.fullmatch(token.text)
            if hex_match is None:
                continue
            hex_digits, suffix = hex_match.groups()
            value = int(hex_digits, 16)
            if value > self._INT_MAX:
                continue  # wider than int: decimal would change the literal's type
            decimal = str(value)
            if len(decimal) < len(hex_digits):
                edits.append((token.start, token.end, decimal + suffix))
        if not edits:
            return code
        # Build the result in one forward pass: a hex-heavy file has thousands of edits, and slicing per edit is
        # quadratic.
        transformed_parts: List[str] = []
        copied_up_to = 0
        for start, end, replacement in edits:
            transformed_parts.append(code[copied_up_to:start])
            transformed_parts.append(replacement)
            copied_up_to = end
        transformed_parts.append(code[copied_up_to:])
        return "".join(transformed_parts)


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

    # Tokens after which `*` is a multiply. A postfix `++`/`--` ends an operand (`x++ * (p + 4)`). This also skips the
    # prefix case `++*(p + 4)`, which looks the same; skipping only misses a rewrite.
    _VALUE_BEFORE = frozenset({")", "]", "++", "--"})
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
                # `CNUMBER`, not `CINT`: a float (`1.5 * (a + 4)`) is a value too, and a match only skips the rewrite.
                is_value = previous is not None and (
                    previous in self._VALUE_BEFORE
                    or CNUMBER.fullmatch(previous)
                    or (_IDENT_RX.match(previous) and previous not in _NONVALUE_KW)
                )
                if not is_value:
                    close = match_delimiter(tokens, index + 1)
                    if close is not None:
                        replacement = self._index_form([token.text for token in tokens[index + 2 : close]])
                        after = tokens[close + 1].text if close + 1 < token_count else None
                        if replacement is not None and after not in self._BLOCK_AFTER:
                            edits.append((tokens[index].start, tokens[close].end, replacement))
                            index = close + 1
                            continue
            index += 1
        for start, end, replacement in reversed(edits):
            code = code[:start] + replacement + code[end:]
        return code

    @staticmethod
    def _index_form(inner: List[str]) -> Optional[str]:
        """
        Return `name[N]` for the inner tokens `name + N` or `& name + N`, else None.
        """
        if (
            len(inner) == 3
            and _IDENT_RX.match(inner[0])
            and inner[0] not in _NONVALUE_KW
            and inner[1] == "+"
            and CINT.fullmatch(inner[2])
        ):
            return f"{inner[0]}[{inner[2]}]"
        if (
            len(inner) == 4
            and inner[0] == "&"
            and _IDENT_RX.match(inner[1])
            and inner[1] not in _NONVALUE_KW
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
        depth = 0
        edits: List[Tuple[int, int]] = []
        for index, token in enumerate(tokens):
            if token.text == "{":
                depth += 1
            elif token.text == "}":
                depth -= 1
                # A function body closes when the depth is back to 0. If it ends in `return ;`, that return is
                # redundant, unless it is the unbraced body of `if (c)`, `else`, `for (...)` or `while (...)`, or of a
                # label (`done: return; }`). Dropping it would leave `if (c) }` or `done: }`, so it must follow `;`, `{`
                # or `}`.
                if (
                    depth == 0
                    and index >= 3
                    and tokens[index - 1].text == ";"
                    and tokens[index - 2].text == "return"
                    and tokens[index - 3].text in (";", "{", "}")
                ):
                    edits.append((tokens[index - 2].start, tokens[index - 1].end))
        for start, end in reversed(edits):
            code = code[:start] + code[end:]
        return code
