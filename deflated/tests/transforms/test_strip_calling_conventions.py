"""Tests for the `strip-callconv` transform (StripCallingConventions)."""

from __future__ import annotations

import pytest

from deflated.transforms import StripCallingConventions


class TestStripCallingConventions:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("void __cdecl f(int a);", "void f(int a);"),
            ("int __thiscall g(void);", "int g(void);"),
            ("x = (__fastcall *)p;", "x = ( *)p;"),
            ("__noreturn void h(void);", " void h(void);"),
            ("int f(std::exception *__hidden this, int n);", "int f(std::exception * this, int n);"),
            ("void __stdcall f(int a);", "void f(int a);"),
            ("__pure int g(void);", " int g(void);"),
            ("void __vectorcall f(void);", "void f(void);"),
            ("void __usercall f(void);", "void f(void);"),
            ("void __userpurge f(void);", "void f(void);"),
        ],
    )
    def test_removed(self, src, expected) -> None:
        assert StripCallingConventions().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "int __cdecl_table;",  # trailing underscore keeps the ident intact
            "y = my__cdecl;",  # keyword embedded mid-ident
            's = "__cdecl";',  # string literal
        ],
    )
    def test_kept(self, src) -> None:
        assert StripCallingConventions().apply(src) == src

    def test_multiple_conventions_in_one_signature(self) -> None:
        # A signature carrying both a calling convention and an attribute keyword.
        out = StripCallingConventions().apply("__noreturn void __cdecl abort(void);")
        assert "__noreturn" not in out and "__cdecl" not in out
        assert "void" in out and "abort" in out
