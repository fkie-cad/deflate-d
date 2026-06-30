"""DEFLATE-D: token-efficient reformatting of decompiler output.

Quick start::

    from deflated import transform, Tier

    compressed = transform(raw_decompiler_output, Tier.T2_STRUCTURAL)

Tiers are cumulative and ordered by information loss: T1 (cosmetic, lossless),
T2 (structural, lossless), T3 (contextual --- discards machine-generated names /
type verbosity), T4 (reductive --- discards low-confidence analyst signal).
"""

from __future__ import annotations

from .transforms import Pipeline, Tier, build_pipeline, parse_tier, transform

__all__ = ["Tier", "Pipeline", "build_pipeline", "parse_tier", "transform"]
