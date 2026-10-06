"""
DEFLATE-D: token-efficient reformatting of decompiler output.

Public API:

- `transform`: apply the pipeline for a tier to a string in one call.
- `build_pipeline`: build a reusable `Pipeline` for a tier.
- `Pipeline`: an ordered sequence of transforms.
- `Tier`: the reduction tiers and what each one discards.
- `parse_tier`: convert `"T3"`, `3` or `Tier` to a `Tier`.

The command-line interface is `python -m deflated.reformat`; see the README for examples.
"""

from __future__ import annotations

from .transforms import Pipeline, Tier, build_pipeline, parse_tier, transform

__all__ = ["Tier", "Pipeline", "build_pipeline", "parse_tier", "transform"]
