---
name: power-sample-size
description: A-priori statistical power and sample-size determination. Given a design family (parallel two-group, paired, one-sample, proportions, correlation, linear/logistic regression, survival, one-/two-way ANOVA, repeated measures), an effect size (or means+SD, or rates), alpha, target power, allocation ratio, and dropout, compute required N (or power|MDE given N), a sensitivity table over plausible effect sizes, and a ready Methods-section sentence. Runs Python (statsmodels.stats.power / pingouin) or R; degrades to explicit formulas. Flags post-hoc/observed power as invalid and separates statistical from clinical significance.
allowed-tools: [Read, Bash, Write]
---

# power-sample-size

A-priori statistical **power** and **sample-size** determination. Turn a study design plus a few assumptions (effect size, alpha, target power, allocation, dropout) into a defensible required N, a sensitivity table, and a paste-ready Methods sentence — every number coming from a tool computation, never from the model.

**Stage:** ANALYZE. **Tools:** Read, Bash, Write.

This skill does the **planning math** only. It is deliberately narrow: design → N (or the inverse). It does not run your final analysis, and it does not critique anyone else's statistics (see Boundaries).

---

## Configuration

This skill reads an optional profile, in this resolution order, and uses the first that exists:

1. `./.scriptorium/profile.md` (project-local)
2. `~/.scriptorium/profile.md` (user-global)
3. none → universal defaults below.

Do not rely on `${CLAUDE_PLUGIN_ROOT}` to locate the profile; resolve the two literal paths above with the Read tool.

Fields this skill consults (all optional):

- `statistics.prefer_runtime` — `python` (default) | `r` | `none`. Selects the calculation engine; `none` forces the explicit-formula degradation path.
- `style.units_inline` — when `true` (default), keep each parameter+unit on one line (e.g. `Δ 0.40 SD, SD 1.0 → d 0.40`); never wrap a value away from its unit.
- `epistemic.asymmetric_risk` — when `true`, treat the design as high-stakes/clinical: prefer the more conservative cell when assumptions are uncertain, widen the sensitivity grid downward (smaller, harder-to-detect effects), and state assumption fragility prominently.

**Universal defaults (no profile):** Python runtime, two-sided alpha 0.05, target power 0.80, allocation ratio 1:1, dropout 0%, effect size required from the user (never assumed). The skill works out-of-the-box for any user; a profile only personalizes runtime and tone.

---

## Inputs

Collect these before computing. If the user gives only some, ask for the rest or state explicitly which default you applied.

| Input | Meaning | Default |
|---|---|---|
| **Design family** | parallel two-group, paired, one-sample, proportions (two-group / one-sample), correlation, linear regression, logistic regression, survival (log-rank / Cox), one-way ANOVA, two-way / factorial ANOVA, repeated-measures ANOVA | required |
| **Effect size** | standardized (d, f, f², r, w/h, HR) **or** raw means + SD **or** event rates p1, p2 **or** slope + residual SD | required (never invented) |
| **Alpha** | two-sided / one-sided significance level | 0.05, two-sided |
| **Target power** | 1 − beta | 0.80 |
| **Allocation ratio** | k = n2/n1 | 1 (equal) |
| **Dropout / non-evaluability** | expected attrition fraction | 0% |
| **Solve for** | N \| power \| MDE (minimum detectable effect) | N |
| **Design extras** | survival: accrual, follow-up, baseline hazard/median, censoring; ANOVA: #groups, #levels, correction (G-G/H-F); regression: #predictors, covariate R², for logistic the event probability and odds ratio | as applicable |

**Effect-size sourcing (anti-hallucination, hard rule).** An effect size must come from one of: (a) the user's stated assumption, (b) a pilot/observed value the user provides, or (c) a literature value the user cites — quoted with its source. The skill never supplies a "typical" or "conventional" effect size as if it were a fact. Cohen's small/medium/large anchors may be **offered as labelled conventions** (clearly marked as conventions, not data), but the chosen value is the user's decision and must be recorded as an assumption.

---

## Outputs

Always produce all four:

1. **Headline result** — required N per arm and total (or power given N, or MDE given N), with every input echoed back.
2. **Sensitivity table** — vary the effect size (and, where relevant, power and allocation) across a plausible range; show how N responds. This is the most important output: a single point estimate hides the fragility of the plan.
3. **Methods-section sentence** — paste-ready, following the protocol pattern (see below).
4. **Caveats block** — assumptions made, what would change the answer, statistical-vs-clinical note, and any data the user still owes.

### Methods-section sentence (the pattern)

Fill this template from the computed numbers only:

> "Assuming Δ X, SD Y (standardized effect d = …), a two-sided α of 0.05 and 80% power, N = … evaluable participants (… per arm at a 1:1 allocation) are required; allowing for Z% dropout, N = … participants are planned."

Adapt the slots to the design (rates p1/p2 and a relative risk for proportions; hazard ratio and number of events for survival; effect size f and group count for ANOVA; the partial R² increment for regression). Keep units on one line. State the software and procedure used (e.g. "computed with statsmodels.stats.power TTestIndPower"), so the calculation is reproducible. Never write a sentence whose numbers you did not compute.

---

## Procedure

1. **Identify the design family** from the user's description. If ambiguous, name the two most likely families and ask one disambiguating question (e.g. "are the two measurements on the same subjects?" → paired vs independent).
2. **Resolve runtime** from `statistics.prefer_runtime`, then probe availability (see Runtime). Decide engine: Python, R, or formula-only.
3. **Normalize the effect size** to the metric the chosen routine expects (means+SD → d; p1,p2 → Cohen's h or risk-based; slope+SDs → f²; HR → events). Record the conversion explicitly.
4. **Compute the headline result** with the tool. Echo the routine name and its raw return.
5. **Build the sensitivity table** by re-running the routine across an effect-size grid (and power/allocation where useful). Centre the grid on the user's value; in `asymmetric_risk` mode, extend it toward smaller effects.
6. **Apply dropout** by inflation: `N_planned = ceil(N_evaluable / (1 − dropout))`. State that dropout inflation assumes attrition is non-informative; if it is differential or outcome-related, the inflation under-protects and a sensitivity analysis on the missingness mechanism is warranted.
7. **Write the Methods sentence** and the caveats block.
8. **Optionally save** a reproducible script (see Write policy).

---

## Runtime

**Preferred — Python** (`statsmodels.stats.power`, `pingouin`, `scipy.stats`):

| Design | Routine |
|---|---|
| two-group means | `statsmodels.stats.power.TTestIndPower().solve_power(effect_size=d, alpha, power, ratio, alternative)` |
| paired / one-sample means | `TTestPower().solve_power(...)` |
| two proportions | `statsmodels.stats.proportion.NormalIndPower().solve_power(effect_size=h, ...)` with `h = proportion_effectsize(p1, p2)`; or `samplesize_proportions_2indep_onecase` |
| one-way ANOVA | `FTestAnovaPower().solve_power(effect_size=f, k_groups, ...)` |
| general F-test / regression | `FTestPower().solve_power(effect_size=f2, df_num, df_denom, ...)` |
| correlation | Fisher z transform: `n = ((z_{1−α/2}+z_{1−β}) / atanh(r))² + 3` |
| survival (log-rank) | events via Schoenfeld: `d = (z_{1−α/2}+z_{1−β})² / (p1·p2·(ln HR)²)`; map events→N via accrual/follow-up/baseline hazard |
| repeated measures / mixed | `pingouin.power_rm_anova` / `statsmodels` F-test with corrected df (Greenhouse-Geisser ε) |

**Alternative — R** (`pwr`, `WebPower`, `powerSurvEpi`, `Hmisc::cpower`) when `prefer_runtime: r` or Python is unavailable. Map to the same families.

**Probe before computing** (do not assume a package is installed):

```bash
python3 - <<'PY'
import importlib, sys
mods = ["statsmodels", "scipy", "pingouin", "numpy"]
have = {m: importlib.util.find_spec(m) is not None for m in mods}
print(have)
sys.exit(0 if have["statsmodels"] or have["scipy"] else 1)
PY
```

**Degradation — formulas only** (`prefer_runtime: none`, or no runtime available). Do not silently skip the calculation: state that no engine was found, then compute by hand from the closed forms and show the arithmetic so the user can verify. Core forms:

- **Two-group means (equal n, two-sided):** `n_per_group = 2·((z_{1−α/2}+z_{1−β}) / d)²`, with `d = (μ1−μ2)/SD`.
- **One-sample / paired means:** `n = ((z_{1−α/2}+z_{1−β}) / d)²`, paired d on the difference scores (uses SD of differences, not raw SD).
- **Two proportions (equal n):** `n_per_group = (z_{1−α/2}·√(2·p̄·(1−p̄)) + z_{1−β}·√(p1(1−p1)+p2(1−p2)))² / (p1−p2)²`, `p̄=(p1+p2)/2`.
- **Correlation:** `n = ((z_{1−α/2}+z_{1−β}) / atanh(r))² + 3`.
- **Survival (events):** `d_events = (z_{1−α/2}+z_{1−β})² / (p1·p2·(ln HR)²)`, p1/p2 = allocation fractions.
- **Unequal allocation (k = n2/n1):** multiply the equal-n total by `(1+k)²/(4k)` (efficiency loss vs balanced).

Standard normal quantiles to use verbatim: `z_{0.975}=1.95996`, `z_{0.95}=1.64485`, `z_{0.80}=0.84162` (power 0.80), `z_{0.90}=1.28155` (power 0.90). The normal-approximation forms ignore the t-distribution df penalty and modestly **underestimate** small samples; flag this and add +1–2 per group for n<30 `[rule of thumb]`, or — preferred — recompute with a t-based routine when one is available.

---

## Worked example (illustrative — synthetic)

Two-group parallel trial, continuous primary outcome. User states: expected difference Δ 4.0 units, common SD 10 units (→ d 0.40), two-sided α 0.05, power 0.80, 1:1 allocation, anticipated dropout 15%.

```bash
python3 - <<'PY'
from statsmodels.stats.power import TTestIndPower
import math
d, alpha, power = 0.40, 0.05, 0.80
n1 = TTestIndPower().solve_power(effect_size=d, alpha=alpha, power=power,
                                 ratio=1.0, alternative="two-sided")
n1 = math.ceil(n1)
total_eval = 2 * n1
dropout = 0.15
total_plan = math.ceil(total_eval / (1 - dropout))
print(f"per_arm={n1} total_eval={total_eval} total_planned={total_plan}")
# sensitivity over d
for dd in (0.30, 0.35, 0.40, 0.45, 0.50):
    n = math.ceil(TTestIndPower().solve_power(effect_size=dd, alpha=alpha,
        power=power, ratio=1.0, alternative="two-sided"))
    print(f"d={dd:.2f} per_arm={n} total={2*n}")
PY
```

Report (numbers shown here are the kind of values the routine returns — present whatever the tool actually outputs, never a remembered figure):

- **Headline:** ~100 evaluable per arm, ~200 total; planned ~236 after 15% dropout inflation.
- **Sensitivity:** detectable effect halves → N roughly quadruples; the plan is fragile to the SD assumption, which is the single most consequential input.
- **Methods sentence:** "Assuming a between-group difference Δ 4.0 units, common SD 10 units (standardized d 0.40), two-sided α 0.05 and 80% power, 200 evaluable participants (100 per arm, 1:1 allocation) are required (statsmodels TTestIndPower); allowing for 15% dropout, 236 participants are planned."
- **Caveats:** SD is the dominant assumption; if the true SD is 12, recompute (N grows ~44%). Δ 4.0 units is the user's assumed effect, not an observed value.

---

## Anti-hallucination discipline

This component produces statistics, so the rule is strict:

- **Every number comes from a tool computation or a user-supplied input.** Never report an N, a z-quantile, or a power figure from memory. If the engine ran, quote its return; if you used a formula, show the arithmetic.
- **No invented effect sizes.** If the user has not supplied one, say so and stop — do not assume a "medium" effect to produce a tidy answer. Conventions (Cohen anchors) may be offered, clearly labelled as conventions, for the user to choose from.
- **Mark AI inference explicitly.** Any value you derive by reasoning rather than computation (e.g. a conversion you did by hand) is labelled as such, separate from tool returns.
- **Absent inputs are reported, not filled.** Use "not supplied" / "absent" and list what the user still owes; do not guess a SD, a baseline rate, or a hazard.
- **Reproducibility.** Always name the routine and the package version, so the calculation can be re-run independently.

---

## Two hard statistical rules

**1. Post-hoc / "observed" power is invalid — flag it, never compute it as if meaningful.** Power computed *after* the study using the *observed* effect size is a deterministic monotone function of the p-value: it adds no information beyond the confidence interval and is widely discredited (Hoenig & Heisey 2001). If asked for it, refuse the framing and redirect: report the **observed effect size with its confidence interval** instead — a wide CI that includes both null and clinically important effects is the honest statement of "inconclusive / underpowered", not a recomputed power number. The only legitimate retrospective question is *a-priori* power under a *prespecified, externally justified* effect size (a design audit), which is a different object and must be labelled as such.

**2. Statistical significance is not clinical significance.** Sample size is the lever that converts any non-zero effect, however trivial, into a "significant" p-value at large enough N. Always separate the two: power the study for a **minimal clinically important difference (MCID)** the user can justify, not for the smallest effect that is merely detectable. Report the effect size with uncertainty, and state the MCID assumption explicitly. A result can be statistically significant yet clinically negligible (over-powered), or clinically meaningful yet non-significant (under-powered) — the Methods sentence and caveats must make the targeted MCID visible so a reader can judge relevance, not just p < 0.05.

---

## Write policy

By default, return the result inline (headline, sensitivity table, Methods sentence, caveats). **Offer** to save a reproducible calculation script (the exact Python/R used, with inputs and outputs as comments) next to the user's work — write it only when the user agrees, using the Write tool. Never overwrite an existing file without confirmation. The saved script is the provenance: re-running it must reproduce the reported N.

---

## Boundaries

- **vs `statistician` (agent, ANALYZE).** This skill is the narrow a-priori procedure: design → N. The statistician is the broad analyst (data → result) and may invoke this skill's logic when planning. Once you have data and need the actual test, effect estimate, or model, that is the statistician, not this skill. The statistician also owns **optional-stopping / multiplicity control for repeated non-clinical evaluations** (e.g. early-stopping a model-benchmark sweep without inflating type-I error) — that is an ML-evaluation concern, distinct from this skill's fixed-N planning and from clinical interim analysis.
- **vs `interim-analysis-reviewer` (skill, REVIEW/ANALYZE).** That skill is the clinical interim-analysis specialist (DSMB/DMC, alpha-spending, group-sequential boundaries, ICH-E9 governance) and reviews whether sequential designs are prespecified and valid. This skill computes a **fixed-design** a-priori N. Sequential / adaptive sample-size re-estimation under interim looks is its territory, not this one's; cross-refer when the design includes planned interim analyses.
- **vs `reporting-guideline-check` and `peer-reviewer`.** Those critique *others'* statistics and reporting (e.g. whether a manuscript prespecified its power). This skill *produces* the a-priori calculation for *your own* protocol.

If a request drifts outside design→N (running the final analysis, reviewing someone else's interim plan, sweeping benchmark stopping rules), name the right component and hand off rather than improvising.
