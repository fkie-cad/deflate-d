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

    def test_multiline_block_comment_blank_lines_collapsed(self) -> None:
        # Comments are not protected, so blank lines inside a block comment collapse too.
        c = CollapseBlankLines()
        code = "x = 1; /* first\n\n\n   \nlast */\n\n\ny = 2;"
        assert c.apply(code) == "x = 1; /* first\n\nlast */\n\ny = 2;"

    def test_multiline_string_unchanged(self) -> None:
        # A `\`-newline continuation keeps the string open; only the blank lines after it collapse.
        c = CollapseBlankLines()
        code = 'p = "first \\\n   ";\n\n\ny = 2;'
        assert c.apply(code) == 'p = "first \\\n   ";\n\ny = 2;'

    def test_whitespace_only_line_in_string_kept(self) -> None:
        # The `   ` line continues the string, so it is string content and not a blank line.
        c = CollapseBlankLines()
        code = 'p = "abc \\\n   \n\n\ny = 2;'
        assert c.apply(code) == 'p = "abc \\\n   \n\ny = 2;'

    def test_asm_block_unchanged(self) -> None:
        c = CollapseBlankLines()
        assert c.apply("x = 1; __asm { nop }\n\n\ny = 2;") == "x = 1; __asm { nop }\n\ny = 2;"

    def test_multiline_asm_block_blank_lines_kept(self) -> None:
        # Blank lines inside an `__asm` block belong to the block; only the ones after `}` collapse.
        c = CollapseBlankLines()
        code = "__asm\n{\n  mov eax, ebx\n\n\n   \n  nop\n}\n\n\ny = 2;"
        assert c.apply(code) == "__asm\n{\n  mov eax, ebx\n\n\n   \n  nop\n}\n\ny = 2;"

    def test_asm_block_opened_mid_line(self) -> None:
        # Line 1 starts as code but ends inside the block, so the blank lines after it are block content.
        c = CollapseBlankLines()
        code = "    x = 1; __asm {   \n\n\n      nop   \n    }   \n\n\n    y = 2;   "
        assert c.apply(code) == "    x = 1; __asm {   \n\n\n      nop   \n    }   \n\n    y = 2;   "

    def test_string_opened_mid_line(self) -> None:
        # Line 1 starts as code but ends inside the string; line 2 starts inside it, so it is kept as string content.
        c = CollapseBlankLines()
        code = '    p = "abc   \\\n    def   ";   \n\n\n    y = 2;   '
        assert c.apply(code) == '    p = "abc   \\\n    def   ";   \n\n    y = 2;   '
