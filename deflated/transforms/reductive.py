"""T4 --- reductive, lossy transforms (analyst signal and boilerplate).

These discard information that is *genuine* rather than synthesized, but of low
value for our tasks: decompiler warning banners, ABI keywords, qualifiers and
pseudo-width casts, plus whole boilerplate bodies (forwarding thunks, resolver
stubs, CRT scaffolding). Unlike T3, what is dropped here is not recoverable from
the remaining text.
"""

from __future__ import annotations

import re
from collections import Counter

from .base import Tier, Transform
from .contextual import _IDENT, _RESERVED
from .ctokens import CINT, CNUMBER, ctokenize as _tok_offsets, match_delimiter as _match_delim, split_args as _split_args
from .lexer import SegmentType, scan


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
_WCAST_IDENT = re.compile(r"[A-Za-z_]\w*")
# Bit widths of the pseudo-width types, for the literal-narrowing guard in
# :class:`StripWidthCasts`: stripping `(_DWORD)` off a literal that does not fit
# the cast width (or any float literal) would truncate it and change the value.
_WIDTH_BITS = {"_BYTE": 8, "_WORD": 16, "_DWORD": 32, "_QWORD": 64, "_OWORD": 128}


class StripWidthCasts(Transform):
    """Drop Hex-Rays pseudo-width narrowing casts in value position.

    Hex-Rays litters expressions with explicit width casts to its own pseudo-
    width *types* (``(_BYTE)``, ``(_WORD)``, ``(_DWORD)``, ``(_QWORD)``,
    ``(_OWORD)``) --- spellings that do not exist in hand-written C, so they are
    pure artifacts of mapping fixed-width x86 operations back to source. We drop
    the cast (``(_BYTE)gv`` -> ``gv``) where it sits in value position, keeping
    the operand and the surrounding operation.

    This is not value-preserving, and it is not merely the loss of a hint: the
    cast performs a real truncation. ``(_BYTE)eax == 0`` asks whether the low
    byte is zero, ``eax == 0`` asks about all 32 bits, and the two disagree for
    every ``eax`` whose high bits are set. We accept that because the width is
    usually an artifact of instruction selection rather than of the original
    source, and because the operand's declared type still lets a reader recover
    the intended reading --- a trade of fidelity for brevity that belongs in T4
    alongside the other genuine-signal reductions, and never in a lossless tier.

    Only the exact shape ``( <pseudo-width-type> )`` followed by an operand start
    is removed. A pointer cast (``(_BYTE *)p`` --- a real reinterpretation whose
    access width is load-bearing) keeps its ``*`` and is never matched; and
    ``sizeof(_QWORD)`` or a call ``f(_QWORD)`` is excluded by the value-position
    guard, so no operator-bearing or size-of context is ever touched. A cast on
    a *literal* that the width would narrow is also left in place: stripping
    ``(_DWORD)0x123456789`` would turn one constant into a different constant
    (and a float operand always truncates). That guard is not what makes the
    pass safe --- per above, it isn't safe --- it only excludes the one shape
    where nothing left on the page could tell a reader what the value was meant
    to be, unlike a variable whose declaration still carries the width.
    Decompiler output never puts a width cast on a literal anyway (the operand
    is always a recovered variable/expression), so the guard is defensive.

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
                if self._operand_starts(after) and not self._prev_is_value(prev) and self._literal_safe(toks[i + 1][0], toks, i + 3, n):
                    cuts.append((toks[i][1], toks[i + 2][2]))
                    i += 3
                    continue
            i += 1
        for lo, hi in reversed(cuts):
            code = code[:lo] + code[hi:]
        return code

    @classmethod
    def _literal_safe(cls, cast_type: str, toks, j: int, n: int) -> bool:
        """Whether dropping ``(<cast_type>)`` is permitted for the operand beginning
        at token index ``j`` (or ``j >= n`` when the cast ends the input).

        A *narrowing* width cast on a literal can change the value: an integer
        literal wider than the cast truncates, and a float (``1.5``, ``1e3``,
        ``0x1.8p3``) always truncates. We look past a single leading
        unary ``+``/``-``/``~`` and unwrap a parenthesised lone literal, so
        ``(_BYTE)-1`` (== 255, not -1), ``(_BYTE)~0`` (== 255), and
        ``(_BYTE)(0x1ff)`` (== 255) are all recognised as narrowing and declined.

        Variables and multi-token sub-expressions are not scrutinised, which is a
        policy and not a safety proof: ``(_BYTE)eax`` -> ``eax`` can change the
        value exactly as a narrowed literal does. The difference is recoverability
        --- the variable's declaration still states the width, while a rewritten
        constant leaves no trace of the original --- so the class accepts the
        former as its T4 trade and this guard declines the latter.
        """
        if j >= n:
            return True
        tok = toks[j][0]
        # Unwrap a parenthesised lone literal: ``(LIT)`` narrows exactly as ``LIT``
        # would; a multi-token expression in parens falls under the same trade as
        # a bare variable, so allow it.
        if tok == "(":
            close = _match_delim(toks, j)
            if close == j + 2:
                return cls._literal_safe(cast_type, toks, j + 1, n)
            return True
        # A leading unary sign/complement. ``+LIT`` keeps the value; ``-LIT``/``~LIT``
        # of an integer literal become a large positive under the unsigned width
        # truncation (and ``-`` of a float literal truncates anyway), so the value
        # always changes -> decline. On a variable the whole operand is an
        # expression, which this guard does not police.
        if tok in ("+", "-", "~"):
            if j + 1 < n and CNUMBER.fullmatch(toks[j + 1][0]):
                return cls._literal_safe(cast_type, toks, j + 1, n) if tok == "+" else False
            return True
        if not CNUMBER.fullmatch(tok):
            return True  # not a literal: existing (lossy) behaviour
        # ``CINT``, not ``CNUMBER``: the narrowing guard below reasons about an
        # integer value against a bit width, so a float literal operand must not
        # reach it --- truncating one always changes the value, so decline.
        m = CINT.fullmatch(tok)
        if m is None:
            return False
        bits = _WIDTH_BITS.get(cast_type)
        if bits is None:
            return True
        digits = m.group(1)
        value = int(digits, 16) if digits[:2].lower() == "0x" else int(digits, 10)
        return value < (1 << bits)

    @staticmethod
    def _operand_starts(tok: str | None) -> bool:
        if tok is None:
            return False
        return bool(tok in _OPERAND_START_OPS or _WCAST_IDENT.fullmatch(tok) or CNUMBER.fullmatch(tok) or tok[0] in "\"'")

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
        return bool(prev in {")", "]"} or CNUMBER.fullmatch(prev) or (_WCAST_IDENT.fullmatch(prev) and prev not in _CAST_PREV_KW))


class StripCallingConventions(Transform):
    """Remove decompiler-emitted calling-convention and attribute keywords.

    IDA/Hex-Rays and Binary Ninja annotate signatures and function-pointer casts
    with ABI keywords (``__cdecl``, ``__thiscall``, ``__fastcall``,
    ``__stdcall``) and attributes (``__noreturn``, ``__pure``, and IDA's
    ``__hidden`` marking an implicit ``this``). Each is two to
    four tokens of pure boilerplate that an LLM rarely needs for analysis, and
    they recur on nearly every function in C++-heavy output. Dropping them
    discards a genuine, non-recoverable ABI hint (not mere bookkeeping), so the
    transform is gated at the reductive tier (T4), above placeholder compression.

    The keyword plus one run of surrounding spaces is replaced by a single space
    (``int __fastcall f(...)`` -> ``int f(...)``; ``(__cdecl *)`` -> ``( *)``),
    which the cosmetic passes then tighten. String/char/comment regions are
    protected by the scanner, and ``\\b`` anchors keep identifiers such as
    ``my__cdecl`` or ``__cdecl_table`` untouched.
    """

    id = "strip-callconv"
    tier = Tier.T4_REDUCTIVE
    description = "Remove calling-convention and ABI keywords."

    KEYWORDS = (
        "cdecl",
        "thiscall",
        "fastcall",
        "stdcall",
        "vectorcall",
        "usercall",
        "userpurge",
        "noreturn",
        "pure",
        "hidden",
    )

    def __init__(self) -> None:
        self._rx = re.compile(r" *\b__(?:" + "|".join(self.KEYWORDS) + r")\b *")

    def apply(self, code: str) -> str:
        return "".join((self._rx.sub(" ", t) if seg_type == SegmentType.CODE else t) for seg_type, t in scan(code))


class StripConstQualifier(Transform):
    r"""Remove the ``const`` type qualifier.

    Binary Ninja sprinkles recovered ``const`` widely (``char const *``,
    ``void *const``, top-level ``const`` on parameters). Each is a single token of
    low-signal type decoration: it constrains nothing an analyst reading
    decompiler output relies on, and it recurs on most pointer parameters. We
    drop the keyword (and one run of surrounding spaces, which the cosmetic passes
    then tighten), e.g. ``char const *msgid`` -> ``char *msgid``. Dropping a
    genuine (if low-value) qualifier is reductive, hence T4 alongside
    ``strip-callconv`` --- the same flavour of removing recovered type/ABI
    decoration. ``\b`` anchors keep identifiers such as ``const_table`` untouched,
    and the scanner protects string/char/comment regions.
    """

    id = "strip-const"
    tier = Tier.T4_REDUCTIVE
    description = "Remove the low-signal const Binary Ninja recovers on most pointer parameters."

    _RX = re.compile(r" *\bconst\b *")

    def apply(self, code: str) -> str:
        return "".join((self._RX.sub(" ", t) if seg_type == SegmentType.CODE else t) for seg_type, t in scan(code))


class StripChkSuffix(Transform):
    r"""Strip glibc's ``_chk`` FORTIFY suffix, restoring the familiar libc name.

    ``_FORTIFY_SOURCE`` rewrites ``printf`` -> ``__printf_chk``,
    ``memcpy`` -> ``__memcpy_chk``, and so on; the decompiler surfaces the
    hardened spelling verbatim. The ``__``/``_chk`` decoration is a build-flag
    artifact, so where it is safe we drop it (``__printf_chk`` -> ``printf``,
    ``_snprintf_chk`` -> ``snprintf``); only the "built with FORTIFY" hint is
    lost, hence the reductive tier (T4).

    Crucially, the rewrite fires *only on an empty-argument occurrence*
    (``NAME ( )``). The FORTIFY wrappers do **not** share the base function's
    argument list --- ``__printf_chk(int flag, const char *fmt, ...)`` has a
    leading ``flag``, and ``__snprintf_chk(s, n, flag, slen, fmt, ...)`` two extra
    arguments --- so renaming a *call that carries arguments* would shift the
    FORTIFY ``flag``/``slen`` into a real operand position (e.g.
    ``__printf_chk(1, "%d", x)`` would become ``printf(1, "%d", x)``, with ``1`` in
    the format slot). A plain token rename cannot fix the argument list, so an
    argument-bearing call is left untouched. The empty-argument form is exactly
    what matters in practice: Hex-Rays emits ``_chk`` call sites with the varargs
    dropped (``__printf_chk()``), and every decompiler emits the empty-argument
    forwarder ``i64 __snprintf_chk(){return _snprintf_chk();}``.

    Renaming both empty-argument halves of that forwarder turns it into a
    self-call ``i64 snprintf(){return snprintf();}``, which ``thunk-elision``
    (running after this pass) reduces to the bare prototype --- so this pass also
    clears the empty-argument ``_chk`` forwarders that neither ``thunk-elision``
    nor ``drop-resolver-stubs`` caught on their own.

    The ``_chk`` must sit at a word boundary, so genuine multi-segment symbols
    such as ``__stack_chk_fail`` (``_chk`` is followed by ``_fail``) never match.
    The base name (between the leading underscores and ``_chk``) must be in the
    fixed set of glibc ``_FORTIFY_SOURCE`` wrappers below, so a coincidental
    application symbol such as ``_my_chk`` is left untouched.
    """

    id = "strip-chk"
    tier = Tier.T4_REDUCTIVE
    description = "Strip glibc's _chk FORTIFY suffix."

    # glibc _FORTIFY_SOURCE-wrapped functions (the base name only). Restricting to
    # this fixed vocabulary makes the strip provably collision-free.
    _FORTIFY_BASES = frozenset(
        {
            # stdio / printf family
            "printf",
            "fprintf",
            "dprintf",
            "sprintf",
            "snprintf",
            "asprintf",
            "obstack_printf",
            "vprintf",
            "vfprintf",
            "vdprintf",
            "vsprintf",
            "vsnprintf",
            "vasprintf",
            "obstack_vprintf",
            "fwprintf",
            "wprintf",
            "swprintf",
            "vfwprintf",
            "vwprintf",
            "vswprintf",
            # mem / str
            "memcpy",
            "memmove",
            "mempcpy",
            "memset",
            "bcopy",
            "bzero",
            "explicit_bzero",
            "stpcpy",
            "stpncpy",
            "strcat",
            "strcpy",
            "strncat",
            "strncpy",
            "wmemcpy",
            "wmemmove",
            "wmempcpy",
            "wmemset",
            "wcscpy",
            "wcpcpy",
            "wcscat",
            "wcsncat",
            "wcsncpy",
            "wcpncpy",
            # io / system
            "gets",
            "fgets",
            "fgets_unlocked",
            "fread",
            "fread_unlocked",
            "getcwd",
            "getwd",
            "getdomainname",
            "getgroups",
            "gethostname",
            "getlogin_r",
            "pread",
            "pread64",
            "read",
            "readlink",
            "readlinkat",
            "realpath",
            "recv",
            "recvfrom",
            "ttyname_r",
            "ptsname_r",
            "confstr",
            "poll",
            "ppoll",
            "wctomb",
            "mbstowcs",
            "wcstombs",
            "mbsrtowcs",
            "wcsrtombs",
            "mbsnrtowcs",
            "wcsnrtombs",
            "syslog",
            "vsyslog",
        }
    )

    # One or two leading underscores, a lazy body, then the ``_chk`` boundary.
    _RX = re.compile(r"_{1,2}(\w+?)_chk")

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int, str]] = []
        for i, (text, start, end) in enumerate(toks):
            m = self._RX.fullmatch(text)
            if not m or m.group(1) not in self._FORTIFY_BASES:
                continue
            # Only an empty-argument occurrence `NAME ( )` is safe to rename: a
            # call carrying arguments would leave the FORTIFY flag/slen in a real
            # operand position (see the class docstring).
            if i + 2 < n and toks[i + 1][0] == "(" and toks[i + 2][0] == ")":
                edits.append((start, end, m.group(1)))
        for lo, hi, rep in reversed(edits):
            code = code[:lo] + rep + code[hi:]
        return code


class StripTranslationWrappers(Transform):
    """Unwrap libc i18n calls, keeping only the message string.

    Decompiled coreutils wraps nearly every user-facing string in a ``gettext``
    family call (Binary Ninja emits ``dcgettext(0, "msg", 5)`` thousands of times
    per file). The wrapper is a translation lookup at runtime; for static reading
    the analyst-relevant part is the message, so we replace the whole call with
    its message-id argument (``dcgettext(0, "msg", 5)`` -> ``"msg"``).

    Lossy (the translation-domain/category arguments and the call itself are
    discarded), so it is gated at the reductive tier. The replacement is taken
    verbatim from the source, so a string-literal message keeps its exact bytes;
    a non-literal message id (a variable) is simply unwrapped to that variable.
    A call is rewritten only when its argument count matches the function's known
    arity and it is not a member access (``p->gettext(...)``).
    """

    id = "strip-i18n"
    tier = Tier.T4_REDUCTIVE
    description = "Unwrap a gettext-family lookup to its message string."

    # name -> (arity, 0-based index of the message-id argument to keep).
    WRAPPERS = {
        "gettext": (1, 0),
        "dgettext": (2, 1),
        "dcgettext": (3, 1),
    }

    def apply(self, code: str) -> str:
        # A pass rewrites only outermost calls (it skips past each match), so a
        # nested wrapper `dcgettext(0, gettext("x"), 5)` peels one level per pass;
        # iterate to a fixed point. Bounded loop is a safety net (normally <=2).
        for _ in range(64):
            new = self._unwrap_once(code)
            if new == code:
                break
            code = new
        return code

    # Keywords that may precede a *call* used as an expression/statement, so a
    # preceding identifier here does not mark a declarator.
    _CALL_PREV_KW = frozenset({"return", "else", "do"})

    def _unwrap_once(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int, str]] = []
        i = 0
        while i < n - 1:
            spec = self.WRAPPERS.get(toks[i][0])
            if spec and toks[i + 1][0] == "(":
                prev = toks[i - 1][0] if i > 0 else None
                close = _match_delim(toks, i + 1)
                # Skip a member access (`p->gettext(...)`) and a declarator (a
                # gettext *prototype/definition* such as
                # `char *dcgettext(const char *a, const char *msgid, int c) {` is
                # not a call): the name in declarator position is preceded by a
                # return type (`*` or a type/identifier word, not a call-prev
                # keyword), or the `)` is immediately followed by a `{` body.
                is_member = prev in (".", "->")
                is_declarator = prev == "*" or (prev is not None and _IDENT.fullmatch(prev) and prev not in self._CALL_PREV_KW)
                is_def = close is not None and close + 1 < n and toks[close + 1][0] == "{"
                if close is not None and not is_member and not is_declarator and not is_def:
                    arity, keep = spec
                    args = _split_args(toks, i + 1)
                    if args is not None and len(args) == arity:
                        lo_t, hi_t = args[keep]
                        if lo_t < hi_t:
                            msg = code[toks[lo_t][1] : toks[hi_t - 1][2]].strip()
                            edits.append((toks[i][1], toks[close][2], msg))
                            i = close + 1
                            continue
            i += 1
        for lo, hi, rep in reversed(edits):
            code = code[:lo] + rep + code[hi:]
        return code


class ElideThunkBodies(Transform):
    """Collapse a pure forwarding-thunk function definition to a prototype.

    Every decompiler emits, as a full function definition, a trampoline per
    imported libc symbol whose body carries no information beyond the signature
    it already states. Two families dominate and are recognised here by *shape*
    (not by a comment or name, so detection survives comment-stripping at T2 and
    name compression at T3):

    * **Self-call thunk** (Hex-Rays, Binary Ninja): the body is exactly
      ``return strncmp(s1, s2, n);`` --- a call to the function's own name. In
      authored C this is infinite recursion; in decompiler output it is always
      the PLT import thunk.
    * **Indirect import thunk** (Ghidra): the body's sole action is one call
      through a ``PTR_<symbol>`` global, e.g.
      ``(*(code *)PTR_free_001...)();`` (optionally storing the result in a
      temporary and returning it).
    * **Bad-instruction stub** (Ghidra): the body is exactly the sentinel
      ``halt_baddata();`` --- Ghidra's marker for an imported symbol it could not
      disassemble (preceded by a ``/* WARNING: Bad instruction ... */`` banner,
      already stripped at T4). The recovered import prototype is kept; the
      give-up marker is dropped.
    * **Pure passthrough forwarder** (Binary Ninja): the body is a single
      ``return worker(a, b);`` delegating to *another* function with the
      forwarder's own parameters passed verbatim and in order --- a degenerate
      tail-call alias carrying nothing beyond "calls worker". This case is gated
      two ways: a *family guard* (collapse only when at least two such functions
      forward to the same worker, mirroring ``drop-resolver-stubs``), and a
      *verbatim-argument guard* --- the forwarded arguments must be exactly the
      parameters. The second guard is what keeps real code alive: a forwarder
      whose arguments differ (a baked-in constant ``worker(x, 0xa)`` vs
      ``worker(x, 0)`` --- two argument parsers; a dereference/reorder
      ``strcmp(*a, *b)`` vs ``strcmp(*b, *a)`` --- a forward vs reverse
      comparator; any nested expression) carries distinguishing semantics in those
      arguments, so its body is genuine logic and is preserved. The non-empty
      argument list distinguishes these from the empty-argument resolver stubs that
      ``drop-resolver-stubs`` removes.

    The self-call, indirect, and bad-instruction shapes are rewritten to the
    signature alone (``int strncmp(char *s1, char *s2, size_t n);``), which keeps
    the one recovered datum --- the symbol and its parameter types --- and drops
    the mechanical body. Reductive (hence T4): the indirect-call/PLT detail, the
    forwarded constant, and the body are discarded.

    The match is deliberately strict. A function is collapsed only when its body
    is a single qualifying call, optionally preceded by one bare temporary
    declaration and followed by ``return``/``return <tmp>``, and contains *no*
    control flow (``if``/``for``/``while``/...) and no second statement.
    """

    id = "thunk-elision"
    tier = Tier.T4_REDUCTIVE
    description = "Collapse a forwarding import trampoline to its prototype."

    # Body containing any of these is real logic, never a pure forwarding thunk.
    _CTRL = frozenset({"if", "else", "for", "while", "switch", "case", "do", "goto", "default"})
    # Decompiler give-up markers whose sole-call body is a thunk to collapse.
    _SENTINELS = frozenset({"halt_baddata"})
    # A delegator to a *different* function is collapsed only when at least this
    # many of them forward to the same worker (the trampoline-fan signature).
    _MIN_FORWARD_FAMILY = 2

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        funcs = _top_level_functions(toks)
        if not funcs:
            return code
        edits: list[tuple[int, int]] = []
        forwarders: dict[int, str] = {}  # func index -> worker it delegates to
        for k, (name, _ss, bo, bc, _bce) in enumerate(funcs):
            body = [x[0] for x in toks[bo + 1 : bc]]
            if self._is_thunk_body(body, name=name):
                edits.append((toks[bo][1], toks[bc][2]))
            else:
                callee = self._forward_callee(body, name, self._param_names(toks, bo))
                if callee is not None:
                    forwarders[k] = callee
        # Family guard: only collapse delegators that share a worker with a peer.
        family = Counter(forwarders.values())
        for k, callee in forwarders.items():
            if family[callee] >= self._MIN_FORWARD_FAMILY:
                _name, _ss, bo, bc, _bce = funcs[k]
                edits.append((toks[bo][1], toks[bc][2]))
        for lo, hi in sorted(edits, reverse=True):
            code = code[:lo] + ";" + code[hi:]
        return code

    def _is_thunk_body(self, body: list[str], *, name: str) -> bool:
        if not body or any(w in self._CTRL for w in body):
            return False
        decl = call = ret = None
        for stmt in self._split_semis(body):
            if not stmt:
                continue
            if "(" in stmt:
                if call is not None:
                    return False  # more than one call statement
                call = stmt
            elif stmt[0] == "return":
                if ret is not None or len(stmt) > 2 or (len(stmt) == 2 and not _IDENT.fullmatch(stmt[1])):
                    return False
                ret = stmt
            else:
                if decl is not None or not self._is_simple_decl(stmt):
                    return False
                decl = stmt
        return call is not None and self._is_forward_call(call, name)

    @staticmethod
    def _split_semis(body: list[str]) -> list[list[str]]:
        """Split a body token list into statements at depth-0 ``;``."""
        out: list[list[str]] = []
        cur: list[str] = []
        depth = 0
        for tok in body:
            if tok in "([{":
                depth += 1
            elif tok in ")]}":
                depth -= 1
            if tok == ";" and depth == 0:
                out.append(cur)
                cur = []
            else:
                cur.append(tok)
        if cur:
            out.append(cur)
        return out

    @staticmethod
    def _is_simple_decl(stmt: list[str]) -> bool:
        """A bare temp declaration: ``TYPE ident`` optionally ``= <number>``."""
        if "(" in stmt or len(stmt) < 2:
            return False
        if "=" in stmt:
            eq = stmt.index("=")
            # exactly `... ident = <single literal>`
            return eq == len(stmt) - 2 and _IDENT.fullmatch(stmt[eq - 1]) is not None
        return _IDENT.fullmatch(stmt[-1]) is not None

    def _is_forward_call(self, call: list[str], name: str) -> bool:
        c = call[:]
        if c and c[0] == "return":
            c = c[1:]
        # strip a leading `tmp =` (the returning-temp Ghidra shape)
        if len(c) >= 2 and _IDENT.fullmatch(c[0]) and c[1] == "=":
            c = c[2:]
        c = self._strip_leading_casts(c)
        if len(c) < 3:
            return False
        # Bad-instruction sentinel: `halt_baddata ( ... )` spanning to the end.
        if c[0] in self._SENTINELS and c[1] == "(" and self._spans_to_end(c, 1):
            return True
        # Self-call: `name ( ...args... )` spanning to the end.
        if c[0] == name and c[1] == "(" and self._spans_to_end(c, 1):
            return True
        # Indirect import thunk: `( *...PTR_... ) ( ...args... )` to the end.
        if c[0] == "(":
            g = self._match(c, 0)
            if g is None or g + 1 >= len(c) or c[g + 1] != "(":
                return False
            group = c[1:g]
            return "*" in group and any(tok.startswith("PTR_") for tok in group) and self._spans_to_end(c, g + 1)
        return False

    def _forward_callee(self, body: list[str], name: str, params: list[str] | None) -> str | None:
        """Worker delegated to by a *pure passthrough* family-forwarder, else None.

        Recognises a body that is exactly ``return WORKER(args);`` where ``WORKER``
        is a bare identifier other than the function itself (so it is not a
        self-call thunk), is not a ``PTR_`` indirect call, and -- crucially -- the
        forwarded ``args`` are exactly the function's own parameters ``params``,
        verbatim and in order.

        That last condition is the narrowing that keeps this from deleting real
        code. A forwarder whose arguments are anything *other* than its parameters
        passed straight through carries distinguishing semantics in those
        arguments, so its body is not mechanical: a baked-in constant
        (``f(x,0xa,..)`` vs ``f(x,0,..)`` -- two different argument parsers), a
        dereference or reordering (``strcmp(*a,*b)`` vs ``strcmp(*b,*a)`` -- a
        forward vs reverse comparator), or any nested expression all distinguish
        the function from its siblings, and collapsing it to a bare prototype would
        erase that meaning. Only the degenerate ``T f(a,b){return g(a,b);}``
        tail-call trampoline -- a true alias carrying nothing beyond "calls g" --
        is collapsed. The empty-argument resolver stubs are ``drop-resolver-stubs``'
        job. The caller applies the family guard.
        """
        if params is None or not body or any(w in self._CTRL for w in body):
            return None
        stmts = [s for s in self._split_semis(body) if s]
        if len(stmts) != 1:
            return None
        s = stmts[0]
        if len(s) < 5 or s[0] != "return" or s[2] != "(":
            return None
        callee = s[1]
        if not _IDENT.fullmatch(callee) or callee == name or callee in _RESERVED or callee.startswith("PTR_"):
            return None
        c = s[1:]  # `WORKER ( ...args... )`
        close = self._match(c, 1)
        # Must span the whole statement and carry at least one argument.
        if close is None or close != len(c) - 1 or close <= 2:
            return None
        # Pure-passthrough guard: the forwarded arguments must be exactly this
        # function's parameters, verbatim and in order. Anything else (a constant,
        # a dereference, a reorder, a nested call) is distinguishing semantics.
        arg_lists = self._split_top_commas(c[2:close])
        arg_idents = [a[0] if len(a) == 1 and _IDENT.fullmatch(a[0]) else None for a in arg_lists]
        if not params or arg_idents != params:
            return None
        return callee

    @staticmethod
    def _param_names(toks: list, bo: int) -> list[str] | None:
        """Parameter names of the function whose body opens at token index ``bo``.

        Returns the last identifier of each top-level, comma-separated parameter
        (``const char **a1`` -> ``a1``), ``[]`` for a ``(void)`` list, or None if
        the parameter list cannot be located (an unusual declarator), in which case
        the caller declines to collapse -- the conservative direction.
        """
        j = bo - 1
        while j >= 0 and toks[j][0] != ")":
            j -= 1
        if j < 0:
            return None
        depth, k = 0, j
        while k >= 0:
            t = toks[k][0]
            if t == ")":
                depth += 1
            elif t == "(":
                depth -= 1
                if depth == 0:
                    break
            k -= 1
        if k < 0:
            return None
        inner = [x[0] for x in toks[k + 1 : j]]
        names: list[str] = []
        for param in ElideThunkBodies._split_top_commas(inner):
            ids = [t for t in param if _IDENT.fullmatch(t)]
            if ids:
                names.append(ids[-1])
        return [] if names == ["void"] else names

    @staticmethod
    def _split_top_commas(toks: list[str]) -> list[list[str]]:
        """Split a flat token-string list on top-level ``,`` (``()[]{}``-aware)."""
        out: list[list[str]] = []
        depth = 0
        cur: list[str] = []
        for t in toks:
            if t in "([{":
                depth += 1
            elif t in ")]}":
                depth -= 1
            elif t == "," and depth == 0:
                out.append(cur)
                cur = []
                continue
            cur.append(t)
        if cur or out:
            out.append(cur)
        return out

    @classmethod
    def _strip_leading_casts(cls, c: list[str]) -> list[str]:
        """Drop leading ``( type-spelling )`` casts (identifiers and ``*`` only)."""
        while len(c) > 1 and c[0] == "(":
            close = cls._match(c, 0)
            if close is None or close == len(c) - 1:
                break  # this paren is the call's own arg list, not a cast
            inner = c[1:close]
            # A cast's inner is a type spelling: identifiers/keywords then `*`.
            # A dereferenced callee `(*PTR_x)` also contains only idents and `*`
            # but *starts* with `*`, so the leading-`*` test keeps it as the
            # callee group rather than stripping it as a cast.
            if not inner or inner[0] == "*" or any(not (_IDENT.fullmatch(tok) or tok == "*") for tok in inner):
                break
            c = c[close + 1 :]
        return c

    @staticmethod
    def _match(c: list[str], i: int) -> int | None:
        """Index of the ``)`` matching the ``(`` at ``c[i]``."""
        depth = 0
        for j in range(i, len(c)):
            if c[j] == "(":
                depth += 1
            elif c[j] == ")":
                depth -= 1
                if depth == 0:
                    return j
        return None

    @classmethod
    def _spans_to_end(cls, c: list[str], open_idx: int) -> bool:
        """True if the ``(`` at ``open_idx`` matches the final token of ``c``."""
        close = cls._match(c, open_idx)
        return close is not None and close == len(c) - 1


# Tokens that may sit between a function's parameter list and its body brace ---
# the declarator suffix of a function that returns a pointer-to-function or whose
# name is wrapped in a grouping, e.g. ``i64 (**init_proc())(void) { ... }``.
_DECL_SUFFIX = frozenset({")", "(", "*", "[", "]", ","})


def _body_open_after(toks: list, close: int, n: int) -> int | None:
    """Index of the ``{`` that opens the body of a definition whose parameter list
    closes at ``close``, or None if no body follows.

    The common case is ``toks[close + 1] == "{"``. A function that returns a
    pointer-to-function carries a trailing declarator (``...())(void) {``) between
    the parameter list and the brace; we step over a run of declarator tokens
    (``)``/``(``/``*``/``[``/``]``/``,`` and type words) to reach it. Anything else
    (a ``;``, an operator, a number) means this was not a definition.
    """
    j = close + 1
    while j < n:
        tj = toks[j][0]
        if tj == "{":
            return j
        if tj in _DECL_SUFFIX or _IDENT.fullmatch(tj):
            j += 1
            continue
        return None
    return None


def _top_level_functions(toks: list) -> list[tuple[str, int, int, int, int]]:
    """Locate every top-level function definition in a token stream.

    Returns one ``(name, sig_start_char, body_open_idx, body_close_idx,
    body_end_char)`` tuple per definition, where ``sig_start_char`` is the source
    offset at which the signature begins (just past the previous top-level ``;``
    or ``}``), so a caller can delete the whole definition. Function bodies are
    skipped wholesale, so only depth-0 definitions are reported and nested braces
    never confuse the scan.

    Handles the function-returning-function-pointer declarator decompilers emit
    for the ``__gmon_start__`` registration hook (``i64 (**init_proc())(void){``):
    the real name owns the *first* parameter list, and a ``(`` whose first inner
    token is ``*`` is a declarator grouping (no C parameter list starts with
    ``*``), so we skip it and let the inner name match.
    """
    n = len(toks)
    out: list[tuple[str, int, int, int, int]] = []
    depth = 0
    i = 0
    seg_start = toks[0][1] if toks else 0
    while i < n:
        t = toks[i][0]
        if t == "{":
            depth += 1
            i += 1
            continue
        if t == "}":
            depth -= 1
            i += 1
            if depth == 0:
                seg_start = toks[i - 1][2]
            continue
        if depth == 0 and t == ";":
            seg_start = toks[i][2]
            i += 1
            continue
        # A `(` immediately followed by `*` is a declarator grouping wrapping the
        # real name (`(**init_proc())`), not this token's parameter list.
        if (
            depth == 0
            and _IDENT.fullmatch(t)
            and t not in _RESERVED
            and i + 1 < n
            and toks[i + 1][0] == "("
            and (i + 2 >= n or toks[i + 2][0] != "*")
        ):
            close = _match_delim(toks, i + 1)
            if close is not None:
                bo = _body_open_after(toks, close, n)
                if bo is not None:
                    bc = _match_delim(toks, bo)
                    if bc is not None:
                        out.append((t, seg_start, bo, bc, toks[bc][2]))
                        seg_start = toks[bc][2]
                        i = bc + 1
                        continue
        i += 1
    return out


class EraseResolverStubs(Transform):
    """Delete Binary Ninja's CRT/IFUNC lazy-binding resolver stub functions.

    Binary Ninja recovers the dynamic-loader resolver chain as a family of tiny
    functions: a shared resolver, plus one stub per relocation slot that loads a
    constant index into a dead local and tail-calls the shared resolver
    (``i64 b(){i64 er=0;return a();}``, ``i64 e(){i64 er=1;return a();}``, ...,
    around 57 per coreutils binary). These are pure loader plumbing with no
    analyst value, and they are the single largest Binary-Ninja-specific source
    of avoidable tokens (the main reason its T3 reduction trails Ghidra and
    Hex-Rays). Unlike every other pass, this one *removes whole definitions*
    rather than rewriting text, so it is gated at the reductive tier (T4).

    Two guards make the deletion provably safe against removing real code:

    * **Family guard.** A stub is removed only when at least
      ``_MIN_FAMILY`` (3) trivially-shaped functions tail-call the *same* target.
      A function whose entire body is ``[type local = const;] return CALLEE();``
      shared by three or more callers is the unmistakable resolver signature; no
      ordinary program produces it.
    * **Reference guard.** A stub is removed only when its name occurs exactly
      once in the unit (its own definition), so nothing else refers to it.

    The shared resolver itself is kept (it is referenced by the stubs and keeping
    it sidesteps any dangling-reference question); only the per-slot stubs, which
    dominate the count, are deleted.
    """

    id = "drop-resolver-stubs"
    tier = Tier.T4_REDUCTIVE
    description = "Delete Binary Ninja lazy-binding resolver-stub families."

    _MIN_FAMILY = 3

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        funcs = _top_level_functions(toks)
        if not funcs:
            return code
        # Classify each function: does its body tail-call a single callee?
        callees: dict[int, str] = {}
        for k, (_name, _ss, bo, bc, _bce) in enumerate(funcs):
            callee = self._stub_callee([x[0] for x in toks[bo + 1 : bc]])
            if callee is not None:
                callees[k] = callee
        family = Counter(callees.values())
        resolvers = {c for c, cnt in family.items() if cnt >= self._MIN_FAMILY}
        if not resolvers:
            return code
        # Reference guard: how often does each name appear across CODE tokens?
        name_count = Counter(x[0] for x in toks if _IDENT.fullmatch(x[0]))
        edits: list[tuple[int, int]] = []
        for k, (name, ss, _bo, _bc, bce) in enumerate(funcs):
            if callees.get(k) in resolvers and name_count[name] == 1:
                edits.append((ss, bce))
        for lo, hi in sorted(edits, reverse=True):
            code = code[:lo] + code[hi:]
        return code

    def _stub_callee(self, body: list[str]) -> str | None:
        """Return the tail-called callee if ``body`` is a trivial forwarding stub.

        A stub body is ``[type local = <single token>;] return CALLEE();`` with
        an empty argument list, no control flow, and no other statement. Returns
        ``CALLEE`` (a bare identifier) or None.
        """
        if not body or any(w in ElideThunkBodies._CTRL for w in body):
            return None
        decl = call = None
        for stmt in ElideThunkBodies._split_semis(body):
            if not stmt:
                continue
            if stmt[0] == "return":
                if call is not None or len(stmt) < 4 or not _IDENT.fullmatch(stmt[1]) or stmt[2] != "(" or stmt[-1] != ")":
                    return None
                if stmt[3:-1]:  # the call must take no arguments
                    return None
                call = stmt[1]
            elif "(" in stmt:
                return None  # a second call: not a pure forwarding stub
            else:
                if decl is not None or not self._is_const_decl(stmt):
                    return None
                decl = stmt
        return call

    @staticmethod
    def _is_const_decl(stmt: list[str]) -> bool:
        """A bare local declaration, optionally ``= <single token>`` (a constant
        index or a data symbol)."""
        if "(" in stmt or len(stmt) < 2:
            return False
        if "=" in stmt:
            eq = stmt.index("=")
            return eq == len(stmt) - 2 and _IDENT.fullmatch(stmt[eq - 1]) is not None
        return _IDENT.fullmatch(stmt[-1]) is not None


class DropCrtFunctions(Transform):
    """Delete C-runtime / ELF-scaffolding functions by their fixed names.

    Every binary carries a handful of toolchain-generated functions that are
    identical across programs and never the analysis target: the ``.init``/
    ``.fini`` section stubs, the ``__gmon_start__`` profiling hook, and the
    ``tm_clones`` / global-ctor-dtor registration glue. Their names come from a
    fixed compiler vocabulary that no application reuses, so deleting whole
    definitions by name is safe. Like ``drop-resolver-stubs`` this removes
    definitions rather than rewriting text, so it is gated at T4.

    Only unambiguous scaffolding names are dropped (``_DT_INIT``, ``_init``,
    ``frame_dummy``, ``register_tm_clones``, ``_start``, ``init_proc``, ...). The
    bare ``start`` and ``__libc_start_main`` are deliberately excluded: ``start``
    is a plausible application name, and ``__libc_start_main`` is usually a real
    import handled by ``thunk-elision``.

    Two patterns need more than a name match. Ghidra renames the ELF entry point
    ``_start`` to ``entry``, which is too plausible an application name to delete
    unconditionally, so an ``entry`` function is dropped only when its body calls
    ``__libc_start_main`` (the unmistakable program-startup trampoline). And the
    ``__gmon_start__`` registration hook is emitted with a function-returning-
    function-pointer declarator (``i64 (**init_proc())(void){...}``); the parser in
    :func:`_top_level_functions` recognises that shape, so the ``init_proc`` name
    match fires.
    """

    id = "drop-crt"
    tier = Tier.T4_REDUCTIVE
    description = "Delete C-runtime and ELF scaffolding functions."

    _CRT_NAMES = frozenset(
        {
            "_DT_INIT",
            "_DT_FINI",
            "_INIT_0",
            "_FINI_0",
            "_init",
            "_fini",
            "init_proc",
            "_start",
            "frame_dummy",
            "register_tm_clones",
            "deregister_tm_clones",
            "__do_global_ctors_aux",
            "__do_global_dtors_aux",
            "__libc_csu_init",
            "__libc_csu_fini",
        }
    )

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        candidates = [
            (name, ss, bce)
            for name, ss, bo, bc, bce in _top_level_functions(toks)
            if name in self._CRT_NAMES or (name == "entry" and self._is_entry_trampoline(toks, bo, bc))
        ]
        if not candidates:
            return code

        # Reference guard: char offsets of every identifier token whose name is a
        # candidate. A candidate is deleted only when *all* of its references lie
        # within the spans being deleted, so deleting the set leaves no dangling
        # reference. Binary Ninja sometimes recovers a spurious `return _start(..)`
        # in a surviving function; deleting `_start` then orphans that call, so the
        # guard keeps `_start` (and any cross-referenced CRT function) in that case.
        # Ghidra/Hex-Rays CRT families only reference each other and are deleted as
        # a set, so the guard does not block them.
        cand_names = {c[0] for c in candidates}
        occ: dict[str, list[int]] = {nm: [] for nm in cand_names}
        for text, start, _end in toks:
            if text in cand_names and _IDENT.fullmatch(text):
                occ[text].append(start)

        deletion = list(candidates)
        changed = True
        while changed:
            changed = False
            spans = [(ss, bce) for _nm, ss, bce in deletion]
            survivors = [c for c in deletion if any(not any(lo <= p < hi for lo, hi in spans) for p in occ[c[0]])]
            if survivors:
                surv = {id(c) for c in survivors}
                deletion = [c for c in deletion if id(c) not in surv]
                changed = True

        for _nm, ss, bce in sorted(deletion, key=lambda c: c[1], reverse=True):
            code = code[:ss] + code[bce:]
        return code

    @staticmethod
    def _is_entry_trampoline(toks: list, bo: int, bc: int) -> bool:
        """True if the body between ``bo``/``bc`` calls ``__libc_start_main``.

        Ghidra calls it through the GOT pointer ``PTR___libc_start_main``, so the
        symbol appears as a substring of a body token rather than a bare name.
        """
        return any("__libc_start_main" in toks[j][0] for j in range(bo + 1, bc))


class TrimSpuriousArgs(Transform):
    """Truncate surplus arguments on calls to fixed-arity libc functions.

    Binary Ninja often surfaces *more* arguments than the callee takes, because
    it could not prove the call-site arity and spilled the caller-saved registers
    as extra operands (``setlocale(6,(s+20),mc,mb,md,me,...)`` --- ``setlocale``
    takes two). For a function with a *fixed, well-known* arity the surplus is
    provably not a real parameter (the function cannot accept it), so truncating
    the top-level argument list to that arity is safe regardless of what the extra
    operands are. Discarding the (bogus) recovered operands is reductive --- and,
    unusually, *helps* a reader by removing arguments the real API does not have
    --- hence T4.

    Conservative by construction: only a curated set of unambiguously
    non-variadic libc functions with stable arity is touched, and only when the
    call carries *more* arguments than that arity (a correctly-argged call, a
    prototype, or a definition is left exactly as-is). Variadic functions
    (``printf`` and friends) are never in the table, so their genuine varargs are
    never cut. A definition (``)`` followed by ``{``) and a member call
    (``p->free(...)``) are both skipped.
    """

    id = "trim-spurious-args"
    tier = Tier.T4_REDUCTIVE
    description = "Truncate spilled surplus arguments on curated fixed-arity libc calls."

    # Keywords that may precede a *call* used as an expression/statement, so a
    # preceding identifier here does not mark a declarator. Every other leading
    # identifier (a type word, a return type, or a `*`) means the name sits in
    # declarator position, i.e. a prototype or definition, which must be left alone.
    _CALL_PREV_KW = frozenset({"return", "else", "do"})

    # name -> exact arity. Only non-variadic libc functions whose arity is fixed
    # by the C standard; truncating beyond arity can never drop a real parameter.
    ARITY = {
        "setlocale": 2,
        "free": 1,
        "fclose": 1,
        "fflush": 1,
        "fileno": 1,
        "rewind": 1,
        "strlen": 1,
        "getenv": 1,
        "perror": 1,
        "puts": 1,
        "memset": 3,
        "memcpy": 3,
        "memmove": 3,
        "memcmp": 3,
        "bcopy": 3,
        "bcmp": 3,
        "strncmp": 3,
        "strncpy": 3,
        "strncat": 3,
        "strcmp": 2,
        "strcpy": 2,
        "strcat": 2,
        "strchr": 2,
        "strrchr": 2,
        "strstr": 2,
        "strspn": 2,
        "strcspn": 2,
        "strpbrk": 2,
        "strcasecmp": 2,
        "fputs": 2,
        "fgets": 3,
        "fwrite": 4,
        "fread": 4,
    }

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int]] = []
        i = 0
        while i < n - 1:
            name = toks[i][0]
            arity = self.ARITY.get(name)
            if arity is None or toks[i + 1][0] != "(":
                i += 1
                continue
            # Skip a member call (`p->free(...)`).
            if i > 0 and toks[i - 1][0] in (".", "->"):
                i += 1
                continue
            # Skip a declaration / prototype: the name sits in declarator position,
            # preceded by a return type (a `*` or a type/identifier token) rather
            # than by the operator or punctuation that precedes a real call. This
            # leaves an over-arged prototype (`void *memcpy(a, b, c, extra);`)
            # untouched, exactly like a definition.
            prev = toks[i - 1][0] if i > 0 else None
            if prev == "*" or (prev is not None and _IDENT.fullmatch(prev) and prev not in self._CALL_PREV_KW):
                i += 1
                continue
            close = _match_delim(toks, i + 1)
            if close is None:
                i += 1
                continue
            # Skip a definition: `)` immediately followed by `{`.
            if close + 1 < n and toks[close + 1][0] == "{":
                i = close + 1
                continue
            args = _split_args(toks, i + 1)
            if args is not None and len(args) > arity:
                # Keep the first `arity` args; cut from the end of arg[arity-1]
                # to just before `)`.
                keep_hi_tok = args[arity - 1][1]  # one past last kept arg
                lo = toks[keep_hi_tok][1]
                hi = toks[close][1]
                edits.append((lo, hi))
            i = close + 1
        for lo, hi in sorted(edits, reverse=True):
            code = code[:lo] + code[hi:]
        return code
