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
from typing import Callable, List, Tuple

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


def scan(code: str) -> List[Segment]:
    """
    Split `code` into ordered `(SegmentType, text)` segments whose texts concatenate back to `code` exactly.

    A string still open at a bare newline (malformed output, e.g. Binary Ninja's unescaped embedded quotes) is frozen:
    everything from the first quote on that line up to the newline becomes one `STRING` segment, so a stray quote
    cannot swallow the following lines. A `\\`-newline continuation keeps a string open and is not frozen.
    """
    segments: List[Segment] = []
    string_starts: List[int] = []  # start offsets of all closed strings, in order
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
            if match["close"]:
                string_starts.append(current_position)
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
    True if the STRING segment `text` is a normally closed `"..."`, False if it is a frozen one from function `scan`.

    Line-joining transforms use this to keep the newline after a frozen string, so its content is not glued onto the
    next line of code.
    """
    match = _STRING.match(text)
    return bool(match and match["close"] and match.end() == len(text))


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
