"""Tests for the `comments` transform (RemoveComments)."""

from __future__ import annotations

from deflated.transforms import RemoveComments


class TestRemoveComments:
    def test_line_and_block_comments_removed(self) -> None:
        r = RemoveComments()
        out = r.apply("int x = 1;  // set x\n/* block */\nint y = 2;\n")
        assert "set x" not in out
        assert "block" not in out

    def test_address_annotation_removed(self) -> None:
        r = RemoveComments()
        out = r.apply("int x = 1;\n/* 0x4011a0 */\nint y = 2;\n")
        assert "0x4011a0" not in out

    def test_warning_banner_kept(self) -> None:
        # WARNING banners survive until T4; `comments` must preserve them.
        r = RemoveComments()
        src = "int f(void){\n/* WARNING: Could not recover jumptable */\nreturn 0;}\n"
        assert "WARNING" in r.apply(src)

    def test_comment_marker_inside_string_preserved(self) -> None:
        r = RemoveComments()
        assert r.apply('s = "a // b";') == 's = "a // b";'

    def test_multiline_block_comment_removed(self) -> None:
        r = RemoveComments()
        out = r.apply("int x;\n/* line one\n   line two */\nint y;\n")
        assert "line one" not in out and "line two" not in out
        assert "int x;" in out and "int y;" in out

    def test_inline_block_comment_removed(self) -> None:
        r = RemoveComments()
        out = r.apply("int x = /* initial value */ 1;\n")
        assert "initial value" not in out
        assert "int x" in out and "1" in out
