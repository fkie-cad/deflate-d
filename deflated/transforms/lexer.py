"""A minimal C-like scanner that segments source into code / string / char /
comment regions.

Token-reduction transforms must not corrupt the *meaning* of the code: a `//`
inside a string literal is not a comment, and whitespace inside a string is
significant. Every transform that could touch those regions runs through this
scanner so it only edits ``code`` segments and leaves literals/comments intact.

This is deliberately not a full C parser --- it tracks just enough lexical
state (strings, char literals, line/block comments, escapes) to be safe on
decompiler output.
"""

from __future__ import annotations

import re
from enum import StrEnum

# A well-formed C character literal: a single char or a standard escape,
# closed on the same line. Decompilers (esp. MSVC C++ output) also emit lone
# apostrophes inside special names such as ``Animal::`vftable'`` and
# ``Foo::`scalar deleting destructor'``; those are *not* char literals, so a
# ``'`` that does not match this is treated as ordinary code (see ``scan``).
_CHAR_LIT = re.compile(r"'(?:\\(?:x[0-9a-fA-F]+|u[0-9a-fA-F]{4}|[0-7]{1,3}|.)|[^'\\\n])'")


class SegmentType(StrEnum):
    CODE          = "code"
    STRING        = "string"
    CHAR          = "char"
    LINE_COMMENT  = "line_comment"
    BLOCK_COMMENT = "block_comment"
    ASM           = "asm"  # IDA/Hex-Rays inline `__asm { ... }` block (opaque)


Segment = tuple[SegmentType, str]


def _asm_block_end(src: str, i: int, n: int) -> int | None:
    """If a standalone ``__asm { ... }`` block starts at ``src[i]``, return the
    offset just past its closing ``}``; otherwise None.

    Handles both the single-line (``__asm { cpuid }``) and the brace-on-next-line
    form IDA emits. MASM-syntax asm braces never nest, so the first ``}`` closes
    the block. ``__asm`` must be a whole token (no leading identifier char), so
    ``my__asm`` is not matched.
    """
    if not src.startswith("__asm", i):
        return None
    if i > 0 and (src[i - 1].isalnum() or src[i - 1] == "_"):
        return None  # part of a longer identifier
    j = i + 5
    if j < n and (src[j].isalnum() or src[j] == "_"):
        return None  # e.g. `__asmfoo`
    while j < n and src[j] in " \t\r\n":
        j += 1
    if j >= n or src[j] != "{":
        return None  # bare `__asm` keyword without a block: leave as code
    k = src.find("}", j)
    return n if k == -1 else k + 1


def scan(src: str) -> list[Segment]:
    """Split ``src`` into ordered ``(kind, text)`` segments.

    Concatenating every segment's text reproduces ``src`` exactly.

    A double-quoted string normally closes on its own physical line. When one is
    left *unclosed* at a bare newline --- malformed decompiler output such as
    Binary Ninja's unescaped embedded quotes (``"  File: "%n"...``) or a
    truncated literal --- everything from the *first* quote on that line through
    to the newline is emitted as one opaque ``STRING`` segment ("frozen"). This
    both stops a stray quote from cascading over the *following* lines of real
    code and keeps the malformed line's bytes (which may be string content the
    lexer cannot delimit) away from every transform. Code before that first quote
    has no quote to misparse, so it is left as ordinary code and still compresses.
    A ``\\``-newline continuation legitimately keeps a string open, so a genuinely
    continued literal is not frozen.
    """
    segments: list[Segment] = []
    n = len(src)
    i = 0
    start = 0  # start of the current code run; segments always cover src[0:start]

    def flush_code(end: int) -> None:
        if end > start:
            segments.append((SegmentType.CODE, src[start:end]))

    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""

        if c == "/" and nxt == "/":
            flush_code(i)
            j = src.find("\n", i)
            if j == -1:
                j = n
            # A line comment ending in '\' (line continuation) runs onto the next line.
            while i < j < n and src[j - 1] == "\\":
                j = src.find("\n", j + 1)
                if j == -1:
                    j = n
            segments.append((SegmentType.LINE_COMMENT, src[i:j]))
            i = j
            start = i
        elif c == "/" and nxt == "*":
            flush_code(i)
            j = src.find("*/", i + 2)
            end = n if j == -1 else j + 2
            segments.append((SegmentType.BLOCK_COMMENT, src[i:end]))
            i = end
            start = i
        elif c == '"':
            # Find the literal's end. '\' escapes the next char (incl. a newline:
            # a line continuation keeps the string open). A *bare* newline means
            # the literal is unclosed on its line -> malformed decompiler output.
            j = i + 1
            closed = False
            bare_nl = -1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == '"':
                    j += 1
                    closed = True
                    break
                if src[j] == "\n":
                    bare_nl = j
                    break
                j += 1
            if closed:
                flush_code(i)
                segments.append((SegmentType.STRING, src[i:j]))
                i = j
                start = i
            else:
                # Unclosed literal: the quote structure on this physical line is
                # unreliable (Binary Ninja's unescaped embedded quotes, or a
                # truncated string), so freeze from the *first* string opened on
                # the line through to the newline as one opaque STRING. This stops
                # a stray quote from cascading onto the next line and keeps the
                # ambiguous bytes away from every transform. Code (and any char
                # literals) before that first quote is unambiguous --- it has no
                # quote to misparse --- so it is left intact and still compresses.
                ls = src.rfind("\n", 0, i) + 1
                end = bare_nl if bare_nl != -1 else n
                freeze = i  # default: this quote is the first string on the line
                off = start
                for kind, text in reversed(segments):
                    off -= len(text)
                    if off < ls:
                        break  # segment began on an earlier line; stop here
                    if kind == SegmentType.STRING:
                        freeze = off
                while start > freeze:
                    start -= len(segments[-1][1])
                    segments.pop()
                flush_code(freeze)
                segments.append((SegmentType.STRING, src[freeze:end]))
                i = end
                start = end
        elif c == "'":
            m = _CHAR_LIT.match(src, i)
            if m:
                flush_code(i)
                segments.append((SegmentType.CHAR, m.group(0)))
                i = m.end()
                start = i
            else:
                # Lone apostrophe (e.g. MSVC `vftable'): ordinary code, so the
                # rest of the line is still seen by comment/name transforms.
                i += 1
        elif c == "_" and (end := _asm_block_end(src, i, n)) is not None:
            # IDA/Hex-Rays inline asm `__asm { ... }`: freeze the whole block so
            # no transform renames its registers/stack aliases or reflows its
            # operands (`[rsp+var_28]` is hardware, not a pseudocode placeholder).
            flush_code(i)
            segments.append((SegmentType.ASM, src[i:end]))
            i = end
            start = i
        else:
            i += 1

    flush_code(n)
    return segments


def string_is_terminated(text: str) -> bool:
    """True if ``text`` is a normally-closed ``"..."`` STRING segment --- its first
    unescaped closing quote is its last character.

    :func:`scan` also emits *frozen* STRING segments for malformed lines (an
    unclosed or embedded-quote literal, captured from the first quote up to the
    newline); those are not terminated. Line-joining transforms use this to keep
    the newline that bounds a frozen literal instead of collapsing it, which would
    glue the malformed string content onto the next line of real code.
    """
    if len(text) < 2 or text[0] != '"':
        return False
    j = 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == '"':
            return j == len(text) - 1
        j += 1
    return False


def map_code(src: str, fn) -> str:
    """Apply ``fn`` to every code segment of ``src``; leave the rest verbatim."""
    return "".join(fn(text) if seg_type == SegmentType.CODE else text for seg_type, text in scan(src))


def strip_comments(src: str, keep_warnings: bool = False) -> str:
    """Remove line and block comments, preserving strings and code.

    Block comments collapse to a single space so adjacent tokens don't merge;
    line comments are dropped entirely (their trailing newline lives in the
    following code segment). With ``keep_warnings=True``, block comments whose
    text mentions ``WARNING`` (decompiler reliability banners) are preserved ---
    they are analyst signal, not noise.
    """
    out: list[str] = []
    for seg_type, text in scan(src):
        if seg_type == SegmentType.LINE_COMMENT:
            continue
        if seg_type == SegmentType.BLOCK_COMMENT:
            out.append(text if (keep_warnings and "WARNING" in text) else " ")
        else:
            out.append(text)
    return "".join(out)


def protected_line_edges(src: str) -> list[tuple[bool, bool]]:
    """For each physical line of ``src``, return ``(lead, trail)``: whether the
    line's first / last character lies inside a string/char literal or an
    ``__asm { ... }`` block as classified by :func:`scan`.

    Strings and char literals are protected because their whitespace is
    program-meaningful, and ``__asm`` blocks because they are frozen opaque
    regions: the line-oriented passes (indent / trailing / blank-line) would
    otherwise de-indent and reflow their interior --- the multi-line interior of
    one such block is the one place these passes can reach a non-CODE region,
    since the character-level passes go through ``map_code`` (CODE only) and
    ``ws-newlines`` emits non-CODE segments verbatim. Comment whitespace is *not*
    protected (it is normalised by ``ws-comments`` and discarded at T2). A line
    may be part code and part protected region --- it can open or close a
    multi-line string or asm block --- so the leading and trailing positions are
    reported separately. An empty line reports the protection of its position, so
    a blank line inside a multi-line string is recognised as protected content
    rather than ordinary code. Line-oriented transforms use this to edit only
    genuine code whitespace and leave literal/asm interiors untouched.
    """
    protected_segs = (SegmentType.STRING, SegmentType.CHAR, SegmentType.ASM)
    protected = bytearray(len(src))
    offset = 0
    for seg_type, text in scan(src):
        if seg_type in protected_segs:
            protected[offset : offset + len(text)] = b"\x01" * len(text)
        offset += len(text)

    edges: list[tuple[bool, bool]] = []
    pos = 0
    for line in src.split("\n"):
        if line:
            edges.append((bool(protected[pos]), bool(protected[pos + len(line) - 1])))
        else:
            here = bool(protected[pos]) if pos < len(src) else False
            edges.append((here, here))
        pos += len(line) + 1  # + 1 for the "\n" that split() removed
    return edges
