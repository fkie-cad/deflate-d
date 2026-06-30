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

    def test_triple_cast_collapses_to_one(self) -> None:
        # Iterative passes should remove both redundant outer copies.
        out = RedundantCastElision().apply("x = (int)(int)(int)y;")
        assert out == "x = (int)y;"

    def test_cast_inside_string_literal_not_touched(self) -> None:
        src = 's = "(int)(int)x";'
        assert RedundantCastElision().apply(src) == src
