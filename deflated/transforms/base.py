"""Transform framework: the tier taxonomy, transform interface, and tier parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum


class Tier(IntEnum):
    """Cumulative aggressiveness tiers, ordered by information loss.

    Each tier includes all transforms of the tiers below it.
    """

    #: No transformation.
    T0_RAW = 0
    #: Lossless: formatting invisible to semantics.
    T1_COSMETIC = 1
    #: Semantics-preserving rewrites; drops all comments (including address metadata).
    T2_STRUCTURAL = 2
    #: Lossy: discards decompiler bookkeeping (machine-generated names, type verbosity,
    #: reading hints).
    T3_CONTEXTUAL = 3
    #: Lossy: discards low-confidence analyst signal (ABI keywords, warning banners,
    #: width casts) and boilerplate bodies (thunks, resolver stubs, CRT functions).
    T4_REDUCTIVE = 4


_TIER_ALIASES = {
    "0": Tier.T0_RAW,
    "raw": Tier.T0_RAW,
    "t0": Tier.T0_RAW,
    "1": Tier.T1_COSMETIC,
    "cosmetic": Tier.T1_COSMETIC,
    "t1": Tier.T1_COSMETIC,
    "2": Tier.T2_STRUCTURAL,
    "structural": Tier.T2_STRUCTURAL,
    "t2": Tier.T2_STRUCTURAL,
    "3": Tier.T3_CONTEXTUAL,
    "contextual": Tier.T3_CONTEXTUAL,
    "t3": Tier.T3_CONTEXTUAL,
    "4": Tier.T4_REDUCTIVE,
    "reductive": Tier.T4_REDUCTIVE,
    "t4": Tier.T4_REDUCTIVE,
}


def parse_tier(value: str | int | Tier) -> Tier:
    """Resolve a tier from an int, a :class:`Tier`, or a name/number string."""
    if isinstance(value, Tier):
        return value
    if isinstance(value, int):
        return Tier(value)
    key = str(value).strip().lower()
    if key not in _TIER_ALIASES:
        valid = ", ".join(sorted(_TIER_ALIASES))
        raise ValueError(f"unknown tier {value!r}; valid: {valid}")
    return _TIER_ALIASES[key]


class Transform(ABC):
    """A single source-to-source rewrite.

    Subclasses set attributes `id`, `tier` and `description` and implement method `apply`.
    To take effect, the *class* must be added to ``ORDERED_TRANSFORMS`` in `deflated.transforms.pipeline.py`;
    `build_pipeline` instantiates it once per pipeline, so the class must be constructible with no arguments and
    `apply` must be a pure function of its argument. It may record something for the caller to read afterward
    (`CompressPlaceholderNames.current_mapping`), as long as it never reads that record back.
    """

    #: Stable short identifier, used on the CLI (``--exclude``) and in reports.
    id: str = "unknown"
    #: The tier at which this transform is included.
    tier: Tier = Tier.T0_RAW
    #: Human-readable summary, shown by ``--list-verbose``.
    description: str = "unknown"

    @abstractmethod
    def apply(self, code: str) -> str:
        """Return ``code`` rewritten by this transform."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{self.id} {self.tier.name}>"
