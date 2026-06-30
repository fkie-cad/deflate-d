"""Tests for the `inline-temps` transform (InlineSingleUseTemps)."""

from __future__ import annotations

from deflated.transforms import InlineSingleUseTemps


class TestInlineSingleUseTemps:
    def test_folds_into_return(self) -> None:
        t = InlineSingleUseTemps()
        assert t.apply("uVar1 = f(a, b); return uVar1;") == "return f(a, b);"

    def test_declared_spill_temp_dropped(self) -> None:
        t = InlineSingleUseTemps()
        out = t.apply("undefined8 uVar1;\nuVar1 = f();\nreturn uVar1;\n")
        assert "uVar1" not in out and "undefined8" not in out
        assert "return f();" in out

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
        out = t.apply('int uVar1;\nuVar1 = f("uVar1");\nreturn uVar1;\n')
        assert out == '\nreturn f("uVar1");\n'

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
        src = "undefined8 uVar1;\nx = 1;\nuVar1 = f();\nreturn uVar1;\n"
        out = t.apply(src)
        assert "undefined8" not in out and "uVar1" not in out
        assert "return f();" in out

    def test_string_safety(self) -> None:
        # An assign+return-of-temp pattern inside a string literal (where the
        # ``;`` are not statement separators) must not trigger a fold.
        t = InlineSingleUseTemps()
        assert t.apply('s = "uVar1 = f(); return uVar1;";') == 's = "uVar1 = f(); return uVar1;";'
