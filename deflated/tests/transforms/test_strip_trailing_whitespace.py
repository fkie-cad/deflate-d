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
        assert t.apply(" // some   comment"  ) == " // some   comment"
        assert t.apply("\t// some \tcomment\t") == "\t// some \tcomment"
        assert t.apply("/* some   comment */\t") == "/* some   comment */"
        assert t.apply("/* some \tcomment */   ") == "/* some \tcomment */"

    def test_string_escape_trailing_preserved(self) -> None:
        # Trailing spaces written inside a string (before a \n escape) are string
        # content and must survive; only the code line's trailing run is removed.
        s = StripTrailingWhitespace()
        assert s.apply(r'printf("line1   \nline2");   ') == r'printf("line1   \nline2");'