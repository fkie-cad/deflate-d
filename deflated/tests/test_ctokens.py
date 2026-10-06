"""Tests for the token-stream toolkit (ctokens.py)."""

from __future__ import annotations

from deflated.transforms.ctokens import ctokenize, has_top, match_delim, split_args, split_statements


def test_multi_char_operators_and_offsets() -> None:
    # Multi-char operators stay whole; offsets index back into the source.
    src = "a >>= b->c;"
    toks = ctokenize(src)
    assert [t for t, _, _ in toks] == ["a", ">>=", "b", "->", "c", ";"]
    assert all(src[s:e] == t for t, s, e in toks)


def test_literals_are_opaque() -> None:
    # Literals/comments enter as one opaque token, so their innards never match.
    assert [t for t, _, _ in ctokenize('x = "a;b{c";')] == ["x", "=", '"a;b{c"', ";"]


def test_split_statements_depth_aware() -> None:
    code = "if (a) { x = f(1, 2); } else y = 3;"
    pieces = split_statements(code)
    assert "".join(pieces) == code  # reconstructs the input exactly
    assert any("f(1, 2)" in p for p in pieces)


def test_match_delim_and_has_top() -> None:
    # match_delim pairs the right delimiter across nesting.
    t = ctokenize("(a, (b, c)) , d")
    assert match_delim(t, 0, "(", ")") == 8
    # has_top reports a delimiter only at the slice's own depth 0.
    assert not has_top(ctokenize("a (b, c) d"), 0, 4, frozenset({","}))
    assert has_top(ctokenize("a , b"), 0, 3, frozenset({","}))


def test_split_args_top_level_only() -> None:
    # Commas nested in inner delimiters do not split; each arg is a token span.
    t = ctokenize("f(a, g(b, c), d)")
    open_i = 1  # the '(' after 'f'
    close_i = match_delim(t, open_i, "(", ")")
    spans = split_args(t, open_i, close_i)
    args = ["".join(tt for tt, _, _ in t[lo:hi]) for lo, hi in spans]
    assert args == ["a", "g(b,c)", "d"]


def test_split_args_empty_call() -> None:
    t = ctokenize("f()")
    assert split_args(t, 1, match_delim(t, 1, "(", ")")) == []
