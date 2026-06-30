"""Tests for the `addr-of-index` transform (AddressOfIndexToOffset)."""

from __future__ import annotations

import pytest

from deflated.transforms import AddressOfIndexToOffset


class TestAddressOfIndexToOffset:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("p = &buf[0x10];", "p = (buf+0x10);"),
            ("f(&data_x[0x1b]);", "f((data_x+0x1b));"),
            ("return &arr[0];", "return (arr+0);"),
            ("x = &a[0x1b] == y;", "x = (a+0x1b) == y;"),
            ("p = &buf[10];", "p = (buf+10);"),  # decimal index
        ],
    )
    def test_rewritten(self, src, expected) -> None:
        assert AddressOfIndexToOffset().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "x = a & buf[0x10];",  # binary bitwise-and, not address-of
            "x = foo() & buf[0x10];",  # `&` after a value (`)`)
            "y = &m[i];",  # variable index (precedence safety)
            "z = &m[i + 1];",  # non-literal index
            "w = arr[0x10];",  # no `&`
            # A postfix operator after the `]` binds tighter than the unary `&`:
            # `&buf[0x10].field` is `&(buf[0x10].field)`, so rewriting the
            # `&buf[0x10]` part alone would drop the `&` and re-associate.
            "p = &buf[0x10].field;",  # member on element
            "p = &buf[0x10]->field;",  # arrow on element
            "p = &buf[0x10][2];",  # nested subscript
            "p = &buf[0x10](a);",  # call on element
            "p = &buf[0x10]++;",  # postfix increment
        ],
    )
    def test_kept(self, src) -> None:
        assert AddressOfIndexToOffset().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            # A *non*-postfix token after `]` is safe: the parenthesised result
            # keeps the original precedence as an operand.
            ("x = &buf[0x10] + 3;", "x = (buf+0x10) + 3;"),
            ("x = &buf[0x10] == y;", "x = (buf+0x10) == y;"),
        ],
    )
    def test_rewritten_when_followed_by_binary_op(self, src, expected) -> None:
        assert AddressOfIndexToOffset().apply(src) == expected

    def test_inside_string_not_touched(self) -> None:
        src = 's = "&buf[0x10]";'
        assert AddressOfIndexToOffset().apply(src) == src
