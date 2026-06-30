"""Tests for the `compress-funcs` transform (CompressFunctionNames)."""

from __future__ import annotations

from deflated.transforms import CompressFunctionNames


class TestCompressFunctionNames:
    def test_single_placeholder_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("int FUN_100(void){return 0;}")
        assert "FUN_100" not in out

    def test_definition_and_call_sites_consistent(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("int FUN_100(int x){return x;}\nint FUN_200(void){return FUN_100(5);}\n")
        assert "FUN_100" not in out and "FUN_200" not in out
        assert "return a(5)" in out and "int a(int x)" in out
        assert "int b(void)" in out

    def test_undefined_callee_renamed_by_default(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("int FUN_100(void){return FUN_999(0);}")
        assert "FUN_999" not in out and "FUN_100" not in out

    def test_declaration_only_placeholder_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("int sub_401041(char *, char);\nint h(){return sub_401041(0, 0);}")
        assert "sub_401041" not in out

    def test_require_definition_keeps_external_callee(self) -> None:
        g = CompressFunctionNames(require_definition=True)
        out = g.apply("int FUN_100(void){return FUN_999(0);}")
        assert "FUN_999" in out and "FUN_100" not in out

    def test_thunk_and_target_distinguished(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("void j_sub_406370(void){sub_406370();}\nvoid u(void){j_sub_406370();j___RTC_CheckEsp();}")
        assert "j_sub_406370" not in out and "sub_406370" not in out
        assert "j___RTC_CheckEsp" in out

    def test_unwind_placeholder_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("void Unwind_00408930(void){return;}")
        assert "Unwind_00408930" not in out

    def test_real_symbols_preserved(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("int process_record(long p){return validate(p);}")
        assert "process_record" in out and "validate" in out

    def test_body_left_intact(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("void FUN_1(int x){if (x) {return;}}")
        assert "if (x)" in out and "FUN_1" not in out

    def test_recursive_self_call_renamed_once(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("int FUN_1(void){int a; return FUN_1();}")
        assert "FUN_1" not in out and out.count("(void)") == 1

    def test_nullsub_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("void nullsub_1(void){} void g(void){nullsub_1();}")
        assert "nullsub_1" not in out

    def test_unknown_libname_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("void h(void){unknown_libname_9();}")
        assert "unknown_libname_9" not in out

    def test_bn_jump_thunk_to_placeholder_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply("void j_FUN_401abc(void){FUN_401abc();}")
        assert "j_FUN_401abc" not in out and "FUN_401abc" not in out

    def test_placeholder_inside_string_literal_not_renamed(self) -> None:
        f = CompressFunctionNames()
        out = f.apply('void FUN_100(void){ s = "FUN_100"; }')
        assert '"FUN_100"' in out

    def test_generated_names_avoid_existing_identifiers(self) -> None:
        # If short names like 'a'..'m' are all taken, compression picks the
        # next available; result must not collide with any existing identifier.
        existing = " ".join(f"int {chr(c)};" for c in range(ord("a"), ord("n")))  # a..m taken
        src = existing + " void FUN_1(void){}"
        f = CompressFunctionNames()
        out = f.apply(src)
        assert "FUN_1" not in out
