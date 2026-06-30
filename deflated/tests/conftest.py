"""Shared fixtures for the transform test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

import deflated


@pytest.fixture
def ghidra_sample() -> str:
    """Raw text of the bundled Ghidra sample, located via the package root so
    callers don't hard-code a `parents[N]` depth that breaks under subfolders."""
    root = Path(deflated.__file__).resolve().parent
    return (root / "examples" / "ghidra_sample.c").read_text()
