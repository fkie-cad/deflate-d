#!/usr/bin/env python3
"""Reformat decompiler output at a chosen reduction tier.

Examples::

    # Apply T2 (cosmetic + structural) to a file, print to stdout
    python -m deflated.reformat --tier T2 func.c

    # Most aggressive tier from stdin, but keep placeholder names
    cat func.c | python -m deflated.reformat --tier T4 --exclude compress-names -

    # Show the transforms each tier applies (--list-verbose adds descriptions)
    python -m deflated.reformat --list
    python -m deflated.reformat --list-verbose
"""

from __future__ import annotations

import argparse
import sys

from typing import List

from .transforms import build_pipeline, parse_tier
from .transforms.base import Tier
from .transforms.pipeline import ORDERED_TRANSFORMS


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _list_transforms(verbose: bool = False) -> None:
    print("Transforms by tier (cumulative):")
    print("(use the ID with --exclude)")
    width = max((len(t.id) for t in ORDERED_TRANSFORMS), default=0)
    for tier in list(Tier)[1:]:  # skip T0_RAW
        members = [t for t in ORDERED_TRANSFORMS if t.tier == tier]
        print(f"\n  {tier.name}")
        for t in members:
            if verbose:
                print(f"    {t.id:<{width}}  {t.description}")
            else:
                print(f"    id: {t.id}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reformat", description="Reformat decompiler output (DEFLATE-D).")
    parser.add_argument("file", nargs="?", help="input file, or '-' for stdin")
    parser.add_argument(
        "--tier",
        "-t",
        default="T3",
        help="target tier: T1/T2/T3/T4 or 1-4 (default: T3, the most "
        "aggressive lossless-of-meaning tier; T4 also strips genuine "
        "signal such as ABI keywords)",
    )
    parser.add_argument("--exclude", default="", metavar="ID[,ID...]", help="comma-separated transform ids to skip")
    parser.add_argument("--list", action="store_true", help="list transform ids per tier and exit")
    parser.add_argument("--list-verbose", action="store_true", help="like --list, but also show each transform's description")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list or args.list_verbose:
        _list_transforms(verbose=args.list_verbose)
        return 0
    if not args.file:
        parser.error("provide an input file or '-' for stdin (or use --list)")

    exclude = {x.strip() for x in args.exclude.split(",") if x.strip()}
    try:
        pipeline = build_pipeline(args.tier, exclude=exclude)
        text = _read(args.file)
    except ValueError as e:  # unknown --tier
        parser.error(str(e))
    except OSError as e:  # unreadable input file
        parser.error(f"cannot read {args.file!r}: {e.strerror or e}")
    sys.stdout.write(pipeline.apply(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
