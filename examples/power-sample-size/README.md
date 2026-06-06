# Examples — power-sample-size engine

Each `*_input.json` is a request; the matching `*_output.json` is the **actual, verified**
response produced by running it through the engine. Outputs are reproducible: the provenance
`run` id is derived from the request payload, so re-running a fixture yields a byte-identical
result.

## Run them yourself

```bash
# from the repository root
cat examples/power-sample-size/two_sample_t_input.json \
  | python scripts/core/power_sample_size.py | python -m json.tool

cat examples/power-sample-size/two_proportions_input.json \
  | python scripts/core/power_sample_size.py | python -m json.tool
```

## What to notice

- **`n_per_group` / `n_total`** — the required sample size (ceil of the analytic solution).
- **`method`** — the exact routine used (e.g. `statsmodels.stats.power.TTestIndPower`), so the
  calculation is reproducible by hand.
- **`assumptions`** — alpha, power, alternative, and the effect input, all echoed back.
- **`finding.source`** — the provenance trace; the number is never "from the model".

| Fixture | Result |
|---|---|
| `two_sample_t` (d=0.40, α=0.05, power=0.80) | 100 / group, 200 total |
| `two_proportions` (p1=0.30, p2=0.50, α=0.05, power=0.80) | 93 / group, 186 total |
| `correlation` (r=0.30, α=0.05, power=0.80) | 85 total (Fisher z) |

Supported designs and their status are listed in [../../STATUS.md](../../STATUS.md).
