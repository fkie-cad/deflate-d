"""Tier-level tests for T4 (reductive): cumulative + lossy reductions."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms import build_pipeline

T3_IDS = {"compress-funcs", "compress-names", "simplify-types"}
T4_IDS = {"comments-warning", "strip-callconv", "strip-i18n", "drop-code-cast"}


class TestTierT4:
    def test_membership_is_cumulative(self) -> None:
        ids = set(build_pipeline(4).ids())
        assert T3_IDS <= ids  # all contextual passes still present
        assert T4_IDS <= ids

    def test_warning_dropped_and_callconv_stripped(self) -> None:
        src = "/* WARNING: jumptable */\nvoid __cdecl f(void);\n"
        out = transform(src, Tier.T4_REDUCTIVE)
        assert "WARNING" not in out
        assert "__cdecl" not in out

    def test_contextual_effects_still_applied(self) -> None:
        out = transform("int iVar1;\niVar1 = 0;\n", Tier.T4_REDUCTIVE)
        assert "iVar1" not in out

    def test_string_safety(self) -> None:
        assert '"a  //  b"' in transform('char *s = "a  //  b";\n', Tier.T4_REDUCTIVE)

    def test_i18n_and_code_cast_reduced(self) -> None:
        out = transform('r = (*(code *)PTR_x)(); s = dcgettext(0, "msg", 5);\n', Tier.T4_REDUCTIVE)
        assert "(code" not in out  # function-pointer cast dropped
        assert "dcgettext" not in out and '"msg"' in out  # i18n wrapper unwrapped

    def test_reductions_are_t4_only(self) -> None:
        # The two new reductions must not leak into T3 (lossless-of-meaning).
        t3 = transform('s = dcgettext(0, "msg", 5); r = (*(code *)p)();\n', Tier.T3_CONTEXTUAL)
        assert "dcgettext" in t3 and "code" in t3  # both kept (whitespace-agnostic)
