"""Tests for the `flag-temps` transform (NormalizeFlagTemps)."""

from __future__ import annotations

import pytest

from deflated import Tier, transform
from deflated.transforms import NormalizeFlagTemps


class TestNormalizeFlagTemps:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("bool cond:0 = fe;", "bool cond0 = fe;"),
            ("if (x && cond:0) y();", "if (x && cond0) y();"),
            ("a = cond:12_1;", "a = cond12_1;"),
        ],
    )
    def test_normalized(self, src, expected) -> None:
        assert NormalizeFlagTemps().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # A label / ternary colon is not a flag temp.
            "x = a ? b : c;",
            "goto done; done: return;",
            "cond = 1;",  # no colon
        ],
    )
    def test_kept(self, src) -> None:
        assert NormalizeFlagTemps().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "cond:0";'
        assert NormalizeFlagTemps().apply(src) == src

    def test_compressed_away_at_t3(self) -> None:
        # After normalization the `condN` placeholder is renamed by compress-names.
        out = transform("bool cond:0 = fe; if (x && cond:0) g();", Tier.T3_CONTEXTUAL)
        assert "cond" not in out

    def test_statement_leading_cond_survives_cfg_canon(self) -> None:
        # Regression: a statement-leading `cond:N = ...` must NOT be misread as a
        # goto label `cond:` by cfg-canon (which would drop it and orphan the
        # assignment). The normalization runs first (T2), so the colon is gone
        # before any structural pass sees it. The lvalue must survive at T2.
        out = transform("cond:1 = rax_1 > 2; if (cond:1) g();", Tier.T2_STRUCTURAL)
        assert "cond1" in out  # the lvalue is preserved, not dropped
        assert "=" in out.split(";")[0]  # still an assignment, not an orphan

    def test_normalization_is_t2(self) -> None:
        # The colon fix is information-preserving, so it lands at T2 (and thus
        # runs before the T2 structural passes that could misread the colon).
        from deflated.transforms import NormalizeFlagTemps

        assert NormalizeFlagTemps().tier == Tier.T2_STRUCTURAL
        assert "cond:" not in transform("a = cond:0;", Tier.T2_STRUCTURAL)
