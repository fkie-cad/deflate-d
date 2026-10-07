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

    def test_single_tab_unchanged(self) -> None:
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

    def test_preprocessor_directive_collapsed(self) -> None:
        t = CollapseInlineSpaces()
        assert t.apply("#include  <stdio.h>") == "#include <stdio.h>"
        assert t.apply("  #define  FOO  1") == " #define FOO 1"

    def test_comments_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        assert t.apply("a = b; // some   comment") == "a = b; // some   comment"
        assert t.apply("a = b; // some \tcomment") == "a = b; // some \tcomment"
        assert t.apply("a  = b; /*  some   comment  */") == "a = b; /*  some   comment  */"

    def test_line_breaks_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        assert t.apply("int  x;\n\n\n    y  =  1;") == "int x;\n\n\n y = 1;"

    def test_multiline_block_comment_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        code = "    x  =  1; /*  first   line\n    second   line  */\n    y  =  2;"
        assert t.apply(code) == " x = 1; /*  first   line\n    second   line  */\n y = 2;"

    def test_multiline_string_unchanged(self) -> None:
        # A `\`-newline continuation keeps the string open, so the next line's blanks are string content.
        t = CollapseInlineSpaces()
        code = '    p  =  "first   line\\\n    second   line";\n    y  =  2;'
        assert t.apply(code) == ' p = "first   line\\\n    second   line";\n y = 2;'

    def test_asm_block_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        code = "    x  =  1;  __asm  {  mov   eax,  ebx  }\n    y  =  2;"
        assert t.apply(code) == " x = 1; __asm  {  mov   eax,  ebx  }\n y = 2;"

    def test_multiline_asm_block_unchanged(self) -> None:
        t = CollapseInlineSpaces()
        code = "    __asm\n    {\n        mov   eax,  ebx\n        nop\n    }\n    y  =  2;"
        assert t.apply(code) == " __asm\n    {\n        mov   eax,  ebx\n        nop\n    }\n y = 2;"
