"""Tier-level tests for T2 (structural): cumulative + lossless guarantees."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms import build_pipeline

T1_IDS = {"ws-collapse", "ws-indent", "ws-trailing", "ws-blanklines", "ws-newlines", "ws-tighten"}
T2_IDS = {"comments", "ternary", "inline-temps", "decl-coalesce", "cast-elision", "brace-elision", "compound-assign", "cfg-canon"}


class TestTierT2:
    def test_membership_is_cumulative(self) -> None:
        ids = set(build_pipeline(2).ids())
        assert T1_IDS <= ids  # T2 still includes every cosmetic pass
        assert T2_IDS <= ids

    def test_still_applies_whitespace(self) -> None:
        # The cosmetic passes keep running at T2.
        out = transform("int   x   =   0;\n", Tier.T2_STRUCTURAL)
        assert "  " not in out

    def test_comments_removed_but_warning_kept(self) -> None:
        out = transform("int x;  // note\n/* WARNING: jumptable */\nint y;\n", Tier.T2_STRUCTURAL)
        assert "note" not in out
        assert "WARNING" in out

    def test_lossless_no_renaming(self) -> None:
        # T3-only lossy passes must not fire at T2.
        src = "int iVar1;\nlocal_28 = param_1;\n__int64 q;\n"
        out = transform(src, Tier.T2_STRUCTURAL)
        assert "iVar1" in out and "local_28" in out
        assert "__int64" in out  # simplify-types is T3

    def test_string_safety(self) -> None:
        assert '"a  //  b"' in transform('char *s = "a  //  b";\n', Tier.T2_STRUCTURAL)
