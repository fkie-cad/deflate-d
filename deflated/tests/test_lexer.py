"""Tests for the C lexer (scan / strip_comments)."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms.lexer import SegmentType, protected_line_edges, scan, string_is_terminated, strip_comments


def test_lexer_roundtrip() -> None:
    src = "a /* c */ \"s\" 'x' // line\nb\n"
    assert "".join(t for _, t in scan(src)) == src
    assert "line" not in strip_comments(src)
    # Valid char literals protect a '//' inside them.
    assert strip_comments("c = '/'; // x\n") == "c = '/'; \n"


def test_escaped_newline_string_is_single_segment() -> None:
    # In real C a newline inside a string is the escape \n (backslash + n), so the
    # literal stays on one physical line. It must be captured as one STRING segment,
    # escape and all, never split into a following CODE segment where transforms
    # would corrupt it.
    src = r'printf("line1\nline2");' + "\n"
    segs = scan(src)
    assert "".join(t for _, t in segs) == src  # round-trip
    assert [t for k, t in segs if k == SegmentType.STRING] == [r'"line1\nline2"']


def test_escaped_quote_inside_string_does_not_close() -> None:
    src = 's = "he said \\"hi\\"";\n'
    segs = scan(src)
    assert "".join(t for _, t in segs) == src
    assert [t for k, t in segs if k == SegmentType.STRING] == ['"he said \\"hi\\""']


def test_unterminated_string_freezes_from_the_quote() -> None:
    # A truncated literal (no closing quote, e.g. a clipped Binary Ninja URL)
    # leaves the string open at the newline. Everything from the quote to the
    # newline is frozen as one opaque STRING so the stray quote cannot cascade;
    # the unambiguous code before the quote (`x = `) stays CODE, and the next
    # line is ordinary CODE again.
    src = 'x = "https://truncated\nint y;\n'
    segs = scan(src)
    assert "".join(t for _, t in segs) == src  # round-trip
    assert (SegmentType.STRING, '"https://truncated') in segs
    assert any(k == SegmentType.CODE and t.strip() == "x =" for k, t in segs)
    assert any(k == SegmentType.CODE and "int y;" in t for k, t in segs)


def test_string_is_terminated() -> None:
    # A normally-closed literal ends on its own closing quote...
    assert string_is_terminated('"hi"')
    assert string_is_terminated(r'"he said \"hi\""')  # escaped inner quotes
    assert string_is_terminated('"line1\\nline2"')  # \n escape, still closed
    # ...frozen segments scan emits for malformed lines are not terminated.
    assert not string_is_terminated('"https://truncated')  # no closing quote
    assert not string_is_terminated('"File: "%n" here;')  # embedded-quote freeze
    assert not string_is_terminated('"')  # lone quote
    assert not string_is_terminated("code")  # not a string at all


def test_msvc_quoted_name() -> None:
    # MSVC C++ symbols contain a lone apostrophe (`vftable'`); it must NOT start a
    # char literal, or the rest of the line escapes every transform.
    src = "void *Animal::`vftable' = &sub_4010A0; // weak\n"
    assert "".join(t for _, t in scan(src)) == src
    out = transform(src, Tier.T3_CONTEXTUAL)
    assert "weak" not in out
    assert "sub_4010A0" not in out
    assert "vftable" in out


def test_line_comment_backslash_continuation() -> None:
    # A `//` comment ending in `\` continues onto the next line in C; that line
    # is comment, not code, so the scanner must not surface it as CODE.
    src = "a; // cont \\\nstill comment\nb;\n"
    kinds = {kind for kind, _ in scan(src)}
    assert "".join(t for _, t in scan(src)) == src  # roundtrip preserved
    assert "still comment" not in strip_comments(src)


# --- malformed strings (Binary Ninja: embedded / line-wrapped quotes) ---


def test_well_formed_code_has_no_frozen_lines() -> None:
    # Every literal closes on its own line, so none is frozen: no STRING segment
    # spans a newline.
    src = 'int f(void) {\n  char *s = "hi";\n  return 0;\n}\n'
    assert all("\n" not in t for k, t in scan(src) if k == SegmentType.STRING)


def test_embedded_quote_line_is_byte_preserved_under_t1() -> None:
    # A string with an unescaped embedded quote leaves the lexer unsure where it
    # ends; T1 must not edit (collapse the double space in) the affected bytes.
    src = 'data = "[.?!][]"\\)[ \\t]*  end";\n'
    out = transform(src, Tier.T1_COSMETIC)
    assert "  end" in out  # the run of two spaces inside the literal survives


def test_unterminated_string_freeze_is_line_local() -> None:
    # Binary Ninja emits unescaped embedded quotes, leaving a string "open" at the
    # physical line end. The freeze covers the quote region (first quote -> line
    # end) so its interleaved quotes are never trusted, while the following lines
    # of real code are NOT swallowed (the old cascade bug) and their placeholders
    # still compress. The unambiguous `rdi = ` prefix stays ordinary code.
    frozen = '"File: "%n" here;'  # from the first quote through the line end
    src = "rdi = " + frozen + "\nv1 = sub_401abc(data_40c0);\n"
    assert (SegmentType.STRING, frozen) in scan(src)  # quote region frozen as one STRING
    out = transform(src, Tier.T3_CONTEXTUAL)
    assert "sub_401abc" not in out  # second line was reached by compress-funcs
    assert "data_40c0" not in out  # ...and by compress-names (no cascade)


def test_genuine_multiline_string_concatenation_not_split() -> None:
    # Adjacent string-literal concatenation across lines is valid C: each literal
    # is closed on its own line, so none is "open" at a break and nothing freezes.
    src = 'char *s =\n    "line one "\n    "line two";\n'
    strings = [t for k, t in scan(src) if k == SegmentType.STRING]
    assert strings == ['"line one "', '"line two"']  # two separate literals, none frozen
    out = transform(src, Tier.T1_COSMETIC)
    assert '"line one "' in out and '"line two"' in out


def test_scan_roundtrips_malformed_string() -> None:
    src = 'a = "x"y"z";\nb = "FILE\n exist";\n'
    assert "".join(t for _, t in scan(src)) == src


# --- inline asm (IDA/Hex-Rays `__asm { ... }`) ---


def test_asm_block_is_opaque_segment() -> None:
    # Both the single-line and brace-on-next-line forms are one ASM segment, so no
    # transform reaches their register/stack operands.
    for src in ("__asm { vmovdqa xmm4, [rsp+var_28] }", "__asm\n{\n  cpuid\n}"):
        asm = [t for k, t in scan(src) if k == SegmentType.ASM]
        assert asm == [src]
        assert "".join(t for _, t in scan(src)) == src  # roundtrip


def test_asm_substring_in_identifier_not_matched() -> None:
    # `__asm` only matches as a whole token, and only when a `{` block follows.
    assert not any(k == SegmentType.ASM for k, _ in scan("int my__asm = 1;"))
    assert not any(k == SegmentType.ASM for k, _ in scan("__asmfoo();"))
    assert not any(k == SegmentType.ASM for k, _ in scan("x = __asm + 1;"))


def test_protected_line_edges_marks_asm_interior() -> None:
    # An `__asm { ... }` block is a frozen opaque region, so its interior lines
    # must report as protected (like a multi-line string) --- otherwise the
    # line-oriented cosmetic passes would de-indent its assembly operands.
    src = "x = 1;\n__asm\n{\n  vmovdqa xmm7, foo\n}\ny = 2;\n"
    edges = protected_line_edges(src)
    lines = src.split("\n")
    assert lines[0] == "x = 1;" and edges[0] == (False, False)  # plain code
    assert lines[3] == "  vmovdqa xmm7, foo" and edges[3] == (True, True)  # asm interior


def test_t1_preserves_asm_block_interior() -> None:
    # Regression: the line-oriented T1 passes (ws-indent/-trailing/-blanklines)
    # once de-indented `__asm` interiors because `protected_line_edges` only
    # guarded string/char literals. The assembly text must survive T1 verbatim.
    src = "void f(){\n  __asm\n    {\n      vmovdqa xmm7, cs:foo\n    }\n  x = 1;\n}\n"
    out = transform(src, Tier.T1_COSMETIC)
    assert "      vmovdqa xmm7, cs:foo" in out


def test_t1_keeps_do_keyword_off_asm_block() -> None:
    # Regression: a `do` immediately before an `__asm { ... }` block was glued by
    # ws-tighten into the identifier `do__asm`, which destroyed the `do` keyword
    # and de-protected the asm block on the next scan (its operands were then
    # reflowed, making T2/T3 non-idempotent). The `__asm` block must stay one
    # opaque segment through a full T2 pass.
    src = "void f(){\n  do\n    __asm\n    {\n      nop\n    }\n  while (c);\n}\n"
    out = transform(src, Tier.T2_STRUCTURAL)
    assert "do__asm" not in out
    asm = [t for k, t in scan(out) if k == SegmentType.ASM]
    assert len(asm) == 1 and "nop" in asm[0]
    # And the whole thing is idempotent under T2.
    assert transform(out, Tier.T2_STRUCTURAL) == out
