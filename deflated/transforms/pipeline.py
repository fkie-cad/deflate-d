"""Pipeline assembly: the Pipeline class, transform registry, and build helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .base import Tier, Transform, parse_tier
from .contextual import (
    AddressOfIndexToOffset,
    CompressFunctionNames,
    CompressPlaceholderNames,
    DropNullPointerCast,
    SimplifyLowConfidenceTypes,
    StripPointerSlotAddress,
    TrimPieceAccessSuffix,
)
from .cosmetic import (
    CollapseBlankLines,
    CollapseInlineSpaces,
    JoinLines,
    StripIndentation,
    StripTrailingWhitespace,
    TightenCommentSpaces,
    TightenWhitespace,
)
from .reductive import (
    DropCodePointerCast,
    DropCrtFunctions,
    ElideThunkBodies,
    EraseResolverStubs,
    RemoveWarningComments,
    StripCallingConventions,
    StripChkSuffix,
    StripConstQualifier,
    StripTranslationWrappers,
    StripWidthCasts,
    TrimSpuriousArgs,
)
from .structural import (
    CanonicalizeControlFlow,
    CoalesceDeclarations,
    CompoundAssignment,
    DerefOffsetToIndex,
    DropSingleStatementBraces,
    DropTrailingReturn,
    InlineSingleUseTemps,
    MinimizeIntegerLiterals,
    NormalizeFlagTemps,
    RedundantCastElision,
    RemoveComments,
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


# Canonical application order. A transform's position here and its tier are
# independent: the tier (the `# Tn` tag on each line) only decides *whether* it
# runs at a given target, while the position decides *when*, by what each pass
# needs from the ones before it. So the list is deliberately not sorted by tier:
# cosmetic normalization (T1) runs last so it tidies up after the other edits and
# so earlier passes still see one statement per line, and `decl-coalesce` (T2)
# sits among the T3 passes. `build_pipeline` filters this list by tier,
# preserving relative order.
#
# The registry holds transform *classes*, not instances: `build_pipeline`
# constructs a fresh object per call so two pipelines never share one. Module-level
# instances would be shared by every pipeline in the process, which makes any per-apply
# record a cross-pipeline data race -- concretely
# `CompressPlaceholderNames.current_mapping`, which callers read after `apply` to recover
# the rename map. Private instances make that read correct instead of racy.
# Reading `.id` / `.tier` / `.description` off this list still works
# because all three are class attributes declared on `Transform`.
#
# Every entry must therefore be constructible with no arguments. A variant that needs
# non-default constructor arguments is registered as a subclass that bakes them into
# its own `__init__` defaults -- not as a `functools.partial`, which would hide the
# class attributes the CLI's `--list` and the `--exclude` validation read from here.
ORDERED_TRANSFORMS: list[type[Transform]] = [
    NormalizeFlagTemps,  # T2 (cond:N -> condN; FIRST, before any pass can misread the colon)
    RemoveComments,  # T2
    TernaryFromIfElse,  # T2 (before inline: folds may expose a temp)
    InlineSingleUseTemps,  # T2 (before coalesce: dead decl still 1/line)
    RedundantCastElision,  # T2
    DropSingleStatementBraces,  # T2
    CompoundAssignment,  # T2
    CanonicalizeControlFlow,  # T2 (label/jump cleanup)
    MinimizeIntegerLiterals,  # T2 (hex int literals -> shorter decimal; lossless)
    DerefOffsetToIndex,  # T2 (*(p+N) -> p[N]; lossless)
    DropTrailingReturn,  # T2 (drops redundant trailing `return;`)
    CompressFunctionNames,  # T3 (file-global; runs before locals)
    CompressPlaceholderNames,  # T3
    SimplifyLowConfidenceTypes,  # T3
    DropNullPointerCast,  # T3 (drops redundant pointer cast on `0x0`)
    AddressOfIndexToOffset,  # T3 (&base[0xNN] -> (base+0xNN))
    StripPointerSlotAddress,  # T3 (PTR_<sym>_<addr> -> PTR_<sym>; after compress-names)
    TrimPieceAccessSuffix,  # T3 (._N_M_ -> ._N_M)
    # decl-coalesce groups declarators by their (exact) type spelling, so it runs
    # *after* simplify-types -- otherwise two runs that only become same-typed
    # once spellings are normalized (e.g. `signed __int64` + `__int64` -> `i64`)
    # merge on a later pass, leaving T3 non-idempotent and under-coalesced. At T2
    # (simplify-types absent) its output is byte-identical to the old position.
    CoalesceDeclarations,  # T2 (after simplify-types; see note above)
    RemoveWarningComments,  # T4 (drops genuine-signal warning banners)
    StripCallingConventions,  # T4 (drops genuine-signal ABI keywords)
    StripConstQualifier,  # T4 (drops the low-signal `const` qualifier)
    StripTranslationWrappers,  # T4 (drops i18n wrapper, keeps the message)
    StripWidthCasts,  # T4 (drops Hex-Rays pseudo-width casts (_BYTE)/(_DWORD)/...)
    DropCodePointerCast,  # T4 (drops Ghidra's (code *) call cast)
    StripChkSuffix,  # T4 (drops _chk FORTIFY suffix; before thunk-elision so the
    #     resulting self-call forwarders collapse)
    ElideThunkBodies,  # T4 (collapses pure forwarding thunks to a prototype)
    TrimSpuriousArgs,  # T4 (truncates surplus args on fixed-arity libc calls)
    EraseResolverStubs,  # T4 (deletes Binary Ninja CRT resolver-stub family)
    DropCrtFunctions,  # T4 (deletes CRT/ELF scaffolding functions by name)
    CollapseInlineSpaces,  # T1
    StripIndentation,  # T1
    StripTrailingWhitespace,  # T1
    CollapseBlankLines,  # T1
    JoinLines,  # T1 (joins the tidied lines)
    TightenCommentSpaces,  # T1
    TightenWhitespace,  # T1 (runs last: tightens punct + operators)
]


def build_pipeline(tier: str | int | Tier, *, exclude: set[str] | None = None) -> Pipeline:
    """Assemble the cumulative pipeline for ``tier``.

    Includes every transform whose ``tier`` is at or below the target. Pass
    ``exclude`` to drop transforms by ``id``; unknown ids raise ``ValueError``.

    The selected classes are instantiated here, once per call, so the returned
    pipeline owns its transforms outright: callers may hold several pipelines (or
    use them from several threads) without one apply clobbering another's state.
    Selection itself reads only the class attributes ``id`` and ``tier``, so no
    transform is constructed unless it makes the cut.
    """
    target = parse_tier(tier)
    exclude = exclude or set()
    unknown = exclude - {t.id for t in ORDERED_TRANSFORMS}
    if unknown:
        raise ValueError(f"unknown transform id(s): {', '.join(sorted(unknown))} (see --list)")
    chosen = [cls() for cls in ORDERED_TRANSFORMS if cls.tier <= target and cls.id not in exclude]
    return Pipeline(chosen)


def transform(code: str, tier: str | int | Tier, **kwargs) -> str:
    """Convenience: build the pipeline for ``tier`` and apply it to ``code``."""
    return build_pipeline(tier, **kwargs).apply(code)
