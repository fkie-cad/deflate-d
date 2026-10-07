"""T3 --- contextual, lossy transforms (machine-generated artifacts).

These discard information the decompiler *synthesized* rather than recovered:
placeholder identifier names (built from stack offsets / SSA indices) and verbose
type spellings. Meaning and internal consistency are preserved, but the discarded
strings (an address, an offset) are gone from the text --- low-value decompiler
bookkeeping. Confidence-gated so symbol-anchored names survive.
"""

from __future__ import annotations

import itertools
import re
import string

from .base import Tier, Transform
from .ctokens import CINT, CNUMBER, ctokenize as _tok_offsets, match_delimiter as _match_delim
from .lexer import SegmentType, scan

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
                close = _match_delim(toks, j)
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
        return "".join(
            (big.sub(lambda m: mapping[m.group(0)], text) if seg_type == SegmentType.CODE else text) for seg_type, text in segments
        )

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
        #: The {placeholder: short_name} map for the code :meth:`apply` returned most
        #: recently --- ``{}`` before the first call. Read it straight after the
        #: ``apply`` whose output you hold; the next ``apply`` on this instance
        #: replaces it.
        #:
        #: This is the only way to recover the mapping from a pipeline run, because
        #: ``compress-names`` rewrites text that earlier passes already changed, so its
        #: input cannot be reconstructed from the original source::
        #:
        #:     p = build_pipeline("T3")
        #:     out = p.apply(src)
        #:     m = next(t for t in p.transforms if t.id == "compress-names").current_mapping
        #:
        #: Safe because ``build_pipeline`` gives every pipeline its own instances; with
        #: the module-level instances this class used to be registered with, two
        #: pipelines would overwrite each other's value here.
        self.current_mapping: dict[str, str] = {}

    def apply(self, code: str) -> str:
        # Records the mapping for callers that only have the pipeline, then returns
        # just the text. The attribute is write-only from the transform's side: it is
        # never read back, so the rewrite stays a pure function of `code`.
        rewritten, mapping = self.apply_with_mapping(code)
        self.current_mapping = mapping
        return rewritten

    def apply_with_mapping(self, code: str) -> tuple[str, dict[str, str]]:
        """Rewrite ``code`` and return it together with the {placeholder: short_name} map.

        The rename is one-way in the text: once ``local_10`` has become ``b``, nothing
        in the output says which variable ``b`` was. A caller that needs to attribute
        something back to the original identity --- a variable-name recovery evaluation
        scoring a model's predictions against ground truth keyed by the decompiler's
        placeholder --- needs this map as the join key.

        Prefer this over :attr:`current_mapping` wherever you call the transform
        directly: it hands the map back with the text it describes, so there is no
        window in which the two can drift apart.
        """
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
            return code, {}

        gen = _short_names(used=set(existing))
        mapping = {name: next(gen) for name in unique}

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
        return "".join(out), dict(mapping)


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
    _GROUPING_BEFORE = frozenset(
        {"return", "sizeof", "if", "while", "for", "switch", "case", "do", "else", "goto", "_Alignof", "alignof", "typeof"}
    )
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
            close = _match_delim(toks, i)
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
            if before == "(" and after == ")" and _match_delim(toks, i - 1) == null_idx + 1:
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

    Semantically identical, but lossy for the reader (hence T3): the subscript
    spelling marks ``a`` as an array and the literal as an element index, while
    the pointer-add form drops that hint and reads easily as a byte offset. It
    is the inverse of the T2 ``deref-offset`` rewrite, which *adds* the index
    reading; the asymmetry is intentional.
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

    def apply(self, code: str) -> str:
        toks = _tok_offsets(code)
        n = len(toks)
        edits: list[tuple[int, int, str]] = []
        i = 0
        while i + 4 < n:
            if toks[i][0] == "&" and _IDENT.fullmatch(toks[i + 1][0]) and toks[i + 2][0] == "[":
                close = _match_delim(toks, i + 2)
                prev = toks[i - 1][0] if i > 0 else None
                # `&` is binary (bitwise-and) only after a value: a non-keyword
                # identifier, a number, or a closing `)`/`]`. After a keyword
                # (`return`), an operator, or `(`/`,`/`;` it is unary address-of.
                is_value = prev is not None and (
                    prev in self._VALUE_BEFORE or CNUMBER.fullmatch(prev) or (_IDENT.fullmatch(prev) and prev not in _RESERVED)
                )
                unary = not is_value
                after = toks[close + 1][0] if close is not None and close + 1 < n else None
                # ``CINT``, not ``CNUMBER``: a match here *performs* the rewrite,
                # and only an integer is a valid subscript to fold into a pointer
                # add. (Above, a match only declines, so the wider form is safe.)
                if close == i + 4 and unary and CINT.fullmatch(toks[i + 3][0]) and after not in self._BLOCK_AFTER:
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
        return "".join(
            (big.sub(lambda m: mapping[m.group(0)], text) if seg_type == SegmentType.CODE else text) for seg_type, text in segments
        )


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
