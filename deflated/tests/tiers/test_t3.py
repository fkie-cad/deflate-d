"""Tier-level tests for T3 (contextual): cumulative + name/type compression."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms import build_pipeline

T2_IDS = {"comments", "ternary", "inline-temps", "decl-coalesce", "cast-elision", "brace-elision", "compound-assign", "cfg-canon"}
T3_IDS = {"compress-funcs", "compress-names", "simplify-types"}


class TestTierT3:
    def test_membership_is_cumulative(self) -> None:
        ids = set(build_pipeline(3).ids())
        assert T2_IDS <= ids  # all structural passes still present
        assert T3_IDS <= ids

    def test_placeholders_renamed_consistently(self) -> None:
        src = "int iVar1;\nlocal_28 = param_1;\niVar1 = local_28 + uStack_20;\n"
        out = transform(src, Tier.T3_CONTEXTUAL)
        for ph in ("iVar1", "local_28", "param_1", "uStack_20"):
            assert ph not in out
        # Two distinct placeholders -> two distinct names; structure preserved.
        assert out.count("+") == 1

    def test_types_simplified(self) -> None:
        out = transform("__int64 q;\n", Tier.T3_CONTEXTUAL)
        assert "i64" in out and "__int64" not in out

    def test_warning_and_callconv_still_present(self) -> None:
        src = "/* WARNING: jumptable */\nvoid __cdecl f(void);\n"
        out = transform(src, Tier.T3_CONTEXTUAL)
        assert "WARNING" in out  # comments-warning is T4
        assert "__cdecl" in out  # strip-callconv is T4

    def test_still_applies_whitespace(self) -> None:
        assert "  " not in transform("int   x   =   0;\n", Tier.T3_CONTEXTUAL)

    def test_string_safety(self) -> None:
        assert '"a  //  b"' in transform('char *s = "a  //  b";\n', Tier.T3_CONTEXTUAL)
