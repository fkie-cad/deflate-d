# DEFLATE-D transform reference

The full per-transform reference and scope notes for DEFLATE-D. For the project
overview, install, and library/CLI quickstart, see the
[top-level README](../README.md).

Transforms are grouped into cumulative tiers (T2 ⊇ T1, T3 ⊇ T2, T4 ⊇ T3),
ordered by information loss. Cosmetic normalization always runs last so it tidies
up after the structural/contextual edits. The T3/T4 split separates lossy edits
that only discard decompiler bookkeeping (placeholder names that encode
addresses/offsets, type-spelling verbosity, with meaning preserved and kept
self-consistent) from edits that throw away genuine analyst hints (ABI/calling-
convention keywords, decompiler `/* WARNING */` banners). T3 is the recommended
default; T4 is opt-in for the most aggressive cost reduction.

Every transform has a stable `id` (use it with `--exclude`); the CLI prints this
same list via `--list` / `--list-verbose`.

## T1: Cosmetic (semantics-preserving)

| id | what it does |
|----|--------------|
| `ws-collapse` | Collapse any combination of 2+ spaces/tabs into a single space in code. |
| `ws-indent` | Remove leading whitespace from each line. |
| `ws-trailing` | Remove trailing whitespace from each line. |
| `ws-blanklines` | Collapse consecutive blank lines to one and drop leading/trailing blanks. |
| `ws-newlines` | Join lines into as few physical lines as possible, replacing all non-significant line breaks with a single space. |
| `ws-comments` | Strip and collapse whitespace inside comments. |
| `ws-tighten` | Remove unnecessary whitespace (includes most of `ws-collapse`, `ws-indent`, `ws-trailing`). |

## T2: Structural (semantics-preserving)

These rewrites leave the rendering's C semantics unchanged. The one boundary case
is the `comments` pass, which drops auto-generated address/storage metadata
(keeping warning banners); this is the single point where T2 is
semantics-preserving but not information-preserving.

| id | what it does |
|----|--------------|
| `flag-temps` | Normalize Binary Ninja colon-flag temporaries into plain identifiers. |
| `comments` | Remove auto-generated address and storage-location comments, keeping warning banners. |
| `ternary` | Fold a same-target if/else assignment into a ternary. |
| `inline-temps` | Inline a single-use spill temporary into its return. |
| `cast-elision` | Collapse stacked identical casts. |
| `brace-elision` | Drop braces around a single-statement control block (if/else/for/while/do). |
| `compound-assign` | Fold an expanded assignment into compound form. |
| `cfg-canon` | Remove no-op gotos and unreferenced labels. |
| `int-minform` | Re-spell a hex literal in decimal when shorter. |
| `deref-offset` | Rewrite a dereferenced pointer-add as a subscript. |
| `drop-trailing-return` | Drop a redundant trailing return at the end of a function body. |
| `decl-coalesce` | Merge same-type uninitialized declarations into one statement. |

## T3: Contextual (discards decompiler bookkeeping)

| id | what it does |
|----|--------------|
| `compress-funcs` | Rename address-placeholder function names across the unit, keeping real wrapped symbols. |
| `compress-names` | Remap placeholder locals, labels, and globals to the shortest collision-free tokens. |
| `simplify-types` | Re-spell verbose width types to compact aliases where it reduces tokens. |
| `null-cast` | Drop a redundant pointer cast on a null constant. |
| `addr-of-index` | Rewrite the address-of-a-literal-index idiom to a pointer add. |
| `strip-ptr-addr` | Drop the `.got.plt` slot address from a recovered import pointer name. |
| `piece-access` | Drop the trailing separator of a Ghidra piece access. |

## T4: Reductive (discards low-confidence analyst signal)

| id | what it does |
|----|--------------|
| `comments-warning` | Remove the decompiler's WARNING unreliability banners. |
| `strip-callconv` | Remove calling-convention and ABI keywords. |
| `strip-const` | Remove the low-signal `const` Binary Ninja recovers on most pointer parameters. |
| `strip-i18n` | Unwrap a `gettext`-family lookup to its message string. |
| `strip-width-cast` | Remove Hex-Rays pseudo-width casts, keeping load-bearing pointer casts. |
| `drop-code-cast` | Drop Ghidra's `(code *)` cast on an indirect call. |
| `strip-chk` | Strip glibc's `_chk` FORTIFY suffix. |
| `thunk-elision` | Collapse a forwarding import trampoline to its prototype. |
| `trim-spurious-args` | Truncate spilled surplus arguments on curated fixed-arity libc calls. |
| `drop-resolver-stubs` | Delete Binary Ninja lazy-binding resolver-stub families. |
| `drop-crt` | Delete C-runtime and ELF scaffolding functions. |

## Scope and limitations

- `simplify-types` ships a
  fixed vocabulary of decompiler type spellings whose compaction reduces tokens
  on the GPT, Claude, and Gemini tokenizers without ever
  increasing any (IDA `__intN`/`_QWORD`, Binary Ninja `intN_t`/`uintN_t`,
  Ghidra `undefined1`); `compress-names` covers Ghidra/IDA/Binary Ninja locals
  (including Ghidra's typedef-prefixed `Var`/`Stack` forms and `stack0x` slots),
  labels, global-data placeholders (Ghidra `DAT_`/`PTR_DAT_`, IDA
  `dword_`/`unk_`/`byte_`/`off_`/..., Binary Ninja `data_`/`jump_table_`), and
  register-derived temporaries (and Ghidra's prefix-less `VarN`);
  `compress-funcs` additionally folds Ghidra's address-named `Unwind_` handlers.
- **Inline asm is opaque.** IDA/Hex-Rays `__asm { ... }` blocks are segmented out
  by the lexer, so no pass renames their hardware registers / stack aliases or
  reflows their operands. Likewise a string left unterminated by a decompiler's
  unescaped embedded quote (Binary Ninja) is frozen *per physical line* only, so
  the malformed line is byte-preserved without the freeze cascading over the
  following real code.
- **Genuinely out of scope (need a CFG / bit-width semantics, not text
  rewriting):** `goto`-to-structured-control reconstruction, block
  de-duplication, and Ghidra p-code intrinsic normalization
  (`CONCAT`/`SUB`/`ZEXT`/`SEXT`).
