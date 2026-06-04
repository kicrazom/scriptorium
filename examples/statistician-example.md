# Statistician — worked example (illustrative, synthetic)

> **This is an illustrative, synthetic example.** The dataset, numbers, and transcript below
> were fabricated for documentation only. They are **not** real measurements, not a real
> study, and not advice. The agent's actual output depends on the data you give it and the
> runtime it can verify. Domain is deliberately neutral (environmental sensors). No personal,
> patient, or proprietary data appears here.

This transcript shows the *shape* of a statistician-agent run on a small **paired** dataset:
plan → assumptions → classical result → Bayesian companion → interpretation with caveats →
reproducible script. It is abbreviated; a live run prints fuller tool output.

---

## User request

> I have 12 soil-moisture sensors. Each was read on the same plot **before** and **after** a
> firmware recalibration, same day, same conditions. I want to know whether the recalibration
> shifted the readings, and by how much — with honest uncertainty. Data is at
> `./sensor_recal.csv` (columns: `sensor_id, before, after`, units = % volumetric water
> content). Give me a classical answer and a Bayesian one.

---

## Agent output (abbreviated)

**Config.** No `./.scriptorium/profile.md` or `~/.scriptorium/profile.md` found — proceeding
with universal defaults: `prefer_runtime: python`, `bayesian_backend: pymc`,
`asymmetric_risk: false`, `units_inline: true`. (Said once; not blocking.)

**Runtime probe.** Verified before claiming anything could run:

```
python3 -c "import scipy, numpy, pandas; print(scipy.__version__)"   # → 1.13.1  OK
python3 -c "import pingouin; print(pingouin.__version__)"            # → 0.5.4   OK
python3 -c "import pymc, arviz; print(pymc.__version__)"             # → 5.16.2  OK
```

All present → full classical + Bayesian run (no degrade-to-advisory needed).

### 1. Plan

| Item | Value |
|---|---|
| Question | Did recalibration shift sensor readings, and by how much? |
| Estimand | Mean **within-pair** difference `after − before` (% VWC), in this sensor set |
| Design | **Paired** (same sensor, two conditions) — analyse the 12 differences, not 24 independent values |
| Confirmatory vs exploratory | **Confirmatory** — one prespecified question, one prespecified test |
| Paradigm | **Both.** Classical for the prespecified test; Bayesian companion because n = 12 is small and the user wants a posterior over the shift magnitude |
| Candidate method | Paired *t*-test on the differences (assumes the differences are ~Normal); fallback Wilcoxon signed-rank if that fails |
| Effect size | Cohen's `d_z` (within-pair) with 95% CI |

### 2. Data & assumptions

- **n = 12 pairs**, 0 missing, 0 duplicate `sensor_id`. No prompt-injection-style text in the
  file (column names / cells are data, not instructions). Differences `d = after − before`
  computed.
- **Distribution of the 12 differences.** Inspected Q-Q plot + Shapiro-Wilk **on the
  differences** (the relevant quantity), not on raw readings.

| Assumption check | Result | Verdict |
|---|---|---|
| Normality of differences (Shapiro-Wilk) | `W = 0.961, p = 0.79` | Pass — no evidence against Normality (and Q-Q points near the line) |
| Outliers / leverage in `d` | max \|z\| `= 1.6` | None extreme |
| Independence of pairs | one reading per sensor, distinct plots | Assumed satisfied (design) |

Shapiro passes, so the **paired *t*-test holds**; Wilcoxon kept as a cross-check, not a
switch. `n = 12` is small — flagged below.

### 3. Results — classical

Numbers transcribed verbatim from the run (`pingouin.ttest(after, before, paired=True)`):

```
Paired t-test (after − before), n = 12
  mean difference  = +1.85 % VWC
  95% CI           = [ +0.62 , +3.08 ] % VWC
  t(11)            = 3.31
  p                = 0.0069   (two-sided)
  Cohen's d_z      = 0.96     95% CI [0.26, 1.63]
Wilcoxon signed-rank (cross-check): W = 7.0, p = 0.013   (consistent direction & significance)
```

- **Power context (a-priori framing only).** With n = 12, α = 0.05 two-sided, 80% power, the
  design can reliably detect roughly `d_z ≈ 0.85` or larger; the observed `d_z = 0.96` sits
  near that floor. **Observed/post-hoc power is not computed** — it is a deterministic
  function of the p-value and statistically invalid. (Prospective planning is the
  power-sample-size skill's job.)

### 4. Results — Bayesian companion

Same paired differences, modelled as `d_i ~ Normal(μ, σ)`. **Priors stated explicitly**
(weakly-informative; differences are small % values so a unit-scale prior is generous):

```
μ ~ Normal(0, 5)          # mean shift in % VWC; 0 = "no shift" centred, ±10 plausible
σ ~ HalfNormal(5)         # within-set SD of differences
Prior predictive check: implied differences span ≈ [−12, +12] % — plausible, not absurd. OK.
```

MCMC diagnostics (required before trusting any posterior) — 4 chains, 2000 draws each:

```
R-hat:  μ = 1.000,  σ = 1.001     (target < 1.01)            OK
ESS:    μ bulk 3550 / tail 2900,  σ bulk 3100                OK
Divergences: 0                                               OK
Posterior predictive check: observed mean & spread fall well inside the PPC band.  OK
```

Posterior (note: **credible interval**, not confidence interval):

```
μ  posterior median = +1.83 % VWC,  95% CrI [ +0.55 , +3.10 ]
P(μ > 0)            = 0.996
ROPE [−0.5, +0.5] % VWC: P(μ inside ROPE) = 0.014   → shift is very likely outside "practically zero"
```

[AI-inferred] The classical CI and the Bayesian CrI nearly coincide here because the prior is
weak and n, while small, is informative enough that the likelihood dominates. This is expected,
not a coincidence to over-read.

### 5. Interpretation (with caveats)

- **Direction & magnitude.** Recalibration is associated with a **positive shift of ≈ 1.8–1.9
  % VWC** (classical mean diff `+1.85`, 95% CI `[+0.62, +3.08]`; Bayesian median `+1.83`, 95%
  CrI `[+0.55, +3.10]`). Both paradigms agree: the readings went **up** after recalibration,
  and "no shift" is implausible (`p = 0.0069`; `P(μ > 0) = 0.996`).
- **Statistical vs practical significance.** Whether `+1.85 % VWC` *matters* is a domain call,
  not a statistical one. The CI lower bound (`+0.62`) is small; the upper (`+3.08`) is several
  times larger. The data are compatible with a shift from "barely noticeable" to "clearly
  relevant" — magnitude is **not yet pinned down**. Report the interval, not a verdict.
- **Effect size.** `d_z = 0.96` is large, but its CI `[0.26, 1.63]` is wide — consistent with
  anything from a modest to a very large standardized within-pair shift.

**Caveats / what this cannot tell you.**

- **n = 12 is small** — the wide intervals are the honest cost. This is *evidence of a shift*,
  not a precise estimate of its size.
- **Scope.** 12 sensors of one configuration on one day. It does **not** establish that the
  shift generalizes to other firmware, sensor models, soil types, or temperatures — that is an
  inference beyond the data. [AI-inferred] a directional bias from recalibration is a plausible
  mechanism, but mechanism is not tested here.
- **Causal claim** rests on the paired design holding conditions constant (same plot, same day);
  any uncontrolled drift between the two readings would confound it.
- Confirmatory result stands as prespecified; no multiplicity issue (single hypothesis).

### 6. Reproducibility

Runnable script saved next to the data — reproduces **every** number above:

```
./sensor_recal_analysis.py
  header: runtime python 3.11 · scipy 1.13.1 · pingouin 0.5.4 · pymc 5.16.2 · arviz 0.18.0
          seed = 20260604 · date 2026-06-04
  run:    python3 sensor_recal_analysis.py    # prints the classical block, then the PyMC fit + ArviZ summary
```

---

### Notes on what this example demonstrates

- **Numbers only from runs** — every statistic is transcribed from a tool response; nothing is
  guessed. (`not computed` would appear if a runtime were missing.)
- **Assumptions checked and reported**, each with its result and verdict — not skipped.
- **Effect sizes carry uncertainty** (CI and CrI), and statistical vs practical significance is
  separated.
- **Bayesian discipline:** priors stated, prior predictive check, MCMC diagnostics (R-hat / ESS
  / divergences) and PPC reported *before* the posterior is trusted; "credible interval", never
  "confidence interval".
- **Honest small-n flagging** — wide intervals named as the cost, no over-generalization.
- **Every AI inference marked** `[AI-inferred]` and kept out of the fact-claims.
- **A reproducible script** is the deliverable, not just the prose.
