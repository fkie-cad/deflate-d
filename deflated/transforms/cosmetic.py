"""
T1 cosmetic transforms: whitespace and layout changes only, so all of them are semantics-preserving.

No pass changes the inside of a string, char literal or `__asm` block. `ws-collapse`, `ws-tighten`, `ws-comments` and
`ws-newlines` work on the segments from `scan`. `ws-indent`, `ws-trailing` and `ws-blanklines` work line by line and
use `lines_with_protection` to skip line edges that lie inside a protected segment.
"""

from __future__ import annotations

import re
from itertools import groupby, pairwise
from typing import List

from .base import Tier, Transform
from .lexer import SegmentType, lines_with_protection, map_code, scan, string_is_terminated

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


def _needs_space(left: str, right: str) -> bool:
    """
    True if the space between the non-empty tokens `left` and `right` cannot be removed without changing how they lex.
    """
    a, b = left[-1], right[0]
    return (_is_word_char(a) and _is_word_char(b)) or a + b in _FUSING_PAIRS or _forms_pp_number(left, right)


def _tighten_line(line: str) -> str:
    """
    Remove all spaces and tabs from `line`, keeping a single space only where `_needs_space` requires one.
    """
    parts = _BLANKS.split(line.strip(" \t"))
    tightened_line: str = parts[0]
    for left, right in pairwise(parts):
        if _needs_space(left, right):
            tightened_line += " "
        tightened_line += right
    return tightened_line


def _directive_flags(all_lines: List[str]) -> List[bool]:
    """
    Return for each line of `all_lines` whether it is a preprocessor directive or a `\\` continuation of one.
    """
    flags: List[bool] = []
    inside_directive = False
    for line in all_lines:
        is_directive = inside_directive or line.lstrip().startswith("#")
        flags.append(is_directive)
        inside_directive = is_directive and line.rstrip().endswith("\\")
    return flags


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
        return "\n".join(line if starts_protected else line.lstrip() for line, starts_protected, _ in lines_with_protection(code))


class StripTrailingWhitespace(Transform):
    """Remove trailing whitespace from each line, unless the line ends inside a string, char or `__asm` block."""

    id = "ws-trailing"
    tier = Tier.T1_COSMETIC
    description = "Remove trailing whitespace from each line."

    def apply(self, code: str) -> str:
        return "\n".join(line if ends_protected else line.rstrip() for line, _, ends_protected in lines_with_protection(code))


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
        transformed_code: str = ""
        for seg_type, text in scan(code):
            if seg_type == SegmentType.LINE_COMMENT:
                interior = _BLANKS.sub(" ", text[2:]).strip(" \t")
                transformed_code += "//" + interior
            elif seg_type == SegmentType.BLOCK_COMMENT:
                # An unterminated `/* ...` (run to EOF by the lexer) has no closer to strip or re-append:
                # keep the interior but don't fabricate `*/`. Note, `/*/` opens a comment, but does not close it.
                is_closed = text != "/*/" and text.endswith("*/")
                interior = text[2:-2] if is_closed else text[2:]
                interior = _BLANKS.sub(" ", interior).strip(" \t")
                transformed_code += "/*" + interior + ("*/" if is_closed else "")
            else:
                transformed_code += text
        return transformed_code


class TightenWhitespace(Transform):
    """
    Remove every space or tab whose removal does not change how the code lexes (`while ( x )` -> `while(x)`).

    One space is kept where `_needs_space` requires it: between word characters (`int d`), between characters that
    would fuse into another token (`a - -b`, `a / *p`), and where a number would absorb a `.`. Preprocessor lines are
    left unchanged. A space is also kept before an `__asm` block if the code before it ends in a word character;
    otherwise `do __asm{...}` becomes `do__asm{...}` and the lexer no longer recognises the block.
    """

    id = "ws-tighten"
    tier = Tier.T1_COSMETIC
    description = "Remove unnecessary whitespace (includes most of ws-collapse, ws-indent, ws-trailing)."

    def apply(self, code: str) -> str:
        segments = scan(code)
        next_types = [seg_type for seg_type, _ in segments[1:]] + [None]
        out: List[str] = []
        for (seg_type, text), next_type in zip(segments, next_types):
            if seg_type != SegmentType.CODE:
                out.append(text)
                continue
            tight = self._tighten(text)
            if next_type == SegmentType.ASM and tight and _is_word_char(tight[-1]):
                tight += " "
            out.append(tight)
        return "".join(out)

    @staticmethod
    def _tighten(text: str) -> str:
        """
        Tighten each line of the CODE segment `text` with `_tighten_line`, leaving directive lines unchanged.
        """
        lines = text.split("\n")
        return "\n".join(line if is_directive else _tighten_line(line) for line, is_directive in zip(lines, _directive_flags(lines)))


class JoinLines(Transform):
    """
    Join all lines with single spaces, except where a line break is needed.

    A line break is kept after a `//` comment, before and after a frozen string, and around each preprocessor directive
    (including its `\\` continuation lines).
    """

    id = "ws-newlines"
    tier = Tier.T1_COSMETIC
    description = "Join lines into as few as possible, keeping only the line breaks the code needs."

    def apply(self, code: str) -> str:
        out: List[str] = []
        keep_following_newline = False  # prev segment bounds its line: // comment or frozen string

        def append_separated(s: str) -> None:
            # Keep a space where a dropped newline would glue two word chars: do\n__asm{...} -> do __asm{...}.
            if s and out:
                prev = out[-1]
                if prev and _is_word_char(prev[-1]) and _is_word_char(s[0]):
                    out.append(" ")
            out.append(s)

        for seg_type, text in scan(code):
            if seg_type != SegmentType.CODE:
                is_frozen_string = seg_type == SegmentType.STRING and not string_is_terminated(text)
                # Start a frozen string on its own line. If it were joined to the previous code, a later re-scan would
                # see its stray quote mid-line and freeze the whole joined line as one literal.
                if is_frozen_string and out and not out[-1].endswith("\n"):
                    out.append("\n")
                append_separated(text)
                keep_following_newline = seg_type == SegmentType.LINE_COMMENT or is_frozen_string
                continue
            if keep_following_newline:
                out.append("\n")
            append_separated(self._collapse(text))
            keep_following_newline = False
        return "".join(out)

    @staticmethod
    def _collapse(text: str) -> str:
        """
        Join the lines of the CODE segment `text` with single spaces and drop blank lines; directive lines stay separate.
        """
        lines = text.split("\n")
        flags = _directive_flags(lines)
        out: List[str] = []
        for is_directive, group in groupby(zip(lines, flags), key=lambda pair: pair[1]):
            group_lines = [line for line, _ in group]
            if is_directive:
                out.extend(line.strip() for line in group_lines)
            else:
                joined = " ".join(line.strip() for line in group_lines if line.strip())
                if joined:
                    out.append(joined)
        return "\n".join(out)
