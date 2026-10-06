"""
Structure-aware primitives for editing C text that may not parse.

Decompiler output is frequently not valid, complete C, so transforms cannot use a parser, yet they still must
answer "where does this construct end?" and "is this `,`/`;`/keyword at the nesting level I care about?"
This module answers both, and is the only place that logic lives.

Everything here is depth-aware (`()`/`[]`/`{}` nesting is tracked, so a nested delimiter never fools a caller) and
literal-safe (raw source is read through `lexer.scan`, so string, char, and comment interiors are inert).

`ctokenize` gives the C-token stream: `(text, start, end)` triples with offsets into the original string. Over it,
`match_delimiter` finds a delimiter's partner, `split_args` spans a call's arguments, and `has_top_level_token` tests
for a token at depth 0. Working on raw text instead: `split_statements` cuts at top-level `;{}`, and `word_before`
reads back the identifier ending at a given position.
"""

from __future__ import annotations

import re
import string
from typing import NamedTuple, Tuple, List

from .lexer import SegmentType, scan


class CToken(NamedTuple):
    """A C token: its text, and the half-open `[start, end)` span it covers in the original string."""

    text: str
    start: int
    end: int

# A whole C numeric literal: hex float (`0x1.8p3`), hex integer, or decimal integer/float (`1e-3`, `.5`), each with any
# trailing suffix (`u`, `ULL`, `f`, Hex-Rays' `i64`). An exponent sign is taken only right after `e`/`E` (decimal) or
# `p`/`P` (hex float), so `0x1e+3` stays `0x1e` `+` `3`.
CNUMBER = re.compile(r"0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)[pP][+-]?\d+\w*" r"|0[xX][0-9a-fA-F]+\w*" r"|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?\w*")

# An integer literal with an optional integer suffix; group 1 is the digits (with any `0x` prefix), group 2 the suffix.
CINT = re.compile(r"(0[xX][0-9a-fA-F]+|\d+)([uUlL]*|[uU]?i(?:8|16|32|64))")

# A single C token: multi-char operators first (so they are not split), then identifiers, numeric literals, and finally
# any single non-space character.
CTOKEN = re.compile(r"<<=|>>=|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=" r"|[A-Za-z_]\w*" rf"|{CNUMBER.pattern}" r"|\S")


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


def split_statements(code: str) -> List[str]:
    """
    Split `code` into pieces at top-level `;`, `{`, `}`.

    Depth-aware, `()`/`[]` are not split points, and string-safe (via the scanner).
    Each delimiter stays attached to its piece; concatenating the pieces reproduces `code` exactly.
    """
    pieces: List[str] = []
    current_piece = ""
    depth = 0
    for seg_type, text in scan(code):
        if seg_type != SegmentType.CODE:
            current_piece += text
            continue
        for character in text:
            current_piece += character
            if character in "([":
                depth += 1
            elif character in ")]":
                depth = max(0, depth - 1)
            elif depth == 0 and character in ";{}":
                pieces.append(current_piece)
                current_piece = ""
    if current_piece:
        pieces.append(current_piece)
    return pieces


# Each opening delimiter and the closing delimiter that pairs with it.
CLOSER_FOR = {"(": ")", "[": "]", "{": "}"}


def match_delimiter(ctokens: List[CToken], open_idx: int) -> int | None:
    """Return the index of the token that closes the opening delimiter at `ctokens[open_idx]`.

    The opener is read from `ctokens[open_idx]` and its closer looked up in `CLOSER_FOR`.
    Nested pairs of the same kind in between are skipped, so for `(a, (b)) c` starting at the first `(` the result is
    the second `)`.
    Returns None if `open_idx` is out of range, `ctokens[open_idx]` is not an opening delimiter, or it is never closed.
    """
    if not 0 <= open_idx < len(ctokens):
        return None
    opener = ctokens[open_idx].text
    closer = CLOSER_FOR.get(opener)
    if closer is None:
        return None
    depth = 0
    for idx in range(open_idx, len(ctokens)):
        t = ctokens[idx].text
        if t == opener:
            depth += 1
        elif t == closer:
            depth -= 1
            if depth == 0:
                return idx
    return None


def split_args(ctokens: List[CToken], open_idx: int) -> List[Tuple[int, int]] | None:
    """
    Token-index spans of the top-level, comma-separated items between the delimiter at `ctokens[open_idx]` and its
    match, e.g. the arguments of a call `f(a, b)` or the elements of an initializer `{a, b}`.

    Returns one `(lo, hi)` half-open token-index span per item. Every top-level comma ends an item, so a missing item
    (`f(a,,b)`, `f(a,)`) is an empty span; only `()` with nothing inside yields `[]`. Commas nested inside
    `()`/`[]`/`{}` do not split, and a stray closer stays in its item without hiding later commas.
    Returns None under the same conditions as `match_delimiter` (out of range, not an opener, or never closed).
    """
    close_idx = match_delimiter(ctokens, open_idx)
    if close_idx is None:
        return None
    args: List[Tuple[int, int]] = []
    depth = 0
    lo_idx = open_idx + 1
    for idx in range(open_idx + 1, close_idx):
        current_token = ctokens[idx].text
        if current_token in CLOSER_FOR:
            depth += 1
        elif current_token in CLOSER_FOR.values():
            depth = max(0, depth - 1)  # a stray closer must not hide later top-level commas
        elif depth == 0 and current_token == ",":
            args.append((lo_idx, idx))
            lo_idx = idx + 1
    if lo_idx < close_idx or args:  # trailing arg, unless this is an empty `()`
        args.append((lo_idx, close_idx))
    return args


def has_top_level_token(ctokens: List[CToken], lo_idx: int, hi_idx: int, token_texts: frozenset) -> bool:
    """
    True if any token in `ctokens[lo_idx:hi_idx]` has its text in `token_texts` at delimiter depth 0 within the slice.

    Depth is counted from `lo_idx`; a stray closer is ignored rather than pushing later tokens below depth 0.
    Delimiters themselves (`()[]{}`) only change the depth and are never reported, even if they are in `token_texts`.
    The slice is clamped to `ctokens`, so indices outside it are never read.
    """
    depth = 0
    for idx in range(max(0, lo_idx), min(hi_idx, len(ctokens))):
        current_token = ctokens[idx].text
        if current_token in CLOSER_FOR:
            depth += 1
        elif current_token in CLOSER_FOR.values():
            depth = max(0, depth - 1)  # a stray closer must not hide later top-level tokens
        elif depth == 0 and current_token in token_texts:
            return True
    return False


# Characters that can appear in a C identifier or keyword.
WORD_CHARS = frozenset(string.ascii_letters + string.digits + "_")


def word_before(code_chars: List[str], end_idx: int) -> str:
    """
    Return the identifier or keyword that ends right before `code_chars[end_idx]`, read backwards from
    `code_chars[end_idx - 1]`.

    `code_chars` is the code as single characters with whitespace removed and strings/comments skipped, so a caller can
    ask which word precedes a `{` or `(` at `end_idx`: for `} else {` the word before the `{` is `else`.
    Because there is no whitespace, adjacent words read back glued together (`else if (` gives `elseif`, `struct foo {`
    gives `structfoo`).
    Only ASCII letters, digits, and `_` (`WORD_CHARS`) form a word. Returns `""` if `end_idx` is 0, the character before
    it is not a word character, or the run starts with a digit (the tail of a number such as `1` or `0x1F`, never a
    valid identifier).
    """
    word = ""
    idx = end_idx - 1
    while idx >= 0 and code_chars[idx] in WORD_CHARS:
        word = code_chars[idx] + word  # prepend, since we walk backwards
        idx -= 1
    if word[:1].isdigit():
        return ""
    return word
