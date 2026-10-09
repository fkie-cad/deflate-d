"""Tests for the `ws-tighten` transform (TightenWhitespace)."""

from __future__ import annotations

import pytest

from deflated.transforms import TightenWhitespace


class TestTightenWhitespace:
    def test_spaces_around_operators_removed(self) -> None:
        t = TightenWhitespace()
        assert t.apply("  a = b == c;  ") == "a=b==c;"
        assert t.apply("\ta = b == c;  ") == "a=b==c;"

    def test_tab_collapse(self) -> None:
        c = TightenWhitespace()
        assert c.apply("int\tx;") == "int x;"

    def test_word_boundary_space_kept(self) -> None:
        # `int d` must not become `intd`.
        t = TightenWhitespace()
        assert t.apply("int  d;\t") == "int d;"

    def test_operator_adjacency_not_corrupted(self) -> None:
        t = TightenWhitespace()
        # `a - -b` must not become `a--b`; `a / *p` must not become `a/*p`.
        assert "--" not in t.apply("x = a - -b;")
        assert "/*" not in t.apply("x = a / *p;")

    def test_digraphs_not_fused(self) -> None:
        # The C alternative-token digraphs must not be created by removing a space:
        # `< :` -> `<:` (=`[`), `: >` -> `:>` (=`]`), `< %` -> `<%`, `% >`, `% :`.
        t = TightenWhitespace()
        assert "<:" not in t.apply("x = a < : b;")
        assert ":>" not in t.apply("x = a : > b;")
        assert "<%" not in t.apply("x = a < % b;")
        assert "%>" not in t.apply("x = a % > b;")
        assert "%:" not in t.apply("x = a % : b;")

    def test_string_literal_preserved(self) -> None:
        t = TightenWhitespace()
        assert t.apply('f ( "a , b");') == 'f("a , b");'

    def test_string_spaces_untouched(self) -> None:
        # Spaces inside a string literal are never collapsed or removed.
        t = TightenWhitespace()
        assert t.apply('"int  x  =  1;"') == '"int  x  =  1;"'

    def test_string_operators_untouched(self) -> None:
        # Operator sequences inside a string are not interpreted as C operators.
        t = TightenWhitespace()
        assert t.apply('"a + + b"') == '"a + + b"'
        assert t.apply('"a / * b"') == '"a / * b"'

    def test_string_comment_like_sequence_untouched(self) -> None:
        # `//` and `/*` inside a string must not be treated as comment openers.
        t = TightenWhitespace()
        assert t.apply('"http://example"') == '"http://example"'
        assert t.apply('"a /* b */ c"') == '"a /* b */ c"'

    def test_spaces_outside_string_tightened(self) -> None:
        # Only the spaces outside the string literal are tightened.
        t = TightenWhitespace()
        assert t.apply('x = "hello  world" ;') == 'x="hello  world";'

    def test_spaces_around_block_comment_removed(self) -> None:
        # In actual code, spaces between tokens and a block comment are dropped.
        t = TightenWhitespace()
        assert t.apply("a /* b */ c;") == "a/* b */c;"

    def test_does_not_touch_blank_lines(self) -> None:
        c = TightenWhitespace()
        assert c.apply("a;\n\t\n  \n \nb;") == "a;\n\n\n\nb;"

    def test_preprocessor_directive_unchanged(self) -> None:
        t = TightenWhitespace()
        assert t.apply("#include  <stdio.h>") == "#include  <stdio.h>"
        assert t.apply("  #define  FOO  1") == "  #define  FOO  1"

    def test_not_merging_into_block_comment_start(self) -> None:
        t = TightenWhitespace()
        assert t.apply("a = b / * c;") == "a=b/ *c;"

    def test_comments(self) -> None:
        t = TightenWhitespace()
        assert t.apply(" // some   comment") == "// some   comment"
        assert t.apply("\t// some \tcomment") == "// some \tcomment"
        assert t.apply(" /* some   comment */") == "/* some   comment */"
        assert t.apply("\t\t/* some \tcomment */") == "/* some \tcomment */"

    # --- Positive cases: spaces that should be removed ---

    def test_arithmetic_and_comparison_tightened(self) -> None:
        t = TightenWhitespace()
        assert t.apply("a + b;") == "a+b;"
        assert t.apply("a - b;") == "a-b;"
        assert t.apply("a * b;") == "a*b;"
        assert t.apply("a / b;") == "a/b;"
        assert t.apply("a % b;") == "a%b;"
        assert t.apply("a < b;") == "a<b;"
        assert t.apply("a > b;") == "a>b;"

    def test_unary_operators_tightened(self) -> None:
        t = TightenWhitespace()
        assert t.apply("* ptr;") == "*ptr;"
        assert t.apply("& x;") == "&x;"
        assert t.apply("! x;") == "!x;"
        assert t.apply("~ x;") == "~x;"

    def test_punctuation_tightened(self) -> None:
        t = TightenWhitespace()
        assert t.apply("f ( a , b );") == "f(a,b);"
        assert t.apply("a [ i ];") == "a[i];"
        assert t.apply("{ a ; }") == "{a;}"

    def test_member_access_tightened(self) -> None:
        # `->` and `.` are single tokens; only the surrounding spaces are removed.
        t = TightenWhitespace()
        assert t.apply("ptr -> field;") == "ptr->field;"
        assert t.apply("a . b;") == "a.b;"

    def test_ternary_tightened(self) -> None:
        t = TightenWhitespace()
        assert t.apply("a ? b : c;") == "a?b:c;"

    def test_star_slash_safe_to_merge(self) -> None:
        # `*/` is not a token in code context, so `* /` can be merged safely.
        # C tokenises `b*/* test */c` as `b * c` (the `/*` opens a comment).
        t = TightenWhitespace()
        assert t.apply("a * / b;") == "a*/b;"

    def test_block_comment_between_operators(self) -> None:
        # The lexer splits at `/*`, putting `*` and `/*` into separate code
        # segments, so the transform never sees them adjacent.  No danger.
        t = TightenWhitespace()
        assert t.apply("a = b * /* test */ c;") == "a=b*/* test */c;"

    # --- Negative cases: spaces that must be kept (full _FUSING_PAIRS coverage) ---

    def test_no_merge_increment_decrement(self) -> None:
        t = TightenWhitespace()
        assert "++" not in t.apply("a + +b;")
        assert "--" not in t.apply("a - -b;")

    def test_no_merge_shift_operators(self) -> None:
        t = TightenWhitespace()
        assert "<<" not in t.apply("a < <b;")
        assert ">>" not in t.apply("a > >b;")

    def test_no_merge_comparison_operators(self) -> None:
        t = TightenWhitespace()
        assert "<=" not in t.apply("a < =b;")
        assert ">=" not in t.apply("a > =b;")
        assert "==" not in t.apply("a = =b;")
        assert "!=" not in t.apply("a ! =b;")

    def test_no_merge_logical_operators(self) -> None:
        t = TightenWhitespace()
        assert "&&" not in t.apply("a & &b;")
        assert "||" not in t.apply("a | |b;")

    def test_no_merge_arrow_operator(self) -> None:
        t = TightenWhitespace()
        assert "->" not in t.apply("a - >b;")

    def test_no_merge_compound_assignment(self) -> None:
        t = TightenWhitespace()
        assert "+=" not in t.apply("a + =b;")
        assert "-=" not in t.apply("a - =b;")
        assert "*=" not in t.apply("a * =b;")
        assert "/=" not in t.apply("a / =b;")
        assert "%=" not in t.apply("a % =b;")
        assert "&=" not in t.apply("a & =b;")
        assert "|=" not in t.apply("a | =b;")
        assert "^=" not in t.apply("a ^ =b;")

    def test_no_merge_line_comment_start(self) -> None:
        t = TightenWhitespace()
        assert "//" not in t.apply("a / /b;")

    def test_char_literal_preserved(self) -> None:
        # Char literals are a distinct lexer segment; interior is untouched and
        # spaces around them are removed like any other non-word/non-op boundary.
        t = TightenWhitespace()
        assert t.apply("f ( 'a' );") == "f('a');"

    def test_star_slash_then_slash_star(self) -> None:
        # `* /` merges safely (not in _FUSING_PAIRS), but the resulting `/ *` keeps
        # its space (`/*` IS in _FUSING_PAIRS): `a * / * b` -> `a*/ *b`.
        t = TightenWhitespace()
        assert t.apply("a * / * b;") == "a*/ *b;"

    def test_inline_line_comment(self) -> None:
        # The space before `//` is the trailing char of its code segment and is
        # dropped; the comment itself is left verbatim.
        t = TightenWhitespace()
        assert t.apply("a = b; // result") == "a=b;// result"

    def test_digits_are_word_chars(self) -> None:
        # Digits are word chars, so digit-digit and letter-digit
        # boundaries keep their space; digit-operator boundaries drop it.
        t = TightenWhitespace()
        assert t.apply("x2 y3;") == "x2 y3;"
        assert t.apply("a2 + b3;") == "a2+b3;"

    def test_empty_lines(self) -> None:
        t = TightenWhitespace()
        assert t.apply("\t \t  ") == ""
        assert t.apply(" ") == ""
        assert t.apply("\t") == ""

    def test_digit_dot_not_fused_into_float(self) -> None:
        # Dropping the space in `1 . 5` would retokenize `1.` as a float constant,
        # changing the token stream; a digit/`.` boundary must keep its space.
        t = TightenWhitespace()
        assert "1.5" not in t.apply("x = 1 . 5;")
        assert "5.field" not in t.apply("x = 5 . field;")

    def test_hex_literal_dot_not_fused(self) -> None:
        # Regression: a hex literal ends in a letter (`0x1f`), so a last-char
        # `isdigit` test missed it and `0x1f . y` fused to the single pp-number
        # `0x1f.y`. The number-dot guard must treat a hex literal as numeric too.
        t = TightenWhitespace()
        assert t.apply("x = 0x1f . y;") == "x=0x1f .y;"
        assert "0x1f.y" not in t.apply("x = 0x1f . y;")

    def test_dot_digit_not_fused_into_float(self) -> None:
        # `x . 5` must not become `x.5`, which retokenizes as `x` followed by the float `.5`.
        t = TightenWhitespace()
        assert t.apply("y = x . 5;") == "y=x. 5;"

    def test_identifier_ending_in_digit_dot_merges(self) -> None:
        # An identifier is no number even if it ends in a digit, so `ab12 . x` tightens fully.
        t = TightenWhitespace()
        assert t.apply("y = ab12 . x;") == "y=ab12.x;"

    def test_float_with_dot_and_exponent_not_extended(self) -> None:
        # `1.e5` is one float; `.x` glued to it would extend that number token.
        t = TightenWhitespace()
        assert t.apply("y = 1.e5 . x;") == "y=1.e5 .x;"

    def test_exponent_sign_not_fused_into_number(self) -> None:
        # `0x1e+5` lexes as one invalid number (`e+` is an exponent), so `0x1e + 5` keeps the space before `+`.
        # In `e+1` only `1` is a number, so the space before `.` stays and the one before `+` goes.
        t = TightenWhitespace()
        assert t.apply("y = 0x1e + 5;") == "y=0x1e +5;"
        assert t.apply("y = 1e+5 . x;") == "y=1e+5 .x;"
        assert t.apply("y = e + 1 . x;") == "y=e+1 .x;"
        assert t.apply("y = 0x1e - 5;") == "y=0x1e -5;"
        assert t.apply("y = 0x1P - 1;") == "y=0x1P -1;"

    def test_hex_not_ending_in_exponent_letter_still_tightened(self) -> None:
        # Guard: only a number ending in `e`/`E`/`p`/`P` keeps the space before a sign.
        t = TightenWhitespace()
        assert t.apply("x = 0xFA - 1;") == "x=0xFA-1;"
        assert t.apply("x = 0x1f + z;") == "x=0x1f+z;"

    def test_word_after_number_ending_in_dot_not_fused(self) -> None:
        # `5.` is one float; `x` or `123` glued to it would extend that number token to `5.x` or `5.123`.
        t = TightenWhitespace()
        assert t.apply("y = 5. x;") == "y=5. x;"
        assert t.apply("y = 5. 123;") == "y=5. 123;"

    def test_gnu_case_range_keeps_spaces(self) -> None:
        # GNU case ranges: `1...` would lex the dots into the number. The space after `...` is kept conservatively.
        t = TightenWhitespace()
        assert t.apply("case 1 ... 5:") == "case 1 ... 5:"
        assert t.apply("case 0x1e ... 0x2f:") == "case 0x1e ... 0x2f:"

    def test_no_merge_scope_and_ptr_to_member(self) -> None:
        # C++ decompiler output: a label/ternary `:` next to a leading-scope `::`
        # must not fuse into the invalid `:::`, and `. *` must not fuse into the
        # pointer-to-member `.*`. Both would retokenize.
        t = TightenWhitespace()
        assert ":::" not in t.apply("switch(x){case 1: ::f();}")
        assert ":::" not in t.apply("x = cond ? a : ::glob;")
        assert ".*" not in t.apply("x = a . *p;")

    def test_scope_operator_still_tightened(self) -> None:
        # A genuine `A :: B` scope resolution still tightens to `A::B` -- the
        # `::` guard only fires on a `:`-then-`:` adjacency, never on a lone `::`.
        t = TightenWhitespace()
        assert t.apply("x = Foo :: bar;") == "x=Foo::bar;"

    def test_multiline_preprocessor_continuation_left_intact(self) -> None:
        # A '\'-continued #define is a directive across physical lines; neither the
        # directive line nor its continuation may be tightened.
        t = TightenWhitespace()
        src = "#define SWAP(a, b) { t = a ; } \\\nwhile ( 0 )\nint  c;\n"
        out = t.apply(src)
        assert "{ t = a ; }" in out  # directive line verbatim
        assert "while ( 0 )" in out  # its continuation verbatim too
        assert "int c;" in out  # ordinary code still tightened

    @pytest.mark.parametrize(
        "src",
        [
            "#define /* c */ F (x) x\n",  # else `F(x)`: an object-like macro becomes function-like
            '#define F(x) \\\n  puts("s"); foo \\\n  bar\n',  # else `foo\` + `bar` splices to `foobar`
            "#define P a /* c */ x # # b\n",  # else `##`: a paste instead of two `#`
            # A block comment spanning lines continues the directive: `+ 2` belongs to the macro body.
            "#define A 1 /* x\n y */ + 2\n",
            # A comment before `#` on the same line is part of the directive line.
            "/* c */ #define F (x) x\n",
        ],
    )
    def test_directive_split_by_comment_or_string_unchanged(self, src) -> None:
        assert TightenWhitespace().apply(src) == src

    def test_code_around_directive_with_comment_still_tightened(self) -> None:
        src = "int  a ;\n#define F /* c */ (x) x\nint  b ;\n"
        assert TightenWhitespace().apply(src) == "int a;\n#define F /* c */ (x) x\nint b;\n"

    def test_word_token_not_glued_to_asm_block(self) -> None:
        # `__asm` begins with a word char and is a separate (opaque) segment, so
        # tightening the code's trailing space away would fuse a preceding word
        # token into it (`do __asm{...}` -> `do__asm{...}`), corrupting the `do`
        # keyword and de-protecting the asm block on a re-scan. One space is kept.
        t = TightenWhitespace()
        out = t.apply("do __asm { nop }")
        assert "do__asm" not in out
        assert out.startswith("do __asm")
        # Idempotent: a second pass keeps the restored boundary space.
        assert t.apply(out) == out

    @pytest.mark.parametrize(
        "src, expected",
        [
            ("x = a / /* c */ b;", "x=a/ /* c */b;"),  # else `//*` starts a line comment
            ("x = a / // c\n b;", "x=a/ // c\nb;"),  # else `///` swallows the `/` operator
        ],
    )
    def test_division_not_fused_with_following_comment(self, src, expected) -> None:
        assert TightenWhitespace().apply(src) == expected

    @pytest.mark.parametrize("prefix", ["L", "u", "U", "u8"])
    def test_identifier_not_fused_into_literal_prefix(self, prefix) -> None:
        t = TightenWhitespace()
        assert t.apply(f'f({prefix} "s");') == f'f({prefix} "s");'
        assert t.apply(f"f({prefix} 'a');") == f"f({prefix} 'a');"
        assert t.apply(f'f({prefix}\n"s");') == f'f({prefix}\n"s");'

    @pytest.mark.parametrize("src, expected", [('f(xL "s");', 'f(xL"s");'), ('f(a.L "s");', 'f(a.L "s");')])
    def test_literal_prefix_only_as_whole_word(self, src, expected) -> None:
        # Only a whole word `L`, `u`, `U` or `u8` is a prefix, not the end of a longer name; a member `L` still is one.
        assert TightenWhitespace().apply(src) == expected

    @pytest.mark.parametrize(
        "src, expected", [('wcscpy(buf, L"text");', 'wcscpy(buf,L"text");'), ("c = u8'a';", "c=u8'a';")]
    )
    def test_prefixed_literal_not_split(self, src, expected) -> None:
        assert TightenWhitespace().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "__asm { nop }",  # nothing before the block
            "/* c */__asm { nop }",  # a comment, not code, before the block
            "/* a *///b",  # `*/` is the end of a comment, not a `/` operator: no space added
        ],
    )
    def test_segment_boundary_without_code_before_unchanged(self, src) -> None:
        assert TightenWhitespace().apply(src) == src

    def test_punctuation_still_tightened_before_asm(self) -> None:
        # When the code before the asm block ends in a non-word char there is no
        # gluing risk, so the boundary is tightened normally.
        t = TightenWhitespace()
        assert t.apply("x ;  __asm { nop }") == "x;__asm { nop }"
