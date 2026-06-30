"""Tests for the `ws-collapse` transform (CollapseInlineSpaces)."""

from __future__ import annotations

from deflated.transforms import CollapseInlineSpaces


class TestCollapseInlineSpaces:
    def test_runs_of_spaces_collapse(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("int    x  =  1;") == "int x = 1;"

    def test_tabs_collapse(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("int\t\tx;") == "int x;"

    def test_tab_collapse(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("int\tx;") == "int\tx;"

    def test_single_space_unchanged(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("int x = 1;") == "int x = 1;"

    def test_string_literal_preserved(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply('s = "a    b";') == 's = "a    b";'

    def test_space_front(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("  int x = 1;") == " int x = 1;"

    def test_tab_front(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("\tint x = 1;") == "\tint x = 1;"

    def test_tabs_front(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("\t\tint x = 1;") == " int x = 1;"

    def test_mixed_spaces_collapse(self) -> None:
        c = CollapseInlineSpaces()
        assert c.apply("\t \t int\t \tx;") == " int x;"

    def test_preprocessor_directive_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        assert t.apply("#include  <stdio.h>") == "#include <stdio.h>"
        assert t.apply("  #define  FOO  1") == " #define FOO 1"

    def test_comments_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        assert t.apply("a = b; // some   comment") == "a = b; // some   comment"
        assert t.apply("a = b; // some \tcomment") == "a = b; // some \tcomment"