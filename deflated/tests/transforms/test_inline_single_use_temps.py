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

    def test_return_type_found_after_earlier_fold(self) -> None:
        # An earlier fold shortens its piece; the lookup of the enclosing function must still use the original
        # offsets, or it lands in the previous function's header and compares against the wrong return type.
        name = "uVar" + "x" * 40
        src = (
            f"char f1(void) {{\n  char {name};\n  {name} = a();\n  return {name};\n}}\n"
            "int f2(void) {\n  char c;\n  c = h();\n  return c;\n}\n"
        )
        out = InlineSingleUseTemps().apply(src)
        assert out == "char f1(void) {\n  return a();\n}\nint f2(void) {\n  return (char)h();\n}\n"

    @pytest.mark.parametrize(
        "src",
        [
            "int x;\nint f(void) {\n  x = g();\n  return x;\n}\n",
            "int f(void) {\n  x = g();\n  return x;\n}\nint x;\n",
            "int f(void) {\n  extern int x;\n  x = g();\n  return x;\n}\n",
        ],
    )
    def test_global_kept(self, src) -> None:
        # The store to a global is observable, so neither it nor the global's declaration may be dropped.
        assert InlineSingleUseTemps().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("int f(void) {\n  static int x;\n  x = g();\n  return x;\n}", "int f(void) {\n  return g();\n}"),
            ("int f(void) {\n  register int x;\n  x = g();\n  return x;\n}", "int f(void) {\n  return g();\n}"),
            ("int f(void) {\n  static char x;\n  x = g();\n  return x;\n}", "int f(void) {\n  return (char)g();\n}"),
            ("int f(void) {\n  register char x;\n  x = g();\n  return x;\n}", "int f(void) {\n  return (char)g();\n}"),
        ],
    )
    def test_storage_class_not_part_of_cast(self, src, expected) -> None:
        # `static` and `register` belong to the declaration, not the type: `(static int)` is not valid C.
        assert InlineSingleUseTemps().apply(src) == expected

    def test_equality_is_not_an_assignment(self) -> None:
        src = "x == y; return x;"
        assert InlineSingleUseTemps().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        [
            "int f(void) {\n  int x;\n  if (c) x = g();\n  return x;\n}",
            "int f(void) {\n  int x;\n  if (c) h(); else x = g();\n  return x;\n}",
            "int f(void) {\n  int x;\n  while (c) x = g();\n  return x;\n}",
        ],
    )
    def test_unbraced_conditional_assignment_kept(self, src) -> None:
        # The assignment only runs on one path, so the return cannot take its value.
        assert InlineSingleUseTemps().apply(src) == src

    def test_calling_convention_ignored_in_return_type(self) -> None:
        src = "undefined4 __stdcall f(void) {\n  undefined4 x;\n  x = g();\n  return x;\n}"
        assert InlineSingleUseTemps().apply(src) == "undefined4 __stdcall f(void) {\n  return g();\n}"

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("struct S f(void) {\n  struct S s;\n  s = g();\n  return s;\n}", "struct S f(void) {\n  return g();\n}"),
            (
                "const char *f(void) {\n  const char *p;\n  p = g();\n  return p;\n}",
                "const char *f(void) {\n  return g();\n}",
            ),
        ],
    )
    def test_no_cast_for_multiword_return_type(self, src, expected) -> None:
        assert InlineSingleUseTemps().apply(src) == expected

    def test_name_reused_in_other_function_kept(self) -> None:
        # Counts are over the whole input, so a second function using the same name blocks both folds.
        src = (
            "int f(void) {\n  int x;\n  x = g();\n  return x;\n}\n"
            "int h(void) {\n  int x;\n  x = g();\n  return x;\n}\n"
        )
        assert InlineSingleUseTemps().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        [
            "int f(void) {\n  int a, x;\n  x = g();\n  return x;\n}",
            "int f(void) {\n  int x = 0;\n  x = g();\n  return x;\n}",
        ],
    )
    def test_unrecognized_declaration_kept(self, src) -> None:
        # The declaration does not match the single-name form, so the use count is off by one and blocks the fold.
        assert InlineSingleUseTemps().apply(src) == src

    def test_parenthesized_return_kept(self) -> None:
        src = "x = g(); return (x);"
        assert InlineSingleUseTemps().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            (
                "int f(void) {\n  int x;\n  if (c) {\n    x = g();\n    return x;\n  }\n  return 0;\n}",
                "int f(void) {\n  if (c) {\n    return g();\n  }\n  return 0;\n}",
            ),
            (
                "int f(void) {\n  char x;\n  if (c) {\n    x = g();\n    return x;\n  }\n  return 0;\n}",
                "int f(void) {\n  if (c) {\n    return (char)g();\n  }\n  return 0;\n}",
            ),
        ],
    )
    def test_return_type_found_in_nested_block(self, src, expected) -> None:
        # Inner braces do not change the enclosing function, so its return type is still known and a same-type temp
        # folds without a cast.
        assert InlineSingleUseTemps().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "x = a, f(); return x;",
            "int f(void) {\n  int x;\n  x = a, g();\n  return x;\n}",
        ],
    )
    def test_top_level_comma_kept(self, src) -> None:
        # `=` binds tighter than `,`: `x = a, g();` stores `a`, but `return a, g();` would return `g()`.
        assert InlineSingleUseTemps().apply(src) == src

    def test_comma_inside_call_folds(self) -> None:
        # A comma between call arguments is not the comma operator.
        assert InlineSingleUseTemps().apply("x = f(a, b); return x;") == "return f(a, b);"

    def test_stray_closing_brace_stops_inlining(self) -> None:
        # After a stray `}` the scope of every statement is unknown, so no declaration is matched and nothing folds.
        src = "}\nint f(void){int x;x=g();return x;}"
        assert InlineSingleUseTemps().apply(src) == src

    def test_stray_closing_brace_after_function_does_not_matter(self) -> None:
        src = "int f(void){int x;x=g();return x;}\n}"
        assert InlineSingleUseTemps().apply(src) == "int f(void){return g();}\n}"

    def test_name_in_macro_body_kept(self) -> None:
        # A macro body can expand to a use of the temp, so a name in a `#define` counts as one and blocks the fold.
        src = "#define USE uVar1\nint g(void) {\n  int uVar1;\n  uVar1 = f();\n  return uVar1;\n}\n"
        assert InlineSingleUseTemps().apply(src) == src
