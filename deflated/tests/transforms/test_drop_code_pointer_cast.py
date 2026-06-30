"""Tests for the `drop-code-cast` transform (DropCodePointerCast)."""

from __future__ import annotations

from deflated.transforms import DropCodePointerCast


class TestDropCodePointerCast:
    def test_indirect_call_cast_dropped(self) -> None:
        c = DropCodePointerCast()
        assert c.apply("(*(code *)PTR_func_0010b000)();") == "(*PTR_func_0010b000)();"

    def test_pointer_to_pointer_cast_dropped(self) -> None:
        c = DropCodePointerCast()
        assert c.apply("x = (code **)p;") == "x = p;"

    def test_multiple_casts_in_one_input(self) -> None:
        c = DropCodePointerCast()
        out = c.apply("(*(code *)a)(); (*(code *)b)();")
        assert "(code" not in out and out.count("(*") == 2

    def test_multiplication_not_a_cast(self) -> None:
        # `code * 2` has no closing paren right after the star -> not a cast.
        c = DropCodePointerCast()
        assert c.apply("y = code * 2;") == "y = code * 2;"

    def test_declaration_not_a_cast(self) -> None:
        # `code *p;` has no surrounding parens -> a declaration, not a cast.
        c = DropCodePointerCast()
        assert c.apply("code *p; code **q;") == "code *p; code **q;"

    def test_code_inside_identifier_not_matched(self) -> None:
        c = DropCodePointerCast()
        assert c.apply("(*(encode *)p)();") == "(*(encode *)p)();"

    def test_cast_inside_string_preserved(self) -> None:
        c = DropCodePointerCast()
        assert c.apply('s = "(code *)x";') == 's = "(code *)x";'
