"""Tests for the `thunk-elision` transform (ElideThunkBodies)."""

from __future__ import annotations

import pytest

from deflated.transforms import ElideThunkBodies


class TestElideThunkBodies:
    @pytest.mark.parametrize(
        "src,expected",
        [
            # Hex-Rays / Binary Ninja self-call thunk (returning).
            (
                "int strncmp(const char *s1, const char *s2, size_t n){return strncmp(s1, s2, n);}",
                "int strncmp(const char *s1, const char *s2, size_t n);",
            ),
            # Self-call thunk (void), and a void-self-call followed by bare return.
            ("void abort(void){abort();}", "void abort(void);"),
            ("void _exit(int s){_exit(s);return;}", "void _exit(int s);"),
            # Ghidra void indirect import thunk through PTR_<sym> (with (code *) cast).
            ("void free(void *__ptr){(*(code *)PTR_free_0010b000)();return;}", "void free(void *__ptr);"),
            # Ghidra returning thunk via temp (the inline-temps-off shape).
            (
                "int strncmp(char *__s1,char *__s2,size_t __n){int dd;dd=(*PTR_strncmp_0010b018)();return dd;}",
                "int strncmp(char *__s1,char *__s2,size_t __n);",
            ),
            # Ghidra direct return with a result cast.
            (
                "int *__errno_location(void){return (int *)(*PTR___errno_location_0010b010)();}",
                "int *__errno_location(void);",
            ),
            # No-symbol indirect thunk: PTR_<addr> with no symbol still collapses.
            ("void a(void){(*PTR_0010aff8)();return;}", "void a(void);"),
            # Ghidra bad-instruction stub: the sole `halt_baddata();` body collapses.
            ("void free(void *__ptr){halt_baddata();}", "void free(void *__ptr);"),
            ("int *__errno_location(void){halt_baddata();}", "int *__errno_location(void);"),
        ],
    )
    def test_collapsed(self, src, expected) -> None:
        assert ElideThunkBodies().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            # Conditional init (Ghidra _DT_INIT): control flow => never a thunk.
            "void _DT_INIT(void){if(PTR_x!=(undefined*)0x0)(*PTR_x)();return;}",
            # A delegator to a *different* function is real code, not a thunk.
            "int wrap(int x){return helper(x);}",
            # Recursion mixed with logic must not be mistaken for a self-thunk.
            "int fact(int n){return n<=1?1:fact(n-1);}",
            # Two real statements.
            "int f(void){g();return h();}",
            # An ordinary small function body.
            "int add(int a,int b){int c;c=a+b;return c;}",
            # Indirect call through a non-PTR function pointer is not an import thunk.
            "int viaptr(int x){return (*fp)(x);}",
            # Empty body (e.g. nullsub) is not a forwarding thunk.
            "void nullsub(void){}",
        ],
    )
    def test_kept(self, src) -> None:
        assert ElideThunkBodies().apply(src) == src

    def test_multiple_thunks_and_a_real_function(self) -> None:
        src = (
            "void free(void *p){(*PTR_free_1)();return;}"
            "int real(int x){int y;y=x*x;return y;}"
            "void abort(void){abort();}"
        )
        out = ElideThunkBodies().apply(src)
        assert "void free(void *p);" in out
        assert "void abort(void);" in out
        # The genuine function keeps its body.
        assert "int real(int x){int y;y=x*x;return y;}" in out

    def test_thunk_text_inside_string_not_touched(self) -> None:
        src = 'const char *s = "void free(void *p){(*PTR_free_1)();}";'
        assert ElideThunkBodies().apply(src) == src

    def test_pure_passthrough_family_collapses(self) -> None:
        # A family (>= 2) of *pure passthrough* trampolines -- the forwarded
        # arguments are exactly the parameters, verbatim and in order -- carries
        # nothing beyond "calls worker", so the family collapses to prototypes.
        src = (
            "i64 ht(i32 *a, i64 c){return gv(a, c);}"
            "i64 hu(i32 *a, i64 c){return gv(a, c);}"
        )
        out = ElideThunkBodies().apply(src)
        assert "i64 ht(i32 *a, i64 c);" in out
        assert "i64 hu(i32 *a, i64 c);" in out

    def test_family_forwarders_with_constants_kept(self) -> None:
        # Regression: forwarders to the same worker but with a *baked-in constant*
        # are NOT pure passthroughs -- the constant distinguishes them (e.g. two
        # argument parsers differing only in the numeric base), so the bodies are
        # real code and must survive even though >= 2 share the worker.
        src = (
            "i64 ht(i32 *a, i64 c){return gv(a, c, 0);}"
            "i64 hu(i32 *a, i64 c){return gv(a, c, 2);}"
        )
        assert ElideThunkBodies().apply(src) == src

    def test_reordered_comparator_family_kept(self) -> None:
        # Regression (corpus: hexrays dir.c/ls.c/vdir.c): forward vs reverse
        # comparators forward the SAME worker but reorder/deref the parameters, so
        # the argument order is the semantics. They must not collapse to identical
        # prototypes (which would erase the sort direction).
        src = (
            "int fwd(char **a1, char **a2){return strcmp(*a1, *a2);}"
            "int rev(char **a1, char **a2){return strcmp(*a2, *a1);}"
        )
        assert ElideThunkBodies().apply(src) == src

    def test_lone_forwarder_kept(self) -> None:
        # A single delegator to a worker (family of one) is genuine code.
        src = "i64 only(i32 *a, void *b){return worker(a, b);}"
        assert ElideThunkBodies().apply(src) == src

    def test_empty_arg_forwarder_left_for_resolver_pass(self) -> None:
        # `return g();` (empty args) is a resolver-stub shape, not a family
        # forwarder, so thunk-elision leaves it for `drop-resolver-stubs`.
        src = "i64 b(){return a();}i64 c(){return a();}"
        assert ElideThunkBodies().apply(src) == src
