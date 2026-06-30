"""Tests for the `simplify-types` transform (SimplifyLowConfidenceTypes)."""

from __future__ import annotations

import pytest

from deflated.transforms import SimplifyLowConfidenceTypes


class TestSimplifyLowConfidenceTypes:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("__int64 a; __int32 b;", "i64 a; i32 b;"),
            ("__int16 a; __int8 b;", "i16 a; i8 b;"),
            ("unsigned __int64 a;", "u64 a;"),
            ("unsigned __int32 a;", "u32 a;"),
            ("unsigned __int16 a;", "u16 a;"),
            ("unsigned __int8 a;", "u8 a;"),
            ("_QWORD x;", "u64 x;"),
            ("int32_t a; uint32_t b; uint8_t c; int64_t d;", "i32 a; u32 b; u8 c; i64 d;"),
            ("uint16_t a; int8_t b;", "u16 a; i8 b;"),
            ("undefined1 a;", "u8 a;"),
            # `signed __intN`: the `signed` must be consumed, not orphaned to the
            # invalid `signed i64`. `signed` is the default, so dropping it is safe.
            ("signed __int64 a; signed __int8 b;", "i64 a; i8 b;"),
            ("signed __int32 a; signed __int16 b;", "i32 a; i16 b;"),
            # 128-bit family: `unsigned`/`signed` prefix consumed before the tail.
            ("__int128 a;", "i128 a;"),
            ("unsigned __int128 a;", "u128 a;"),
            ("signed __int128 a;", "i128 a;"),
            # Binary Ninja 128-bit stdint spelling (three tokens -> two).
            ("int128_t a; uint128_t b;", "i128 a; u128 b;"),
            # glibc internal aliases -> public POSIX typedefs (same type, lossless).
            (
                "__off_t o; __mode_t m; __pid_t p; __ssize_t s; __time_t t;",
                "off_t o; mode_t m; pid_t p; ssize_t s; time_t t;",
            ),
            ("__uid_t u; __gid_t g; __ino_t i; __dev_t d;", "uid_t u; gid_t g; ino_t i; dev_t d;"),
            # glibc double-underscore stdint aliases.
            ("__int32_t a; __uint64_t b;", "i32 a; u64 b;"),
            ("__int8_t a; __uint16_t b; __int64_t c;", "i8 a; u16 b; i64 c;"),
        ],
    )
    def test_shortened(self, src, expected) -> None:
        assert SimplifyLowConfidenceTypes().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "undefined8 a; undefined4 b; uint c; _DWORD d;",  # Ghidra compact types kept
            "_OWORD w;",  # rejected mapping (regresses on Gemini): must be kept
            "size_t n; int k;",  # real types kept
            "__int64_helper(x);",  # must not match inside a longer ident
            "my_int32_t_field = 0;",  # width substring not matched
            # Regression: a struct member spelled like a width type is a *member
            # name*, not a type, so it must not be rewritten (which would corrupt
            # the reference). The leading member-op guard declines `.`/`->` positions.
            "a = x.int32_t;",
            "b = p->uint64_t;",
            "c = s.__int64;",
        ],
    )
    def test_kept(self, src) -> None:
        assert SimplifyLowConfidenceTypes().apply(src) == src

    def test_member_op_guard_does_not_block_real_types(self) -> None:
        # The member-op guard fires only after `.`/`->`; genuine type positions
        # (declaration, cast, C++ template argument) still shorten.
        t = SimplifyLowConfidenceTypes()
        assert t.apply("int32_t v = 5;") == "i32 v = 5;"
        assert t.apply("x = (int32_t)y;") == "x = (i32)y;"
        assert t.apply("vector<int32_t> z;") == "vector<i32> z;"

    def test_type_inside_string_not_touched(self) -> None:
        src = 's = "__int64 and uint64_t";'
        assert SimplifyLowConfidenceTypes().apply(src) == src


class TestSimplifyTypesMemberGuard:
    def test_spaced_member_spelled_like_type_not_rewritten(self) -> None:
        # Regression (F3): a struct member spelled like a width type must not be
        # rewritten into a corrupted field reference, even when whitespace (or a
        # newline) separates the member operator from the name.
        from deflated.transforms import SimplifyLowConfidenceTypes

        t = SimplifyLowConfidenceTypes()
        assert t.apply("x = s . int32_t;") == "x = s . int32_t;"
        assert t.apply("x = s->\nint32_t;") == "x = s->\nint32_t;"
        # A genuine type (not after a member operator) still simplifies.
        assert t.apply("int32_t v;") == "i32 v;"
