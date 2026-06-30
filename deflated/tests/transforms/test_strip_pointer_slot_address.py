"""Tests for the `strip-ptr-addr` transform (StripPointerSlotAddress)."""

from __future__ import annotations

from deflated.transforms import StripPointerSlotAddress


class TestStripPointerSlotAddress:
    def test_strips_address_keeps_symbol(self) -> None:
        out = StripPointerSlotAddress().apply("x=(*PTR_free_0010b000)(); y=PTR_strncmp_0010b018;")
        assert "PTR_free_0010b000" not in out and "PTR_free" in out
        assert "PTR_strncmp_0010b018" not in out and "PTR_strncmp" in out

    def test_underscored_symbol(self) -> None:
        out = StripPointerSlotAddress().apply("if(PTR___gmon_start___0010afc8) f();")
        assert out == "if(PTR___gmon_start__) f();"

    def test_collision_kept(self) -> None:
        # Two slots of the same symbol would both strip to PTR_free; keep both.
        src = "a=PTR_free_0010b000; b=PTR_free_0020c000;"
        assert StripPointerSlotAddress().apply(src) == src

    def test_existing_stripped_name_kept(self) -> None:
        # If the stripped form already occurs verbatim, do not create a collision.
        src = "a=PTR_free_0010b000; b=PTR_free;"
        assert StripPointerSlotAddress().apply(src) == src

    def test_symbolless_pointer_untouched(self) -> None:
        # Bare PTR_<addr> has no symbol to keep; leave it for compress-names.
        src = "x=PTR_0010aff8;"
        assert StripPointerSlotAddress().apply(src) == src

    def test_inside_string_not_touched(self) -> None:
        src = 's = "PTR_free_0010b000";'
        assert StripPointerSlotAddress().apply(src) == src
