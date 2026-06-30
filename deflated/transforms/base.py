"""Transform framework: the tier taxonomy, transform interface, and tier parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum


class Tier(IntEnum):
    """Cumulative aggressiveness tiers, ordered by information loss.

    Each step up adds transforms with a single honest answer to "what might I
    lose?": T1 loses only formatting you did not write; T2 loses nothing
    meaningful; T3 discards machine-generated identifiers and type verbosity
    (decompiler bookkeeping); T4 discards low-confidence analyst signal (ABI
    keywords, decompiler warning banners) that is not recoverable from the text.
    """

    T0_RAW = 0  # no transformation
    T1_COSMETIC = 1  # lossless: formatting invisible to semantics
    T2_STRUCTURAL = 2  # lossless: information-preserving rewrites
    T3_CONTEXTUAL = 3  # lossy: discards machine-generated names / type verbosity
    T4_REDUCTIVE = 4  # lossy: discards low-confidence analyst signal


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

    Subclasses set :attr:`id` and :attr:`tier` and implement :meth:`apply`.
    A transform must be a pure function of its input string.
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
