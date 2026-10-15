"""
Structure-aware primitives for editing C text that may not parse.

Decompiler output is frequently not valid, complete C, so transforms cannot use a parser, yet they still must
answer "where does this construct end?" and "is this `,`/`;`/keyword at the nesting level I care about?"
This module answers both, and is the only place that logic lives.

Everything here is depth-aware (`()`/`[]`/`{}` nesting is tracked, so a nested delimiter never fools a caller) and
literal-safe (raw source is read through `lexer.scan`, so string, char, and comment interiors are inert).

`ctokenize` gives the C-token stream: `(text, start, end)` triples with offsets into the original string. Over it,
`match_delimiter` / `match_delimiter_backward` find a delimiter's partner, `iter_depth` walks the tokens with their
nesting depth, `top_level_indices` / `first_top_level` / `split_top_level` find and split on tokens at depth 0
(`split_args` and `has_top_level_token` are the common cases), and `split_statements` cuts code at top-level `;{}`.
`word_before` works on raw characters instead and reads back the identifier ending at a given position.
`apply_edits` writes a batch of `(start, end, replacement)` edits, found on the original offsets, back in one pass.

A stray closer means the structure is unknown from there on. Every helper then answers so that its caller backs off:
the walk stops, a search finds nothing, a split returns None, and a guard reports a hit.
"""

from __future__ import annotations

import re
import string
from typing import Collection, Iterator, List, NamedTuple, Sequence, Tuple

from .lexer import SegmentType, scan


class CToken(NamedTuple):
    """A C token: its text, and the half-open `[start, end)` span it covers in the original string."""

    text: str
    start: int
    end: int


# A whole C numeric literal: hex float (`0x1.8p3`), hex integer, or decimal integer/float (`1e-3`, `.5`), each with any
# trailing suffix (`u`, `ULL`, `f`, Hex-Rays' `i64`). An exponent sign is taken only right after `e`/`E` (decimal) or
# `p`/`P` (hex float), so `0x1e+3` stays `0x1e` `+` `3`.
CNUMBER = re.compile(
    r"0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)[pP][+-]?\d+\w*"
    r"|0[xX][0-9a-fA-F]+\w*"
    r"|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?\w*"
)

# An integer literal with an optional integer suffix; `digits` keeps any `0x` prefix.
CINT = re.compile(r"(?P<digits>0[xX][0-9a-fA-F]+|\d+)(?P<suffix>[uUlL]*|[uU]?i(?:8|16|32|64))")

# An identifier or keyword: `fullmatch` tests a token, `finditer` finds the names in code.
IDENT = re.compile(r"[A-Za-z_]\w*")

# A single C token: multi-char operators first (so they are not split), then identifiers, numeric literals, and finally
# any single non-space character.
CTOKEN = re.compile(
    r"<<=|>>=|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^="
    r"|[A-Za-z_]\w*"
    rf"|{CNUMBER.pattern}"
    r"|\S"
)


def ctokenize(code: str) -> List[CToken]:
    """
    Tokenize `code` into `(text, start, end)` CTokens.

    String, character, and comment regions are emitted as one opaque token each, so their contents never participate in
    C-token matching.
    """
    all_c_tokens: List[CToken] = []
    current_position = 0
    for seg_type, text in scan(code):
        if seg_type != SegmentType.CODE:
            if text.strip():
                all_c_tokens.append(CToken(text, current_position, current_position + len(text)))
            current_position += len(text)
            continue
        for m in CTOKEN.finditer(text):
            all_c_tokens.append(CToken(m.group(0), current_position + m.start(), current_position + m.end()))
        current_position += len(text)
    return all_c_tokens


def apply_edits(code: str, edits: Collection[Tuple[int, int, str]]) -> str:
    """
    Return `code` with every `(start, end, replacement)` in `edits` applied, all offsets into the original `code`.

    The edits may come in any order. One that overlaps an edit starting earlier is dropped, so an outer rewrite wins
    over one nested in it. The result is built in one forward pass: a file can have thousands of edits, and slicing per
    edit is quadratic.
    """
    parts: List[str] = []
    copied_up_to = 0
    for start, end, replacement in sorted(edits):
        if start < copied_up_to:
            continue
        parts.append(code[copied_up_to:start])
        parts.append(replacement)
        copied_up_to = end
    parts.append(code[copied_up_to:])
    return "".join(parts)


def split_statements(code: str) -> List[str]:
    """
    Split `code` into pieces at top-level `;`, `{`, `}`.

    Depth-aware, `()`/`[]` are not split points, and string-safe (via `ctokenize`). After a stray `)` or `]` the depth
    is unknown, so the rest of `code` stays one piece (see `iter_depth`).
    Each delimiter stays attached to its piece; concatenating the pieces reproduces `code` exactly.
    """
    tokens = ctokenize(code)
    ends = [
        tokens[idx].end
        for idx, text, depth in iter_depth(tokens, openers="([")
        if depth == 0 and text in (";", "{", "}")
    ]
    pieces = [code[start:end] for start, end in zip([0] + ends, ends)]
    rest_start = ends[-1] if ends else 0
    if rest_start < len(code):
        pieces.append(code[rest_start:])
    return pieces


# Each opening delimiter and the closing delimiter that pairs with it.
CLOSER_FOR = {"(": ")", "[": "]", "{": "}"}
# Each closing delimiter and the opening delimiter that pairs with it.
OPENER_FOR = {closer: opener for opener, closer in CLOSER_FOR.items()}


def _text(token: CToken | str) -> str:
    """The text of `token`, which is either a `CToken` or already a plain token string."""
    return token if isinstance(token, str) else token.text


def match_delimiter(ctokens: Sequence[CToken | str], open_idx: int) -> int | None:
    """Return the index of the token that closes the opening delimiter at `ctokens[open_idx]`.

    The opener is read from `ctokens[open_idx]` and its closer looked up in `CLOSER_FOR`.
    Nested pairs of the same kind in between are skipped, so for `(a, (b)) c` starting at the first `(` the result is
    the second `)`.
    `ctokens` may also be plain token strings instead of `CToken`s.
    Returns None if `open_idx` is out of range, `ctokens[open_idx]` is not an opening delimiter, or it is never closed.
    """
    if not 0 <= open_idx < len(ctokens):
        return None
    opener = _text(ctokens[open_idx])
    closer = CLOSER_FOR.get(opener)
    if closer is None:
        return None
    depth = 0
    for idx in range(open_idx, len(ctokens)):
        t = _text(ctokens[idx])
        if t == opener:
            depth += 1
        elif t == closer:
            depth -= 1
            if depth == 0:
                return idx
    return None


def match_delimiter_backward(ctokens: Sequence[CToken | str], close_idx: int, lo_idx: int = 0) -> int | None:
    """Return the index of the token that opens the closing delimiter at `ctokens[close_idx]`.

    Searches back from `close_idx` to `lo_idx`. The mirror of `match_delimiter`: for `f(a, (b))` starting at the last
    `)` the result is the first `(`.
    `ctokens` may also be plain token strings instead of `CToken`s.
    Returns None if `close_idx` is out of range, `ctokens[close_idx]` is not a closing delimiter, or no opener for it is
    found at or after `lo_idx`.
    """
    if not 0 <= close_idx < len(ctokens):
        return None
    closer = _text(ctokens[close_idx])
    opener = OPENER_FOR.get(closer)
    if opener is None:
        return None
    depth = 0
    for idx in range(close_idx, max(0, lo_idx) - 1, -1):
        t = _text(ctokens[idx])
        if t == closer:
            depth += 1
        elif t == opener:
            depth -= 1
            if depth == 0:
                return idx
    return None


def iter_depth(
    ctokens: Sequence[CToken | str], lo_idx: int = 0, hi_idx: int | None = None, openers: str = "([{"
) -> Iterator[Tuple[int, str, int]]:
    """
    Yield `(idx, text, depth)` for every token in `ctokens[lo_idx:hi_idx]`, where `depth` is the nesting of the
    delimiter pairs opened by `openers` (all of `()`/`[]`/`{}` by default) the token sits at, counted from `lo_idx`.

    A delimiter sits at the depth outside its pair, so in `f(a)` the `(` and `)` are at depth 0 and `a` at depth 1.
    Delimiters not in `openers` count as ordinary tokens: with `openers="{"` only braces nest.
    A stray closer (one with no opener in the slice) means the walk has lost track of the structure: it is yielded at
    depth -1 and the walk stops there, so a caller never acts on tokens whose depth it cannot know.
    The slice is clamped to `ctokens` (a `hi_idx` of None means its end), and `ctokens` may also be plain token strings.
    """
    opener_set = frozenset(openers)
    closer_set = frozenset(CLOSER_FOR[opener] for opener in openers)
    depth = 0
    hi_idx = len(ctokens) if hi_idx is None else min(hi_idx, len(ctokens))
    for idx in range(max(0, lo_idx), hi_idx):
        text = _text(ctokens[idx])
        if text in opener_set:
            yield idx, text, depth
            depth += 1
        elif text in closer_set:
            depth -= 1
            yield idx, text, depth
            if depth < 0:
                return
        else:
            yield idx, text, depth


def top_level_indices(
    ctokens: Sequence[CToken | str], lo_idx: int, hi_idx: int | None, token_texts: Collection[str]
) -> List[int] | None:
    """
    Return the index of every token in `ctokens[lo_idx:hi_idx]` whose text is in `token_texts` and that sits at
    depth 0, in order, or None if the slice has a stray closer (see `iter_depth`), since then which tokens are top level
    is unknown.

    Depth and the slice bounds work as in `iter_depth`. Delimiters (`()[]{}`) only change the depth and are never
    reported, even if they are in `token_texts`.
    """
    indices: List[int] = []
    for idx, text, depth in iter_depth(ctokens, lo_idx, hi_idx):
        if depth < 0:
            return None
        if depth == 0 and text in token_texts and text not in CLOSER_FOR and text not in OPENER_FOR:
            indices.append(idx)
    return indices


def first_top_level(
    ctokens: Sequence[CToken | str], lo_idx: int, hi_idx: int | None, token_texts: Collection[str]
) -> int | None:
    """
    Return the index of the first token in `ctokens[lo_idx:hi_idx]` that `top_level_indices` would report, or None if
    there is none before the end of the slice or a stray closer.

    Unlike `top_level_indices`, a stray closer after the first match does not matter, so the slice may run past the
    end of the construct the caller is in (`hi_idx=None` to search to the end).
    """
    for idx, text, depth in iter_depth(ctokens, lo_idx, hi_idx):
        if depth < 0:
            return None
        if depth == 0 and text in token_texts and text not in CLOSER_FOR and text not in OPENER_FOR:
            return idx
    return None


def split_top_level(
    ctokens: Sequence[CToken | str], lo_idx: int, hi_idx: int, separators: Collection[str]
) -> List[Tuple[int, int]] | None:
    """
    Token-index spans of the items in `ctokens[lo_idx:hi_idx]` that are separated by a top-level token in
    `separators`, or None if the slice has a stray closer (see `top_level_indices`).

    Returns one `(lo, hi)` half-open token-index span per item, separators left out. Every separator ends an item, so
    a missing item (`a,,b`, `a,`) is an empty span; only an empty slice yields `[]`.
    """
    seps = top_level_indices(ctokens, lo_idx, hi_idx, separators)
    if seps is None:
        return None
    if not seps and lo_idx >= hi_idx:
        return []
    bounds = [lo_idx - 1] + seps + [hi_idx]
    return [(before + 1, after) for before, after in zip(bounds, bounds[1:])]


def split_args(ctokens: List[CToken], open_idx: int) -> List[Tuple[int, int]] | None:
    """
    Token-index spans of the top-level, comma-separated items between the delimiter at `ctokens[open_idx]` and its
    match, e.g. the arguments of a call `f(a, b)` or the elements of an initializer `{a, b}`.

    Returns one `(lo, hi)` half-open token-index span per item. Every top-level comma ends an item, so a missing item
    (`f(a,,b)`, `f(a,)`) is an empty span; only `()` with nothing inside yields `[]`. Commas nested inside
    `()`/`[]`/`{}` do not split.
    Returns None under the same conditions as `match_delimiter` (out of range, not an opener, or never closed), and if
    there is a stray closer of another kind inside (`f(a ] , b)`), since then the items are unknown.
    """
    close_idx = match_delimiter(ctokens, open_idx)
    if close_idx is None:
        return None
    return split_top_level(ctokens, open_idx + 1, close_idx, {","})


def has_top_level_token(ctokens: List[CToken], lo_idx: int, hi_idx: int, token_texts: frozenset) -> bool:
    """
    True if any token in `ctokens[lo_idx:hi_idx]` has its text in `token_texts` at delimiter depth 0 within the slice,
    or if the slice has a stray closer.

    This is a guard ("could this contain a top-level `;`?"), so when a stray closer makes the answer unknown it says
    yes, and the caller backs off. Depth is counted from `lo_idx`. Delimiters themselves (`()[]{}`) only change the
    depth and are never reported, even if they are in `token_texts`. The slice is clamped to `ctokens`, so indices
    outside it are never read.
    """
    indices = top_level_indices(ctokens, lo_idx, hi_idx, token_texts)
    return indices is None or bool(indices)


# Characters that can appear in a C identifier or keyword.
WORD_CHARS = frozenset(string.ascii_letters + string.digits + "_")


def word_before(code_chars: List[str], end_idx: int) -> str:
    """
    Return the identifier or keyword that ends right before `code_chars[end_idx]`, read backwards from
    `code_chars[end_idx - 1]`.

    `code_chars` is the code as single characters with whitespace removed and strings/comments skipped, so a caller can
    ask which word precedes a `{` or `(` at `end_idx`: for `} else {` the word before the `{` is `else`.
    Because there is no whitespace, adjacent words read back glued together (`else if (` gives `elseif`, `struct foo {`
    gives `structfoo`). Only ASCII letters, digits, and `_` (`WORD_CHARS`) form a word.
    Returns `""` if `end_idx` is 0, the character before it is not a word character, or the run starts with a digit
    (the tail of a number such as `1` or `0x1F`, never a valid identifier).
    """
    word = ""
    idx = end_idx - 1
    while idx >= 0 and code_chars[idx] in WORD_CHARS:
        word = code_chars[idx] + word  # prepend, since we walk backwards
        idx -= 1
    if word[:1].isdigit():
        return ""
    return word
