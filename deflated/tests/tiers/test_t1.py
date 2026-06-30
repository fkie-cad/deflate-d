"""Tier-level tests for T1 (cosmetic): the assembled cosmetic pipeline."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms import build_pipeline

T1_IDS = ["ws-collapse", "ws-indent", "ws-trailing", "ws-blanklines", "ws-newlines", "ws-comments", "ws-tighten"]


class TestTierT1:

    def test_membership(self) -> None:
        assert build_pipeline(1).ids() == T1_IDS
        assert all(t.tier == Tier.T1_COSMETIC for t in build_pipeline(1).transforms)

    def test_whitespace_normalized(self) -> None:
        out = transform("int   x   =   0;\n\n\n    return  x;\n", Tier.T1_COSMETIC)
        assert "  " not in out  # no runs of 2+ spaces
        for line in out.split("\n"):
            assert line == line.strip()  # no leading/trailing whitespace

    def test_idempotent(self) -> None:
        src = "int   x   =   0;\n\n\n    return  x;\n"
        once = transform(src, Tier.T1_COSMETIC)
        assert transform(once, Tier.T1_COSMETIC) == once

    def test_tab_collapse(self) -> None:
        out = transform("int\tx;", Tier.T1_COSMETIC)
        assert out == "int x;"

    def test_mixed_spaces_collapse(self) -> None:
        out = transform("\t \t int\t \tx;", Tier.T1_COSMETIC)
        assert out == "int x;"

    def test_comments_kept(self) -> None:
        # T1 is purely cosmetic: comments survive (removal starts at T2).
        assert "set x" in transform("int x = 1;  // set x\n", Tier.T1_COSMETIC)

    def test_string_safety(self) -> None:
        assert '"a  //  b"' in transform('char *s = "a  //  b";\n', Tier.T1_COSMETIC)

    def test_string_escape_interior_preserved(self) -> None:
        # A string's interior --- its \n escapes and the spaces around them --- is
        # content, not code layout, so the line-oriented cosmetic passes
        # (indent/trailing/blanklines) must pass it through untouched.
        src = (
            "int f(void){\n"
            r'  puts("line1\n    line2\n\n    line3");' "\n"
            "  return 0;\n"
            "}\n"
        )
        assert r'"line1\n    line2\n\n    line3"' in transform(src, Tier.T1_COSMETIC)

    def test_preprocessor_directive_preserved(self) -> None:
        out = transform("#define  A   1\nint x = A;\n", Tier.T1_COSMETIC)
        assert "#define A 1" in out.split("\n")
