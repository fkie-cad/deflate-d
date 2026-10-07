#!/usr/bin/env python3
"""
Command-line entry point: reformat decompiler output at a chosen reduction tier.

See `--help` for options and the README for usage examples.
"""

from __future__ import annotations

import argparse
import sys

from typing import List

from .transforms import build_pipeline, parse_tier
from .transforms.base import Tier
from .transforms.pipeline import ORDERED_TRANSFORMS


def _read(path: str) -> str:
    """Read `path` (file-path or stdin for "-") as UTF-8 with `surrogateescape`.

    Undecodable bytes become lone surrogates instead of U+FFFD, so `_write` can restore them and non-UTF-8 input
    passes through every tier unchanged.
    """
    if path == "-":
        buf = getattr(sys.stdin, "buffer", None)
        return buf.read().decode("utf-8", "surrogateescape") if buf else sys.stdin.read()
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        return fh.read()


def _write(text: str) -> None:
    """Write `text` to stdout, turning lone surrogates from `_read` back into the original bytes.

    Falls back to a plain text write when stdout has no binary buffer (e.g. a `StringIO`).
    """
    buf = getattr(sys.stdout, "buffer", None)
    if buf is None:
        sys.stdout.write(text)
        return
    sys.stdout.flush()
    buf.write(text.encode("utf-8", "surrogateescape"))
    buf.flush()


def _list_transforms(verbose: bool = False) -> None:
    """
    Print the transform ids grouped by tier, in pipeline order (for `--list`).

    With `verbose` (`--list-verbose`), each id is followed by its description.
    """
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
    """
    Build the argument parser for the `deflate-d` CLI.

    Defines the input `file` (or `-` for stdin), `--tier`, `--exclude`, `--list` and `--list-verbose`.
    Values are returned as given; `main` validates the tier and the excluded ids.
    """
    parser = argparse.ArgumentParser(prog="deflate-d", description="Reformat decompiler output (DEFLATE-D).")
    parser.add_argument("file", nargs="?", help="input file, or '-' for stdin")
    parser.add_argument(
        "--tier",
        "-t",
        default="T3",
        help="target tier: T1/T2/T3/T4 or 1-4 (default: T3, the most aggressive tier that only "
        "discards decompiler bookkeeping; T4 also strips genuine analyst signal such as ABI keywords)",
    )
    parser.add_argument("--exclude", default="", metavar="ID[,ID...]", help="comma-separated transform ids to skip")
    parser.add_argument("--list", action="store_true", help="list transform ids per tier and exit")
    parser.add_argument("--list-verbose", action="store_true", help="like --list, but also show each transform's description")
    return parser


def main(argv: List[str] | None = None) -> int:
    """
    Run the `deflate-d` CLI on `argv` (default: `sys.argv[1:]`).

    Reads the input, applies the pipeline for `--tier` minus `--exclude`, and writes the result to stdout.
    Returns 0 on success. Usage errors (no input, unknown tier or transform id, unreadable file) exit with code 2.
    """
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
    except ValueError as e:  # unknown --tier or --exclude id
        parser.error(str(e))
    except OSError as e:  # unreadable input file
        parser.error(f"cannot read {args.file!r}: {e.strerror or e}")
    _write(pipeline.apply(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
