#include "out.h"


undefined DAT_0040d430;
undefined DAT_0040d42c;
undefined DAT_0040d428;
undefined DAT_0040d424;
undefined DAT_0040d420;
undefined DAT_0040d41c;
undefined DAT_0040d448;
undefined DAT_0040d43c;
undefined DAT_0040d418;
undefined DAT_0040d414;
undefined DAT_0040d410;
undefined DAT_0040d40c;
undefined DAT_0040d440;
undefined DAT_0040d434;
undefined4 DAT_0040d438;
undefined DAT_0040d444;
undefined DAT_0040d380;
undefined DAT_0040d33c;
undefined DAT_0040d330;
undefined DAT_0040d334;
undefined DAT_0040d340;
undefined4 DAT_0040d004;
undefined4 DAT_0040d000;
undefined4 DAT_0040d344;
pointer PTR_DAT_0040b5a0;
undefined LAB_00408988;
void *ExceptionList;
uint DAT_0040d004;
undefined DAT_0040d750;
uint DAT_0040d02c;
uint DAT_0040d754;
pointer[2] vftable;
char DAT_0040d701;
undefined4 DAT_0040d704;
undefined DAT_0040d708;
undefined DAT_0040d70c;
undefined4 DAT_0040d710;
undefined DAT_0040d714;
undefined DAT_0040d718;
undefined DAT_00402c70;
undefined4 DAT_0040d6ec;
undefined LAB_004089b8;
undefined LAB_00408a10;
int DAT_0040d01c;
undefined DAT_0040b480;
undefined DAT_0040b484;
int DAT_0040d028;
undefined LAB_004089e0;
undefined4 DAT_0040d6fc;
undefined LAB_00408ad0;
int DAT_0040d030;
undefined DAT_0040ab78;
undefined DAT_0040d744;
undefined1 DAT_0040d700;
undefined4 DAT_0040c120;
undefined DAT_0040c324;
undefined4 DAT_0040d6f0;
undefined DAT_0040d320;
undefined DAT_0040d768;
int DAT_0040d014;
undefined DAT_0040c94c;
IMAGE_DOS_HEADER IMAGE_DOS_HEADER_00400000;
undefined __except_handler4;
pointer[1] vftable;
undefined DAT_00402b40;
int DAT_0040d004;
undefined LAB_00408a40;
undefined DAT_004020cc;
undefined DAT_00402e00;
undefined DAT_00403214;
undefined LAB_00408aa0;
undefined DAT_0040d75c;
char DAT_0040d700;
undefined *PTR_s_The_value_of_ESP_was_not_properl_0040aee4;
undefined DAT_0040d00c;
undefined LAB_00408940;
TypeDescriptor RTTI_Type_Descriptor;
undefined DAT_0040d738;
uint DAT_0040d000;
undefined DAT_0040d728;
undefined DAT_0040c8e8;
undefined DAT_00403908;
undefined LAB_00401195;
undefined LAB_00408a70;
int DAT_0040d6fc;
char DAT_0040d74d;
HMODULE DAT_0040d748;
undefined DAT_0040b890;
undefined LAB_00401343;
undefined LAB_004013c0;
int DAT_0040d6f8;
undefined DAT_0040a000;
undefined DAT_0040a208;
undefined DAT_0040a30c;
undefined DAT_0040a618;
undefined DAT_0040aefc;
undefined __except_handler4_noexcept;
int DAT_0040d018;
undefined DAT_0040d348;
undefined *PTR_s_Stack_pointer_corruption_0040b5ac;
undefined __security_check_cookie;
pointer PTR_guard_check_icall_0040f000;
undefined guard_check_icall;
char DAT_0040d74c;

// WARNING: Globals starting with '_' overlap smaller symbols at the same address

void __cdecl ___report_gsfailure(void)

{
  code *pcVar1;
  uint uVar2;
  undefined4 extraout_ECX;
  undefined4 extraout_ECX_00;
  undefined4 uVar3;
  uint extraout_EDX;
  undefined4 unaff_EBX;
  undefined4 unaff_EBP;
  undefined4 unaff_ESI;
  undefined4 unaff_EDI;
  undefined2 in_ES;
  undefined2 in_CS;
  undefined2 in_SS;
  undefined2 in_DS;
  undefined2 in_FS;
  undefined2 in_GS;
  byte bVar4;
  byte bVar5;
  byte in_AF;
  byte bVar6;
  byte bVar7;
  byte in_TF;
  byte in_IF;
  byte bVar8;
  byte in_NT;
  byte in_AC;
  byte in_VIF;
  byte in_VIP;
  byte in_ID;
  longlong lVar9;
  undefined4 unaff_retaddr;
  
  uVar2 = IsProcessorFeaturePresent(0x17);
  bVar4 = 0;
  bVar8 = 0;
  bVar7 = (int)uVar2 < 0;
  bVar6 = uVar2 == 0;
  bVar5 = (POPCOUNT(uVar2 & 0xff) & 1U) == 0;
  lVar9 = (ulonglong)extraout_EDX << 0x20;
  uVar3 = extraout_ECX;
  if (!(bool)bVar6) {
    pcVar1 = (code *)swi(0x29);
    lVar9 = (*pcVar1)();
    uVar3 = extraout_ECX_00;
  }
  _DAT_0040d428 = (undefined4)((ulonglong)lVar9 >> 0x20);
  _DAT_0040d430 = (undefined4)lVar9;
  _DAT_0040d440 =
       (uint)(in_NT & 1) * 0x4000 | (uint)(bVar8 & 1) * 0x800 | (uint)(in_IF & 1) * 0x200 |
       (uint)(in_TF & 1) * 0x100 | (uint)(bVar7 & 1) * 0x80 | (uint)(bVar6 & 1) * 0x40 |
       (uint)(in_AF & 1) * 0x10 | (uint)(bVar5 & 1) * 4 | (uint)(bVar4 & 1) |
       (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
       (uint)(in_AC & 1) * 0x40000;
  _DAT_0040d444 = &stack0x00000004;
  _DAT_0040d380 = 0x10001;
  _DAT_0040d330 = 0xc0000409;
  _DAT_0040d334 = 1;
  _DAT_0040d340 = 1;
  DAT_0040d344 = 2;
  _DAT_0040d33c = unaff_retaddr;
  _DAT_0040d40c = in_GS;
  _DAT_0040d410 = in_FS;
  _DAT_0040d414 = in_ES;
  _DAT_0040d418 = in_DS;
  _DAT_0040d41c = unaff_EDI;
  _DAT_0040d420 = unaff_ESI;
  _DAT_0040d424 = unaff_EBX;
  _DAT_0040d42c = uVar3;
  _DAT_0040d434 = unaff_EBP;
  DAT_0040d438 = unaff_retaddr;
  _DAT_0040d43c = in_CS;
  _DAT_0040d448 = in_SS;
  ___raise_securityfailure((_EXCEPTION_POINTERS *)&PTR_DAT_0040b5a0);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_004022d0(undefined4 *param_1)

{
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408988;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  thunk_FUN_00401c30(param_1);
  uStack_8 = 0;
  thunk_FUN_00402a90(param_1);
  ExceptionList = pvStack_10;
  return param_1;
}



// WARNING: Removing unreachable block (ram,0x0040701a)
// WARNING: Removing unreachable block (ram,0x00406f46)
// WARNING: Removing unreachable block (ram,0x00406ed0)
// WARNING: Globals starting with '_' overlap smaller symbols at the same address

void ___isa_available_init(void)

{
  int *piVar1;
  uint *puVar2;
  int iVar3;
  uint uVar4;
  BOOL BVar5;
  uint uVar6;
  uint uVar7;
  uint in_XCR0;
  uint uStack_c;
  
  uVar4 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  _DAT_0040d750 = 0;
  DAT_0040d02c = DAT_0040d02c | 1;
  BVar5 = IsProcessorFeaturePresent(10);
  uVar6 = DAT_0040d02c;
  if (BVar5 != 0) {
    uStack_c = 0;
    _DAT_0040d750 = 1;
    piVar1 = (int *)cpuid_basic_info(0);
    puVar2 = (uint *)cpuid_Version_info(1);
    uVar6 = *puVar2;
    uVar7 = puVar2[3];
    if (((piVar1[1] == 0x756e6547 && piVar1[2] == 0x49656e69) && piVar1[3] == 0x6c65746e) &&
       ((((((uVar6 & 0xfff3ff0) == 0x106c0 || ((uVar6 & 0xfff3ff0) == 0x20660)) ||
          ((uVar6 & 0xfff3ff0) == 0x20670)) ||
         (((uVar6 & 0xfff3ff0) == 0x30650 || ((uVar6 & 0xfff3ff0) == 0x30660)))) ||
        ((uVar6 & 0xfff3ff0) == 0x30670)))) {
      DAT_0040d754 = DAT_0040d754 | 1;
    }
    if (6 < *piVar1) {
      iVar3 = cpuid_Extended_Feature_Enumeration_info(7);
      uStack_c = *(uint *)(iVar3 + 4);
      if ((uStack_c & 0x200) != 0) {
        DAT_0040d754 = DAT_0040d754 | 2;
      }
    }
    uVar6 = DAT_0040d02c | 2;
    if ((uVar7 & 0x100000) != 0) {
      _DAT_0040d750 = 2;
      uVar6 = DAT_0040d02c | 6;
      if ((((uVar7 & 0x8000000) != 0) && ((uVar7 & 0x10000000) != 0)) && ((in_XCR0 & 6) == 6)) {
        _DAT_0040d750 = 3;
        uVar6 = DAT_0040d02c | 0xe;
        if ((uStack_c & 0x20) != 0) {
          _DAT_0040d750 = 5;
          uVar6 = DAT_0040d02c | 0x2e;
        }
      }
    }
  }
  DAT_0040d02c = uVar6;
  __security_check_cookie(uVar4 ^ (uint)&stack0xfffffffc);
  return;
}



void FID_conflict___initialize_denormal_control(void)

{
  return;
}



undefined4 __cdecl thunk_FUN_00406380(undefined4 *param_1)

{
  return *param_1;
}



exception * __thiscall std::exception::exception(exception *this,char *param_1,int param_2)

{
  *(undefined ***)this = vftable;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(char **)(this + 4) = param_1;
  return this;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

undefined4 __cdecl ___scrt_initialize_onexit_tables(int param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  uint uVar2;
  _func_void **pp_Var3;
  
  if (DAT_0040d701 != '\0') {
    return 1;
  }
  if ((param_1 != 0) && (param_1 != 1)) {
    ___scrt_fastfail();
  }
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if ((CONCAT31(extraout_var,bVar1) == 0) || (param_1 != 0)) {
    pp_Var3 = __crt_fast_encode_pointer<void_(__cdecl**)(void)>((_func_void **)0xffffffff);
    DAT_0040d704 = pp_Var3;
    _DAT_0040d708 = pp_Var3;
    _DAT_0040d70c = pp_Var3;
    DAT_0040d710 = pp_Var3;
    _DAT_0040d714 = pp_Var3;
    _DAT_0040d718 = pp_Var3;
  }
  else {
    uVar2 = initialize_onexit_table(&DAT_0040d704);
    if (uVar2 != 0) {
      return uVar2 & 0xffffff00;
    }
    uVar2 = initialize_onexit_table(&DAT_0040d710);
    if (uVar2 != 0) {
      return uVar2 & 0xffffff00;
    }
    pp_Var3 = (_func_void **)0x0;
  }
  DAT_0040d701 = 1;
  return CONCAT31((int3)((uint)pp_Var3 >> 8),1);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __thiscall thunk_FUN_00402bc0(void *this,uint param_1)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  undefined4 extraout_EDX;
  undefined4 uVar4;
  undefined8 uVar5;
  uint uStack_24;
  uint uStack_20;
  undefined4 uStack_1c;
  uint auStack_18 [4];
  void *pvStack_8;
  
  uStack_24 = 0xcccccccc;
  uStack_20 = 0xcccccccc;
  uStack_1c = 0xcccccccc;
  auStack_18[0] = 0xcccccccc;
  auStack_18[1] = 0xcccccccc;
  auStack_18[2] = 0xcccccccc;
  auStack_18[3] = 0xcccccccc;
  pvStack_8 = this;
  uVar5 = thunk_FUN_00403870(this);
  auStack_18[3] = (uint)uVar5;
  uVar5 = thunk_FUN_00402e90(pvStack_8);
  auStack_18[2] = (uint)uVar5;
  auStack_18[0] = param_1 | 0xf;
  uVar2 = auStack_18[3];
  if (auStack_18[0] <= auStack_18[3]) {
    uStack_20 = *(uint *)(auStack_18[2] + 0x18);
    uVar3 = auStack_18[3] - (uStack_20 >> 1);
    uVar5 = CONCAT44(uVar3,auStack_18[2]);
    if (uStack_20 <= uVar3) {
      uStack_24 = (uStack_20 >> 1) + uStack_20;
      puVar1 = thunk_FUN_00401f10(auStack_18,&uStack_24);
      uVar5 = CONCAT44(extraout_EDX,auStack_18[2]);
      uVar2 = *puVar1;
    }
  }
  uVar4 = (undefined4)((ulonglong)uVar5 >> 0x20);
  auStack_18[2] = (uint)uVar5;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00402c70);
  return CONCAT44(uVar4,uVar2);
}



undefined4 thunk_FUN_00405dc0(void)

{
  return 0x4000;
}



undefined4 thunk_FUN_00405310(void)

{
  return DAT_0040d6ec;
}



uint __cdecl __crt_rotate_pointer_value(uint param_1,int param_2)

{
  byte bVar1;
  
  bVar1 = (byte)param_2 & 0x1f;
  return param_1 >> bVar1 | param_1 << 0x20 - bVar1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 __cdecl thunk_FUN_00403a70(undefined4 param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  
  uVar2 = 0;
  uVar1 = __acrt_iob_func(1,param_1,0,&stack0x00000008);
  uVar1 = thunk_FUN_00403a20(uVar1,0x403ab0,param_1,uVar2);
  return uVar1;
}



undefined4 FID_conflict____scrt_initialize_mta(void)

{
  return 0;
}



undefined4 thunk_FUN_00405db0(void)

{
  return 0;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __thiscall thunk_FUN_004023f0(void *this,char *param_1)

{
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_004089b8;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  thunk_FUN_004022d0(this);
  uStack_8 = 0;
  thunk_FUN_00403370(this);
  thunk_FUN_004034c0(this,param_1);
  ExceptionList = pvStack_10;
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_004039a0(void *param_1,void *param_2,size_t param_3)

{
  memmove(param_1,param_2,param_3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

int __fastcall thunk_FUN_00403090(int param_1)

{
  bool bVar1;
  undefined4 uStack_c;
  
  uStack_c = param_1 + 4;
  bVar1 = thunk_FUN_00402fa0(param_1);
  if (bVar1) {
    uStack_c = thunk_FUN_004021a0(*(undefined4 *)(param_1 + 4));
  }
  return uStack_c;
}



void thunk_FUN_00402290(void)

{
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall thunk_FUN_004027f0(void *this,char *param_1)

{
  thunk_FUN_004034c0(this,param_1);
  return;
}



bad_array_new_length * __thiscall
std::bad_array_new_length::bad_array_new_length(bad_array_new_length *this)

{
  bad_alloc::bad_alloc((bad_alloc *)this,"bad array new length");
  *(undefined ***)this = vftable;
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00401c90(void *param_1,char *param_2)

{
  thunk_FUN_00402cc0(param_1,param_2);
  return;
}



undefined1 thunk_FUN_00407430(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FID_conflict__CAtlWinModule(int param_1)

{
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408a10;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  thunk_FUN_00402d70(param_1);
  ~CAssoc(param_1);
  ExceptionList = pvStack_10;
  return;
}



void __cdecl _RTC_AllocaFailure(void *param_1,_RTC_ALLOCA_NODE *param_2,int param_3)

{
  int iVar1;
  char acStack_144 [244];
  char acStack_50 [52];
  char acStack_1c [20];
  uint uStack_8;
  
  iVar1 = DAT_0040d01c;
  uStack_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  if (DAT_0040d01c != -1) {
    if (param_2 == (_RTC_ALLOCA_NODE *)0x0) {
      failwithmessage(param_1,DAT_0040d01c,4,
                      "Stack area around _alloca memory reserved by this function is corrupted\n");
      __security_check_cookie(uStack_8 ^ (uint)&stack0xfffffffc);
      return;
    }
    _getMemBlockDataString
              (acStack_1c,acStack_50,(char *)(param_2 + 0x20),*(int *)(param_2 + 0xc) - 0x24);
    _sprintf_s(acStack_144,0xf4,"%s%s%p%s%zd%s%d%s%s%s%s%s",
               "Stack area around _alloca memory reserved by this function is corrupted",
               "\nAddress: 0x",param_2 + 0x20,"\nSize: ",*(int *)(param_2 + 0xc) + -0x24,
               "\nAllocation number within this function: ",param_3,"\nData: <",acStack_1c,
               &DAT_0040b484,acStack_50,&DAT_0040b480);
    failwithmessage(param_1,iVar1,4,acStack_144);
  }
  __security_check_cookie(uStack_8 ^ (uint)&stack0xfffffffc);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00403740(int param_1)

{
  thunk_FUN_00403600(param_1 + 4);
  thunk_FUN_00403a70("animal: %s\n");
  return;
}



bool ___scrt_is_user_matherr_present(void)

{
  return DAT_0040d028 == 0;
}



exception * __thiscall std::exception::exception(exception *this,exception *param_1)

{
  *(undefined ***)this = vftable;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  __std_exception_copy(param_1 + 4,this + 4);
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_00402490(undefined4 *param_1)

{
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_004089e0;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  thunk_FUN_004022d0(param_1);
  thunk_FUN_00403370(param_1);
  ExceptionList = pvStack_10;
  return param_1;
}



void __cdecl ___scrt_release_startup_lock(char param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if ((CONCAT31(extraout_var,bVar1) != 0) && (param_1 == '\0')) {
    LOCK();
    DAT_0040d6fc = 0;
    UNLOCK();
  }
  return;
}



undefined4 __fastcall thunk_FUN_00402f00(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00403830(char *param_1)

{
  strlen(param_1);
  return;
}



undefined1 thunk_FUN_00407420(void)

{
  return 1;
}



undefined4 thunk_FUN_00407450(void)

{
  return 0;
}



void __cdecl ___raise_securityfailure(_EXCEPTION_POINTERS *param_1)

{
  HANDLE hProcess;
  UINT uExitCode;
  
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)0x0);
  UnhandledExceptionFilter(param_1);
  uExitCode = 0xc0000409;
  hProcess = GetCurrentProcess();
  TerminateProcess(hProcess,uExitCode);
  return;
}



undefined1 thunk_FUN_00407410(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00402ba0(uint param_1)

{
  operator_new(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00403600(undefined4 param_1)

{
  int iVar1;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408ad0;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  iVar1 = thunk_FUN_00402e90(param_1);
  thunk_FUN_00403090(iVar1);
  ExceptionList = pvStack_10;
  return;
}



void thunk_FUN_00403400(void)

{
                    // WARNING: Subroutine does not return
  std::_Xlength_error("string too long");
}



undefined4 __cdecl thunk_FUN_004027e0(undefined4 param_1,undefined4 param_2)

{
  return param_2;
}



void FID_conflict___initialize_denormal_control(void)

{
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

void __cdecl ___report_securityfailure(undefined4 param_1)

{
  code *pcVar1;
  uint uVar2;
  undefined4 extraout_ECX;
  undefined4 extraout_ECX_00;
  undefined4 uVar3;
  uint extraout_EDX;
  undefined4 unaff_EBX;
  undefined4 unaff_EBP;
  undefined4 unaff_ESI;
  undefined4 unaff_EDI;
  undefined2 in_ES;
  undefined2 in_CS;
  undefined2 in_SS;
  undefined2 in_DS;
  undefined2 in_FS;
  undefined2 in_GS;
  byte bVar4;
  byte bVar5;
  byte in_AF;
  byte bVar6;
  byte bVar7;
  byte in_TF;
  byte in_IF;
  byte bVar8;
  byte in_NT;
  byte in_AC;
  byte in_VIF;
  byte in_VIP;
  byte in_ID;
  longlong lVar9;
  undefined4 unaff_retaddr;
  
  uVar2 = IsProcessorFeaturePresent(0x17);
  bVar4 = 0;
  bVar8 = 0;
  bVar7 = (int)uVar2 < 0;
  bVar6 = uVar2 == 0;
  bVar5 = (POPCOUNT(uVar2 & 0xff) & 1U) == 0;
  lVar9 = (ulonglong)extraout_EDX << 0x20;
  uVar3 = extraout_ECX;
  if (!(bool)bVar6) {
    pcVar1 = (code *)swi(0x29);
    lVar9 = (*pcVar1)();
    uVar3 = extraout_ECX_00;
  }
  _DAT_0040d428 = (undefined4)((ulonglong)lVar9 >> 0x20);
  _DAT_0040d430 = (undefined4)lVar9;
  _DAT_0040d440 =
       (uint)(in_NT & 1) * 0x4000 | (uint)(bVar8 & 1) * 0x800 | (uint)(in_IF & 1) * 0x200 |
       (uint)(in_TF & 1) * 0x100 | (uint)(bVar7 & 1) * 0x80 | (uint)(bVar6 & 1) * 0x40 |
       (uint)(in_AF & 1) * 0x10 | (uint)(bVar5 & 1) * 4 | (uint)(bVar4 & 1) |
       (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
       (uint)(in_AC & 1) * 0x40000;
  _DAT_0040d444 = &param_1;
  _DAT_0040d330 = 0xc0000409;
  _DAT_0040d334 = 1;
  _DAT_0040d340 = 1;
  DAT_0040d344 = param_1;
  _DAT_0040d33c = unaff_retaddr;
  _DAT_0040d40c = in_GS;
  _DAT_0040d410 = in_FS;
  _DAT_0040d414 = in_ES;
  _DAT_0040d418 = in_DS;
  _DAT_0040d41c = unaff_EDI;
  _DAT_0040d420 = unaff_ESI;
  _DAT_0040d424 = unaff_EBX;
  _DAT_0040d42c = uVar3;
  _DAT_0040d434 = unaff_EBP;
  DAT_0040d438 = unaff_retaddr;
  _DAT_0040d43c = in_CS;
  _DAT_0040d448 = in_SS;
  ___raise_securityfailure((_EXCEPTION_POINTERS *)&PTR_DAT_0040b5a0);
  return;
}



bool ___scrt_is_ucrt_dll_in_use(void)

{
  return DAT_0040d030 != 0;
}



undefined4 thunk_FUN_00403860(void)

{
  return 0xffffffff;
}



undefined1 thunk_FUN_00407430(void)

{
  return 1;
}



undefined4 __fastcall thunk_FUN_00402ee0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00403670(void *param_1,void *param_2,size_t param_3)

{
  memcmp(param_1,param_2,param_3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

uint __cdecl thunk_FUN_00401d00(uint param_1)

{
  code *pcVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint uStack_8;
  
  uStack_8 = param_1 + 0x27;
  if (uStack_8 <= param_1) {
    uStack_8 = 0xffffffff;
  }
  iVar2 = thunk_FUN_00402ba0(uStack_8);
  if (iVar2 == 0) {
    iVar3 = _CrtDbgReport(2,
                          "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                          ,0x65,0,&DAT_0040ab78,"invalid argument");
    if (iVar3 == 1) {
      pcVar1 = (code *)swi(3);
      uVar4 = (*pcVar1)();
      return uVar4;
    }
    invalid_parameter(L"\"invalid argument\"",L"std::_Allocate_manually_vector_aligned",
                      L"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                      ,0x65,0,0x401d72);
  }
  uVar4 = iVar2 + 0x27U & 0xffffffe0;
  *(int *)(uVar4 - 4) = iVar2;
  *(undefined4 *)(uVar4 - 8) = 0xfafafafa;
  return uVar4;
}



undefined4 * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  thunk_FUN_00403e40(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



undefined1 __should_initialize_environment(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

int __fastcall thunk_FUN_00403020(int param_1)

{
  bool bVar1;
  undefined4 uStack_c;
  
  uStack_c = param_1 + 4;
  bVar1 = thunk_FUN_00402fa0(param_1);
  if (bVar1) {
    uStack_c = thunk_FUN_004021a0(*(undefined4 *)(param_1 + 4));
  }
  return uStack_c;
}



void __cdecl thunk_FUN_00404690(undefined4 param_1)

{
  free_dbg(param_1,0xffffffff);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void thunk_FUN_00403960(void)

{
  thunk_FUN_00403a70("meow\n");
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

void __cdecl __crt_debugger_hook(int param_1)

{
  _DAT_0040d744 = 0;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_00402370(undefined4 *param_1)

{
  thunk_FUN_004025e0(param_1);
  thunk_FUN_004025c0(param_1 + 1);
  param_1[5] = 0;
  param_1[6] = 0;
  return param_1;
}



int __cdecl ___scrt_initialize_crt(int param_1)

{
  char cVar1;
  int iVar2;
  undefined3 extraout_var;
  uint3 extraout_var_00;
  
  if (param_1 == 0) {
    DAT_0040d700 = 1;
  }
  ___isa_available_init();
  cVar1 = thunk_FUN_00407400();
  if (cVar1 == '\0') {
    iVar2 = 0;
  }
  else {
    cVar1 = thunk_FUN_00407400();
    if (cVar1 == '\0') {
      thunk_FUN_00407430();
      iVar2 = (uint)extraout_var_00 << 8;
    }
    else {
      iVar2 = CONCAT31(extraout_var,1);
    }
  }
  return iVar2;
}



_func_void ** __cdecl __crt_fast_encode_pointer<void_(__cdecl**)(void)>(_func_void **param_1)

{
  uint uVar1;
  
  uVar1 = __crt_rotate_pointer_value((uint)param_1,0x20 - DAT_0040d004 % 0x20);
  return (_func_void **)(uVar1 ^ DAT_0040d004);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_00401c30(undefined4 *param_1)

{
  thunk_FUN_004023d0(param_1);
  thunk_FUN_00402370(param_1);
  return param_1;
}



undefined4 FID_conflict____scrt_initialize_mta(void)

{
  return 0;
}



void __cdecl __scrt_file_policy::set_commode(void)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  
  uVar1 = thunk_FUN_00405db0();
  puVar2 = (undefined4 *)__p__commode();
  *puVar2 = uVar1;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00402e90(undefined4 param_1)

{
  thunk_FUN_00402f20(param_1);
  return;
}



undefined4 __cdecl thunk_FUN_00401e20(undefined4 param_1)

{
  return param_1;
}



undefined1 thunk_FUN_00407400(void)

{
  return 1;
}



void __RTC_Initialize(void)

{
  code *pcVar1;
  undefined4 *puVar2;
  
  puVar2 = &DAT_0040c120;
  do {
    pcVar1 = (code *)*puVar2;
    if (pcVar1 != (code *)0x0) {
      guard_check_icall();
      (*pcVar1)();
    }
    puVar2 = puVar2 + 1;
  } while (puVar2 < &DAT_0040c324);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_00402580(undefined4 *param_1)

{
  thunk_FUN_00402500(param_1);
  *param_1 = Cat::vftable;
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void thunk_FUN_00403440(undefined4 param_1)

{
  uint uVar1;
  
  uVar1 = thunk_FUN_00401eb0(param_1);
  thunk_FUN_00401cb0(uVar1);
  return;
}



undefined4 thunk_FUN_00405320(void)

{
  return DAT_0040d6f0;
}



int __cdecl
__vsprintf_s_l(char *_DstBuf,size_t _DstSize,char *_Format,_locale_t _Locale,va_list _ArgList)

{
  undefined4 *puVar1;
  int iVar2;
  
  puVar1 = (undefined4 *)___local_stdio_scanf_options();
  iVar2 = __stdio_common_vsprintf_s(*puVar1,puVar1[1],_DstBuf,_DstSize,_Format,_Locale,_ArgList);
  if (iVar2 < 0) {
    iVar2 = -1;
  }
  return iVar2;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_004036d0(undefined4 param_1,int param_2,int param_3)

{
  thunk_FUN_00401e30(param_2,param_3 << 3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00403370(undefined4 param_1)

{
  undefined4 uStack_10;
  int iStack_c;
  undefined4 uStack_8;
  
  uStack_10 = 0xcccccccc;
  iStack_c = 0xcccccccc;
  uStack_8 = param_1;
  iStack_c = thunk_FUN_00402e60(param_1);
  *(undefined4 *)(iStack_c + 0x14) = 0;
  *(undefined4 *)(iStack_c + 0x18) = 0xf;
  uStack_10 = uStack_10 & 0xffffff;
  thunk_FUN_004035e0((undefined1 *)(iStack_c + 4),(undefined1 *)((int)&uStack_10 + 3));
  return;
}



exception * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  thunk_FUN_004044c0(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_004036a0(void *param_1,void *param_2,size_t param_3)

{
  memcpy(param_1,param_2,param_3);
  return;
}



undefined * ___local_stdio_scanf_options(void)

{
  return &DAT_0040d320;
}



int __cdecl thunk_FUN_00401ec0(uint param_1)

{
  undefined4 uStack_c;
  
  uStack_c = param_1 << 3;
  if (0x1fffffff < param_1) {
    uStack_c = -1;
  }
  return uStack_c;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00403270(undefined4 param_1)

{
  bool bVar1;
  undefined4 uStack_18;
  undefined4 uStack_14;
  int iStack_10;
  int iStack_c;
  undefined4 uStack_8;
  
  uStack_18 = 0xcccccccc;
  uStack_14 = 0xcccccccc;
  iStack_10 = -0x33333334;
  iStack_c = 0xcccccccc;
  uStack_8 = param_1;
  thunk_FUN_00403100(param_1);
  iStack_c = thunk_FUN_00402e60(uStack_8);
  bVar1 = thunk_FUN_00402fa0(iStack_c);
  if (bVar1) {
    iStack_10 = *(int *)(iStack_c + 4);
    uStack_14 = thunk_FUN_00402f40(uStack_8);
    thunk_FUN_004021c0(iStack_c + 4);
    thunk_FUN_00402290();
    thunk_FUN_00403700(iStack_10,*(int *)(iStack_c + 0x18) + 1);
  }
  *(undefined4 *)(iStack_c + 0x14) = 0;
  *(undefined4 *)(iStack_c + 0x18) = 0xf;
  uStack_18 = uStack_18 & 0xffffff;
  thunk_FUN_004035e0((undefined1 *)(iStack_c + 4),(undefined1 *)((int)&uStack_18 + 3));
  return;
}



undefined4 __fastcall thunk_FUN_004023d0(undefined4 param_1)

{
  return param_1;
}



undefined * FID_conflict____scrt_get_dyn_tls_dtor_callback(void)

{
  return &DAT_0040d768;
}



void __cdecl _RTC_StackFailure(void *param_1,char *param_2)

{
  int iVar1;
  uint uVar2;
  char *pcVar3;
  char acStack_408 [1024];
  uint uStack_8;
  
  iVar1 = DAT_0040d014;
  uStack_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  if (DAT_0040d014 == -1) goto LAB_0040498a;
  if (*param_2 == '\0') {
LAB_00404978:
    pcVar3 = "Stack corrupted near unknown variable";
  }
  else {
    uVar2 = _strlen_priv(param_2);
    if (0x400 < uVar2 + 0x2d) goto LAB_00404978;
    strcpy_s(acStack_408,0x400,"Stack around the variable \'");
    strcat_s(acStack_408,0x400,param_2);
    strcat_s(acStack_408,0x400,"\' was corrupted.");
    pcVar3 = acStack_408;
  }
  failwithmessage(param_1,iVar1,2,pcVar3);
LAB_0040498a:
  __security_check_cookie(uStack_8 ^ (uint)&stack0xfffffffc);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00401e80(undefined4 param_1,int param_2)

{
  thunk_FUN_004036d0(param_1,param_2,1);
  return;
}



undefined4 * __fastcall thunk_FUN_004025e0(undefined4 *param_1)

{
  *param_1 = 0;
  return param_1;
}



// guard_check_icall

void __cdecl guard_check_icall(void)

{
  return;
}



void __fastcall thunk_FUN_004044e0(exception *param_1)

{
  thunk_FUN_004044c0(param_1);
  return;
}



exception * __thiscall thunk_FUN_004045b0(void *this,uint param_1)

{
  std::exception::~exception(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl
thunk_FUN_00403a20(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 *puVar1;
  
  puVar1 = (undefined4 *)___local_stdio_scanf_options();
  __stdio_common_vfprintf(*puVar1,puVar1[1],param_1,param_2,param_3,param_4);
  return;
}



undefined4 __cdecl thunk_FUN_004021b0(undefined4 param_1)

{
  return param_1;
}



void thunk_FUN_00404620(void)

{
  bad_array_new_length abStack_10 [12];
  
  std::bad_array_new_length::bad_array_new_length(abStack_10);
                    // WARNING: Subroutine does not return
  _CxxThrowException(abStack_10,(ThrowInfo *)&DAT_0040c94c);
}



int __cdecl ___scrt_is_nonwritable_in_current_image(int param_1)

{
  bool bVar1;
  uint3 extraout_var;
  int iVar2;
  _IMAGE_SECTION_HEADER *p_Var3;
  uint3 uVar4;
  void *pvStack_14;
  code *pcStack_10;
  uint uStack_c;
  undefined4 uStack_8;
  
  pcStack_10 = __except_handler4;
  pvStack_14 = ExceptionList;
  uStack_c = DAT_0040d004 ^ 0x40c9b8;
  ExceptionList = &pvStack_14;
  uStack_8 = 0;
  bVar1 = is_potentially_valid_image_base(&IMAGE_DOS_HEADER_00400000);
  if (bVar1) {
    p_Var3 = find_pe_section((uchar *)&IMAGE_DOS_HEADER_00400000,param_1 - 0x400000);
    if (p_Var3 == (_IMAGE_SECTION_HEADER *)0x0) {
      iVar2 = 0;
    }
    else {
      uVar4 = (uint3)((uint)p_Var3 >> 8);
      if ((*(uint *)(p_Var3 + 0x24) & 0x80000000) == 0) {
        iVar2 = CONCAT31(uVar4,1);
      }
      else {
        iVar2 = (uint)uVar4 << 8;
      }
    }
  }
  else {
    iVar2 = (uint)extraout_var << 8;
  }
  ExceptionList = pvStack_14;
  return iVar2;
}



undefined4 __fastcall thunk_FUN_00402ec0(undefined4 param_1)

{
  return param_1;
}



uint ___scrt_is_managed_app(void)

{
  HMODULE pHVar1;
  uint uVar2;
  int *piVar3;
  
  pHVar1 = GetModuleHandleW((LPCWSTR)0x0);
  if (pHVar1 == (HMODULE)0x0) {
    uVar2 = 0;
  }
  else if ((short)pHVar1->unused == 0x5a4d) {
    piVar3 = (int *)((int)&pHVar1->unused + pHVar1[0xf].unused);
    if (*piVar3 == 0x4550) {
      if ((short)piVar3[6] == 0x10b) {
        if ((uint)piVar3[0x1d] < 0xf) {
          uVar2 = 0x100;
        }
        else if (piVar3[0x3a] == 0) {
          uVar2 = 0;
        }
        else {
          uVar2 = 1;
        }
      }
      else {
        uVar2 = (uint)(byte)((ushort)(short)piVar3[6] >> 8) << 8;
      }
    }
    else {
      uVar2 = (uint)piVar3 & 0xffffff00;
    }
  }
  else {
    uVar2 = (uint)pHVar1 & 0xffffff00;
  }
  return uVar2;
}



void __fastcall thunk_FUN_00403e40(undefined4 *param_1)

{
  *param_1 = type_info::vftable;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall thunk_FUN_00402a90(undefined4 param_1)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 uStack_c;
  undefined4 uStack_8;
  
  uStack_1c = 0xcccccccc;
  uStack_18 = 0xcccccccc;
  uStack_14 = 0xcccccccc;
  uStack_10 = 0xcccccccc;
  uStack_c = 0xcccccccc;
  uStack_8 = param_1;
  thunk_FUN_00402f40(param_1);
  thunk_FUN_00401c70((int)&uStack_10 + 3);
  uVar1 = thunk_FUN_00403480(1);
  uVar1 = thunk_FUN_004021b0(uVar1);
  puVar2 = (undefined4 *)thunk_FUN_00402ff0(uStack_8);
  *puVar2 = uVar1;
  puVar2 = thunk_FUN_00402610(&uStack_1c);
  puVar3 = (undefined4 *)thunk_FUN_00402ff0(uStack_8);
  thunk_FUN_00402230((int)&uStack_10 + 3,*puVar3,puVar2);
  uVar1 = thunk_FUN_00402e60(uStack_8);
  uVar1 = thunk_FUN_004021d0(uVar1);
  puVar3 = (undefined4 *)thunk_FUN_00402ff0(uStack_8);
  puVar2 = (undefined4 *)*puVar3;
  *puVar2 = uVar1;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00402b40);
  return CONCAT44(puVar2,puVar3);
}



undefined4 __cdecl thunk_FUN_004021c0(undefined4 param_1)

{
  return param_1;
}



void __fastcall __security_check_cookie(int param_1)

{
  if (param_1 == DAT_0040d004) {
    return;
  }
                    // WARNING: Subroutine does not return
  ___report_gsfailure();
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_004037e0(int param_1)

{
  thunk_FUN_00403600(param_1 + 4);
  thunk_FUN_00403a70("cat: %s\n");
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void thunk_FUN_00402830(void *param_1,size_t param_2,void *param_3)

{
  undefined4 uStack_c;
  
  uStack_c = 0xcccccccc;
  thunk_FUN_004036a0(param_1,param_3,param_2);
  uStack_c = uStack_c & 0xffffff;
  thunk_FUN_004035e0((undefined1 *)((int)param_1 + param_2),(undefined1 *)((int)&uStack_c + 3));
  return;
}



undefined4 thunk_FUN_00405dd0(void)

{
  return 0;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FID_conflict__CAtlWinModule(int param_1)

{
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408a40;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  thunk_FUN_00403270(param_1);
  FID_conflict__CAtlWinModule(param_1);
  ExceptionList = pvStack_10;
  return;
}



bad_alloc * __thiscall std::bad_alloc::bad_alloc(bad_alloc *this,char *param_1)

{
  exception::exception((exception *)this,param_1,1);
  *(undefined ***)this = vftable;
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __thiscall thunk_FUN_00401fb0(void *this,uint param_1,undefined4 param_2,void *param_3)

{
  void *pvVar1;
  undefined4 uVar2;
  int *extraout_EDX;
  int *piVar3;
  undefined8 uVar4;
  int aiStack_20 [5];
  int *piStack_c;
  void *pvStack_8;
  
  aiStack_20[0] = -0x33333334;
  aiStack_20[1] = 0xcccccccc;
  aiStack_20[2] = 0xcccccccc;
  aiStack_20[3] = 0xcccccccc;
  aiStack_20[4] = 0xcccccccc;
  piStack_c = (int *)0xcccccccc;
  pvStack_8 = this;
  uVar4 = thunk_FUN_00403870(this);
  if ((uint)uVar4 < param_1) {
    thunk_FUN_00403400();
  }
  piStack_c = (int *)thunk_FUN_00402e60(pvStack_8);
  aiStack_20[4] = piStack_c[6];
  uVar4 = thunk_FUN_00402bc0(pvStack_8,param_1);
  aiStack_20[3] = (int)uVar4;
  aiStack_20[2] = thunk_FUN_00402f40(pvStack_8);
  uVar4 = thunk_FUN_00403440(aiStack_20[3] + 1);
  aiStack_20[0] = (int)uVar4;
  thunk_FUN_00403140(piStack_c,(int)((ulonglong)uVar4 >> 0x20));
  piStack_c[5] = param_1;
  piStack_c[6] = aiStack_20[3];
  pvVar1 = (void *)thunk_FUN_004021a0(aiStack_20[0]);
  thunk_FUN_00402830(pvVar1,param_1,param_3);
  if ((uint)aiStack_20[4] < 0x10) {
    piVar3 = aiStack_20;
    uVar2 = thunk_FUN_004021c0(piStack_c + 1);
    thunk_FUN_004021e0(aiStack_20[2],uVar2,piVar3);
    piVar3 = extraout_EDX;
  }
  else {
    thunk_FUN_00403700(piStack_c[1],aiStack_20[4] + 1);
    piStack_c[1] = aiStack_20[0];
    piVar3 = piStack_c;
  }
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_004020cc);
  return CONCAT44(piVar3,pvStack_8);
}



void __thiscall ATL::CComCriticalSection::~CComCriticalSection(CComCriticalSection *this)

{
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void thunk_FUN_004039d0(void)

{
  thunk_FUN_00403a70("roar\n");
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void thunk_FUN_00403480(uint param_1)

{
  uint uVar1;
  
  uVar1 = thunk_FUN_00401ec0(param_1);
  thunk_FUN_00401cb0(uVar1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall thunk_FUN_00402d70(undefined4 param_1)

{
  int *piVar1;
  undefined8 uVar2;
  undefined4 uStack_10;
  undefined4 uStack_c;
  undefined4 uStack_8;
  
  uStack_10 = 0xcccccccc;
  uStack_c = 0xcccccccc;
  uStack_8 = param_1;
  thunk_FUN_00402f40(param_1);
  thunk_FUN_00401c70((int)&uStack_10 + 3);
  thunk_FUN_00403100(uStack_8);
  thunk_FUN_00402ff0(uStack_8);
  thunk_FUN_004022a0();
  piVar1 = (int *)thunk_FUN_00402ff0(uStack_8);
  thunk_FUN_00401e80((int)&uStack_10 + 3,*piVar1);
  uVar2 = thunk_FUN_00402ff0(uStack_8);
  *(undefined4 *)uVar2 = 0;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00402e00);
  return uVar2;
}



void __cdecl thunk_FUN_00403b60(undefined4 param_1)

{
  thunk_FUN_00404690(param_1);
  return;
}



undefined1 thunk_FUN_00407410(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall thunk_FUN_004034c0(void *this,char *param_1)

{
  undefined4 uVar1;
  uint uVar2;
  
  uVar1 = thunk_FUN_00403830(param_1);
  uVar2 = thunk_FUN_00401e20(uVar1);
  thunk_FUN_00403510(this,param_1,uVar2);
  return;
}



undefined4 __cdecl thunk_FUN_004022c0(undefined4 param_1)

{
  return param_1;
}



int __cdecl _atexit(_func_4879 *param_1)

{
  _onexit_t p_Var1;
  undefined4 uStack_8;
  
  p_Var1 = __onexit((_onexit_t)param_1);
  if (p_Var1 == (_onexit_t)0x0) {
    uStack_8 = -1;
  }
  else {
    uStack_8 = 0;
  }
  return uStack_8;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall thunk_FUN_00403140(int *param_1,undefined4 param_2)

{
  int *extraout_EAX;
  int *piVar1;
  undefined4 extraout_EDX;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  int *piStack_14;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408aa0;
  pvStack_10 = ExceptionList;
  uStack_1c = 0xcccccccc;
  uStack_18 = 0xcccccccc;
  ExceptionList = &pvStack_10;
  piStack_14 = param_1;
  if (*param_1 != 0) {
    std::_Lockit::_Lockit((_Lockit *)&uStack_1c,3);
    piVar1 = (int *)(*piStack_14 + 4);
    while (*piVar1 != 0) {
      *(undefined4 *)*piVar1 = 0;
      *piVar1 = *(int *)(*piVar1 + 4);
    }
    *(undefined4 *)(*piStack_14 + 4) = 0;
    std::_Lockit::~_Lockit((_Lockit *)&uStack_1c);
    param_1 = extraout_EAX;
    param_2 = extraout_EDX;
  }
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00403214);
  ExceptionList = pvStack_10;
  return CONCAT44(param_2,param_1);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00402f40(undefined4 param_1)

{
  thunk_FUN_00402ec0(param_1);
  return;
}



// WARNING: This is an inlined function

void __RTC_CheckEsp(void)

{
  int in_EAX;
  bool in_ZF;
  ulonglong in_BND0_LB;
  uint in_BND0_UB;
  void *unaff_retaddr;
  
  if (in_ZF) {
    return;
  }
  *(ulonglong *)(&stack0xfffffff8 + in_EAX) =
       (ulonglong)in_BND0_UB << 0x20 | in_BND0_LB & 0xffffffff;
  _RTC_Failure(unaff_retaddr,0);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_004028f0(int *param_1,int *param_2)

{
  int iVar1;
  code *pcVar2;
  int iVar3;
  uint uVar4;
  undefined4 uVar5;
  
  uVar5 = 0xcccccccc;
  *param_2 = *param_2 + 0x27;
  iVar1 = *(int *)(*param_1 + -4);
  if (*(int *)(*param_1 + -8) != -0x5050506) {
    iVar3 = _CrtDbgReport(2,
                          "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                          ,0x7a,0,&DAT_0040ab78,"invalid argument");
    if (iVar3 == 1) {
      pcVar2 = (code *)swi(3);
      (*pcVar2)();
      return;
    }
    invalid_parameter(L"\"invalid argument\"",L"std::_Adjust_manually_vector_aligned",
                      L"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                      ,0x7a,0,0x40296b,uVar5);
  }
  uVar5 = 8;
  uVar4 = *param_1 - iVar1;
  if ((uVar4 < 8) || (0x27 < uVar4)) {
    iVar3 = _CrtDbgReport(2,
                          "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                          ,0x84,0,&DAT_0040ab78,"invalid argument");
    if (iVar3 == 1) {
      pcVar2 = (code *)swi(3);
      (*pcVar2)();
      return;
    }
    invalid_parameter(L"\"invalid argument\"",L"std::_Adjust_manually_vector_aligned",
                      L"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                      ,0x84,0,0x4029e8,uVar5);
  }
  *param_1 = iVar1;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall ~CAssoc(int param_1)

{
  ~CPair(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall ~CPair(int param_1)

{
  ATL::CComCriticalSection::~CComCriticalSection((CComCriticalSection *)(param_1 + 4));
  return;
}



_onexit_t __cdecl __onexit(_onexit_t _Func)

{
  _func_void **pp_Var1;
  int iVar2;
  _onexit_t p_Stack_c;
  _onexit_t p_Stack_8;
  
  pp_Var1 = __crt_fast_decode_pointer<void_(__cdecl**)(void)>(DAT_0040d704);
  p_Stack_c = _Func;
  if (pp_Var1 == (_func_void **)0xffffffff) {
    iVar2 = crt_atexit(_Func);
    if (iVar2 != 0) {
      p_Stack_8 = (_onexit_t)0x0;
      p_Stack_c = p_Stack_8;
    }
  }
  else {
    iVar2 = register_onexit_function(&DAT_0040d704,_Func);
    if (iVar2 != 0) {
      p_Stack_c = (_onexit_t)0x0;
    }
  }
  return p_Stack_c;
}



int __cdecl __scrt_narrow_environment_policy::initialize_environment(void)

{
  int iVar1;
  
  iVar1 = initialize_narrow_environment();
  return iVar1;
}



undefined * FID_conflict____scrt_get_dyn_tls_dtor_callback(void)

{
  return &DAT_0040d75c;
}



void __fastcall _RTC_CheckStackVars(int param_1,int *param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  void *unaff_retaddr;
  
  iVar2 = 0;
  if (0 < *param_2) {
    iVar3 = 0;
    do {
      iVar1 = param_2[1];
      if ((*(int *)(*(int *)(iVar1 + iVar3) + param_1 + -4) != -0x33333334) ||
         (*(int *)(*(int *)(iVar1 + 4 + iVar3) + *(int *)(iVar1 + iVar3) + param_1) != -0x33333334))
      {
        _RTC_StackFailure(unaff_retaddr,*(char **)(iVar1 + 8 + iVar3));
      }
      iVar2 = iVar2 + 1;
      iVar3 = iVar3 + 0xc;
    } while (iVar2 < *param_2);
  }
  return;
}



undefined4 __fastcall thunk_FUN_004025c0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_004021e0(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  
  puVar1 = (undefined4 *)thunk_FUN_004027e0(4,param_2);
  puVar2 = (undefined4 *)thunk_FUN_004022b0(param_3);
  *puVar1 = *puVar2;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00402f70(undefined4 param_1)

{
  thunk_FUN_00402ee0(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

uint __cdecl thunk_FUN_00401cb0(uint param_1)

{
  uint uVar1;
  
  if (param_1 < 0x1000) {
    if (param_1 == 0) {
      uVar1 = 0;
    }
    else {
      uVar1 = thunk_FUN_00402ba0(param_1);
    }
  }
  else {
    uVar1 = thunk_FUN_00401d00(param_1);
  }
  return uVar1;
}



undefined4 __cdecl ___scrt_uninitialize_crt(undefined4 param_1,char param_2)

{
  undefined4 uVar1;
  undefined3 extraout_var;
  
  if ((DAT_0040d700 == '\0') || (param_2 == '\0')) {
    thunk_FUN_00407430();
    thunk_FUN_00407430();
    uVar1 = CONCAT31(extraout_var,1);
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}



void __initialize_default_precision(void)

{
  errno_t eVar1;
  
  eVar1 = _controlfp_s((uint *)0x0,0x10000,0x30000);
  if (eVar1 != 0) {
    ___scrt_fastfail();
  }
  return;
}



void __cdecl _RTC_Failure(void *param_1,int param_2)

{
  if ((uint)param_2 < 5) {
    if (*(int *)(&DAT_0040d00c + param_2 * 4) != -1) {
      failwithmessage(param_1,*(int *)(&DAT_0040d00c + param_2 * 4),param_2,
                      (&PTR_s_The_value_of_ESP_was_not_properl_0040aee4)[param_2]);
      return;
    }
  }
  else {
    failwithmessage(param_1,1,5,"Unknown Runtime Check Error\n\r");
  }
  return;
}



exception * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  thunk_FUN_004044e0(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00403790(int param_1)

{
  thunk_FUN_00403600(param_1 + 4);
  thunk_FUN_00403a70("bear: %s\n");
  return;
}



void __cdecl __scrt_file_policy::set_fmode(void)

{
  int _Mode;
  
  _Mode = thunk_FUN_00405dc0();
  _set_fmode(_Mode);
  return;
}



undefined4 * __fastcall thunk_FUN_00402610(undefined4 *param_1)

{
  *param_1 = 0;
  param_1[1] = 0;
  return param_1;
}



void __cdecl thunk_FUN_004035e0(undefined1 *param_1,undefined1 *param_2)

{
  *param_1 = *param_2;
  return;
}



undefined4 __fastcall thunk_FUN_00401c70(undefined4 param_1)

{
  return param_1;
}



int __cdecl _sprintf_s(char *_DstBuf,size_t _SizeInBytes,char *_Format,...)

{
  int iVar1;
  
  iVar1 = __vsprintf_s_l(_DstBuf,_SizeInBytes,_Format,(_locale_t)0x0,&stack0x00000010);
  return iVar1;
}



undefined1 thunk_FUN_00407420(void)

{
  return 1;
}



void ___scrt_initialize_mta(void)

{
  thunk_FUN_00406210();
  return;
}



undefined4 __cdecl thunk_FUN_00401eb0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_004018e0(int param_1,int param_2)

{
  int iVar1;
  _CTaskDialogButton **pp_Var2;
  char *pcVar3;
  undefined4 uVar4;
  _CTaskDialogButton *ap_Stack_8c [4];
  undefined4 *puStack_7c;
  undefined4 *puStack_78;
  undefined4 *puStack_74;
  undefined4 *puStack_70;
  undefined4 *puStack_6c;
  undefined4 *puStack_68;
  char cStack_61;
  undefined4 *puStack_60;
  char cStack_59;
  int *piStack_58;
  int *piStack_54;
  undefined1 auStack_50 [28];
  undefined1 auStack_34 [28];
  undefined4 *puStack_18;
  uint uStack_14;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408940;
  pvStack_10 = ExceptionList;
  pp_Var2 = ap_Stack_8c;
  for (iVar1 = 0x1f; iVar1 != 0; iVar1 = iVar1 + -1) {
    *pp_Var2 = (_CTaskDialogButton *)0xcccccccc;
    pp_Var2 = pp_Var2 + 1;
  }
  uStack_14 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  ExceptionList = &pvStack_10;
  if (1 < param_1) {
    puStack_18 = (undefined4 *)0x0;
    pcVar3 = "bear";
    puStack_78 = thunk_FUN_004023f0(auStack_34,*(char **)(param_2 + 4));
    uStack_8 = 0;
    puStack_74 = puStack_78;
    cStack_59 = thunk_FUN_00401c90(puStack_78,pcVar3);
    uStack_8 = 0xffffffff;
    FID_conflict__CAtlWinModule((int)auStack_34);
    if (cStack_59 != '\0') {
      puStack_60 = operator_new(0x20);
      if (puStack_60 == (undefined4 *)0x0) {
        puStack_7c = (undefined4 *)0x0;
      }
      else {
        *puStack_60 = 0;
        puStack_60[1] = 0;
        puStack_60[2] = 0;
        puStack_60[3] = 0;
        puStack_60[4] = 0;
        puStack_60[5] = 0;
        puStack_60[6] = 0;
        puStack_60[7] = 0;
        puStack_7c = thunk_FUN_00402540(puStack_60);
      }
      puStack_18 = puStack_7c;
      thunk_FUN_004027f0(puStack_7c + 1,"luke bear-y");
    }
    pcVar3 = "cat";
    ap_Stack_8c[2] = (_CTaskDialogButton *)thunk_FUN_004023f0(auStack_50,*(char **)(param_2 + 4));
    uStack_8 = 1;
    ap_Stack_8c[3] = ap_Stack_8c[2];
    cStack_61 = thunk_FUN_00401c90(ap_Stack_8c[2],pcVar3);
    uStack_8 = 0xffffffff;
    FID_conflict__CAtlWinModule((int)auStack_50);
    if (cStack_61 != '\0') {
      puStack_68 = operator_new(0x20);
      if (puStack_68 == (undefined4 *)0x0) {
        ap_Stack_8c[1] = (_CTaskDialogButton *)0x0;
      }
      else {
        *puStack_68 = 0;
        puStack_68[1] = 0;
        puStack_68[2] = 0;
        puStack_68[3] = 0;
        puStack_68[4] = 0;
        puStack_68[5] = 0;
        puStack_68[6] = 0;
        puStack_68[7] = 0;
        ap_Stack_8c[1] = (_CTaskDialogButton *)thunk_FUN_00402580(puStack_68);
      }
      puStack_18 = (undefined4 *)ap_Stack_8c[1];
      thunk_FUN_004027f0((undefined4 *)((int)ap_Stack_8c[1] + 4),"hurricane cat-rina");
    }
    (**(code **)*puStack_18)();
    uVar4 = 0x401aa7;
    piStack_54 = (int *)__RTDynamicCast(puStack_18,0,&Animal::RTTI_Type_Descriptor,
                                        &Bear::RTTI_Type_Descriptor,0,0x401aa7);
    if (piStack_54 != (int *)0x0) {
      (**(code **)(*piStack_54 + 4))();
      uVar4 = 0x401ae0;
    }
    piStack_58 = (int *)__RTDynamicCast(puStack_18,0,&Animal::RTTI_Type_Descriptor,
                                        &Cat::RTTI_Type_Descriptor,0,uVar4);
    if (piStack_58 != (int *)0x0) {
      (**(code **)(*piStack_58 + 4))();
    }
    if (puStack_18 != (undefined4 *)0x0) {
      puStack_70 = puStack_18;
      puStack_6c = puStack_18;
      if (puStack_18 == (undefined4 *)0x0) {
        ap_Stack_8c[0] = (_CTaskDialogButton *)0x0;
      }
      else {
        ap_Stack_8c[0] = FID_conflict__scalar_deleting_destructor_(puStack_18,1);
      }
    }
  }
  ExceptionList = pvStack_10;
  __security_check_cookie(uStack_14 ^ (uint)&stack0xfffffffc);
  return;
}



undefined * ___local_stdio_scanf_options(void)

{
  return &DAT_0040d738;
}



undefined1 thunk_FUN_00407440(void)

{
  return 1;
}



bool __fastcall thunk_FUN_00402fa0(int param_1)

{
  return 0xf < *(uint *)(param_1 + 0x18);
}



void __cdecl ___security_init_cookie(void)

{
  undefined4 uStack_8;
  
  if ((DAT_0040d004 == 0xbb40e64e) || ((DAT_0040d004 & 0xffff0000) == 0)) {
    uStack_8 = ___get_entropy();
    if (uStack_8 == 0xbb40e64e) {
      uStack_8 = 0xbb40e64f;
    }
    else if ((uStack_8 & 0xffff0000) == 0) {
      uStack_8 = (uStack_8 | 0x4711) << 0x10 | uStack_8;
    }
    DAT_0040d004 = uStack_8;
  }
  DAT_0040d000 = ~DAT_0040d004;
  return;
}



void thunk_FUN_004022a0(void)

{
  return;
}



void * __cdecl operator_new(uint param_1)

{
  void *pvVar1;
  int iVar2;
  
  while (pvVar1 = malloc(param_1), pvVar1 == (void *)0x0) {
    iVar2 = _callnewh(param_1);
    if (iVar2 == 0) {
      if (param_1 == 0xffffffff) {
        thunk_FUN_00404620();
      }
      else {
        thunk_FUN_004045f0();
      }
    }
  }
  return pvVar1;
}



undefined1 thunk_FUN_00407400(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall thunk_FUN_00403100(undefined4 param_1)

{
  undefined8 uVar1;
  
  uVar1 = thunk_FUN_00402e60(param_1);
  uVar1 = thunk_FUN_00403140((int *)uVar1,(int)((ulonglong)uVar1 >> 0x20));
  return uVar1;
}



void ___scrt_fastfail(void)

{
  code *pcVar1;
  BOOL BVar2;
  undefined4 auStack_330 [39];
  EXCEPTION_RECORD EStack_64;
  _EXCEPTION_POINTERS _Stack_14;
  LONG LStack_c;
  char cStack_6;
  undefined1 uStack_5;
  
  BVar2 = IsProcessorFeaturePresent(0x17);
  if (BVar2 != 0) {
    pcVar1 = (code *)swi(0x29);
    (*pcVar1)();
  }
  __crt_debugger_hook(3);
  memset(auStack_330,0,0x2cc);
  auStack_330[0] = 0x10001;
  memset(&EStack_64,0,0x50);
  EStack_64.ExceptionCode = 0x40000015;
  EStack_64.ExceptionFlags = 1;
  BVar2 = IsDebuggerPresent();
  cStack_6 = BVar2 == 1;
  _Stack_14.ExceptionRecord = &EStack_64;
  _Stack_14.ContextRecord = (PCONTEXT)auStack_330;
  uStack_5 = cStack_6;
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)0x0);
  LStack_c = UnhandledExceptionFilter(&_Stack_14);
  if ((LStack_c == 0) && (cStack_6 == '\0')) {
    __crt_debugger_hook(3);
  }
  return;
}



undefined4 __cdecl thunk_FUN_004021a0(undefined4 param_1)

{
  return param_1;
}



void __cdecl __scrt_initialize_type_info(void)

{
  InitializeSListHead((PSLIST_HEADER)&DAT_0040d728);
  return;
}



undefined4 thunk_FUN_00405da0(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall CTaskDialog::_CTaskDialogButton::~_CTaskDialogButton(_CTaskDialogButton *this)

{
  FID_conflict__CAtlWinModule((int)(this + 4));
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00401e30(int param_1,uint param_2)

{
  if (0xfff < param_2) {
    thunk_FUN_004028f0(&param_1,(int *)&param_2);
  }
  thunk_FUN_00403b60(param_1);
  return;
}



void __cdecl _ReadPointerNoFence(undefined4 *param_1)

{
  thunk_FUN_00406380(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void * __thiscall thunk_FUN_00403510(void *this,void *param_1,uint param_2)

{
  undefined8 uVar1;
  undefined4 uStack_14;
  void *pvStack_10;
  int iStack_c;
  void *pvStack_8;
  
  uStack_14 = 0xcccccccc;
  pvStack_10 = (void *)0xcccccccc;
  iStack_c = 0xcccccccc;
  pvStack_8 = this;
  iStack_c = thunk_FUN_00402e60(this);
  if (*(uint *)(iStack_c + 0x18) < param_2) {
    uStack_14._0_3_ = (uint3)(ushort)uStack_14;
    uVar1 = thunk_FUN_00401fb0(pvStack_8,param_2,0,param_1);
    pvStack_8 = (void *)uVar1;
  }
  else {
    pvStack_10 = (void *)thunk_FUN_00403020(iStack_c);
    *(uint *)(iStack_c + 0x14) = param_2;
    thunk_FUN_004039a0(pvStack_10,param_1,param_2);
    uStack_14 = uStack_14 & 0xffffff;
    thunk_FUN_004035e0((undefined1 *)((int)pvStack_10 + param_2),(undefined1 *)((int)&uStack_14 + 3)
                      );
  }
  return pvStack_8;
}



undefined4 __fastcall thunk_FUN_00402f20(undefined4 param_1)

{
  return param_1;
}



undefined4 __cdecl thunk_FUN_004021d0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00402e60(undefined4 param_1)

{
  thunk_FUN_00402f00(param_1);
  return;
}



undefined4 __cdecl thunk_FUN_004022b0(undefined4 param_1)

{
  return param_1;
}



uint * __cdecl thunk_FUN_00401f10(uint *param_1,uint *param_2)

{
  undefined4 uStack_c;
  
  if (*param_1 < *param_2) {
    uStack_c = param_2;
  }
  else {
    uStack_c = param_1;
  }
  return uStack_c;
}



undefined4 thunk_FUN_00403850(void)

{
  return 0x7fffffff;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_00402540(undefined4 *param_1)

{
  thunk_FUN_00402500(param_1);
  *param_1 = Bear::vftable;
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined1 __cdecl thunk_FUN_00402140(void *param_1,size_t param_2,void *param_3,size_t param_4)

{
  int iVar1;
  
  if ((param_2 == param_4) && (iVar1 = thunk_FUN_00403670(param_1,param_3,param_2), iVar1 == 0)) {
    return 1;
  }
  return 0;
}



void __fastcall thunk_FUN_004044c0(exception *param_1)

{
  std::exception::~exception(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void thunk_FUN_00403700(int param_1,uint param_2)

{
  thunk_FUN_00401e30(param_1,param_2);
  return;
}



void thunk_FUN_004045f0(void)

{
  exception aeStack_10 [12];
  
  FID_conflict_bad_cast(aeStack_10);
                    // WARNING: Subroutine does not return
  _CxxThrowException(aeStack_10,(ThrowInfo *)&DAT_0040c8e8);
}



undefined1 thunk_FUN_00407440(void)

{
  return 1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall thunk_FUN_00403870(undefined4 param_1)

{
  uint *puVar1;
  undefined4 extraout_EDX;
  uint uVar2;
  undefined4 uVar3;
  uint uStack_24;
  uint auStack_20 [7];
  
  uStack_24 = 0xcccccccc;
  auStack_20[0] = 0xcccccccc;
  auStack_20[1] = 0xcccccccc;
  auStack_20[2] = 0xcccccccc;
  auStack_20[3] = 0xcccccccc;
  auStack_20[4] = 0xcccccccc;
  auStack_20[5] = 0xcccccccc;
  auStack_20[6] = param_1;
  thunk_FUN_00402f70(param_1);
  auStack_20[4] = thunk_FUN_00403860();
  auStack_20[1] = 0x10;
  puVar1 = thunk_FUN_00401f10(auStack_20 + 4,auStack_20 + 1);
  auStack_20[2] = *puVar1;
  auStack_20[0] = auStack_20[2] - 1;
  uStack_24 = thunk_FUN_00403850();
  puVar1 = thunk_FUN_00401f60(&uStack_24,auStack_20);
  uVar2 = *puVar1;
  uVar3 = extraout_EDX;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00403908);
  return CONCAT44(uVar3,uVar2);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall thunk_FUN_00402500(undefined4 *param_1)

{
  *param_1 = Animal::vftable;
  thunk_FUN_00402490(param_1 + 1);
  return param_1;
}



char * __thiscall std::exception::what(exception *this)

{
  char *pcStack_c;
  
  if (*(int *)(this + 4) == 0) {
    pcStack_c = "Unknown exception";
  }
  else {
    pcStack_c = *(char **)(this + 4);
  }
  return pcStack_c;
}



exception * __fastcall FID_conflict_bad_cast(exception *param_1)

{
  std::exception::exception(param_1,"bad allocation",1);
  *(undefined ***)param_1 = std::bad_alloc::vftable;
  return param_1;
}



_func_void ** __cdecl __crt_fast_decode_pointer<void_(__cdecl**)(void)>(_func_void **param_1)

{
  _func_void **pp_Var1;
  
  pp_Var1 = (_func_void **)
            __crt_rotate_pointer_value((uint)param_1 ^ DAT_0040d004,DAT_0040d004 % 0x20);
  return pp_Var1;
}



uint * __cdecl thunk_FUN_00401f60(uint *param_1,uint *param_2)

{
  undefined4 uStack_c;
  
  if (*param_2 < *param_1) {
    uStack_c = param_2;
  }
  else {
    uStack_c = param_1;
  }
  return uStack_c;
}



void entry(void)

{
  __scrt_common_main();
  return;
}



int __cdecl __scrt_narrow_argv_policy::configure_argv(void)

{
  undefined4 uVar1;
  int iVar2;
  
  uVar1 = thunk_FUN_00405da0();
  iVar2 = configure_narrow_argv(uVar1);
  return iVar2;
}



void thunk_FUN_004061f0(void)

{
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)&LAB_00401195);
  return;
}



void __thiscall std::exception::~exception(exception *this)

{
  *(undefined ***)this = vftable;
  __std_exception_destroy(this + 4);
  return;
}



void __cdecl __scrt_main_policy::set_app_type(void)

{
  ::set_app_type(1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

_CTaskDialogButton * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  CTaskDialog::_CTaskDialogButton::~_CTaskDialogButton(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



undefined4 thunk_FUN_00406210(void)

{
  return 0;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl thunk_FUN_00402230(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  
  puVar2 = (undefined4 *)thunk_FUN_004027e0(8,param_2);
  puVar3 = (undefined4 *)thunk_FUN_004022c0(param_3);
  uVar1 = puVar3[1];
  *puVar2 = *puVar3;
  puVar2[1] = uVar1;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall thunk_FUN_00402ff0(undefined4 param_1)

{
  thunk_FUN_00402e60(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall thunk_FUN_00402cc0(void *this,char *param_1)

{
  int iVar1;
  size_t sVar2;
  void *pvVar3;
  size_t sVar4;
  void *pvStack_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408a70;
  pvStack_10 = ExceptionList;
  ExceptionList = &pvStack_10;
  iVar1 = thunk_FUN_00402e90(this);
  sVar2 = thunk_FUN_00403830(param_1);
  sVar4 = *(size_t *)(iVar1 + 0x14);
  pvVar3 = (void *)thunk_FUN_00403090(iVar1);
  thunk_FUN_00402140(pvVar3,sVar4,param_1,sVar2);
  ExceptionList = pvStack_10;
  return;
}



void ___scrt_initialize_default_local_stdio_options(void)

{
  uint *puVar1;
  
  puVar1 = (uint *)___local_stdio_scanf_options();
  *puVar1 = *puVar1 | 4;
  puVar1[1] = puVar1[1];
  puVar1 = (uint *)___local_stdio_scanf_options();
  *puVar1 = *puVar1 | 2;
  puVar1[1] = puVar1[1];
  return;
}



// WARNING: Unknown calling convention -- yet parameter storage is locked

_TEB * _NtCurrentTeb(void)

{
  return (_TEB *)&ExceptionList;
}



int ___scrt_acquire_startup_lock(void)

{
  int iVar1;
  bool bVar2;
  uint3 extraout_var;
  int iVar3;
  _TEB *p_Var4;
  int iVar5;
  
  bVar2 = ___scrt_is_ucrt_dll_in_use();
  if (CONCAT31(extraout_var,bVar2) == 0) {
    iVar3 = (uint)extraout_var << 8;
  }
  else {
    p_Var4 = _NtCurrentTeb();
    iVar3 = *(int *)(p_Var4 + 4);
    do {
      iVar5 = 0;
      LOCK();
      iVar1 = iVar3;
      if (DAT_0040d6fc != 0) {
        iVar5 = DAT_0040d6fc;
        iVar1 = DAT_0040d6fc;
      }
      DAT_0040d6fc = iVar1;
      UNLOCK();
      if (iVar5 == 0) {
        return 0;
      }
    } while (iVar3 != iVar5);
    iVar3 = CONCAT31((int3)((uint)iVar3 >> 8),1);
  }
  return iVar3;
}



exception * __thiscall thunk_FUN_00404370(void *this,exception *param_1)

{
  std::exception::exception(this,param_1);
  *(undefined ***)this = std::bad_alloc::vftable;
  return this;
}



int __cdecl
_RTC_GetSrcLine(uchar *param_1,wchar_t *param_2,ulong param_3,int *param_4,wchar_t *param_5,
               ulong param_6)

{
  code *pcVar1;
  char cVar2;
  SIZE_T SVar3;
  int iVar4;
  uint uVar5;
  FARPROC pFVar6;
  HANDLE pvVar7;
  int *piVar8;
  uint *puVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  undefined4 *puVar13;
  uint *puVar14;
  ushort *puVar15;
  ulong *puVar16;
  DWORD DVar17;
  wchar_t *pwVar18;
  undefined4 uVar19;
  int **ppiVar20;
  undefined4 uVar21;
  undefined4 uVar22;
  undefined1 *puVar23;
  undefined4 uVar24;
  undefined4 uVar25;
  undefined *puVar26;
  _MEMORY_BASIC_INFORMATION _Stack_50;
  undefined1 auStack_34 [4];
  undefined4 uStack_30;
  int iStack_2c;
  int iStack_28;
  int *piStack_24;
  uint uStack_20;
  int *piStack_1c;
  int *piStack_18;
  uint uStack_14;
  uint *puStack_10;
  int *piStack_c;
  ushort auStack_8 [2];
  
  *param_4 = 0;
  *param_2 = L'\0';
  SVar3 = VirtualQuery(param_1 + -1,&_Stack_50,0x1c);
  if ((((SVar3 == 0) ||
       (iVar4 = __vcrt_GetModuleFileNameW(_Stack_50.AllocationBase,param_5,param_6), iVar4 == 0)) ||
      (*(short *)_Stack_50.AllocationBase != 0x5a4d)) ||
     ((*(int *)((int)_Stack_50.AllocationBase + 0x3c) < 1 ||
      (piVar8 = (int *)(*(int *)((int)_Stack_50.AllocationBase + 0x3c) +
                       (int)_Stack_50.AllocationBase), *piVar8 != 0x4550)))) {
    return 0;
  }
  uVar11 = (int)(param_1 + -1) - (int)_Stack_50.AllocationBase;
  uVar12 = (uint)*(ushort *)((int)piVar8 + 6);
  uVar10 = 0;
  uVar5 = 0;
  if (uVar12 != 0) {
    puVar9 = (uint *)((int)piVar8 + *(ushort *)(piVar8 + 5) + 0x20);
    do {
      if ((puVar9[1] <= uVar11) && (uVar10 = uVar11 - puVar9[1], uVar11 < *puVar9)) break;
      uVar5 = uVar5 + 1;
      puVar9 = puVar9 + 10;
    } while (uVar5 < uVar12);
  }
  if (uVar5 == uVar12) {
    return 0;
  }
  puStack_10 = (uint *)(uVar5 + 1);
  if (DAT_0040d74d == '\0') {
    if (DAT_0040d748 != (HMODULE)0x0) {
      return 0;
    }
    DAT_0040d748 = GetPdbDll();
    if (DAT_0040d748 == (HINSTANCE__ *)0x0) {
      return 0;
    }
    DAT_0040d74d = '\x01';
  }
  pFVar6 = GetProcAddress(DAT_0040d748,"PDBOpenValidate5");
  if (pFVar6 == (FARPROC)0x0) {
    return 0;
  }
  ppiVar20 = &piStack_1c;
  uVar25 = 0;
  uVar24 = 0;
  puVar23 = auStack_34;
  uVar22 = 0;
  uVar21 = 0;
  uVar19 = 0;
  pwVar18 = param_5;
  guard_check_icall();
  iVar4 = (*pFVar6)(pwVar18,uVar19,uVar21,uVar22,puVar23,uVar24,uVar25,ppiVar20);
  if (iVar4 == 0) {
    return 0;
  }
  iStack_28 = 0;
  pcVar1 = *(code **)*piStack_1c;
  guard_check_icall();
  iVar4 = (*pcVar1)();
  if (iVar4 != 0x1329141) goto LAB_00406c2e;
  pcVar1 = *(code **)(*piStack_1c + 0x1c);
  ppiVar20 = &piStack_24;
  puVar26 = &DAT_0040b890;
  uVar19 = 0;
  guard_check_icall();
  iVar4 = (*pcVar1)(uVar19,puVar26,ppiVar20);
  if (iVar4 == 0) goto LAB_00406c2e;
  uVar22 = 0;
  uVar21 = 0;
  uVar19 = 0;
  pcVar1 = *(code **)(*piStack_24 + 0x20);
  ppiVar20 = &piStack_18;
  puVar9 = puStack_10;
  uVar5 = uVar10;
  guard_check_icall();
  iVar4 = (*pcVar1)(puVar9,uVar5,ppiVar20,uVar19,uVar21,uVar22);
  if (iVar4 != 0) {
    piStack_c = (int *)0x0;
    pcVar1 = *(code **)(*piStack_18 + 0x68);
    ppiVar20 = &piStack_c;
    guard_check_icall();
    cVar2 = (*pcVar1)(ppiVar20);
    if ((cVar2 != '\0') && (piStack_c != (int *)0x0)) {
      pcVar1 = *(code **)(*piStack_c + 8);
      guard_check_icall();
      iVar4 = (*pcVar1)();
      puVar9 = (uint *)0x0;
      if (iVar4 != 0) {
        do {
          uVar21 = 0;
          pcVar1 = *(code **)(*piStack_c + 0xc);
          puVar9 = &uStack_14;
          piVar8 = &iStack_2c;
          puVar15 = auStack_8;
          puVar14 = &uStack_20;
          uVar19 = 0;
          guard_check_icall();
          cVar2 = (*pcVar1)(uVar19,puVar14,puVar15,piVar8,puVar9,uVar21);
          if (cVar2 == '\0') goto LAB_00406bf3;
          if ((((uint *)(uint)auStack_8[0] == puStack_10) && (uStack_20 <= uVar10)) &&
             (uVar10 < iStack_2c + uStack_20)) {
            if ((uStack_14 == 0) || (0x1ffffffe < uStack_14)) goto LAB_00406bf3;
            SVar3 = uStack_14 << 3;
            DVar17 = 0;
            pvVar7 = GetProcessHeap();
            puVar9 = HeapAlloc(pvVar7,DVar17,SVar3);
            puStack_10 = puVar9;
            if (puVar9 == (uint *)0x0) goto LAB_00406bf3;
            puVar14 = &uStack_14;
            puVar13 = &uStack_30;
            uVar22 = 0;
            uVar21 = 0;
            uVar19 = 0;
            pcVar1 = *(code **)(*piStack_c + 0xc);
            guard_check_icall();
            cVar2 = (*pcVar1)(puVar13,uVar19,uVar21,uVar22,puVar14,puVar9);
            puVar9 = puStack_10;
            if ((cVar2 == '\0') || (uVar10 - uStack_20 < *puStack_10)) goto LAB_00406be3;
            uVar5 = 1;
            if (uStack_14 < 2) goto LAB_00406cca;
            goto LAB_00406cc0;
          }
          pcVar1 = *(code **)(*piStack_c + 8);
          guard_check_icall();
          iVar4 = (*pcVar1)();
        } while (iVar4 != 0);
        puVar9 = (uint *)0x0;
      }
      goto LAB_00406be3;
    }
    goto LAB_00406c06;
  }
  goto LAB_00406c1a;
  while (uVar5 = uVar5 + 1, uVar5 < uStack_14) {
LAB_00406cc0:
    if (uVar10 - uStack_20 < puStack_10[uVar5 * 2]) break;
  }
LAB_00406cca:
  uVar22 = 0;
  uVar21 = 0;
  *param_4 = puStack_10[uVar5 * 2 + -1] & 0xffffff;
  uVar19 = 0;
  pcVar1 = *(code **)(*piStack_18 + 0x70);
  puVar16 = &param_3;
  guard_check_icall();
  cVar2 = (*pcVar1)(uStack_30,param_2,puVar16,uVar19,uVar21,uVar22);
  puVar9 = puStack_10;
  if (cVar2 != '\0') {
    iStack_28 = 1;
  }
LAB_00406be3:
  DVar17 = 0;
  pvVar7 = GetProcessHeap();
  HeapFree(pvVar7,DVar17,puVar9);
LAB_00406bf3:
  pcVar1 = *(code **)*piStack_c;
  guard_check_icall();
  (*pcVar1)();
LAB_00406c06:
  pcVar1 = *(code **)(*piStack_18 + 0x40);
  guard_check_icall();
  (*pcVar1)();
LAB_00406c1a:
  pcVar1 = *(code **)(*piStack_24 + 0x38);
  guard_check_icall();
  (*pcVar1)();
LAB_00406c2e:
  pcVar1 = *(code **)(*piStack_1c + 0x2c);
  guard_check_icall();
  (*pcVar1)();
  return iStack_28;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_004018e0(int param_1,int param_2)

{
  int iVar1;
  _CTaskDialogButton **pp_Var2;
  char *pcVar3;
  undefined4 uVar4;
  _CTaskDialogButton *local_8c [4];
  undefined4 *local_7c;
  undefined4 *local_78;
  undefined4 *local_74;
  undefined4 *local_70;
  undefined4 *local_6c;
  undefined4 *local_68;
  char local_61;
  undefined4 *local_60;
  char local_59;
  int *local_58;
  int *local_54;
  undefined1 local_50 [28];
  undefined1 local_34 [28];
  undefined4 *local_18;
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_00408940;
  local_10 = ExceptionList;
  pp_Var2 = local_8c;
  for (iVar1 = 0x1f; iVar1 != 0; iVar1 = iVar1 + -1) {
    *pp_Var2 = (_CTaskDialogButton *)0xcccccccc;
    pp_Var2 = pp_Var2 + 1;
  }
  local_14 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  if (1 < param_1) {
    local_18 = (undefined4 *)0x0;
    pcVar3 = "bear";
    local_78 = thunk_FUN_004023f0(local_34,*(char **)(param_2 + 4));
    local_8 = 0;
    local_74 = local_78;
    local_59 = thunk_FUN_00401c90(local_78,pcVar3);
    local_8 = 0xffffffff;
    FID_conflict__CAtlWinModule((int)local_34);
    if (local_59 != '\0') {
      local_60 = operator_new(0x20);
      if (local_60 == (undefined4 *)0x0) {
        local_7c = (undefined4 *)0x0;
      }
      else {
        *local_60 = 0;
        local_60[1] = 0;
        local_60[2] = 0;
        local_60[3] = 0;
        local_60[4] = 0;
        local_60[5] = 0;
        local_60[6] = 0;
        local_60[7] = 0;
        local_7c = thunk_FUN_00402540(local_60);
      }
      local_18 = local_7c;
      thunk_FUN_004027f0(local_7c + 1,"luke bear-y");
    }
    pcVar3 = "cat";
    local_8c[2] = (_CTaskDialogButton *)thunk_FUN_004023f0(local_50,*(char **)(param_2 + 4));
    local_8 = 1;
    local_8c[3] = local_8c[2];
    local_61 = thunk_FUN_00401c90(local_8c[2],pcVar3);
    local_8 = 0xffffffff;
    FID_conflict__CAtlWinModule((int)local_50);
    if (local_61 != '\0') {
      local_68 = operator_new(0x20);
      if (local_68 == (undefined4 *)0x0) {
        local_8c[1] = (_CTaskDialogButton *)0x0;
      }
      else {
        *local_68 = 0;
        local_68[1] = 0;
        local_68[2] = 0;
        local_68[3] = 0;
        local_68[4] = 0;
        local_68[5] = 0;
        local_68[6] = 0;
        local_68[7] = 0;
        local_8c[1] = (_CTaskDialogButton *)thunk_FUN_00402580(local_68);
      }
      local_18 = (undefined4 *)local_8c[1];
      thunk_FUN_004027f0((undefined4 *)((int)local_8c[1] + 4),"hurricane cat-rina");
    }
    (**(code **)*local_18)();
    uVar4 = 0x401aa7;
    local_54 = (int *)__RTDynamicCast(local_18,0,&Animal::RTTI_Type_Descriptor,
                                      &Bear::RTTI_Type_Descriptor,0,0x401aa7);
    if (local_54 != (int *)0x0) {
      (**(code **)(*local_54 + 4))();
      uVar4 = 0x401ae0;
    }
    local_58 = (int *)__RTDynamicCast(local_18,0,&Animal::RTTI_Type_Descriptor,
                                      &Cat::RTTI_Type_Descriptor,0,uVar4);
    if (local_58 != (int *)0x0) {
      (**(code **)(*local_58 + 4))();
    }
    if (local_18 != (undefined4 *)0x0) {
      local_70 = local_18;
      local_6c = local_18;
      if (local_18 == (undefined4 *)0x0) {
        local_8c[0] = (_CTaskDialogButton *)0x0;
      }
      else {
        local_8c[0] = FID_conflict__scalar_deleting_destructor_(local_18,1);
      }
    }
  }
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_00401c30(undefined4 *param_1)

{
  thunk_FUN_004023d0(param_1);
  thunk_FUN_00402370(param_1);
  return param_1;
}



undefined4 __fastcall FUN_00401c70(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00401c90(void *param_1,char *param_2)

{
  thunk_FUN_00402cc0(param_1,param_2);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

uint __cdecl FUN_00401cb0(uint param_1)

{
  uint uVar1;
  
  if (param_1 < 0x1000) {
    if (param_1 == 0) {
      uVar1 = 0;
    }
    else {
      uVar1 = thunk_FUN_00402ba0(param_1);
    }
  }
  else {
    uVar1 = thunk_FUN_00401d00(param_1);
  }
  return uVar1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

uint __cdecl FUN_00401d00(uint param_1)

{
  code *pcVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint local_8;
  
  local_8 = param_1 + 0x27;
  if (local_8 <= param_1) {
    local_8 = 0xffffffff;
  }
  iVar2 = thunk_FUN_00402ba0(local_8);
  if (iVar2 == 0) {
    iVar3 = _CrtDbgReport(2,
                          "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                          ,0x65,0,&DAT_0040ab78,"invalid argument");
    if (iVar3 == 1) {
      pcVar1 = (code *)swi(3);
      uVar4 = (*pcVar1)();
      return uVar4;
    }
    invalid_parameter(L"\"invalid argument\"",L"std::_Allocate_manually_vector_aligned",
                      L"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                      ,0x65,0,0x401d72);
  }
  uVar4 = iVar2 + 0x27U & 0xffffffe0;
  *(int *)(uVar4 - 4) = iVar2;
  *(undefined4 *)(uVar4 - 8) = 0xfafafafa;
  return uVar4;
}



undefined4 __cdecl FUN_00401e20(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00401e30(int param_1,uint param_2)

{
  if (0xfff < param_2) {
    thunk_FUN_004028f0(&param_1,(int *)&param_2);
  }
  thunk_FUN_00403b60(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00401e80(undefined4 param_1,int param_2)

{
  thunk_FUN_004036d0(param_1,param_2,1);
  return;
}



undefined4 __cdecl FUN_00401eb0(undefined4 param_1)

{
  return param_1;
}



int __cdecl FUN_00401ec0(uint param_1)

{
  undefined4 local_c;
  
  local_c = param_1 << 3;
  if (0x1fffffff < param_1) {
    local_c = -1;
  }
  return local_c;
}



uint * __cdecl FUN_00401f10(uint *param_1,uint *param_2)

{
  undefined4 local_c;
  
  if (*param_1 < *param_2) {
    local_c = param_2;
  }
  else {
    local_c = param_1;
  }
  return local_c;
}



uint * __cdecl FUN_00401f60(uint *param_1,uint *param_2)

{
  undefined4 local_c;
  
  if (*param_2 < *param_1) {
    local_c = param_2;
  }
  else {
    local_c = param_1;
  }
  return local_c;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __thiscall FUN_00401fb0(void *this,uint param_1,undefined4 param_2,void *param_3)

{
  void *pvVar1;
  undefined4 uVar2;
  int *extraout_EDX;
  int *piVar3;
  undefined8 uVar4;
  int local_20 [5];
  int *local_c;
  void *local_8;
  
  local_20[0] = -0x33333334;
  local_20[1] = 0xcccccccc;
  local_20[2] = 0xcccccccc;
  local_20[3] = 0xcccccccc;
  local_20[4] = 0xcccccccc;
  local_c = (int *)0xcccccccc;
  local_8 = this;
  uVar4 = thunk_FUN_00403870(this);
  if ((uint)uVar4 < param_1) {
    thunk_FUN_00403400();
  }
  local_c = (int *)thunk_FUN_00402e60(local_8);
  local_20[4] = local_c[6];
  uVar4 = thunk_FUN_00402bc0(local_8,param_1);
  local_20[3] = (int)uVar4;
  local_20[2] = thunk_FUN_00402f40(local_8);
  uVar4 = thunk_FUN_00403440(local_20[3] + 1);
  local_20[0] = (int)uVar4;
  thunk_FUN_00403140(local_c,(int)((ulonglong)uVar4 >> 0x20));
  local_c[5] = param_1;
  local_c[6] = local_20[3];
  pvVar1 = (void *)thunk_FUN_004021a0(local_20[0]);
  thunk_FUN_00402830(pvVar1,param_1,param_3);
  if ((uint)local_20[4] < 0x10) {
    piVar3 = local_20;
    uVar2 = thunk_FUN_004021c0(local_c + 1);
    thunk_FUN_004021e0(local_20[2],uVar2,piVar3);
    piVar3 = extraout_EDX;
  }
  else {
    thunk_FUN_00403700(local_c[1],local_20[4] + 1);
    local_c[1] = local_20[0];
    piVar3 = local_c;
  }
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_004020cc);
  return CONCAT44(piVar3,local_8);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined1 __cdecl FUN_00402140(void *param_1,size_t param_2,void *param_3,size_t param_4)

{
  int iVar1;
  
  if ((param_2 == param_4) && (iVar1 = thunk_FUN_00403670(param_1,param_3,param_2), iVar1 == 0)) {
    return 1;
  }
  return 0;
}



undefined4 __cdecl FUN_004021a0(undefined4 param_1)

{
  return param_1;
}



undefined4 __cdecl FUN_004021b0(undefined4 param_1)

{
  return param_1;
}



undefined4 __cdecl FUN_004021c0(undefined4 param_1)

{
  return param_1;
}



undefined4 __cdecl FUN_004021d0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_004021e0(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  
  puVar1 = (undefined4 *)thunk_FUN_004027e0(4,param_2);
  puVar2 = (undefined4 *)thunk_FUN_004022b0(param_3);
  *puVar1 = *puVar2;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00402230(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  
  puVar2 = (undefined4 *)thunk_FUN_004027e0(8,param_2);
  puVar3 = (undefined4 *)thunk_FUN_004022c0(param_3);
  uVar1 = puVar3[1];
  *puVar2 = *puVar3;
  puVar2[1] = uVar1;
  return;
}



void FUN_00402290(void)

{
  return;
}



void FUN_004022a0(void)

{
  return;
}



undefined4 __cdecl FUN_004022b0(undefined4 param_1)

{
  return param_1;
}



undefined4 __cdecl FUN_004022c0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_004022d0(undefined4 *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_00408988;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  thunk_FUN_00401c30(param_1);
  local_8 = 0;
  thunk_FUN_00402a90(param_1);
  ExceptionList = local_10;
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_00402370(undefined4 *param_1)

{
  thunk_FUN_004025e0(param_1);
  thunk_FUN_004025c0(param_1 + 1);
  param_1[5] = 0;
  param_1[6] = 0;
  return param_1;
}



undefined4 __fastcall FUN_004023d0(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __thiscall FUN_004023f0(void *this,char *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_004089b8;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  thunk_FUN_004022d0(this);
  local_8 = 0;
  thunk_FUN_00403370(this);
  thunk_FUN_004034c0(this,param_1);
  ExceptionList = local_10;
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_00402490(undefined4 *param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_004089e0;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  thunk_FUN_004022d0(param_1);
  thunk_FUN_00403370(param_1);
  ExceptionList = local_10;
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_00402500(undefined4 *param_1)

{
  *param_1 = Animal::vftable;
  thunk_FUN_00402490(param_1 + 1);
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_00402540(undefined4 *param_1)

{
  thunk_FUN_00402500(param_1);
  *param_1 = Bear::vftable;
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 * __fastcall FUN_00402580(undefined4 *param_1)

{
  thunk_FUN_00402500(param_1);
  *param_1 = Cat::vftable;
  return param_1;
}



undefined4 __fastcall FUN_004025c0(undefined4 param_1)

{
  return param_1;
}



undefined4 * __fastcall FUN_004025e0(undefined4 *param_1)

{
  *param_1 = 0;
  return param_1;
}



undefined4 * __fastcall FUN_00402610(undefined4 *param_1)

{
  *param_1 = 0;
  param_1[1] = 0;
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp
// Library Function - Multiple Matches With Same Base Name
//  public: __thiscall CMap<unsigned long,unsigned long,class ATL::CStringT<char,class
// StrTraitMFC<char,class ATL::ChTraitsCRT<char> > >,char const *>::CAssoc::~CAssoc(void)
//  public: __thiscall CMap<unsigned long,unsigned long,class ATL::CStringT<wchar_t,class
// StrTraitMFC<wchar_t,class ATL::ChTraitsCRT<wchar_t> > >,wchar_t const *>::CAssoc::~CAssoc(void)
//  public: __thiscall CMap<class CDocument *,class CDocument *,class ATL::CStringT<char,class
// StrTraitMFC<char,class ATL::ChTraitsCRT<char> > >,char const *>::CAssoc::~CAssoc(void)
//  public: __thiscall CMap<class CDocument *,class CDocument *,class ATL::CStringT<wchar_t,class
// StrTraitMFC<wchar_t,class ATL::ChTraitsCRT<wchar_t> > >,wchar_t const *>::CAssoc::~CAssoc(void)
// 
// Libraries: Visual Studio 2012 Debug, Visual Studio 2015 Debug

void __fastcall ~CAssoc(int param_1)

{
  ~CPair(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp
// Library Function - Multiple Matches With Different Base Names
//  public: __thiscall ATL::CAtlComModule::~CAtlComModule(void)
//  public: __thiscall ATL::CAtlWinModule::~CAtlWinModule(void)
//  public: __thiscall CPaneContainerGC::~CPaneContainerGC(void)
// 
// Library: Visual Studio 2015 Debug

void __fastcall FID_conflict__CAtlWinModule(int param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408a10;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  thunk_FUN_00402d70(param_1);
  ~CAssoc(param_1);
  ExceptionList = local_10;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp
// Library Function - Multiple Matches With Same Base Name
//  public: __thiscall CMap<unsigned long,unsigned long,class ATL::CStringT<char,class
// StrTraitMFC<char,class ATL::ChTraitsCRT<char> > >,char const *>::CPair::~CPair(void)
//  public: __thiscall CMap<unsigned long,unsigned long,class ATL::CStringT<wchar_t,class
// StrTraitMFC<wchar_t,class ATL::ChTraitsCRT<wchar_t> > >,wchar_t const *>::CPair::~CPair(void)
//  public: __thiscall CMap<class CDocument *,class CDocument *,class ATL::CStringT<char,class
// StrTraitMFC<char,class ATL::ChTraitsCRT<char> > >,char const *>::CPair::~CPair(void)
//  public: __thiscall CMap<class CDocument *,class CDocument *,class ATL::CStringT<wchar_t,class
// StrTraitMFC<wchar_t,class ATL::ChTraitsCRT<wchar_t> > >,wchar_t const *>::CPair::~CPair(void)
// 
// Libraries: Visual Studio 2012 Debug, Visual Studio 2015 Debug

void __fastcall ~CPair(int param_1)

{
  ATL::CComCriticalSection::~CComCriticalSection((CComCriticalSection *)(param_1 + 4));
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp
// Library Function - Multiple Matches With Different Base Names
//  public: __thiscall ATL::CAtlComModule::~CAtlComModule(void)
//  public: __thiscall ATL::CAtlWinModule::~CAtlWinModule(void)
//  public: __thiscall CPaneContainerGC::~CPaneContainerGC(void)
// 
// Library: Visual Studio 2015 Debug

void __fastcall FID_conflict__CAtlWinModule(int param_1)

{
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408a40;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  thunk_FUN_00403270(param_1);
  FID_conflict__CAtlWinModule(param_1);
  ExceptionList = local_10;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp
// Library Function - Single Match
//  public: __thiscall CTaskDialog::_CTaskDialogButton::~_CTaskDialogButton(void)
// 
// Library: Visual Studio 2015 Debug

void __thiscall CTaskDialog::_CTaskDialogButton::~_CTaskDialogButton(_CTaskDialogButton *this)

{
  FID_conflict__CAtlWinModule((int)(this + 4));
  return;
}



// Library Function - Single Match
//  public: __thiscall ATL::CComCriticalSection::~CComCriticalSection(void)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2019 Debug, Visual Studio 2019 Release

void __thiscall ATL::CComCriticalSection::~CComCriticalSection(CComCriticalSection *this)

{
  return;
}



undefined4 __cdecl FUN_004027e0(undefined4 param_1,undefined4 param_2)

{
  return param_2;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall FUN_004027f0(void *this,char *param_1)

{
  thunk_FUN_004034c0(this,param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void FUN_00402830(void *param_1,size_t param_2,void *param_3)

{
  undefined4 local_c;
  
  local_c = 0xcccccccc;
  thunk_FUN_004036a0(param_1,param_3,param_2);
  local_c = local_c & 0xffffff;
  thunk_FUN_004035e0((undefined1 *)((int)param_1 + param_2),(undefined1 *)((int)&local_c + 3));
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp
// Library Function - Multiple Matches With Different Base Names
//  public: void * __thiscall AFX_AUTOHIDE_DOCKSITE_SAVE_INFO::`scalar deleting destructor'(unsigned
// int)
//  public: void * __thiscall CControlBarInfo::`scalar deleting destructor'(unsigned int)
//  public: void * __thiscall CTaskDialog::_CTaskDialogButton::`scalar deleting destructor'(unsigned
// int)
// 
// Library: Visual Studio 2015 Debug

_CTaskDialogButton * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  CTaskDialog::_CTaskDialogButton::~_CTaskDialogButton(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_004028f0(int *param_1,int *param_2)

{
  int iVar1;
  code *pcVar2;
  int iVar3;
  uint uVar4;
  undefined4 uVar5;
  
  uVar5 = 0xcccccccc;
  *param_2 = *param_2 + 0x27;
  iVar1 = *(int *)(*param_1 + -4);
  if (*(int *)(*param_1 + -8) != -0x5050506) {
    iVar3 = _CrtDbgReport(2,
                          "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                          ,0x7a,0,&DAT_0040ab78,"invalid argument");
    if (iVar3 == 1) {
      pcVar2 = (code *)swi(3);
      (*pcVar2)();
      return;
    }
    invalid_parameter(L"\"invalid argument\"",L"std::_Adjust_manually_vector_aligned",
                      L"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                      ,0x7a,0,0x40296b,uVar5);
  }
  uVar5 = 8;
  uVar4 = *param_1 - iVar1;
  if ((uVar4 < 8) || (0x27 < uVar4)) {
    iVar3 = _CrtDbgReport(2,
                          "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                          ,0x84,0,&DAT_0040ab78,"invalid argument");
    if (iVar3 == 1) {
      pcVar2 = (code *)swi(3);
      (*pcVar2)();
      return;
    }
    invalid_parameter(L"\"invalid argument\"",L"std::_Adjust_manually_vector_aligned",
                      L"C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\WDExpress\\VC\\Tools\\MSVC\\14.16.27023\\include\\xmemory0"
                      ,0x84,0,0x4029e8,uVar5);
  }
  *param_1 = iVar1;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall FUN_00402a90(undefined4 param_1)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  
  local_1c = 0xcccccccc;
  local_18 = 0xcccccccc;
  local_14 = 0xcccccccc;
  local_10 = 0xcccccccc;
  local_c = 0xcccccccc;
  local_8 = param_1;
  thunk_FUN_00402f40(param_1);
  thunk_FUN_00401c70((int)&local_10 + 3);
  uVar1 = thunk_FUN_00403480(1);
  uVar1 = thunk_FUN_004021b0(uVar1);
  puVar2 = (undefined4 *)thunk_FUN_00402ff0(local_8);
  *puVar2 = uVar1;
  puVar2 = thunk_FUN_00402610(&local_1c);
  puVar3 = (undefined4 *)thunk_FUN_00402ff0(local_8);
  thunk_FUN_00402230((int)&local_10 + 3,*puVar3,puVar2);
  uVar1 = thunk_FUN_00402e60(local_8);
  uVar1 = thunk_FUN_004021d0(uVar1);
  puVar3 = (undefined4 *)thunk_FUN_00402ff0(local_8);
  puVar2 = (undefined4 *)*puVar3;
  *puVar2 = uVar1;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00402b40);
  return CONCAT44(puVar2,puVar3);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00402ba0(uint param_1)

{
  operator_new(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __thiscall FUN_00402bc0(void *this,uint param_1)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  undefined4 extraout_EDX;
  undefined4 uVar4;
  undefined8 uVar5;
  uint local_24;
  uint local_20;
  undefined4 local_1c;
  uint local_18 [4];
  void *local_8;
  
  local_24 = 0xcccccccc;
  local_20 = 0xcccccccc;
  local_1c = 0xcccccccc;
  local_18[0] = 0xcccccccc;
  local_18[1] = 0xcccccccc;
  local_18[2] = 0xcccccccc;
  local_18[3] = 0xcccccccc;
  local_8 = this;
  uVar5 = thunk_FUN_00403870(this);
  local_18[3] = (uint)uVar5;
  uVar5 = thunk_FUN_00402e90(local_8);
  local_18[2] = (uint)uVar5;
  local_18[0] = param_1 | 0xf;
  uVar2 = local_18[3];
  if (local_18[0] <= local_18[3]) {
    local_20 = *(uint *)(local_18[2] + 0x18);
    uVar3 = local_18[3] - (local_20 >> 1);
    uVar5 = CONCAT44(uVar3,local_18[2]);
    if (local_20 <= uVar3) {
      local_24 = (local_20 >> 1) + local_20;
      puVar1 = thunk_FUN_00401f10(local_18,&local_24);
      uVar5 = CONCAT44(extraout_EDX,local_18[2]);
      uVar2 = *puVar1;
    }
  }
  uVar4 = (undefined4)((ulonglong)uVar5 >> 0x20);
  local_18[2] = (uint)uVar5;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00402c70);
  return CONCAT44(uVar4,uVar2);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall FUN_00402cc0(void *this,char *param_1)

{
  int iVar1;
  size_t sVar2;
  void *pvVar3;
  size_t sVar4;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408a70;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  iVar1 = thunk_FUN_00402e90(this);
  sVar2 = thunk_FUN_00403830(param_1);
  sVar4 = *(size_t *)(iVar1 + 0x14);
  pvVar3 = (void *)thunk_FUN_00403090(iVar1);
  thunk_FUN_00402140(pvVar3,sVar4,param_1,sVar2);
  ExceptionList = local_10;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall FUN_00402d70(undefined4 param_1)

{
  int *piVar1;
  undefined8 uVar2;
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  
  local_10 = 0xcccccccc;
  local_c = 0xcccccccc;
  local_8 = param_1;
  thunk_FUN_00402f40(param_1);
  thunk_FUN_00401c70((int)&local_10 + 3);
  thunk_FUN_00403100(local_8);
  thunk_FUN_00402ff0(local_8);
  thunk_FUN_004022a0();
  piVar1 = (int *)thunk_FUN_00402ff0(local_8);
  thunk_FUN_00401e80((int)&local_10 + 3,*piVar1);
  uVar2 = thunk_FUN_00402ff0(local_8);
  *(undefined4 *)uVar2 = 0;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00402e00);
  return uVar2;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00402e60(undefined4 param_1)

{
  thunk_FUN_00402f00(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00402e90(undefined4 param_1)

{
  thunk_FUN_00402f20(param_1);
  return;
}



undefined4 __fastcall FUN_00402ec0(undefined4 param_1)

{
  return param_1;
}



undefined4 __fastcall FUN_00402ee0(undefined4 param_1)

{
  return param_1;
}



undefined4 __fastcall FUN_00402f00(undefined4 param_1)

{
  return param_1;
}



undefined4 __fastcall FUN_00402f20(undefined4 param_1)

{
  return param_1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00402f40(undefined4 param_1)

{
  thunk_FUN_00402ec0(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00402f70(undefined4 param_1)

{
  thunk_FUN_00402ee0(param_1);
  return;
}



bool __fastcall FUN_00402fa0(int param_1)

{
  return 0xf < *(uint *)(param_1 + 0x18);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00402ff0(undefined4 param_1)

{
  thunk_FUN_00402e60(param_1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

int __fastcall FUN_00403020(int param_1)

{
  bool bVar1;
  undefined4 local_c;
  
  local_c = param_1 + 4;
  bVar1 = thunk_FUN_00402fa0(param_1);
  if (bVar1) {
    local_c = thunk_FUN_004021a0(*(undefined4 *)(param_1 + 4));
  }
  return local_c;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

int __fastcall FUN_00403090(int param_1)

{
  bool bVar1;
  undefined4 local_c;
  
  local_c = param_1 + 4;
  bVar1 = thunk_FUN_00402fa0(param_1);
  if (bVar1) {
    local_c = thunk_FUN_004021a0(*(undefined4 *)(param_1 + 4));
  }
  return local_c;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall FUN_00403100(undefined4 param_1)

{
  undefined8 uVar1;
  
  uVar1 = thunk_FUN_00402e60(param_1);
  uVar1 = thunk_FUN_00403140((int *)uVar1,(int)((ulonglong)uVar1 >> 0x20));
  return uVar1;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall FUN_00403140(int *param_1,undefined4 param_2)

{
  int *extraout_EAX;
  int *piVar1;
  undefined4 extraout_EDX;
  undefined4 local_1c;
  undefined4 local_18;
  int *local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408aa0;
  local_10 = ExceptionList;
  local_1c = 0xcccccccc;
  local_18 = 0xcccccccc;
  ExceptionList = &local_10;
  local_14 = param_1;
  if (*param_1 != 0) {
    std::_Lockit::_Lockit((_Lockit *)&local_1c,3);
    piVar1 = (int *)(*local_14 + 4);
    while (*piVar1 != 0) {
      *(undefined4 *)*piVar1 = 0;
      *piVar1 = *(int *)(*piVar1 + 4);
    }
    *(undefined4 *)(*local_14 + 4) = 0;
    std::_Lockit::~_Lockit((_Lockit *)&local_1c);
    param_1 = extraout_EAX;
    param_2 = extraout_EDX;
  }
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00403214);
  ExceptionList = local_10;
  return CONCAT44(param_2,param_1);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00403270(undefined4 param_1)

{
  bool bVar1;
  undefined4 local_18;
  undefined4 local_14;
  int local_10;
  int local_c;
  undefined4 local_8;
  
  local_18 = 0xcccccccc;
  local_14 = 0xcccccccc;
  local_10 = -0x33333334;
  local_c = 0xcccccccc;
  local_8 = param_1;
  thunk_FUN_00403100(param_1);
  local_c = thunk_FUN_00402e60(local_8);
  bVar1 = thunk_FUN_00402fa0(local_c);
  if (bVar1) {
    local_10 = *(int *)(local_c + 4);
    local_14 = thunk_FUN_00402f40(local_8);
    thunk_FUN_004021c0(local_c + 4);
    thunk_FUN_00402290();
    thunk_FUN_00403700(local_10,*(int *)(local_c + 0x18) + 1);
  }
  *(undefined4 *)(local_c + 0x14) = 0;
  *(undefined4 *)(local_c + 0x18) = 0xf;
  local_18 = local_18 & 0xffffff;
  thunk_FUN_004035e0((undefined1 *)(local_c + 4),(undefined1 *)((int)&local_18 + 3));
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00403370(undefined4 param_1)

{
  undefined4 local_10;
  int local_c;
  undefined4 local_8;
  
  local_10 = 0xcccccccc;
  local_c = 0xcccccccc;
  local_8 = param_1;
  local_c = thunk_FUN_00402e60(param_1);
  *(undefined4 *)(local_c + 0x14) = 0;
  *(undefined4 *)(local_c + 0x18) = 0xf;
  local_10 = local_10 & 0xffffff;
  thunk_FUN_004035e0((undefined1 *)(local_c + 4),(undefined1 *)((int)&local_10 + 3));
  return;
}



void FUN_00403400(void)

{
                    // WARNING: Subroutine does not return
  std::_Xlength_error("string too long");
}



void FUN_00403420(void)

{
  return;
}



void FUN_00403430(void)

{
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void FUN_00403440(undefined4 param_1)

{
  uint uVar1;
  
  uVar1 = thunk_FUN_00401eb0(param_1);
  thunk_FUN_00401cb0(uVar1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void FUN_00403480(uint param_1)

{
  uint uVar1;
  
  uVar1 = thunk_FUN_00401ec0(param_1);
  thunk_FUN_00401cb0(uVar1);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __thiscall FUN_004034c0(void *this,char *param_1)

{
  undefined4 uVar1;
  uint uVar2;
  
  uVar1 = thunk_FUN_00403830(param_1);
  uVar2 = thunk_FUN_00401e20(uVar1);
  thunk_FUN_00403510(this,param_1,uVar2);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void * __thiscall FUN_00403510(void *this,void *param_1,uint param_2)

{
  undefined8 uVar1;
  undefined4 local_14;
  void *local_10;
  int local_c;
  void *local_8;
  
  local_14 = 0xcccccccc;
  local_10 = (void *)0xcccccccc;
  local_c = 0xcccccccc;
  local_8 = this;
  local_c = thunk_FUN_00402e60(this);
  if (*(uint *)(local_c + 0x18) < param_2) {
    local_14._0_3_ = (uint3)(ushort)local_14;
    uVar1 = thunk_FUN_00401fb0(local_8,param_2,0,param_1);
    local_8 = (void *)uVar1;
  }
  else {
    local_10 = (void *)thunk_FUN_00403020(local_c);
    *(uint *)(local_c + 0x14) = param_2;
    thunk_FUN_004039a0(local_10,param_1,param_2);
    local_14 = local_14 & 0xffffff;
    thunk_FUN_004035e0((undefined1 *)((int)local_10 + param_2),(undefined1 *)((int)&local_14 + 3));
  }
  return local_8;
}



void __cdecl FUN_004035e0(undefined1 *param_1,undefined1 *param_2)

{
  *param_1 = *param_2;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00403600(undefined4 param_1)

{
  int iVar1;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &LAB_00408ad0;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  iVar1 = thunk_FUN_00402e90(param_1);
  thunk_FUN_00403090(iVar1);
  ExceptionList = local_10;
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00403670(void *param_1,void *param_2,size_t param_3)

{
  memcmp(param_1,param_2,param_3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_004036a0(void *param_1,void *param_2,size_t param_3)

{
  memcpy(param_1,param_2,param_3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_004036d0(undefined4 param_1,int param_2,int param_3)

{
  thunk_FUN_00401e30(param_2,param_3 << 3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void FUN_00403700(int param_1,uint param_2)

{
  thunk_FUN_00401e30(param_1,param_2);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00403740(int param_1)

{
  thunk_FUN_00403600(param_1 + 4);
  thunk_FUN_00403a70("animal: %s\n");
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_00403790(int param_1)

{
  thunk_FUN_00403600(param_1 + 4);
  thunk_FUN_00403a70("bear: %s\n");
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __fastcall FUN_004037e0(int param_1)

{
  thunk_FUN_00403600(param_1 + 4);
  thunk_FUN_00403a70("cat: %s\n");
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_00403830(char *param_1)

{
  strlen(param_1);
  return;
}



undefined4 FUN_00403850(void)

{
  return 0x7fffffff;
}



undefined4 FUN_00403860(void)

{
  return 0xffffffff;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined8 __fastcall FUN_00403870(undefined4 param_1)

{
  uint *puVar1;
  undefined4 extraout_EDX;
  uint uVar2;
  undefined4 uVar3;
  uint local_24;
  uint local_20 [7];
  
  local_24 = 0xcccccccc;
  local_20[0] = 0xcccccccc;
  local_20[1] = 0xcccccccc;
  local_20[2] = 0xcccccccc;
  local_20[3] = 0xcccccccc;
  local_20[4] = 0xcccccccc;
  local_20[5] = 0xcccccccc;
  local_20[6] = param_1;
  thunk_FUN_00402f70(param_1);
  local_20[4] = thunk_FUN_00403860();
  local_20[1] = 0x10;
  puVar1 = thunk_FUN_00401f10(local_20 + 4,local_20 + 1);
  local_20[2] = *puVar1;
  local_20[0] = local_20[2] - 1;
  local_24 = thunk_FUN_00403850();
  puVar1 = thunk_FUN_00401f60(&local_24,local_20);
  uVar2 = *puVar1;
  uVar3 = extraout_EDX;
  _RTC_CheckStackVars((int)&stack0xfffffffc,(int *)&DAT_00403908);
  return CONCAT44(uVar3,uVar2);
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void FUN_00403960(void)

{
  thunk_FUN_00403a70("meow\n");
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl FUN_004039a0(void *param_1,void *param_2,size_t param_3)

{
  memmove(param_1,param_2,param_3);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void FUN_004039d0(void)

{
  thunk_FUN_00403a70("roar\n");
  return;
}



// Library Function - Single Match
//  ___local_stdio_scanf_options
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined * ___local_stdio_scanf_options(void)

{
  return &DAT_0040d320;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

void __cdecl
FUN_00403a20(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 *puVar1;
  
  puVar1 = (undefined4 *)___local_stdio_scanf_options();
  __stdio_common_vfprintf(*puVar1,puVar1[1],param_1,param_2,param_3,param_4);
  return;
}



// WARNING: Function: __RTC_CheckEsp replaced with injection: __RTC_CheckEsp

undefined4 __cdecl FUN_00403a70(undefined4 param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  
  uVar2 = 0;
  uVar1 = __acrt_iob_func(1,param_1,0,&stack0x00000008);
  uVar1 = thunk_FUN_00403a20(uVar1,0x403ab0,param_1,uVar2);
  return uVar1;
}



void __cdecl std::_Xlength_error(char *param_1)

{
                    // WARNING: Could not recover jumptable at 0x00403afa. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  _Xlength_error(param_1);
  return;
}



// Library Function - Single Match
//  void * __cdecl operator new(unsigned int)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void * __cdecl operator_new(uint param_1)

{
  void *pvVar1;
  int iVar2;
  
  while (pvVar1 = malloc(param_1), pvVar1 == (void *)0x0) {
    iVar2 = _callnewh(param_1);
    if (iVar2 == 0) {
      if (param_1 == 0xffffffff) {
        thunk_FUN_00404620();
      }
      else {
        thunk_FUN_004045f0();
      }
    }
  }
  return pvVar1;
}



void __cdecl FUN_00403b60(undefined4 param_1)

{
  thunk_FUN_00404690(param_1);
  return;
}



// Library Function - Single Match
//  @_RTC_AllocaHelper@12
// 
// Libraries: Visual Studio 2012, Visual Studio 2015, Visual Studio 2017, Visual Studio 2019
// __fastcall _RTC_AllocaHelper,12

void __fastcall _RTC_AllocaHelper(undefined1 *param_1,int param_2,undefined4 *param_3)

{
  int iVar1;
  undefined1 *puVar2;
  
  if (((param_1 != (undefined1 *)0x0) && (param_2 != 0)) &&
     (iVar1 = param_2, puVar2 = param_1, param_3 != (undefined4 *)0x0)) {
    for (; iVar1 != 0; iVar1 = iVar1 + -1) {
      *puVar2 = 0xcc;
      puVar2 = puVar2 + 1;
    }
    *(undefined4 *)(param_1 + 4) = *param_3;
    *(int *)(param_1 + 0xc) = param_2;
    *param_3 = param_1;
  }
  return;
}



// Library Function - Single Match
//  @_RTC_CheckStackVars2@12
// 
// Library: Visual Studio 2017 Debug
// __fastcall _RTC_CheckStackVars2,12

void __fastcall _RTC_CheckStackVars2(int param_1,int *param_2,_RTC_ALLOCA_NODE *param_3)

{
  _RTC_ALLOCA_NODE *p_Var1;
  int iVar2;
  _RTC_ALLOCA_NODE *p_Var3;
  int iVar4;
  int iVar5;
  void *unaff_retaddr;
  
  if ((param_2 != (int *)0x0) && (iVar4 = 0, 0 < *param_2)) {
    iVar5 = 0;
    do {
      iVar2 = param_2[1];
      if ((*(int *)(*(int *)(iVar2 + iVar5) + param_1 + -4) != -0x33333334) ||
         (*(int *)(*(int *)(iVar2 + 4 + iVar5) + *(int *)(iVar2 + iVar5) + param_1) != -0x33333334))
      {
        _RTC_StackFailure(unaff_retaddr,*(char **)(iVar2 + 8 + iVar5));
      }
      iVar4 = iVar4 + 1;
      iVar5 = iVar5 + 0xc;
    } while (iVar4 < *param_2);
  }
  iVar4 = 0;
  p_Var3 = param_3;
  if (param_3 != (_RTC_ALLOCA_NODE *)0x0) {
    do {
      p_Var1 = p_Var3 + 4;
      iVar4 = iVar4 + 1;
      p_Var3 = *(_RTC_ALLOCA_NODE **)p_Var1;
    } while (*(_RTC_ALLOCA_NODE **)p_Var1 != (_RTC_ALLOCA_NODE *)0x0);
    for (; param_3 != (_RTC_ALLOCA_NODE *)0x0; param_3 = *(_RTC_ALLOCA_NODE **)(param_3 + 4)) {
      if ((((*(int *)param_3 != -0x33333334) || (*(int *)(param_3 + 0x14) != -0x33333334)) ||
          (*(int *)(param_3 + 0x18) != -0x33333334)) || (*(int *)(param_3 + 0x1c) != -0x33333334)) {
        _RTC_AllocaFailure(unaff_retaddr,param_3,iVar4);
      }
      if (*(int *)(param_3 + *(int *)(param_3 + 0xc) + -4) != -0x33333334) {
        _RTC_AllocaFailure(unaff_retaddr,param_3,iVar4);
      }
      iVar4 = iVar4 + -1;
    }
  }
  return;
}



// Library Function - Single Match
//  @_RTC_CheckStackVars@8
// 
// Library: Visual Studio 2017 Debug
// __fastcall _RTC_CheckStackVars,8

void __fastcall _RTC_CheckStackVars(int param_1,int *param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  void *unaff_retaddr;
  
  iVar2 = 0;
  if (0 < *param_2) {
    iVar3 = 0;
    do {
      iVar1 = param_2[1];
      if ((*(int *)(*(int *)(iVar1 + iVar3) + param_1 + -4) != -0x33333334) ||
         (*(int *)(*(int *)(iVar1 + 4 + iVar3) + *(int *)(iVar1 + iVar3) + param_1) != -0x33333334))
      {
        _RTC_StackFailure(unaff_retaddr,*(char **)(iVar1 + 8 + iVar3));
      }
      iVar2 = iVar2 + 1;
      iVar3 = iVar3 + 0xc;
    } while (iVar2 < *param_2);
  }
  return;
}



// WARNING: This is an inlined function
// Library Function - Single Match
//  __RTC_CheckEsp
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __RTC_CheckEsp(void)

{
  int in_EAX;
  bool in_ZF;
  ulonglong in_BND0_LB;
  uint in_BND0_UB;
  void *unaff_retaddr;
  
  if (in_ZF) {
    return;
  }
  *(ulonglong *)(&stack0xfffffff8 + in_EAX) =
       (ulonglong)in_BND0_UB << 0x20 | in_BND0_LB & 0xffffffff;
  _RTC_Failure(unaff_retaddr,0);
  return;
}



// Library Function - Single Match
//  @__security_check_cookie@4
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug
// __fastcall __security_check_cookie,4

void __fastcall __security_check_cookie(int param_1)

{
  if (param_1 == DAT_0040d004) {
    return;
  }
                    // WARNING: Subroutine does not return
  ___report_gsfailure();
}



void __fastcall FUN_00403e40(undefined4 *param_1)

{
  *param_1 = type_info::vftable;
  return;
}



// Library Function - Multiple Matches With Different Base Names
//  public: virtual void * __thiscall std::_Ref_count_base::`scalar deleting destructor'(unsigned
// int)
//  public: virtual void * __thiscall type_info::`scalar deleting destructor'(unsigned int)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2015 Release, Visual Studio 2017 Debug, Visual
// Studio 2019 Debug

undefined4 * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  thunk_FUN_00403e40(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



// Library Function - Single Match
//  int __cdecl pre_c_initialization(void)
// 
// Library: Visual Studio 2017 Debug

int __cdecl pre_c_initialization(void)

{
  bool bVar1;
  char cVar2;
  uint uVar3;
  int iVar4;
  undefined3 extraout_var;
  
  __scrt_main_policy::set_app_type();
  __scrt_file_policy::set_fmode();
  __scrt_file_policy::set_commode();
  uVar3 = ___scrt_initialize_onexit_tables(1);
  if ((uVar3 & 0xff) == 0) {
    ___scrt_fastfail();
  }
  __RTC_Initialize();
  _atexit((_func_4879 *)&LAB_00401343);
  iVar4 = __scrt_narrow_argv_policy::configure_argv();
  if (iVar4 != 0) {
    ___scrt_fastfail();
  }
  __scrt_initialize_type_info();
  bVar1 = ___scrt_is_user_matherr_present();
  if (CONCAT31(extraout_var,bVar1) != 0) {
    __setusermatherr(&LAB_004013c0);
  }
  FID_conflict___initialize_denormal_control();
  FID_conflict___initialize_denormal_control();
  __initialize_default_precision();
  iVar4 = FID_conflict____scrt_initialize_mta();
  _configthreadlocale(iVar4);
  cVar2 = __should_initialize_environment();
  if (cVar2 != '\0') {
    __scrt_narrow_environment_policy::initialize_environment();
  }
  FID_conflict____scrt_initialize_mta();
  iVar4 = ___scrt_initialize_mta();
  if (iVar4 != 0) {
    ___scrt_fastfail();
  }
  return 0;
}



// Library Function - Single Match
//  int __cdecl post_pgo_initialization(void)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl post_pgo_initialization(void)

{
  ___scrt_initialize_default_local_stdio_options();
  return 0;
}



// Library Function - Single Match
//  void __cdecl pre_cpp_initialization(void)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl pre_cpp_initialization(void)

{
  undefined4 uVar1;
  
  thunk_FUN_004061f0();
  uVar1 = thunk_FUN_00405dd0();
  set_new_mode(uVar1);
  return;
}



// Library Function - Single Match
//  int __cdecl __scrt_common_main(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl __scrt_common_main(void)

{
  int iVar1;
  
  ___security_init_cookie();
  iVar1 = __scrt_common_main_seh();
  return iVar1;
}



// Library Function - Single Match
//  int __cdecl __scrt_common_main_seh(void)
// 
// Library: Visual Studio 2017 Debug

int __cdecl __scrt_common_main_seh(void)

{
  code *pcVar1;
  bool bVar2;
  uint uVar3;
  undefined4 uVar4;
  int *piVar5;
  int iVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  void *local_14;
  code *pcStack_10;
  uint local_c;
  undefined4 local_8;
  
  local_8 = 0xfffffffe;
  pcStack_10 = __except_handler4;
  local_14 = ExceptionList;
  local_c = DAT_0040d004 ^ 0x40c8c8;
  ExceptionList = &local_14;
  uVar8 = 1;
  uVar3 = ___scrt_initialize_crt(1);
  if ((uVar3 & 0xff) == 0) {
    uVar8 = 7;
    ___scrt_fastfail();
  }
  bVar2 = false;
  local_8 = 0;
  uVar4 = ___scrt_acquire_startup_lock();
  if (DAT_0040d6f8 == 1) {
    ___scrt_fastfail();
  }
  else if (DAT_0040d6f8 == 0) {
    DAT_0040d6f8 = 1;
    iVar6 = initterm_e(&DAT_0040a30c,&DAT_0040a618,uVar8);
    if (iVar6 != 0) {
      ExceptionList = local_14;
      return 0xff;
    }
    initterm(&DAT_0040a000,&DAT_0040a208);
    DAT_0040d6f8 = 2;
  }
  else {
    bVar2 = true;
  }
  ___scrt_release_startup_lock((char)uVar4);
  piVar5 = (int *)FID_conflict____scrt_get_dyn_tls_dtor_callback();
  if ((*piVar5 != 0) &&
     (uVar3 = ___scrt_is_nonwritable_in_current_image((int)piVar5), (uVar3 & 0xff) != 0)) {
    pcVar1 = (code *)*piVar5;
    uVar7 = 0;
    uVar4 = 2;
    uVar8 = 0;
    guard_check_icall();
    (*pcVar1)(uVar8,uVar4,uVar7);
  }
  piVar5 = (int *)FID_conflict____scrt_get_dyn_tls_dtor_callback();
  if ((*piVar5 != 0) &&
     (uVar3 = ___scrt_is_nonwritable_in_current_image((int)piVar5), (uVar3 & 0xff) != 0)) {
    register_thread_local_exe_atexit_callback(*piVar5);
  }
  iVar6 = invoke_main();
  uVar3 = ___scrt_is_managed_app();
  if ((uVar3 & 0xff) != 0) {
    if (!bVar2) {
      _cexit();
    }
    ___scrt_uninitialize_crt(1,'\0');
    ExceptionList = local_14;
    return iVar6;
  }
                    // WARNING: Subroutine does not return
  exit(iVar6);
}



// Library Function - Single Match
//  public: static int __cdecl __scrt_narrow_argv_policy::configure_argv(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl __scrt_narrow_argv_policy::configure_argv(void)

{
  undefined4 uVar1;
  int iVar2;
  
  uVar1 = thunk_FUN_00405da0();
  iVar2 = configure_narrow_argv(uVar1);
  return iVar2;
}



// Library Function - Single Match
//  public: static int __cdecl __scrt_narrow_environment_policy::initialize_environment(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl __scrt_narrow_environment_policy::initialize_environment(void)

{
  int iVar1;
  
  iVar1 = initialize_narrow_environment();
  return iVar1;
}



// Library Function - Single Match
//  int __cdecl invoke_main(void)
// 
// Library: Visual Studio 2017 Debug

int __cdecl invoke_main(void)

{
  undefined4 uVar1;
  int *piVar2;
  int iVar3;
  
  uVar1 = get_initial_narrow_environment();
  piVar2 = (int *)__p___argv(uVar1);
  iVar3 = *piVar2;
  piVar2 = (int *)__p___argc();
  iVar3 = thunk_FUN_004018e0(*piVar2,iVar3);
  return iVar3;
}



// Library Function - Single Match
//  public: static void __cdecl __scrt_main_policy::set_app_type(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl __scrt_main_policy::set_app_type(void)

{
  ::set_app_type(1);
  return;
}



// Library Function - Single Match
//  public: static void __cdecl __scrt_file_policy::set_commode(void)
// 
// Library: Visual Studio 2017 Debug

void __cdecl __scrt_file_policy::set_commode(void)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  
  uVar1 = thunk_FUN_00405db0();
  puVar2 = (undefined4 *)__p__commode();
  *puVar2 = uVar1;
  return;
}



// Library Function - Multiple Matches With Different Base Names
//  public: static int __cdecl __scrt_narrow_argv_policy::configure_argv(void)
//  public: static void __cdecl __scrt_file_policy::set_fmode(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl __scrt_file_policy::set_fmode(void)

{
  int _Mode;
  
  _Mode = thunk_FUN_00405dc0();
  _set_fmode(_Mode);
  return;
}



void FUN_00404330(void)

{
  __scrt_common_main();
  return;
}



// Library Function - Single Match
//  private: __thiscall std::bad_alloc::bad_alloc(char const * const)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug, Visual
// Studio 2019 Release

bad_alloc * __thiscall std::bad_alloc::bad_alloc(bad_alloc *this,char *param_1)

{
  exception::exception((exception *)this,param_1,1);
  *(undefined ***)this = vftable;
  return this;
}



exception * __thiscall FUN_00404370(void *this,exception *param_1)

{
  std::exception::exception(this,param_1);
  *(undefined ***)this = std::bad_alloc::vftable;
  return this;
}



// Library Function - Multiple Matches With Different Base Names
//  public: __thiscall std::bad_alloc::bad_alloc(void)
//  public: __thiscall std::bad_cast::bad_cast(void)
//  public: __thiscall std::bad_exception::bad_exception(void)
// 
// Libraries: Visual Studio 2015, Visual Studio 2017, Visual Studio 2019

exception * __fastcall FID_conflict_bad_cast(exception *param_1)

{
  std::exception::exception(param_1,"bad allocation",1);
  *(undefined ***)param_1 = std::bad_alloc::vftable;
  return param_1;
}



// Library Function - Multiple Matches With Different Base Names
//  public: __thiscall CTypedPtrList<class CList<void *,void *>,struct COleControlSiteOrWnd
// *>::CTypedPtrList<class CList<void *,void *>,struct COleControlSiteOrWnd *>(int)
//  public: __thiscall CTypedPtrList<class CPtrList,struct COleControlSiteOrWnd
// *>::CTypedPtrList<class CPtrList,struct COleControlSiteOrWnd *>(int)
//  public: __thiscall __non_rtti_object::__non_rtti_object(class __non_rtti_object const &)
//  public: __thiscall std::__non_rtti_object::__non_rtti_object(class std::__non_rtti_object const
// &)
//   21 names - too many to list
// 
// Library: Visual Studio

undefined4 * __thiscall FID_conflict_evaluation_error(void *this,exception *param_1)

{
  thunk_FUN_00404370(this,param_1);
  *(undefined ***)this = std::bad_array_new_length::vftable;
  return this;
}



// Library Function - Single Match
//  public: __thiscall std::bad_array_new_length::bad_array_new_length(void)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug, Visual
// Studio 2019 Release

bad_array_new_length * __thiscall
std::bad_array_new_length::bad_array_new_length(bad_array_new_length *this)

{
  bad_alloc::bad_alloc((bad_alloc *)this,"bad array new length");
  *(undefined ***)this = vftable;
  return this;
}



// Library Function - Single Match
//  public: __thiscall std::exception::exception(class std::exception const &)
// 
// Libraries: Visual Studio 2015, Visual Studio 2017, Visual Studio 2019

exception * __thiscall std::exception::exception(exception *this,exception *param_1)

{
  *(undefined ***)this = vftable;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  __std_exception_copy(param_1 + 4,this + 4);
  return this;
}



// Library Function - Single Match
//  public: __thiscall std::exception::exception(char const * const,int)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug, Visual
// Studio 2019 Release

exception * __thiscall std::exception::exception(exception *this,char *param_1,int param_2)

{
  *(undefined ***)this = vftable;
  *(undefined4 *)(this + 4) = 0;
  *(undefined4 *)(this + 8) = 0;
  *(char **)(this + 4) = param_1;
  return this;
}



void __fastcall FUN_004044c0(exception *param_1)

{
  std::exception::~exception(param_1);
  return;
}



void __fastcall FUN_004044e0(exception *param_1)

{
  thunk_FUN_004044c0(param_1);
  return;
}



// Library Function - Single Match
//  public: virtual __thiscall std::exception::~exception(void)
// 
// Libraries: Visual Studio 2015, Visual Studio 2017, Visual Studio 2019

void __thiscall std::exception::~exception(exception *this)

{
  *(undefined ***)this = vftable;
  __std_exception_destroy(this + 4);
  return;
}



// Library Function - Multiple Matches With Different Base Names
//  public: virtual void * __thiscall Concurrency::details::_Interruption_exception::`scalar
// deleting destructor'(unsigned int)
//  public: virtual void * __thiscall std::__non_rtti_object::`scalar deleting destructor'(unsigned
// int)
//  public: virtual void * __thiscall std::bad_alloc::`scalar deleting destructor'(unsigned int)
//  public: virtual void * __thiscall std::bad_array_new_length::`scalar deleting
// destructor'(unsigned int)
//   39 names - too many to list
// 
// Libraries: Visual Studio 2015, Visual Studio 2017, Visual Studio 2019

exception * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  thunk_FUN_004044c0(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



// Library Function - Multiple Matches With Different Base Names
//  public: virtual void * __thiscall Concurrency::details::_Interruption_exception::`scalar
// deleting destructor'(unsigned int)
//  public: virtual void * __thiscall std::__non_rtti_object::`scalar deleting destructor'(unsigned
// int)
//  public: virtual void * __thiscall std::bad_alloc::`scalar deleting destructor'(unsigned int)
//  public: virtual void * __thiscall std::bad_array_new_length::`scalar deleting
// destructor'(unsigned int)
//   39 names - too many to list
// 
// Libraries: Visual Studio 2015, Visual Studio 2017, Visual Studio 2019

exception * __thiscall FID_conflict__scalar_deleting_destructor_(void *this,uint param_1)

{
  thunk_FUN_004044e0(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



exception * __thiscall FUN_004045b0(void *this,uint param_1)

{
  std::exception::~exception(this);
  if ((param_1 & 1) != 0) {
    thunk_FUN_00403b60(this);
  }
  return this;
}



void FUN_004045f0(void)

{
  exception local_10 [12];
  
  FID_conflict_bad_cast(local_10);
                    // WARNING: Subroutine does not return
  _CxxThrowException(local_10,(ThrowInfo *)&DAT_0040c8e8);
}



void FUN_00404620(void)

{
  bad_array_new_length local_10 [12];
  
  std::bad_array_new_length::bad_array_new_length(local_10);
                    // WARNING: Subroutine does not return
  _CxxThrowException(local_10,(ThrowInfo *)&DAT_0040c94c);
}



// Library Function - Single Match
//  public: virtual char const * __thiscall std::exception::what(void)const 
// 
// Library: Visual Studio

char * __thiscall std::exception::what(exception *this)

{
  char *local_c;
  
  if (*(int *)(this + 4) == 0) {
    local_c = "Unknown exception";
  }
  else {
    local_c = *(char **)(this + 4);
  }
  return local_c;
}



void __cdecl FUN_00404690(undefined4 param_1)

{
  free_dbg(param_1,0xffffffff);
  return;
}



// Library Function - Single Match
//  bool __cdecl DebuggerProbe(unsigned long)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

bool __cdecl DebuggerProbe(ulong param_1)

{
  undefined4 local_20;
  ulong local_1c;
  char *local_18;
  char local_5;
  
  local_1c = param_1;
  local_18 = &local_5;
  local_5 = '\0';
  local_20 = 0x1001;
  notify_debugger((tagEXCEPTION_VISUALCPP_DEBUG_INFO *)&local_20);
  return local_5 != '\0';
}



// Library Function - Single Match
//  bool __cdecl DebuggerRuntime(unsigned long,int,void *,wchar_t const *)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

bool __cdecl DebuggerRuntime(ulong param_1,int param_2,void *param_3,wchar_t *param_4)

{
  undefined4 local_20;
  ulong local_1c;
  int local_18;
  void *local_14;
  char *local_10;
  wchar_t *local_c;
  char local_5;
  
  local_1c = param_1;
  local_18 = param_2;
  local_14 = param_3;
  local_10 = &local_5;
  local_c = param_4;
  local_5 = '\0';
  local_20 = 0x1002;
  notify_debugger((tagEXCEPTION_VISUALCPP_DEBUG_INFO *)&local_20);
  return local_5 != '\0';
}



// Library Function - Single Match
//  void __cdecl _RTC_AllocaFailure(void *,struct _RTC_ALLOCA_NODE *,int)
// 
// Library: Visual Studio 2017 Debug

void __cdecl _RTC_AllocaFailure(void *param_1,_RTC_ALLOCA_NODE *param_2,int param_3)

{
  int iVar1;
  char local_144 [244];
  char local_50 [52];
  char local_1c [20];
  uint local_8;
  
  iVar1 = DAT_0040d01c;
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  if (DAT_0040d01c != -1) {
    if (param_2 == (_RTC_ALLOCA_NODE *)0x0) {
      failwithmessage(param_1,DAT_0040d01c,4,
                      "Stack area around _alloca memory reserved by this function is corrupted\n");
      __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
      return;
    }
    _getMemBlockDataString
              (local_1c,local_50,(char *)(param_2 + 0x20),*(int *)(param_2 + 0xc) - 0x24);
    _sprintf_s(local_144,0xf4,"%s%s%p%s%zd%s%d%s%s%s%s%s",
               "Stack area around _alloca memory reserved by this function is corrupted",
               "\nAddress: 0x",param_2 + 0x20,"\nSize: ",*(int *)(param_2 + 0xc) + -0x24,
               "\nAllocation number within this function: ",param_3,"\nData: <",local_1c,
               &DAT_0040b484,local_50,&DAT_0040b480);
    failwithmessage(param_1,iVar1,4,local_144);
  }
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}



// Library Function - Single Match
//  void __cdecl _RTC_Failure(void *,int)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl _RTC_Failure(void *param_1,int param_2)

{
  if ((uint)param_2 < 5) {
    if (*(int *)(&DAT_0040d00c + param_2 * 4) != -1) {
      failwithmessage(param_1,*(int *)(&DAT_0040d00c + param_2 * 4),param_2,
                      (&PTR_s_The_value_of_ESP_was_not_properl_0040aee4)[param_2]);
      return;
    }
  }
  else {
    failwithmessage(param_1,1,5,"Unknown Runtime Check Error\n\r");
  }
  return;
}



// Library Function - Single Match
//  void __cdecl _RTC_StackFailure(void *,char const *)
// 
// Library: Visual Studio 2017 Debug

void __cdecl _RTC_StackFailure(void *param_1,char *param_2)

{
  int iVar1;
  uint uVar2;
  char *pcVar3;
  char local_408 [1024];
  uint local_8;
  
  iVar1 = DAT_0040d014;
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  if (DAT_0040d014 == -1) goto LAB_0040498a;
  if (*param_2 == '\0') {
LAB_00404978:
    pcVar3 = "Stack corrupted near unknown variable";
  }
  else {
    uVar2 = _strlen_priv(param_2);
    if (0x400 < uVar2 + 0x2d) goto LAB_00404978;
    strcpy_s(local_408,0x400,"Stack around the variable \'");
    strcat_s(local_408,0x400,param_2);
    strcat_s(local_408,0x400,"\' was corrupted.");
    pcVar3 = local_408;
  }
  failwithmessage(param_1,iVar1,2,pcVar3);
LAB_0040498a:
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}



// Library Function - Single Match
//  void __cdecl _getMemBlockDataString(char *,char *,char const *,unsigned int)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl _getMemBlockDataString(char *param_1,char *param_2,char *param_3,uint param_4)

{
  byte bVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  
  uVar3 = 0;
  iVar5 = 0;
  iVar4 = (int)param_3 - (int)param_1;
  while( true ) {
    uVar2 = param_4;
    if (0xf < param_4) {
      uVar2 = 0x10;
    }
    if (uVar2 <= uVar3) break;
    bVar1 = param_1[iVar4];
    _sprintf_s(param_2 + iVar5,0x31 - iVar5,"%.2X ",(uint)bVar1);
    *param_1 = bVar1;
    uVar3 = uVar3 + 1;
    param_1 = param_1 + 1;
    iVar5 = iVar5 + 3;
  }
  *param_1 = 0;
  param_2[iVar5] = '\0';
  return;
}



// Library Function - Single Match
//  unsigned int __cdecl _strlen_priv(char const *)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

uint __cdecl _strlen_priv(char *param_1)

{
  char cVar1;
  char *pcVar2;
  
  pcVar2 = param_1;
  do {
    cVar1 = *pcVar2;
    pcVar2 = pcVar2 + 1;
  } while (cVar1 != '\0');
  return (uint)(pcVar2 + (-1 - (int)param_1));
}



// Library Function - Single Match
//  void __cdecl failwithmessage(void *,int,int,char const *)
// 
// Library: Visual Studio 2017 Debug

void __cdecl failwithmessage(void *param_1,int param_2,int param_3,char *param_4)

{
  bool bVar1;
  code *pcVar2;
  uint cchWideChar;
  int iVar3;
  BOOL BVar4;
  wchar_t *pwVar5;
  char *pcVar6;
  char *pcVar7;
  wchar_t *pwVar8;
  wchar_t *pwVar9;
  wchar_t *pwVar10;
  char *pcVar11;
  ulong uVar12;
  int local_e3c;
  code *local_e38;
  ulong local_e34;
  WCHAR local_e30 [512];
  CHAR local_a30 [780];
  CHAR local_724 [780];
  wchar_t local_418 [260];
  wchar_t local_210 [260];
  uint local_8;
  
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  local_e34 = param_3;
  local_e38 = (code *)0x0;
  pcVar2 = (code *)thunk_FUN_00405320();
  if (pcVar2 == (code *)0x0) {
    local_e38 = (code *)thunk_FUN_00405310();
  }
  cchWideChar = MultiByteToWideChar(0xfde9,0,param_4,-1,(LPWSTR)0x0,0);
  if (cchWideChar < 0x200) {
    iVar3 = MultiByteToWideChar(0xfde9,0,param_4,-1,local_e30,cchWideChar);
    pwVar5 = local_e30;
    if (iVar3 == 0) goto LAB_00404b10;
  }
  else {
LAB_00404b10:
    pwVar5 = L"Runtime Check Error.\n\r Unable to display RTC Message.";
  }
  bVar1 = DebuggerProbe(0x1002);
  if (bVar1) {
    bVar1 = DebuggerRuntime(local_e34,*(int *)(&DAT_0040aefc + local_e34 * 4),param_1,pwVar5);
    if (bVar1) goto LAB_00404c6d;
    bVar1 = false;
  }
  else {
    bVar1 = true;
  }
  if ((local_e38 != (code *)0x0) || (pcVar2 != (code *)0x0)) {
    if (bVar1) {
      BVar4 = IsDebuggerPresent();
      if (BVar4 != 0) goto LAB_00404c6c;
    }
    _RTC_GetSrcLine((uchar *)((int)param_1 + -5),local_210,0x104,&local_e3c,local_418,0x104);
    if (pcVar2 == (code *)0x0) {
      pcVar6 = "Unknown Filename";
      iVar3 = WideCharToMultiByte(0xfde9,0,local_210,-1,local_724,0x30a,(LPCSTR)0x0,(LPBOOL)0x0);
      if (iVar3 != 0) {
        pcVar6 = local_724;
      }
      pcVar7 = "Unknown Module Name";
      iVar3 = WideCharToMultiByte(0xfde9,0,local_418,-1,local_a30,0x30a,(LPCSTR)0x0,(LPBOOL)0x0);
      pcVar2 = local_e38;
      if (iVar3 != 0) {
        pcVar7 = local_a30;
      }
      pcVar11 = "Run-Time Check Failure #%d - %s";
      uVar12 = local_e34;
      guard_check_icall();
      iVar3 = (*pcVar2)(param_2,pcVar6,local_e3c,pcVar7,pcVar11,uVar12,param_4);
    }
    else {
      pwVar9 = local_418;
      pwVar10 = L"Run-Time Check Failure #%d - %s";
      pwVar8 = local_210;
      uVar12 = local_e34;
      guard_check_icall();
      iVar3 = (*pcVar2)(param_2,pwVar8,local_e3c,pwVar9,pwVar10,uVar12,pwVar5);
    }
    if (iVar3 != 1) {
LAB_00404c6d:
      __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
      return;
    }
  }
LAB_00404c6c:
  pcVar2 = (code *)swi(3);
  (*pcVar2)();
  return;
}



// Library Function - Single Match
//  void __cdecl notify_debugger(struct tagEXCEPTION_VISUALCPP_DEBUG_INFO const &)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl notify_debugger(tagEXCEPTION_VISUALCPP_DEBUG_INFO *param_1)

{
  void *local_14;
  code *pcStack_10;
  uint local_c;
  undefined4 local_8;
  
  pcStack_10 = __except_handler4_noexcept;
  local_14 = ExceptionList;
  local_c = DAT_0040d004 ^ 0x40c998;
  ExceptionList = &local_14;
  local_8 = 0;
  RaiseException(0x406d1388,0,6,(ULONG_PTR *)param_1);
  ExceptionList = local_14;
  return;
}



// Library Function - Single Match
//  __RTC_UninitUse
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl __RTC_UninitUse(char *param_1)

{
  int iVar1;
  uint uVar2;
  char *pcVar3;
  void *unaff_retaddr;
  char local_408 [1024];
  uint local_8;
  
  iVar1 = DAT_0040d018;
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  if (DAT_0040d018 == -1) goto LAB_00404e38;
  if (param_1 == (char *)0x0) {
LAB_00404e23:
    pcVar3 = "A variable is being used without being initialized.";
  }
  else {
    uVar2 = _strlen_priv(param_1);
    if (0x400 < uVar2 + 0x3a) goto LAB_00404e23;
    strcpy_s(local_408,0x400,"The variable \'");
    strcat_s(local_408,0x400,param_1);
    strcat_s(local_408,0x400,"\' is being used without being initialized.");
    pcVar3 = local_408;
  }
  failwithmessage(unaff_retaddr,iVar1,3,pcVar3);
LAB_00404e38:
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}



// Library Function - Single Match
//  __vsprintf_s_l
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl
__vsprintf_s_l(char *_DstBuf,size_t _DstSize,char *_Format,_locale_t _Locale,va_list _ArgList)

{
  undefined4 *puVar1;
  int iVar2;
  
  puVar1 = (undefined4 *)___local_stdio_scanf_options();
  iVar2 = __stdio_common_vsprintf_s(*puVar1,puVar1[1],_DstBuf,_DstSize,_Format,_Locale,_ArgList);
  if (iVar2 < 0) {
    iVar2 = -1;
  }
  return iVar2;
}



// Library Function - Single Match
//  _sprintf_s
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl _sprintf_s(char *_DstBuf,size_t _SizeInBytes,char *_Format,...)

{
  int iVar1;
  
  iVar1 = __vsprintf_s_l(_DstBuf,_SizeInBytes,_Format,(_locale_t)0x0,&stack0x00000010);
  return iVar1;
}



// Library Function - Single Match
//  ___raise_securityfailure
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl ___raise_securityfailure(_EXCEPTION_POINTERS *param_1)

{
  HANDLE hProcess;
  UINT uExitCode;
  
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)0x0);
  UnhandledExceptionFilter(param_1);
  uExitCode = 0xc0000409;
  hProcess = GetCurrentProcess();
  TerminateProcess(hProcess,uExitCode);
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
// Library Function - Single Match
//  ___report_gsfailure
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl ___report_gsfailure(void)

{
  code *pcVar1;
  uint uVar2;
  undefined4 extraout_ECX;
  undefined4 extraout_ECX_00;
  undefined4 uVar3;
  uint extraout_EDX;
  undefined4 unaff_EBX;
  undefined4 unaff_EBP;
  undefined4 unaff_ESI;
  undefined4 unaff_EDI;
  undefined2 in_ES;
  undefined2 in_CS;
  undefined2 in_SS;
  undefined2 in_DS;
  undefined2 in_FS;
  undefined2 in_GS;
  byte bVar4;
  byte bVar5;
  byte in_AF;
  byte bVar6;
  byte bVar7;
  byte in_TF;
  byte in_IF;
  byte bVar8;
  byte in_NT;
  byte in_AC;
  byte in_VIF;
  byte in_VIP;
  byte in_ID;
  longlong lVar9;
  undefined4 unaff_retaddr;
  
  uVar2 = IsProcessorFeaturePresent(0x17);
  bVar4 = 0;
  bVar8 = 0;
  bVar7 = (int)uVar2 < 0;
  bVar6 = uVar2 == 0;
  bVar5 = (POPCOUNT(uVar2 & 0xff) & 1U) == 0;
  lVar9 = (ulonglong)extraout_EDX << 0x20;
  uVar3 = extraout_ECX;
  if (!(bool)bVar6) {
    pcVar1 = (code *)swi(0x29);
    lVar9 = (*pcVar1)();
    uVar3 = extraout_ECX_00;
  }
  _DAT_0040d428 = (undefined4)((ulonglong)lVar9 >> 0x20);
  _DAT_0040d430 = (undefined4)lVar9;
  _DAT_0040d440 =
       (uint)(in_NT & 1) * 0x4000 | (uint)(bVar8 & 1) * 0x800 | (uint)(in_IF & 1) * 0x200 |
       (uint)(in_TF & 1) * 0x100 | (uint)(bVar7 & 1) * 0x80 | (uint)(bVar6 & 1) * 0x40 |
       (uint)(in_AF & 1) * 0x10 | (uint)(bVar5 & 1) * 4 | (uint)(bVar4 & 1) |
       (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
       (uint)(in_AC & 1) * 0x40000;
  _DAT_0040d444 = &stack0x00000004;
  _DAT_0040d380 = 0x10001;
  _DAT_0040d330 = 0xc0000409;
  _DAT_0040d334 = 1;
  _DAT_0040d340 = 1;
  DAT_0040d344 = 2;
  _DAT_0040d33c = unaff_retaddr;
  _DAT_0040d40c = in_GS;
  _DAT_0040d410 = in_FS;
  _DAT_0040d414 = in_ES;
  _DAT_0040d418 = in_DS;
  _DAT_0040d41c = unaff_EDI;
  _DAT_0040d420 = unaff_ESI;
  _DAT_0040d424 = unaff_EBX;
  _DAT_0040d42c = uVar3;
  _DAT_0040d434 = unaff_EBP;
  DAT_0040d438 = unaff_retaddr;
  _DAT_0040d43c = in_CS;
  _DAT_0040d448 = in_SS;
  ___raise_securityfailure((_EXCEPTION_POINTERS *)&PTR_DAT_0040b5a0);
  return;
}



// Library Function - Single Match
//  ___report_rangecheckfailure
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void ___report_rangecheckfailure(void)

{
  ___report_securityfailure(8);
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
// Library Function - Single Match
//  ___report_securityfailure
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl ___report_securityfailure(undefined4 param_1)

{
  code *pcVar1;
  uint uVar2;
  undefined4 extraout_ECX;
  undefined4 extraout_ECX_00;
  undefined4 uVar3;
  uint extraout_EDX;
  undefined4 unaff_EBX;
  undefined4 unaff_EBP;
  undefined4 unaff_ESI;
  undefined4 unaff_EDI;
  undefined2 in_ES;
  undefined2 in_CS;
  undefined2 in_SS;
  undefined2 in_DS;
  undefined2 in_FS;
  undefined2 in_GS;
  byte bVar4;
  byte bVar5;
  byte in_AF;
  byte bVar6;
  byte bVar7;
  byte in_TF;
  byte in_IF;
  byte bVar8;
  byte in_NT;
  byte in_AC;
  byte in_VIF;
  byte in_VIP;
  byte in_ID;
  longlong lVar9;
  undefined4 unaff_retaddr;
  
  uVar2 = IsProcessorFeaturePresent(0x17);
  bVar4 = 0;
  bVar8 = 0;
  bVar7 = (int)uVar2 < 0;
  bVar6 = uVar2 == 0;
  bVar5 = (POPCOUNT(uVar2 & 0xff) & 1U) == 0;
  lVar9 = (ulonglong)extraout_EDX << 0x20;
  uVar3 = extraout_ECX;
  if (!(bool)bVar6) {
    pcVar1 = (code *)swi(0x29);
    lVar9 = (*pcVar1)();
    uVar3 = extraout_ECX_00;
  }
  _DAT_0040d428 = (undefined4)((ulonglong)lVar9 >> 0x20);
  _DAT_0040d430 = (undefined4)lVar9;
  _DAT_0040d440 =
       (uint)(in_NT & 1) * 0x4000 | (uint)(bVar8 & 1) * 0x800 | (uint)(in_IF & 1) * 0x200 |
       (uint)(in_TF & 1) * 0x100 | (uint)(bVar7 & 1) * 0x80 | (uint)(bVar6 & 1) * 0x40 |
       (uint)(in_AF & 1) * 0x10 | (uint)(bVar5 & 1) * 4 | (uint)(bVar4 & 1) |
       (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
       (uint)(in_AC & 1) * 0x40000;
  _DAT_0040d444 = &param_1;
  _DAT_0040d330 = 0xc0000409;
  _DAT_0040d334 = 1;
  _DAT_0040d340 = 1;
  DAT_0040d344 = param_1;
  _DAT_0040d33c = unaff_retaddr;
  _DAT_0040d40c = in_GS;
  _DAT_0040d410 = in_FS;
  _DAT_0040d414 = in_ES;
  _DAT_0040d418 = in_DS;
  _DAT_0040d41c = unaff_EDI;
  _DAT_0040d420 = unaff_ESI;
  _DAT_0040d424 = unaff_EBX;
  _DAT_0040d42c = uVar3;
  _DAT_0040d434 = unaff_EBP;
  DAT_0040d438 = unaff_retaddr;
  _DAT_0040d43c = in_CS;
  _DAT_0040d448 = in_SS;
  ___raise_securityfailure((_EXCEPTION_POINTERS *)&PTR_DAT_0040b5a0);
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
// Library Function - Single Match
//  ___report_securityfailureEx
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl ___report_securityfailureEx(undefined4 param_1,uint param_2,int param_3)

{
  code *pcVar1;
  uint uVar2;
  undefined4 extraout_ECX;
  undefined4 extraout_ECX_00;
  undefined4 uVar3;
  uint extraout_EDX;
  undefined4 unaff_EBX;
  undefined4 unaff_EBP;
  undefined4 unaff_ESI;
  undefined4 unaff_EDI;
  undefined2 in_ES;
  undefined2 in_CS;
  undefined2 in_SS;
  undefined2 in_DS;
  undefined2 in_FS;
  undefined2 in_GS;
  byte bVar4;
  byte bVar5;
  byte in_AF;
  byte bVar6;
  byte bVar7;
  byte in_TF;
  byte in_IF;
  byte bVar8;
  byte in_NT;
  byte in_AC;
  byte in_VIF;
  byte in_VIP;
  byte in_ID;
  longlong lVar9;
  undefined4 unaff_retaddr;
  uint local_8;
  
  uVar2 = IsProcessorFeaturePresent(0x17);
  bVar4 = 0;
  bVar8 = 0;
  bVar7 = (int)uVar2 < 0;
  bVar6 = uVar2 == 0;
  bVar5 = (POPCOUNT(uVar2 & 0xff) & 1U) == 0;
  lVar9 = (ulonglong)extraout_EDX << 0x20;
  uVar3 = extraout_ECX;
  if (!(bool)bVar6) {
    pcVar1 = (code *)swi(0x29);
    lVar9 = (*pcVar1)();
    uVar3 = extraout_ECX_00;
  }
  _DAT_0040d440 =
       (uint)(in_NT & 1) * 0x4000 | (uint)(bVar8 & 1) * 0x800 | (uint)(in_IF & 1) * 0x200 |
       (uint)(in_TF & 1) * 0x100 | (uint)(bVar7 & 1) * 0x80 | (uint)(bVar6 & 1) * 0x40 |
       (uint)(in_AF & 1) * 0x10 | (uint)(bVar5 & 1) * 4 | (uint)(bVar4 & 1) |
       (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
       (uint)(in_AC & 1) * 0x40000;
  _DAT_0040d444 = &param_1;
  _DAT_0040d330 = 0xc0000409;
  _DAT_0040d334 = 1;
  if ((param_2 != 0) && (param_3 == 0)) {
    param_2 = 0;
  }
  if (0xe < param_2) {
    param_2 = param_2 - 1;
  }
  _DAT_0040d340 = param_2 + 1;
  DAT_0040d344 = param_1;
  _DAT_0040d33c = unaff_retaddr;
  _DAT_0040d40c = in_GS;
  _DAT_0040d410 = in_FS;
  _DAT_0040d414 = in_ES;
  _DAT_0040d418 = in_DS;
  _DAT_0040d41c = unaff_EDI;
  _DAT_0040d420 = unaff_ESI;
  _DAT_0040d424 = unaff_EBX;
  _DAT_0040d42c = uVar3;
  _DAT_0040d434 = unaff_EBP;
  DAT_0040d438 = unaff_retaddr;
  _DAT_0040d43c = in_CS;
  _DAT_0040d448 = in_SS;
  for (local_8 = 0; _DAT_0040d428 = (undefined4)((ulonglong)lVar9 >> 0x20),
      _DAT_0040d430 = (undefined4)lVar9, local_8 < param_2; local_8 = local_8 + 1) {
    *(undefined4 *)(&DAT_0040d348 + local_8 * 4) = *(undefined4 *)(param_3 + local_8 * 4);
    lVar9 = CONCAT44(_DAT_0040d428,_DAT_0040d430);
  }
  ___raise_securityfailure((_EXCEPTION_POINTERS *)&PTR_DAT_0040b5a0);
  return;
}



undefined4 FUN_00405310(void)

{
  return DAT_0040d6ec;
}



undefined4 FUN_00405320(void)

{
  return DAT_0040d6f0;
}



undefined * __cdecl FUN_00405330(uint param_1)

{
  if (param_1 < 5) {
    return (&PTR_s_Stack_pointer_corruption_0040b5ac)[param_1];
  }
  return (undefined *)0x0;
}



undefined4 __cdecl FUN_00405360(undefined4 param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_0040d6ec;
  DAT_0040d6ec = param_1;
  DAT_0040d6f0 = 0;
  return uVar1;
}



undefined4 __cdecl FUN_00405390(undefined4 param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_0040d6f0;
  DAT_0040d6f0 = param_1;
  DAT_0040d6ec = 0;
  return uVar1;
}



// Library Function - Single Match
//  __RTC_SetErrorType
// 
// Libraries: Visual Studio 2015, Visual Studio 2017, Visual Studio 2019

undefined4 __cdecl __RTC_SetErrorType(uint param_1,undefined4 param_2)

{
  undefined4 uVar1;
  
  if (param_1 < 5) {
    uVar1 = *(undefined4 *)(&DAT_0040d00c + param_1 * 4);
    *(undefined4 *)(&DAT_0040d00c + param_1 * 4) = param_2;
    return uVar1;
  }
  return 0xffffffff;
}



// Library Function - Single Match
//  void (__cdecl** __cdecl __crt_fast_decode_pointer<void (__cdecl**)(void)>(void (__cdecl**
// const)(void)))(void)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

_func_void ** __cdecl __crt_fast_decode_pointer<void_(__cdecl**)(void)>(_func_void **param_1)

{
  _func_void **pp_Var1;
  
  pp_Var1 = (_func_void **)
            __crt_rotate_pointer_value((uint)param_1 ^ DAT_0040d004,DAT_0040d004 % 0x20);
  return pp_Var1;
}



// Library Function - Single Match
//  void (__cdecl** __cdecl __crt_fast_encode_pointer<void (__cdecl**)(void)>(void (__cdecl**
// const)(void)))(void)
// 
// Library: Visual Studio 2017 Debug

_func_void ** __cdecl __crt_fast_encode_pointer<void_(__cdecl**)(void)>(_func_void **param_1)

{
  uint uVar1;
  
  uVar1 = __crt_rotate_pointer_value((uint)param_1,0x20 - DAT_0040d004 % 0x20);
  return (_func_void **)(uVar1 ^ DAT_0040d004);
}



// Library Function - Single Match
//  unsigned int __cdecl __crt_rotate_pointer_value(unsigned int,int)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2017 Release, Visual
// Studio 2019 Debug

uint __cdecl __crt_rotate_pointer_value(uint param_1,int param_2)

{
  byte bVar1;
  
  bVar1 = (byte)param_2 & 0x1f;
  return param_1 >> bVar1 | param_1 << 0x20 - bVar1;
}



// Library Function - Single Match
//  struct _IMAGE_SECTION_HEADER * __cdecl find_pe_section(unsigned char * const,unsigned int)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

_IMAGE_SECTION_HEADER * __cdecl find_pe_section(uchar *param_1,uint param_2)

{
  int iVar1;
  _IMAGE_SECTION_HEADER *p_Var2;
  _IMAGE_SECTION_HEADER *local_8;
  
  iVar1 = *(int *)(param_1 + 0x3c);
  local_8 = (_IMAGE_SECTION_HEADER *)
            (param_1 + (uint)*(ushort *)(param_1 + iVar1 + 0x14) + iVar1 + 0x18);
  p_Var2 = local_8 + (uint)*(ushort *)(param_1 + iVar1 + 6) * 0x28;
  while( true ) {
    if (local_8 == p_Var2) {
      return (_IMAGE_SECTION_HEADER *)0x0;
    }
    if ((*(uint *)(local_8 + 0xc) <= param_2) &&
       (param_2 < (uint)(*(int *)(local_8 + 0xc) + *(int *)(local_8 + 8)))) break;
    local_8 = local_8 + 0x28;
  }
  return local_8;
}



// Library Function - Single Match
//  bool __cdecl is_potentially_valid_image_base(void * const)
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

bool __cdecl is_potentially_valid_image_base(void *param_1)

{
  bool bVar1;
  int *piVar2;
  
  if (param_1 == (void *)0x0) {
    bVar1 = false;
  }
  else if (*(short *)param_1 == 0x5a4d) {
    piVar2 = (int *)((int)param_1 + *(int *)((int)param_1 + 0x3c));
    if (*piVar2 == 0x4550) {
      if ((short)piVar2[6] == 0x10b) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
    }
    else {
      bVar1 = false;
    }
  }
  else {
    bVar1 = false;
  }
  return bVar1;
}



// WARNING: Unknown calling convention -- yet parameter storage is locked
// Library Function - Single Match
//  _NtCurrentTeb
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

_TEB * _NtCurrentTeb(void)

{
  return (_TEB *)&ExceptionList;
}



// Library Function - Single Match
//  ___scrt_acquire_startup_lock
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int ___scrt_acquire_startup_lock(void)

{
  int iVar1;
  bool bVar2;
  uint3 extraout_var;
  int iVar3;
  _TEB *p_Var4;
  int iVar5;
  
  bVar2 = ___scrt_is_ucrt_dll_in_use();
  if (CONCAT31(extraout_var,bVar2) == 0) {
    iVar3 = (uint)extraout_var << 8;
  }
  else {
    p_Var4 = _NtCurrentTeb();
    iVar3 = *(int *)(p_Var4 + 4);
    do {
      iVar5 = 0;
      LOCK();
      iVar1 = iVar3;
      if (DAT_0040d6fc != 0) {
        iVar5 = DAT_0040d6fc;
        iVar1 = DAT_0040d6fc;
      }
      DAT_0040d6fc = iVar1;
      UNLOCK();
      if (iVar5 == 0) {
        return 0;
      }
    } while (iVar3 != iVar5);
    iVar3 = CONCAT31((int3)((uint)iVar3 >> 8),1);
  }
  return iVar3;
}



// Library Function - Single Match
//  ___scrt_dllmain_after_initialize_c
// 
// Library: Visual Studio 2017 Debug

undefined4 ___scrt_dllmain_after_initialize_c(void)

{
  bool bVar1;
  undefined3 extraout_var;
  int iVar2;
  uint uVar3;
  
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if (CONCAT31(extraout_var,bVar1) == 0) {
    uVar3 = __scrt_narrow_argv_policy::configure_argv();
    if (uVar3 != 0) {
      return uVar3 & 0xffffff00;
    }
    iVar2 = __scrt_narrow_environment_policy::initialize_environment();
  }
  else {
    iVar2 = ___isa_available_init();
  }
  return CONCAT31((int3)((uint)iVar2 >> 8),1);
}



// Library Function - Single Match
//  ___scrt_dllmain_before_initialize_c
// 
// Library: Visual Studio 2017 Debug

bool ___scrt_dllmain_before_initialize_c(void)

{
  uint uVar1;
  
  uVar1 = ___scrt_initialize_onexit_tables(0);
  return (uVar1 & 0xff) != 0;
}



// Library Function - Single Match
//  ___scrt_dllmain_crt_thread_attach
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

int ___scrt_dllmain_crt_thread_attach(void)

{
  char cVar1;
  int iVar2;
  undefined3 extraout_var;
  uint3 extraout_var_00;
  
  cVar1 = thunk_FUN_00407410();
  if (cVar1 == '\0') {
    iVar2 = 0;
  }
  else {
    cVar1 = thunk_FUN_00407410();
    if (cVar1 == '\0') {
      thunk_FUN_00407420();
      iVar2 = (uint)extraout_var_00 << 8;
    }
    else {
      iVar2 = CONCAT31(extraout_var,1);
    }
  }
  return iVar2;
}



undefined1 FUN_004056d0(void)

{
  thunk_FUN_00407420();
  thunk_FUN_00407420();
  return 1;
}



// Library Function - Single Match
//  ___scrt_dllmain_exception_filter
// 
// Library: Visual Studio 2017 Debug

void __cdecl
___scrt_dllmain_exception_filter
          (undefined4 param_1,int param_2,undefined4 param_3,undefined *param_4,undefined4 param_5,
          undefined4 param_6)

{
  bool bVar1;
  undefined3 extraout_var;
  undefined4 uVar2;
  
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if ((CONCAT31(extraout_var,bVar1) == 0) && (param_2 == 1)) {
    uVar2 = 0;
    guard_check_icall();
    (*(code *)param_4)(param_1,uVar2,param_3);
  }
  seh_filter_dll(param_5,param_6);
  return;
}



// Library Function - Single Match
//  ___scrt_dllmain_uninitialize_c
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void ___scrt_dllmain_uninitialize_c(void)

{
  bool bVar1;
  undefined3 extraout_var;
  int iVar2;
  
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if (CONCAT31(extraout_var,bVar1) == 0) {
    iVar2 = thunk_FUN_00407450();
    if (iVar2 == 0) {
      _cexit();
    }
  }
  else {
    execute_onexit_table(&DAT_0040d704);
  }
  return;
}



void FUN_00405790(void)

{
  thunk_FUN_00407440();
  thunk_FUN_00407440();
  return;
}



// Library Function - Single Match
//  ___scrt_initialize_crt
// 
// Library: Visual Studio 2017 Debug

int __cdecl ___scrt_initialize_crt(int param_1)

{
  char cVar1;
  int iVar2;
  undefined3 extraout_var;
  uint3 extraout_var_00;
  
  if (param_1 == 0) {
    DAT_0040d700 = 1;
  }
  ___isa_available_init();
  cVar1 = thunk_FUN_00407400();
  if (cVar1 == '\0') {
    iVar2 = 0;
  }
  else {
    cVar1 = thunk_FUN_00407400();
    if (cVar1 == '\0') {
      thunk_FUN_00407430();
      iVar2 = (uint)extraout_var_00 << 8;
    }
    else {
      iVar2 = CONCAT31(extraout_var,1);
    }
  }
  return iVar2;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
// Library Function - Single Match
//  ___scrt_initialize_onexit_tables
// 
// Library: Visual Studio 2017 Debug

undefined4 __cdecl ___scrt_initialize_onexit_tables(int param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  uint uVar2;
  _func_void **pp_Var3;
  
  if (DAT_0040d701 != '\0') {
    return 1;
  }
  if ((param_1 != 0) && (param_1 != 1)) {
    ___scrt_fastfail();
  }
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if ((CONCAT31(extraout_var,bVar1) == 0) || (param_1 != 0)) {
    pp_Var3 = __crt_fast_encode_pointer<void_(__cdecl**)(void)>((_func_void **)0xffffffff);
    DAT_0040d704 = pp_Var3;
    _DAT_0040d708 = pp_Var3;
    _DAT_0040d70c = pp_Var3;
    DAT_0040d710 = pp_Var3;
    _DAT_0040d714 = pp_Var3;
    _DAT_0040d718 = pp_Var3;
  }
  else {
    uVar2 = initialize_onexit_table(&DAT_0040d704);
    if (uVar2 != 0) {
      return uVar2 & 0xffffff00;
    }
    uVar2 = initialize_onexit_table(&DAT_0040d710);
    if (uVar2 != 0) {
      return uVar2 & 0xffffff00;
    }
    pp_Var3 = (_func_void **)0x0;
  }
  DAT_0040d701 = 1;
  return CONCAT31((int3)((uint)pp_Var3 >> 8),1);
}



// Library Function - Single Match
//  ___scrt_is_nonwritable_in_current_image
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl ___scrt_is_nonwritable_in_current_image(int param_1)

{
  bool bVar1;
  uint3 extraout_var;
  int iVar2;
  _IMAGE_SECTION_HEADER *p_Var3;
  uint3 uVar4;
  void *local_14;
  code *pcStack_10;
  uint local_c;
  undefined4 local_8;
  
  pcStack_10 = __except_handler4;
  local_14 = ExceptionList;
  local_c = DAT_0040d004 ^ 0x40c9b8;
  ExceptionList = &local_14;
  local_8 = 0;
  bVar1 = is_potentially_valid_image_base(&IMAGE_DOS_HEADER_00400000);
  if (bVar1) {
    p_Var3 = find_pe_section((uchar *)&IMAGE_DOS_HEADER_00400000,param_1 - 0x400000);
    if (p_Var3 == (_IMAGE_SECTION_HEADER *)0x0) {
      iVar2 = 0;
    }
    else {
      uVar4 = (uint3)((uint)p_Var3 >> 8);
      if ((*(uint *)(p_Var3 + 0x24) & 0x80000000) == 0) {
        iVar2 = CONCAT31(uVar4,1);
      }
      else {
        iVar2 = (uint)uVar4 << 8;
      }
    }
  }
  else {
    iVar2 = (uint)extraout_var << 8;
  }
  ExceptionList = local_14;
  return iVar2;
}



// Library Function - Single Match
//  ___scrt_release_startup_lock
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl ___scrt_release_startup_lock(char param_1)

{
  bool bVar1;
  undefined3 extraout_var;
  
  bVar1 = ___scrt_is_ucrt_dll_in_use();
  if ((CONCAT31(extraout_var,bVar1) != 0) && (param_1 == '\0')) {
    LOCK();
    DAT_0040d6fc = 0;
    UNLOCK();
  }
  return;
}



// Library Function - Single Match
//  ___scrt_uninitialize_crt
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined4 __cdecl ___scrt_uninitialize_crt(undefined4 param_1,char param_2)

{
  undefined4 uVar1;
  undefined3 extraout_var;
  
  if ((DAT_0040d700 == '\0') || (param_2 == '\0')) {
    thunk_FUN_00407430();
    thunk_FUN_00407430();
    uVar1 = CONCAT31(extraout_var,1);
  }
  else {
    uVar1 = 1;
  }
  return uVar1;
}



// Library Function - Single Match
//  __onexit
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

_onexit_t __cdecl __onexit(_onexit_t _Func)

{
  _func_void **pp_Var1;
  int iVar2;
  _onexit_t local_c;
  _onexit_t local_8;
  
  pp_Var1 = __crt_fast_decode_pointer<void_(__cdecl**)(void)>(DAT_0040d704);
  local_c = _Func;
  if (pp_Var1 == (_func_void **)0xffffffff) {
    iVar2 = crt_atexit(_Func);
    if (iVar2 != 0) {
      local_8 = (_onexit_t)0x0;
      local_c = local_8;
    }
  }
  else {
    iVar2 = register_onexit_function(&DAT_0040d704,_Func);
    if (iVar2 != 0) {
      local_c = (_onexit_t)0x0;
    }
  }
  return local_c;
}



// Library Function - Single Match
//  _at_quick_exit
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

void __cdecl at_quick_exit(undefined4 param_1)

{
  _func_void **pp_Var1;
  
  pp_Var1 = __crt_fast_decode_pointer<void_(__cdecl**)(void)>(DAT_0040d710);
  if (pp_Var1 == (_func_void **)0xffffffff) {
    crt_at_quick_exit(param_1);
  }
  else {
    register_onexit_function(&DAT_0040d710,param_1);
  }
  return;
}



// Library Function - Single Match
//  _atexit
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

int __cdecl _atexit(_func_4879 *param_1)

{
  _onexit_t p_Var1;
  undefined4 local_8;
  
  p_Var1 = __onexit((_onexit_t)param_1);
  if (p_Var1 == (_onexit_t)0x0) {
    local_8 = -1;
  }
  else {
    local_8 = 0;
  }
  return local_8;
}



// Library Function - Single Match
//  ___get_entropy
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

uint ___get_entropy(void)

{
  DWORD DVar1;
  LARGE_INTEGER local_18;
  _FILETIME local_10;
  uint local_8;
  
  local_10.dwLowDateTime = 0;
  local_10.dwHighDateTime = 0;
  GetSystemTimeAsFileTime(&local_10);
  local_8 = local_10.dwLowDateTime ^ local_10.dwHighDateTime;
  DVar1 = GetCurrentThreadId();
  local_8 = DVar1 ^ local_8;
  DVar1 = GetCurrentProcessId();
  local_8 = DVar1 ^ local_8;
  QueryPerformanceCounter(&local_18);
  return local_8 ^ local_18.s.LowPart ^ local_18.s.HighPart ^ (uint)&local_8;
}



// Library Function - Single Match
//  ___security_init_cookie
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl ___security_init_cookie(void)

{
  undefined4 local_8;
  
  if ((DAT_0040d004 == 0xbb40e64e) || ((DAT_0040d004 & 0xffff0000) == 0)) {
    local_8 = ___get_entropy();
    if (local_8 == 0xbb40e64e) {
      local_8 = 0xbb40e64f;
    }
    else if ((local_8 & 0xffff0000) == 0) {
      local_8 = (local_8 | 0x4711) << 0x10 | local_8;
    }
    DAT_0040d004 = local_8;
  }
  DAT_0040d000 = ~DAT_0040d004;
  return;
}



undefined4 FUN_00405d90(void)

{
  return 0;
}



undefined4 FUN_00405da0(void)

{
  return 1;
}



undefined4 FUN_00405db0(void)

{
  return 0;
}



undefined4 FUN_00405dc0(void)

{
  return 0x4000;
}



undefined4 FUN_00405dd0(void)

{
  return 0;
}



// Library Function - Multiple Matches With Different Base Names
//  ___scrt_initialize_mta
//  ___scrt_initialize_winrt
//  __get_startup_thread_locale_mode
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined4 FID_conflict____scrt_initialize_mta(void)

{
  return 0;
}



// Library Function - Single Match
//  void __cdecl __scrt_initialize_type_info(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl __scrt_initialize_type_info(void)

{
  InitializeSListHead((PSLIST_HEADER)&DAT_0040d728);
  return;
}



void FUN_00405e10(void)

{
  __std_type_info_destroy_list(&DAT_0040d728);
  return;
}



// Library Function - Single Match
//  __should_initialize_environment
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined1 __should_initialize_environment(void)

{
  return 1;
}



// Library Function - Single Match
//  __initialize_default_precision
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __initialize_default_precision(void)

{
  errno_t eVar1;
  
  eVar1 = _controlfp_s((uint *)0x0,0x10000,0x30000);
  if (eVar1 != 0) {
    ___scrt_fastfail();
  }
  return;
}



// Library Function - Multiple Matches With Different Base Names
//  __initialize_denormal_control
//  __initialize_invalid_parameter_handler
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void FID_conflict___initialize_denormal_control(void)

{
  return;
}



// Library Function - Multiple Matches With Different Base Names
//  __initialize_denormal_control
//  __initialize_invalid_parameter_handler
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void FID_conflict___initialize_denormal_control(void)

{
  return;
}



// Library Function - Single Match
//  ___local_stdio_scanf_options
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined * ___local_stdio_scanf_options(void)

{
  return &DAT_0040d738;
}



// Library Function - Single Match
//  ___scrt_initialize_default_local_stdio_options
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

void ___scrt_initialize_default_local_stdio_options(void)

{
  uint *puVar1;
  
  puVar1 = (uint *)___local_stdio_scanf_options();
  *puVar1 = *puVar1 | 4;
  puVar1[1] = puVar1[1];
  puVar1 = (uint *)___local_stdio_scanf_options();
  *puVar1 = *puVar1 | 2;
  puVar1[1] = puVar1[1];
  return;
}



// Library Function - Single Match
//  ___scrt_is_user_matherr_present
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

bool ___scrt_is_user_matherr_present(void)

{
  return DAT_0040d028 == 0;
}



// Library Function - Multiple Matches With Different Base Names
//  ___scrt_get_dyn_tls_dtor_callback
//  ___scrt_get_dyn_tls_init_callback
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined * FID_conflict____scrt_get_dyn_tls_dtor_callback(void)

{
  return &DAT_0040d768;
}



// Library Function - Multiple Matches With Different Base Names
//  ___scrt_get_dyn_tls_dtor_callback
//  ___scrt_get_dyn_tls_init_callback
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined * FID_conflict____scrt_get_dyn_tls_dtor_callback(void)

{
  return &DAT_0040d75c;
}



// Library Function - Single Match
//  ___scrt_fastfail
// 
// Library: Visual Studio 2017 Debug

void ___scrt_fastfail(void)

{
  code *pcVar1;
  BOOL BVar2;
  undefined4 local_330 [39];
  EXCEPTION_RECORD local_64;
  _EXCEPTION_POINTERS local_14;
  LONG local_c;
  char local_6;
  undefined1 local_5;
  
  BVar2 = IsProcessorFeaturePresent(0x17);
  if (BVar2 != 0) {
    pcVar1 = (code *)swi(0x29);
    (*pcVar1)();
  }
  __crt_debugger_hook(3);
  memset(local_330,0,0x2cc);
  local_330[0] = 0x10001;
  memset(&local_64,0,0x50);
  local_64.ExceptionCode = 0x40000015;
  local_64.ExceptionFlags = 1;
  BVar2 = IsDebuggerPresent();
  local_6 = BVar2 == 1;
  local_14.ExceptionRecord = &local_64;
  local_14.ContextRecord = (PCONTEXT)local_330;
  local_5 = local_6;
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)0x0);
  local_c = UnhandledExceptionFilter(&local_14);
  if ((local_c == 0) && (local_6 == '\0')) {
    __crt_debugger_hook(3);
  }
  return;
}



// Library Function - Single Match
//  ___scrt_get_show_window_mode
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

WORD ___scrt_get_show_window_mode(void)

{
  _STARTUPINFOW local_4c;
  
  memset(&local_4c,0,0x44);
  GetStartupInfoW(&local_4c);
  if ((local_4c.dwFlags & 1) == 0) {
    local_4c.wShowWindow = 10;
  }
  return local_4c.wShowWindow;
}



// Library Function - Multiple Matches With Different Base Names
//  public: static int __cdecl __scrt_narrow_environment_policy::initialize_environment(void)
//  ___scrt_initialize_mta
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void ___scrt_initialize_mta(void)

{
  thunk_FUN_00406210();
  return;
}



// Library Function - Multiple Matches With Different Base Names
//  ___scrt_initialize_mta
//  ___scrt_initialize_winrt
//  __get_startup_thread_locale_mode
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

undefined4 FID_conflict____scrt_initialize_mta(void)

{
  return 0;
}



// Library Function - Single Match
//  ___scrt_is_managed_app
// 
// Library: Visual Studio 2019 Debug

uint ___scrt_is_managed_app(void)

{
  HMODULE pHVar1;
  uint uVar2;
  int *piVar3;
  
  pHVar1 = GetModuleHandleW((LPCWSTR)0x0);
  if (pHVar1 == (HMODULE)0x0) {
    uVar2 = 0;
  }
  else if ((short)pHVar1->unused == 0x5a4d) {
    piVar3 = (int *)((int)&pHVar1->unused + pHVar1[0xf].unused);
    if (*piVar3 == 0x4550) {
      if ((short)piVar3[6] == 0x10b) {
        if ((uint)piVar3[0x1d] < 0xf) {
          uVar2 = 0x100;
        }
        else if (piVar3[0x3a] == 0) {
          uVar2 = 0;
        }
        else {
          uVar2 = 1;
        }
      }
      else {
        uVar2 = (uint)(byte)((ushort)(short)piVar3[6] >> 8) << 8;
      }
    }
    else {
      uVar2 = (uint)piVar3 & 0xffffff00;
    }
  }
  else {
    uVar2 = (uint)pHVar1 & 0xffffff00;
  }
  return uVar2;
}



void FUN_004061f0(void)

{
  SetUnhandledExceptionFilter((LPTOP_LEVEL_EXCEPTION_FILTER)&LAB_00401195);
  return;
}



undefined4 FUN_00406210(void)

{
  return 0;
}



// Library Function - Single Match
//  ___scrt_unhandled_exception_filter@4
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

undefined4 ___scrt_unhandled_exception_filter_4(int *param_1)

{
  int *piVar1;
  
  piVar1 = (int *)*param_1;
  if (((*piVar1 == -0x1f928c9d) && (piVar1[4] == 3)) &&
     ((piVar1[5] == 0x19930520 ||
      (((piVar1[5] == 0x19930521 || (piVar1[5] == 0x19930522)) || (piVar1[5] == 0x1994000)))))) {
                    // WARNING: Subroutine does not return
    terminate();
  }
  return 0;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
// Library Function - Single Match
//  __crt_debugger_hook
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl __crt_debugger_hook(int param_1)

{
  _DAT_0040d744 = 0;
  return;
}



// Library Function - Single Match
//  __RTC_Initialize
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __RTC_Initialize(void)

{
  code *pcVar1;
  undefined4 *puVar2;
  
  puVar2 = &DAT_0040c120;
  do {
    pcVar1 = (code *)*puVar2;
    if (pcVar1 != (code *)0x0) {
      guard_check_icall();
      (*pcVar1)();
    }
    puVar2 = puVar2 + 1;
  } while (puVar2 < &DAT_0040c324);
  return;
}



// Library Function - Single Match
//  __except_handler4
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

void __cdecl
__except_handler4(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  except_handler4_common(&DAT_0040d004,__security_check_cookie,param_1,param_2,param_3,param_4);
  return;
}



void FUN_00406370(void)

{
  return;
}



undefined4 __cdecl FUN_00406380(undefined4 *param_1)

{
  return *param_1;
}



// Library Function - Single Match
//  _ReadPointerNoFence
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

void __cdecl _ReadPointerNoFence(undefined4 *param_1)

{
  thunk_FUN_00406380(param_1);
  return;
}



// Library Function - Single Match
//  __guard_icall_checks_enforced
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

bool __guard_icall_checks_enforced(void)

{
  code *pcVar1;
  
  pcVar1 = (code *)_ReadPointerNoFence(&PTR_guard_check_icall_0040f000);
  return pcVar1 != guard_check_icall;
}



// Library Function - Single Match
//  struct HINSTANCE__ * __cdecl GetPdbDll(void)
// 
// Library: Visual Studio 2017 Debug

HINSTANCE__ * __cdecl GetPdbDll(void)

{
  HINSTANCE__ *pHVar1;
  int iVar2;
  DWORD DVar3;
  wchar_t local_418 [260];
  wchar_t local_210 [260];
  uint local_8;
  
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  if (DAT_0040d74c == '\0') {
    DAT_0040d74c = '\x01';
    pHVar1 = GetPdbDllFromInstallPath();
    if ((pHVar1 == (HINSTANCE__ *)0x0) &&
       (((((iVar2 = __vcrt_GetModuleHandleW(L"VCRUNTIME140D.dll"), iVar2 == 0 ||
           (iVar2 = __vcrt_GetModuleFileNameW(iVar2,local_418,0x104), iVar2 == 0)) ||
          (iVar2 = GetPdbDllPathFromFilePath(local_418,local_210,0x104), iVar2 == 0)) ||
         ((iVar2 = __vcrt_LoadLibraryExW(local_210,0,0x900), iVar2 == 0 &&
          ((DVar3 = GetLastError(), DVar3 != 0x57 ||
           (iVar2 = __vcrt_LoadLibraryExW(local_210,0,8), iVar2 == 0)))))) &&
        ((iVar2 = __vcrt_LoadLibraryExW(L"MSPDB140",0,0xa00), iVar2 == 0 &&
         (((DVar3 = GetLastError(), DVar3 == 0x57 &&
           (iVar2 = __vcrt_GetModuleFileNameW(0,local_418,0x104), iVar2 != 0)) &&
          (iVar2 = GetPdbDllPathFromFilePath(local_418,local_210,0x104), iVar2 != 0)))))))) {
      __vcrt_LoadLibraryExW(local_210,0,8);
    }
  }
  pHVar1 = (HINSTANCE__ *)__security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return pHVar1;
}



// Library Function - Single Match
//  struct HINSTANCE__ * __cdecl GetPdbDllFromInstallPath(void)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

HINSTANCE__ * __cdecl GetPdbDllFromInstallPath(void)

{
  HMODULE hModule;
  DWORD DVar1;
  FARPROC pFVar2;
  FARPROC pFVar3;
  int iVar4;
  HINSTANCE__ *pHVar5;
  uint uVar6;
  uint uVar7;
  undefined4 uVar8;
  wchar_t *pwVar9;
  wchar_t *pwVar10;
  undefined4 uVar11;
  int *piVar12;
  undefined4 uVar13;
  undefined4 *puVar14;
  uint *puVar15;
  int local_220;
  FARPROC local_21c;
  uint local_218;
  undefined4 local_214;
  wchar_t local_210 [17];
  wchar_t awStack_1ee [243];
  uint local_8;
  
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  hModule = (HMODULE)__vcrt_LoadLibraryExW(L"api-ms-win-core-registry-l1-1-0.dll",0,0x800);
  if (hModule == (HMODULE)0x0) {
    hModule = (HMODULE)__vcrt_LoadLibraryExW(L"advapi32.dll",0,0x800);
    if (hModule == (HMODULE)0x0) {
      DVar1 = GetLastError();
      if (DVar1 != 0x57) goto LAB_0040665d;
      hModule = (HMODULE)__vcrt_LoadLibraryExW(L"advapi32.dll",0,0);
      if (hModule == (HMODULE)0x0) goto LAB_0040665d;
    }
  }
  pFVar2 = GetProcAddress(hModule,"RegOpenKeyExW");
  if (pFVar2 != (FARPROC)0x0) {
    pFVar3 = GetProcAddress(hModule,"RegQueryValueExW");
    if (pFVar3 != (FARPROC)0x0) {
      local_21c = GetProcAddress(hModule,"RegCloseKey");
      if (local_21c != (FARPROC)0x0) {
        puVar14 = &local_214;
        uVar13 = 1;
        uVar11 = 0;
        pwVar10 = L"SOFTWARE\\Wow6432Node\\Microsoft\\VisualStudio\\14.0\\Setup\\VC";
        uVar8 = 0x80000002;
        guard_check_icall();
        iVar4 = (*pFVar2)(uVar8,pwVar10,uVar11,uVar13,puVar14);
        if (iVar4 == 0) {
          puVar15 = &local_218;
          local_218 = 0x208;
          pwVar10 = local_210;
          piVar12 = &local_220;
          uVar11 = 0;
          pwVar9 = L"ProductDir";
          uVar8 = local_214;
          guard_check_icall();
          iVar4 = (*pFVar3)(uVar8,pwVar9,uVar11,piVar12,pwVar10,puVar15);
          pFVar2 = local_21c;
          guard_check_icall();
          (*pFVar2)(local_214);
          FreeLibrary(hModule);
          if ((((iVar4 == 0) && (local_220 == 1)) && ((local_218 & 1) == 0)) &&
             (uVar6 = local_218 >> 1, 1 < uVar6)) {
            uVar7 = uVar6 - 1;
            if (local_210[uVar7] == L'\0') {
              if (local_210[uVar6 - 2] != L'\\') {
                local_210[uVar7] = L'\\';
                uVar7 = uVar6;
              }
              if ((0x11 < ~uVar7) && (uVar7 + 0x11 < 0x105)) {
                builtin_wcsncpy(local_210 + uVar7,L"bin\\MSPDB140.DLL",0x11);
                iVar4 = __vcrt_LoadLibraryExW(local_210,0,0x900);
                if (iVar4 == 0) {
                  DVar1 = GetLastError();
                  if (DVar1 == 0x57) {
                    __vcrt_LoadLibraryExW(local_210,0,8);
                  }
                }
                pHVar5 = (HINSTANCE__ *)__security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
                return pHVar5;
              }
            }
          }
        }
        else {
          FreeLibrary(hModule);
        }
      }
    }
  }
LAB_0040665d:
  pHVar5 = (HINSTANCE__ *)__security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return pHVar5;
}



// Library Function - Single Match
//  int __cdecl GetPdbDllPathFromFilePath(wchar_t const *,wchar_t *,unsigned int)
// 
// Libraries: Visual Studio 2017 Debug, Visual Studio 2019 Debug

int __cdecl GetPdbDllPathFromFilePath(wchar_t *param_1,wchar_t *param_2,uint param_3)

{
  errno_t eVar1;
  int iVar2;
  wchar_t local_610 [256];
  wchar_t local_410 [256];
  wchar_t local_210 [256];
  wchar_t local_10 [4];
  uint local_8;
  
  local_8 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  eVar1 = _wsplitpath_s(param_1,local_10,3,local_610,0x100,local_410,0x100,local_210,0x100);
  if (eVar1 == 0) {
    eVar1 = wcscpy_s(local_410,9,L"MSPDB140");
    if (eVar1 == 0) {
      eVar1 = wcscpy_s(local_210,4,L"DLL");
      if (eVar1 == 0) {
        eVar1 = _wmakepath_s(param_2,param_3,local_10,local_610,local_410,local_210);
        if (eVar1 == 0) {
          iVar2 = __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
          return iVar2;
        }
      }
    }
  }
  iVar2 = __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return iVar2;
}



// Library Function - Single Match
//  int __cdecl _RTC_GetSrcLine(unsigned char *,wchar_t *,unsigned long,int *,wchar_t *,unsigned
// long)
// 
// Library: Visual Studio 2017 Debug

int __cdecl
_RTC_GetSrcLine(uchar *param_1,wchar_t *param_2,ulong param_3,int *param_4,wchar_t *param_5,
               ulong param_6)

{
  code *pcVar1;
  char cVar2;
  SIZE_T SVar3;
  int iVar4;
  uint uVar5;
  FARPROC pFVar6;
  HANDLE pvVar7;
  int *piVar8;
  uint *puVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  undefined4 *puVar13;
  uint *puVar14;
  ushort *puVar15;
  ulong *puVar16;
  DWORD DVar17;
  wchar_t *pwVar18;
  undefined4 uVar19;
  int **ppiVar20;
  undefined4 uVar21;
  undefined4 uVar22;
  undefined1 *puVar23;
  undefined4 uVar24;
  undefined4 uVar25;
  undefined *puVar26;
  _MEMORY_BASIC_INFORMATION local_50;
  undefined1 local_34 [4];
  undefined4 local_30;
  int local_2c;
  int local_28;
  int *local_24;
  uint local_20;
  int *local_1c;
  int *local_18;
  uint local_14;
  uint *local_10;
  int *local_c;
  ushort local_8 [2];
  
  *param_4 = 0;
  *param_2 = L'\0';
  SVar3 = VirtualQuery(param_1 + -1,&local_50,0x1c);
  if ((((SVar3 == 0) ||
       (iVar4 = __vcrt_GetModuleFileNameW(local_50.AllocationBase,param_5,param_6), iVar4 == 0)) ||
      (*(short *)local_50.AllocationBase != 0x5a4d)) ||
     ((*(int *)((int)local_50.AllocationBase + 0x3c) < 1 ||
      (piVar8 = (int *)(*(int *)((int)local_50.AllocationBase + 0x3c) + (int)local_50.AllocationBase
                       ), *piVar8 != 0x4550)))) {
    return 0;
  }
  uVar11 = (int)(param_1 + -1) - (int)local_50.AllocationBase;
  uVar12 = (uint)*(ushort *)((int)piVar8 + 6);
  uVar10 = 0;
  uVar5 = 0;
  if (uVar12 != 0) {
    puVar9 = (uint *)((int)piVar8 + *(ushort *)(piVar8 + 5) + 0x20);
    do {
      if ((puVar9[1] <= uVar11) && (uVar10 = uVar11 - puVar9[1], uVar11 < *puVar9)) break;
      uVar5 = uVar5 + 1;
      puVar9 = puVar9 + 10;
    } while (uVar5 < uVar12);
  }
  if (uVar5 == uVar12) {
    return 0;
  }
  local_10 = (uint *)(uVar5 + 1);
  if (DAT_0040d74d == '\0') {
    if (DAT_0040d748 != (HMODULE)0x0) {
      return 0;
    }
    DAT_0040d748 = GetPdbDll();
    if (DAT_0040d748 == (HINSTANCE__ *)0x0) {
      return 0;
    }
    DAT_0040d74d = '\x01';
  }
  pFVar6 = GetProcAddress(DAT_0040d748,"PDBOpenValidate5");
  if (pFVar6 == (FARPROC)0x0) {
    return 0;
  }
  ppiVar20 = &local_1c;
  uVar25 = 0;
  uVar24 = 0;
  puVar23 = local_34;
  uVar22 = 0;
  uVar21 = 0;
  uVar19 = 0;
  pwVar18 = param_5;
  guard_check_icall();
  iVar4 = (*pFVar6)(pwVar18,uVar19,uVar21,uVar22,puVar23,uVar24,uVar25,ppiVar20);
  if (iVar4 == 0) {
    return 0;
  }
  local_28 = 0;
  pcVar1 = *(code **)*local_1c;
  guard_check_icall();
  iVar4 = (*pcVar1)();
  if (iVar4 != 0x1329141) goto LAB_00406c2e;
  pcVar1 = *(code **)(*local_1c + 0x1c);
  ppiVar20 = &local_24;
  puVar26 = &DAT_0040b890;
  uVar19 = 0;
  guard_check_icall();
  iVar4 = (*pcVar1)(uVar19,puVar26,ppiVar20);
  if (iVar4 == 0) goto LAB_00406c2e;
  uVar22 = 0;
  uVar21 = 0;
  uVar19 = 0;
  pcVar1 = *(code **)(*local_24 + 0x20);
  ppiVar20 = &local_18;
  puVar9 = local_10;
  uVar5 = uVar10;
  guard_check_icall();
  iVar4 = (*pcVar1)(puVar9,uVar5,ppiVar20,uVar19,uVar21,uVar22);
  if (iVar4 != 0) {
    local_c = (int *)0x0;
    pcVar1 = *(code **)(*local_18 + 0x68);
    ppiVar20 = &local_c;
    guard_check_icall();
    cVar2 = (*pcVar1)(ppiVar20);
    if ((cVar2 != '\0') && (local_c != (int *)0x0)) {
      pcVar1 = *(code **)(*local_c + 8);
      guard_check_icall();
      iVar4 = (*pcVar1)();
      puVar9 = (uint *)0x0;
      if (iVar4 != 0) {
        do {
          uVar21 = 0;
          pcVar1 = *(code **)(*local_c + 0xc);
          puVar9 = &local_14;
          piVar8 = &local_2c;
          puVar15 = local_8;
          puVar14 = &local_20;
          uVar19 = 0;
          guard_check_icall();
          cVar2 = (*pcVar1)(uVar19,puVar14,puVar15,piVar8,puVar9,uVar21);
          if (cVar2 == '\0') goto LAB_00406bf3;
          if ((((uint *)(uint)local_8[0] == local_10) && (local_20 <= uVar10)) &&
             (uVar10 < local_2c + local_20)) {
            if ((local_14 == 0) || (0x1ffffffe < local_14)) goto LAB_00406bf3;
            SVar3 = local_14 << 3;
            DVar17 = 0;
            pvVar7 = GetProcessHeap();
            puVar9 = HeapAlloc(pvVar7,DVar17,SVar3);
            local_10 = puVar9;
            if (puVar9 == (uint *)0x0) goto LAB_00406bf3;
            puVar14 = &local_14;
            puVar13 = &local_30;
            uVar22 = 0;
            uVar21 = 0;
            uVar19 = 0;
            pcVar1 = *(code **)(*local_c + 0xc);
            guard_check_icall();
            cVar2 = (*pcVar1)(puVar13,uVar19,uVar21,uVar22,puVar14,puVar9);
            puVar9 = local_10;
            if ((cVar2 == '\0') || (uVar10 - local_20 < *local_10)) goto LAB_00406be3;
            uVar5 = 1;
            if (local_14 < 2) goto LAB_00406cca;
            goto LAB_00406cc0;
          }
          pcVar1 = *(code **)(*local_c + 8);
          guard_check_icall();
          iVar4 = (*pcVar1)();
        } while (iVar4 != 0);
        puVar9 = (uint *)0x0;
      }
      goto LAB_00406be3;
    }
    goto LAB_00406c06;
  }
  goto LAB_00406c1a;
  while (uVar5 = uVar5 + 1, uVar5 < local_14) {
LAB_00406cc0:
    if (uVar10 - local_20 < local_10[uVar5 * 2]) break;
  }
LAB_00406cca:
  uVar22 = 0;
  uVar21 = 0;
  *param_4 = local_10[uVar5 * 2 + -1] & 0xffffff;
  uVar19 = 0;
  pcVar1 = *(code **)(*local_18 + 0x70);
  puVar16 = &param_3;
  guard_check_icall();
  cVar2 = (*pcVar1)(local_30,param_2,puVar16,uVar19,uVar21,uVar22);
  puVar9 = local_10;
  if (cVar2 != '\0') {
    local_28 = 1;
  }
LAB_00406be3:
  DVar17 = 0;
  pvVar7 = GetProcessHeap();
  HeapFree(pvVar7,DVar17,puVar9);
LAB_00406bf3:
  pcVar1 = *(code **)*local_c;
  guard_check_icall();
  (*pcVar1)();
LAB_00406c06:
  pcVar1 = *(code **)(*local_18 + 0x40);
  guard_check_icall();
  (*pcVar1)();
LAB_00406c1a:
  pcVar1 = *(code **)(*local_24 + 0x38);
  guard_check_icall();
  (*pcVar1)();
LAB_00406c2e:
  pcVar1 = *(code **)(*local_1c + 0x2c);
  guard_check_icall();
  (*pcVar1)();
  return local_28;
}



// Library Function - Single Match
//  __except_handler4_noexcept
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

int __cdecl
__except_handler4_noexcept(int *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  
  iVar1 = __except_handler4(param_1,param_2,param_3,param_4);
  if ((((param_1[1] & 0x66U) == 0) && (*param_1 == -0x1f928c9d)) && (iVar1 == 1)) {
                    // WARNING: Subroutine does not return
    terminate();
  }
  return iVar1;
}



// WARNING: Removing unreachable block (ram,0x0040701a)
// WARNING: Removing unreachable block (ram,0x00406f46)
// WARNING: Removing unreachable block (ram,0x00406ed0)
// WARNING: Globals starting with '_' overlap smaller symbols at the same address
// Library Function - Single Match
//  ___isa_available_init
// 
// Libraries: Visual Studio 2015 Debug, Visual Studio 2017 Debug

void ___isa_available_init(void)

{
  int *piVar1;
  uint *puVar2;
  int iVar3;
  uint uVar4;
  BOOL BVar5;
  uint uVar6;
  uint uVar7;
  uint in_XCR0;
  uint local_c;
  
  uVar4 = DAT_0040d004 ^ (uint)&stack0xfffffffc;
  _DAT_0040d750 = 0;
  DAT_0040d02c = DAT_0040d02c | 1;
  BVar5 = IsProcessorFeaturePresent(10);
  uVar6 = DAT_0040d02c;
  if (BVar5 != 0) {
    local_c = 0;
    _DAT_0040d750 = 1;
    piVar1 = (int *)cpuid_basic_info(0);
    puVar2 = (uint *)cpuid_Version_info(1);
    uVar6 = *puVar2;
    uVar7 = puVar2[3];
    if (((piVar1[1] == 0x756e6547 && piVar1[2] == 0x49656e69) && piVar1[3] == 0x6c65746e) &&
       ((((((uVar6 & 0xfff3ff0) == 0x106c0 || ((uVar6 & 0xfff3ff0) == 0x20660)) ||
          ((uVar6 & 0xfff3ff0) == 0x20670)) ||
         (((uVar6 & 0xfff3ff0) == 0x30650 || ((uVar6 & 0xfff3ff0) == 0x30660)))) ||
        ((uVar6 & 0xfff3ff0) == 0x30670)))) {
      DAT_0040d754 = DAT_0040d754 | 1;
    }
    if (6 < *piVar1) {
      iVar3 = cpuid_Extended_Feature_Enumeration_info(7);
      local_c = *(uint *)(iVar3 + 4);
      if ((local_c & 0x200) != 0) {
        DAT_0040d754 = DAT_0040d754 | 2;
      }
    }
    uVar6 = DAT_0040d02c | 2;
    if ((uVar7 & 0x100000) != 0) {
      _DAT_0040d750 = 2;
      uVar6 = DAT_0040d02c | 6;
      if ((((uVar7 & 0x8000000) != 0) && ((uVar7 & 0x10000000) != 0)) && ((in_XCR0 & 6) == 6)) {
        _DAT_0040d750 = 3;
        uVar6 = DAT_0040d02c | 0xe;
        if ((local_c & 0x20) != 0) {
          _DAT_0040d750 = 5;
          uVar6 = DAT_0040d02c | 0x2e;
        }
      }
    }
  }
  DAT_0040d02c = uVar6;
  __security_check_cookie(uVar4 ^ (uint)&stack0xfffffffc);
  return;
}



// Library Function - Single Match
//  ___scrt_is_ucrt_dll_in_use
// 
// Library: Visual Studio 2017 Debug

bool ___scrt_is_ucrt_dll_in_use(void)

{
  return DAT_0040d030 != 0;
}



int __cdecl memcmp(void *_Buf1,void *_Buf2,size_t _Size)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040721d. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = memcmp(_Buf1,_Buf2,_Size);
  return iVar1;
}



void * __cdecl memcpy(void *_Dst,void *_Src,size_t _Size)

{
  void *pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407223. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = memcpy(_Dst,_Src,_Size);
  return pvVar1;
}



void * __cdecl memmove(void *_Dst,void *_Src,size_t _Size)

{
  void *pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407229. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = memmove(_Dst,_Src,_Size);
  return pvVar1;
}



void __RTDynamicCast(void)

{
                    // WARNING: Could not recover jumptable at 0x00407235. Too many branches
                    // WARNING: Treating indirect jump as call
  __RTDynamicCast();
  return;
}



void __std_exception_copy(void)

{
                    // WARNING: Could not recover jumptable at 0x0040723b. Too many branches
                    // WARNING: Treating indirect jump as call
  __std_exception_copy();
  return;
}



void __std_exception_destroy(void)

{
                    // WARNING: Could not recover jumptable at 0x00407241. Too many branches
                    // WARNING: Treating indirect jump as call
  __std_exception_destroy();
  return;
}



void _CxxThrowException(void *pExceptionObject,ThrowInfo *pThrowInfo)

{
                    // WARNING: Could not recover jumptable at 0x00407247. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  _CxxThrowException(pExceptionObject,pThrowInfo);
  return;
}



void __std_type_info_destroy_list(void)

{
                    // WARNING: Could not recover jumptable at 0x0040724d. Too many branches
                    // WARNING: Treating indirect jump as call
  __std_type_info_destroy_list();
  return;
}



void * __cdecl memset(void *_Dst,int _Val,size_t _Size)

{
  void *pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407253. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = memset(_Dst,_Val,_Size);
  return pvVar1;
}



void __cdecl except_handler4_common(void)

{
                    // WARNING: Could not recover jumptable at 0x00407259. Too many branches
                    // WARNING: Treating indirect jump as call
  except_handler4_common();
  return;
}



void __vcrt_GetModuleFileNameW(void)

{
                    // WARNING: Could not recover jumptable at 0x0040725f. Too many branches
                    // WARNING: Treating indirect jump as call
  __vcrt_GetModuleFileNameW();
  return;
}



void __vcrt_GetModuleHandleW(void)

{
                    // WARNING: Could not recover jumptable at 0x00407265. Too many branches
                    // WARNING: Treating indirect jump as call
  __vcrt_GetModuleHandleW();
  return;
}



void __vcrt_LoadLibraryExW(void)

{
                    // WARNING: Could not recover jumptable at 0x0040726b. Too many branches
                    // WARNING: Treating indirect jump as call
  __vcrt_LoadLibraryExW();
  return;
}



size_t __cdecl strlen(char *_Str)

{
  size_t sVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407289. Too many branches
                    // WARNING: Treating indirect jump as call
  sVar1 = strlen(_Str);
  return sVar1;
}



int __cdecl _callnewh(size_t _Size)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040728f. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = _callnewh(_Size);
  return iVar1;
}



void * __cdecl malloc(size_t _Size)

{
  void *pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407295. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = malloc(_Size);
  return pvVar1;
}



void _seh_filter_exe(void)

{
                    // WARNING: Could not recover jumptable at 0x004072a1. Too many branches
                    // WARNING: Treating indirect jump as call
  _seh_filter_exe();
  return;
}



void __cdecl set_app_type(void)

{
                    // WARNING: Could not recover jumptable at 0x004072a7. Too many branches
                    // WARNING: Treating indirect jump as call
  set_app_type();
  return;
}



void __setusermatherr(void)

{
                    // WARNING: Could not recover jumptable at 0x004072ad. Too many branches
                    // WARNING: Treating indirect jump as call
  __setusermatherr();
  return;
}



void __cdecl configure_narrow_argv(void)

{
                    // WARNING: Could not recover jumptable at 0x004072b3. Too many branches
                    // WARNING: Treating indirect jump as call
  configure_narrow_argv();
  return;
}



void __cdecl initialize_narrow_environment(void)

{
                    // WARNING: Could not recover jumptable at 0x004072b9. Too many branches
                    // WARNING: Treating indirect jump as call
  initialize_narrow_environment();
  return;
}



void __cdecl get_initial_narrow_environment(void)

{
                    // WARNING: Could not recover jumptable at 0x004072bf. Too many branches
                    // WARNING: Treating indirect jump as call
  get_initial_narrow_environment();
  return;
}



void __cdecl initterm(void)

{
                    // WARNING: Could not recover jumptable at 0x004072c5. Too many branches
                    // WARNING: Treating indirect jump as call
  initterm();
  return;
}



void __cdecl initterm_e(void)

{
                    // WARNING: Could not recover jumptable at 0x004072cb. Too many branches
                    // WARNING: Treating indirect jump as call
  initterm_e();
  return;
}



void __cdecl exit(int _Code)

{
                    // WARNING: Could not recover jumptable at 0x004072d1. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  exit(_Code);
  return;
}



void __cdecl _exit(int _Code)

{
                    // WARNING: Could not recover jumptable at 0x004072d7. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  _exit(_Code);
  return;
}



errno_t __cdecl _set_fmode(int _Mode)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x004072dd. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = _set_fmode(_Mode);
  return eVar1;
}



void __p___argc(void)

{
                    // WARNING: Could not recover jumptable at 0x004072e3. Too many branches
                    // WARNING: Treating indirect jump as call
  __p___argc();
  return;
}



void __p___argv(void)

{
                    // WARNING: Could not recover jumptable at 0x004072e9. Too many branches
                    // WARNING: Treating indirect jump as call
  __p___argv();
  return;
}



void __cdecl _cexit(void)

{
                    // WARNING: Could not recover jumptable at 0x004072ef. Too many branches
                    // WARNING: Treating indirect jump as call
  _cexit();
  return;
}



void __cdecl _c_exit(void)

{
                    // WARNING: Could not recover jumptable at 0x004072f5. Too many branches
                    // WARNING: Treating indirect jump as call
  _c_exit();
  return;
}



void __cdecl register_thread_local_exe_atexit_callback(void)

{
                    // WARNING: Could not recover jumptable at 0x004072fb. Too many branches
                    // WARNING: Treating indirect jump as call
  register_thread_local_exe_atexit_callback();
  return;
}



int __cdecl _configthreadlocale(int _Flag)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407301. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = _configthreadlocale(_Flag);
  return iVar1;
}



void __cdecl set_new_mode(void)

{
                    // WARNING: Could not recover jumptable at 0x00407307. Too many branches
                    // WARNING: Treating indirect jump as call
  set_new_mode();
  return;
}



void __p__commode(void)

{
                    // WARNING: Could not recover jumptable at 0x0040730d. Too many branches
                    // WARNING: Treating indirect jump as call
  __p__commode();
  return;
}



void __cdecl free_dbg(void)

{
                    // WARNING: Could not recover jumptable at 0x00407313. Too many branches
                    // WARNING: Treating indirect jump as call
  free_dbg();
  return;
}



errno_t __cdecl strcpy_s(char *_Dst,rsize_t _SizeInBytes,char *_Src)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407319. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = strcpy_s(_Dst,_SizeInBytes,_Src);
  return eVar1;
}



errno_t __cdecl strcat_s(char *_Dst,rsize_t _SizeInBytes,char *_Src)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040731f. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = strcat_s(_Dst,_SizeInBytes,_Src);
  return eVar1;
}



void __stdio_common_vsprintf_s(void)

{
                    // WARNING: Could not recover jumptable at 0x00407325. Too many branches
                    // WARNING: Treating indirect jump as call
  __stdio_common_vsprintf_s();
  return;
}



void __cdecl seh_filter_dll(void)

{
                    // WARNING: Could not recover jumptable at 0x0040732b. Too many branches
                    // WARNING: Treating indirect jump as call
  seh_filter_dll();
  return;
}



void __cdecl initialize_onexit_table(void)

{
                    // WARNING: Could not recover jumptable at 0x00407331. Too many branches
                    // WARNING: Treating indirect jump as call
  initialize_onexit_table();
  return;
}



void __cdecl register_onexit_function(void)

{
                    // WARNING: Could not recover jumptable at 0x00407337. Too many branches
                    // WARNING: Treating indirect jump as call
  register_onexit_function();
  return;
}



void __cdecl execute_onexit_table(void)

{
                    // WARNING: Could not recover jumptable at 0x0040733d. Too many branches
                    // WARNING: Treating indirect jump as call
  execute_onexit_table();
  return;
}



void __cdecl crt_atexit(void)

{
                    // WARNING: Could not recover jumptable at 0x00407343. Too many branches
                    // WARNING: Treating indirect jump as call
  crt_atexit();
  return;
}



void __cdecl crt_at_quick_exit(void)

{
                    // WARNING: Could not recover jumptable at 0x00407349. Too many branches
                    // WARNING: Treating indirect jump as call
  crt_at_quick_exit();
  return;
}



errno_t __cdecl _controlfp_s(uint *_CurrentState,uint _NewValue,uint _Mask)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040734f. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = _controlfp_s(_CurrentState,_NewValue,_Mask);
  return eVar1;
}



void terminate(void)

{
                    // WARNING: Could not recover jumptable at 0x00407355. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  terminate();
  return;
}



errno_t __cdecl
_wmakepath_s(wchar_t *_PathResult,size_t _SIZE,wchar_t *_Drive,wchar_t *_Dir,wchar_t *_Filename,
            wchar_t *_Ext)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040735b. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = _wmakepath_s(_PathResult,_SIZE,_Drive,_Dir,_Filename,_Ext);
  return eVar1;
}



errno_t __cdecl
_wsplitpath_s(wchar_t *_FullPath,wchar_t *_Drive,size_t _DriveSize,wchar_t *_Dir,size_t _DirSize,
             wchar_t *_Filename,size_t _FilenameSize,wchar_t *_Ext,size_t _ExtSize)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407361. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = _wsplitpath_s(_FullPath,_Drive,_DriveSize,_Dir,_DirSize,_Filename,_FilenameSize,_Ext,
                        _ExtSize);
  return eVar1;
}



errno_t __cdecl wcscpy_s(wchar_t *_Dst,rsize_t _SizeInWords,wchar_t *_Src)

{
  errno_t eVar1;
  
                    // WARNING: Could not recover jumptable at 0x00407367. Too many branches
                    // WARNING: Treating indirect jump as call
  eVar1 = wcscpy_s(_Dst,_SizeInWords,_Src);
  return eVar1;
}



BOOL IsProcessorFeaturePresent(DWORD ProcessorFeature)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040739d. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = IsProcessorFeaturePresent(ProcessorFeature);
  return BVar1;
}



undefined1 FUN_00407400(void)

{
  return 1;
}



undefined1 FUN_00407410(void)

{
  return 1;
}



undefined1 FUN_00407420(void)

{
  return 1;
}



undefined1 FUN_00407430(void)

{
  return 1;
}



undefined1 FUN_00407440(void)

{
  return 1;
}



undefined4 FUN_00407450(void)

{
  return 0;
}



void Unwind_00408930(void)

{
  int unaff_EBP;
  
  FID_conflict__CAtlWinModule(unaff_EBP + -0x30);
  return;
}



void Unwind_00408938(void)

{
  int unaff_EBP;
  
  FID_conflict__CAtlWinModule(unaff_EBP + -0x4c);
  return;
}



void Unwind_00408980(void)

{
  int unaff_EBP;
  
  ~CAssoc(*(int *)(unaff_EBP + -0x10));
  return;
}



void Unwind_004089b0(void)

{
  int unaff_EBP;
  
  FID_conflict__CAtlWinModule(*(int *)(unaff_EBP + -0x10));
  return;
}



