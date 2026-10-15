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
            ("p = (char*)(char *)q;", "p = (char *)q;"),  # same type, different spacing
            ("x = (unsigned int)(unsigned int)y;", "x = (unsigned int)y;"),
            ("p = (struct foo *)(struct foo *)q;", "p = (struct foo *)q;"),
            ("p = (code *)(code *)q;", "p = (code *)q;"),
            ("x = (long)(int)(int)y;", "x = (long)(int)y;"),
            ("x = ((int)(int)y);", "x = ((int)y);"),
            ("return (int)(int)x;", "return (int)x;"),
        ],
    )
    def test_collapsed(self, src, expected) -> None:
        assert RedundantCastElision().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "x = (uint)(byte)y;",  # different casts are not redundant
            "r = (fp)(fp);",  # call-through-pointer, not a cast
            "x = (int)(long)(int)y;",  # the identical casts are not adjacent
            "x = (a, b *)(a, b *);",  # a comma expression is not a type
            "x = (c ? p * q : r)(c ? p * q : r);",  # a conditional expression is not a type
        ],
    )
    def test_kept(self, src) -> None:
        assert RedundantCastElision().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        [
            "y = f(a * b)(a * b);",
            "y = (*get)(n * 2)(n * 2);",
            "x = (a * b)(a * b);",
        ],
    )
    def test_call_with_expression_argument_is_not_a_cast(self, src) -> None:
        # `f(a * b)` returns a function pointer that is then called with `a * b`; neither group is a type.
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

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("x = (int) (int) y;", "x = (int) y;"),
            ("x = (int)\n(int)y;", "x = (int)y;"),
        ],
    )
    def test_whitespace_after_removed_cast_is_dropped(self, src, expected) -> None:
        assert RedundantCastElision().apply(src) == expected

    def test_triple_cast_collapses_to_one(self) -> None:
        out = RedundantCastElision().apply("x = (int)(int)(int)y;")
        assert out == "x = (int)y;"

    def test_collapses_many_stacked_casts(self) -> None:
        src = " ".join(f"a{i} = (int)(int)b;" for i in range(70))
        assert RedundantCastElision().apply(src) == " ".join(f"a{i} = (int)b;" for i in range(70))

    def test_collapses_deep_cast_chain(self) -> None:
        assert RedundantCastElision().apply("x = " + "(int)" * 100 + "y;") == "x = (int)y;"

    def test_cast_inside_string_literal_not_touched(self) -> None:
        src = 's = "(int)(int)x";'
        assert RedundantCastElision().apply(src) == src

    @pytest.mark.parametrize("src", ["x = (int)(int", "x = (int)("])
    def test_unbalanced_parentheses_left_alone(self, src) -> None:
        assert RedundantCastElision().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        ["x = (int)(int)(int)y;", "x = (long)(int)(int)y;", "x = (int) (int) y;", "p = (char*)(char *)q;"],
    )
    def test_idempotent(self, src) -> None:
        once = RedundantCastElision().apply(src)
        assert RedundantCastElision().apply(once) == once
