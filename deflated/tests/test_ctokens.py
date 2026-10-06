"""Tests for the token-stream toolkit (ctokens.py)."""

from __future__ import annotations

import pytest

from deflated.transforms.ctokens import (
    ctokenize,
    has_top_level_token,
    match_delimiter,
    split_args,
    split_statements,
    word_before,
)


def test_multi_char_operators_and_offsets() -> None:
    # Multi-char operators stay whole; offsets index back into the source.
    src = "a >>= b->c;"
    toks = ctokenize(src)
    assert [t for t, _, _ in toks] == ["a", ">>=", "b", "->", "c", ";"]
    assert all(src[s:e] == t for t, s, e in toks)


def test_literals_are_opaque() -> None:
    # Literals/comments enter as one opaque token, so their innards never match.
    assert [t for t, _, _ in ctokenize('x = "a;b{c";')] == ["x", "=", '"a;b{c"', ";"]


# Forms that actually turn up in decompiler output: Ghidra and Hex-Rays both print `u`/`U` suffixes, Hex-Rays suffixes
# 64-bit constants (`LL`, or MSVC-style `i64`/`ui64`), both print doubles %g-style so extreme values arrive in exponent
# form, and either decompiler emits `0b...` once a scalar is converted to binary.
DECOMPILER_LITERALS = [
    "0.0",
    "1.0e+300",
    "4.6116860184273879e18",  # Hex-Rays float reconstruction, unsigned exponent
    "1e3",  # exponent, no dot
    "42u",
    "0x8000u",
    "0x10u",  # hex + integer suffix
    "10ULL",
    "0xffffffffffffffffLL",
    "0x1Fi64",  # Hex-Rays, MSVC style
    "0xFFui64",
    "0b1010",  # binary literal (C23/GCC extension)
]

# Not seen from a decompiler, but valid C the lexer still must not split. C++ digit separators (`1'000'000`) are
# deliberately out of scope: no decompiler emits them, and a pp-number rule covering `'` would collide with char literals.
EXOTIC_LITERALS = [
    "1.5e-3f",  # signed exponent + float suffix
    "2.5E+10",  # uppercase exponent
    "1.f",  # trailing dot + suffix
    ".5",  # leading dot; formatters always print the 0
    "0x1fULL",
    "0x1p4",  # hex float, no dot
    "0x1.8p3",  # hex float with dot
    "0x1.8P-3L",
]


@pytest.mark.parametrize("lit", DECOMPILER_LITERALS + EXOTIC_LITERALS)
def test_numeric_literal_is_one_token(lit) -> None:
    # A C numeric literal (exponent, suffix, leading dot, hex float) is one token.
    # Split up, its tail reads as an identifier (`e3`, `ULL`), an operator (`-`), or
    # a member access (`.`), which fools the literal guards in the transforms.
    src = f"x = {lit};"
    assert [t for t, _, _ in ctokenize(src)] == ["x", "=", lit, ";"]


def test_sign_is_not_part_of_the_literal() -> None:
    # `-0x80000000LL` is unary minus applied to a literal; transforms match the
    # operator on its own, so the sign must stay a separate token.
    toks = [t for t, _, _ in ctokenize("x = -0x80000000LL;")]
    assert toks == ["x", "=", "-", "0x80000000LL", ";"]


def test_numeric_literals_in_expression() -> None:
    src = "x = 1.5e-3f + 10ULL + .5;"
    toks = ctokenize(src)
    assert [t for t, _, _ in toks] == ["x", "=", "1.5e-3f", "+", "10ULL", "+", ".5", ";"]
    assert all(src[s:e] == t for t, s, e in toks)


def test_exponent_sign_only_after_exponent_marker() -> None:
    # `e` is a hex digit, not an exponent: `0x1e+3` is `0x1e` plus `3`.
    assert [t for t, _, _ in ctokenize("x = 0x1e+3;")] == ["x", "=", "0x1e", "+", "3", ";"]


def test_member_access_is_not_a_number() -> None:
    # The leading-dot rule must not swallow `.` before an identifier or after one.
    assert [t for t, _, _ in ctokenize("a.b + s.x1")] == ["a", ".", "b", "+", "s", ".", "x1"]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        # Every top-level `;`, `{`, `}` closes a piece; the delimiter stays attached.
        ("if (a) { x = f(1, 2); } else y = 3;", ["if (a) {", " x = f(1, 2);", " }", " else y = 3;"]),
        ("{{}}", ["{", "{", "}", "}"]),
        # Delimiters nested in `()` / `[]` are not split points.
        ("for (i = 0; i < n; i++) x++;", ["for (i = 0; i < n; i++) x++;"]),
        ("a[i; j] = 1; b;", ["a[i; j] = 1;", " b;"]),
        ("x = ({ a; b; });", ["x = ({ a; b; });"]),  # GNU statement expression
        # Delimiters inside strings, chars, comments, and `__asm` blocks are opaque.
        ('s = "{;}"; t;', ['s = "{;}";', " t;"]),
        ("c = ';'; d;", ["c = ';';", " d;"]),
        ("x; // a; b {\ny;", ["x;", " // a; b {\ny;"]),
        ("x /* ; { } */ = 1;", ["x /* ; { } */ = 1;"]),
        ("__asm { mov eax, 1; } x;", ["__asm { mov eax, 1; } x;"]),
        # Trailing text without a delimiter still forms a final piece.
        ("x; y", ["x;", " y"]),
        ("", []),
        # A stray `)` must not push depth negative and suppress later splits.
        (") a; b;", [") a;", " b;"]),
        # An unclosed `(` keeps everything after it in one piece.
        ("f(a; b; c", ["f(a; b; c"]),
    ],
)
def test_split_statements(code: str, expected: list[str]) -> None:
    pieces = split_statements(code)
    assert pieces == expected
    assert "".join(pieces) == code  # reconstructs the input exactly


@pytest.mark.parametrize(
    ("code", "open_idx", "expected"),
    [
        # Nested pairs of the same kind are skipped.
        ("(a, (b, c)) , d", 0, 8),
        ("()", 0, 1),
        # The closer follows from the opener; other kinds in between do not interfere.
        ("{ a[(b)] } c", 0, 7),
        ("{ a[(b)] } c", 2, 6),
        ("(a]", 0, None),
        # Crossed pairs are malformed but accepted: only the opener's own kind is counted.
        ("([)]", 0, 2),
        ("([)]", 1, 3),
        # Delimiters inside strings, chars, and comments are opaque tokens and never match.
        ("f(\")\", ')', /* ) */ x)", 1, 8),
        ("{ // }\n}", 0, 2),
        # Not an opener, or never closed.
        ("f(a)", 0, None),
        (")", 0, None),
        ("(a, (b)", 0, None),
        # Out-of-range index (negative indices are not wrapped around).
        ("(a)", 3, None),
        ("(a)", -1, None),
        ("", 0, None),
    ],
)
def test_match_delimiter(code: str, open_idx: int, expected: int | None) -> None:
    assert match_delimiter(ctokenize(code), open_idx) == expected


@pytest.mark.parametrize(
    ("code", "lo_idx", "hi_idx", "token_texts", "expected"),
    [
        # Only depth 0 within the slice counts, for every bracket kind.
        ("a , b", 0, 3, {","}, True),
        ("a (b, c) d", 0, 7, {","}, False),
        ("a [b, c] d", 0, 7, {","}, False),
        ("a {b, c} d", 0, 7, {","}, False),
        # Depth is counted from lo_idx: inside `(b, c)` the comma is top level.
        ("a (b, c) d", 2, 5, {","}, True),
        # Whole tokens are matched, so `==` is not `=`; multi-char targets work.
        ("a == b", 0, 3, {"="}, False),
        ("a <<= b", 0, 3, {"<<="}, True),
        # Commas inside strings, chars, and comments are opaque.
        ('a "b, c" d', 0, 3, {","}, False),
        ("a ',' d", 0, 3, {","}, False),
        ("a /* , */ d", 0, 3, {","}, False),
        # Delimiters only change the depth and are never reported.
        ("(a)", 0, 3, {"(", ")"}, False),
        # A stray closer does not push later tokens below depth 0.
        ("a ] , b", 0, 4, {","}, True),
        # The slice bounds are respected: the comma at index 1 is outside [2, 3).
        ("a , b", 2, 3, {","}, False),
        ("a , b", 1, 1, {","}, False),  # empty slice
        # Out-of-range bounds are clamped instead of raising.
        ("a , b", 0, 99, {","}, True),
        ("a , b", -5, 3, {","}, True),
        ("", 0, 1, {","}, False),
    ],
)
def test_has_top_level_token(code: str, lo_idx: int, hi_idx: int, token_texts: set[str], expected: bool) -> None:
    assert has_top_level_token(ctokenize(code), lo_idx, hi_idx, frozenset(token_texts)) is expected


@pytest.mark.parametrize(
    ("code", "open_idx", "expected"),
    [
        # Commas nested in inner delimiters do not split.
        ("f(a, g(b, c), d)", 1, ["a", "g(b,c)", "d"]),
        ("f(a[i, j], {x, y})", 1, ["a[i,j]", "{x,y}"]),
        ("f(a)", 1, ["a"]),
        ("f()", 1, []),
        # Every comma ends an item, so missing items become empty ones.
        ("f(a,)", 1, ["a", ""]),
        ("f(,a)", 1, ["", "a"]),
        ("f(a,,b)", 1, ["a", "", "b"]),
        ("f(,)", 1, ["", ""]),
        # Only the tokens up to the matching closer are split.
        ("f(a, b) , c", 1, ["a", "b"]),
        # A stray closer inside is kept in its item and does not hide later commas.
        ("f(a ] , b)", 1, ["a]", "b"]),
        # Any opener works, not only a call's `(`.
        ("{a, b}", 0, ["a", "b"]),
        # A comma inside a string, char, or comment is opaque.
        ("f(\",\", ',', /* , */ x)", 1, ['","', "','", "/* , */x"]),
        # Same None conditions as match_delimiter.
        ("f(a)", 0, None),  # not an opener
        ("f(a, b", 1, None),  # never closed
        ("f(a)", 4, None),  # out of range
    ],
)
def test_split_args(code: str, open_idx: int, expected: list[str] | None) -> None:
    t = ctokenize(code)
    spans = split_args(t, open_idx)
    items = None if spans is None else ["".join(tok.text for tok in t[lo:hi]) for lo, hi in spans]
    assert items == expected


def test_split_args_spans() -> None:
    # Spans are half-open token indices; an empty item is an empty span at its own position.
    #                      0 1 2 3 4 5 6 7
    t = ctokenize("f(a,,b)")  # f ( a , , b )
    assert split_args(t, 1) == [(2, 3), (4, 4), (5, 6)]


@pytest.mark.parametrize(
    ("code", "end_idx", "expected"),
    [
        # end_idx counts in the whitespace-free characters: `}else{` has the `{` at 5.
        ("} else {", 5, "else"),
        ("do {", 2, "do"),  # word at the very start
        ("} else", 5, "else"),  # end_idx past the last character
        # Underscores and digits are part of the word.
        ("; _Loop2 :", 7, "_Loop2"),
        # Adjacent words read back glued together, since whitespace is gone.
        ("} else if (c) {", 7, "elseif"),
        ("struct foo {", 9, "structfoo"),
        # No word directly before end_idx.
        ("f(x) {", 4, ""),
        ("x; {", 2, ""),
        ("{", 0, ""),
        # Only ASCII word characters count: non-ASCII letters and digits end the word.
        ("aé {", 2, ""),
        ("x² {", 2, ""),
        ("éelse {", 5, "else"),
        # A run starting with a digit is the tail of a number, not a word.
        ("x = 1 {", 3, ""),
        ("x = 0x1F {", 6, ""),
    ],
)
def test_word_before(code: str, end_idx: int, expected: str) -> None:
    code_chars = [ch for ch in code if not ch.isspace()]
    assert word_before(code_chars, end_idx) == expected
