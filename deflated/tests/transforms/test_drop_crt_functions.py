"""Tests for the `drop-crt` transform (DropCrtFunctions)."""

from __future__ import annotations

from deflated.transforms import DropCrtFunctions


class TestDropCrtFunctions:
    def test_drops_named_crt_functions(self) -> None:
        src = (
            "void _DT_INIT(void){(*PTR_x)();return;}"
            "int register_tm_clones(void){return 0;}"
            "void frame_dummy(void){}"
            "int main(){return 0;}"
        )
        out = DropCrtFunctions().apply(src)
        assert out == "int main(){return 0;}"

    def test_keeps_application_functions(self) -> None:
        # `start` (no underscore) and a normal function are application code.
        src = "int start(int x){return x;}int helper(void){return 1;}"
        assert DropCrtFunctions().apply(src) == src

    def test_drops_underscored_start(self) -> None:
        src = "void _start(void){__libc_start_main();}int main(){return 0;}"
        assert DropCrtFunctions().apply(src) == "int main(){return 0;}"

    def test_libc_start_main_not_dropped(self) -> None:
        # Excluded from the set (often a real import thunk).
        src = "int __libc_start_main(void){return 0;}"
        assert DropCrtFunctions().apply(src) == src

    def test_crt_name_inside_string_not_touched(self) -> None:
        src = 'const char *s = "_DT_INIT";int main(){return 0;}'
        assert DropCrtFunctions().apply(src) == src

    def test_drops_ghidra_entry_trampoline(self) -> None:
        # Ghidra renames `_start` to `entry`; gated on the __libc_start_main call.
        src = (
            "void processEntry entry(undefined8 g,undefined8 h){"
            "undefined8 np[8];(*PTR___libc_start_main)(c,h,&nq,0,0,g,np);do{}while(true);}"
            "int main(int argc,char **argv){return 0;}"
        )
        assert DropCrtFunctions().apply(src) == "int main(int argc,char **argv){return 0;}"

    def test_keeps_application_entry(self) -> None:
        # An `entry` function that does not hand off to __libc_start_main is kept.
        src = "int entry(int x){return x+1;}"
        assert DropCrtFunctions().apply(src) == src

    def test_kept_when_referenced_by_surviving_function(self) -> None:
        # Binary Ninja sometimes recovers a spurious `return _start(...)` in a
        # regular function. Deleting the `_start` definition would orphan that
        # call, so the reference guard keeps `_start` here (no dangling reference).
        src = "void _start(void){halt();}int run(int x){return _start(x);}"
        out = DropCrtFunctions().apply(src)
        assert "_start(void)" in out  # definition kept because it is still called

    def test_deletes_self_referential_crt_family(self) -> None:
        # A CRT family that only references itself is deleted as a set: no
        # surviving function refers to it, so the guard does not block it.
        src = "void _init(void){frame_dummy();}void frame_dummy(void){return;}int main(){return 0;}"
        out = DropCrtFunctions().apply(src)
        assert "_init" not in out and "frame_dummy" not in out and "int main()" in out

    def test_drops_init_proc_funcptr_declarator(self) -> None:
        # The __gmon_start__ hook uses a function-returning-function-pointer
        # declarator; the parser must see through it so the name match fires.
        src = (
            "i64(**init_proc())(void){i64(**r)(void);r=&_gmon_start__;"
            "if(&_gmon_start__)return(i64(**)(void))_gmon_start__();return r;}"
            "int main(){return 0;}"
        )
        assert DropCrtFunctions().apply(src) == "int main(){return 0;}"
