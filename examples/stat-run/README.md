# Examples — stat_run engine (permutation_test, multiple_testing)

Each `*_input.json` is a request; the matching `*_output.json` is the **actual, verified**
response produced by running it through the engine. Outputs are reproducible: the provenance
`run` id is derived from the request payload, so re-running a fixture yields a byte-identical
result (the permutation Monte-Carlo seed, when used, is itself derived from that id).

## Run them yourself

```bash
# from the repository root
cat examples/stat-run/permutation_test_input.json \
  | python scripts/core/stat_run.py | python -m json.tool

cat examples/stat-run/multiple_testing_input.json \
  | python scripts/core/stat_run.py | python -m json.tool
```

## What to notice

- **`permutation_test`** — two-sample test for the difference in means (`group[0] − group[1]`).
  For small n the engine enumerates **all** `C(n, n_a)` pooled splits (`exact: true`,
  `seed: null`), giving an exact p-value validated to < 1e-12 against
  `scipy.stats.permutation_test`. When the split count exceeds `exact_max_perms` (default
  10000) it falls back to a **seeded** Monte-Carlo estimate (`exact: false`, finding demoted to
  `corroborated_inference` — it is a stochastic estimate). Optional inputs:
  `alternative` (`two-sided` | `less` | `greater`), `n_resamples`, `exact_max_perms`.
- **`multiple_testing`** — Bonferroni and Benjamini-Hochberg (FDR) adjusted p-values plus which
  hypotheses survive `alpha`. Adjusted p-values reproduce
  `statsmodels.stats.multitest.multipletests` (`bonferroni`, `fdr_bh`) to < 1e-12. The finding
  is scoped to *"adjustment computed"* — the arithmetic is exact, but whether the surviving
  effects are *real* inherits the weakest input p-value, not the engine's word.
- **`finding.source`** — the provenance trace; the number is never "from the model".

| Fixture | Result |
|---|---|
| `permutation_test` (n=6 vs 6, exact, two-sided) | p = 0.00216 (924 splits, exact) |
| `multiple_testing` (12 p-values, α=0.05) | Bonferroni: 1 survives · BH: 2 survive |

Supported ops and their status are listed in [../../STATUS.md](../../STATUS.md).
