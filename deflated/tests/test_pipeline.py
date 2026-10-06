"""Cross-cutting pipeline tests: membership, monotonic size, tier parsing."""

from __future__ import annotations

import pytest

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


def test_build_pipeline_rejects_unknown_exclude_id() -> None:
    with pytest.raises(ValueError):
        build_pipeline("T3", exclude={"no-such-id"})


def test_pipelines_do_not_share_transform_instances() -> None:
    # The registry holds transform *classes*, so every build_pipeline() call gets
    # fresh instances. Sharing them would let one pipeline clobber another's
    # CompressPlaceholderNames.current_mapping, which is exactly what that
    # attribute is read for.
    a, b = build_pipeline("T3"), build_pipeline("T3")
    assert all(x is not y for x, y in zip(a.transforms, b.transforms))


def test_placeholder_mapping_is_recoverable_from_a_pipeline() -> None:
    # The documented way to get the rename map back out of a pipeline run, and the
    # reason current_mapping exists: compress-names rewrites text that earlier
    # passes already changed, so a caller cannot re-derive the map from `src`.
    p = build_pipeline("T3")
    out = p.apply("void FUN_1(int param_1){ int local_10; local_10 = param_1; }")
    mapping = next(t for t in p.transforms if t.id == "compress-names").current_mapping
    assert set(mapping) == {"param_1", "local_10"}
    for old, new in mapping.items():
        assert old not in out and new in out

    # A second pipeline must not disturb the first one's record.
    build_pipeline("T3").apply("void FUN_9(int param_9){ int local_99; local_99 = param_9; }")
    assert set(mapping) == {"param_1", "local_10"}


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
