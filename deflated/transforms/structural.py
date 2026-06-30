"""T2 --- structural, lossless transforms.

Information-preserving rewrites: nothing the model could use is removed, but the
rendering gets smaller. The one exception split out of this tier is the removal
of decompiler *warning* banners (e.g. ``/* WARNING: Could not recover
jumptable */``), which carry genuine analyst signal --- that lives in
``RemoveWarningComments`` at the reductive tier (T4), so T2 stays strictly
information-preserving.
"""

from __future__ import annotations

import re

from .base import Tier, Transform
from .lexer import SegmentType, scan, strip_comments
from .tokens import (
    Token,
    has_top as _has_top,
    match_delim as _match_delim,
    split_statements as _split_statements,
    tokenize as _tok_offsets,
    word_before as _word_before,
)

# Keywords whose first word introduces a control statement (so a block body
# beginning with one is *not* a single simple statement) ...
_CTRL_KW = frozenset({"if", "for", "while", "do", "switch", "else"})
# ... and statement keywords that are not types, so a sole `<kw> ...;` body must
# never be mistaken for a declaration.
_STMT_KW = frozenset({"return", "goto", "break", "continue", "case", "default", "sizeof", "typedef"})
# A local declaration -- bare (`int x;`), array (`int x[3];`), or *initialized*
# (`int x = 1;`). The leading `type [*]name` shape (two-plus identifier words,
# the last being the declared name) is what separates a declaration from an
# assignment (`x = 1;`) or any other expression statement, which never begin
# `<word> <word>`. Array dimensions and an initializer are both optional.
_DECL = re.compile(r"^[A-Za-z_][A-Za-z0-9_ ]*\s+\**[A-Za-z_]\w*(?:\s*\[[^\];]*\])*\s*(?:=[^;]*)?;$")

# Binary operators that have a compound-assignment form (a = a OP b -> a OP= b).
_COMPOUND_OPS = frozenset("+ - * / % & | ^ << >>".split())


# A single leading goto-label prefix, e.g. ``LABEL_3:`` (but not C++ ``::``).
_LABEL_PREFIX = re.compile(r"\s*[A-Za-z_]\w*\s*:(?!:)\s*")


def _split_leading_labels(s: str) -> tuple[str, str]:
    """Split ``s`` into its run of leading ``label:`` prefixes and the remainder.

    ``"L1: L2: x = 1;"`` -> ``("L1: L2: ", "x = 1;")``. ``case``/``default``
    labels are left attached (they are not plain goto-labels), so a ``switch``
    body is never mis-split.
    """
    i = 0
    while (m := _LABEL_PREFIX.match(s, i)) and s[i : m.end()].strip().rstrip(":").strip() not in ("default", "case"):
        i = m.end()
    return s[:i], s[i:]


def _strip_leading_labels(s: str) -> str:
    """Return ``s`` with any leading goto-labels removed (see _split_leading_labels)."""
    return _split_leading_labels(s)[1]

# C binary-operator precedence (smaller binds tighter). Used to verify that
# folding `a = a OP rest` -> `a OP= rest` does not silently re-group the
# right-hand side (which would change the result for non-associative OPs).
_PRECEDENCE = {
    "*": 3, "/": 3, "%": 3,
    "+": 4, "-": 4,
    "<<": 5, ">>": 5,
    "<": 6, "<=": 6, ">": 6, ">=": 6,
    "==": 7, "!=": 7,
    "&": 8, "^": 9, "|": 10, "&&": 11, "||": 12,
    "?": 13, ":": 13, ",": 14,
}
# OPs whose repeated application is associative *for every operand type they
# accept*, so a same-precedence chain `a OP b OP c` may still fold. Only the
# bitwise operators qualify: they apply solely to integers, where they are exactly
# associative. `+`/`*` are deliberately excluded: although associative on integers
# (mod 2^n), they also apply to floating-point, where reassociating `(a+b)+c` into
# `a+(b+c)` changes the rounded result --- and this text-local pass cannot tell a
# float lvalue from an int one, so it must refuse the chain to stay lossless.
# (Single-term `a = a + b` -> `a += b` and tighter-binding `a = a + b*c` are
# unaffected: neither reassociates.)
_ASSOCIATIVE_OPS = frozenset({"&", "|", "^"})


def _looks_like_decl(s: str, first: str) -> bool:
    """True if ``s`` is a local declaration (illegal as a control sub-statement)."""
    if first in _CTRL_KW or first in _STMT_KW:
        return False
    return bool(_DECL.match(s))


class RemoveComments(Transform):
    """Remove auto-generated line and block comments, *except* warning banners.

    Address annotations (``/* 0x4011a0 */``) and Hex-Rays' per-variable
    storage-location notes (``// rax``, ``// [rsp+8h]``, ``BYREF``) are both
    decompiler-recovered location/provenance metadata: invisible to program
    semantics and irrelevant to our tasks, so removing them is lossless here,
    even though each is signal for some low-level analysis (addresses for binary
    diffing or trace correlation, the location notes for ABI/calling-convention
    recovery; see the Threats discussion). Decompiler *warning* banners
    (``/* WARNING: Could not recover jumptable... */``) are different --- they
    signal that the decompilation is unreliable here, which is genuine analyst
    signal --- so they are preserved at this tier and only dropped by
    :class:`RemoveWarningComments` at T4. String-safe via the scanner.
    """

    id = "comments"
    tier = Tier.T2_STRUCTURAL
    description = "Remove auto-generated address and storage-location comments, keeping warning banners."

    def apply(self, code: str) -> str:
        return strip_comments(code, keep_warnings=True)


class RemoveWarningComments(Transform):
    """Remove decompiler warning banners (``/* WARNING: ... */``).

    Lossy by design: a warning banner tells the analyst the decompiler gave up
    or guessed (unrecovered jumptables, type conflicts), which is real signal.
    Dropping it is therefore gated at the reductive tier, separate from the
    lossless comment removal at T2.
    """

    id = "comments-warning"
    tier = Tier.T4_REDUCTIVE
    description = "Remove the decompiler's WARNING unreliability banners."

    def apply(self, code: str) -> str:
        return "".join(" " if (seg_type == SegmentType.BLOCK_COMMENT and "WARNING" in text) else text for seg_type, text in scan(code))


class DropCodePointerCast(Transform):
    """Drop Ghidra's ``(code *)`` function-pointer casts on indirect calls.

    Ghidra spells every indirect call through a data pointer as
    ``(*(code *)PTR_x)()``. The cast to its synthetic ``code`` type carries no
    analyst signal beyond "this is called through a pointer", and the pattern
    recurs thousands of times in a single translation unit, so at the reductive
    tier we drop the cast (``(*PTR_x)()``). Lossy because the function-pointer
    typing hint is discarded --- hence T4, alongside the other genuine-signal
    reductions.

    Only the exact cast shape ``( code *+ )`` is removed. A multiplication
    ``code * 2`` (no closing paren right after the stars) and a declaration
    ``code *p`` (no surrounding parens) are never touched, and ``code`` inside a
    longer identifier never matches --- the match is token-level.
    """

    id = "drop-code-cast"
    tier = Tier.T4_REDUCTIVE
    description = "Drop Ghidra's (code *) cast on an indirect call."

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        cuts: list[tuple[int, int]] = []
        i = 0
        while i < n:
            if toks[i][0] == "(" and i + 2 < n and toks[i + 1][0] == "code" and toks[i + 2][0] == "*":
                j = i + 2
                while j < n and toks[j][0] == "*":
                    j += 1
                if j < n and toks[j][0] == ")":
                    cuts.append((toks[i][1], toks[j][2]))
                    i = j + 1
                    continue
            i += 1
        for lo, hi in reversed(cuts):
            code = code[:lo] + code[hi:]
        return code


# Hex-Rays pseudo-width *types*: spellings that never occur in hand-written C, so
# a value-context cast to one is unambiguously a decompiler width annotation.
_WIDTH_CAST_TYPES = frozenset({"_BYTE", "_WORD", "_DWORD", "_QWORD", "_OWORD"})
# A token that begins an operand (so a preceding `(TYPE)` is a cast, not a stray
# parenthesised type): an opening paren, a prefix-unary operator, an identifier,
# a number, or a string/char literal.
_OPERAND_START_OPS = frozenset({"(", "*", "&", "-", "~", "!", "+", "++", "--"})
# Keywords that may precede a cast's `(` (a cast can follow `return`, `case`, ...)
# without the parentheses being a call/grouping applied to a value.
_CAST_PREV_KW = frozenset({"return", "case", "sizeof", "if", "while", "for", "switch", "do", "else", "goto"})
_WCAST_NUM = re.compile(r"0[xX][0-9a-fA-F]+|\d+\.?\d*")
_WCAST_IDENT = re.compile(r"[A-Za-z_]\w*")
# Bit widths of the pseudo-width types, for the literal-narrowing guard in
# :class:`StripWidthCasts`: stripping `(_DWORD)` off a literal that does not fit
# the cast width (or any float literal) would truncate it and change the value.
_WIDTH_BITS = {"_BYTE": 8, "_WORD": 16, "_DWORD": 32, "_QWORD": 64, "_OWORD": 128}
# A pure integer literal (no float point/exponent). ``_WCAST_NUM`` would also
# match floats, so this stricter pattern is what the narrowing guard reasons on.
_WCAST_INT = re.compile(r"0[xX][0-9a-fA-F]+|\d+")


class StripWidthCasts(Transform):
    """Drop Hex-Rays pseudo-width narrowing casts in value position.

    Hex-Rays litters expressions with explicit width casts to its own pseudo-
    width *types* (``(_BYTE)``, ``(_WORD)``, ``(_DWORD)``, ``(_QWORD)``,
    ``(_OWORD)``) --- spellings that do not exist in hand-written C, so they are
    pure artifacts of mapping fixed-width x86 operations back to source. We drop
    the cast (``(_BYTE)gv`` -> ``gv``) where it sits in value position, keeping
    the operand and the surrounding operation. Lossy: the width/sign hint is
    discarded (though it stays recoverable from the operand's declared type),
    hence T4 alongside the other genuine-signal reductions.

    Only the exact shape ``( <pseudo-width-type> )`` followed by an operand start
    is removed. A pointer cast (``(_BYTE *)p`` --- a real reinterpretation whose
    access width is load-bearing) keeps its ``*`` and is never matched; and
    ``sizeof(_QWORD)`` or a call ``f(_QWORD)`` is excluded by the value-position
    guard, so no operator-bearing or size-of context is ever touched. A cast on
    a *literal* that the width would narrow is also left in place: stripping
    ``(_DWORD)0x123456789`` would drop the truncation and change the value (and a
    float operand always truncates). Decompiler output never puts a width cast on
    a literal --- the operand is always a recovered variable/expression --- so
    this literal guard is defensive; it declines only the value-unsafe cases and
    leaves every other site to the existing (lossy) rule.

    The pseudo-width spellings are the conservative, no-false-positive subset.
    The conventional casts Hex-Rays also inserts (``(int)``, ``(char)``,
    ``(unsigned int)``) carry slightly more signal and a real (if rare)
    false-positive surface, so they are intentionally out of the default set.
    """

    id = "strip-width-cast"
    tier = Tier.T4_REDUCTIVE
    description = "Remove Hex-Rays pseudo-width casts, keeping load-bearing pointer casts."

    def __init__(self, types: frozenset[str] | None = None) -> None:
        self._types = types if types is not None else _WIDTH_CAST_TYPES

    def apply(self, code: str) -> str:
        # Stacked width casts (``(_DWORD)(_BYTE)x``) peel one layer per pass,
        # because the inner cast's ``(`` is preceded by the outer cast's ``)`` (a
        # value position the guard rejects); iterate to a fixed point so the pass
        # is idempotent. Bounded by the number of casts.
        prev = None
        while code != prev:
            prev = code
            code = self._strip_once(code)
        return code

    def _strip_once(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        cuts: list[tuple[int, int]] = []
        i = 0
        while i < n:
            if toks[i][0] == "(" and i + 2 < n and toks[i + 1][0] in self._types and toks[i + 2][0] == ")":
                prev = toks[i - 1][0] if i > 0 else None
                after = toks[i + 3][0] if i + 3 < n else None
                if self._operand_starts(after) and not self._prev_is_value(prev) and self._literal_safe(toks[i + 1][0], toks, i + 3, n, code):
                    cuts.append((toks[i][1], toks[i + 2][2]))
                    i += 3
                    continue
            i += 1
        for lo, hi in reversed(cuts):
            code = code[:lo] + code[hi:]
        return code

    @classmethod
    def _literal_safe(cls, cast_type: str, toks, j: int, n: int, code: str) -> bool:
        """Whether dropping ``(<cast_type>)`` is value-preserving for the operand
        beginning at token index ``j`` (or ``j >= n`` when the cast ends the input).

        A *narrowing* width cast on a literal can change the value: an integer
        literal wider than the cast truncates, and a float (or a hex-float head
        continued by ``.``/``p``) always truncates. We look past a single leading
        unary ``+``/``-``/``~`` and unwrap a parenthesised lone literal, so
        ``(_BYTE)-1`` (== 255, not -1), ``(_BYTE)~0`` (== 255), and
        ``(_BYTE)(0x1ff)`` (== 255) are all recognised as narrowing and declined.
        Variables and multi-token sub-expressions are unaffected --- the discarded
        width is a decompiler hint, lossy but value-neutral --- so only literal
        operands are scrutinised.
        """
        if j >= n:
            return True
        tok, _, end = toks[j]
        # Unwrap a parenthesised lone literal: ``(LIT)`` narrows exactly as ``LIT``
        # would; a multi-token expression in parens is value-neutral, so allow it.
        if tok == "(":
            close = _match_delim(toks, j, "(", ")")
            if close == j + 2:
                return cls._literal_safe(cast_type, toks, j + 1, n, code)
            return True
        # A leading unary sign/complement. ``+LIT`` keeps the value; ``-LIT``/``~LIT``
        # of an integer literal become a large positive under the unsigned width
        # truncation, so the value always changes -> decline. On a variable the
        # whole operand is an expression, so it is value-neutral.
        if tok in ("+", "-", "~"):
            if j + 1 < n and _WCAST_INT.fullmatch(toks[j + 1][0]):
                return cls._literal_safe(cast_type, toks, j + 1, n, code) if tok == "+" else False
            return True
        # A float literal operand: truncation always changes the value.
        if _WCAST_NUM.fullmatch(tok) and "." in tok:
            return False
        if not _WCAST_INT.fullmatch(tok):
            return True  # not an integer literal: existing (lossy) behaviour
        # An integer head immediately followed by `.` or `p`/`P` is a hex-float
        # literal (`0x1.8p3` tokenizes as `0x1` then `.8p3`); stripping truncates.
        if end < len(code) and code[end] in ".pP":
            return False
        bits = _WIDTH_BITS.get(cast_type)
        if bits is None:
            return True
        value = int(tok, 16) if tok[:2].lower() == "0x" else int(tok, 10)
        return value < (1 << bits)

    @staticmethod
    def _operand_starts(tok: str | None) -> bool:
        if tok is None:
            return False
        return bool(tok in _OPERAND_START_OPS or _WCAST_IDENT.fullmatch(tok) or _WCAST_NUM.fullmatch(tok) or tok[0] in "\"'")

    @staticmethod
    def _prev_is_value(prev: str | None) -> bool:
        # A value before `(` means the parens are a call/subscript/group applied
        # to that value (``f(_QWORD)``, ``a[i](_QWORD)``), never a cast. Keywords
        # such as ``return``/``sizeof`` are not values, but ``sizeof(_QWORD)`` is
        # a size-of, so it is excluded here too.
        if prev is None:
            return False
        if prev == "sizeof":
            return True
        return bool(prev in {")", "]"} or _WCAST_NUM.fullmatch(prev) or (_WCAST_IDENT.fullmatch(prev) and prev not in _CAST_PREV_KW))


class CoalesceDeclarations(Transform):
    """Consolidate same-type local declarations across a declaration region.

    Within a maximal run of consecutive uninitialized declaration statements,
    declarators are grouped by type and emitted as one statement per type ---
    even when the same type is non-adjacent, e.g.

        int iVar1; ulong uVar2, uVar3; int iVar4;
        ->  int iVar1, iVar4; ulong uVar2, uVar3;

    Safety: only *uninitialized* declarators (optional ``*``s plus a plain
    identifier) are consolidated. They have no initializer, hence no side
    effects and no dependence on declaration order, so regrouping them is
    strictly lossless. Initialized *definitions* (``int x = f();``), arrays, and
    function pointers are left untouched --- reordering a side-effecting
    initializer is unsafe without a full parser. Keyword-led statements
    (``goto h;``, ``return iVar1;``) are explicitly excluded.
    """

    id = "decl-coalesce"
    tier = Tier.T2_STRUCTURAL
    description = "Merge same-type uninitialized declarations into one statement."

    # A consolidatable declaration: type, then a comma-list of uninitialized
    # declarators (each an optional run of '*' before a plain identifier). The
    # trailing ';' anchors the last declarator so the non-greedy type absorbs
    # multi-word types ("unsigned int") unambiguously. '=', '[', '(' are
    # excluded, so initializers / arrays / function pointers never match.
    _DECL = re.compile(
        r"^(?P<lead>\s*)"
        r"(?P<type>[A-Za-z_][A-Za-z0-9_ ]*?)[ \t]+"
        r"(?P<decls>\**\s*[A-Za-z_]\w*(?:[ \t]*,[ \t]*\**\s*[A-Za-z_]\w*)*)"
        r"[ \t]*;[ \t]*$"
    )

    # First-word "types" that actually introduce a statement, not a declaration.
    _NON_TYPES = frozenset("return goto break continue case default sizeof typedef " "do else while for if switch".split())

    def _match_decl(self, piece: str) -> re.Match | None:
        m = self._DECL.match(piece)
        if m and m.group("type").split()[0] in self._NON_TYPES:
            return None
        return m

    def apply(self, code: str) -> str:
        pieces = _split_statements(code)
        out: list[str] = []
        i, n = 0, len(pieces)
        while i < n:
            m = self._match_decl(pieces[i])
            if not m:
                out.append(pieces[i])
                i += 1
                continue
            run = [m]
            j = i + 1
            while j < n:
                mj = self._match_decl(pieces[j])
                if not mj:
                    break
                run.append(mj)
                j += 1
            out.append(self._consolidate(run, pieces[i:j]))
            i = j
        return "".join(out)

    @staticmethod
    def _consolidate(run: list[re.Match], originals: list[str]) -> str:
        groups: dict[str, list[str]] = {}
        order: list[str] = []
        for m in run:
            btype = re.sub(r"\s+", " ", m.group("type").strip())
            decls = [re.sub(r"\s+", "", d) for d in m.group("decls").split(",")]
            if btype not in groups:
                groups[btype] = []
                order.append(btype)
            groups[btype].extend(decls)
        if len(order) == len(run):  # nothing merges; leave the run verbatim
            return "".join(originals)
        lead = run[0].group("lead")
        sep = lead if "\n" in lead else " "
        stmts = [f"{t} {', '.join(groups[t])};" for t in order]
        return lead + sep.join(stmts)


class DropSingleStatementBraces(Transform):
    """Remove the braces of a control block that holds one simple statement.

    ``if (c) { x = 1; }`` -> ``if (c) x = 1;`` (and likewise for ``else``,
    ``for``, ``while``, ``do``). The braces are pure punctuation here, so the
    rewrite is lossless. Three safety traps are handled explicitly:

    * **Only control blocks.** A ``{`` is stripped only when it opens an
      ``if/for/while/switch`` (matched ``(...)`` preceded by the keyword),
      ``else``, or ``do``. Function bodies, struct/enum bodies, array and
      compound-literal initializers, and naked scope blocks are left intact ---
      stripping their braces would be invalid or change scope.

    * **Dangling ``else``.** The body must be a single *simple* statement that
      does not itself begin with a control keyword, so a brace-wrapped inner
      ``if`` (``if (a) { if (b) f(); } else g();``) is never unwrapped and the
      ``else`` cannot re-bind.

    * **Sole declarations.** ``if (c) { int x; }`` keeps its braces, since
      ``if (c) int x;`` is not valid C.

    Strippable blocks contain no nested braces by construction, so every pair
    found in one scan is disjoint; we apply them right-to-left and iterate to a
    fixed point. Runs through the scanner, so braces inside literals/comments are
    never touched.
    """

    id = "brace-elision"
    tier = Tier.T2_STRUCTURAL
    description = "Drop braces around a single-statement control block (if/else/for/while/do)."

    def apply(self, code: str) -> str:
        for _ in range(64):  # bounded fixed-point; one pass usually suffices
            pairs = self._strippable_pairs(code)
            if not pairs:
                break
            for o, c in sorted(pairs, reverse=True):
                # Replace each brace with a space so neighbours never merge
                # (e.g. ``else{`` -> ``else `` not ``elsex``).
                code = code[:o] + " " + code[o + 1 : c] + " " + code[c + 1 :]
        return code

    def _strippable_pairs(self, code: str) -> list[tuple[int, int]]:
        # Non-whitespace code characters with their original offsets (strings
        # and comments are skipped, so their braces are invisible here).
        sig: list[str] = []
        idx: list[int] = []
        pos = 0
        for seg_type, text in scan(code):
            if seg_type == SegmentType.CODE:
                for ch in text:
                    if not ch.isspace():
                        sig.append(ch)
                        idx.append(pos)
                    pos += 1
            else:
                pos += len(text)

        stack: list[int] = []
        result: list[tuple[int, int]] = []
        for m, ch in enumerate(sig):
            if ch == "{":
                stack.append(m)
            elif ch == "}" and stack:
                om = stack.pop()
                if not self._is_control_block(sig, om):
                    continue
                o, c = idx[om], idx[m]
                if self._single_simple(code[o + 1 : c]):
                    result.append((o, c))
        return result

    @staticmethod
    def _is_control_block(sig: list[str], m: int) -> bool:
        """True if ``sig[m] == '{'`` opens a control-flow block."""
        if m == 0:
            return False
        if sig[m - 1] == ")":
            depth, k = 0, m - 1
            while k >= 0:
                if sig[k] == ")":
                    depth += 1
                elif sig[k] == "(":
                    depth -= 1
                    if depth == 0:
                        break
                k -= 1
            if k < 0:
                return False
            # ``sig`` has no whitespace, so an ``else if`` controlling clause
            # reads back as the single word ``elseif`` -- treat it as ``if`` so
            # ``else if (c) { stmt; }`` is unwrapped like a plain ``if``.
            # ``switch`` is deliberately excluded: a switch body carrying a
            # ``case``/``default`` label needs its braces (``switch(x)case 1:...``
            # is invalid C), and ``_single_simple`` keeps the label attached, so a
            # one-statement switch body would otherwise be unwrapped to invalid C.
            return _word_before(sig, k) in {"if", "for", "while", "elseif"}
        return _word_before(sig, m) in {"else", "do"}

    @staticmethod
    def _single_simple(body: str) -> bool:
        code_only = "".join(t for seg_type, t in scan(body) if seg_type == SegmentType.CODE)
        if "{" in code_only or "}" in code_only:
            return False
        s = code_only.strip()
        if not s:
            return False
        depth = semis = 0
        semi_end = False
        last = len(s) - 1
        for i, ch in enumerate(s):
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth = max(0, depth - 1)
            elif ch == ";" and depth == 0:
                semis += 1
                semi_end = i == last
        if semis != 1 or not semi_end:
            return False
        # Look past any leading goto-labels (`LABEL_3: if (b) ...;`) to the real
        # first token. Otherwise the label name is read as ``first`` and a labeled
        # inner control statement slips past the dangling-else guard below, so its
        # protective braces are dropped and an outer ``else`` re-binds to it.
        s_kw = _strip_leading_labels(s)
        mw = re.match(r"[A-Za-z_]\w*", s_kw)
        first = mw.group(0) if mw else ""
        if first in _CTRL_KW:
            return False
        return not _looks_like_decl(s_kw, first)


class CompoundAssignment(Transform):
    """Fold ``a = a OP b;`` into ``a OP= b;`` for the compound-capable operators.

    Decompilers emit the expanded form pervasively (``iVar1 = iVar1 + iVar4;``,
    ``uVar3 = uVar3 + 1;``); the compound form is identical in meaning whenever
    the left-hand side is evaluated only once to the same effect.

    Safety. The transform matches by *token sequence*, not string equality, so
    the left operand of the right-hand side must be the exact same token list as
    the assignment target --- ``a->b`` (token ``->``) and ``a + +b`` (two ``+``
    tokens) can never be misread as ``a`` followed by an operator. The target
    must also be a *pure* lvalue: no ``++``/``--`` and no function call, so
    evaluating it once (compound form) rather than twice (expanded form) cannot
    change behaviour. Address arithmetic without side effects
    (``*(int *)(p + i * 4)``) is therefore eligible, but ``*p++`` is not.
    """

    id = "compound-assign"
    tier = Tier.T2_STRUCTURAL
    description = "Fold an expanded assignment into compound form."

    def apply(self, code: str) -> str:
        return "".join(self._rewrite(p) for p in _split_statements(code))

    def _rewrite(self, piece: str) -> str:
        stripped = piece.rstrip()
        if not stripped.endswith(";"):
            return piece
        n_lead = len(piece) - len(piece.lstrip())
        lead = piece[:n_lead]
        trail = piece[len(stripped) :]
        inner = stripped[n_lead:-1]  # statement text without leading ws or ';'

        # Set aside any leading goto labels so the assignment after them is
        # reachable and the labels are preserved in place.
        label, rest = _split_leading_labels(inner)

        toks = _tok_offsets(rest)
        i = self._assign_index(toks)
        if i <= 0:  # no top-level '=' assignment, or nothing on the left
            return piece
        lhs_tokens = [t for t, _, _ in toks[:i]]
        if not self._pure_lvalue(lhs_tokens):
            return piece

        rhs = toks[i + 1 :]
        k = len(lhs_tokens)
        if len(rhs) <= k or [t for t, _, _ in rhs[:k]] != lhs_tokens:
            return piece
        op = rhs[k][0]
        if op not in _COMPOUND_OPS:
            return piece
        if not self._remainder_safe(op, rhs[k + 1 :]):
            return piece
        remainder = rest[rhs[k][2] :].strip()
        if not remainder:
            return piece

        lhs_text = rest[: toks[i][1]].strip()
        return f"{lead}{label}{lhs_text} {op}= {remainder};{trail}"

    @staticmethod
    def _remainder_safe(op: str, rem: list[Token]) -> bool:
        """True if ``a OP= rem`` preserves the meaning of ``a = a OP rem``.

        Folding re-groups the right-hand side as ``a OP (rem)``. That is only
        equivalent to the original left-associative evaluation when every
        top-level binary operator in ``rem`` binds *tighter* than OP, or repeats
        an associative OP. Operators that bind looser or equal (``a - b - c``,
        ``a * b + c``) would change the result, so the fold is refused. A unary
        operator (one not following an operand) is part of an operand and never
        counts; ``->``/``.`` are not split operators either.
        """
        depth = 0
        prev_operand = False
        for t, _, _ in rem:
            if t in ("(", "[", "{"):
                depth += 1
                prev_operand = False
            elif t in (")", "]", "}"):
                depth -= 1
                prev_operand = True
            elif depth == 0 and prev_operand and t in _PRECEDENCE:
                tighter = _PRECEDENCE[t] < _PRECEDENCE[op]
                if not (tighter or (t == op and op in _ASSOCIATIVE_OPS)):
                    return False
                prev_operand = False
            else:
                prev_operand = True
        return True

    @staticmethod
    def _assign_index(toks: list[Token]) -> int:
        """Index of the first top-level plain ``=`` token, or -1."""
        depth = 0
        for idx, (t, _, _) in enumerate(toks):
            if t in ("(", "[", "{"):
                depth += 1
            elif t in (")", "]", "}"):
                depth = max(0, depth - 1)
            elif t == "=" and depth == 0:
                return idx
        return -1

    @staticmethod
    def _pure_lvalue(toks: list[str]) -> bool:
        if not toks or "++" in toks or "--" in toks:
            return False
        for a, b in zip(toks, toks[1:]):
            if b == "(" and re.fullmatch(r"[A-Za-z_]\w*", a):
                return False  # identifier immediately followed by '(' -> a call
        return toks[0] in ("*", "(") or bool(re.fullmatch(r"[A-Za-z_]\w*", toks[0]))


class RedundantCastElision(Transform):
    """Drop provably-redundant *duplicate* casts: ``(T)(T)x`` -> ``(T)x``.

    Decompilers occasionally stack a cast on top of an identical one. Casting a
    value to ``T`` and then to ``T`` again is idempotent, so the outer copy is
    removed. We only collapse two *adjacent, token-identical* casts whose type
    is unambiguous (it contains a ``*`` or a recognised type keyword), so a
    call-through-pointer such as ``(x)(x)`` --- which is not a cast --- is never
    touched. General redundant-cast removal (e.g. a cast matching the operand's
    inferred type) needs type information and is out of scope.
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
        for _ in range(64):
            toks = _tok_offsets(code)
            cut = self._first_dup_cast(toks)
            if cut is None:
                break
            lo, hi = cut
            code = code[:lo] + code[hi:]
        return code

    def _first_dup_cast(self, toks: list[Token]):
        n = len(toks)
        for i in range(n):
            if toks[i][0] != "(":
                continue
            cp = _match_delim(toks, i, "(", ")")
            if cp is None or cp + 1 >= n or toks[cp + 1][0] != "(":
                continue
            cp2 = _match_delim(toks, cp + 1, "(", ")")
            if cp2 is None:
                continue
            g1 = [t[0] for t in toks[i + 1 : cp]]
            g2 = [t[0] for t in toks[cp + 2 : cp2]]
            if g1 and g1 == g2 and self._type_like(g1):
                # Remove the first, redundant cast "(T)".
                return toks[i][1], toks[cp][2]
        return None

    @classmethod
    def _type_like(cls, g: list[str]) -> bool:
        if "," in g or "?" in g:
            return False
        return "*" in g or any(t in cls._TYPE_WORDS for t in g)


class InlineSingleUseTemps(Transform):
    """Inline a spill temporary whose only use is the next ``return``.

    Decompilers spill a result into a one-shot variable and return it::

        undefined8 uVar1;   // declaration
        ...
        uVar1 = f();        // sole assignment
        return uVar1;       // sole use

    We fold the adjacent ``uVar1 = f(); return uVar1;`` to ``return f();`` and
    drop the now-dead declaration. The fold fires only when the name occurs
    exactly as often as those roles account for --- assignment + return, plus an
    optional single uninitialised declaration --- so it is provably used nowhere
    else; and because the two statements are adjacent, the initializer keeps its
    position and no evaluation is reordered (safe even if ``f()`` has side
    effects). The whole-input count is deliberately conservative: a name reused
    across functions blocks the fold rather than risking a wrong rewrite. Runs
    before declaration coalescing so the dead declaration is still its own line.
    """

    id = "inline-temps"
    tier = Tier.T2_STRUCTURAL
    description = "Inline a single-use spill temporary into its return."

    _ASSIGN = re.compile(r"^(\s*)([A-Za-z_]\w*)\s*=\s*(.+);\s*$", re.S)
    _RETURN = re.compile(r"^\s*return\s+([A-Za-z_]\w*)\s*;(\s*)$", re.S)
    _DECL = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_ ]*\s+\**(?P<name>[A-Za-z_]\w*)\s*;\s*$")

    def apply(self, code: str) -> str:
        counts: dict[str, int] = {}
        for seg_type, text in scan(code):
            if seg_type == SegmentType.CODE:
                for m in re.finditer(r"[A-Za-z_]\w*", text):
                    counts[m.group(0)] = counts.get(m.group(0), 0) + 1

        pieces = _split_statements(code)
        n = len(pieces)
        keep = [True] * n

        # Standalone single-declarator declarations, by declared name. The
        # leading word must be a real type, not a statement keyword (otherwise
        # `return x;` would parse as a declaration of `x`).
        decls: dict[str, list[int]] = {}
        for idx, p in enumerate(pieces):
            md = self._DECL.match(p)
            # A `volatile` temp's store-then-load is observable, so leave it: not
            # tracking the declaration makes the use-count mismatch and blocks the
            # fold (the variable is preserved rather than inlined away).
            if md and p.split()[0] not in (_STMT_KW | _CTRL_KW) and "volatile" not in p.split():
                decls.setdefault(md.group("name"), []).append(idx)

        i = 0
        while i < n - 1:
            ma = self._ASSIGN.match(pieces[i])
            mr = self._RETURN.match(pieces[i + 1])
            if keep[i] and keep[i + 1] and ma and mr and ma.group(2) == mr.group(1):
                name, expr = ma.group(2), ma.group(3)
                d = decls.get(name, [])
                expected = 2 + (1 if len(d) == 1 else 0)
                # Check for a self-reference in the initializer over CODE only, so
                # the name appearing inside a string literal (`f("uVar1")`) does
                # not spuriously block the fold (the counts above are CODE-only too).
                expr_code = "".join(t for st, t in scan(expr) if st == SegmentType.CODE)
                if counts.get(name, 0) == expected and len(d) <= 1 and not re.search(r"\b" + re.escape(name) + r"\b", expr_code):
                    pieces[i] = f"{ma.group(1)}return {expr.strip()};{mr.group(2)}"
                    keep[i + 1] = False
                    if d:
                        keep[d[0]] = False
                    i += 2
                    continue
            i += 1
        return "".join(p for k, p in enumerate(pieces) if keep[k])


# --- ternary-fold helpers (token-level, string-safe) ---------------------------
def _parse_assign(toks, lo: int, hi: int):
    """If ``toks[lo:hi]`` is a single ``LV = RHS`` (optional trailing ``;``),
    return ``(lv_lo, lv_hi, rhs_lo, rhs_hi)`` token-index spans; else None."""
    if hi > lo and toks[hi - 1][0] == ";":
        hi -= 1
    depth, eq = 0, None
    for j in range(lo, hi):
        t = toks[j][0]
        if t in "([{":
            depth += 1
        elif t in ")]}":
            depth -= 1
        elif depth == 0 and t == ";":
            return None  # more than one statement
        elif depth == 0 and t == "=":
            if eq is not None:
                return None  # chained assignment
            eq = j
    if eq is None or eq == lo or eq + 1 >= hi:
        return None
    return lo, eq, eq + 1, hi


def _branch(toks, start: int):
    """Parse a then/else branch beginning at token ``start``.

    Returns ``(assign_spans_or_None, after_index, end_char)`` where
    ``assign_spans`` is the ``_parse_assign`` tuple for a single-assignment
    branch (braced or bare), or None if the branch is not exactly one assignment.
    """
    n = len(toks)
    if start >= n:
        return None
    if toks[start][0] == "{":
        close = _match_delim(toks, start, "{", "}")
        if close is None:
            return None
        return _parse_assign(toks, start + 1, close), close + 1, toks[close][2]
    depth, j = 0, start
    while j < n:
        t = toks[j][0]
        if t in "([{":
            depth += 1
        elif t in ")]}":
            depth -= 1
        elif depth == 0 and t == ";":
            return _parse_assign(toks, start, j), j + 1, toks[j][2]
        j += 1
    return None


# Top-level tokens that make a ternary fold unsafe in the condition or a branch:
# ``?``/``,`` would change precedence once inlined, and a bare ``=`` in the
# condition (``if (x = y) ...``) is a side-effecting assignment that must run
# unconditionally -- folding it into ``LV = (x = y) ? a : b`` makes it conditional.
# (``==``/``+=``/... are distinct single tokens and remain foldable.)
_TERNARY_UNSAFE = frozenset({"?", ",", "="})
_ASSIGN_OPS = frozenset({"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="})
_COND_UNSAFE = _TERNARY_UNSAFE | _ASSIGN_OPS


class TernaryFromIfElse(Transform):
    """Collapse ``if (C) LV = A; else LV = B;`` into ``LV = C ? A : B;``.

    Both branches must be a single plain assignment to the *same* left-hand
    side (token-identical). This is safe for arbitrary side effects: exactly one
    of ``A``/``B`` is evaluated in either form, ``C`` once, and ``LV`` once, so
    the rewrite preserves evaluation. Branches may be braced or bare. As a
    correctness guard we refuse to fold when ``C``, ``A``, or ``B`` contains a
    top-level ``?`` or ``,`` (whose precedence would change once inlined), which
    also prevents building ambiguous nested ternaries; the condition is
    additionally rejected if it holds a top-level assignment, which binds looser
    than ``?:`` (``if (a = b) ...`` must not become ``x = a = b ? 1 : 2``).
    """

    id = "ternary"
    tier = Tier.T2_STRUCTURAL
    description = "Fold a same-target if/else assignment into a ternary."

    def apply(self, code: str) -> str:
        # Collect every disjoint fold in a single tokenization, then apply them
        # right-to-left so earlier offsets stay valid. Folded branches contain a
        # top-level ``?`` (rejected by ``_TERNARY_UNSAFE``), so a fold never
        # enables an enclosing one; the bounded outer loop is just a safety net
        # and normally converges in one pass. (Collecting the folds in one
        # tokenization keeps this O(n) per pass; re-tokenizing per fold would be
        # O(folds*n), pathological on large decompiled files.)
        for _ in range(64):
            folds = self._folds(code)
            if not folds:
                break
            for lo, hi, new in reversed(folds):
                code = code[:lo] + new + code[hi:]
        return code

    def _folds(self, code: str):
        """All non-overlapping ``if/else`` -> ternary rewrites, left to right."""
        toks = _tok_offsets(code)
        n = len(toks)
        out: list[tuple[int, int, str]] = []
        i = 0
        while i < n:
            if toks[i][0] != "if" or i + 1 >= n or toks[i + 1][0] != "(":
                i += 1
                continue
            cp = _match_delim(toks, i + 1, "(", ")")
            if cp is None or cp <= i + 2:  # need a non-empty condition
                i += 1
                continue
            th = _branch(toks, cp + 1)
            if not th or th[0] is None:
                i += 1
                continue
            then_a, after_then, _ = th
            if after_then >= n or toks[after_then][0] != "else":
                i += 1
                continue
            eb = _branch(toks, after_then + 1)
            if not eb or eb[0] is None:
                i += 1
                continue
            else_a, after_else, end_char = eb

            lv1_lo, lv1_hi, r1_lo, r1_hi = then_a
            lv2_lo, lv2_hi, r2_lo, r2_hi = else_a
            if [t[0] for t in toks[lv1_lo:lv1_hi]] != [t[0] for t in toks[lv2_lo:lv2_hi]]:
                i += 1
                continue
            if (
                _has_top(toks, i + 2, cp, _COND_UNSAFE)
                or _has_top(toks, r1_lo, r1_hi, _TERNARY_UNSAFE)
                or _has_top(toks, r2_lo, r2_hi, _TERNARY_UNSAFE)
            ):
                i += 1
                continue

            cond = code[toks[i + 2][1] : toks[cp - 1][2]].strip()
            lv = code[toks[lv1_lo][1] : toks[lv1_hi - 1][2]].strip()
            a = code[toks[r1_lo][1] : toks[r1_hi - 1][2]].strip()
            b = code[toks[r2_lo][1] : toks[r2_hi - 1][2]].strip()
            out.append((toks[i][1], end_char, f"{lv} = {cond} ? {a} : {b};"))
            i = after_else  # skip the consumed region: keeps folds disjoint
        return out


class CanonicalizeControlFlow(Transform):
    """Canonicalize control flow by cleaning up dead labels and jumps.

    Two safe, CFG-free simplifications that decompiler output invites:

    * **Dead forward jump.** ``goto X;`` immediately followed by the label
      ``X:`` is removed --- control already falls through to ``X``.
    * **Unreferenced label.** A label definition ``X:`` with no remaining
      ``goto X`` anywhere is dropped (keeping the statement it tagged).

    Both are lossless. Full goto-to-structured-control reconstruction needs a
    control-flow graph and is out of scope; these passes only remove jumps and
    labels that provably do nothing.
    """

    id = "cfg-canon"
    tier = Tier.T2_STRUCTURAL
    description = "Remove no-op gotos and unreferenced labels."

    _GOTO = re.compile(r"^\s*goto\s+([A-Za-z_]\w*)\s*;\s*$")
    _LABEL = re.compile(r"^(\s*)([A-Za-z_]\w*)\s*:(?!:)")
    _NON_LABEL = frozenset({"default", "case"})

    def apply(self, code: str) -> str:
        code = self._drop_dead_jumps(code)
        code = self._drop_unreferenced_labels(code)
        return code

    def _drop_dead_jumps(self, code: str) -> str:
        pieces = _split_statements(code)
        out: list[str] = []
        i, n = 0, len(pieces)
        while i < n:
            mg = self._GOTO.match(pieces[i])
            nxt = pieces[i + 1] if i + 1 < n else ""
            ml = self._LABEL.match(nxt.lstrip()) if nxt else None
            if mg and ml and ml.group(2) == mg.group(1):
                i += 1  # skip the redundant goto; keep the labelled statement
                continue
            out.append(pieces[i])
            i += 1
        return "".join(out)

    # A label is referenced by a plain ``goto X`` or by GCC's label-address
    # operator ``&&X`` (computed goto). ``&&`` also spells logical-AND, but
    # over-counting an ``&&`` operand as a label reference is the safe direction:
    # it keeps a label rather than dropping a live one, so a computed goto's target
    # is never orphaned. (Decompilers rarely emit computed gotos, so the only cost
    # is occasionally not dropping a genuinely dead label.)
    _LABEL_REF = re.compile(r"\bgoto\s+([A-Za-z_]\w*)|&&\s*([A-Za-z_]\w*)")

    def _drop_unreferenced_labels(self, code: str) -> str:
        referenced = {g for seg_type, text in scan(code) if seg_type == SegmentType.CODE for m in self._LABEL_REF.finditer(text) for g in m.groups() if g}
        out: list[str] = []
        for piece in _split_statements(code):
            ml = self._LABEL.match(piece)
            if ml and ml.group(2) not in self._NON_LABEL and ml.group(2) not in referenced:
                # Drop the "name:" prefix, keep its leading whitespace + the rest.
                out.append(ml.group(1) + piece[ml.end() :].lstrip())
            else:
                out.append(piece)
        return "".join(out)


# An identifier, a number, and the statement keywords that can legitimately sit
# just before a unary ``*`` deref or that must never be read as an operand value.
_IDENT_RX = re.compile(r"^[A-Za-z_]\w*$")
_NUM_RX = re.compile(r"^(?:0[xX][0-9a-fA-F]+|\d+)$")
_NONVALUE_KW = _CTRL_KW | _STMT_KW


class MinimizeIntegerLiterals(Transform):
    """Re-spell hexadecimal integer literals in the shorter decimal form.

    Decompilers print *every* integer constant in hexadecimal --- loop bounds,
    struct offsets, small counts, ``0`` --- whereas authored C already writes the
    small ones in decimal and reserves hex for masks and addresses. Because the
    hex spelling is the decompiler's habit rather than analyst signal, rewriting
    ``0x10`` to ``16`` is a pure radix change: the numeric value, and therefore the
    meaning, is identical, so this is a lossless (T2) rewrite that a source-code
    reformatter would never have occasion to make.

    The rewrite is self-selecting and fires only where it *shrinks* the text: it
    converts a hex literal to decimal exactly when the decimal spelling has fewer
    characters (``0x10`` -> ``16``, ``0xff`` -> ``255``, ``0xffff`` -> ``65535``),
    and leaves it as hex otherwise (``0xffffff`` -> ``16777215`` is no shorter;
    ``0xffffffff`` -> ``4294967295`` is no shorter), so the wider bitmasks --- where
    the hex grouping carries a visual cue --- keep their hex form. (The 8- and
    16-bit round masks ``0xff``/``0xffff`` are short enough in decimal to convert;
    the lost hex grouping is a minor readability trade for a strictly lossless
    radix change.) The character count is the tokenizer-independent surrogate the
    tool optimizes (the design is model-agnostic); fewer characters do not
    *guarantee* fewer tokens under an arbitrary vocabulary, but for typical LLM
    tokenizers this is the single largest lossless lever in decompiler output.

    Only values that fit in a signed ``int`` (``<= 0x7fffffff``) are converted, so
    the literal's *type* is unchanged: for such values the decimal and hexadecimal
    spellings (with any shared ``u``/``l`` suffix) denote the same ``int``/
    ``unsigned`` type, whereas a value in ``(INT_MAX, UINT_MAX]`` would be
    ``unsigned int`` in hex but ``long`` in decimal. Larger values are also where
    hex is already the shorter spelling, so the type guard costs no savings. Any
    integer-suffix token (``0x10u`` -> ``16u``) is left attached untouched.
    Operates on CODE segments only, so hex inside strings/comments is never
    rewritten.
    """

    id = "int-minform"
    tier = Tier.T2_STRUCTURAL
    description = "Re-spell a hex literal in decimal when shorter."

    _HEX = re.compile(r"^0[xX][0-9a-fA-F]+$")
    _INT_MAX = 0x7FFFFFFF

    def apply(self, code: str) -> str:
        edits: list[tuple[int, int, str]] = []
        for text, start, end in _tok_offsets(code):
            if not self._HEX.match(text):
                continue
            # A hex-float literal (`0x1f.0p3`, `0x1fp3`) tokenizes as a hex head
            # followed adjacently by `.`/`p`/`P`; re-spelling the head in decimal
            # would change the value, so leave any hex token in that position.
            if end < len(code) and code[end] in ".pP":
                continue
            value = int(text, 16)
            if value > self._INT_MAX:
                continue  # wider than int: decimal would change the literal's type
            dec = str(value)
            if len(dec) < len(text):
                edits.append((start, end, dec))
        if not edits:
            return code
        # Single forward pass: a hex-heavy file yields thousands of edits, so the
        # naive slice-per-edit rebuild would be quadratic.
        out: list[str] = []
        last = 0
        for lo, hi, rep in edits:
            out.append(code[last:lo])
            out.append(rep)
            last = hi
        out.append(code[last:])
        return "".join(out)


class DerefOffsetToIndex(Transform):
    """Rewrite a dereferenced pointer-add ``*(p + N)`` to the index form ``p[N]``.

    ``*(p + n)`` and ``p[n]`` are identical in C for any pointer ``p`` and integer
    ``n``, so Binary Ninja's pointer-arithmetic spelling of an array/field read
    (``*(ji + 8)``, ``*(&mw + 0xc)``) is rewritten to the shorter, equivalent
    subscript form. Authored C writes ``p[n]`` directly; the explicit-add spelling
    is a decompiler lowering, so this is a lossless (T2) rewrite.

    Two guards keep it sound. The ``*`` must be a *unary* dereference, never the
    binary multiply: we rewrite only when the token before ``*`` is not a value
    (so ``a * (b + c)`` is left alone but ``= *(p + 4)`` is rewritten), the same
    unary-position test the address-of and null-cast passes use. And the token
    *after* the closing ``)`` must not be a postfix operator (``.``/``->``/``(``/
    ``[``/``++``/``--``), since those bind tighter than the prefix ``*`` and would
    re-associate against the new subscript. The base must be a single identifier
    (optionally address-of ``&x``, which is parenthesised as ``(&x)[N]`` to keep
    its precedence) and the offset a single integer literal.
    """

    id = "deref-offset"
    tier = Tier.T2_STRUCTURAL
    description = "Rewrite a dereferenced pointer-add as a subscript."

    # Tokens after which a ``*`` is the binary multiply, not a unary dereference.
    # A postfix ``++``/``--`` ends an operand (``x++ * (p + 4)`` is a multiply of
    # ``x++`` by ``(p + 4)``), so it counts as a value here. This also declines the
    # mirror prefix case ``++*(p + 4)`` --- which a unary deref *could* rewrite ---
    # because the two are textually indistinguishable; declining is the lossless
    # direction (a missed rewrite, never a wrong one).
    _VALUE_BEFORE = frozenset({")", "]", "++", "--"})
    # Postfix operators bind tighter than prefix ``*``; if one follows the ``)``
    # the rewrite would change associativity, so we decline.
    _BLOCK_AFTER = frozenset({".", "->", "(", "[", "++", "--"})

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int, str]] = []
        i = 0
        while i < n:
            if toks[i][0] == "*" and i + 1 < n and toks[i + 1][0] == "(":
                prev = toks[i - 1][0] if i > 0 else None
                is_value = prev is not None and (prev in self._VALUE_BEFORE or _NUM_RX.match(prev) or (_IDENT_RX.match(prev) and prev not in _NONVALUE_KW))
                if not is_value:
                    close = _match_delim(toks, i + 1, "(", ")")
                    if close is not None:
                        rep = self._index_form([t[0] for t in toks[i + 2 : close]])
                        after = toks[close + 1][0] if close + 1 < n else None
                        if rep is not None and after not in self._BLOCK_AFTER:
                            edits.append((toks[i][1], toks[close][2], rep))
                            i = close + 1
                            continue
            i += 1
        for lo, hi, rep in reversed(edits):
            code = code[:lo] + rep + code[hi:]
        return code

    @staticmethod
    def _index_form(inner: list[str]) -> str | None:
        """Return ``base[off]`` for an inner ``IDENT + NUM`` / ``& IDENT + NUM``."""
        if len(inner) == 3 and _IDENT_RX.match(inner[0]) and inner[0] not in _NONVALUE_KW and inner[1] == "+" and _NUM_RX.match(inner[2]):
            return f"{inner[0]}[{inner[2]}]"
        if len(inner) == 4 and inner[0] == "&" and _IDENT_RX.match(inner[1]) and inner[1] not in _NONVALUE_KW and inner[2] == "+" and _NUM_RX.match(inner[3]):
            return f"(&{inner[1]})[{inner[3]}]"
        return None


class DropTrailingReturn(Transform):
    """Drop a redundant ``return;`` at the very end of a function body.

    A bare ``return;`` as the last statement before a function's closing brace is
    a no-op: control falls off the end either way. Ghidra emits one at the end of
    every ``void`` function. We delete the ``return;`` only when its ``;`` is
    immediately followed by the ``}`` that closes a *function body* (the brace that
    returns the brace depth to zero), never a nested block --- a ``return;`` ending
    a loop or ``if`` body exits the whole function early and is not redundant.
    Lossless (T2): the statement does nothing the implicit fall-through does not.
    """

    id = "drop-trailing-return"
    tier = Tier.T2_STRUCTURAL
    description = "Drop a redundant trailing return at the end of a function body."

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        depth = 0
        edits: list[tuple[int, int]] = []
        for j, (t, _s, _e) in enumerate(toks):
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
                # A function body closes when the depth returns to 0. If the two
                # tokens it closes over are exactly `return ;`, that return is the
                # redundant fall-off-the-end statement.
                # ... unless the `return` is the sole statement of a label
                # (`done: return; }`): dropping it would leave `done: }`, a label
                # with no statement (invalid C before C23), so keep it.
                if depth == 0 and j >= 2 and toks[j - 1][0] == ";" and toks[j - 2][0] == "return" and not (j >= 3 and toks[j - 3][0] == ":"):
                    edits.append((toks[j - 2][1], toks[j - 1][2]))
        for lo, hi in reversed(edits):
            code = code[:lo] + code[hi:]
        return code
