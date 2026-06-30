"""Tests for the `decl-coalesce` transform (CoalesceDeclarations)."""

from __future__ import annotations

from deflated.transforms import CoalesceDeclarations


class TestCoalesceDeclarations:
    def test_same_type_uninitialized_grouped(self) -> None:
        c = CoalesceDeclarations()
        out = c.apply("int a;\nint b;\nint c;\nlong d;\n")
        assert "int a, b, c;" in out
        assert "long d;" in out

    def test_initialized_declarations_left_alone(self) -> None:
        c = CoalesceDeclarations()
        out = c.apply("int a = 1;\nint b = 2;\n")
        assert "int a = 1;" in out and "int b = 2;" in out

    def test_grouped_by_type(self) -> None:
        c = CoalesceDeclarations()
        out = c.apply("int iVar1; ulong uVar2, uVar3; int iVar4;")
        assert "int iVar1, iVar4;" in out
        assert "ulong uVar2, uVar3;" in out

    def test_keyword_statements_not_coalesced(self) -> None:
        c = CoalesceDeclarations()
        out = c.apply("goto h; return iVar1;")
        assert "goto h;" in out and "return iVar1;" in out

    def test_pointer_declarations_coalesced(self) -> None:
        c = CoalesceDeclarations()
        out = c.apply("int *p;\nint *q;\n")
        assert "int *p, *q;" in out

    def test_multiword_type_coalesced(self) -> None:
        c = CoalesceDeclarations()
        out = c.apply("unsigned int a;\nunsigned int b;\n")
        assert "unsigned int a, b;" in out

    def test_array_declaration_not_coalesced(self) -> None:
        # '['  in the declarator makes it non-consolidatable.
        c = CoalesceDeclarations()
        src = "int arr[4];\nint b;\n"
        out = c.apply(src)
        assert "int arr[4];" in out and "int b;" in out

    def test_single_declaration_unchanged(self) -> None:
        c = CoalesceDeclarations()
        src = "int x;\n"
        assert c.apply(src) == src

    def test_string_and_comment_safety(self) -> None:
        # Declaration-like text inside a literal or comment must not be merged.
        c = CoalesceDeclarations()
        assert c.apply('s = "int a; int b;";') == 's = "int a; int b;";'
        # A comment between two declarations breaks the run; the literal is intact.
        assert c.apply("int a; /* int b; */ int c;") == "int a; /* int b; */ int c;"
