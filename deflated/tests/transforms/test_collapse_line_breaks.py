"""Tests for the `ws-newlines` transform (CollapseLineBreaks)."""

from __future__ import annotations

from deflated.transforms import CollapseLineBreaks


class TestCollapseLineBreaks:
    def test_lines_joined_with_space(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("int x;\n int y;") == "int x; int y;"

    def test_line_comment_newline_preserved(self) -> None:
        c = CollapseLineBreaks()
        # The newline terminating a `//` comment must survive, or the following
        # code would be swallowed into the comment.
        assert c.apply("// c\ncode;") == "// c\ncode;"
        assert c.apply("// c\ncode;  ") == "// c\ncode;"
        assert c.apply("  // c  \n\tcode;  ") == "// c  \ncode;"

    def test_preprocessor_directive_kept_on_own_line(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("#define A 1\nint x;") == "#define A 1\nint x;"
        assert c.apply("  #define A 1 \n int x;") == "#define A 1\nint x;"

    def test_string_literal_preserved(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply('s = "a b";\nx;') == 's ="a b"; x;'

    def test_string_escape_interior_preserved(self) -> None:
        # The \n escapes inside a "..." literal are content and must survive
        # untouched; only the real line break after the statement is collapsed.
        c = CollapseLineBreaks()
        assert c.apply(r'printf("line1\nline2");' + "\nreturn 0;") == r'printf("line1\nline2");' + " return 0;"
        assert c.apply(r'printf("line1\n\n  line2");' + "\nx;") == r'printf("line1\n\n  line2");' + " x;"

    # --- Positive cases: line breaks that should be removed ---

    def test_multiple_lines_joined(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("a;\nb;\nc;") == "a; b; c;"

    def test_indentation_stripped_on_join(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("int x;\n    int y;\n\treturn x;") == "int x; int y; return x;"

    def test_empty_lines_dropped(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("a;\n\nb;") == "a; b;"

    def test_tokens_separated_by_space_on_join(self) -> None:
        # Word tokens on adjacent lines must not merge: `int\nx` -> `int x`, not `intx`.
        c = CollapseLineBreaks()
        assert c.apply("int\nx;") == "int x;"

    def test_code_around_block_comment_joined(self) -> None:
        # The newlines around the block comment are dropped; no space is inserted
        # between a code segment and a comment — that is left to ws-tighten.
        c = CollapseLineBreaks()
        assert c.apply("a;\n/* note */\nb;") == "a;/* note */b;"

    # --- Negative cases: line breaks that must be kept ---

    def test_block_comment_interior_newlines_preserved(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("/*\n * doc\n */") == "/*\n * doc\n */"

    def test_multiline_block_comment_in_code_newlines_preserved(self) -> None:
        # Newlines inside a block comment survive even when code surrounds it;
        # only the code-segment newlines (before/after the comment) are collapsed.
        c = CollapseLineBreaks()
        assert c.apply("a;\n/*\n * doc\n */\nb;") == "a;/*\n * doc\n */b;"

    def test_string_literal_content_not_collapsed(self) -> None:
        # The scanner passes STRING segments verbatim, so \n escapes inside a
        # closed "..." literal are never touched by the line-collapse logic ---
        # only line breaks outside the string collapse.
        c = CollapseLineBreaks()
        assert c.apply(r'printf("line1\nline2");' + "\nreturn 0;") == r'printf("line1\nline2");' + " return 0;"
        # An escaped quote (\") inside the string does not close it.
        assert c.apply(r'printf("line1\n \" line2");' + "\nreturn 0;") == r'printf("line1\n \" line2");' + " return 0;"
        # Blank lines (\n\n) and indentation escapes between the quotes are part of
        # the string and survive verbatim; only the trailing line break collapses.
        assert c.apply(r'printf("line1\n\n        line2");' + "\nreturn 0;") == r'printf("line1\n\n        line2");' + " return 0;"

    def test_unterminated_string_keeps_its_newline(self) -> None:
        # A frozen (unterminated) literal must be ISOLATED on its own physical line:
        # the newline is kept both AFTER it (so its malformed content does not glue
        # onto the next line of real code) and BEFORE it (so its head does not join
        # the preceding code into one long line, which a later re-scan would then
        # backtrack the freeze across, swallowing real code).
        c = CollapseLineBreaks()
        # truncated literal (no closing quote): newline kept before AND after; the
        # following real lines still join to each other.
        assert c.apply('x = "https://trunc\ny = f();\nz = g();') == 'x =\n"https://trunc\ny = f(); z = g();'
        # embedded-quote freeze ends mid-content (`;`), still isolated on its line.
        assert c.apply('rdi = "File: "%n" here;\nuVar1 = sub();') == 'rdi =\n"File: "%n" here;\nuVar1 = sub();'

    def test_frozen_string_does_not_swallow_preceding_code_on_rescan(self) -> None:
        # Regression for the cascade: a real-code line, then a normal closed string,
        # then a malformed embedded-quote line. After ws-newlines, re-scanning (as
        # ws-tighten does) must NOT freeze back across the joined code to the first
        # string. The closed string and the `while` keyword must remain CODE/STRING,
        # not be absorbed into one giant opaque literal.
        from deflated import Tier, transform
        from deflated.transforms.lexer import SegmentType, scan, string_is_terminated

        src = 'a = bindtextdomain("coreutils", x);\nwhile (y) g();\nz = strncmp(p, "TZ="", 4);\n'
        out = transform(src, Tier.T1_COSMETIC)
        code = "".join(t for k, t in scan(out) if k == SegmentType.CODE)
        assert "while" in code  # control flow survives as code
        frozen = sum(len(t) for k, t in scan(out) if k == SegmentType.STRING and not string_is_terminated(t))
        assert frozen < 40  # only the malformed `"TZ="", 4);` tail is frozen, not the whole prefix

    def test_keyword_not_merged_into_asm_block(self) -> None:
        # A keyword on its own line followed by an opaque `__asm{...}` block must
        # not glue into one identifier when the newline is collapsed (`do __asm`,
        # not `do__asm` -- the latter also defeats the lexer's ASM protection).
        c = CollapseLineBreaks()
        assert "do__asm" not in c.apply("do\n__asm { mov rax, rbx }\nwhile (x);")
        assert "else__asm" not in c.apply("else\n__asm { nop }\nf();")
        assert "return__asm" not in c.apply("return\n__asm { cpuid };")

    def test_char_literal_preserved(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("f('a');\nf('b');") == "f('a'); f('b');"

    def test_line_comment_mid_file(self) -> None:
        # Only the one newline terminating the `//` is kept; subsequent code lines join.
        c = CollapseLineBreaks()
        assert c.apply("a;\n// note\nb;\nc;") == "a;// note\nb; c;"

    def test_multiple_preprocessor_directives(self) -> None:
        c = CollapseLineBreaks()
        assert c.apply("#define A 1\n#define B 2\n#define C 3") == "#define A 1\n#define B 2\n#define C 3"

    def test_preprocessor_between_code_lines(self) -> None:
        # Code on both sides of a preprocessor directive stays split across lines.
        c = CollapseLineBreaks()
        assert c.apply("a;\n#define X 1\nb;\n c;") == "a;\n#define X 1\nb; c;"
        assert c.apply("a;\n  #define X 1\nb;\n c;") == "a;\n#define X 1\nb; c;"
        assert c.apply("a;\n  #define X 1\n #define Y 3\n b;\n c;") == "a;\n#define X 1\n#define Y 3\nb; c;"

    def test_multiline_macro_continuation_kept(self) -> None:
        # A '\'-continued #define spans physical lines; each stays on its own line
        # and the following code must not be fused into the macro body.
        c = CollapseLineBreaks()
        out = c.apply("#define M(x) do { \\\n  f(x); \\\n} while(0)\nint y;\n")
        assert "int y;" in out
        assert "while(0)int y" not in out and "while(0) int y" not in out
        assert out.count("\\") == 2  # both line continuations preserved