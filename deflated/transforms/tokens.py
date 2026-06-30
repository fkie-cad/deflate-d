"""Token-stream toolkit: the layer between the lexer and the transforms.

``lexer.scan`` segments source into code / string / char / comment regions. The
structural transforms need a finer view --- a stream of C tokens with their
source offsets --- so they can reason about *structure* (balanced delimiters,
statement boundaries, operator sequences) without re-parsing raw text.

This module is that view, and it deliberately stops short of a parse tree. We do
not build an AST because decompiler output is frequently not valid, complete C
(synthetic types such as ``undefined4`` and ``code *``, intrinsics such as
``CONCAT44``, undeclared structs): a real C parser would reject it, while a
permissive token stream walked with explicit depth counters degrades gracefully
and lets each transform bail out the moment structure becomes ambiguous. Regex
is used only for *lexical* token shapes (the one place it is the right tool);
all *structural* decisions are made by walking these tokens.

Every function here is string/char/comment-safe: literal and comment regions
enter the stream as single opaque tokens, so their contents never participate in
matching.
"""

from __future__ import annotations

import re

from .lexer import SegmentType, scan

Token = tuple[str, int, int]  # (text, start, end) into the original string

# A single C token: multi-char operators first (so they are not split), then
# identifiers, hex/decimal numbers, and finally any single non-space character.
TOKEN = re.compile(
    r"<<=|>>=|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=" r"|[A-Za-z_]\w*" r"|0[xX][0-9a-fA-F]+" r"|\d+\.?\d*" r"|\S"
)


def tokenize(s: str) -> list[Token]:
    """Tokenize ``s`` into ``(text, start, end)`` triples (string/comment-safe).

    String, character, and comment regions are emitted as one opaque token each,
    so their contents never participate in token matching.
    """
    out: list[Token] = []
    pos = 0
    for seg_type, text in scan(s):
        if seg_type != SegmentType.CODE:
            if text.strip():
                out.append((text, pos, pos + len(text)))
            pos += len(text)
            continue
        for m in TOKEN.finditer(text):
            out.append((m.group(0), pos + m.start(), pos + m.end()))
        pos += len(text)
    return out


def split_statements(code: str) -> list[str]:
    """Split ``code`` into pieces at top-level ``;``, ``{``, ``}``.

    Depth-aware (``()``/``[]`` are not split points) and string-safe (via the
    scanner). Each delimiter stays attached to its piece; concatenating the
    pieces reproduces ``code`` exactly.
    """
    pieces: list[str] = []
    cur: list[str] = []
    depth = 0
    for seg_type, text in scan(code):
        if seg_type != SegmentType.CODE:
            cur.append(text)
            continue
        for ch in text:
            cur.append(ch)
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth = max(0, depth - 1)
            elif depth == 0 and ch in ";{}":
                pieces.append("".join(cur))
                cur = []
    if cur:
        pieces.append("".join(cur))
    return pieces


def match_delim(toks: list[Token], i: int, op: str, cl: str) -> int | None:
    """Index of the delimiter matching ``toks[i] == op``, or None."""
    depth = 0
    for j in range(i, len(toks)):
        t = toks[j][0]
        if t == op:
            depth += 1
        elif t == cl:
            depth -= 1
            if depth == 0:
                return j
    return None


def split_args(toks: list[Token], open_idx: int, close_idx: int) -> list[tuple[int, int]]:
    """Token-index spans of the top-level, comma-separated arguments of a call.

    ``open_idx``/``close_idx`` are the indices of a matched ``(`` / ``)``. Returns
    one ``(lo, hi)`` half-open token-index span per argument; the empty arg list
    ``()`` yields ``[]``. Commas nested inside ``()``/``[]``/``{}`` do not split.
    """
    args: list[tuple[int, int]] = []
    depth = 0
    lo = open_idx + 1
    for j in range(open_idx + 1, close_idx):
        t = toks[j][0]
        if t in "([{":
            depth += 1
        elif t in ")]}":
            depth -= 1
        elif depth == 0 and t == ",":
            args.append((lo, j))
            lo = j + 1
    if lo < close_idx or args:  # trailing arg, unless this is an empty `()`
        args.append((lo, close_idx))
    return args


def has_top(toks: list[Token], lo: int, hi: int, chars: frozenset) -> bool:
    """True if any token in ``toks[lo:hi]`` is in ``chars`` at delimiter depth 0."""
    depth = 0
    for j in range(lo, hi):
        t = toks[j][0]
        if t in "([{":
            depth += 1
        elif t in ")]}":
            depth -= 1
        elif depth == 0 and t in chars:
            return True
    return False


def word_before(sig: list[str], k: int) -> str:
    """Return the identifier/keyword whose last character sits at ``sig[k-1]``.

    ``sig`` is a list of significant (non-whitespace) code characters, as built
    by callers that need to look back past a delimiter to the preceding word.
    """
    j = k - 1
    out: list[str] = []
    while j >= 0 and (sig[j].isalnum() or sig[j] == "_"):
        out.append(sig[j])
        j -= 1
    return "".join(reversed(out))
