/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined8 process_record(long param_1,int param_2)

{
  int iVar1;
  uint uVar2;
  char *pcVar3;
  undefined8 uVar4;
  long local_28;
  uint local_1c;

  local_1c = 0;
  local_28 = param_1;
  if (param_2 < 1) {
    uVar4 = 0xffffffffffffffff;
  }
  else {
    do {
      iVar1 = validate_entry(local_28);          // checks the header
      if (iVar1 == 0) {
        pcVar3 = (char *)(local_28 + 8);
        uVar2 = compute_hash(pcVar3,"  seed//x");  // string keeps its spaces + slashes
        local_1c = local_1c + uVar2;
      }
      local_28 = local_28 + 0x18;
      param_2 = param_2 + -1;
    } while (param_2 != 0);
    uVar4 = (undefined8)local_1c;
  }
  return uVar4;
}
