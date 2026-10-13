"""
Random decompiler-like C and a lexer independent of `cosmetic.py`, for the `ws-newlines`/`ws-tighten` property tests.
"""

from __future__ import annotations

import random
import re
from typing import List, Pattern, Tuple

from deflated.transforms.lexer import SegmentType, scan, split_directives

# The punctuators longer than one character: C digraphs and the C++ `::`, `.*`, `->*` included.
PUNCTUATORS = (
    "%:%: ... <<= >>= ->* -> .* :: ## %: <: :> <% %> ++ -- << >> <= >= == != && || -= += *= /= %= &= |= ^=".split()
)


def pp_token(punctuators: List[str]) -> Pattern[str]:
    """
    A C preprocessing token in code, independent of `cosmetic.py`: pp-number (`.`? digit, then word chars, `.` and
    exponent signs), identifier, one of `punctuators` (longest match first), or any other single character.
    """
    longest_first = sorted(punctuators, key=len, reverse=True)
    return re.compile(
        r"\.?\d(?:[eEpP][+-]|[\w.])*|[A-Za-z_]\w*|" + "".join(re.escape(p) + "|" for p in longest_first) + r"\S"
    )


PP_TOKEN = pp_token(PUNCTUATORS)

# Pieces of a line. Literals carry the prefixes that 1.15, 1.16 and 1.18 are about.
_WORDS = ["x", "foo", "int", "return", "L", "u", "U", "u8", "xL"]
_NUMBERS = ["1", "0x1E", "0xFE", "0x1P", "1.", "1.e5", ".5", "10ULL"]
_OPERATORS = list("+-*/%=<>&|^!?:;,.(){}[]#~") + ["->", "++", "<<", "==", "##", "::"]
_LITERALS = ['"s"', '"a b"', '""', '"q\\""', 'L"w"', 'u8"x"', "'a'", "' '", "'ABCD'", "L'a'", "'\\''"]
_COMMENTS = ["/* c */", "/**/", "/* a\n b */"]
_ASM = ["__asm { mov eax, 1 }", "__asm {\n  nop\n}"]
# A piece that must end its line: a line comment, a frozen (unterminated) string.
_LINE_ENDERS = ["// c", "// c  ", "//", '"trunc', 'L"trunc']
_DIRECTIVES = [
    "#define A 1",
    '#include "a.h"',
    "#endif /* X */",
    '  # define F(x) \\\n  puts("s"); \\\n  x',
    "#define G foo\\\n  bar",
    "/* c */ #define B 2",
    '#define L "s"',
    "#if A // c",
    "#define D 1 /* x\n y */ + 2",
]


def _random_line(rng: random.Random) -> str:
    """One physical line (or a few, for directives and multi-line comments or `__asm`) of decompiler-like C."""
    if rng.random() < 0.15:
        return rng.choice(_DIRECTIVES)
    kinds = [_WORDS, _NUMBERS, _OPERATORS, _LITERALS, _COMMENTS, _ASM]
    pieces = [rng.choice(rng.choices(kinds, weights=[4, 2, 5, 2, 1, 0.3])[0]) for _ in range(rng.randint(0, 6))]
    if rng.random() < 0.2:
        pieces.append(rng.choice(_LINE_ENDERS))
    return "".join(piece + rng.choice(["", "", " ", "  ", "\t"]) for piece in pieces)


def random_source(rng: random.Random) -> str:
    lines = [rng.choice(["", " ", "\t"]) + _random_line(rng) for _ in range(rng.randint(1, 6))]
    return "".join(line + rng.choice(["\n", "\n", "\n\n", "\r\n"]) for line in lines)[: -rng.randint(0, 1) or None]


def lexed(code: str, token: Pattern[str] = PP_TOKEN) -> List[Tuple[str, str]]:
    """
    The tokens of `code`, blanks ignored: `token` matches in code, every other segment as a whole.

    A directive is compared as its text without the blanks at its ends, the only change `ws-newlines` may make to it.
    """
    tokens: List[Tuple[str, str]] = []
    for seg_type, text in split_directives(scan(code)):
        if seg_type == SegmentType.CODE:
            tokens.extend(("code", m.group(0)) for m in token.finditer(text))
        elif seg_type == SegmentType.DIRECTIVE:
            tokens.append((seg_type, text.lstrip(" \t").rstrip(" \t\r")))
        else:
            tokens.append((seg_type, text))
    return tokens
