"""Tests for the `int-minform` transform (MinimizeIntegerLiterals)."""

from __future__ import annotations

import pytest

from deflated.transforms import MinimizeIntegerLiterals


class TestMinimizeIntegerLiterals:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("a = 0x10;", "a = 16;"),  # 0x10 (4) -> 16 (2)
            ("x = 0xff;", "x = 255;"),  # 0xff (4) -> 255 (3)
            ("p = 0x0;", "p = 0;"),  # 0x0 (3) -> 0 (1)
            ("n = 0xffff;", "n = 65535;"),  # 0xffff (6) -> 65535 (5)
            ("case 0x7b:", "case 123:"),
            ("y = 0x401000;", "y = 4198400;"),  # address, fits in int, shorter
            ("c = 0x28u;", "c = 40u;"),  # suffix left attached
            ("v = 0X1A;", "v = 26;"),  # uppercase prefix
        ],
    )
    def test_rewritten(self, src, expected) -> None:
        assert MinimizeIntegerLiterals().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "m = 0xffffffff;",  # value > INT_MAX: decimal would change the type
            "m = 0x80000000;",  # value > INT_MAX
            "m = 0x7fffffff;",  # decimal 2147483647 is no shorter than the hex
        ],
    )
    def test_kept_large_or_no_win(self, src) -> None:
        assert MinimizeIntegerLiterals().apply(src) == src

    def test_decimal_untouched(self) -> None:
        assert MinimizeIntegerLiterals().apply("a = 16; b = 1000000;") == "a = 16; b = 1000000;"

    def test_float_untouched(self) -> None:
        assert MinimizeIntegerLiterals().apply("d = 1.5; e = 16.0;") == "d = 1.5; e = 16.0;"

    def test_identifier_with_hex_substring_untouched(self) -> None:
        # `DAT_0040d430` / `local_0x10` are identifiers, not number tokens.
        src = "x = DAT_0040d430; y = stack0xfffffffc;"
        assert MinimizeIntegerLiterals().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "0x10"; c = 0x10;'
        assert MinimizeIntegerLiterals().apply(src) == 's = "0x10"; c = 16;'

    def test_inside_comment_not_touched(self) -> None:
        src = "x = 0x10; /* keep 0xff here */"
        assert MinimizeIntegerLiterals().apply(src) == "x = 16; /* keep 0xff here */"

    def test_negative_literal(self) -> None:
        assert MinimizeIntegerLiterals().apply("a = -0x10;") == "a = -16;"

    @pytest.mark.parametrize(
        "src",
        [
            # C99 hex-float literals: the hex head must NOT be re-spelled in decimal
            # (it would change the value), even though it tokenizes separately.
            "x = 0x1f.0p3;",
            "y = 0x1fp3;",
            "z = 0x10.8p1;",
            "w = 0X1Fp2;",
        ],
    )
    def test_hex_float_literal_kept(self, src) -> None:
        assert MinimizeIntegerLiterals().apply(src) == src
