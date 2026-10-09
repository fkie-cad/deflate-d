"""Tests for the `ws-newlines` transform (JoinLines)."""

from __future__ import annotations

from typing import Set

import pytest

from deflated.transforms import JoinLines


class TestJoinLines:
    def test_lines_joined_with_space(self) -> None:
        c = JoinLines()
        assert c.apply("int x;\n int y;") == "int x; int y;"

    def test_line_comment_newline_preserved(self) -> None:
        c = JoinLines()
        # The newline terminating a `//` comment must survive, or the following
        # code would be swallowed into the comment.
        assert c.apply("// c\ncode;") == "// c\ncode;"
        assert c.apply("// c\ncode;  ") == "// c\ncode;"
        assert c.apply("  // c  \n\tcode;  ") == "// c  \ncode;"

    def test_preprocessor_directive_kept_on_own_line(self) -> None:
        c = JoinLines()
        assert c.apply("#define A 1\nint x;") == "#define A 1\nint x;"
        assert c.apply("  #define A 1 \n int x;") == "#define A 1\nint x;"

    def test_string_literal_preserved(self) -> None:
        c = JoinLines()
        assert c.apply('s = "a b";\nx;') == 's ="a b"; x;'

    def test_string_escape_interior_preserved(self) -> None:
        # The \n escapes inside a "..." literal are content and must survive
        # untouched; only the real line break after the statement is collapsed.
        c = JoinLines()
        assert c.apply(r'printf("line1\nline2");' + "\nreturn 0;") == r'printf("line1\nline2");' + " return 0;"
        assert c.apply(r'printf("line1\n\n  line2");' + "\nx;") == r'printf("line1\n\n  line2");' + " x;"

    # --- Positive cases: line breaks that should be removed ---

    def test_multiple_lines_joined(self) -> None:
        c = JoinLines()
        assert c.apply("a;\nb;\nc;") == "a; b; c;"

    def test_indentation_stripped_on_join(self) -> None:
        c = JoinLines()
        assert c.apply("int x;\n    int y;\n\treturn x;") == "int x; int y; return x;"

    def test_empty_lines_dropped(self) -> None:
        c = JoinLines()
        assert c.apply("a;\n\nb;") == "a; b;"

    def test_tokens_separated_by_space_on_join(self) -> None:
        # Word tokens on adjacent lines must not merge: `int\nx` -> `int x`, not `intx`.
        c = JoinLines()
        assert c.apply("int\nx;") == "int x;"

    def test_code_around_block_comment_joined(self) -> None:
        # The newlines around the block comment are dropped; no space is inserted
        # between a code segment and a comment — that is left to ws-tighten.
        c = JoinLines()
        assert c.apply("a;\n/* note */\nb;") == "a;/* note */b;"

    # --- Negative cases: line breaks that must be kept ---

    def test_block_comment_interior_newlines_preserved(self) -> None:
        c = JoinLines()
        assert c.apply("/*\n * doc\n */") == "/*\n * doc\n */"

    def test_multiline_block_comment_in_code_newlines_preserved(self) -> None:
        # Newlines inside a block comment survive even when code surrounds it;
        # only the code-segment newlines (before/after the comment) are collapsed.
        c = JoinLines()
        assert c.apply("a;\n/*\n * doc\n */\nb;") == "a;/*\n * doc\n */b;"

    def test_string_literal_content_not_collapsed(self) -> None:
        # The scanner passes STRING segments verbatim, so \n escapes inside a
        # closed "..." literal are never touched by the line-collapse logic ---
        # only line breaks outside the string collapse.
        c = JoinLines()
        assert c.apply(r'printf("line1\nline2");' + "\nreturn 0;") == r'printf("line1\nline2");' + " return 0;"
        # An escaped quote (\") inside the string does not close it.
        assert c.apply(r'printf("line1\n \" line2");' + "\nreturn 0;") == r'printf("line1\n \" line2");' + " return 0;"
        # Blank lines (\n\n) and indentation escapes between the quotes are part of
        # the string and survive verbatim; only the trailing line break collapses.
        assert (
            c.apply(r'printf("line1\n\n        line2");' + "\nreturn 0;")
            == r'printf("line1\n\n        line2");' + " return 0;"
        )

    def test_unterminated_string_keeps_its_newline(self) -> None:
        # A frozen (unterminated) literal keeps the line break after it; the following lines still join.
        c = JoinLines()
        assert c.apply('x = "https://trunc\ny = f();\nz = g();') == 'x ="https://trunc\ny = f(); z = g();'
        assert c.apply('rdi = "File: "%n" here;\nuVar1 = sub();') == 'rdi ="File: "%n" here;\nuVar1 = sub();'

    def test_frozen_string_line_joined_onto_previous_line(self) -> None:
        # Without a closed string on the previous line, the frozen line joins like any other line.
        c = JoinLines()
        assert c.apply('a;\nb;\n  x = "trunc\ny;') == 'a; b; x ="trunc\ny;'
        assert c.apply('a;\n    "trunc\ny;') == 'a;"trunc\ny;'
        assert c.apply('/* c */\n"trunc\ny;') == '/* c */"trunc\ny;'
        assert c.apply("a;\n  c = 'q'; x = \"trunc\ny;") == "a; c ='q'; x =\"trunc\ny;"
        assert c.apply('// c\n"trunc\ny;') == '// c\n"trunc\ny;'

    def test_frozen_string_line_not_joined_onto_closed_string(self) -> None:
        # A re-scan would freeze from the closed string on, so the line break before the frozen line is kept.
        c = JoinLines()
        assert c.apply('a = "ok";\nx = "trunc\ny;') == 'a ="ok";\nx ="trunc\ny;'
        assert c.apply('a = "ok";\nb;\n  "trunc\ny;') == 'a ="ok"; b;\n"trunc\ny;'
        assert c.apply('a = "ok";\n  c = \'q\'; x = "trunc\ny;') == 'a ="ok";\nc =\'q\'; x ="trunc\ny;'
        # The closed string is on an earlier output line, so the frozen line joins.
        assert c.apply('a = "ok";\n// c\nb;\nx = "trunc\ny;') == 'a ="ok";// c\nb; x ="trunc\ny;'
        # On the same source line, `scan` already freezes from the closed string on; the segment passes unchanged.
        assert c.apply('a = "ok"; x = "trunc\ny;') == 'a ="ok"; x = "trunc\ny;'

    def test_directive_line_keeps_newline_before_string_comment_or_char(self) -> None:
        c = JoinLines()
        assert c.apply('a;\n#define A 1\n"trunc\ny;') == 'a;\n#define A 1\n"trunc\ny;'
        assert c.apply('a = "ok";\n#define A 1\n"trunc\ny;') == 'a ="ok";\n#define A 1\n"trunc\ny;'
        assert c.apply('a;\n#define A 1\n"ok";\ny;') == 'a;\n#define A 1\n"ok"; y;'
        assert c.apply("a;\n#define A 1\n\n  /* c */ b;") == "a;\n#define A 1\n/* c */b;"
        assert c.apply("a;\n#define A 1\n'c';") == "a;\n#define A 1\n'c';"

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
        c = JoinLines()
        assert "do__asm" not in c.apply("do\n__asm { mov rax, rbx }\nwhile (x);")
        assert "else__asm" not in c.apply("else\n__asm { nop }\nf();")
        assert "return__asm" not in c.apply("return\n__asm { cpuid };")

    def test_char_literal_preserved(self) -> None:
        c = JoinLines()
        assert c.apply("f('a');\nf('b');") == "f('a'); f('b');"

    def test_line_comment_mid_file(self) -> None:
        # Only the one newline terminating the `//` is kept; subsequent code lines join.
        c = JoinLines()
        assert c.apply("a;\n// note\nb;\nc;") == "a;// note\nb; c;"

    def test_multiple_preprocessor_directives(self) -> None:
        c = JoinLines()
        assert c.apply("#define A 1\n#define B 2\n#define C 3") == "#define A 1\n#define B 2\n#define C 3"

    def test_preprocessor_between_code_lines(self) -> None:
        # Code on both sides of a preprocessor directive stays split across lines.
        c = JoinLines()
        assert c.apply("a;\n#define X 1\nb;\n c;") == "a;\n#define X 1\nb; c;"
        assert c.apply("a;\n  #define X 1\nb;\n c;") == "a;\n#define X 1\nb; c;"
        assert c.apply("a;\n  #define X 1\n #define Y 3\n b;\n c;") == "a;\n#define X 1\n#define Y 3\nb; c;"

    def test_multiline_macro_continuation_kept(self) -> None:
        # A '\'-continued #define spans physical lines; each stays on its own line
        # and the following code must not be fused into the macro body.
        c = JoinLines()
        out = c.apply("#define M(x) do { \\\n  f(x); \\\n} while(0)\nint y;\n")
        assert "int y;" in out
        assert "while(0)int y" not in out and "while(0) int y" not in out
        assert out.count("\\") == 2  # both line continuations preserved

    @pytest.mark.parametrize(
        ("src", "expected"),
        [
            # CODE_REVIEW 1.10: a string or comment ends the directive line.
            ('#include "a.h"\nint x;', '#include "a.h"\nint x;'),
            ("#endif /* X */\nint x;", "#endif /* X */\nint x;"),
            ("#define A 1 // x\nint y;", "#define A 1 // x\nint y;"),
            # CODE_REVIEW 1.10: a comment ends the line before the directive.
            ("int x; /* c */\n#define A 1\nint y;", "int x;/* c */\n#define A 1\nint y;"),
            # A comment before `#` on the same line is part of the directive line.
            ("x;\n/* c */ #define A 1\nint y;", "x;\n/* c */ #define A 1\nint y;"),
            # A block comment spanning lines continues the directive: `+ 2` belongs to the macro body.
            ("#define A 1 /* x\n y */ + 2\nint y;", "#define A 1 /* x\n y */ + 2\nint y;"),
        ],
    )
    def test_directive_kept_on_own_line_next_to_string_or_comment(self, src: str, expected: str) -> None:
        assert JoinLines().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            '#define A "s"\nx;',
            # `#define L"s"` defines nothing: `L"s"` is a wide string, not the macro name `L`.
            '#define L "s"\nx;',
        ],
    )
    def test_directive_interior_unchanged_at_segment_boundary(self, src: str) -> None:
        assert JoinLines().apply(src) == src

    @pytest.mark.parametrize(
        ("src", "expected"),
        [
            # CODE_REVIEW 1.11: the continuation after the string must not lose its line break.
            (
                '#define F(x) \\\n  puts("s"); \\\n  x\nint y;',
                {'#define F(x) \\\nputs("s"); \\\nx\nint y;', '#define F(x) \\\n  puts("s"); \\\n  x\nint y;'},
            ),
            # Splicing gives `foo  bar`; dropping the indentation would give `foobar`.
            ("#define A foo\\\n  bar\nx;", {"#define A foo\\\n  bar\nx;", "#define A foo \\\nbar\nx;"}),
        ],
    )
    def test_macro_continuation_kept(self, src: str, expected: Set[str]) -> None:
        assert JoinLines().apply(src) in expected

    @pytest.mark.parametrize(
        ("src", "expected"),
        [
            # CODE_REVIEW 1.9: else `//*` starts a line comment.
            ("x = a /\n/* c */ b;", "x = a / /* c */b;"),
            ("x = a /\n\n  /* c */ b;", "x = a / /* c */b;"),
            # Else `///` swallows the `/` operator.
            ("x = a /\n// c\nb;", "x = a / // c\nb;"),
            # Same line: stripping the end of the code fuses the `/` with the comment too.
            ("x = a / /* c */ b;", "x = a / /* c */b;"),
            ("x = a / // c\nb;", "x = a / // c\nb;"),
        ],
    )
    def test_division_not_fused_with_following_comment(self, src: str, expected: str) -> None:
        assert JoinLines().apply(src) == expected

    def test_no_space_before_comment_when_nothing_fuses(self) -> None:  # guard: passes today
        c = JoinLines()
        assert c.apply("x = a;\n/* c */ b;") == "x = a;/* c */b;"
        assert c.apply("x = a; /* c */\nb;") == "x = a;/* c */b;"

    @pytest.mark.parametrize("prefix", ["L", "u", "U", "u8"])
    def test_identifier_not_fused_into_literal_prefix(self, prefix: str) -> None:
        # CODE_REVIEW 1.16: else the identifier and the literal become one prefixed literal (`L"s"`, a wide string).
        c = JoinLines()
        assert c.apply(f'f({prefix}\n"s");') == f'f({prefix} "s");'
        assert c.apply(f"f({prefix}\n'a');") == f"f({prefix} 'a');"

    @pytest.mark.parametrize(("src", "expected"), [('f(xL\n"s");', 'f(xL"s");'), ('f(a.L\n"s");', 'f(a.L "s");')])
    def test_literal_prefix_only_as_whole_word(self, src: str, expected: str) -> None:
        # Only a whole word `L`, `u`, `U` or `u8` is a prefix, not the end of a longer name; a member `L` still is one.
        assert JoinLines().apply(src) == expected

    @pytest.mark.parametrize(
        ("src", "expected"),
        [
            ('wcscpy(buf, L"text");', 'wcscpy(buf,L"text");'),
            ("c = u8'a';", "c =u8'a';"),
            ('x = L"a"\n"b";', 'x =L"a""b";'),
        ],
    )
    def test_prefixed_literal_not_split(self, src: str, expected: str) -> None:
        # CODE_REVIEW 1.18: `L"text"` is one wide string; a space inside makes it identifier `L` plus a plain string.
        assert JoinLines().apply(src) == expected
