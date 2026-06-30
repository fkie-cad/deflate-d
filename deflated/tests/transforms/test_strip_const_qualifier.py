"""Tests for the `strip-const` transform (StripConstQualifier)."""

from __future__ import annotations

import pytest

from deflated.transforms import StripConstQualifier


class TestStripConstQualifier:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("char const *msgid;", "char *msgid;"),
            ("void *const p;", "void * p;"),
            ("const int x;", " int x;"),
            ("u64 strlen(char const *fb);", "u64 strlen(char *fb);"),
            ("const char *const *argv;", " char * *argv;"),
        ],
    )
    def test_stripped(self, src, expected) -> None:
        assert StripConstQualifier().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # `const` only as a substring of a longer identifier is untouched.
            "const_table = 1;",
            "x = my_const;",
            "constant = 2;",
        ],
    )
    def test_kept(self, src) -> None:
        assert StripConstQualifier().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "const char *";'
        assert StripConstQualifier().apply(src) == src

    def test_no_token_merge(self) -> None:
        # Stripping must never glue neighbouring tokens together.
        out = StripConstQualifier().apply("int const x;")
        assert "constx" not in out and "intx" not in out
