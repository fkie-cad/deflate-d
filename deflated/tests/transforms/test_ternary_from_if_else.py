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

    @pytest.mark.parametrize(
        "src",
        [
            "if (i++ < 3) a[i] = 1; else a[i] = 2;",  # condition changes i, lvalue reads it
            "if ((i += 1) < 3) a[i] = 1; else a[i] = 2;",
            "if (f()) a[i] = 1; else a[i] = 2;",  # f() may change i
            "if (i < 3) a[i++] = 1; else a[i++] = 2;",  # lvalue changes i, condition reads it
            "if (n > 0) *next() = 1; else *next() = 2;",  # next() may change n
            "if (*p < 3) a[i++] = 1; else a[i++] = 2;",  # p may point to i
            "if (b[0] < 3) a[i++] = 1; else a[i++] = 2;",  # b[0] may be i
            "if ((*fp)()) a[i] = 1; else a[i] = 2;",  # calls through a function pointer may change i
            "if ((**(code **)(*plVar1 + 8))(plVar1) == 0) a[i] = 1; else a[i] = 2;",
            "if (tab[0](x)) a[i] = 1; else a[i] = 2;",
        ],
    )
    def test_no_fold_when_condition_and_lvalue_would_be_unsequenced(self, src) -> None:
        # In the if, the condition runs before the lvalue; in `LV = C ? A : B` their order is not fixed.
        assert TernaryFromIfElse().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("if (f(x) == 0) uVar2 = 1; else uVar2 = 2;", "uVar2 = f(x) == 0 ? 1 : 2;"),
            ("if (c) a[j++] = 1; else a[j++] = 2;", "a[j++] = c ? 1 : 2;"),
            ("if (s.n > 0) a[j++] = 1; else a[j++] = 2;", "a[j++] = s.n > 0 ? 1 : 2;"),
            ("if ((int)(n) < 0) a[i] = 1; else a[i] = 2;", "a[i] = (int)(n) < 0 ? 1 : 2;"),  # a cast is not a call
            ("if (i++ < 3) x = 1; else x = 2;", "x = i++ < 3 ? 1 : 2;"),
        ],
    )
    def test_side_effect_folds_when_order_cannot_matter(self, src, expected) -> None:
        assert TernaryFromIfElse().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "if (a) {\n  if (b) {\n    x = 1;\n  }\n  else {\n    x = 2;\n  }\n}\nelse {\n  x = 3;\n}\n",
            "if (a) {\n  x = 3;\n}\nelse {\n  if (b) {\n    x = 1;\n  }\n  else {\n    x = 2;\n  }\n}\n",
            "if (a) x = 1; else x = 2;\nif (b) y = 1; else y = 2;\n",
        ],
    )
    def test_one_pass_reaches_fixed_point(self, src) -> None:
        # A fold never enables an enclosing one (its branch would hold a top-level `?`), so a second run must find
        # nothing.
        once = TernaryFromIfElse().apply(src)
        assert TernaryFromIfElse().apply(once) == once
