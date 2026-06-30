"""T3 --- contextual, lossy transforms (machine-generated artifacts).

These discard information the decompiler *synthesized* rather than recovered:
placeholder identifier names (built from stack offsets / SSA indices) and verbose
type spellings. Meaning and internal consistency are preserved, but the discarded
strings (an address, an offset) are gone from the text --- low-value decompiler
bookkeeping. Confidence-gated so symbol-anchored names survive.

``StripCallingConventions`` is *not* here: it discards a genuine ABI hint that is
not recoverable from the text, so it sits at the reductive tier (T4) alongside
warning-banner removal.
"""

from __future__ import annotations

import itertools
import re
import string
from collections import Counter

from .base import Tier, Transform
from .lexer import SegmentType, scan
from .tokens import match_delim as _match_delim, split_args as _split_args, tokenize as _tok_offsets

# Keywords/types we must never hand out as a generated short name.
_RESERVED = {
    "if",
    "do",
    "or",
    "to",
    "in",
    "as",
    "is",
    "no",
    "ok",
    "id",
    "int",
    "for",
    "char",
    "void",
    "long",
    "goto",
    "else",
    "enum",
    "case",
    "auto",
    "bool",
    "true",
    "false",
    "short",
    "float",
    "union",
    "const",
    "while",
    "break",
    "double",
    "struct",
    "switch",
    "return",
    "sizeof",
    "static",
    "extern",
    "signed",
    "default",
    "typedef",
    "continue",
    "unsigned",
    "register",
    "volatile",
}

_IDENT = re.compile(r"[A-Za-z_]\w*")


def _after_member_op(text: str, start: int) -> bool:
    """True if the identifier at ``text[start:]`` is a struct/union member access
    (immediately preceded by ``.`` or ``->``, ignoring whitespace).

    Such a name is a real, source-derived field symbol --- not a decompiler
    placeholder --- even when it happens to spell like one (``regs->eax``,
    ``frame->local_18``), so the placeholder compressor must leave it alone.

    All whitespace (including newlines) between the operator and the name is
    skipped, so a member access split across lines (``p->\n  result``) is still
    recognised --- otherwise the same field would be renamed at one use and kept
    at another, producing an inconsistent reference."""
    j = start - 1
    while j >= 0 and text[j] in " \t\r\n":
        j -= 1
    if j < 0:
        return False
    if text[j] == ".":
        return j == 0 or text[j - 1] != "."  # a member dot, not part of `...`
    return text[j] == ">" and j >= 1 and text[j - 1] == "-"


def _struct_body_spans(code: str) -> list[tuple[int, int]]:
    """Char spans of every ``struct``/``union`` *body* ``{...}`` in ``code``.

    A field declared inside such a body is a real, source-derived symbol
    (``struct CONTEXT { uint eax; ... }``), not a decompiler placeholder, even when
    it is spelled like one. The placeholder compressor uses these spans to leave
    field *declarations* alone --- otherwise it would rename the declaration
    (``uint eax;`` -> ``uint a;``) while the member-access guard preserves every
    *use* (``c->eax``), leaving the struct declaring fields the code never
    references. A bare ``struct foo *p;`` reference (no ``{``) opens no body and
    yields no span.

    ``enum`` bodies are deliberately *excluded*: an enum constant is referenced as
    a bare identifier (``return v1 + v2``, not ``e->v1``), so the member-access
    guard does not protect its uses. Protecting only the *definition* would rename
    every use to a fresh name while keeping the definition verbatim --- an
    inconsistent, undefined reference. Leaving enum bodies unprotected lets a
    placeholder-spelled constant rename consistently across its definition and all
    its uses (and a real enum constant does not match a placeholder pattern, so it
    is untouched either way).

    Token-based, so braces inside strings/comments are ignored; empty (the common
    case) when the unit defines no aggregates inline.
    """
    toks = _tok_offsets(code)
    n = len(toks)
    spans: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if toks[i][0] in ("struct", "union"):
            j = i + 1
            while j < n and _IDENT.fullmatch(toks[j][0]):  # optional tag name
                j += 1
            if j < n and toks[j][0] == "{":
                close = _match_delim(toks, j, "{", "}")
                if close is not None:
                    spans.append((toks[j][1], toks[close][2]))
                    i = close + 1
                    continue
        i += 1
    return spans


def _short_names(used: set[str]):
    """Yield the shortest identifiers not in ``used`` or the reserved set.

    Mutates ``used`` so successive callers (e.g. the function-name pass then the
    placeholder pass) never collide on a generated name.
    """
    for size in itertools.count(1):
        for combo in itertools.product(string.ascii_lowercase, repeat=size):
            cand = "".join(combo)
            if cand in used or cand in _RESERVED:
                continue
            used.add(cand)
            yield cand


class NormalizeFlagTemps(Transform):
    r"""Normalize Binary Ninja's colon-spelled flag temporaries to plain identifiers.

    Binary Ninja names a lifted condition-flag SSA value with a colon
    (``cond:0``, ``cond:12_1``) --- the only place ``:`` appears inside what is
    otherwise an identifier, and not legal C. The colon makes it a token the rest
    of the pipeline can misread: a statement-leading ``cond:1 = ...`` looks like a
    goto label ``cond:`` to ``cfg-canon``, which would drop it and orphan the
    assignment. We therefore rewrite ``cond:N`` -> ``condN`` (CODE only) *first*,
    before any structural pass inspects the text; the rewrite only drops a
    non-C separator from one synthesized identifier, so it is information-
    preserving (T2). The matching ``cond\d+`` placeholder in ``compress-names``
    then compresses the normalized name at T3 like any other flag temp.

    Runs at the head of the pipeline (before ``cfg-canon``/``ternary``) so the
    colon never reaches a pass that could misinterpret it.
    """

    id = "flag-temps"
    tier = Tier.T2_STRUCTURAL
    description = "Normalize Binary Ninja colon-flag temporaries into plain identifiers."

    _RX = re.compile(r"\bcond:(\d+(?:_\d+)?)")

    def apply(self, code: str) -> str:
        return "".join((self._RX.sub(r"cond\1", t) if seg_type == SegmentType.CODE else t) for seg_type, t in scan(code))


class CompressFunctionNames(Transform):
    """Rename decompiler placeholder *function* names defined in this file.

    Unlike locals, a function name is a single file-global symbol: every call
    site must remap to the same token as the definition. We therefore scan the
    whole translation unit, remap each placeholder name (``FUN_00401abc``,
    ``sub_401abc``) consistently across its definition and all call sites, and
    leave everything else alone.

    Two properties keep this safe across realistic multi-function files:

    * **Placeholders only.** Real, symbol-derived names (``process_record``, and
      thunks that wrap a real symbol such as ``j_std::exception::exception`` or
      ``j___RTC_CheckEsp``) carry analyst signal and never match the patterns, so
      they survive --- consistent with the confidence-gating that protects
      anchored names at T3. Only pure address placeholders match: ``FUN_*``,
      ``sub_*``, ``unknown_libname_*``, and Binary Ninja ``j_sub_*`` thunks.

    * **Consistent remapping.** Each placeholder is renamed to the same token at
      its definition, prototype, and every call site, so the unit stays
      internally consistent (and a thunk ``j_sub_x`` and its target ``sub_x``,
      being different functions, get different names).

    By default a placeholder is compressed whether or not the unit also contains
    its body --- the address it encodes is meaningless either way, and this is
    the common single-prompt case. Passing ``require_definition=True`` instead
    renames only functions *defined* in the unit, so a callee defined in another
    separately-compressed file keeps one stable name and cross-file references
    never silently diverge.

    Lossy because the address embedded in ``FUN_00401abc`` is discarded.
    """

    id = "compress-funcs"
    tier = Tier.T3_CONTEXTUAL
    description = "Rename address-placeholder function names across the unit, keeping real wrapped symbols."

    # Placeholder function names across Ghidra / IDA / Binary Ninja. Only pure
    # address-derived names; thunks (`j_`) are matched solely when they wrap
    # another placeholder, so `j_<real-symbol>` is preserved.
    DEFAULT_PATTERNS = (
        r"FUN_[0-9a-fA-F]+",  # Ghidra: FUN_00401abc
        r"thunk_FUN_[0-9a-fA-F]+",  # Ghidra thunk wrappers
        r"sub_[0-9a-fA-F]+",  # IDA / Hex-Rays / Binary Ninja: sub_401abc
        r"Unwind_[0-9a-fA-F]+",  # Ghidra: address-named exception unwind handler
        r"nullsub_\d+",  # IDA: nullsub_1
        r"unknown_libname_\d+",  # IDA: unknown_libname_9
        r"j_sub_[0-9a-fA-F]+",  # Binary Ninja: jump-thunk to a placeholder
        r"j_FUN_[0-9a-fA-F]+",
        r"j_nullsub_\d+",
        r"j_unknown_libname_\d+",
    )

    def __init__(
        self,
        patterns: tuple[str, ...] | None = None,
        *,
        require_definition: bool = False,
    ) -> None:
        pats = patterns or self.DEFAULT_PATTERNS
        self._is_func = re.compile(r"^(?:" + "|".join(pats) + r")$")
        self._require_definition = require_definition

    def apply(self, code: str) -> str:
        segments = scan(code)
        targets = self._defined_functions(segments) if self._require_definition else self._all_placeholder_funcs(segments)
        if not targets:
            return code

        existing = {m.group(0) for seg_type, text in segments if seg_type == SegmentType.CODE for m in _IDENT.finditer(text)}
        gen = _short_names(used=set(existing))
        mapping = {name: next(gen) for name in targets}

        big = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in mapping) + r")\b")
        return "".join((big.sub(lambda m: mapping[m.group(0)], text) if seg_type == SegmentType.CODE else text) for seg_type, text in segments)

    def _all_placeholder_funcs(self, segments: list[tuple[str, str]]) -> list[str]:
        """Every placeholder function name anywhere (def, prototype, or call)."""
        found: list[str] = []
        seen: set[str] = set()
        for seg_type, text in segments:
            if seg_type != SegmentType.CODE:
                continue
            for m in _IDENT.finditer(text):
                name = m.group(0)
                if name not in seen and self._is_func.match(name):
                    seen.add(name)
                    found.append(name)
        return found

    def _defined_functions(self, segments: list[tuple[str, str]]) -> list[str]:
        """Names with an in-file definition (``NAME(...) {``), first-seen order."""
        toks = [m.group(0) for seg_type, text in segments if seg_type == SegmentType.CODE for m in re.finditer(r"[A-Za-z_]\w*|\S", text)]
        found: list[str] = []
        seen: set[str] = set()
        n = len(toks)
        for i in range(n - 1):
            name = toks[i]
            if toks[i + 1] != "(" or not self._is_func.match(name):
                continue
            depth, j = 0, i + 1
            while j < n:
                if toks[j] == "(":
                    depth += 1
                elif toks[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth == 0 and j + 1 < n and toks[j + 1] == "{" and name not in seen:
                seen.add(name)
                found.append(name)
        return found


class CompressPlaceholderNames(Transform):
    """Rename decompiler placeholder identifiers to short, consistent tokens.

    Long auto-generated names (``local_148``, ``uStack_20``, ``uVar3``,
    ``var_18``, ``v17``) and jump labels (``LAB_00401234``, ``loc_401234``)
    tokenize to multiple tokens while carrying no information beyond "a local"
    or "a jump target". We remap each unique placeholder to the shortest fresh
    identifier that doesn't collide with anything already in the source ---
    labels share the same generator, so ``goto LAB_x; ... LAB_x:`` becomes
    ``goto q; ... q:``. Only names matching the configured patterns are touched;
    real symbols, types, and meaningful names are left alone.

    Lossy because, e.g., ``param_1`` weakly signals "first argument"; that hint
    is discarded. Patterns are configurable per decompiler.
    """

    id = "compress-names"
    tier = Tier.T3_CONTEXTUAL
    description = "Remap placeholder locals, labels, and globals to the shortest collision-free tokens."

    # Default placeholder patterns across Ghidra / IDA (Hex-Rays) / Binary Ninja.
    DEFAULT_PATTERNS = (
        # --- Variables / parameters ---
        # Ghidra's type-prefixed locals: a run of type-indicator letters (lower-
        # or upper-case typedef letters such as B/H/F/S/D, optionally a pointer
        # marker and underscore) then ``Var``/``Stack`` and the disambiguator.
        # Examples: uVar1, pcVar3, ppiVar2, BVar2, pHVar1, pp_Var3, _Var5.
        r"(?:[A-Za-z]{1,3}_?|_)Var\d+",
        r"Var\d+",  # Ghidra: prefix-less Var1/Var15 (typed unkbyteN/unkuintN)
        # Ghidra prepends one ``p`` per pointer level to the Hungarian base name
        # (``puVar``, ``ppuVar``, ... ``ppppppppppppppuVar1``). Runs up to three
        # letters are already covered above; this catches the deeper ``p{2,}`` run
        # so a 14-deep ``ppppppppppppppuVar64`` renames like ``uVar64``.
        r"p{2,}[A-Za-z]{0,3}Var\d+",
        r"p{2,}[A-Za-z]{0,3}Stack_?[0-9a-fA-F]+",
        r"_?local_[0-9a-fA-F]+",  # Ghidra: local_18, and the split-slot form _local_48
        r"(?:_?[A-Za-z]{1,3}_?|_)Stack_?[0-9a-fA-F]+",  # uStack_20, ap_Stack_18, _Stack_8, _uStack_40, _auStack_80
        r"stack0x[0-9a-fA-F]+",  # Ghidra: unrecovered stack slot stack0xfffffffc
        r"param_\d+",  # Ghidra: param_1
        r"(?:extraout|unaff|in)_\w+",  # Ghidra register placeholders
        r"var_[0-9a-fA-F]+(?:_\d+)?",  # Binary Ninja: var_18, var_8_1
        r"result(?:_\d+)?",  # Binary Ninja: default name for an unrecovered return-value SSA temp
        r"temp\d+(?:_\d+)?",  # Binary Ninja: temp0, temp1, and the SSA-suffixed temp0_1
        r"cond\d+(?:_\d+)?",  # Binary Ninja flag temp (``cond:0`` -> ``cond0`` via flag-temps)
        r"arg_?\d+",  # Binary Ninja / IDA: arg1, arg_4
        r"v\d+",  # Hex-Rays: v1
        r"a\d+",  # Hex-Rays argument: a1
        # Binary Ninja register-derived temporaries (a lifted SSA value named
        # after the register it lived in; the register is a mechanical artifact).
        # Covers the general-purpose registers, the SSE/AVX vector registers
        # (``xmm1``, ``zmm0_1``), and the x87 FPU stack slots (``x87_r7_1``).
        r"(?:[er][abcd]x|[er][sd]i|[er][bs]p|r(?:8|9|1[0-5])[bwd]?|[xyz]?mm\d+|x87_r\d+)(?:_\d+)?",
        # Binary Ninja "value of register X on function entry" spill locals. Gated
        # to the register vocabulary only, so the recovered semantic names that
        # share the prefix (``entry_argv``, ``entry_message``) are left untouched.
        r"entry_(?:r(?:8|9|1[0-5])[bwd]?|[er][abcd]x|[er][sd]i|[er][bs]p|x87\w*)(?:_\d+)?",
        r"[fg]sbase(?:_\d+)?",  # Binary Ninja: fsbase, gsbase
        # --- Global data placeholders (pure address, no symbol signal) ---
        r"_?DAT_[0-9a-fA-F]+(?:_\d+)?",  # Ghidra: DAT_0040d430, _DAT_*, SIMD sub-field DAT_001163b0_4
        r"PTR_DAT_[0-9a-fA-F]+",  # Ghidra pointer-to-data: PTR_DAT_*
        r"PTR_[0-9a-fA-F]+",  # Ghidra symbol-less GOT pointer: PTR_0010aff8
        r"[a-z]{1,3}Ram[0-9a-fA-F]+",  # Ghidra absolute-memory pseudo-symbol: uRam0010c3f8, lRam*, pvRam*
        r"data_[0-9a-fA-F]+",  # Binary Ninja: data_40c898
        r"jump_table_[0-9a-fA-F]+",  # Binary Ninja: jump_table_401abc
        # IDA / Hex-Rays auto-named data by element width and kind. The token is
        # a prefix plus a raw address, carrying no signal beyond "data here".
        r"(?:byte|word|dword|qword|xmmword|ymmword|tbyte|flt|dbl|" r"unk|off|stru|asc|jpt|jptoff|algn)_[0-9a-fA-F]+",
        # --- Jump locations / labels (loses only the address hint) ---
        r"LAB_[0-9a-fA-F]+",  # Ghidra: LAB_00401234
        r"(?:code|joined)_r0x[0-9a-fA-F]+",  # Ghidra: code_r0x..., joined_r0x...
        r"loc(?:ret)?_[0-9a-fA-F]+",  # IDA / Hex-Rays: loc_401234, locret_*
        r"LABEL_\d+",  # Hex-Rays: sequential pseudocode label LABEL_137
        r"switchD_[0-9a-fA-F]+_caseD_[0-9a-fx]+",  # Ghidra switch case label: switchD_00103dbb_caseD_2
        # Ghidra spells jump-table symbols with the C++ scope operator
        # (``switchD_<addr>::switchdataD_<addr>``); the ``::`` splits the name into
        # two identifiers, so each address-derived half is matched and renamed
        # independently but consistently.
        r"switchD_[0-9a-fA-F]+",  # Ghidra jump-table dispatch symbol (bare half)
        r"switchdataD_[0-9a-fA-F]+",  # Ghidra jump-table offset-table symbol
        r"caseD_[0-9a-fx]+",  # Ghidra jump-table case label (bare half)
        r"label_[0-9a-fA-F]+",  # Binary Ninja: label_401234
    )

    def __init__(self, patterns: tuple[str, ...] | None = None) -> None:
        pats = patterns or self.DEFAULT_PATTERNS
        self._is_placeholder = re.compile(r"^(?:" + "|".join(pats) + r")$")
        #: Populated by :meth:`apply` with {placeholder: short_name}; lets a
        #: downstream caller (e.g. a variable-name recovery evaluation) map
        #: predictions on the compressed code back to the original placeholder
        #: identities.
        self.last_mapping: dict[str, str] = {}

    def apply(self, code: str) -> str:
        segments = scan(code)
        struct_spans = _struct_body_spans(code)

        def in_struct_body(pos: int) -> bool:
            return any(lo <= pos < hi for lo, hi in struct_spans)

        existing: set[str] = set()
        placeholders: list[str] = []
        offset = 0
        for seg_type, text in segments:
            if seg_type == SegmentType.CODE:
                for match in _IDENT.finditer(text):
                    name = match.group(0)
                    existing.add(name)
                    # Skip two kinds of real, source-derived names that merely spell
                    # like placeholders: a member access (`p->local_18`, `regs.eax`)
                    # and a field/enumerator declared inside a `struct`/`union`/`enum`
                    # body. Both are neither renamed nor counted as a placeholder
                    # occurrence, so the unit stays internally consistent (a field's
                    # declaration and its `->field` uses keep the same spelling).
                    if (
                        self._is_placeholder.match(name)
                        and not _after_member_op(text, match.start())
                        and not in_struct_body(offset + match.start())
                    ):
                        placeholders.append(name)
            offset += len(text)

        # First-seen order, de-duplicated.
        unique = list(dict.fromkeys(placeholders))
        if not unique:
            self.last_mapping = {}
            return code

        gen = _short_names(used=set(existing))
        mapping = {name: next(gen) for name in unique}
        self.last_mapping = dict(mapping)

        big = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in mapping) + r")\b")

        out: list[str] = []
        offset = 0
        for seg_type, text in segments:
            if seg_type == SegmentType.CODE:
                base = offset

                def rename(m: re.Match, _text: str = text, _base: int = base) -> str:
                    if _after_member_op(_text, m.start()) or in_struct_body(_base + m.start()):
                        return m.group(0)
                    return mapping[m.group(0)]

                out.append(big.sub(rename, text))
            else:
                out.append(text)
            offset += len(text)
        return "".join(out)


class SimplifyLowConfidenceTypes(Transform):
    """Shorten the decompiler's verbose fixed-width type spellings.

    We rewrite a fixed *vocabulary* of decompiler-emitted type names only ---
    never DWARF/PDB-anchored types such as ``size_t`` or a named ``struct`` ---
    so no per-symbol confidence metadata is required to apply it safely.

    The vocabulary is deliberately narrow: it includes only mappings that
    *reduce* token count on all three tokenizers without ever increasing it.
    Compact decompiler
    types are already one or two tokens in modern BPE vocabularies, so
    shortening them (``undefined8`` -> ``u64``, ``uint`` -> ``u32``,
    ``_DWORD`` -> ``u32``) is token-neutral at best and a regression at worst ---
    and lossy --- so those mappings are excluded. The token wins everywhere are
    IDA's genuinely verbose spellings (``__int64``, ``unsigned __int64``,
    ``_QWORD``, the 128-bit ``__int128`` family) and Binary Ninja's
    ``intN_t``/``uintN_t`` family (e.g. ``int32_t`` is three tokens, ``i32`` is
    two), which dominate Binary Ninja output and are its single largest source of
    avoidable tokens. We additionally normalize glibc's internal ``__``-prefixed
    aliases (``__off_t``, ``__mode_t``, ...) to their public POSIX typedefs,
    which is lossless (the same type) and a token win on all three tokenizers.

    Lossy (hence T3): ``unsigned __int64 -> u64`` re-spells an inferred type.
    """

    id = "simplify-types"
    tier = Tier.T3_CONTEXTUAL
    description = "Re-spell verbose width types to compact aliases where it reduces tokens."

    # (pattern, replacement). Each mapping reduces tokens on GPT (o200k), Claude
    # (Opus 4.8), and Gemini (3.1 Pro) tokenizers, and never increases any.
    # `unsigned __intN` first so it wins before the bare `__intN` tail.
    # Mappings that were token-neutral or a regression on at least one tokenizer
    # (Ghidra's undefined2/4/8, uint/ulong/byte; IDA's _DWORD/_WORD/_BYTE) are
    # intentionally omitted.
    REPLACEMENTS = (
        (r"unsigned\s+__int128", "u128"),
        (r"unsigned\s+__int64", "u64"),
        (r"unsigned\s+__int32", "u32"),
        (r"unsigned\s+__int16", "u16"),
        (r"unsigned\s+__int8", "u8"),
        # `signed __intN` before the bare `__intN` tail, else the bare rule fires
        # on the suffix and orphans the now-meaningless `signed` keyword
        # (`signed __int64` -> `signed i64`, invalid C). `signed` is the default,
        # so dropping it is safe.
        (r"signed\s+__int128", "i128"),
        (r"signed\s+__int64", "i64"),
        (r"signed\s+__int32", "i32"),
        (r"signed\s+__int16", "i16"),
        (r"signed\s+__int8", "i8"),
        (r"__int128", "i128"),
        (r"__int64", "i64"),
        (r"__int32", "i32"),
        (r"__int16", "i16"),
        (r"__int8", "i8"),
        (r"_QWORD", "u64"),
        # Binary Ninja fixed-width spellings (uintN before intN is irrelevant
        # here -- each is \b-anchored -- but kept grouped for readability).
        # The 128-bit pair mirrors the IDA ``__int128`` family already mapped
        # above; ``int128_t`` is three tokens, ``i128`` is two.
        (r"uint128_t", "u128"),
        (r"int128_t", "i128"),
        (r"uint64_t", "u64"),
        (r"uint32_t", "u32"),
        (r"uint16_t", "u16"),
        (r"uint8_t", "u8"),
        (r"int64_t", "i64"),
        (r"int32_t", "i32"),
        (r"int16_t", "i16"),
        (r"int8_t", "i8"),
        # glibc's double-underscore stdint aliases (same types as intN_t/uintN_t).
        # `\b` keeps these distinct from the bare intN_t rules above (no boundary
        # sits inside `__int32_t`), so order is irrelevant.
        (r"__uint64_t", "u64"),
        (r"__uint32_t", "u32"),
        (r"__uint16_t", "u16"),
        (r"__uint8_t", "u8"),
        (r"__int64_t", "i64"),
        (r"__int32_t", "i32"),
        (r"__int16_t", "i16"),
        (r"__int8_t", "i8"),
        # Ghidra: only the 1-byte spelling is a net token win; undefined2/4/8
        # regress on Gemini and are omitted.
        (r"undefined1", "u8"),
        # glibc internal type aliases -> their public POSIX typedef. These are
        # the *same* type (e.g. `off_t` is defined as `__off_t`), so the rewrite
        # is a lossless spelling normalization, and it is a token win on all
        # three tokenizers (one fewer token each). Hex-Rays emits the `__`-
        # prefixed spellings pervasively in coreutils output.
        (r"__off_t", "off_t"),
        (r"__mode_t", "mode_t"),
        (r"__pid_t", "pid_t"),
        (r"__uid_t", "uid_t"),
        (r"__gid_t", "gid_t"),
        (r"__ssize_t", "ssize_t"),
        (r"__time_t", "time_t"),
        (r"__ino_t", "ino_t"),
        (r"__dev_t", "dev_t"),
        # `_OWORD` -> `u128` is intentionally omitted: it is a token win on GPT
        # and Claude but a regression on Gemini, so it fails the never-increase
        # rule above.
    )

    def __init__(self) -> None:
        self._subs = [(re.compile(r"\b" + pat + r"\b"), rep) for pat, rep in self.REPLACEMENTS]

    def apply(self, code: str) -> str:
        def fix(text: str) -> str:
            for rx, rep in self._subs:
                # Decline a match right after ``.`` or the ``>`` of ``->``: a token
                # there is a *member name*, never a type, so a field spelled like a
                # width type (``s.int32_t``) is not rewritten into a corrupted
                # reference (``s.i32``). Whitespace (incl. newlines) between the
                # operator and the name is skipped, so a spaced or line-wrapped
                # member access (``s . int32_t``, ``s->\n int32_t``) is also caught.
                # Done in the callback rather than a regex lookbehind so the
                # (dominant) scan cost stays at baseline speed; the check runs only
                # on the rare actual match.
                def repl(m: re.Match, _rep: str = rep) -> str:
                    j = m.start() - 1
                    while j >= 0 and text[j] in " \t\r\n":
                        j -= 1
                    return m.group(0) if j >= 0 and text[j] in ".>" else _rep

                text = rx.sub(repl, text)
            return text

        return "".join(fix(t) if seg_type == SegmentType.CODE else t for seg_type, t in scan(code))


class DropNullPointerCast(Transform):
    """Drop the redundant pointer-type cast on a null constant (``(T *)0x0`` -> ``0``).

    Ghidra spells every null pointer as a typed cast of the literal zero
    (``(char *)0x0``, ``(undefined **)0x0``, ``(FILE *)0x0``), thousands of times
    per binary. In any pointer context the cast is redundant: ``0`` is the null-
    pointer constant for *any* pointer type, so the annotation merely restates a
    type the surrounding expression already fixes.

    We rewrite only where ``0`` is provably interchangeable with the cast. The
    cast must be a pure pointer cast (a type spelling of identifiers/keywords
    followed by one or more ``*``), its operand must be the literal ``0x0``, and
    it must sit in an operand position where a bare null constant cannot change
    meaning. The position is enforced with a whitelist of the neighbouring
    tokens: we fire only when the token before the cast and the token after
    ``0x0`` are both delimiters or comparison/logical operators, never arithmetic
    (``+``/``-``), subscript (``[``), dereference, or member access, where
    switching pointer arithmetic to integer arithmetic would change the result.
    This is conservative by design: it declines ambiguous positions rather than
    risk a semantic change, so it leaves some safe sites untouched.

    Lossy (hence T3): the written pointer type is discarded, though it stays
    recoverable from the lvalue or the comparison operand.
    """

    id = "null-cast"
    tier = Tier.T3_CONTEXTUAL
    description = "Drop a redundant pointer cast on a null constant."

    # Tokens after which a bare null constant is a complete, unambiguous operand.
    _SAFE_BEFORE = frozenset({"=", "==", "!=", "<", ">", "<=", ">=", "(", "[", "{", ",", ";", "return", "?", ":", "&&", "||", "!", "}"})
    # Operators that take a *type* operand: a cast directly inside their `(` is
    # load-bearing (it fixes the operand type), so the pointer cast on the null is
    # NOT redundant there and must be kept (`sizeof((char *)0x0)` is `sizeof(char*)`,
    # not `sizeof(0)`). The `(` of one of these reads as a `_SAFE_BEFORE` token, so
    # it is excluded explicitly.
    _TYPE_OP_BEFORE_PAREN = frozenset({"sizeof", "_Alignof", "alignof", "__alignof__", "typeof", "__typeof__", "decltype"})
    # Keywords that, before a `(`, make it a *grouping* paren rather than a call:
    # `return ((T *)0x0)` is a group, `f((T *)0x0)` is a call. Used to tell the two
    # apart when the cast+null is wrapped in its own parens (see apply()).
    _GROUPING_BEFORE = frozenset({"return", "sizeof", "if", "while", "for", "switch", "case", "do", "else", "goto", "_Alignof", "alignof", "typeof"})
    # Tokens that may follow the null literal without the int/pointer distinction mattering.
    _SAFE_AFTER = frozenset({")", ";", ",", "]", "}", ":", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "?"})
    # The null constant in either spelling. ``int-minform`` (T2) re-spells ``0x0``
    # as ``0`` before this pass runs, so a bare ``0`` after a pointer cast is the
    # same null constant and must be recognised too (the pointer-cast guard above
    # is what makes the rewrite safe, not the radix of the zero).
    _NULL = frozenset({"0x0", "0X0", "0"})

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int]] = []
        i = 0
        while i < n:
            if toks[i][0] != "(":
                i += 1
                continue
            close = _match_delim(toks, i, "(", ")")
            # Need a non-empty cast body and a token after the `)` to inspect.
            if close is None or close <= i + 1 or close + 1 >= n:
                i += 1
                continue
            inner = toks[i + 1 : close]
            # Pointer-type cast: identifiers/keywords and `*` only, ending in `*`.
            if inner[-1][0] != "*" or any(not (_IDENT.fullmatch(t[0]) or t[0] == "*") for t in inner):
                i += 1
                continue
            null_idx = close + 1
            if toks[null_idx][0] not in self._NULL:
                i += 1
                continue
            # A leading cast (no token before) and a trailing null (no token
            # after, so no arithmetic can follow) are both safe operand positions.
            before = toks[i - 1][0] if i > 0 else None
            after = toks[null_idx + 1][0] if null_idx + 1 < n else None
            if (before is not None and before not in self._SAFE_BEFORE) or (after is not None and after not in self._SAFE_AFTER):
                i += 1
                continue
            # `sizeof((T *)0x0)` / `_Alignof((T *)0x0)`: the cast fixes the operand
            # type, so it is load-bearing -- declining keeps the pointer width.
            if before == "(" and i >= 2 and toks[i - 2][0] in self._TYPE_OP_BEFORE_PAREN:
                i += 1
                continue
            # When the cast+null is itself wrapped in parens `((T *)0x0)`, the inner
            # `(`/`)` both read as safe, but the real operand context is OUTSIDE the
            # wrap: `((int *)0x0)->f` must NOT become the invalid `(0)->f`, and
            # `((int *)0x0) + i` must keep its pointer arithmetic. A *call*
            # `f((T *)0x0)` (a value before the open paren) is always safe; a bare
            # grouping re-checks the token after the closing paren. (Decompilers
            # don't emit this double-paren shape, so this only restores the
            # pass's stated decline-when-ambiguous contract.)
            if before == "(" and after == ")" and _match_delim(toks, i - 1, "(", ")") == null_idx + 1:
                outer_before = toks[i - 2][0] if i >= 2 else None
                is_call = outer_before is not None and (
                    outer_before in {")", "]"} or (_IDENT.fullmatch(outer_before) and outer_before not in self._GROUPING_BEFORE)
                )
                if not is_call:
                    outer_after = toks[null_idx + 2][0] if null_idx + 2 < n else None
                    if outer_after is not None and outer_after not in self._SAFE_AFTER:
                        i += 1
                        continue
            edits.append((toks[i][1], toks[null_idx][2]))
            i = null_idx + 1
        for lo, hi in reversed(edits):
            code = code[:lo] + "0" + code[hi:]
        return code


class AddressOfIndexToOffset(Transform):
    """Rewrite ``&base[0xNN]`` to the equivalent ``(base + 0xNN)``.

    ``&a[i]`` and ``a + i`` are identical in C for any array or pointer ``a``, so
    Binary Ninja's address-of-subscript spelling on a literal index (frequent on
    ``data_*`` globals and parameters) is rewritten to the shorter pointer-add
    form, saving a token while preserving meaning. The result is parenthesised so
    its precedence as an operand is unchanged.

    The ``&`` must be unary (address-of), never binary (bitwise-and): we rewrite
    only when the token before ``&`` is not a value (identifier, number, ``)`` or
    ``]``), so ``x & buf[0x10]`` (bitwise) is left alone while ``p = &buf[0x10];``
    is rewritten. The index must be a single integer literal; a variable index is
    skipped (precedence safety). The token *after* the closing ``]`` must not be a
    postfix operator (``.``/``->``/``[``/``(``/``++``/``--``): those bind tighter
    than the unary ``&``, so ``&buf[0x10].field`` is ``&(buf[0x10].field)`` --- the
    ``.`` applies to the element, not to the address --- and rewriting the
    ``&buf[0x10]`` part alone would drop the ``&`` and change the meaning
    (``(buf+0x10).field``). Declining there is the lossless direction.
    Information-preserving, hence T3.
    """

    id = "addr-of-index"
    tier = Tier.T3_CONTEXTUAL
    description = "Rewrite the address-of-a-literal-index idiom to a pointer add."

    # Tokens after which a bare ``&`` is binary (bitwise-and), so a following
    # ``&id[n]`` is NOT an address-of and must not be rewritten.
    _VALUE_BEFORE = frozenset({")", "]"})
    # Postfix operators bind tighter than the prefix ``&``; if one follows the
    # ``]`` the subscript binds to the postfix, not to the ``&``, so rewriting
    # ``&base[n]`` in isolation would re-associate (and drop the ``&``). Mirrors
    # ``DerefOffsetToIndex._BLOCK_AFTER``.
    _BLOCK_AFTER = frozenset({".", "->", "(", "[", "++", "--"})
    _NUM = re.compile(r"0[xX][0-9a-fA-F]+|\d+")

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int, str]] = []
        i = 0
        while i + 4 < n:
            if toks[i][0] == "&" and _IDENT.fullmatch(toks[i + 1][0]) and toks[i + 2][0] == "[":
                close = _match_delim(toks, i + 2, "[", "]")
                prev = toks[i - 1][0] if i > 0 else None
                # `&` is binary (bitwise-and) only after a value: a non-keyword
                # identifier, a number, or a closing `)`/`]`. After a keyword
                # (`return`), an operator, or `(`/`,`/`;` it is unary address-of.
                is_value = prev is not None and (prev in self._VALUE_BEFORE or self._NUM.fullmatch(prev) or (_IDENT.fullmatch(prev) and prev not in _RESERVED))
                unary = not is_value
                after = toks[close + 1][0] if close is not None and close + 1 < n else None
                if close == i + 4 and unary and self._NUM.fullmatch(toks[i + 3][0]) and after not in self._BLOCK_AFTER:
                    rep = f"({toks[i + 1][0]}+{toks[i + 3][0]})"
                    edits.append((toks[i][1], toks[close][2], rep))
                    i = close + 1
                    continue
            i += 1
        for lo, hi, rep in reversed(edits):
            code = code[:lo] + rep + code[hi:]
        return code


class StripPointerSlotAddress(Transform):
    """Strip the trailing slot address from Ghidra's ``PTR_<symbol>_<addr>`` names.

    Ghidra names a recovered import-table pointer ``PTR_<symbol>_<gotslot-addr>``
    (``PTR_free_0010b000``, ``PTR_strncmp_0010b018``). ``compress-names`` rightly
    preserves these because the embedded symbol is analyst signal, but the
    trailing ``_<address>`` is pure bookkeeping (the .got.plt slot), the same kind
    of address ``compress-funcs`` already discards from ``FUN_<addr>``. We keep
    the symbol and drop the address tail (``PTR_free_0010b000`` -> ``PTR_free``).

    A name is rewritten only when the strip leaves a unique result: if two slots
    of the same symbol are present (both would collapse to ``PTR_free``) or the
    stripped form already occurs verbatim, the name is left untouched, so the unit
    stays internally consistent. Lossy (drops the slot address), hence T3.
    """

    id = "strip-ptr-addr"
    tier = Tier.T3_CONTEXTUAL
    description = "Drop the .got.plt slot address from a recovered import pointer name."

    # PTR_ + a symbol (must contain a non-hex-only identifier) + _ + >=6 hex tail.
    _RX = re.compile(r"^(PTR_[A-Za-z_]\w*?)_([0-9a-fA-F]{6,})$")

    def apply(self, code: str) -> str:
        segments = scan(code)
        names: set[str] = set()
        for seg_type, text in segments:
            if seg_type == SegmentType.CODE:
                names.update(m.group(0) for m in _IDENT.finditer(text))
        # Group candidates by their stripped form to detect collisions.
        by_stripped: dict[str, list[str]] = {}
        for name in names:
            m = self._RX.match(name)
            if m:
                by_stripped.setdefault(m.group(1), []).append(name)
        mapping = {origs[0]: stripped for stripped, origs in by_stripped.items() if len(origs) == 1 and stripped not in names}
        if not mapping:
            return code
        big = re.compile(r"\b(?:" + "|".join(re.escape(k) for k in mapping) + r")\b")
        return "".join((big.sub(lambda m: mapping[m.group(0)], text) if seg_type == SegmentType.CODE else text) for seg_type, text in segments)


class TrimPieceAccessSuffix(Transform):
    """Drop the redundant trailing ``_`` from Ghidra piece-access suffixes.

    Ghidra spells a sub-field access (the ``M``-byte field at byte offset ``N`` of
    an aggregate slot) as ``var._N_M_`` (``lb._8_8_``, ``mh._0_2_``). The trailing
    underscore is a pure separator; removing it (``._8_8_`` -> ``._8_8``) saves a
    token while keeping both the offset and the size, so the rewrite is
    information-lossless. A negative lookahead keeps it from biting into a longer
    member name (``._8_8_foo`` is untouched).
    """

    id = "piece-access"
    tier = Tier.T3_CONTEXTUAL
    description = "Drop the trailing separator of a Ghidra piece access."

    _RX = re.compile(r"((?:\.|->)\s*_[0-9a-fA-F]+_[0-9a-fA-F]+)_(?!\w)")

    def apply(self, code: str) -> str:
        return "".join((self._RX.sub(r"\1", text) if seg_type == SegmentType.CODE else text) for seg_type, text in scan(code))


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
            "printf", "fprintf", "dprintf", "sprintf", "snprintf", "asprintf", "obstack_printf",
            "vprintf", "vfprintf", "vdprintf", "vsprintf", "vsnprintf", "vasprintf", "obstack_vprintf",
            "fwprintf", "wprintf", "swprintf", "vfwprintf", "vwprintf", "vswprintf",
            # mem / str
            "memcpy", "memmove", "mempcpy", "memset", "bcopy", "bzero", "explicit_bzero",
            "stpcpy", "stpncpy", "strcat", "strcpy", "strncat", "strncpy",
            "wmemcpy", "wmemmove", "wmempcpy", "wmemset", "wcscpy", "wcpcpy", "wcscat", "wcsncat", "wcsncpy", "wcpncpy",
            # io / system
            "gets", "fgets", "fgets_unlocked", "fread", "fread_unlocked",
            "getcwd", "getwd", "getdomainname", "getgroups", "gethostname", "getlogin_r",
            "pread", "pread64", "read", "readlink", "readlinkat", "realpath",
            "recv", "recvfrom", "ttyname_r", "ptsname_r", "confstr", "poll", "ppoll",
            "wctomb", "mbstowcs", "wcstombs", "mbsrtowcs", "wcsrtombs", "mbsnrtowcs", "wcsnrtombs",
            "syslog", "vsyslog",
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
                close = _match_delim(toks, i + 1, "(", ")")
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
                    args = _split_args(toks, i + 1, close)
                    if len(args) == arity:
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
        if depth == 0 and _IDENT.fullmatch(t) and t not in _RESERVED and i + 1 < n and toks[i + 1][0] == "(" and (i + 2 >= n or toks[i + 2][0] != "*"):
            close = _match_delim(toks, i + 1, "(", ")")
            if close is not None:
                bo = _body_open_after(toks, close, n)
                if bo is not None:
                    bc = _match_delim(toks, bo, "{", "}")
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
        candidates = [(name, ss, bce) for name, ss, bo, bc, bce in _top_level_functions(toks) if name in self._CRT_NAMES or (name == "entry" and self._is_entry_trampoline(toks, bo, bc))]
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
            close = _match_delim(toks, i + 1, "(", ")")
            if close is None:
                i += 1
                continue
            # Skip a definition: `)` immediately followed by `{`.
            if close + 1 < n and toks[close + 1][0] == "{":
                i = close + 1
                continue
            args = _split_args(toks, i + 1, close)
            if len(args) > arity:
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
