"""Tests for the `deref-offset` transform (DerefOffsetToIndex)."""

from __future__ import annotations

import pytest

from deflated.transforms import DerefOffsetToIndex


class TestDerefOffsetToIndex:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("y = *(p + 4);", "y = p[4];"),
            ("z = *(ji + 8);", "z = ji[8];"),
            ("w = *(p + 0x10);", "w = p[0x10];"),  # hex offset preserved verbatim
            ("a = *(&mw + 12);", "a = (&mw)[12];"),  # address-of base parenthesised
            ("return *(buf + 2);", "return buf[2];"),
            ("f(*(p + 1), 0);", "f(p[1], 0);"),
        ],
    )
    def test_rewritten(self, src, expected) -> None:
        assert DerefOffsetToIndex().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "q = a * (b + c);",  # binary multiply, not a deref
            "q = foo() * (b + c);",  # `*` after a value (`)`)
            "w = *(int *)(p + 4);",  # cast, inner is not `IDENT +`
            "v = *(p + 4).field;",  # postfix `.` would re-associate
            "u = *(p + 4)->field;",  # postfix `->`
            "t = *(p + 4)[0];",  # postfix `[`
            "s = *(p + 4)(args);",  # postfix call
            "r = *(p + 4)++;",  # postfix increment
            "k = *(p + i);",  # non-literal offset
            "j = *(p - 4);",  # subtraction, not addition
            "h = *(a + b + 4);",  # multi-term base
            # Regression: a postfix `++`/`--` before `*` ends an operand, so the `*`
            # is the binary multiply (`(x++) * (p + 4)`), not a unary deref. Treating
            # it as a deref produced `x++ p[4]` -- invalid C with the multiply gone.
            "y = x++ *(p + 4);",
            "y = x-- *(p + 4);",
            # The mirror prefix case `++*(p + 4)` is textually identical at the `*`,
            # so it is declined too (lossless: a missed rewrite, never a wrong one).
            "y = ++*(p + 4);",
            "y = --*(p + 4);",
        ],
    )
    def test_kept(self, src) -> None:
        assert DerefOffsetToIndex().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "*(p + 4)"; x = *(p + 4);'
        assert DerefOffsetToIndex().apply(src) == 's = "*(p + 4)"; x = p[4];'

    def test_double_deref(self) -> None:
        assert DerefOffsetToIndex().apply("y = **(p + 4);") == "y = *p[4];"
