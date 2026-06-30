"""Tests for the `comments-warning` transform (RemoveWarningComments)."""

from __future__ import annotations

from deflated.transforms import RemoveWarningComments


class TestRemoveWarningComments:
    def test_warning_banner_dropped(self) -> None:
        r = RemoveWarningComments()
        src = "int f(void){\n/* WARNING: Could not recover jumptable */\nreturn 0;}\n"
        assert "WARNING" not in r.apply(src)

    def test_adjacent_tokens_not_merged(self) -> None:
        # Replacement leaves a separator so neighbours don't fuse.
        r = RemoveWarningComments()
        out = r.apply("int x; /* WARNING: unrecovered */ y;")
        assert "WARNING" not in out
        assert "x;" in out and "y;" in out

    def test_non_warning_block_comment_kept(self) -> None:
        # This pass only targets WARNING banners; ordinary comments are gone by
        # T2, but in isolation it must not touch them.
        r = RemoveWarningComments()
        out = r.apply("int x; /* ordinary */ y;")
        assert "ordinary" in out

    def test_warning_inside_string_literal_not_removed(self) -> None:
        r = RemoveWarningComments()
        out = r.apply('s = "/* WARNING: msg */";')
        assert "WARNING" in out

    def test_multiple_warning_banners_all_removed(self) -> None:
        r = RemoveWarningComments()
        src = "/* WARNING: first */ x = 1; /* WARNING: second */ y = 2;"
        out = r.apply(src)
        assert "WARNING" not in out
        assert "x = 1;" in out and "y = 2;" in out
