"""
T1 cosmetic transforms: whitespace and layout changes only, so all of them are semantics-preserving.

No pass changes the inside of a string, char literal or `__asm` block. `ws-collapse`, `ws-tighten`, `ws-comments` and
`ws-newlines` work on the segments from `scan`. `ws-indent`, `ws-trailing` and `ws-blanklines` work line by line and
use `lines_with_protection` to skip line edges that lie inside a protected segment.
"""

from __future__ import annotations

import re
from itertools import pairwise
from typing import List, Optional, Set

from .base import Tier, Transform
from .lexer import (
    Segment,
    SegmentType,
    ends_with_literal_prefix,
    lines_with_protection,
    map_code,
    scan,
    split_directives,
    string_is_terminated,
)

_MULTI_BLANKS = re.compile(r"[ \t]{2,}")
_BLANKS = re.compile(r"[ \t]+")
# A C pp-number (`.`? digit, then word chars, `.` and exponent signs) or an identifier, read left to right.
_NUMBER_OR_IDENTIFIER = re.compile(r"(?P<number>\.?\d(?:[eEpP][+-]|[\w.])*)|(?P<identifier>[A-Za-z_]\w*)")

# Two operator chars whose adjacency would form a longer C token (or start a comment):
# removing the space between them would change how the code splits into C tokens.
_FUSING_PAIRS = frozenset(
    {
        "++",
        "--",
        "->",
        "<<",
        ">>",
        "<=",
        ">=",
        "==",
        "!=",
        "&&",
        "||",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "&=",
        "|=",
        "^=",
        "/*",
        "//",
        # C++ scope and pointer-to-member: decompilers of C++ binaries emit both.
        "::",
        ".*",
        # C digraphs (`<:` = `[` etc.): decompilers don't emit them, but keeping the space stays lossless.
        "<:",
        ":>",
        "<%",
        "%>",
        "%:",
    }
)


def _is_word_char(character: str) -> bool:
    """Check whether the input character is a word character in C."""
    return character.isalnum() or character == "_"


def _forms_pp_number(left: str, right: str) -> bool:
    """
    True if removing the space between `left` and `right` would extend or start a number, so the space must stay.

    C reads a number from a digit (or `.` + digit) on, taking all following digits, letters, `.` and the `+`/`-` of an
    exponent (`e+`, `p-`, ...). Only reading `left` from the start shows where its last number begins.
    Space kept: `5 .x`, `1.e5 .x`, `0x1e +5`, `5. x` (number before) and `x. 5`, `1 . 5` (`.` + digit).
    Space removed: `ab12 .x` becomes `ab12.x` (identifier, even if it ends in a digit), `x. y` becomes `x.y`.
    """
    words = list(_NUMBER_OR_IDENTIFIER.finditer(left))
    if words and words[-1].end() == len(left) and words[-1].lastgroup == "number":
        return _is_word_char(right[0]) or right[0] == "." or (right[0] in "+-" and left[-1] in "eEpP")
    return left[-1] == "." and right[0].isdigit()


def _forms_literal_prefix(left: str, right: str) -> bool:
    """
    True if `left` ends in the word `L`, `u`, `U` or `u8` and `right` starts a string or char literal.

    Joined, the two would lex as one prefixed literal: `L "s"` (identifier, string) becomes the wide string `L"s"`.
    """
    return right[0] in "\"'" and ends_with_literal_prefix(left)


def _needs_space(left: str, right: str) -> bool:
    """
    True if the space between the non-empty tokens `left` and `right` cannot be removed without changing how they lex.
    """
    a, b = left[-1], right[0]
    return (
        (_is_word_char(a) and _is_word_char(b))
        or a + b in _FUSING_PAIRS
        or _forms_pp_number(left, right)
        or _forms_literal_prefix(left, right)
    )


def _tighten_line(line: str) -> str:
    """
    Remove all spaces and tabs from `line`, keeping a single space only where `_needs_space` requires one.
    """
    parts = _BLANKS.split(line.strip(" \t"))
    tightened_parts: List[str] = [parts[0]]
    for left, right in pairwise(parts):
        if _needs_space(left, right):
            tightened_parts.append(" ")
        tightened_parts.append(right)
    return "".join(tightened_parts)


def _is_frozen_string(seg_type: SegmentType, text: str) -> bool:
    """Check whether the segment is a frozen (unterminated) string from `scan`."""
    return seg_type == SegmentType.STRING and not string_is_terminated(text)


class CollapseInlineSpaces(Transform):
    """Collapse runs of 2+ spaces/tabs to a single space, in code only."""

    id = "ws-collapse"
    tier = Tier.T1_COSMETIC
    description = "Collapse any combination of 2+ spaces/tabs into a single space in code."

    def apply(self, code: str) -> str:
        return map_code(code, lambda s: _MULTI_BLANKS.sub(" ", s))


class StripIndentation(Transform):
    """Remove leading whitespace from each line, unless the line starts inside a string, char or `__asm` block."""

    id = "ws-indent"
    tier = Tier.T1_COSMETIC
    description = "Remove leading whitespace from each line."

    def apply(self, code: str) -> str:
        return "\n".join(
            line if starts_protected else line.lstrip() for line, starts_protected, _ in lines_with_protection(code)
        )


class StripTrailingWhitespace(Transform):
    """Remove trailing whitespace from each line, unless the line ends inside a string, char or `__asm` block."""

    id = "ws-trailing"
    tier = Tier.T1_COSMETIC
    description = "Remove trailing whitespace from each line."

    def apply(self, code: str) -> str:
        return "\n".join(
            line if ends_protected else line.rstrip() for line, _, ends_protected in lines_with_protection(code)
        )


class CollapseBlankLines(Transform):
    """
    Reduce each run of blank or whitespace-only lines to one blank line and remove blank lines at the start and end.
    """

    id = "ws-blanklines"
    tier = Tier.T1_COSMETIC
    description = "Collapse consecutive blank lines to one and drop leading/trailing blanks."

    def apply(self, code: str) -> str:
        transformed_code_lines: List[str] = []
        for line, starts_protected, _ in lines_with_protection(code):
            if line.strip() or starts_protected:  # real content, or protected string interior
                transformed_code_lines.append(line)
            elif transformed_code_lines and transformed_code_lines[-1] != "":
                transformed_code_lines.append("")
        if transformed_code_lines and transformed_code_lines[-1] == "":
            transformed_code_lines.pop()
        return "\n".join(transformed_code_lines)


class TightenCommentSpaces(Transform):
    """
    In every comment, collapse runs of spaces/tabs to one space and strip leading and trailing whitespace.

    Newlines in block comments are kept, and an unterminated `/*` does not get a `*/` added.
    """

    id = "ws-comments"
    tier = Tier.T1_COSMETIC
    description = "Strip and collapse whitespace inside comments."

    def apply(self, code: str) -> str:
        transformed_segments: List[str] = []
        for seg_type, text in scan(code):
            if seg_type == SegmentType.LINE_COMMENT:
                interior = _BLANKS.sub(" ", text[2:]).strip(" \t")
                transformed_segments.append("//" + interior)
            elif seg_type == SegmentType.BLOCK_COMMENT:
                # An unterminated `/* ...` (run to EOF by the lexer) has no closer to strip or re-append:
                # keep the interior but don't fabricate `*/`. Note, `/*/` opens a comment, but does not close it.
                is_closed = text != "/*/" and text.endswith("*/")
                interior = text[2:-2] if is_closed else text[2:]
                interior = _BLANKS.sub(" ", interior).strip(" \t")
                transformed_segments.append("/*" + interior + ("*/" if is_closed else ""))
            else:
                transformed_segments.append(text)
        return "".join(transformed_segments)


class TightenWhitespace(Transform):
    """
    Remove every space or tab whose removal does not change how the code lexes (`while ( x )` -> `while(x)`).

    One space is kept where `_needs_space` requires it: between word characters (`int d`), between characters that
    would fuse into another token (`a - -b`, `a / *p`), and where a number would absorb a `.`. Preprocessor directives
    (see `split_directives`) are left unchanged. The same rule applies where code meets a comment, string or `__asm`
    block: `a / /* c */` keeps its space (else `//` starts a line comment), and so does `do __asm{...}` (else the lexer
    no longer sees the block).
    """

    id = "ws-tighten"
    tier = Tier.T1_COSMETIC
    description = "Remove unnecessary whitespace (includes most of ws-collapse, ws-indent, ws-trailing)."

    def apply(self, code: str) -> str:
        transformed_segments: List[str] = []
        previous_type: Optional[SegmentType] = None
        for seg_type, text in split_directives(scan(code)):
            if seg_type == SegmentType.DIRECTIVE:
                transformed_segments.append(text)
            elif seg_type == SegmentType.CODE:
                transformed_segments.append(self._tighten(text))
            else:
                # Tightened code can fuse with the start of the segment after it: `do __asm{...}` -> `do__asm{...}`,
                # `a / /* c */` -> `a//* c */`. Only the code was tightened, so only a code end needs checking.
                previous_code = transformed_segments[-1] if previous_type == SegmentType.CODE else ""
                if previous_code and _needs_space(previous_code, text):
                    transformed_segments.append(" ")
                transformed_segments.append(text)
            previous_type = seg_type
        return "".join(transformed_segments)

    @staticmethod
    def _tighten(text: str) -> str:
        """
        Tighten each line of the CODE piece `text` with `_tighten_line`.
        """
        return "\n".join(_tighten_line(line) for line in text.split("\n"))


class JoinLines(Transform):
    """
    Join all lines with single spaces, except where a line break is needed.

    A line break is kept after a `//` comment, which would otherwise swallow the code joined behind it. A preprocessor
    directive stays on its own line(s), unchanged apart from blanks at its start and end: it runs from a `#` that is the
    first token on a line to the first newline in code that does not follow a `\\`, so it can span block comments and
    continuation lines. A frozen (unterminated) string also keeps the line break after it. Its line is joined onto the
    previous one unless that line holds a closed string: `scan` freezes from the first closed string on a frozen
    string's line, so a re-scan would swallow the code in between.

    Where two pieces would lex differently once joined, a single space is kept between them, as `_needs_space` decides:
    `do\\n__asm{...}` -> `do __asm{...}`, `a /\\n/* c */` -> `a / /* c */` (else `//*` starts a line comment).
    """

    id = "ws-newlines"
    tier = Tier.T1_COSMETIC
    description = "Join lines into as few as possible, keeping only the line breaks the code needs."

    def apply(self, code: str) -> str:
        pieces = split_directives(scan(code))
        pieces_before_frozen_line = self._line_breaks_before_frozen_strings(pieces)
        transformed_segments: List[str] = []
        keep_following_newline = False
        closed_string_on_line = False

        def append_separated(segment: str, is_closed_string: bool = False) -> None:
            nonlocal closed_string_on_line
            if not segment:
                return
            if transformed_segments and _needs_space(transformed_segments[-1], segment):
                transformed_segments.append(" ")
            transformed_segments.append(segment)
            if "\n" in segment:
                closed_string_on_line = False
            elif is_closed_string:
                closed_string_on_line = True

        def start_new_line() -> None:
            if transformed_segments and not transformed_segments[-1].endswith("\n"):
                append_separated("\n")

        for index, (piece_type, text) in enumerate(pieces):
            if keep_following_newline:
                start_new_line()
            if piece_type == SegmentType.DIRECTIVE:
                start_new_line()
                append_separated(text.lstrip(" \t").rstrip(" \t\r"))
                keep_following_newline = True
                continue
            if piece_type == SegmentType.CODE:
                collapsed = self._collapse(text)
                if index in pieces_before_frozen_line and closed_string_on_line and "\n" not in collapsed:
                    head, last_line = text.rsplit("\n", 1)
                    append_separated(self._collapse(head))
                    start_new_line()
                    append_separated(self._collapse(last_line))
                else:
                    append_separated(collapsed)
                keep_following_newline = False
                continue
            is_frozen_string = _is_frozen_string(piece_type, text)
            append_separated(text, is_closed_string=piece_type == SegmentType.STRING and not is_frozen_string)
            keep_following_newline = piece_type == SegmentType.LINE_COMMENT or is_frozen_string
        return "".join(transformed_segments)

    @staticmethod
    def _line_breaks_before_frozen_strings(pieces: List[Segment]) -> Set[int]:
        """
        Return the indices of the CODE pieces that hold the last line break before a frozen string.
        """
        indices: Set[int] = set()
        for index, (piece_type, text) in enumerate(pieces):
            if not _is_frozen_string(piece_type, text):
                continue
            for previous_index in range(index - 1, -1, -1):
                previous_type, previous_text = pieces[previous_index]
                if "\n" in previous_text:
                    if previous_type == SegmentType.CODE:
                        indices.add(previous_index)
                    break
        return indices

    @staticmethod
    def _collapse(text: str) -> str:
        """
        Join the lines of the CODE piece `text` with single spaces and drop blank lines.
        """
        return " ".join(line.strip() for line in text.split("\n") if line.strip())
