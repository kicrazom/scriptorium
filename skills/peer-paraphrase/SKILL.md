---
name: peer-paraphrase
description: Academic paraphrasing by the PEER framework (Point, Evidence, Explanation, Repeat/Link) — restructure a paragraph at the micro level into clearer, more academic prose without changing meaning, evidence, or argument strength. Use when a draft paragraph, abstract sentence, or borrowed passage needs principled rewriting (not mechanical synonym-swap, not patchwriting). Finds the single main point first, keeps citations attached to their evidence, flags paragraphs that pack more than one idea, and emits an optional P/E/E/R map for transparency.
allowed-tools: [Read]
---

# peer-paraphrase

**Summary.** Rewrite an academic paragraph by reverse-engineering its rhetorical functions
(Point → Evidence → Explanation → Repeat/Link), then rebuilding them in your own words —
shorter, clearer, more academic, but never more complex and never altering meaning. This is
*paraphrase*, not synonym substitution and not patchwriting.

**Why this skill exists.** Mechanical paraphrase (swap words, keep the sentence skeleton)
produces text that is both worse and academically dishonest: it reads awkwardly, it can
inflate or soften claims by accident, and it stays too close to the source. PEER fixes this
by operating on *function* rather than *surface*. You first ask what the author is trying to
do in each sentence, then reconstruct that intent fresh.

**Default working language: English.** A profile may override the output language (see
Configuration). The framework itself is language-independent.

---

## The PEER framework

A well-built academic paragraph performs four functions in order. Paraphrasing means
identifying each, then rewriting it — not transposing it.

### P — Point

Find the **single main point** first. Before touching wording, ask: *what does the author
actually want to say here?* Strip the paragraph to its one claim.

- The point becomes a **strong, clear first sentence**. Lead with it.
- Do **not** synonym-swap the original opener — derive the point, then state it plainly.
- If you cannot name one point in a sentence, the paragraph may carry more than one idea
  (see the one-point rule below).

### E — Evidence

Identify what **supports** the point: data, study results, cited findings, quotations,
figures, statistics.

- **Never distort the evidence or the strength of the argument.** "Some studies suggest"
  must not become "studies show"; "was associated with" must not become "caused". Hedges,
  quantifiers, and modal verbs (may, might, suggests, is associated with, tends to) are
  load-bearing — preserve their force exactly.
- **Restructure language, not meaning.** You may reorder, condense, and recombine the
  evidence; you may not add, drop, or re-weight any of it.
- **Keep every citation attached to its evidence.** A reference travels with the specific
  finding it supports; do not orphan it, merge two studies under one citation, or move a
  citation to a claim it does not source.
- Numbers, sample sizes, effect sizes, p-values, and dates are copied **verbatim** from the
  source. Never round, infer, or "tidy" a statistic during paraphrase.

### E — Explanation

Add or repair the **why-this-evidence-matters** link — the sentence that connects the
evidence back to the point. This is the part weak paraphrase silently omits: it summarizes
*what* was found but never shows *why it bears on the claim*.

- If the source already explains the link, rewrite it cleanly.
- If the source merely juxtaposes point and evidence (a common drafting weakness), you may
  surface the implied connective relation — **without introducing a new claim**. Making an
  existing logical relation explicit is paraphrase; asserting a relation the source never
  implied is fabrication. When in doubt, mark it.

### R — Repeat / Link

Close by **returning to the point** (mini-conclusion) or **bridging to the next paragraph**,
so the paragraph has flow and the argument coheres across the document.

- This is the move that makes the **skip test** pass (below).
- Use the link only to restate or hand off — never to smuggle in a fresh assertion.

---

## Rules (non-negotiable)

1. **Decompose into functions before rewriting.** Map the source onto P / E / E / R first.
   Only then rebuild each function in your own words. Do not start from the source sentence.
2. **One-point rule.** One paragraph = one main idea. If the source packs 2–3 ideas,
   **split** it into separate paragraphs rather than cramming. Flag this explicitly (see
   Output); do not silently merge or silently drop a point.
3. **Shorter, clearer, more academic — but NOT more complex.** Prefer plain, precise
   academic register. Cut filler and redundancy. Do not add nominalizations, jargon, or
   nested clauses to sound "smarter".
4. **Skip test.** Reading **only the first sentences** of consecutive paragraphs should still
   convey the structure of the argument. If your paraphrase fails the skip test, the Point
   sentence is not doing its job — rewrite it.
5. **No new claims. No changed argument strength.** The paraphrase asserts exactly what the
   source asserts, no more, no less, at exactly the same epistemic strength. This is the
   single most important rule. Adding a claim, sharpening a hedge, or weakening a strong
   result are all failures.
6. **Paraphrase, not patchwriting.** Patchwriting (keeping the source's sentence structure
   and replacing a few words) is both poor writing and a plagiarism risk. Rebuild from the
   reconstructed functions, in a genuinely different structure.
7. **Citations stay with their evidence** (restated from E — it governs both rules).

---

## Anti-hallucination discipline

This skill rewrites; it does not invent. The claim/citation discipline:

- **Every fact, number, statistic, and citation in the paraphrase comes only from the source
  text provided.** Copy them verbatim. The model adds nothing.
- **Do not fabricate citations, authors, years, PMIDs, DOIs, or page numbers.** If a
  reference marker is in the source, carry it; if it is absent, leave it absent.
- If the source is ambiguous and a reading would require guessing a fact, mark it
  **`[not-in-source]`** rather than filling the gap. Report missing connective material as a
  finding, not a thing to invent.
- **Mark any AI inference** you make explicit (e.g. surfacing an implied Explanation link)
  with **`[AI-inferred]`**, and keep it separate from the source's own claims so the author
  can accept or reject it.
- When the source's argument strength is itself unclear (vague hedging), preserve the
  ambiguity and flag it — do not resolve it in either direction.

Rationale: a paraphrase that quietly upgrades "associated with" to "causes", or that invents
a plausible-looking citation, is worse than no paraphrase — it launders an unsupported claim
into the author's draft.

---

## Procedure

1. **Read** the source paragraph(s) in full.
2. **Decompose.** Label each clause/sentence as P, E, E, or R. Note citations and their
   evidence anchors. Count the points.
3. **Check the one-point rule.** If >1 main point, plan a split and flag it.
4. **Rebuild** each function in your own words: strong Point first sentence → faithful
   Evidence (verbatim numbers/citations) → Explanation link → Repeat/Link close.
5. **Verify** against the rules: strength unchanged? citations attached? no new claims?
   skip test passes? not patchwriting? numbers verbatim?
6. **Emit** the paraphrased text, plus the optional P/E/E/R map and any flags.

---

## Output format

Return:

1. **Paraphrased text** — the rewritten paragraph(s), ready to drop into the draft.
2. **P/E/E/R map** *(optional, for transparency)* — one line per function showing how the
   source mapped to the rewrite, so the author can audit fidelity. Include this by default
   when the author wants to verify; omit it for a clean drop-in if they ask for prose only.
3. **Flags** — explicit, only when triggered:
   - `⚠️ >1 point` — the source paragraph carries more than one main idea; a split is
     proposed (show the proposed split).
   - `⚠️ strength` — a place where the source's hedging/strength was hard to preserve;
     surfaced for the author to confirm.
   - `[AI-inferred]` — an Explanation link made explicit that the source only implied.
   - `[not-in-source]` — material a faithful paraphrase cannot supply.

Example map shape:

```
P  → "Research increasingly links adolescent social-media use with anxiety,"
E  → "...yet the pathways explaining this relationship..." (carries source's "remain unclear")
E  → (link: why-it-matters — mechanism is the open question, preserved from source)
R  → "...are still not well understood."  [single paragraph; no split needed]
```

---

## Worked mini-example

**Original:**
> Many studies have investigated the relationship between social media use and anxiety among
> adolescents, but the mechanisms underlying this association remain unclear.

**PEER decomposition:**
- **P** — the open problem: the *mechanism* linking adolescent social-media use to anxiety is
  not understood (the contrast "but … remain unclear" carries the real point).
- **E** — the body of existing studies on the use–anxiety association ("Many studies have
  investigated…").
- **E** — implicit: those studies establish the association but not the *why*.
- **R** — the closing turn that names the gap ("remain unclear").

**PEER paraphrase:**
> Research increasingly links adolescent social media use with anxiety, yet the pathways
> explaining this relationship are still not well understood.

**Why it is correct:**
- **Point preserved** — the gap is the mechanism, and the rewrite leads to it.
- **No new claims** — nothing asserted that the source did not assert.
- **Strength unchanged** — "association remain unclear" → "pathways … not well understood";
  the same hedged, non-causal force. ("links … with", not "causes".)
- **Not patchwriting** — different structure, genuinely reworded, not a word-for-word swap.
- **One point** — single idea, no split needed, passes the skip test on its own.

---

## Boundaries

Per the toolkit's component map:

- **vs `manuscript-imrad` (S5).** peer-paraphrase is the **micro level** — one paragraph at a
  time, rhetorical-function rewriting. `manuscript-imrad` is the **document level** — section
  presence/order, IMRaD coherence, claims-vs-data alignment, spin-flagging across the whole
  draft. Use this skill to fix a paragraph; use `manuscript-imrad` to check the architecture.
- **vs whole-manuscript writing.** Generating or drafting a full manuscript is **out of
  scope** here and elsewhere in this toolkit; that craft belongs to a dedicated scientific-
  writing project (cross-linked from the repo README as complementary). peer-paraphrase only
  *rewrites existing text*.
- **vs `epistemic-status` (S3).** This skill **preserves** the source's argument strength
  verbatim; it does not *grade* evidence. If the author wants to assign a graduated epistemic
  label (speculative → … → canonical) to a claim, that is `epistemic-status`, run separately.
- This skill is **read-only** (`allowed-tools: [Read]`): it reads source text and returns
  rewritten prose in the conversation. It does not write files; the author places the result.

---

## Configuration

This skill works out-of-the-box with universal defaults (English output, transparency map on
request). It optionally personalizes by reading a profile, resolving the **first** that
exists:

1. `./.scriptorium/profile.md` (project-local)
2. `~/.scriptorium/profile.md` (user-global)
3. none → universal defaults.

Fields consulted, if present:

- **`style.units_inline`** — keep parameter + unit on one line during rewriting
  (e.g. `FEV1 2.4 L (72%)`), never breaking a value across a line.
- **`style.explain_jargon`** — when `true`, briefly gloss a technical term on first use;
  when `false` (default), write specialist-to-specialist without basic explanations.
- **`reviewer.language`** *(soft default for output language)* — if the author keeps their
  working language here, paraphrase in it; otherwise default to **English**.

The skill does not depend on `${CLAUDE_PLUGIN_ROOT}`; it locates the profile by reading the
conventional paths above.
