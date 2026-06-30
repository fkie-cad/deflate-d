"""Tests for the `ws-comments` transform (TightenCommentSpaces)."""

from __future__ import annotations

from deflated.transforms import TightenCommentSpaces


class TestTightenCommentSpaces:
    # --- Line comments ---

    def test_leading_space_stripped(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("// some comment") == "//some comment"

    def test_leading_tab_stripped(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("//\tsome comment") == "//some comment"

    def test_internal_spaces_collapsed(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("// some   comment") == "//some comment"

    def test_internal_tab_collapsed(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("// some \tcomment") == "//some comment"

    def test_trailing_space_stripped(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("// comment   ") == "//comment"

    def test_inline_line_comment(self) -> None:
        # Code segment is untouched; only the comment interior changes.
        t = TightenCommentSpaces()
        assert t.apply("a = b; // some \tcomment") == "a = b; //some comment"

    # --- Block comments ---

    def test_block_comment_leading_trailing_stripped(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("/*  some comment  */") == "/*some comment*/"

    def test_block_comment_internal_spaces_collapsed(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("/* some   comment */") == "/*some comment*/"

    def test_block_comment_internal_tab_collapsed(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("/* some \tcomment */") == "/*some comment*/"

    def test_block_comment_newlines_preserved(self) -> None:
        # Horizontal whitespace is stripped/collapsed per line, but newlines stay.
        t = TightenCommentSpaces()
        assert t.apply("/* \n * first\n * second\n */") == "/*\n * first\n * second\n*/"

    # --- Non-comment segments are untouched ---

    def test_code_untouched(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("int  x  =  1;") == "int  x  =  1;"

    def test_string_literal_untouched(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply('"a    b"') == '"a    b"'

    def test_char_literal_untouched(self) -> None:
        t = TightenCommentSpaces()
        assert t.apply("f('a')") == "f('a')"

    def test_unterminated_block_comment_preserves_bytes(self) -> None:
        # An unterminated `/* ...` (run to EOF) has no `*/` to strip or re-append:
        # the tail bytes must survive and no closer may be fabricated.
        t = TightenCommentSpaces()
        out = t.apply("a; /* never   closed\nb; c;")
        assert "*/" not in out  # no fabricated terminator
        assert "b; c;" in out  # trailing bytes not dropped
        assert "never closed" in out  # interior still collapsed (lossless)
