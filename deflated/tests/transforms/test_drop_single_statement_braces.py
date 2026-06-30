"""Tests for the `brace-elision` transform (DropSingleStatementBraces)."""

from __future__ import annotations

from deflated.transforms import DropSingleStatementBraces


class TestDropSingleStatementBraces:
    def test_single_statement_block_unwrapped(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("if (c) {\n  x = 1;\n}\n")
        assert "{" not in out and "}" not in out
        assert "x = 1;" in out

    def test_if_else_unwrapped_without_token_merge(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("if (c) {\n  x = 1;\n} else {\n  y = 2;\n}\n")
        assert "{" not in out and "}" not in out
        assert " else " in out and "elsey" not in out

    def test_multi_statement_block_kept(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("if (c) {\n  a = 1;\n  b = 2;\n}\n")
        assert "{" in out and "}" in out

    def test_function_body_kept(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("int f(void) {\n  return 1;\n}\n")
        assert "{" in out and "}" in out

    def test_dangling_else_kept(self) -> None:
        # Unwrapping the inner `if` would let `else` rebind to it.
        b = DropSingleStatementBraces()
        out = b.apply("if (a) {\n  if (b) f();\n} else {\n  g();\n}\n")
        assert out.count("{") == 1

    def test_switch_braces_kept(self) -> None:
        # A switch body carrying a case/default label needs its braces:
        # `switch(x)case 1:break;` is invalid C. Even a single-statement switch
        # body must keep them (regression for switch being wrongly elidable).
        b = DropSingleStatementBraces()
        for src in ("switch (x) {\n  case 1: break;\n}\n", "switch (x) {\n  case 1: g();\n}\n", "switch (x) {\n  default: h();\n}\n"):
            assert "{" in b.apply(src) and "}" in b.apply(src), src

    def test_sole_declaration_kept(self) -> None:
        # `if (c) int x;` is invalid C, so the braces must remain.
        b = DropSingleStatementBraces()
        out = b.apply("if (c) {\n  int x;\n}\n")
        assert "{" in out

    def test_initialized_declaration_kept(self) -> None:
        # `if (c) int x = 1;` is also invalid C (a declaration is not a valid
        # sub-statement), so the braces must remain even with an initializer.
        b = DropSingleStatementBraces()
        assert "{" in b.apply("if (c) {\n  int x = 1;\n}\n")

    def test_declaration_with_call_init_kept(self) -> None:
        b = DropSingleStatementBraces()
        assert "{" in b.apply("if (c) {\n  int x = f(a, b);\n}\n")

    def test_array_declaration_kept(self) -> None:
        b = DropSingleStatementBraces()
        assert "{" in b.apply("if (c) {\n  int arr[3];\n}\n")

    def test_assignment_with_member_lhs_unwrapped(self) -> None:
        # `p->x = 1;` is an assignment, not a declaration, so braces still drop.
        b = DropSingleStatementBraces()
        out = b.apply("if (c) {\n  p->x = 1;\n}\n")
        assert "{" not in out and "p->x = 1;" in out

    def test_do_while_unwrapped(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("do {\n  f();\n} while (c);\n")
        assert "{" not in out and "do " in out

    def test_goto_body_unwrapped(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("if (c) {\n  goto LAB_1;\n}\n")
        assert "{" not in out and "goto LAB_1;" in out

    def test_braces_inside_string_preserved(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply('if (c) {\n  s = "{ }";\n}\n')
        assert '"{ }"' in out

    def test_labeled_inner_if_keeps_braces(self) -> None:
        # The block body is `LABEL: if (b) ...;`. The label must not hide the
        # inner `if` from the dangling-else guard: dropping these braces would let
        # the outer `else` re-bind to the inner `if` (a semantic change).
        b = DropSingleStatementBraces()
        out = b.apply("if (a) { L1: if (b) x = 1; } else x = 2;")
        assert out.count("{") == 1 and out.count("}") == 1

    def test_labeled_simple_statement_unwrapped(self) -> None:
        # A label before a *simple* statement is fine to unwrap (the label's scope
        # is the whole function, so moving it out of the braces is harmless).
        b = DropSingleStatementBraces()
        out = b.apply("if (a) { L1: x = 1; }")
        assert "{" not in out and "L1: x = 1;" in out

    def test_else_if_single_statement_unwrapped(self) -> None:
        # `else if (c) { stmt; }` should unwrap like a plain `if` (the merged
        # `else if` clause is recognised as a control head).
        b = DropSingleStatementBraces()
        out = b.apply("if (a) x = 1; else if (b) { y = 2; }")
        assert "{" not in out and "y = 2;" in out

    def test_else_if_dangling_else_still_guarded(self) -> None:
        # Even via the `else if` head, a brace-wrapped inner `if` is never unwrapped.
        b = DropSingleStatementBraces()
        out = b.apply("if (a) x = 1; else if (b) { if (c) f(); } else g();")
        assert out.count("{") == 1

    def test_while_single_statement_unwrapped(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("while (c) {\n  f();\n}\n")
        assert "{" not in out and "while" in out and "f();" in out

    def test_for_single_statement_unwrapped(self) -> None:
        b = DropSingleStatementBraces()
        out = b.apply("for (i = 0; i < n; i++) {\n  f(i);\n}\n")
        assert "{" not in out and "for" in out and "f(i);" in out

    def test_nested_if_inner_stripped_outer_kept(self) -> None:
        # The inner single-statement `if` loses its braces, but the OUTER braces
        # are kept on purpose: its body begins with a control keyword (`if`), so
        # unwrapping it could let a trailing `else` re-bind (dangling-else
        # safety, see the transform docstring).
        b = DropSingleStatementBraces()
        out = b.apply("if (a) {\n  if (b) {\n    f();\n  }\n}\n")
        assert out.count("{") == 1 and out.count("}") == 1  # only the outer pair remains
        assert "f();" in out
