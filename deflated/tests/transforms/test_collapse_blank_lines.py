"""Tests for the `ws-blanklines` transform (CollapseBlankLines)."""

from __future__ import annotations

from deflated.transforms import CollapseBlankLines


class TestCollapseBlankLines:
    def test_runs_collapse_to_one(self) -> None:
        c = CollapseBlankLines()
        assert c.apply("a;\n\n\n\nb;") == "a;\n\nb;"

    def test_single_blank_kept(self) -> None:
        c = CollapseBlankLines()
        assert c.apply("a;\n\nb;") == "a;\n\nb;"

    def test_leading_and_trailing_blanks_dropped(self) -> None:
        c = CollapseBlankLines()
        assert c.apply("\n\na;\nb;\n\n") == "a;\nb;"
        assert c.apply("\n\n  a;\n\n  \n  b;\nc;  \n\n\n\n") == "  a;\n\n  b;\nc;  "

    def test_whitespace_only_lines_count_as_blank(self) -> None:
        c = CollapseBlankLines()
        assert c.apply("a;\n   \n\t\nb;") == "a;\n\nb;"

    def test_blank_lines_in_string_escape_preserved(self) -> None:
        # Blank lines written inside a string are \n escapes (content on one
        # physical line), not collapsible structural blank lines.
        c = CollapseBlankLines()
        assert c.apply(r'printf("line1\n\n\nline2");') == r'printf("line1\n\n\nline2");'
