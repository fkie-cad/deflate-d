"""Tests for the `drop-trailing-return` transform (DropTrailingReturn)."""

from __future__ import annotations

import pytest

from deflated.transforms import DropTrailingReturn


class TestDropTrailingReturn:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("void f(void){g();return;}", "void f(void){g();}"),
            ("void f(void){return;}", "void f(void){}"),
            ("void f(int x){h(x);return;}\nvoid g(void){k();return;}", "void f(int x){h(x);}\nvoid g(void){k();}"),
        ],
    )
    def test_rewritten(self, src, expected) -> None:
        assert DropTrailingReturn().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "void f(void){if(x){return;}h();}",  # return ends an inner block, not the body
            "void f(void){while(c){g();return;}}",  # return inside a loop body
            "int g(void){return 5;}",  # `return <value>;` is not bare
            "void f(void){g();}",  # no trailing return
            "int h(void){return x;}",  # value return at body end
        ],
    )
    def test_kept(self, src) -> None:
        assert DropTrailingReturn().apply(src) == src

    def test_only_function_end_return_dropped(self) -> None:
        # The early `return;` inside the `if` stays; the trailing one goes.
        src = "void f(int x){if(x){g();return;}h();return;}"
        expected = "void f(int x){if(x){g();return;}h();}"
        assert DropTrailingReturn().apply(src) == expected

    def test_labeled_trailing_return_kept(self) -> None:
        # A `return;` that is a label's sole statement must NOT be dropped:
        # `cleanup: }` is a label with no statement (invalid C before C23).
        src = "void f(int x){if(x)goto cleanup;do_work();cleanup:return;}"
        assert DropTrailingReturn().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        [
            "void f(int c){ g(); if (c) return; }",
            'void f(int c){ if (c) puts("a"); else return; }',
            "void f(int c){ for (;c;) return; }",
            "void f(int c){ while (c) return; }",
        ],
    )
    def test_keeps_return_that_is_an_unbraced_body(self, src) -> None:
        # Dropping it would leave `if (c) }` / `else }`, which is invalid C.
        assert DropTrailingReturn().apply(src) == src

    def test_stray_closing_brace_stops_the_scan(self) -> None:
        # After a stray `}` the depth is unknown. Reading on would see the `}` of the `if` as the body end and drop
        # the early return, so `y()` would run when `c` holds.
        src = "}void f(void){if(c){x();return;}y();}"
        assert DropTrailingReturn().apply(src) == src
