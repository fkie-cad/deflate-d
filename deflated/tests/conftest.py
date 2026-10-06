"""Shared fixtures for the transform test suite."""

from __future__ import annotations

from importlib.resources import files

import pytest


@pytest.fixture(scope="session")
def ghidra_sample() -> str:
    """Raw text of the bundled Ghidra sample."""
    sample = files("deflated") / "examples" / "ghidra_sample.c"
    return sample.read_text(encoding="utf-8")