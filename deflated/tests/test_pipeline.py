"""Cross-cutting pipeline tests: membership, monotonic size, tier parsing."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms import build_pipeline
from deflated.transforms.base import parse_tier


def test_pipeline_membership() -> None:
    assert all(t.tier == Tier.T1_COSMETIC for t in build_pipeline(1).transforms)
    assert "compress-names" in build_pipeline(3).ids()
    t3_ids, t4_ids = build_pipeline(3).ids(), build_pipeline(4).ids()
    assert "strip-callconv" not in t3_ids
    assert "comments-warning" not in t3_ids
    assert "strip-callconv" in t4_ids
    assert "comments-warning" in t4_ids


def test_exclude_drops_transform() -> None:
    assert "compress-names" not in build_pipeline(3, exclude={"compress-names"}).ids()


def test_monotonic_size(ghidra_sample: str) -> None:
    sizes = [len(transform(ghidra_sample, tier)) for tier in (0, 1, 2, 3, 4)]
    assert all(a >= b for a, b in zip(sizes, sizes[1:]))
    assert sizes[4] < sizes[0]


def test_parse_tier_aliases() -> None:
    assert parse_tier(3) == Tier.T3_CONTEXTUAL
    assert parse_tier("t3") == Tier.T3_CONTEXTUAL
    assert parse_tier("contextual") == Tier.T3_CONTEXTUAL


def test_tiers_are_cumulative() -> None:
    # Each higher tier keeps every transform of the tier below and adds at least
    # one of its own (T1 ⊂ T2 ⊂ T3 ⊂ T4).
    for lo, hi in ((1, 2), (2, 3), (3, 4)):
        assert set(build_pipeline(lo).ids()) < set(build_pipeline(hi).ids())


def test_each_transform_added_at_its_own_tier() -> None:
    # A transform first appears at exactly the tier it declares -- guards against
    # a mis-tiered transform leaking into a lower tier.
    for tier in (1, 2, 3, 4):
        added = set(build_pipeline(tier).ids()) - set(build_pipeline(tier - 1).ids())
        assert all(t.tier == Tier(tier) for t in build_pipeline(tier).transforms if t.id in added)


def test_cosmetic_normalization_runs_last() -> None:
    # T1 cosmetic transforms must run after the structural/contextual edits they
    # tidy up: in the assembled pipeline the T1 ids form the trailing block.
    tiers = [t.tier for t in build_pipeline(4).transforms]
    first_cosmetic = tiers.index(Tier.T1_COSMETIC)
    assert all(t == Tier.T1_COSMETIC for t in tiers[first_cosmetic:])
    assert all(t != Tier.T1_COSMETIC for t in tiers[:first_cosmetic])
