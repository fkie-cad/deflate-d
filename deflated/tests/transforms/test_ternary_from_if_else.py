"""Tests for the `ternary` transform (TernaryFromIfElse)."""

from __future__ import annotations

import pytest

from deflated.transforms import TernaryFromIfElse


class TestTernaryFromIfElse:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("if (c) { x = 1; } else { x = 2; }", "x = c ? 1 : 2;"),
            ("if (a < b) x = a; else x = b;", "x = a < b ? a : b;"),
            ("if (c) { x = f(); } else { x = g(); }", "x = c ? f() : g();"),
        ],
    )
    def test_folded(self, src, expected) -> None:
        assert TernaryFromIfElse().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "if (c) x = 1; else y = 2;",  # different lvalues
            "if (c) { x = 1; y = 2; } else { x = 3; }",  # multi-statement branch
            "if (c) x = 1;",  # no else
            "if (c) x = a ? 1 : 2; else x = 3;",  # nested ternary in branch RHS
            # A bare `=` in the condition is an unconditional side effect: folding
            # would make `x = y` conditional, so the fold must be refused.
            "if (x = y) { z = a; } else { z = b; }",
            "if (p = next()) { r = 1; } else { r = 0; }",
            "if (c) x = a ? 1 : 2; else x = 3;",  # nested ternary in then-arm RHS
            "if (c) x = 3; else x = a ? 1 : 2;",  # nested ternary in else-arm RHS
            "if (a, b) x = 1; else x = 2;",  # top-level comma in condition
            "if (a = b) x = 1; else x = 2;",  # assignment in condition binds looser than ?:
            "if (a += b) x = 1; else x = 2;",  # compound assignment in condition
        ],
    )
    def test_kept(self, src) -> None:
        assert TernaryFromIfElse().apply(src) == src

    def test_equality_in_condition_still_folds(self) -> None:
        # `==` is a distinct token from `=`, so an equality test remains foldable.
        assert TernaryFromIfElse().apply("if (x == y) z = a; else z = b;") == "z = x == y ? a : b;"

    def test_bare_assignment_in_condition_not_folded(self) -> None:
        # A bare `=` in the condition is a side effect that must run
        # unconditionally; folding it into `z = (x = y) ? a : b` would make the
        # assignment conditional, so the fold is refused (`=` is in
        # `_TERNARY_UNSAFE`). Contrast `test_equality_in_condition_still_folds`,
        # where the distinct `==` token folds.
        src = "if (x = y) z = a; else z = b;"
        assert TernaryFromIfElse().apply(src) == src

    def test_multiple_folds_in_one_apply(self) -> None:
        # Two independent if/else pairs must both collapse in a single call.
        src = "if (a) x = 1; else x = 2; if (b) y = 3; else y = 4;"
        out = TernaryFromIfElse().apply(src)
        assert "x = a ? 1 : 2;" in out
        assert "y = b ? 3 : 4;" in out

    def test_call_with_comma_args_in_branch_folded(self) -> None:
        # Comma inside f(a,b) is at depth>0, so not a top-level comma.
        out = TernaryFromIfElse().apply("if (c) x = f(a, b); else x = g(d, e);")
        assert "x = c ? f(a, b) : g(d, e);" == out

    def test_string_and_comment_safety(self) -> None:
        # if/else text inside a string or comment must never be folded.
        t = TernaryFromIfElse()
        assert t.apply('s = "if (c) x = 1; else x = 2;";') == 's = "if (c) x = 1; else x = 2;";'
        assert t.apply("y = 0; /* if (c) x = 1; else x = 2; */") == "y = 0; /* if (c) x = 1; else x = 2; */"
