"""
A minimal C-like scanner that segments decompiler output into code, string, char, comment, and asm regions.

Transforms must only edit real code: a `//` inside a string is not a comment, and whitespace inside a literal is
significant. Transforms therefore edit only `CODE` segments and pass everything else through verbatim.

Deliberately not a full C parser, just enough lexical state to be safe on (possibly malformed) decompiler output.
"""

from __future__ import annotations

import re
from bisect import bisect_left
from enum import StrEnum
from typing import Callable, Iterator, List, Optional, Tuple

# A C char constant closed on the same line: one or more escapes (`\xHH`, `\uHHHH`, octal, `\<char>`) or plain chars.
# One-or-more, because decompilers emit multi-char constants like `'ABCD'` (int magic values).
_CHAR_LIT = re.compile(r"'(?:\\(?:x[0-9a-fA-F]+|u[0-9a-fA-F]{4}|[0-7]{1,3}|.)|[^'\\\n])+'")

# A line comment, ending before the `\r` of a `\r\n`; a `\` before the newline (`\n` or `\r\n`, line continuation) runs
# it onto the next line.
_LINE_COMMENT = re.compile(r"//(?:\\\r?\n|[^\r\n])*")

# A block comment; an unclosed one runs to the end.
_BLOCK_COMMENT = re.compile(r"/\*.*?(?:\*/|\Z)", re.S)

# A string up to its closing quote or a bare newline. `\` escapes the next char, a newline too (`\n` or `\r\n`, line
# continuation). Group `close` is the closing quote, empty if the string is unclosed.
_STRING = re.compile(r'"(?:\\\r\n|\\.?|[^"\\\n])*(?P<close>"?)', re.S)

# An encoding prefix directly before the quote of a string or char literal (`L"wide"`, `u8'a'`). It is part of the
# literal: split off as code, a pass could put a space between and turn it into an identifier `L`.
_LITERAL_PREFIX = re.compile(r"(?:u8|[LuU])(?=[\"'])")
_LITERAL_PREFIX_BEFORE_QUOTE = re.compile(r"(?<!\w)(?:u8|[LuU])\Z")

# A newline, kept as its own part when splitting.
_NEWLINE = re.compile(r"(\n)")

# An IDA/Hex-Rays `__asm { ... }` block: `__asm` as a whole word, the `{` possibly on the next line. MASM braces never
# nest, so the first `}` closes it; an unclosed block runs to the end.
_ASM_BLOCK = re.compile(r"\b__asm\s*\{[^}]*\}?")


class SegmentType(StrEnum):
    CODE = "code"
    STRING = "string"
    CHAR = "char"
    LINE_COMMENT = "line_comment"
    BLOCK_COMMENT = "block_comment"
    ASM = "asm"  # IDA/Hex-Rays inline `__asm { ... }` block (opaque)
    DIRECTIVE = "directive"  # a whole preprocessor directive; only from `split_directives`, never from `scan`


Segment = Tuple[SegmentType, str]


def _closes_backtick_name(src: str, code_start: int, quote_pos: int) -> bool:
    """
    True if the `'` at `src[quote_pos]` closes an MSVC backtick name such as Animal::`vftable', i.e. an open backtick
    precedes it in the same line's pending code run (from `code_start`, so backticks in strings or comments don't
    count). Such a `'` must not start a char literal, or it would pair with a later `'` on the line and hide the code
    between them.
    """
    line_before = src[max(code_start, src.rfind("\n", 0, quote_pos) + 1) : quote_pos]
    return line_before.rfind("`") > line_before.rfind("'")


def _literal_start(src: str, code_start: int, quote_pos: int) -> int:
    """
    Start of the literal whose quote is at `src[quote_pos]`: at its encoding prefix if a whole word `L`, `u`, `U` or `u8`
    in the pending code run (from `code_start`) directly precedes the quote, else at the quote.
    """
    match = _LITERAL_PREFIX_BEFORE_QUOTE.search(src, max(code_start, quote_pos - 2), quote_pos)
    return match.start() if match else quote_pos


def scan(code: str) -> List[Segment]:
    """
    Split `code` into ordered `(SegmentType, text)` segments whose texts concatenate back to `code` exactly.

    A string still open at a bare newline (malformed output, e.g. Binary Ninja's unescaped embedded quotes) is frozen:
    everything from the first quote on that line up to the newline becomes one `STRING` segment, so a stray quote
    cannot swallow the following lines. A `\\`-newline continuation keeps a string open and is not frozen.
    An encoding prefix (`L"wide"`, `u8'a'`) belongs to its string or char segment.
    """
    segments: List[Segment] = []
    string_starts: List[int] = []  # start offsets of all closed strings (prefix included), in order
    code_length = len(code)
    current_position = 0
    code_start = 0  # start of the pending code run; segments always cover code[:code_start]

    while current_position < code_length:
        current_character = code[current_position]
        segment_start = current_position
        if current_character == "/" and (match := _LINE_COMMENT.match(code, current_position)):
            seg_type, end = SegmentType.LINE_COMMENT, match.end()
        elif current_character == "/" and (match := _BLOCK_COMMENT.match(code, current_position)):
            seg_type, end = SegmentType.BLOCK_COMMENT, match.end()
        elif current_character == '"' and (match := _STRING.match(code, current_position)):
            seg_type, end = SegmentType.STRING, match.end()
            segment_start = _literal_start(code, code_start, current_position)
            if match["close"]:
                string_starts.append(segment_start)
            else:
                # Unclosed: this line's quotes are unreliable, so freeze from its first string to the newline.
                first = bisect_left(string_starts, code.rfind("\n", 0, current_position) + 1)
                if first < len(string_starts):
                    segment_start = string_starts[first]
        elif (
            current_character == "'"
            and not _closes_backtick_name(code, code_start, current_position)
            and (match := _CHAR_LIT.match(code, current_position))
        ):
            seg_type, end = SegmentType.CHAR, match.end()
            segment_start = _literal_start(code, code_start, current_position)
        elif current_character == "_" and (match := _ASM_BLOCK.match(code, current_position)):
            # Frozen, so no transform renames its registers or reflows its operands.
            seg_type, end = SegmentType.ASM, match.end()
        else:
            current_position += 1  # plain code
            continue

        while code_start > segment_start:  # a frozen string swallows the segments before it on its line
            code_start -= len(segments.pop()[1])
        if segment_start > code_start:
            segments.append((SegmentType.CODE, code[code_start:segment_start]))
        segments.append((seg_type, code[segment_start:end]))
        current_position = code_start = end

    if code_length > code_start:
        segments.append((SegmentType.CODE, code[code_start:]))
    return segments


def string_is_terminated(text: str) -> bool:
    """
    True if the STRING segment `text` is a normally closed `"..."` (encoding prefix allowed), False if it is a frozen
    one from function `scan`.

    Line-joining transforms use this to keep the newline after a frozen string, so its content is not glued onto the
    next line of code.
    """
    prefix = _LITERAL_PREFIX.match(text)
    match = _STRING.match(text, prefix.end() if prefix else 0)
    return bool(match and match["close"] and match.end() == len(text))


def ends_with_literal_prefix(text: str) -> bool:
    """True if `text` ends in the whole word `L`, `u`, `U` or `u8`, which a following quote would make a prefix."""
    return _LITERAL_PREFIX_BEFORE_QUOTE.search(text) is not None


def _code_lines(segments: List[Segment]) -> Iterator[Segment]:
    """Yield `segments` with each CODE segment cut at its newlines, so every newline in code is its own piece."""
    for seg_type, text in segments:
        if seg_type != SegmentType.CODE:
            yield seg_type, text
            continue
        for part in _NEWLINE.split(text):
            if part:
                yield SegmentType.CODE, part


def _merge_code(segments: List[Segment]) -> List[Segment]:
    """Join neighbouring CODE segments into one."""
    merged: List[Segment] = []
    for seg_type, text in segments:
        if seg_type == SegmentType.CODE and merged and merged[-1][0] == SegmentType.CODE:
            merged[-1] = (SegmentType.CODE, merged[-1][1] + text)
        else:
            merged.append((seg_type, text))
    return merged


def _pop_line_prefix(segments: List[Segment]) -> str:
    """
    Take the current line's text before a directive's `#` back off the end of `segments` and return it.

    `split_directives` only sees the `#` after it has already emitted the comments and blanks before it on that line
    (`/* c */ #define A 1`). This pops them, back to the last newline, so they become the start of the directive and a
    `DIRECTIVE` segment always covers whole lines.
    """
    prefix_parts: List[str] = []
    while segments and segments[-1][1] != "\n":
        prefix_parts.append(segments.pop()[1])
    return "".join(reversed(prefix_parts))


def split_directives(segments: List[Segment]) -> List[Segment]:
    """
    Return the `scan` output `segments` with each preprocessor directive merged into one `DIRECTIVE` segment.

    A directive runs from a `#` that is the first token on its line (comments and blanks before it belong to it) to the
    first newline in code that does not follow a `\\`, so it spans strings, comments and continuation lines.
    """
    split_segments: List[Segment] = []
    directive: Optional[str] = None
    at_line_start = True  # only blanks and block comments since the last newline in code
    continued = False  # the code just before ends in a `\`
    for seg_type, text in _code_lines(segments):
        ends_line = seg_type == SegmentType.CODE and text == "\n" and not continued
        continued = seg_type == SegmentType.CODE and text.rstrip().endswith("\\")
        if directive is not None and not ends_line:
            directive += text
            continue
        if directive is not None:
            split_segments.append((SegmentType.DIRECTIVE, directive))
            directive = None
        elif at_line_start and seg_type == SegmentType.CODE and text.lstrip(" \t").startswith("#"):
            directive = _pop_line_prefix(split_segments) + text
            continue
        split_segments.append((seg_type, text))
        at_line_start = text == "\n" or (at_line_start and (seg_type == SegmentType.BLOCK_COMMENT or not text.strip()))
    if directive is not None:
        split_segments.append((SegmentType.DIRECTIVE, directive))
    return _merge_code(split_segments)


def map_code(code: str, edit: Callable[[str], str]) -> str:
    """Apply `edit` to every `CODE` segment of `code` and leave the rest verbatim."""
    return "".join(edit(text) if seg_type == SegmentType.CODE else text for seg_type, text in scan(code))


def strip_comments(code: str, keep_warnings: bool = False) -> str:
    """
    Remove line and block comments, keeping strings and code.

    A block comment becomes a single space so the surrounding tokens don't merge. With `keep_warnings`, block comments
    containing `WARNING` (decompiler reliability banners) are kept.
    """
    resulting_code: List[str] = []
    for seg_type, text in scan(code):
        if seg_type == SegmentType.LINE_COMMENT:
            continue
        if seg_type == SegmentType.BLOCK_COMMENT:
            resulting_code.append(text if (keep_warnings and "WARNING" in text) else " ")
        else:
            resulting_code.append(text)
    return "".join(resulting_code)


def lines_with_protection(code: str) -> List[Tuple[str, bool, bool]]:
    """
    Split `code` at linebreaks and return one `(line, starts_protected, ends_protected)` triple per line.

    `starts_protected` is True if the line's first character is inside a string, char literal or `__asm` block, so its
    leading whitespace must be kept. `ends_protected` is the same for the last character and trailing whitespace.
    The two can differ because a multi-line string or `__asm` block can open or close mid-line.
    An empty line gets `(True, True)` if it lies inside an `__asm` block, so it is not removed as a blank line.
    """
    protected_types = (SegmentType.STRING, SegmentType.CHAR, SegmentType.ASM)
    protected_mask = bytearray(len(code))
    offset = 0
    for seg_type, text in scan(code):
        if seg_type in protected_types:
            protected_mask[offset : offset + len(text)] = b"\x01" * len(text)
        offset += len(text)

    protected_ends: List[Tuple[str, bool, bool]] = []
    line_start = 0
    for line in code.split("\n"):
        if line:
            protected_ends.append(
                (line, bool(protected_mask[line_start]), bool(protected_mask[line_start + len(line) - 1]))
            )
        else:
            inside_protected_area = bool(protected_mask[line_start]) if line_start < len(code) else False
            protected_ends.append((line, inside_protected_area, inside_protected_area))
        line_start += len(line) + 1  # + 1 for the "\n" that split() removed
    return protected_ends
