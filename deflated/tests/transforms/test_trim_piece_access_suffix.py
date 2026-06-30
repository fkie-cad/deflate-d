"""Tests for the `piece-access` transform (TrimPieceAccessSuffix)."""

from __future__ import annotations

import pytest

from deflated.transforms import TrimPieceAccessSuffix


class TestTrimPieceAccessSuffix:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("lb._8_8_ = x;", "lb._8_8 = x;"),
            ("mh[0]._0_2_ = y;", "mh[0]._0_2 = y;"),
            ("a = b._4_12_;", "a = b._4_12;"),
            ("p->_1_7_ = z;", "p->_1_7 = z;"),
        ],
    )
    def test_trimmed(self, src, expected) -> None:
        assert TrimPieceAccessSuffix().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "q._8_8_foo = 1;",  # a longer member name, not a piece suffix
            "x.field = 1;",  # ordinary member
            "y = a_8_8_;",  # not a member access (no . or ->)
        ],
    )
    def test_kept(self, src) -> None:
        assert TrimPieceAccessSuffix().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "x._8_8_";'
        assert TrimPieceAccessSuffix().apply(src) == src
