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
