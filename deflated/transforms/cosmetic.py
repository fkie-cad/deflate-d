"""T1 --- cosmetic transforms.

Formatting that exists only for human readers.  All strictly lossless: program
semantics are untouched.  The space-editing passes run through the lexer
(``map_code`` / ``scan``) and touch only code segments, so string, char, and
comment interiors are preserved.  The line-oriented passes (indent / trailing /
blank-line) consult ``protected_line_edges`` to skip string and char literal
interiors --- including multi-line strings --- while still tidying comment
whitespace (normalised by ``ws-comments`` and discarded at T2).
"""

from __future__ import annotations

from itertools import groupby

import re
import string
from typing import List

from .base import Tier, Transform
from .lexer import SegmentType, map_code, protected_line_edges, scan, string_is_terminated

_INLINE_RUNS = re.compile(r"[ \t]{2,}")
_COMMENT_SPACES = re.compile(r"[ \t]+")


def _preprocessor_flags(lines: list[str]) -> list[bool]:
    """Flag each physical line that is a preprocessor directive or a continuation
    of one (the previous directive line ended with a ``\\``). Such lines must stay
    on their own line and keep their spacing, or the directive breaks."""
    flags: list[bool] = []
    in_directive = False
    for line in lines:
        is_pp = in_directive or line.lstrip().startswith("#")
        flags.append(is_pp)
        in_directive = is_pp and line.rstrip().endswith("\\")
    return flags

# Token-class character sets for whitespace tightening.
_WORD_CHARS = frozenset(string.ascii_letters + string.digits + "_")
_OP_CHARS = frozenset("+-*/%=<>!&|^~.:?")

# Two operator chars whose adjacency would form a longer token (or start a
# comment): removing the space between them would change tokenization.
_DANGER2 = frozenset(
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
        # C++ scope (``::``) and pointer-to-member (``.*``): decompilers of C++
        # binaries emit both. Without these, ``case 1: ::f()`` fuses to the invalid
        # ``:::`` (a ternary/label ``:`` glued to a leading-scope ``::``), and
        # ``a . *p`` fuses to the pointer-to-member ``a.*p`` --- both retokenize.
        "::",
        ".*",
        # C alternative-token digraphs: removing the space would fuse them into the
        # punctuator they spell (`<:`=`[`, `:>`=`]`, `<%`=`{`, `%>`=`}`, `%:`=`#`).
        # Decompilers do not emit digraphs, but keeping the space stays lossless.
        "<:",
        ":>",
        "<%",
        "%>",
        "%:",
    }
)


def _word_boundary(a: str, b: str) -> bool:
    return a in _WORD_CHARS and b in _WORD_CHARS


def _dangerous_op_pair(a: str, b: str) -> bool:
    return a in _OP_CHARS and b in _OP_CHARS and a + b in _DANGER2


def _number_dot(left: str, b: str) -> bool:
    """True if joining ``left`` (the text accumulated so far) and the next token
    starting with ``b`` would fuse a numeric literal and ``.`` into one pp-number
    (``5 . x`` -> ``5.x`` retokenizes ``5.`` as a float).

    The left side is numeric when its trailing word-run starts with a digit ---
    this covers decimal (``10``) *and* hex (``0x1f``, which ends in a letter, so a
    last-char ``isdigit`` test would miss it). We scan back only over that trailing
    word-run (cheap), not the whole accumulated line."""
    if b == ".":
        i = len(left)
        while i > 0 and (left[i - 1].isalnum() or left[i - 1] == "_"):
            i -= 1
        return i < len(left) and left[i].isdigit()
    return left.endswith(".") and b.isdigit()


class CollapseInlineSpaces(Transform):
    """Collapse runs of 2+ spaces/tabs to a single space, in code only."""

    id = "ws-collapse"
    tier = Tier.T1_COSMETIC
    description = "Collapse any combination of 2+ spaces/tabs into a single space in code."

    def apply(self, code: str) -> str:
        return map_code(code, lambda s: _INLINE_RUNS.sub(" ", s))


class StripIndentation(Transform):
    """Remove leading whitespace from every line (lossless; braces carry nesting)."""

    id = "ws-indent"
    tier = Tier.T1_COSMETIC
    description = "Remove leading whitespace from each line."

    def apply(self, code: str) -> str:
        edges = protected_line_edges(code)
        return "\n".join(
            line if lead else line.lstrip()
            for line, (lead, _trail) in zip(code.split("\n"), edges)
        )


class StripTrailingWhitespace(Transform):
    """Strip trailing whitespace from every line."""

    id = "ws-trailing"
    tier = Tier.T1_COSMETIC
    description = "Remove trailing whitespace from each line."

    def apply(self, code: str) -> str:
        edges = protected_line_edges(code)
        return "\n".join(
            line if trail else line.rstrip()
            for line, (_lead, trail) in zip(code.split("\n"), edges)
        )


class CollapseBlankLines(Transform):
    """Collapse 2+ consecutive blank lines to one; drop leading/trailing blanks."""

    id = "ws-blanklines"
    tier = Tier.T1_COSMETIC
    description = "Collapse consecutive blank lines to one and drop leading/trailing blanks."

    def apply(self, code: str) -> str:
        remaining_lines: List[str] = []
        for line, (lead, _trail) in zip(code.split("\n"), protected_line_edges(code)):
            if line.strip() or lead:  # real content, or protected string interior
                remaining_lines.append(line)
            elif remaining_lines and remaining_lines[-1] != "":
                remaining_lines.append("")
        if remaining_lines and remaining_lines[-1] == "":
            remaining_lines.pop()
        return "\n".join(remaining_lines)


class TightenCommentSpaces(Transform):
    """Collapse whitespace inside comments and strip leading/trailing space.

    Applies to line comments (``//``) and block comments (``/* */``): every
    run of spaces/tabs (including a lone tab) collapses to one space, and
    leading/trailing horizontal whitespace is stripped entirely.  Newlines
    inside multi-line block comments are left intact.  Code, strings, and
    char literals are untouched.  Strictly lossless: the compiler discards
    comments.
    """

    id = "ws-comments"
    tier = Tier.T1_COSMETIC
    description = "Strip and collapse whitespace inside comments."

    def apply(self, code: str) -> str:
        resulting_code: List[str] = []
        for seg_type, text in scan(code):
            if seg_type == SegmentType.LINE_COMMENT:
                comment_content = _COMMENT_SPACES.sub(" ", text[2:]).strip()
                resulting_code.append("//" + comment_content)
            elif seg_type == SegmentType.BLOCK_COMMENT:
                # An unterminated `/* ...` (run to EOF by the lexer) has no closer
                # to strip or re-append: keep the interior but don't fabricate `*/`.
                has_close = text.endswith("*/")
                inner = text[2:-2] if has_close else text[2:]
                interior = _COMMENT_SPACES.sub(" ", inner).strip(" \t")
                resulting_code.append("/*" + interior + ("*/" if has_close else ""))
            else:
                resulting_code.append(text)
        return "".join(resulting_code)


class TightenWhitespace(Transform):
    """Remove spaces/tabs around punctuation and operators where lossless.

    Walks each line and drops every run of horizontal whitespace between two
    tokens unless removing it would change tokenization. A single space is kept
    only when (a) both sides are word characters --- ``int d`` must not become
    ``intd`` --- or (b) both sides are operator characters whose adjacency would
    form a longer token or a comment --- ``a - -b`` must not become ``a--b``,
    ``a / *p`` must not become ``a/*p``. Every other boundary is tightened:
    operand/operator (``f * 4`` -> ``f*4``, ``e == b`` -> ``e==b``) and anything
    touching ``(){}[];,`` (``while ( true )`` -> ``while(true)``). Preprocessor
    lines are left intact; runs through the scanner so literals are protected.
    Strictly lossless.

    Segment boundaries get one extra guard. An ``__asm { ... }`` block is a
    separate (opaque) segment that begins with ``__asm`` --- a word character ---
    so tightening a CODE segment's trailing whitespace away would glue a preceding
    word token to it (``do __asm{...}`` -> ``do__asm{...}``). That both fuses the
    ``do`` keyword into an identifier and, on any re-scan, stops ``__asm`` from
    being recognised (the lexer needs a non-word char before it), de-protecting
    the block. A single space is therefore restored at a CODE->ASM boundary when
    the tightened code ends in a word character. (String/char segments start with
    a quote --- a non-word char --- so they need no such guard.)
    """

    id = "ws-tighten"
    tier = Tier.T1_COSMETIC
    description = "Remove unnecessary whitespace (includes most of ws-collapse, ws-indent, ws-trailing)."

    def apply(self, code: str) -> str:
        segments = scan(code)
        out: List[str] = []
        for idx, (seg_type, text) in enumerate(segments):
            if seg_type != SegmentType.CODE:
                out.append(text)
                continue
            tight = self._tighten(text)
            nxt = segments[idx + 1] if idx + 1 < len(segments) else None
            if nxt is not None and nxt[0] == SegmentType.ASM and tight and (tight[-1].isalnum() or tight[-1] == "_"):
                tight += " "
            out.append(tight)
        return "".join(out)

    @classmethod
    def _tighten(cls, text: str) -> str:
        lines = text.split("\n")
        pp = _preprocessor_flags(lines)
        # Preprocessor directives (and their continuations) are left verbatim.
        return "\n".join(line if pp[i] else cls._tighten_line(line) for i, line in enumerate(lines))

    @staticmethod
    def _tighten_line(line: str) -> str:
        code_parts: List[str] = re.split(r"[ \t]+", line.strip(" \t"))
        result: str = code_parts[0]
        for next_part in code_parts[1:]:
            a, b = result[-1], next_part[0]
            if _word_boundary(a, b) or _dangerous_op_pair(a, b) or _number_dot(result, b):
                result += " "
            result += next_part
        return result


class CollapseLineBreaks(Transform):
    """Join lines into as few physical lines as possible.

    The newline terminating a ``//`` comment is kept (removing it would swallow
    the following code into the comment), and likewise the newline bounding a
    frozen (unterminated) string literal is kept (removing it would glue the
    malformed string content onto the next line of real code).  Each preprocessor
    directive stays on its own line.  All other line breaks are replaced with a
    single space.  The scanner protects string and char literal interiors.
    """

    id = "ws-newlines"
    tier = Tier.T1_COSMETIC
    description = "Join lines into as few physical lines as possible, replacing all non-significant line breaks with a single space."

    def apply(self, code: str) -> str:
        resulting_code: List[str] = []
        keep_following_newline = False  # prev segment bounds its line: // comment or frozen string

        def append(s: str) -> None:
            # Guard against gluing two word-char tokens across a segment boundary
            # when the bounding newline is dropped, e.g. a keyword joined to an
            # opaque `__asm{...}` block (`do\n__asm{...}` -> `do __asm{...}`, not
            # `do__asm{...}`, which would also defeat the lexer's ASM protection on
            # a re-scan). CODE->CODE joins already space-separate inside `_collapse`.
            if s and resulting_code:
                prev = resulting_code[-1]
                if prev and (prev[-1].isalnum() or prev[-1] == "_") and (s[0].isalnum() or s[0] == "_"):
                    resulting_code.append(" ")
            resulting_code.append(s)

        for seg_type, text in scan(code):
            if seg_type != SegmentType.CODE:
                frozen_string = seg_type == SegmentType.STRING and not string_is_terminated(text)
                # A frozen (malformed/unterminated) string must be isolated on its
                # own physical line: keep the newline BEFORE it as well as after.
                # Otherwise its head joins the preceding code into one long line,
                # and a later re-scan (ws-tighten) meets the stray quote mid-line
                # and backtracks the freeze across that whole joined line,
                # swallowing tens of KB of real code into one opaque literal.
                if frozen_string and resulting_code and not resulting_code[-1].endswith("\n"):
                    resulting_code.append("\n")
                append(text)
                keep_following_newline = seg_type == SegmentType.LINE_COMMENT or frozen_string
                continue
            if keep_following_newline:
                resulting_code.append("\n")
            append(self._collapse(text))
            keep_following_newline = False
        return "".join(resulting_code)

    @staticmethod
    def _collapse(text: str) -> str:
        """Join runs of ordinary lines with single spaces, dropping blank lines;
        each preprocessor directive --- and its ``\\``-continuation lines --- stays
        on its own line."""
        lines = text.split("\n")
        flags = _preprocessor_flags(lines)
        resulting_code: List[str] = []
        for is_pp, group in groupby(zip(lines, flags), key=lambda pair: pair[1]):
            group_lines = [line for line, _ in group]
            if is_pp:
                resulting_code.extend(line.strip() for line in group_lines)
            else:
                joined = " ".join(line.strip() for line in group_lines if line.strip())
                if joined:
                    resulting_code.append(joined)
        return "\n".join(resulting_code)
