# DEFLATE-D

This repository contains the prototype implementation of DEFLATE-D, the
deterministic decompiler-output reformatter introduced in our SURE '26 paper
*"Stop Paying for Whitespace: Token-Efficient Decompiler Output for LLM-Assisted
Binary Analysis"* (see [How to
reference](#how-to-reference-this-approach-or-prototype-implementation)).

Token-efficient reformatting of decompiler output. DEFLATE-D rewrites C
pseudocode from **Ghidra, IDA/Hex-Rays, and Binary Ninja** into a much
cheaper-to-tokenize form before you feed it to an LLM.

## Tiers

Transforms are grouped into cumulative **tiers**, ordered by how much
information each step can lose:

| Tier | Name | What you lose |
|------|------|---------------|
| **T1** | Cosmetic | nothing but formatting/whitespace |
| **T2** | Structural | semantics-preserving rewrites (casts, braces, …); only the comment pass drops auto-generated address/storage metadata |
| **T3** | Contextual | machine-generated identifiers and type verbosity (decompiler bookkeeping) |
| **T4** | Reductive | low-confidence analyst signal (ABI keywords, decompiler `WARNING` banners, …) |

Tiers are cumulative (T4 ⊇ T3 ⊇ T2 ⊇ T1). **T3 is the recommended default**; T4 is
opt-in for the most aggressive cost reduction. Typical savings on the bundled
`examples/ghidra_sample.c` (GPT tokenizer): T1 ≈ 20%, T2 ≈ 30%, T3 ≈ 54%,
T4 ≈ 60%. On the larger `examples/vtables_*.c` samples, T3/T4 save ≈ 55%/57%
(Ghidra), ≈ 55%/60% (Hex-Rays), and ≈ 43%/47% (Binary Ninja); absolute
magnitudes shift across tokenizers but the tier ranking is stable.

## Install

```bash
pip install -e .            # editable install; adds the `deflate-d` command
# or just run from the source tree with `python -m deflated.reformat`
```

## CLI

```bash
python -m deflated.reformat --tier T3 func.c            # file -> stdout
cat func.c | python -m deflated.reformat --tier T4 -    # stdin
python -m deflated.reformat --tier T3 --exclude compress-names func.c
python -m deflated.reformat --list                      # list transforms per tier
python -m deflated.reformat --list-verbose               # ... with descriptions
```

## Library

```python
from deflated import transform, Tier

compressed = transform(raw_decompiler_output, Tier.T3_CONTEXTUAL)
# also accepts string/int aliases:
compressed = transform(raw_decompiler_output, "T3")
compressed = transform(raw_decompiler_output, 3)
```

For finer control, build a pipeline directly:

```python
from deflated.transforms import build_pipeline

pipe = build_pipeline("T3", exclude={"compress-names"})
out  = pipe.apply(code)
print(pipe.ids())          # the transforms that ran
```

## Tests

```bash
pip install -e ".[test]"
pytest deflated/tests/
```

See [`deflated/README.md`](deflated/README.md) for the full per-transform
reference and scope notes.

## How to reference this approach or prototype implementation

DEFLATE-D is described in the following paper, to appear at the 2nd Workshop on
Software Understanding and Reverse Engineering (SURE '26), co-located with ACM
CCS 2026. If you use it in academic work, please cite:

```bibtex
@inproceedings{enders2026deflated,
  title     = {Stop Paying for Whitespace: Token-Efficient Decompiler Output
               for LLM-Assisted Binary Analysis},
  author    = {Enders, Steffen and Behner, Eva-Maria C. and Padilla, Elmar},
  booktitle = {Proceedings of the 2nd Workshop on Software Understanding and
               Reverse Engineering (SURE), co-located with ACM CCS},
  year      = {2026},
}
```

## Development

This project was developed with the assistance of Anthropic's Claude, under the
authors' direction and review. All design decisions and correctness criteria are
the authors' own, and every transform is covered by the test suite.

## License

Released under the MIT License. See [`LICENSE`](LICENSE).
