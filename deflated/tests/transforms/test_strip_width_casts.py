"""Tests for the `strip-width-cast` transform (StripWidthCasts)."""

from __future__ import annotations

import pytest

from deflated.transforms import StripWidthCasts


class TestStripWidthCasts:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("if (hd && (_BYTE)gv) goto il;", "if (hd && gv) goto il;"),
            ("if (!(_DWORD)da) return;", "if (!da) return;"),
            ("v(s, (_DWORD)n);", "v(s, n);"),
            ("x = (_WORD)y;", "x = y;"),
            ("z = (_QWORD)w;", "z = w;"),
            ("a = (_OWORD)b;", "a = b;"),
            # nested operand starts (paren, deref, address-of, number)
            ("x = (_DWORD)(a + b);", "x = (a + b);"),
            ("x = (_BYTE)*p;", "x = *p;"),
            ("x = (_QWORD)&v;", "x = &v;"),
            ("x = (_BYTE)0x41;", "x = 0x41;"),
            # cast in return / argument position
            ("return (_DWORD)r;", "return r;"),
            ("f((_BYTE)c, (_DWORD)d);", "f(c, d);"),
        ],
    )
    def test_stripped(self, src, expected) -> None:
        assert StripWidthCasts().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # Pointer cast: the access width is load-bearing -- keep the `*`.
            "p = (_BYTE *)q;",
            "x = *(_DWORD *)(p + 4);",
            # sizeof is not a cast.
            "n = sizeof(_QWORD);",
            "n = sizeof(_BYTE);",
            # A call whose name happens to precede the parens (value before `(`).
            "f(_QWORD);",
            # Not a pseudo-width type.
            "x = (int)y;",
            "x = (char)y;",
            # `_BYTE` as a declared type (not a cast) is untouched.
            "_BYTE buf[16];",
            # A width cast on an integer literal wider than the cast narrows it:
            # stripping would drop the truncation and change the value. These do
            # not occur in decompiler output (the operand is always a recovered
            # variable/expression), but the guard is defensive against the
            # value-unsafe case.
            "x = (_DWORD)0x123456789;",  # 33-bit value into a 32-bit cast
            "x = (_BYTE)0x1ff;",  # 9-bit value into an 8-bit cast
            "x = (_WORD)0x12345;",  # 17-bit value into a 16-bit cast
            # A float operand of an integer width cast truncates, so stripping
            # changes the value. A hex-float head (`0x1.8p3`) tokenizes as `0x1`
            # then `.8p3`; the guard declines via the `.`/`p` continuation check.
            "x = (_DWORD)1.5;",
            "x = (_DWORD)0x1.8p3;",
            # Regression: a unary sign/complement or parens around a *literal* must
            # be looked through -- `(_BYTE)-1` is 255 (not -1), `(_BYTE)~0` is 255,
            # `(_BYTE)(0x1ff)` is 255. Stripping any of these changes the value, so
            # the cast is kept. (Hex-Rays does emit width casts on `-1`/`~0` for
            # byte fills and char/EOF comparisons.)
            "x = (_BYTE)-1;",
            "x = (_DWORD)-1;",
            "x = (_BYTE)~0;",
            "x = (_BYTE)(0x1ff);",
            "x = (_WORD)-0x12345;",
        ],
    )
    def test_kept(self, src) -> None:
        assert StripWidthCasts().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            # A unary sign/complement on a *variable/expression* is value-neutral
            # (the discarded width is just a hint), so the cast still strips.
            ("x = (_BYTE)-v1;", "x = -v1;"),
            ("x = (_BYTE)~v1;", "x = ~v1;"),
            # A parenthesised multi-token expression is value-neutral, so it strips.
            ("x = (_BYTE)(v1 + v2);", "x = (v1 + v2);"),
            # Unary `+` keeps the value; a fitting literal under it still strips.
            ("x = (_BYTE)+5;", "x = +5;"),
            # A parenthesised literal that *fits* the cast width strips.
            ("x = (_BYTE)(0xff);", "x = (0xff);"),
        ],
    )
    def test_unary_and_paren_operands(self, src, expected) -> None:
        assert StripWidthCasts().apply(src) == expected

    @pytest.mark.parametrize(
        "src,expected",
        [
            # A literal that *fits* the cast width is value-preserving to strip.
            ("x = (_DWORD)0xffffffff;", "x = 0xffffffff;"),  # 32-bit value into 32-bit
            ("x = (_WORD)0xffff;", "x = 0xffff;"),  # 16-bit value into 16-bit
            ("x = (_BYTE)0xff;", "x = 0xff;"),  # 8-bit value into 8-bit
            # A decimal literal (the form left by int-minform) that fits is stripped.
            ("x = (_DWORD)255;", "x = 255;"),
        ],
    )
    def test_fitting_literal_stripped(self, src, expected) -> None:
        assert StripWidthCasts().apply(src) == expected

    def test_inside_string_not_touched(self) -> None:
        src = 's = "(_BYTE)x";'
        assert StripWidthCasts().apply(src) == src

    def test_stacked_casts_idempotent(self) -> None:
        # Regression: stacked width casts ((_DWORD)(_BYTE)x) must fully strip in
        # one apply() (the pass iterates to a fixed point), not peel one per pass.
        t = StripWidthCasts()
        for src in ("x=(_DWORD)(_BYTE)y;", "f((_DWORD)(_WORD)a);", "x=(_BYTE)(_BYTE)z;"):
            once = t.apply(src)
            assert t.apply(once) == once, f"{src} not idempotent: {once!r}"
        assert t.apply("x=(_DWORD)(_BYTE)y;") == "x=y;"

    def test_extended_type_set_opt_in(self) -> None:
        # The conventional casts are out of the default set but configurable.
        t = StripWidthCasts(types=frozenset({"int", "char"}))
        assert t.apply("x = (int)y + (char)z;") == "x = y + z;"
