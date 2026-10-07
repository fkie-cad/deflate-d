"""Tests for the `ws-indent` transform (StripIndentation)."""

from __future__ import annotations

from deflated.transforms import StripIndentation


class TestStripIndentation:
    def test_leading_whitespace_removed(self) -> None:
        s = StripIndentation()
        assert s.apply("    int x;") == "int x;"
        assert s.apply("\t\treturn 0;") == "return 0;"

    def test_after_whitespace_not_removed(self) -> None:
        s = StripIndentation()
        assert s.apply("int x;  ") == "int x;  "
        assert s.apply("return 0;\t") == "return 0;\t"

    def test_interior_spaces_untouched(self) -> None:
        s = StripIndentation()
        assert s.apply("  int  x = 1;") == "int  x = 1;"
        assert s.apply("  int  x \t = 1;") == "int  x \t = 1;"

    def test_blank_lines_stay_blank(self) -> None:
        s = StripIndentation()
        assert s.apply("    a;\n   \n    b;") == "a;\n\nb;"
        assert s.apply("    a;   \n  \n c; \n  b;") == "a;   \n\nc; \nb;"

    def test_comments(self) -> None:
        t = StripIndentation()
        assert t.apply(" // some   comment") == "// some   comment"
        assert t.apply("\t// some \tcomment") == "// some \tcomment"
        assert t.apply(" /* some   comment */") == "/* some   comment */"
        assert t.apply("\t\t/* some \tcomment */") == "/* some \tcomment */"

    def test_string_escape_indentation_preserved(self) -> None:
        # Indentation written inside a string (after a \n escape) is string
        # content, not code indentation: only the code line's leading whitespace
        # is stripped.
        s = StripIndentation()
        assert s.apply(r'    printf("line1\n    line2");') == r'printf("line1\n    line2");'

    def test_multiline_block_comment_indentation_removed(self) -> None:
        # Comments are not protected, so the inner lines of a block comment lose their indentation too.
        s = StripIndentation()
        code = "    x  =  1; /*  first   line\n    second   line  */\n    y  =  2;"
        assert s.apply(code) == "x  =  1; /*  first   line\nsecond   line  */\ny  =  2;"

    def test_multiline_string_indentation_preserved(self) -> None:
        # A `\`-newline continuation keeps the string open, so the next line's indentation is string content.
        s = StripIndentation()
        code = '    p  =  "first   line\\\n    second   line";\n    y  =  2;'
        assert s.apply(code) == 'p  =  "first   line\\\n    second   line";\ny  =  2;'

    def test_asm_block_unchanged(self) -> None:
        s = StripIndentation()
        code = "    x  =  1;  __asm  {  mov   eax,  ebx  }\n    y  =  2;"
        assert s.apply(code) == "x  =  1;  __asm  {  mov   eax,  ebx  }\ny  =  2;"

    def test_multiline_asm_block_indentation_preserved(self) -> None:
        # Only the `__asm` line itself is code; the lines inside the block keep their indentation.
        s = StripIndentation()
        code = "    __asm\n    {\n        mov   eax,  ebx\n        nop\n    }\n    y  =  2;"
        assert s.apply(code) == "__asm\n    {\n        mov   eax,  ebx\n        nop\n    }\ny  =  2;"

    def test_asm_block_opened_mid_line(self) -> None:
        # Line 1 starts as code, so its indentation is removed even though it ends inside the block; `    }   ` starts
        # inside the block, so its indentation is kept.
        s = StripIndentation()
        code = "    x = 1; __asm {   \n\n\n      nop   \n    }   \n\n\n    y = 2;   "
        assert s.apply(code) == "x = 1; __asm {   \n\n\n      nop   \n    }   \n\n\ny = 2;   "

    def test_string_opened_mid_line(self) -> None:
        # Line 1 starts as code, so its indentation is removed; line 2 starts inside the string, so it is kept.
        s = StripIndentation()
        code = '    p = "abc   \\\n    def   ";   \n\n\n    y = 2;   '
        assert s.apply(code) == 'p = "abc   \\\n    def   ";   \n\n\ny = 2;   '
