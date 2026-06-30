"""Tests for the `trim-spurious-args` transform (TrimSpuriousArgs)."""

from __future__ import annotations

import pytest

from deflated.transforms import TrimSpuriousArgs


class TestTrimSpuriousArgs:
    @pytest.mark.parametrize(
        "src,expected",
        [
            # setlocale takes 2; the register-spill tail is cut.
            ("setlocale(6,(s+20),mc,mb,md,me);", "setlocale(6,(s+20));"),
            ("setlocale(5,0,entry_rdx,entry_rcx,entry_r8,entry_r9);", "setlocale(5,0);"),
            # one-arg functions
            ("free(p,junk);", "free(p);"),
            ("strlen(s,a,b);", "strlen(s);"),
            # three-arg functions; FORTIFY-style trailing size arg gone
            ("memcpy(d,s,n,dn);", "memcpy(d,s,n);"),
            # commas inside a nested arg do not split.
            ("memset(d,f(a,b),n,extra);", "memset(d,f(a,b),n);"),
        ],
    )
    def test_trimmed(self, src, expected) -> None:
        assert TrimSpuriousArgs().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # correctly-argged calls are untouched
            "setlocale(6,(s+20));",
            "memcpy(d,s,n);",
            "free(p);",
            # a definition (`)` then `{`) must not be trimmed
            "int memcpy(d,s,n,extra){return 0;}",
            # a declaration / prototype (`)` then `;`) must not be trimmed
            "void *memcpy(void *a, void *b, size_t c, int extra);",
            "extern void free(void *p, int q);",
            "u64 strlen(char *s, int extra);",
            # member call is not the libc function
            "obj->free(a,b,c);",
            # function not in the fixed-arity table (could be variadic)
            "printf(fmt,a,b,c);",
            "fprintf(f,fmt,a,b);",
        ],
    )
    def test_kept(self, src) -> None:
        assert TrimSpuriousArgs().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            # a call in return / else statement position is still trimmed
            ("return free(p,junk);", "return free(p);"),
            ("if(c) free(p,junk); else free(q,j);", "if(c) free(p); else free(q);"),
        ],
    )
    def test_call_in_statement_position_trimmed(self, src, expected) -> None:
        assert TrimSpuriousArgs().apply(src) == expected

    def test_inside_string_not_touched(self) -> None:
        src = 's = "setlocale(6,a,b,c,d)";'
        assert TrimSpuriousArgs().apply(src) == src

    def test_multiple_calls(self) -> None:
        out = TrimSpuriousArgs().apply("free(p,j);strlen(s,k);")
        assert out == "free(p);strlen(s);"
