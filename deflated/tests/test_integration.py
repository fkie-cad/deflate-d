"""End-to-end integration tests: real .c sample files driven through the CLI.

Each file in ``samples/`` is a small, realistic piece of decompiler output that
exercises a tricky lexical case --- ``\\n``/``\\t`` escapes inside strings, an
unclosed (truncated) string, Binary Ninja's unescaped embedded quotes, string
content that *looks* like ``//`` or ``/* */`` comments, adjacent string-literal
concatenation, and MSVC quoted names / char literals.

The samples are fed through the actual ``reformat`` CLI (``main``, which reads
the file from disk and writes the transformed result to stdout) at real tiers,
so the whole assembled pipeline runs. The point is to prove two things on
genuine multi-pass input:

* literal/comment content is never corrupted even as the names, whitespace, and
  structure *around* it get compressed, and
* a malformed string is frozen line-locally --- it never cascades into and
  swallows the real code that follows it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deflated.reformat import main
from deflated.transforms.lexer import SegmentType, scan

SAMPLES = Path(__file__).parent / "samples"

ALL_SAMPLES = [
    "newline_in_string.c",
    "unclosed_string.c",
    "embedded_quote.c",
    "comment_like_string.c",
    "string_concat.c",
    "quoted_name_and_char.c",
]


def run(capsys, name: str, tier: str, *, exclude: str | None = None) -> str:
    """Run the CLI on ``samples/<name>`` at ``tier`` and return its stdout."""
    argv = ["--tier", tier]
    if exclude:
        argv += ["--exclude", exclude]
    argv.append(str(SAMPLES / name))
    assert main(argv) == 0
    return capsys.readouterr().out


def literals(name: str) -> list[str]:
    """Every string/char literal (incl. frozen regions) in the source file."""
    src = (SAMPLES / name).read_text()
    return [text for kind, text in scan(src) if kind in (SegmentType.STRING, SegmentType.CHAR)]


# --- core guarantee: literals are byte-preserved at every tier ---


@pytest.mark.parametrize("tier", ["T1", "T2", "T3", "T4"])
@pytest.mark.parametrize("name", ALL_SAMPLES)
def test_every_literal_survives_verbatim(capsys, name: str, tier: str) -> None:
    # Whatever the lexer classifies as a string/char literal in the source must
    # appear unchanged in the output --- no pass may edit a single byte of it.
    out = run(capsys, name, tier)
    for lit in literals(name):
        assert lit in out, f"{name} [{tier}] lost literal {lit!r}"


# --- per-sample behavior ---


def test_newline_escapes_survive_while_names_compress(capsys) -> None:
    # T1 leaves names alone; T3 compresses them. The \n / \t escapes inside both
    # string literals stay byte-identical regardless.
    t1 = run(capsys, "newline_in_string.c", "T1")
    assert "FUN_00401000" in t1 and "local_18" in t1 and "param_1" in t1

    t3 = run(capsys, "newline_in_string.c", "T3")
    assert "FUN_00401000" not in t3 and "local_18" not in t3 and "param_1" not in t3
    assert "void a(int b)" in t3  # names actually compressed

    for out in (t1, t3):
        assert r'"Error: code %d\nRetrying...\n"' in out
        assert r'"value = %d\ttag = %s\n"' in out


def test_truncated_string_freezes_without_cascading(capsys) -> None:
    # An unclosed (truncated) literal is frozen verbatim, but the real code on the
    # lines *after* it must still be reached and compressed --- the old cascade
    # bug would have swallowed it into the runaway string.
    t3 = run(capsys, "unclosed_string.c", "T3")
    assert '"https://example.com/very/long/path/that/got/truncated' in t3
    # the newline bounding the frozen line is kept: the broken string content is
    # not glued onto the next statement (no "truncatede = ...").
    assert "truncated\n" in t3
    assert "truncatede" not in t3
    for placeholder in ("FUN_00402000", "sub_403000", "uVar2", "param_1"):
        assert placeholder not in t3, f"cascade: {placeholder} not compressed"


def test_embedded_quote_freeze_is_line_local(capsys) -> None:
    # Binary Ninja's unescaped embedded quotes leave the line's quote structure
    # untrustworthy. The quote region is frozen, but the unambiguous code before
    # the first quote still tightens, and the following lines still compress.
    t1 = run(capsys, "embedded_quote.c", "T1")
    assert "rdi=" in t1  # code before the first quote stays code and tightens
    assert '"File: "%n" here;\n' in t1

    t3 = run(capsys, "embedded_quote.c", "T3")
    assert '"File: "%n" here;\n' in t3
    for placeholder in ("sub_401abc", "sub_402000", "data_40c0", "uVar1"):
        assert placeholder not in t3, f"cascade: {placeholder} not compressed"


def test_comment_markers_inside_string_are_not_removed(capsys) -> None:
    # `//` and `/* */` inside a string are content, so comment removal (T2+) must
    # leave them --- while a genuine trailing comment on the same statement goes.
    content = '"scheme://host  // not a comment  /* nor this */"'

    t1 = run(capsys, "comment_like_string.c", "T1")
    assert content in t1
    assert "real trailing comment\n" in t1  # T1 is cosmetic: comments survive
    assert t1.count("\n") == 1

    t3 = run(capsys, "comment_like_string.c", "T3")
    assert content in t3  # the comment-looking string bytes are untouched
    assert "real trailing comment" not in t3  # the real comment is removed
    assert t3.count("\n") == 0


def test_adjacent_string_concatenation_preserved(capsys) -> None:
    # Two adjacent literals across lines are valid C concatenation: each closes on
    # its own line, so both survive and the spill variable compresses around them.
    t3 = run(capsys, "string_concat.c", "T3")
    assert '"DEFLATE-D "' in t3 and r'"ready\n"' in t3
    assert "pcVar1" not in t3


def test_quoted_name_char_literals_and_warning_tier(capsys) -> None:
    # A MSVC `vftable'` apostrophe is not a char literal; real char literals and
    # the address placeholder around it are handled correctly. The WARNING banner
    # is analyst signal kept through T3 and only dropped at T4.
    t3 = run(capsys, "quoted_name_and_char.c", "T3")
    assert "Animal::`vftable'" in t3  # lone apostrophe left as code
    assert "sub_4010A0" not in t3  # the genuine placeholder is compressed
    assert "'/'" in t3 and r"'\n'" in t3  # char literals intact
    assert "param_1" not in t3  # parameter renamed
    assert "WARNING" in t3  # banner survives T3

    t4 = run(capsys, "quoted_name_and_char.c", "T4")
    assert "WARNING" not in t4  # T4 strips the banner
    assert "'/'" in t4 and r"'\n'" in t4  # ...but still never touches literals


# --- config options (--tier, --exclude) genuinely change the run ---


def test_exclude_keeps_names_but_still_protects_string(capsys) -> None:
    # --exclude drops a single pass: without compress-names the local/param
    # placeholders remain, yet compress-funcs still renames the function and the
    # string literal is protected either way.
    out = run(capsys, "newline_in_string.c", "T3", exclude="compress-names")
    assert "local_18" in out and "param_1" in out  # compress-names skipped
    assert "FUN_00401000" not in out  # compress-funcs still ran
    assert r'"Error: code %d\nRetrying...\n"' in out
    assert r'"value = %d\ttag = %s\n"' in out


def test_tiers_monotonically_shrink_on_a_real_function(capsys) -> None:
    # Each higher tier is at least as aggressive: output size never grows.
    sizes = [len(run(capsys, "newline_in_string.c", t)) for t in ("T1", "T2", "T3", "T4")]
    assert all(a >= b for a, b in zip(sizes, sizes[1:]))
