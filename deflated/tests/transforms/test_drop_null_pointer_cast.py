"""Tests for the `null-cast` transform (DropNullPointerCast)."""

from __future__ import annotations

import pytest

from deflated.transforms import DropNullPointerCast


class TestDropNullPointerCast:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("x = (char *)0x0;", "x = 0;"),
            ("pcVar3 = (char *)0x0;", "pcVar3 = 0;"),
            ("if (db != (void *)0x0) {", "if (db != 0) {"),
            ("while (ppuVar2 != (undefined **)0x0) {", "while (ppuVar2 != 0) {"),
            ("return (char *)0x0;", "return 0;"),
            ("f((undefined4 *)0x0);", "f(0);"),
            ("p == (FILE *)0x0", "p == 0"),
            ("a = b == (int *)0x0 ? 1 : 2;", "a = b == 0 ? 1 : 2;"),
            # multi-word type spelling
            ("x = (unsigned int *)0x0;", "x = 0;"),
            ("x = (undefined *)0x0 == y;", "x = 0 == y;"),
            # `int-minform` (T2) re-spells `0x0` as `0` before this pass; the bare
            # `0` after a pointer cast is still the null constant.
            ("x = (char *)0;", "x = 0;"),
            ("if (db != (void *)0) {", "if (db != 0) {"),
        ],
    )
    def test_dropped(self, src, expected) -> None:
        assert DropNullPointerCast().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # Pointer arithmetic: `(char *)0x0 + i` is address i, `0 + i` is integer i.
            "p = (char *)0x0 + i;",
            "p = (char *)0x0 - 1;",
            # Subscript / member / deref would become ill-typed or change meaning.
            "c = (char *)0x0[i];",
            "x = *(char *)0x0;",
            # Not a pointer cast (no `*`): an integer cast of zero must stay.
            "y = (int)0x0;",
            "y = (size_t)0x0;",
            # Not a cast of `0x0` at all.
            "z = (a * b);",
            "w = (char *)p;",
            # The literal must be exactly 0x0, not another hex constant.
            "x = (char *)0x10;",
            # Cast spelling with an operator inside is not a type cast.
            "v = (a + b *)0x0;",
            # Regression: inside `sizeof(...)`/`_Alignof(...)` the cast fixes the
            # operand *type*, so it is load-bearing -- `sizeof((char *)0x0)` is
            # `sizeof(char *)` (8), not `sizeof(0)` (4). The enclosing `(` reads as
            # a safe-before token, so the sizeof/alignof case is excluded explicitly.
            "n = sizeof((char *)0x0);",
            "n = _Alignof((char *)0x0);",
            "n = sizeof((char *)0x0) + 1;",
            # Regression: when the cast+null is wrapped in its own parens, the
            # real operand context is OUTSIDE the wrap. An unsafe outer operator
            # must keep the cast -- `((int *)0x0)->f` -> `(0)->f` is invalid C, and
            # `((int *)0x0) + i` -> `(0)+i` drops the pointer arithmetic.
            "x = ((char *)0x0)[i];",
            "x = ((int *)0x0) + i;",
            "y = ((int *)0x0)->f;",
            "z = ((char *)0x0).m;",
            "w = ((char *)0x0) - 1;",
        ],
    )
    def test_kept(self, src) -> None:
        assert DropNullPointerCast().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            # A *call* argument (value before the open paren) is always safe, even
            # wrapped: the bare `0` is a complete argument.
            ("f((char *)0x0);", "f(0);"),
            ("f((char *)0x0, (void *)0x0);", "f(0, 0);"),
            ("g(f((char *)0x0));", "g(f(0));"),
            # A grouping whose outer context is safe still rewrites.
            ("return ((char *)0x0);", "return (0);"),
            ("b = ((char *)0x0) == p;", "b = (0) == p;"),
        ],
    )
    def test_wrapped_safe_outer_dropped(self, src, expected) -> None:
        assert DropNullPointerCast().apply(src) == expected

    def test_inside_string_not_touched(self) -> None:
        src = 's = "(char *)0x0";'
        assert DropNullPointerCast().apply(src) == src

    def test_multiple_in_one_statement(self) -> None:
        out = DropNullPointerCast().apply("f((char *)0x0, (void *)0x0);")
        assert out == "f(0, 0);"
