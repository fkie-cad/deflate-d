"""Tests for the `inline-temps` transform (InlineSingleUseTemps)."""

from __future__ import annotations

import pytest

from deflated.transforms import InlineSingleUseTemps


class TestInlineSingleUseTemps:
    def test_folds_into_return(self) -> None:
        t = InlineSingleUseTemps()
        assert t.apply("uVar1 = f(a, b); return uVar1;") == "return f(a, b);"

    def test_declared_spill_temp_dropped(self) -> None:
        t = InlineSingleUseTemps()
        out = t.apply("undefined8 g(void) {\n  undefined8 uVar1;\n  uVar1 = f();\n  return uVar1;\n}\n")
        assert out == "undefined8 g(void) {\n  return f();\n}\n"

    def test_used_more_than_once_kept(self) -> None:
        t = InlineSingleUseTemps()
        src = "x = f(); g(x); return x;"
        assert t.apply(src) == src

    def test_self_referential_initializer_kept(self) -> None:
        t = InlineSingleUseTemps()
        src = "x = x + 1; return x;"
        assert t.apply(src) == src

    def test_next_statement_not_bare_return_kept(self) -> None:
        t = InlineSingleUseTemps()
        src = "x = f(); return x + 1;"
        assert t.apply(src) == src

    def test_name_inside_string_initializer_does_not_block_fold(self) -> None:
        # Regression: the temp name appearing inside a *string literal* in its own
        # initializer must not be read as a self-reference (the use count is
        # CODE-only, so the self-ref guard must be too).
        t = InlineSingleUseTemps()
        out = t.apply('int g(void) {\n  int uVar1;\n  uVar1 = f("uVar1");\n  return uVar1;\n}\n')
        assert out == 'int g(void) {\n  return f("uVar1");\n}\n'

    def test_volatile_temp_kept(self) -> None:
        # A `volatile` temp's store-then-load is observable, so it must not be
        # inlined away even though its shape matches a single-use spill temp.
        t = InlineSingleUseTemps()
        src = "volatile int uVar1;\nuVar1 = f();\nreturn uVar1;\n"
        assert t.apply(src) == src

    def test_two_inlinable_temps_in_one_function(self) -> None:
        t = InlineSingleUseTemps()
        src = "uVar1 = f(); return uVar1;\nuVar2 = g(); return uVar2;\n"
        out = t.apply(src)
        assert "uVar1" not in out and "uVar2" not in out
        assert "return f();" in out and "return g();" in out

    def test_non_adjacent_declaration_dropped(self) -> None:
        # Decl at top, assign+return later — the declaration should be removed.
        t = InlineSingleUseTemps()
        src = "undefined8 g(void) {\n  undefined8 uVar1;\n  x = 1;\n  uVar1 = f();\n  return uVar1;\n}\n"
        assert t.apply(src) == "undefined8 g(void) {\n  x = 1;\n  return f();\n}\n"

    def test_string_safety(self) -> None:
        # An assign+return-of-temp pattern inside a string literal (where the
        # ``;`` are not statement separators) must not trigger a fold.
        t = InlineSingleUseTemps()
        assert t.apply('s = "uVar1 = f(); return uVar1;";') == 's = "uVar1 = f(); return uVar1;";'

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("int f(void) {\n  char c;\n  c = g();\n  return c;\n}", "int f(void) {\n  return (char)g();\n}"),
            ("double f(void) {\n  int c;\n  c = 3.7;\n  return c;\n}", "double f(void) {\n  return (int)3.7;\n}"),
            ("int f(void) {\n  char c;\n  c = a + b;\n  return c;\n}", "int f(void) {\n  return (char)(a + b);\n}"),
        ],
    )
    def test_keeps_conversion_through_temp_type(self, src, expected) -> None:
        # The store into the temp converts to its type; the fold keeps that as a cast.
        assert InlineSingleUseTemps().apply(src) == expected

    @pytest.mark.parametrize(
        "src,expected",
        [
            (
                "undefined8 f(void) {\n  undefined8 uVar1;\n  uVar1 = g();\n  return uVar1;\n}",
                "undefined8 f(void) {\n  return g();\n}",
            ),
            ("char *f(void) {\n  char *p;\n  p = g();\n  return p;\n}", "char *f(void) {\n  return g();\n}"),
        ],
    )
    def test_no_cast_when_temp_type_is_return_type(self, src, expected) -> None:
        assert InlineSingleUseTemps().apply(src) == expected

    def test_cast_when_return_type_not_found(self) -> None:
        # Without a function header the types cannot be compared, so the cast is kept.
        out = InlineSingleUseTemps().apply("undefined8 uVar1;\nuVar1 = f();\nreturn uVar1;\n")
        assert out == "\nreturn (undefined8)f();\n"

    @pytest.mark.parametrize("keyword", ["delete", "throw"])
    def test_keyword_statement_is_not_a_declaration(self, keyword) -> None:
        # `delete p;` is not the declaration of `p`, so it must not be dropped as dead.
        src = f"T *f(void)\n{{\n  {keyword} p;\n  p = g();\n  return p;\n}}\n"
        assert f"{keyword} p;" in InlineSingleUseTemps().apply(src)
