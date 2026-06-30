"""Pipeline assembly: the Pipeline class, transform registry, and build helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .base import Tier, Transform, parse_tier
from .contextual import (
    AddressOfIndexToOffset,
    CompressFunctionNames,
    CompressPlaceholderNames,
    DropCrtFunctions,
    DropNullPointerCast,
    ElideThunkBodies,
    EraseResolverStubs,
    NormalizeFlagTemps,
    SimplifyLowConfidenceTypes,
    StripCallingConventions,
    StripChkSuffix,
    StripConstQualifier,
    StripPointerSlotAddress,
    StripTranslationWrappers,
    TrimPieceAccessSuffix,
    TrimSpuriousArgs,
)
from .cosmetic import (
    CollapseBlankLines,
    CollapseInlineSpaces,
    CollapseLineBreaks,
    StripIndentation,
    StripTrailingWhitespace,
    TightenCommentSpaces,
    TightenWhitespace,
)
from .structural import (
    CanonicalizeControlFlow,
    CoalesceDeclarations,
    CompoundAssignment,
    DerefOffsetToIndex,
    DropCodePointerCast,
    DropSingleStatementBraces,
    DropTrailingReturn,
    InlineSingleUseTemps,
    MinimizeIntegerLiterals,
    RedundantCastElision,
    RemoveComments,
    RemoveWarningComments,
    StripWidthCasts,
    TernaryFromIfElse,
)


@dataclass
class Pipeline:
    """An ordered sequence of transforms applied left to right."""

    transforms: list[Transform]

    def apply(self, code: str) -> str:
        for transform in self.transforms:
            code = transform.apply(code)
        return code

    def ids(self) -> list[str]:
        return [t.id for t in self.transforms]


# Canonical application order. Structural/contextual/reductive rewrites run
# first; cosmetic normalization runs last so it tidies up after the other edits.
# `build_pipeline` filters this list by tier, preserving relative order.
ORDERED_TRANSFORMS: list[Transform] = [
    NormalizeFlagTemps(),  # T2 (cond:N -> condN; FIRST, before any pass can misread the colon)
    RemoveComments(),  # T2
    TernaryFromIfElse(),  # T2 (before inline: folds may expose a temp)
    InlineSingleUseTemps(),  # T2 (before coalesce: dead decl still 1/line)
    RedundantCastElision(),  # T2
    DropSingleStatementBraces(),  # T2
    CompoundAssignment(),  # T2
    CanonicalizeControlFlow(),  # T2 (label/jump cleanup; runs last)
    MinimizeIntegerLiterals(),  # T2 (hex int literals -> shorter decimal; lossless)
    DerefOffsetToIndex(),  # T2 (*(p+N) -> p[N]; lossless)
    DropTrailingReturn(),  # T2 (drops redundant trailing `return;`)
    CompressFunctionNames(),  # T3 (file-global; runs before locals)
    CompressPlaceholderNames(),  # T3
    SimplifyLowConfidenceTypes(),  # T3
    DropNullPointerCast(),  # T3 (drops redundant pointer cast on `0x0`)
    AddressOfIndexToOffset(),  # T3 (&base[0xNN] -> (base+0xNN))
    StripPointerSlotAddress(),  # T3 (PTR_<sym>_<addr> -> PTR_<sym>; after compress-names)
    TrimPieceAccessSuffix(),  # T3 (._N_M_ -> ._N_M)
    # decl-coalesce groups declarators by their (exact) type spelling, so it runs
    # *after* simplify-types -- otherwise two runs that only become same-typed
    # once spellings are normalized (e.g. `signed __int64` + `__int64` -> `i64`)
    # merge on a later pass, leaving T3 non-idempotent and under-coalesced. At T2
    # (simplify-types absent) its output is byte-identical to the old position.
    CoalesceDeclarations(),  # T2 (after simplify-types; see note above)
    RemoveWarningComments(),  # T4 (drops genuine-signal warning banners)
    StripCallingConventions(),  # T4 (drops genuine-signal ABI keywords)
    StripConstQualifier(),  # T4 (drops the low-signal `const` qualifier)
    StripTranslationWrappers(),  # T4 (drops i18n wrapper, keeps the message)
    StripWidthCasts(),  # T4 (drops Hex-Rays pseudo-width casts (_BYTE)/(_DWORD)/...)
    DropCodePointerCast(),  # T4 (drops Ghidra's (code *) call cast)
    StripChkSuffix(),  # T4 (drops _chk FORTIFY suffix; before thunk-elision so the
    #     resulting self-call forwarders collapse)
    ElideThunkBodies(),  # T4 (collapses pure forwarding thunks to a prototype)
    TrimSpuriousArgs(),  # T4 (truncates surplus args on fixed-arity libc calls)
    EraseResolverStubs(),  # T4 (deletes Binary Ninja CRT resolver-stub family)
    DropCrtFunctions(),  # T4 (deletes CRT/ELF scaffolding functions by name)
    CollapseInlineSpaces(),  # T1
    StripIndentation(),  # T1
    StripTrailingWhitespace(),  # T1
    CollapseBlankLines(),  # T1
    CollapseLineBreaks(),  # T1 (joins the tidied lines)
    TightenCommentSpaces(),  # T1
    TightenWhitespace(),  # T1 (runs last: tightens punct + operators)
]


def build_pipeline(tier: str | int | Tier, *, exclude: set[str] | None = None) -> Pipeline:
    """Assemble the cumulative pipeline for ``tier``.

    Includes every transform whose ``tier`` is at or below the target. Pass
    ``exclude`` to drop transforms by ``id``.
    """
    target = parse_tier(tier)
    exclude = exclude or set()
    chosen = [t for t in ORDERED_TRANSFORMS if t.tier <= target and t.id not in exclude]
    return Pipeline(chosen)


def transform(code: str, tier: str | int | Tier, **kwargs) -> str:
    """Convenience: build the pipeline for ``tier`` and apply it to ``code``."""
    return build_pipeline(tier, **kwargs).apply(code)
