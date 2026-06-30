"""Tests for the reformat CLI — argument parser and main entry point."""

from __future__ import annotations

import io
from unittest.mock import patch

import pytest

from deflated.reformat import build_arg_parser, main


# --- build_arg_parser() ---


def test_parser_positional_file() -> None:
    args = build_arg_parser().parse_args(["func.c"])
    assert args.file == "func.c"


def test_parser_stdin_dash() -> None:
    args = build_arg_parser().parse_args(["-"])
    assert args.file == "-"


@pytest.mark.parametrize("tier", ["T1", "T2", "T3", "T4"])
def test_parser_tier_strings(tier: str) -> None:
    args = build_arg_parser().parse_args(["--tier", tier, "f.c"])
    assert args.tier == tier


def test_parser_tier_short_flag() -> None:
    args = build_arg_parser().parse_args(["-t", "T2", "f.c"])
    assert args.tier == "T2" and args.file == "f.c"


@pytest.mark.parametrize("n", ["1", "2", "3", "4"])
def test_parser_tier_numbers(n: str) -> None:
    args = build_arg_parser().parse_args(["--tier", n, "f.c"])
    assert args.tier == n and args.file == "f.c"


def test_parser_exclude_single() -> None:
    args = build_arg_parser().parse_args(["--exclude", "compress-names", "f.c"])
    assert args.exclude == "compress-names" and args.file == "f.c"


def test_parser_exclude_multiple() -> None:
    args = build_arg_parser().parse_args(["--exclude", "compress-names,strip-callconv", "f.c"])
    assert args.exclude == "compress-names,strip-callconv" and args.file == "f.c"


def test_parser_exclude_multiple_2() -> None:
    args = build_arg_parser().parse_args(["--exclude", "compress-names, strip-callconv", "f.c"])
    assert args.exclude == "compress-names, strip-callconv" and args.file == "f.c"


def test_parser_list_flag() -> None:
    args = build_arg_parser().parse_args(["--list"])
    assert args.list is True
    assert args.file is None


def test_parser_unknown_flag() -> None:
    with pytest.raises(SystemExit) as exc:
        build_arg_parser().parse_args(["--unknown"])
    assert exc.value.code == 2


# --- main() ---


def test_main_list(capsys) -> None:
    result = main(["--list"])
    out = capsys.readouterr().out
    assert result == 0
    assert all(t in out for t in ("T1_COSMETIC", "T2_STRUCTURAL", "T3_CONTEXTUAL", "T4_REDUCTIVE"))
    assert "id: compress-names" in out
    assert "id: ws-tighten" in out


def test_main_no_args() -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_main_file(tmp_path, capsys) -> None:
    f = tmp_path / "func.c"
    f.write_text("int   iVar1;\nreturn   iVar1;\n")
    result = main(["--tier", "T1", str(f)])
    out = capsys.readouterr().out
    assert result == 0
    assert len(out) > 0
    assert "int   " not in out


def test_main_stdin(capsys) -> None:
    with patch("sys.stdin", io.StringIO("int   x;\n")):
        result = main(["--tier", "T1", "-"])
    out = capsys.readouterr().out
    assert result == 0
    assert "int   " not in out


def test_main_exclude(tmp_path, capsys) -> None:
    f = tmp_path / "func.c"
    f.write_text("int iVar1;\nreturn iVar1;\n")
    result = main(["--tier", "T3", "--exclude", "compress-names", str(f)])
    out = capsys.readouterr().out
    assert result == 0
    assert "iVar1" in out


def test_main_invalid_tier(tmp_path) -> None:
    # A bad --tier is a usage error: clean parser.error (exit 2), not a traceback.
    f = tmp_path / "func.c"
    f.write_text("int x;\n")
    with pytest.raises(SystemExit) as exc:
        main(["--tier", "T99", str(f)])
    assert exc.value.code == 2


def test_main_missing_file() -> None:
    # An unreadable input path is likewise a clean usage error, not a traceback.
    with pytest.raises(SystemExit) as exc:
        main(["--tier", "T1", "/no/such/file.c"])
    assert exc.value.code == 2


@pytest.mark.parametrize("tier", ["T1", "T2", "T3", "T4"])
def test_main_tier_returns_zero(tmp_path, capsys, tier: str) -> None:
    f = tmp_path / "func.c"
    f.write_text("int iVar1;\nreturn iVar1;\n")
    assert main(["--tier", tier, str(f)]) == 0


def test_main_tiers_monotonically_shrink(tmp_path, capsys) -> None:
    f = tmp_path / "func.c"
    f.write_text("int iVar1;\nreturn iVar1;\n")
    sizes = []
    for tier in ("T1", "T2", "T3", "T4"):
        main(["--tier", tier, str(f)])
        sizes.append(len(capsys.readouterr().out))
    assert all(a >= b for a, b in zip(sizes, sizes[1:]))
