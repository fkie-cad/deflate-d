"""Tests for the C lexer."""

from __future__ import annotations

from deflated import Tier, transform
from deflated.transforms.lexer import (
    SegmentType,
    map_code,
    protected_line_ends,
    scan,
    string_is_terminated,
    strip_comments,
)


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


def test_escaped_backslash_before_quote_closes_string() -> None:
    # In `"a\\"` the `\\` is an escaped backslash, so the following `"` closes the string.
    src = r's = "a\\"; t = "b";'
    assert scan(src) == [
        (SegmentType.CODE, "s = "),
        (SegmentType.STRING, r'"a\\"'),
        (SegmentType.CODE, "; t = "),
        (SegmentType.STRING, '"b"'),
        (SegmentType.CODE, ";"),
    ]
    assert string_is_terminated(r'"a\\"')
    assert not string_is_terminated(r'"a\\\"')  # `\\` then `\"`: the quote is escaped
    assert string_is_terminated(r'"a\" something b"')  # `\"` stays inside, the last `"` closes
    assert [t for k, t in scan(r'x = "a\" something b";') if k == SegmentType.STRING] == [r'"a\" something b"']


def test_crlf_line_continuation() -> None:
    # A `\` before a Windows line ending continues a line comment or string just like before `\n`.
    comment_src = "// a \\\r\n b\r\nint x;"
    assert scan(comment_src)[0] == (SegmentType.LINE_COMMENT, "// a \\\r\n b")
    string_src = 's = "a \\\r\n b";\r\n'
    assert [t for k, t in scan(string_src) if k == SegmentType.STRING] == ['"a \\\r\n b"']


def test_unterminated_block_comment_runs_to_end() -> None:
    # Unlike a string, a block comment may span lines, so there is no line end to stop at: an unclosed `/*` runs to
    # the end of the input, as in C.
    src = "x = 1; /* never closed\nreturn x;\n}"
    segs = scan(src)
    assert "".join(t for _, t in segs) == src
    assert segs == [(SegmentType.CODE, "x = 1; "), (SegmentType.BLOCK_COMMENT, "/* never closed\nreturn x;\n}")]


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
    assert string_is_terminated('"a \\\nb"')  # `\`-newline continuation, closed on the next line
    assert not string_is_terminated('"abc\\')  # trailing `\` escapes past the end
    assert not string_is_terminated('"a\\"')  # the only closing quote is escaped


def test_crlf_line_comment_keeps_line_ending() -> None:
    # The `\r` of a `\r\n` belongs to the line ending, so stripping the comment keeps CRLF line endings intact.
    assert scan("// c\r\nx;") == [(SegmentType.LINE_COMMENT, "// c"), (SegmentType.CODE, "\r\nx;")]
    assert strip_comments("// c\r\nx;") == "\r\nx;"


def test_slash_operators_are_not_comments() -> None:
    assert scan("x = a / b; y /= c;") == [(SegmentType.CODE, "x = a / b; y /= c;")]


def test_apostrophe_inside_string_is_not_a_char() -> None:
    assert scan("""s = "it's"; c = 'a';""") == [
        (SegmentType.CODE, "s = "),
        (SegmentType.STRING, '"it\'s"'),
        (SegmentType.CODE, "; c = "),
        (SegmentType.CHAR, "'a'"),
        (SegmentType.CODE, ";"),
    ]


def test_strip_comments_keep_warnings() -> None:
    src = "/* WARNING: bad stack */ x; /* note */ y; // WARNING line\n"
    assert strip_comments(src, keep_warnings=True) == "/* WARNING: bad stack */ x;   y; \n"
    assert strip_comments(src) == "  x;   y; \n"


def test_map_code_edits_only_code() -> None:
    src = "a = \"a\"; // a\nb = 'a'; /* a */"
    assert map_code(src, str.upper) == "A = \"a\"; // a\nB = 'a'; /* a */"

def test_msvc_quoted_name() -> None:
    # MSVC C++ symbols contain a lone apostrophe (`vftable'`); it must NOT start a
    # char literal, or the rest of the line escapes every transform.
    src = "void *Animal::`vftable' = &sub_4010A0; // weak\n"
    assert "".join(t for _, t in scan(src)) == src
    out = transform(src, Tier.T3_CONTEXTUAL)
    assert "weak" not in out
    assert "sub_4010A0" not in out
    assert "vftable" in out


def test_multichar_constant_is_a_char_segment() -> None:
    # Multi-char constants ('ABCD', an int magic value) are common in decompiler
    # output; they must be one CHAR segment, not code, or transforms rewrite them.
    assert (SegmentType.CHAR, "'ABCD'") in scan("x = 'ABCD';")


def test_msvc_quoted_name_does_not_pair_with_later_char() -> None:
    # The lone `'` closing `vftable' must not open a multi-char constant that
    # runs to the next `'` on the line, hiding the code in between.
    segs = scan("p = &Foo::`vftable'; c = 'A';")
    assert segs[0] == (SegmentType.CODE, "p = &Foo::`vftable'; c = ")
    assert (SegmentType.CHAR, "'A'") in segs


def test_backtick_in_string_or_comment_does_not_hide_char() -> None:
    # Regression: a backtick inside a string or block comment was taken as an open MSVC name, so the next char
    # literal on the line was treated as code and its contents rewritten.
    for src in ("s = \"`ls`\"; c = ' ';", "/* `x */ c = ' ';"):
        assert (SegmentType.CHAR, "' '") in scan(src)
        assert "' '" in transform(src + "\n", Tier.T1_COSMETIC)


def test_line_comment_backslash_continuation() -> None:
    # A `//` comment ending in `\` continues onto the next line in C; that line
    # is comment, not code, so the scanner must not surface it as CODE.
    src = "a; // cont \\\nstill comment\nb;\n"
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


def test_unterminated_string_freeze_swallows_earlier_segments_on_its_line() -> None:
    # Before reaching the unclosed `"c`, scan has already emitted the segments of this line:
    #   CODE 'x = ', STRING '"a"', CODE ' + ', CHAR "'b'"   (and ' + ' is pending code)
    # The freeze moves back to the line's first string `"a"`, pops everything emitted from there on, and emits the
    # whole rest of the line as one STRING. Only the code before the first string survives.
    src = "x = \"a\" + 'b' + \"c\ny;"
    assert scan(src) == [
        (SegmentType.CODE, "x = "),
        (SegmentType.STRING, "\"a\" + 'b' + \"c"),
        (SegmentType.CODE, "\ny;"),
    ]


def test_unterminated_string_freeze_ignores_strings_on_earlier_lines() -> None:
    # Only a closed string on the *same* line moves the freeze start back; `"ok"` on the line before stays intact.
    src = 'a = "ok";\nb = "broken\nc;'
    assert scan(src) == [
        (SegmentType.CODE, "a = "),
        (SegmentType.STRING, '"ok"'),
        (SegmentType.CODE, ";\nb = "),
        (SegmentType.STRING, '"broken'),
        (SegmentType.CODE, "\nc;"),
    ]


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


def test_unterminated_asm_block_runs_to_end() -> None:
    src = "x;\n__asm {\n  nop\ny;"
    assert scan(src) == [(SegmentType.CODE, "x;\n"), (SegmentType.ASM, "__asm {\n  nop\ny;")]


def test_protected_line_ends_marks_asm_interior() -> None:
    # An `__asm { ... }` block is a frozen opaque region, so its interior lines
    # must report as protected (like a multi-line string) --- otherwise the
    # line-oriented cosmetic passes would de-indent its assembly operands.
    src = "x = 1;\n__asm\n{\n  vmovdqa xmm7, foo\n}\ny = 2;\n"
    edges = protected_line_ends(src)
    lines = src.split("\n")
    assert lines[0] == "x = 1;" and edges[0] == (False, False)  # plain code
    assert lines[3] == "  vmovdqa xmm7, foo" and edges[3] == (True, True)  # asm interior


def test_protected_line_ends_start_and_end_differ() -> None:
    # A string continued with `\`-newline opens at the end of one line and closes at the start of the next.
    assert protected_line_ends('x = "a \\\nb";') == [(False, True), (True, False)]
    # A char literal at a line edge protects that edge only.
    assert protected_line_ends("'a' + b") == [(True, False)]


def test_protected_line_ends_empty_lines() -> None:
    # An empty line inside an `__asm` block is protected, an empty line in plain code is not.
    edges = protected_line_ends("__asm {\n\n  nop }\n\nx;")
    assert edges[1] == (True, True)
    assert edges[3] == (False, False)


def test_t1_preserves_asm_block_interior() -> None:
    # Regression: the line-oriented T1 passes (ws-indent/-trailing/-blanklines)
    # once de-indented `__asm` interiors because `protected_line_ends` only
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
