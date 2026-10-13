"""Tests for the `cast-elision` transform (RedundantCastElision)."""

from __future__ import annotations

import pytest

from deflated.transforms import RedundantCastElision


class TestRedundantCastElision:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("x = (int)(int)y;", "x = (int)y;"),
            ("p = (char *)(char *)q;", "p = (char *)q;"),
            ("x = (uint)(uint)-y;", "x = (uint)-y;"),
            ("x = (int)(int)(a+b);", "x = (int)(a+b);"),
        ],
    )
    def test_collapsed(self, src, expected) -> None:
        assert RedundantCastElision().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "x = (uint)(byte)y;",  # different casts are not redundant
            "r = (fp)(fp);",  # call-through-pointer, not a cast
        ],
    )
    def test_kept(self, src) -> None:
        assert RedundantCastElision().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        [
            "(*fp)(*fp);",
            "x = (*fp)(*fp);",
            "(*fp)(*fp)(y);",
            "(**pp)(**pp);",
        ],
    )
    def test_call_through_function_pointer_is_not_a_cast(self, src) -> None:
        # A type never starts with `*`; `(*fp)(*fp)` calls fp with the argument *fp.
        assert RedundantCastElision().apply(src) == src

    def test_triple_cast_collapses_to_one(self) -> None:
        # Iterative passes should remove both redundant outer copies.
        out = RedundantCastElision().apply("x = (int)(int)(int)y;")
        assert out == "x = (int)y;"

    def test_collapses_many_stacked_casts(self) -> None:
        # More double casts than the old 64-round loop could remove one at a time.
        src = " ".join(f"a{i} = (int)(int)b;" for i in range(70))
        assert RedundantCastElision().apply(src) == " ".join(f"a{i} = (int)b;" for i in range(70))

    def test_collapses_deep_cast_chain(self) -> None:
        assert RedundantCastElision().apply("x = " + "(int)" * 100 + "y;") == "x = (int)y;"

    def test_cast_inside_string_literal_not_touched(self) -> None:
        src = 's = "(int)(int)x";'
        assert RedundantCastElision().apply(src) == src
