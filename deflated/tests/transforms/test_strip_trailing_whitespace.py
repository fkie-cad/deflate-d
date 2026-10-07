"""Tests for the `ws-trailing` transform (StripTrailingWhitespace)."""

from __future__ import annotations

from deflated.transforms import StripTrailingWhitespace


class TestStripTrailingWhitespace:
    def test_trailing_whitespace_removed(self) -> None:
        s = StripTrailingWhitespace()
        assert s.apply("int x;   ") == "int x;"
        assert s.apply("return 0;\t") == "return 0;"

    def test_leading_whitespace_not_removed(self) -> None:
        s = StripTrailingWhitespace()
        assert s.apply("    int x;") == "    int x;"
        assert s.apply("\t\treturn 0;") == "\t\treturn 0;"

    def test_interior_and_leading_spaces_untouched(self) -> None:
        s = StripTrailingWhitespace()
        assert s.apply("  int  x = 1;  ") == "  int  x = 1;"

    def test_per_line(self) -> None:
        s = StripTrailingWhitespace()
        assert s.apply("a; \nb;  ") == "a;\nb;"
        assert s.apply("    a;   \n  \n c; \n  b;") == "    a;\n\n c;\n  b;"

    def test_comments(self) -> None:
        t = StripTrailingWhitespace()
        assert t.apply(" // some   comment") == " // some   comment"
        assert t.apply("\t// some \tcomment\t") == "\t// some \tcomment"
        assert t.apply("/* some   comment */\t") == "/* some   comment */"
        assert t.apply("/* some \tcomment */   ") == "/* some \tcomment */"

    def test_string_escape_trailing_preserved(self) -> None:
        # Trailing spaces written inside a string (before a \n escape) are string
        # content and must survive; only the code line's trailing run is removed.
        s = StripTrailingWhitespace()
        assert s.apply(r'printf("line1   \nline2");   ') == r'printf("line1   \nline2");'

    def test_multiline_block_comment_trailing_removed(self) -> None:
        # Comments are not protected, so the inner lines of a block comment lose their trailing whitespace too.
        s = StripTrailingWhitespace()
        code = "x = 1; /* first line   \n    second line  */  \ny = 2;  "
        assert s.apply(code) == "x = 1; /* first line\n    second line  */\ny = 2;"

    def test_multiline_string_trailing_preserved(self) -> None:
        # A `\`-newline continuation keeps the string open; the blanks before the closing quote are string content.
        s = StripTrailingWhitespace()
        code = 'p = "first line   \\\n    second line   ";  \ny = 2;  '
        assert s.apply(code) == 'p = "first line   \\\n    second line   ";\ny = 2;'

    def test_frozen_string_trailing_preserved(self) -> None:
        # A string still open at a bare newline is frozen up to the newline, so its trailing blanks are kept.
        s = StripTrailingWhitespace()
        assert s.apply('p = "abc   \ny = 2;  ') == 'p = "abc   \ny = 2;'

    def test_asm_block_unchanged(self) -> None:
        s = StripTrailingWhitespace()
        code = "x = 1;  __asm { mov eax, ebx   }  \ny = 2;  "
        assert s.apply(code) == "x = 1;  __asm { mov eax, ebx   }\ny = 2;"

    def test_multiline_asm_block_trailing_preserved(self) -> None:
        # Every line from `__asm` to the closing `}` lies inside the block; only the code after `}` is stripped.
        s = StripTrailingWhitespace()
        code = "__asm  \n{  \n    mov eax, ebx   \n    nop  \n}  \ny = 2;  "
        assert s.apply(code) == "__asm  \n{  \n    mov eax, ebx   \n    nop  \n}\ny = 2;"

    def test_asm_block_opened_mid_line(self) -> None:
        # Line 1 starts as code but ends inside the block, so its trailing blanks are kept; `    }   ` starts inside
        # the block but ends as code, so its trailing blanks are removed.
        s = StripTrailingWhitespace()
        code = "    x = 1; __asm {   \n\n\n      nop   \n    }   \n\n\n    y = 2;   "
        assert s.apply(code) == "    x = 1; __asm {   \n\n\n      nop   \n    }\n\n\n    y = 2;"

    def test_string_opened_mid_line(self) -> None:
        # Line 2 starts inside the string but ends as code, so the blanks after `";` are removed and the ones before
        # the closing quote are kept.
        s = StripTrailingWhitespace()
        code = '    p = "abc   \\\n    def   ";   \n\n\n    y = 2;   '
        assert s.apply(code) == '    p = "abc   \\\n    def   ";\n\n\n    y = 2;'
