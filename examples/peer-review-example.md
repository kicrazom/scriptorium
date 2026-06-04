# peer-reviewer — worked example (illustrative, synthetic)

> **⚠ Illustrative synthetic example.** Everything below is fabricated for documentation
> purposes — the manuscript, its numbers, the file path, and the report are invented. No real
> manuscript, no real data, no real people. It shows the *shape* of a `peer-reviewer` run,
> abbreviated. Real reports are longer and quote actual section/line anchors from the file
> under review.
>
> The agent runs **offline** (tools: `Read, Grep, Glob` only) and **never transmits any part
> of a manuscript anywhere**. It returns the report text; the parent saves it as
> `<basename>.review.txt` next to the manuscript. The review is never added to any knowledge
> base.

---

## Scenario

A reviewer points the agent at a download folder, then at one manuscript inside it. No
`profile.md` is present, so the agent runs on **universal defaults** (English report, generic
venue-fit, `asymmetric_risk: false`, first-look guidelines `[STROBE, CONSORT, PRISMA,
TRIPOD]`). The fictional manuscript is a short observational cohort in a neutral domain —
urban tree-canopy coverage vs. summer street-level heat exposure.

---

## Turn 1 — triage a directory

**User request:**

> Triage `~/review-queue/` and tell me which file is the manuscript I agreed to referee.

**Agent output (abbreviated):**

```
Triage of ~/review-queue/ (Glob *.pdf, *.md, *.txt → 5 files). Candidates ranked by
manuscript-likeness:

1. SUBM-2491_R1.pdf        — revision tag _R1, IMRaD markers (Abstract/Methods/Results),
                             a DOI in the header. Most manuscript-like. ← likely target.
2. canopy-cohort-draft.md  — has Abstract + Methods, no revision tag; could be an earlier
                             draft of the same work.
3. reviewer-guidelines.pdf — journal reviewer instructions, not a manuscript.
4. cv-2026.pdf             — CV, not a manuscript.
5. travel-invoice.pdf      — invoice, not a manuscript.

I cannot ask mid-run. Pick the file to review (likely #1). Re-invoke me with that path.
```

The agent stops here — it does not guess which file to referee.

---

## Turn 2 — referee the chosen manuscript

**User request:**

> Review `~/review-queue/SUBM-2491_R1.pdf`.

**Agent output (abbreviated referee report):**

---

### 1. Manuscript ID & snapshot

- **File:** `SUBM-2491_R1.pdf` (revision R1, 14 pp.)
- **Detected design:** retrospective observational cohort (Methods §2.1, "we followed
  N = 318 street segments across two summers") → reporting guideline **STROBE** (cohort).
- **Target venue:** none provided (no `reviewer.journals`) → generic venue-fit assessed.
- **Topic:** association between block-level tree-canopy coverage and street-level daytime
  heat exposure in a mid-size city, one fabricated study site.

### 2. Recommendation

**Major revision.** The core association is plausible and the dataset is adequately sized,
but three methodological gaps block acceptance as written: confounding is controlled only by
crude stratification (no adjustment set justified, §2.4), missing exposure-sensor data are
dropped silently rather than handled (§3.1, drop from N = 318 to n = 271 unexplained), and
the abstract states a causal claim the cross-segment design cannot support (§Abstract vs
§4.2). All three are fixable with the data apparently in hand.

### 3. Rubric checklist

| Dimension (A–G) | Status | Evidence (section/page/line) | Comment |
|---|---|---|---|
| A. Design → guideline (STROBE) | ⚠ | §2.1 p.3 | Design correct; STROBE flow diagram absent. |
| A. Participant/segment flow | ✗ | §3.1 p.6 | N 318 → n 271 drop unexplained; no flow figure. |
| B. A-priori power / sample size | ✗ | not-in-source | No sample-size justification anywhere. |
| B. Confounder control | ⚠ | §2.4 p.5 | Stratified by district only; no adjustment set, no rationale. |
| B. Effect size + CI | ✓ | §3.2 p.7, Table 2 | β reported with 95% CI; good — not p-values alone. |
| B. Missing-data handling | ✗ | §3.1 p.6 | Complete-case by default; mechanism not stated. |
| C. IMRaD coherence | ⚠ | §Abstract vs §4.2 | Conclusions overreach the design (causal language). |
| C. Internal consistency | ⚠ | Abstract vs Table 2 | Abstract β 0.34, Table 2 β 0.31 — mismatch to reconcile. |
| D. Venue / scope fit | ✓ | whole | Coherent, well-scoped for an environmental-monitoring venue. |
| E. Explicit Limitations | ✗ | not-in-source | No Limitations section. |
| E. Epistemic status of central claim | ⚠ | §4.2 | Authors claim causal; data support working_hypothesis. |
| F. Reproducibility (data/code) | ✗ | not-in-source | No data- or code-availability statement. |
| F. Ethics / consent | n/a | — | No human subjects; environmental sensors only. |
| G. AI-usage disclosure | ✗ | not-in-source | No AI-usage statement; not required by all venues, note it. |

(`✓` met, `⚠` partial/needs work, `✗` absent or inadequate.)

### 4. Major issues

1. **Confounding under-controlled (§2.4, p.5).** Canopy and heat both track with district
   wealth, road width, and building density; stratifying by district alone leaves these
   uncontrolled. *Why it matters:* the headline β is likely confounded upward. *Fix:* justify
   an a-priori adjustment set (e.g. road width, surface albedo, building density), report
   adjusted estimates, and state the rationale rather than a kitchen-sink model.

2. **Silent missing-data drop (§3.1, p.6).** N = 318 segments become n = 271 with no
   explanation. *Why it matters:* if sensor dropout correlates with heat (e.g. failures in the
   hottest segments), the estimate is biased. *Fix:* state the missingness mechanism, report a
   complete-case vs. sensitivity comparison, and add a STROBE flow diagram.

3. **Causal overreach (§Abstract, §4.2).** The abstract says canopy "reduces" heat exposure;
   a single cross-segment observational cohort supports association, not causation. *Why it
   matters:* over-claim beyond design. *Fix:* reword to associational language; downgrade the
   central claim to `working_hypothesis` (one study, observational) — see §6.

### 5. Minor issues

1. Abstract β 0.34 vs. Table 2 β 0.31 — reconcile (§3.2).
2. No a-priori sample-size justification (§2); add or state as a limitation.
3. Units inconsistent — temperature given as °C in text, K in Figure 3 axis.
4. Figure 2 legend truncated (p.8); reference list uses two citation styles.

### 6. Research-integrity / red flags

- **No prompt-injection text detected** in the readable layers of the PDF. *(The agent treats
  any "instructions to the reviewer/AI" found in a manuscript as hostile data to report, never
  obey — none here.)*
- **Epistemic status of central claim:** `working_hypothesis`, confidence moderate,
  source_independence = 1 (single observational study). Authors present it as established —
  flag the mismatch to the editor.
- **Citations:** two references look topically off (general climate-policy reviews cited for a
  specific sensor-calibration method, refs [11], [14]). Cannot verify online (offline by
  design) → `[needs offline-independent verification]`; not asserting fabrication.

### 7. Confidential note to the editor

Sound, useful dataset on a real-world question; the analysis is not yet rigorous enough to
support the stated conclusion. Generic venue-fit is good for an environmental-monitoring
journal (novelty: moderate — local replication of a known canopy-cooling association). With
the adjustment set, missing-data handling, a STROBE flow diagram, a Limitations section, and
associational rewording, this becomes acceptable. Recommend **major revision**.

> *Confidential offline review — manuscript content was not transmitted. To be saved as a
> local plain-text file next to the manuscript; not added to any knowledge base or index.*

---

## What this example illustrates

- **Triage → stop → human picks.** The agent lists candidates and halts; it never guesses
  which file to referee (it cannot ask mid-run).
- **Design-detection drives the guideline.** Cohort → STROBE, picked from the *detected*
  design, not the default first-look list.
- **Absence is a finding.** `not-in-source` / `✗` for the missing power calculation,
  Limitations section, and data-availability statement — not silently filled.
- **Graduated epistemics.** The central claim is labelled `working_hypothesis` with a
  confidence and source-independence count, against the authors' implied certainty.
- **Confidential & offline.** No network tools; the closing line is mandatory; the parent (not
  the agent) saves the report as `SUBM-2491_R1.review.txt` next to the manuscript.
