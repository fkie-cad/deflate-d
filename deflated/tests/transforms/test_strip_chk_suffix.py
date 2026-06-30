"""Tests for the `strip-chk` transform (StripChkSuffix)."""

from __future__ import annotations

import pytest

from deflated import Tier, transform
from deflated.transforms import StripChkSuffix


class TestStripChkSuffix:
    @pytest.mark.parametrize(
        "src,expected",
        [
            # Only EMPTY-argument occurrences are renamed (safe: no args to shift).
            ("__printf_chk();", "printf();"),
            ("x = __snprintf_chk();", "x = snprintf();"),
            ("__fprintf_chk();", "fprintf();"),
            ("__memcpy_chk();", "memcpy();"),
            # single-underscore internal spelling collapses to the same name
            ("return _printf_chk();", "return printf();"),
        ],
    )
    def test_stripped(self, src, expected) -> None:
        assert StripChkSuffix().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # `_chk` is not at a word boundary: a genuine multi-segment symbol.
            "__stack_chk_fail();",
            "x = __stack_chk_guard;",
            # No `_chk` suffix at all.
            "printf(fmt);",
            "y = check_value(x);",
            # Not a glibc FORTIFY wrapper: an application symbol that merely ends
            # in `_chk` must NOT be renamed (would otherwise alias an unrelated
            # name). Only the curated FORTIFY base set is stripped.
            "_my_chk();",
            "__frobnicate_chk(x);",
            "x = widget_chk(a, b);",
            # Argument-bearing FORTIFY calls must NOT be renamed: the wrappers have
            # extra leading flag/slen args, so a plain rename would shift the flag
            # into a real operand position (corruption). These are left untouched.
            "__printf_chk(1, fmt);",
            "__fprintf_chk(f, 1, fmt);",
            "__snprintf_chk(b, n, 1, m, fmt);",
            "__memcpy_chk(d, s, n, dn);",
        ],
    )
    def test_kept(self, src) -> None:
        assert StripChkSuffix().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "__printf_chk";'
        assert StripChkSuffix().apply(src) == src

    def test_empty_arg_forwarder_collapses_via_thunk_elision(self) -> None:
        # The `__X_chk(){return _X_chk();}` forwarder becomes a self-call once both
        # halves lose the suffix, which thunk-elision (running after) collapses to
        # the bare prototype -- closing the empty-arg forwarder gap.
        src = "i64 __snprintf_chk(){return _snprintf_chk();}"
        assert transform(src, Tier.T4_REDUCTIVE) == "i64 snprintf();"
