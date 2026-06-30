"""Tests for the `drop-resolver-stubs` transform (EraseResolverStubs)."""

from __future__ import annotations

from deflated.transforms import EraseResolverStubs


class TestEraseResolverStubs:
    def test_family_deleted_resolver_kept(self) -> None:
        # The post-T3 Binary Ninja shape: a shared resolver `a` plus per-slot
        # stubs that load a constant and tail-call it.
        src = (
            "i64 a(){i64 er=es;}"
            "i64 b(){i64 er=0;return a();}"
            "i64 e(){i64 er=1;return a();}"
            "i64 f(){i64 er=2;return a();}"
        )
        out = EraseResolverStubs().apply(src)
        assert "i64 a(){i64 er=es;}" in out  # resolver kept
        for stub in ("i64 b()", "i64 e()", "i64 f()"):
            assert stub not in out

    def test_no_decl_stub_also_deleted(self) -> None:
        # A stub need not carry a dead local; `return a();` alone qualifies.
        src = "i64 b(){return a();}i64 e(){return a();}i64 f(){return a();}"
        assert EraseResolverStubs().apply(src) == ""

    def test_below_family_threshold_kept(self) -> None:
        # Two stubs is not a resolver family (threshold is 3); leave them.
        src = "i64 b(){i64 er=0;return a();}i64 e(){i64 er=1;return a();}i64 a(){i64 er=es;}"
        assert EraseResolverStubs().apply(src) == src

    def test_referenced_stub_kept(self) -> None:
        # A stub whose name is referenced elsewhere is not deleted (its name
        # occurs more than once), even if its shape matches the family.
        src = (
            "i64 b(){i64 er=0;return a();}"
            "i64 e(){i64 er=1;return a();}"
            "i64 f(){i64 er=2;return a();}"
            "int main(){return b();}"
        )
        out = EraseResolverStubs().apply(src)
        assert "i64 b()" in out  # referenced -> kept
        assert "i64 e()" not in out and "i64 f()" not in out

    def test_control_flow_or_extra_call_kept(self) -> None:
        src = "int g(){int x=0;if(x)return a();return a();}int h(){foo();return a();}int i(){return a();}"
        assert EraseResolverStubs().apply(src) == src

    def test_stub_with_args_kept(self) -> None:
        # A tail-call passing arguments is a real delegator, not a resolver stub.
        src = "int b(){return a(1);}int e(){return a(2);}int f(){return a(3);}"
        assert EraseResolverStubs().apply(src) == src

    def test_real_functions_untouched(self) -> None:
        src = "int add(int a,int b){return a+b;}int sq(int x){return x*x;}"
        assert EraseResolverStubs().apply(src) == src

    def test_shape_inside_string_not_touched(self) -> None:
        src = 'const char *s = "i64 b(){i64 er=0;return a();}";'
        assert EraseResolverStubs().apply(src) == src
