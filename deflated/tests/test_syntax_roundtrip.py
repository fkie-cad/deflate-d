"""Syntax round-trip: whatever T1/T2 emit must still be compilable C.

T1 and T2 are the *lossless* tiers --- they promise to change only how the code
looks, never what it means. The cheapest independent judge of "still valid C" we
can reach for is a real compiler, so this module feeds the transformed text back
to ``gcc -fsyntax-only -w`` and demands it parse. ``-w`` because decompiler
output is a swamp of legitimate warnings (implicit conversions, unused values)
that say nothing about the transform; only a hard parse error is a verdict here.

Decompiler output is not self-contained C: it names types the decompiler invents
(``undefined8``, ``code``, ``_DWORD``) and calls functions it never declares. So
every compile is prefixed with :data:`PRELUDE`, which supplies exactly those two
missing things and nothing else.

The method matters more than the assertions. Compiling transformed output only
*means* something if the untransformed input compiled first --- otherwise a pass
could emit rubble and the test would blame the sample. Several corpus files are
therefore skipped, and deliberately so: they are decompiler artifacts (C++
mangled names, ``#include``s we do not have) or intentionally malformed fixtures
that exist precisely to prove the lexer survives broken input. Which files those
are, and why, is pinned in :data:`RAW_UNCOMPILABLE`, and
``test_raw_corpus_split_is_as_documented`` re-derives that table from gcc on
every run. That test is the tripwire: if the prelude rots or gcc stops being
invoked, the round-trip tests would quietly degrade into skips, but the tripwire
fails loudly instead of letting the suite pass on nothing.

The file corpus alone exercises only the shapes the samples happen to contain,
which is why :data:`CONTROL_FLOW_SNIPPETS` adds a few minimal functions covering
the control-flow forms the structural passes rewrite. That is where bug 1.1
(``drop-trailing-return`` eating a ``return;`` that is an ``if``/``else`` body,
leaving ``if(c)}``) actually shows up; see :data:`XFAIL_RETURN_IN_BRANCH`.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from deflated.transforms import build_pipeline

# A compiler is optional tooling, not a dependency of the package, so the whole
# module stands down rather than failing where gcc is absent.
pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc not available; cannot syntax-check output")

SAMPLES = Path(__file__).parent / "samples"
EXAMPLES = Path(__file__).parent.parent / "examples"

# Only the lossless tiers are held to this standard. T3/T4 are allowed to drop
# declarations and whole statements, so their output is not expected to parse.
LOSSLESS_TIERS = ["T1", "T2"]

# The two things decompiler output assumes and never provides: its invented
# scalar types, and prototypes for the callees it references. Signatures are
# spelled out rather than left empty because C23 reads `f()` as `f(void)`, which
# would reject every call with arguments.
PRELUDE = """\
/* Ghidra's synthesized scalars. `code` is the element type of a function
   pointer, so `void` makes `code *` work without inventing a signature. */
typedef unsigned char undefined;
typedef unsigned char undefined1;
typedef unsigned short undefined2;
typedef unsigned int undefined4;
typedef unsigned long long undefined8;
typedef unsigned char byte;
typedef unsigned short ushort;
typedef unsigned int uint;
typedef unsigned long ulong;
typedef void code;

/* Hex-Rays' width aliases. */
typedef unsigned char _BYTE;
typedef unsigned short _WORD;
typedef unsigned int _DWORD;
typedef unsigned long long _QWORD;

/* Callees referenced by the corpus but never declared in it. */
int puts(const char *);
int printf(const char *, ...);
int validate_entry(long);
uint compute_hash(char *, char *);
"""

# Corpus files whose *raw* text gcc rejects, with the reason. Excluded on
# purpose: there is no transform that could make these parse, so demanding it of
# the output would only produce a permanently red test. Keeping the reasons here
# rather than in a bare skip list means a file silently becoming uncompilable
# (or newly compilable) is caught by test_raw_corpus_split_is_as_documented.
RAW_UNCOMPILABLE: dict[str, str] = {
    # Intentionally malformed fixtures --- the point of these samples is that the
    # lexer freezes the broken region instead of cascading, so they can never be
    # valid C by construction.
    "unclosed_string.c": "truncated string literal: missing terminating quote",
    "embedded_quote.c": "Binary Ninja's unescaped embedded quotes break the line's quoting",
    # Genuine decompiler output that is simply not C.
    "quoted_name_and_char.c": "MSVC C++ qualified name with a backtick (Animal::`vftable')",
    "vtables_ghidra.c": 'includes "out.h" (Ghidra type header, not shipped)',
    "vtables_hexrays.c": "includes <windows.h> and <defs.h>, plus C++ qualified names",
    "vtables_binja.c": "C++ qualified names and register annotations (int64_t arg1 @ xcr0)",
}

CORPUS: list[Path] = [
    EXAMPLES / "ghidra_sample.c",
    EXAMPLES / "vtables_ghidra.c",
    EXAMPLES / "vtables_hexrays.c",
    EXAMPLES / "vtables_binja.c",
    SAMPLES / "comment_like_string.c",
    SAMPLES / "embedded_quote.c",
    SAMPLES / "newline_in_string.c",
    SAMPLES / "quoted_name_and_char.c",
    SAMPLES / "string_concat.c",
    SAMPLES / "unclosed_string.c",
]

# Minimal functions in decompiler dialect, one per control-flow shape that the
# structural passes (brace-elision, drop-trailing-return, ternary, compound
# assignment) rewrite. The file corpus contains almost none of these, so without
# them the round-trip test would compile four tidy samples and prove very little.
CONTROL_FLOW_SNIPPETS: dict[str, str] = {
    "return_in_if": 'void f(int c)\n\n{\n  puts("x");\n  if (c != 0) {\n    return;\n  }\n}\n',
    "return_in_else": ('void f(int c)\n\n{\n  if (c != 0) {\n    puts("a");\n  }\n  else {\n    return;\n  }\n}\n'),
    "return_in_while": "void f(int c)\n\n{\n  while (c != 0) {\n    c = c + -1;\n    return;\n  }\n}\n",
    "for_loop": (
        "void f(int c)\n\n{\n  int iVar1;\n" '  for (iVar1 = 0; iVar1 < c; iVar1 = iVar1 + 1) {\n    puts("y");\n  }\n  return;\n}\n'
    ),
    "do_while": "void f(int c)\n\n{\n  do {\n    c = c + -1;\n  } while (c != 0);\n  return;\n}\n",
    "switch": (
        "void f(int c)\n\n{\n  switch(c) {\n" '  case 1:\n    puts("a");\n    break;\n  default:\n    puts("b");\n  }\n  return;\n}\n'
    ),
    "if_else_assign": (
        "undefined4 f(int c)\n\n{\n  undefined4 uVar1;\n"
        "  if (c != 0) {\n    uVar1 = 1;\n  }\n  else {\n    uVar1 = 2;\n  }\n  return uVar1;\n}\n"
    ),
    "goto_label": ('void f(int c)\n\n{\n  if (c != 0) goto LAB_1;\n  puts("a");\nLAB_1:\n  return;\n}\n'),
    # CODE_REVIEW 1.8: `0xFE-1` lexes as one invalid number. Only T1 can fail, since `int-minform` rewrites `0xFE` at T2.
    "hex_e_constant": "uint f(uint c)\n\n{\n  return c + 0xFE - 1;\n}\n",
}

# CODE_REVIEW 1.1: brace-elision strips the braces, then drop-trailing-return
# removes the now-bare `return;` that was the whole body of the branch, leaving
# `if(c!=0)}` / `else}`. Non-strict so the suite stays green until 1.1 is fixed,
# at which point these turn into XPASS and the marks can go.
XFAIL_RETURN_IN_BRANCH = {("return_in_if", "T2"), ("return_in_else", "T2")}


def syntax_check(source: str, tmp_path: Path) -> tuple[bool, str]:
    """Prepend :data:`PRELUDE` to ``source`` and parse it; return (ok, stderr)."""
    # One translation unit: concatenation is safe only because no file we compile
    # has #include lines of its own (those are all in RAW_UNCOMPILABLE).
    unit = tmp_path / "unit.c"
    unit.write_text(PRELUDE + source + "\n", encoding="utf-8")
    proc = subprocess.run(
        ["gcc", "-fsyntax-only", "-w", str(unit)],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0, proc.stderr


def _snippet_params() -> Iterator[pytest.ParameterSet]:
    for name, src in CONTROL_FLOW_SNIPPETS.items():
        for tier in LOSSLESS_TIERS:
            marks = (
                [pytest.mark.xfail(reason="CODE_REVIEW 1.1 drop-trailing-return", strict=False)]
                if (name, tier) in XFAIL_RETURN_IN_BRANCH
                else []
            )
            yield pytest.param(src, tier, id=f"{name}-{tier}", marks=marks)


# --- the tripwire: the raw corpus is exactly as documented ---


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.name)
def test_raw_corpus_split_is_as_documented(path: Path, tmp_path: Path) -> None:
    # Guards the guard. The round-trip test below skips anything in
    # RAW_UNCOMPILABLE, so if the prelude lost a typedef (or gcc stopped running
    # at all) every file would land in that bucket and the suite would go green
    # having compiled nothing. Asserting the split in both directions makes that
    # failure mode impossible to miss.
    ok, stderr = syntax_check(path.read_text(encoding="utf-8"), tmp_path)
    if path.name in RAW_UNCOMPILABLE:
        assert not ok, f"{path.name} now compiles raw; drop it from RAW_UNCOMPILABLE " f"(recorded reason: {RAW_UNCOMPILABLE[path.name]})"
    else:
        assert ok, f"{path.name} no longer compiles raw --- the prelude is incomplete:\n{stderr}"


def test_at_least_one_sample_is_actually_compiled() -> None:
    # A round-trip suite that skipped everything would pass while testing nothing.
    assert set(RAW_UNCOMPILABLE) < {p.name for p in CORPUS}


# --- the round trip itself ---


@pytest.mark.parametrize("tier", LOSSLESS_TIERS)
@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.name)
def test_lossless_tier_output_still_parses(path: Path, tier: str, tmp_path: Path) -> None:
    # The lossless guarantee in its bluntest form: if gcc accepted the input, it
    # must accept the output. Only meaningful for inputs gcc accepted, hence the
    # skip --- see RAW_UNCOMPILABLE for why each skipped file can never parse.
    if path.name in RAW_UNCOMPILABLE:
        pytest.skip(f"raw sample is not valid C: {RAW_UNCOMPILABLE[path.name]}")
    out = build_pipeline(tier).apply(path.read_text(encoding="utf-8"))
    ok, stderr = syntax_check(out, tmp_path)
    assert ok, f"{path.name} [{tier}] produced invalid C:\n{stderr}\n--- output ---\n{out}"


@pytest.mark.parametrize(("src", "tier"), list(_snippet_params()))
def test_control_flow_snippet_survives_lossless_tier(src: str, tier: str, tmp_path: Path) -> None:
    # Same contract on hand-written shapes. The raw assert is not ceremony: a
    # typo in the snippet would otherwise read as a transform bug.
    raw_ok, raw_stderr = syntax_check(src, tmp_path)
    assert raw_ok, f"snippet is not valid C to begin with:\n{raw_stderr}"
    out = build_pipeline(tier).apply(src)
    ok, stderr = syntax_check(out, tmp_path)
    assert ok, f"[{tier}] produced invalid C:\n{stderr}\n--- output ---\n{out}"
