"""Tests for the `compress-names` transform (CompressPlaceholderNames)."""

from __future__ import annotations

from deflated.transforms import CompressPlaceholderNames


class TestCompressPlaceholderNames:
    def test_ghidra_global_and_bn_versioned_locals(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("w = DAT_0040d430 + _DAT_0040d428; v = var_8_1; u = PTR_DAT_0040b5a0;")
        for ph in ("DAT_0040d430", "_DAT_0040d428", "var_8_1", "PTR_DAT_0040b5a0"):
            assert ph not in out, f"placeholder {ph} should be renamed"

    def test_binary_ninja_global_data(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("return __CxxFrameHandler3(&data_40c898, nl); switch (jump_table_401abc[i]);")
        for ph in ("data_40c898", "jump_table_401abc"):
            assert ph not in out, f"BN placeholder {ph} should be renamed"

    def test_real_symbol_starting_with_data_kept(self) -> None:
        c = CompressPlaceholderNames()
        assert c.apply("x = data_buffer;") == "x = data_buffer;"

    def test_ida_width_named_data(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("a = dword_40C324[i] + unk_40C120; b = off_4011A0; c = byte_402000;")
        for ph in ("dword_40C324", "unk_40C120", "off_4011A0", "byte_402000"):
            assert ph not in out, f"IDA placeholder {ph} should be renamed"

    def test_non_hex_tail_kept(self) -> None:
        c = CompressPlaceholderNames()
        assert c.apply("n = word_count;") == "n = word_count;"

    def test_ghidra_type_prefixed_var_and_stack(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("x = BVar2 + pHVar1 + pp_Var3 + DVar17; y = EStack_8 + ap_Stack_18 + _Stack_4;")
        for ph in ("BVar2", "pHVar1", "pp_Var3", "DVar17", "EStack_8", "ap_Stack_18", "_Stack_4"):
            assert ph not in out, f"Ghidra placeholder {ph} should be renamed"

    def test_msvc_rtc_symbol_preserved(self) -> None:
        c = CompressPlaceholderNames()
        assert "_RTC_CheckStackVars" in c.apply("z = _RTC_CheckStackVars(p);")

    def test_binary_ninja_lifted_temps(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("temp0 = a; temp1 = temp0 + b;")
        assert "temp0" not in out and "temp1" not in out

    def test_ghidra_unrecovered_stack_slots(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("p = &stack0xfffffffc; q = &stack0x00000004;")
        assert "stack0xfffffffc" not in out and "stack0x00000004" not in out

    def test_register_derived_temporaries(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("eax = ecx + edx; fsbase = eax; r9_1 = rdi;")
        assert all(r not in out for r in ("eax", "ecx", "edx", "fsbase", "r9_1", "rdi"))

    def test_string_or_symbol_bearing_names_preserved(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("p = PTR_s_Hello_0040aee4; q = PTR_guard_check_0040f000;")
        assert "PTR_s_Hello_0040aee4" in out
        assert "PTR_guard_check_0040f000" in out

    def test_register_name_inside_larger_ident_kept(self) -> None:
        c = CompressPlaceholderNames()
        assert c.apply("x = context->eax_saved;") == "x = context->eax_saved;"

    def test_struct_member_named_like_placeholder_kept(self) -> None:
        # `regs->eax`, `frame->local_18`, `ctx.rdi` are real field symbols, not
        # decompiler placeholders, even though they spell like one. Member access
        # (`.`/`->`) must be left untouched.
        c = CompressPlaceholderNames()
        assert c.apply("regs->eax = regs->ebx + 1;") == "regs->eax = regs->ebx + 1;"
        assert c.apply("frame->local_18 = 0;") == "frame->local_18 = 0;"
        assert c.apply("ctx.rdi = arg;") == "ctx.rdi = arg;"

    def test_local_and_same_named_member_do_not_collapse(self) -> None:
        # A local `eax` and an unrelated member `p->eax` are distinct entities and
        # must not both become the same name: the local renames, the member stays.
        c = CompressPlaceholderNames()
        out = c.apply("eax = p->eax;")
        assert "p->eax" in out  # member preserved
        assert out.split("=", 1)[0].strip() != "eax"  # local was renamed
        assert out.count("eax") == 1  # only the member's `eax` remains

    def test_ghidra_prefixless_var(self) -> None:
        # Ghidra also emits prefix-less Var1/Var15 (typed unkbyteN/unkuintN); they
        # are placeholders too and must be renamed, consistently.
        c = CompressPlaceholderNames()
        out = c.apply("x = Var15 + Var1; y = Var15;")
        assert "Var15" not in out and "Var1" not in out
        assert out.count("+") == 1

    def test_registers_inside_asm_block_preserved(self) -> None:
        # Hex-Rays inline `__asm { ... }` holds hardware registers and asm stack
        # aliases, not pseudocode placeholders: they must never be renamed (doing
        # so corrupts the assembly). A register in real code still renames.
        c = CompressPlaceholderNames()
        out = c.apply("void f() { eax = 1; __asm { vmovdqa xmm4, [rsp+var_28] } }")
        assert "[rsp+var_28]" in out  # asm operands untouched
        assert "rsp" in out and "var_28" in out
        assert "eax = 1;" not in out  # the real-code register was renamed

    def test_consistent_renaming(self) -> None:
        # The same placeholder maps to the same new name everywhere; two distinct
        # placeholders map to two distinct names, so structure is preserved.
        c = CompressPlaceholderNames()
        out = c.apply("x = local_10;\ny = local_10 + local_20;\nz = local_20;\n")
        assert "local_10" not in out and "local_20" not in out
        assert out.count("+") == 1

    def test_hexrays_local_vars_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("x = v1 + v17;")
        assert "v1" not in out and "v17" not in out

    def test_hexrays_arg_vars_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("return a1 + a2;")
        assert "a1" not in out and "a2" not in out

    def test_ghidra_param_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("x = param_1 + param_2;")
        assert "param_1" not in out and "param_2" not in out

    def test_jump_labels_renamed_consistently(self) -> None:
        # LAB_* label in both the goto and the label definition must use the
        # same short name so the control flow remains valid.
        c = CompressPlaceholderNames()
        out = c.apply("if (c) goto LAB_00401234; LAB_00401234: x = 1;")
        assert "LAB_00401234" not in out
        # The goto target and the label definition must be the same token.
        import re
        gotos = re.findall(r"goto\s+(\w+)", out)
        labels = re.findall(r"(\w+)\s*:", out)
        assert gotos and labels and gotos[0] in labels

    def test_ida_loc_label_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("goto loc_401234; loc_401234: return 0;")
        assert "loc_401234" not in out

    def test_ghidra_register_placeholders_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("x = extraout_EAX; y = unaff_EBX; z = in_EAX;")
        assert "extraout_EAX" not in out
        assert "unaff_EBX" not in out
        assert "in_EAX" not in out

    def test_ghidra_code_r0x_labels_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("goto code_r0x00401abc; code_r0x00401abc: x = 1;")
        assert "code_r0x00401abc" not in out

    def test_placeholder_inside_string_not_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply('x = local_10; s = "local_10";')
        assert '"local_10"' in out

    def test_last_mapping_populated(self) -> None:
        c = CompressPlaceholderNames()
        c.apply("x = local_10 + local_20;")
        assert "local_10" in c.last_mapping and "local_20" in c.last_mapping
        assert c.last_mapping["local_10"] != c.last_mapping["local_20"]

    def test_bn_label_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("goto label_401abc; label_401abc: x = 1;")
        assert "label_401abc" not in out

    def test_hexrays_LABEL_renamed_consistently(self) -> None:
        # Hex-Rays spells pseudocode labels `LABEL_<n>` (a sequential integer),
        # distinct from Ghidra's `LAB_<addr>` and IDA's `loc_<addr>`. The goto and
        # the label definition must remap to the same fresh token.
        import re

        c = CompressPlaceholderNames()
        out = c.apply("if (c) goto LABEL_137; LABEL_137: x = 1;")
        assert "LABEL_137" not in out
        gotos = re.findall(r"goto\s+(\w+)\s*;", out)
        labels = re.findall(r"(\w+)\s*:", out)
        assert gotos and labels and gotos[0] in labels

    def test_lowercase_label_not_a_hexrays_LABEL(self) -> None:
        # `LABEL_\d+` is uppercase and digit-tailed; a real lowercase identifier
        # such as `label_count` must never be mistaken for a placeholder.
        c = CompressPlaceholderNames()
        assert c.apply("int label_count = 0;") == "int label_count = 0;"

    def test_leading_underscore_split_slot_locals(self) -> None:
        # Ghidra split-slot spellings carry a leading underscore the base
        # local/Stack patterns did not match.
        c = CompressPlaceholderNames()
        out = c.apply("_local_48 = 1; _uStack_40 = 2; _auStack_80 = 3;")
        for nm in ("_local_48", "_uStack_40", "_auStack_80"):
            assert nm not in out

    def test_uram_absolute_memory_pseudo_symbol(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("a = uRam0010c3f8; b = lRam0010e458;")
        assert "uRam0010c3f8" not in out and "lRam0010e458" not in out

    def test_symbolless_ptr_renamed_but_symbol_bearing_kept(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("x = PTR_0010aff8; y = PTR_free_0010b000;")
        assert "PTR_0010aff8" not in out  # bare address pointer -> renamed
        assert "PTR_free_0010b000" in out  # symbol-bearing -> preserved here

    def test_ghidra_switchD_case_label_renamed(self) -> None:
        import re

        c = CompressPlaceholderNames()
        out = c.apply("goto switchD_00103dbb_caseD_2; switchD_00103dbb_caseD_2: x = 1;")
        assert "switchD_00103dbb_caseD_2" not in out
        gotos = re.findall(r"goto\s+(\w+)\s*;", out)
        labels = re.findall(r"(\w+)\s*:", out)
        assert gotos and labels and gotos[0] in labels

    def test_bn_result_temps_renamed(self) -> None:
        # `result` is Binary Ninja's default for an unrecovered return-value temp.
        c = CompressPlaceholderNames()
        out = c.apply("result = f(); result = result + 1; x = result_2;")
        assert "result" not in out and "result_2" not in out

    def test_result_member_access_kept(self) -> None:
        c = CompressPlaceholderNames()
        assert c.apply("x = p->result;") == "x = p->result;"

    def test_bn_vector_register_temps_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("a = zmm0_1 + xmm1; b = ymm2; c = mm0;")
        for ph in ("zmm0_1", "xmm1", "ymm2", "mm0"):
            assert ph not in out, f"{ph} should be renamed"

    def test_bn_x87_fpu_temps_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("x87_r7_1 = a; b = x87_r0;")
        assert "x87_r7_1" not in out and "x87_r0" not in out

    def test_bn_temp_ssa_suffix_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("temp6_1 = a; temp7_1 = b;")
        assert "temp6_1" not in out and "temp7_1" not in out

    def test_bn_entry_register_spill_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("f(entry_rdx, entry_rcx, entry_r8, entry_r9);")
        for ph in ("entry_rdx", "entry_rcx", "entry_r8", "entry_r9"):
            assert ph not in out, f"{ph} should be renamed"

    def test_bn_entry_semantic_names_kept(self) -> None:
        # Recovered names that merely share the `entry_` prefix must survive.
        c = CompressPlaceholderNames()
        out = c.apply("g(entry_argv, entry_message, entry_category);")
        for nm in ("entry_argv", "entry_message", "entry_category"):
            assert nm in out, f"{nm} must be preserved"

    def test_bn_flag_temp_after_normalization(self) -> None:
        # `cond:0` is normalized to `cond0` by flag-temps before this pass.
        c = CompressPlaceholderNames()
        out = c.apply("a = cond0 + cond12_1;")
        assert "cond0" not in out and "cond12_1" not in out

    def test_ghidra_deep_pointer_prefix_renamed(self) -> None:
        # The leading `p`-run encodes pointer depth and defeats the anchored
        # base pattern; a 14-deep name must rename like its shallow base.
        c = CompressPlaceholderNames()
        out = c.apply("ppppppppppppppuVar64 = gr; q = ppppppppppppppuStack_50;")
        assert "ppppppppppppppuVar64" not in out
        assert "ppppppppppppppuStack_50" not in out

    def test_ghidra_dat_subfield_suffix_renamed(self) -> None:
        c = CompressPlaceholderNames()
        out = c.apply("DAT_001163b0_4 = 0; DAT_00116340_12 = 1;")
        assert "DAT_001163b0_4" not in out and "DAT_00116340_12" not in out

    def test_ghidra_switchD_scope_halves_renamed_consistently(self) -> None:
        # `switchD_<addr>::switchdataD_<addr>` -- the `::` splits the name; each
        # address-derived half renames independently but consistently.
        c = CompressPlaceholderNames()
        out = c.apply("a = &switchD_00105dac::switchdataD_00107e80 + (&switchD_00105dac::switchdataD_00107e80)[i];")
        assert "switchD_00105dac" not in out and "switchdataD_00107e80" not in out
        # the data symbol recurs -> same short name both times (one `+`, two refs)
        assert out.count("::") == 2

    def test_member_access_split_across_lines_kept_consistently(self) -> None:
        # Regression (F2): the member-access guard skips all whitespace, including
        # a newline, so a field accessed as `p->\nresult` is recognised as a member
        # at *both* sites -- otherwise one use would be renamed and the other kept,
        # producing an inconsistent reference to a nonexistent field.
        c = CompressPlaceholderNames()
        out = c.apply("p->\nresult = 1; x = p->result;")
        assert out == "p->\nresult = 1; x = p->result;"

    def test_struct_field_declaration_not_renamed(self) -> None:
        # Regression (F1): a field declared inside a struct/union body is a real
        # source-derived name, not a placeholder. Renaming the declaration while
        # the member-access guard preserves every use (`c->eax`) would leave the
        # struct declaring fields the code never references. The declaration must
        # be preserved too, consistently with its uses.
        c = CompressPlaceholderNames()
        src = "struct S { unsigned int eax; unsigned int ebx; }; void h(struct S *c){ c->eax = c->ebx; }"
        out = c.apply(src)
        assert "eax" in out and "ebx" in out
        assert "struct S { unsigned int eax; unsigned int ebx; }" in out

    def test_struct_field_preserved_but_standalone_local_renamed(self) -> None:
        # A name spelled like a placeholder is preserved inside the struct body
        # (real field) yet still compressed where it is a genuine standalone local
        # outside any aggregate -- the two are distinct entities.
        c = CompressPlaceholderNames()
        out = c.apply("struct S { int result; }; int g(struct S *s){ int result; result = s->result; return result; }")
        assert "struct S { int result; }" in out  # field declaration preserved
        assert "s->result" in out                  # member access preserved
        assert "int result;" not in out.split("}", 1)[1]  # the standalone local was renamed

    def test_enum_constants_renamed_consistently_def_and_use(self) -> None:
        # Regression: an enum body is NOT a protected span, because enum constants
        # are referenced as bare identifiers (no `.`/`->`). Protecting only the
        # definition would rename every use while keeping the definition verbatim,
        # producing undefined references. A placeholder-spelled constant must rename
        # consistently across its definition and all uses.
        c = CompressPlaceholderNames()
        out = c.apply("enum E { v1 = 1, v2 = 2 }; int f(){ return v1 + v2; }")
        assert "v1" not in out and "v2" not in out  # both def and uses renamed
        # ...and a real (non-placeholder) enum constant is left untouched.
        out2 = c.apply("enum Color { RED = 1, GREEN = 2 }; int f(){ return RED + GREEN; }")
        assert out2 == "enum Color { RED = 1, GREEN = 2 }; int f(){ return RED + GREEN; }"
