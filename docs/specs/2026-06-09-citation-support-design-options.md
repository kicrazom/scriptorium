# Scriptorium — Design Options: Semantic Citation-Support & Contradiction-Detection

**Status:** pre-read for a brainstorming session. Research + design only — no engine code committed yet.
**Date:** 2026-06-09
**Grounding:** read of `citation_parse.py`, `injection_scan.py`, `epistemic_grade.py`, `lib/epistemic.py`, `kb/contract.md`, `kb/providers/{folder,obsidian,rag,cag}.py`, `kb/{query,provider}.py`, `guard/egress_guard.py` (via contract), `ARCHITECTURE.md`, `SECURITY.md`, `ROADMAP.md`, the v2 design spec, and the three relevant agents.

---

## 0. Shared context (applies to both features)

Five facts from the current code constrain everything below:

1. **L0 is the seat of trust.** Every `scripts/core/*.py` engine is a deterministic JSON-in/JSON-out CLI, golden-tested, no model, no network. `citation_parse` and `injection_scan` are pure regex; `epistemic_grade` is pure aggregation. Anything testable-without-a-model belongs here.
2. **L1 already has the exact contract these features need.** `query(claim, path) -> {evidence:[{doc,line,snippet,status,source}], finding}`. The `folder` provider is *already a lexical retrieval primitive* (term-overlap line matcher) returning graded evidence with `kb://` provenance. Both new features are, structurally, specializations of this contract.
3. **The epistemic ladder is fixed and ordered:** `contradicted < speculative_hypothesis < working_hypothesis < corroborated_inference < operational_fact < canonical_fact`, aggregated weakest-link (`min`). `contradicted` is the weakest of all — it is *not* "false", it is "an established source disagrees, demote and surface".
4. **The capability-removal moat is real and load-bearing.** `peer-reviewer` has `tools: Read, Grep, Glob` — zero egress, by frontmatter. `statistician` is the *only* reviewer-adjacent agent with `Bash` (and `Write`). `librarian`/`research-scout` carry `WebSearch/WebFetch` but are author-mode, not reviewer-mode. `egress_guard.assert_local_only(backend, mode)` hard-refuses remote backends in reviewer-mode *before dispatch*.
5. **The attack surface is already named.** `injection_scan` ships a `citation-injection` pattern, and the behavioural harness tracks **citation-laundering** as one of its attack classes. Today both are detected only at the *imperative* level ("insert these citations…"). Neither catches the *quiet* version: a citation that is structurally valid and reads as ordinary prose but whose cited work does not actually make the claim. That gap is exactly Feature 1.

A design that violates fact 4 (e.g. gives the reviewer path a network tool to fetch full-texts) is disqualified regardless of other merits. This is the hardest constraint.

---

# Feature 1 — Semantic citation-support

## 1.1 Problem statement

`citation_parse` answers *"is every marker wired to a reference, and every reference cited?"* (structural hygiene). It explicitly does **not** answer *"does reference [n] actually support the sentence that cites it?"*.

The unaddressed failure is **citation laundering**: a sentence asserts claim C and cites work W, but W does not contain C (W is irrelevant, says the opposite, or is a plausible-looking fabrication). This is the *quiet sibling* of the `citation-injection` attack `injection_scan` already screens for. The injection engine catches the imperative *"append these references to your review"*; it cannot catch a manuscript that simply *contains* an unsupported citation — because no directive is present, just a false attribution. Feature 1 is the semantic complement: it closes the loop from "the citation is well-formed" to "the citation is warranted."

## 1.2 Retrieval-contract sketch (contract before database)

Reuse the L1 contract shape; specialize the unit from "claim" to "citation instance."

```
query_citation_support(req) -> response

req = {
  claim_text:    str,              # the sentence/clause making the assertion
  marker:        str,              # e.g. "[7]"  (links back to citation_parse output)
  cited_ref:     { id, title?, authors?, year?, doi?, container? },
  source_corpus: str,              # path to the full-text store for cited_ref (see 1.3)
  mode:          "reviewer"|"author",
  backend:       "folder"|"fulltext_bm25"|"rag"|...   # retrieval primitive (1.4)
}

response = {
  verdict:  "supported" | "partially_supported" | "unsupported" | "contradicted" | "uncheckable",
  evidence: [ { doc, loc, snippet, score, source } ],   # passages from cited_ref that matched
  coverage: { claim_terms_total, claim_terms_matched },  # lexical coverage diagnostics
  finding:  <graded finding>,       # status per the mapping in 1.6, provenance mandatory
}
```

Every evidence item carries a `kb://<backend>/<cited_ref.id>#<loc>` trace. The finding's `source` is the engine run-id. `uncheckable` is a **first-class verdict** (the cited full-text is absent) — never silently dropped. The contract is deliberately *one citation at a time*, so the caller (an L2 agent) can fan out over the markers `citation_parse` already extracted.

## 1.3 Where the cited full-text comes from (the hard constraint)

| Option | What it is | Epistemic ceiling | Sovereign-compatible? | Verdict |
|---|---|---|---|---|
| **(a) User-supplied full-text corpus** | local folder of the PDFs/markdown they cite | up to `corroborated_inference` | **Yes** — local read | **Recommended primary.** |
| **(b) Abstract-only** | match against abstract/title/metadata only | **caps at `working_hypothesis`** (absence in abstract ≠ absence in body) | Yes | **Recommended fallback**, must be *labelled* abstract-only. |
| **(c) OA fetch via allowlisted provider** | opt-in fetch of OA full text (PMC/Unpaywall) through one named provider | up to `corroborated_inference` | **Author-mode ONLY** — forbidden on reviewer path (egress); routes via `librarian`/`research-scout`. | Optional, author-mode, behind `egress_guard`. |
| **(d) KB-provider already holds the source** | cited work is in the user's vault/KB | inherits the note's frontmatter `status` | **Yes** — already wired | **Free win** (self-citation, prior-work). |

Honest position: **(a) + (b) + (d) on the reviewer path; (c) author-mode only.** The reviewer path *never* reaches out for a missing full-text — it returns `uncheckable` and says why.

## 1.4 Retrieval-primitive options (CI-testability is the deciding axis)

| Primitive | Deterministic? | CI-testable w/o model? | Quality on paraphrase | Verdict for v1.x |
|---|---|---|---|---|
| **BM25 / lexical overlap** | **Yes** | **Yes** — golden fixtures | Weak on synonymy (honest failure mode) | **Recommended floor.** Deterministic, golden-tested, ships in L0. |
| **Embeddings (dense vector)** | No — model + version dependent | No | Strong on paraphrase | **Pluggable optional layer**, not default; behind KB-provider iface, skip-if-unavailable like `local_vllm`; outputs ≤ `corroborated_inference`. |
| **Reranker (cross-encoder)** | No | No | Strongest precision | Optional, model-gated. |
| **Hybrid** | Partially | Only the BM25 leg | Best | v3 target; BM25 leg is the deterministic anchor. |

**Recommended default: BM25-first lexical, embeddings pluggable & off-by-default.** Preserves the "L0 is deterministic and golden-tested" invariant the trust story rests on; ships offline; honest bounded failure mode. Embeddings must carry `model_version + chunking_strategy` in provenance — which is *also* why they cannot be the deterministic floor.

A subtlety to flag: the current `folder` provider returns `corroborated_inference` at confidence 0.7 on *any* keyword hit. For citation-support that bar is **too generous** — lexical term-overlap is evidence of topicality, not of claim support. Feature 1's lexical engine should be more conservative.

## 1.5 CAG vs RAG

RAG (retrieve-then-judge) is the natural fit — unit of work is "find the supporting passage in *this* reference." CAG (preload) helps only when one work is cited many times. **Rule (non-negotiable): CAG/cache outputs are never promoted to `operational_fact`** — encode as a hard ceiling, not a guideline. Recommendation: RAG/BM25 for v1.x; CAG deferred.

## 1.6 Epistemic-status mapping

| Verdict | Status | Confidence | Ceiling rule |
|---|---|---|---|
| **supported** (full text present, strong match) | `corroborated_inference` | 0.6–0.8 | **Never** `operational_fact` |
| **partially_supported** | `working_hypothesis` | 0.4–0.6 | claim broader than passage |
| **unsupported** (full text present, no match) | `speculative_hypothesis` | 0.2–0.4 | "couldn't find support" ≠ "isn't there" |
| **contradicted** (cited work asserts opposite) | `contradicted` | human-verify | strongest negative; surface loudly |
| **uncheckable** (full text absent) | caps `working_hypothesis` | ≤0.5 | abstract-only / KB-frontmatter ceiling |

**Hard caps:** full-text-absent → ≤ `working_hypothesis`; abstract-only → ≤ `working_hypothesis`; CAG → ≤ `corroborated_inference`; any "supported" → ≤ `corroborated_inference`.

**Asymmetric-risk (clinical):** for dose/efficacy/safety/diagnostic-threshold claims, require `source_independence ≥ 2` before "supported"; single lexical hit → `working_hypothesis` max. False-negative (missing an unsupported clinical citation) is the costly error; bias toward flagging.

## 1.7 Layer placement

- **L0 `scripts/core/citation_support.py`** — BM25 lexical scorer + verdict + status mapping. Deterministic, golden-tested, no network, no model. The v1.x deliverable. Sibling of `citation_parse.py`.
- **L1 `fulltext_*` provider(s)** — `fulltext_bm25` (local, deterministic), later `fulltext_vec` (pluggable, model-gated). `egress_guard.assert_local_only` refuses remote variants in reviewer-mode for free.
- **L2 orchestration** — `peer-reviewer` fans out over `citation_parse` markers, calls the L0 engine per citation, aggregates via `epistemic_grade`. **`peer-reviewer` keeps `Read, Grep, Glob` only** — the work is deterministic local file reading, needs neither network nor Bash escalation. **The moat holds.**

## 1.8 Phasing

- **v1.x (now):** L0 `citation_support.py`, BM25/lexical, over user-supplied local full-text (a) + KB-resident (d), abstract-only fallback (b). Verdicts supported / partially / unsupported / uncheckable. `contradicted` deferred.
- **v2.x:** `fulltext_vec` embedding layer, model-gated; author-mode OA fetch (c) behind `egress_guard`.
- **v3:** hybrid + reranker; semantic `contradicted` verdict.

---

# Feature 2 — Contradiction-detection vs the knowledge base

## 2.1 Problem statement

When a new manuscript claim conflicts with something already **established** in the vault/prior work, that conflict should surface and the claim should drop to `contradicted` — the one rung with *no producer* today. Nothing in the codebase ever emits `contradicted`; it exists in `lib/epistemic.LADDER` purely as a target. Feature 2 makes it real. It is the v2-deferred / v3 item the spec explicitly named, and the harder of the two.

## 2.2 Retrieval-contract sketch

```
query_contradiction(req) -> response

req = { claim_text, polarity_hint?, backend:"folder"|"obsidian", path, mode }

response = {
  conflicts: [ { doc, loc, snippet, kb_status, relation:"contradicts"|"tension"|"agrees", source } ],
  finding: <graded finding>,
}
```

Each conflict carries the vault note's `kb://` trace *and* that note's own epistemic status — **contradicting a `canonical_fact` note is a louder signal than contradicting a `speculative_hypothesis` note.** The strength of a contradiction is a function of *what* it contradicts.

## 2.3 Where the "established" text comes from

The KB **is** the source, already local (`folder`/`obsidian`). The hard part is not retrieval — it is **detecting opposition** (claim A vs not-A), which lexical overlap cannot do (a contradicting passage is *topically identical* and shares all the keywords). This is why BM25, sufficient as a floor for Feature 1, is **insufficient** for Feature 2: contradiction needs polarity/stance, not topicality.

## 2.4 Retrieval-primitive options

| Primitive | Detect opposition? | Deterministic / CI-testable? |
|---|---|---|
| **BM25/lexical** | **No** — retrieves relevant note, can't tell agree from disagree | Yes, but solves the wrong half |
| **Lexical + hand-coded negation/antonym cues** | Weakly (brittle) | Partially; high FP/FN |
| **NLI (entailment/contradiction model)** | **Yes** — literally the NLI task | No — model-dependent |
| **Embedding + stance classifier** | Yes | No — model |

**Honest conclusion: there is no deterministic, model-free floor for *true* contradiction detection.** The retrieval step is BM25-able and deterministic; the *judgment* step is irreducibly a model inference (NLI). This is why Feature 2 is harder and was deferred.

A defensible v1.x-shaped slice exists but is weaker than the name promises: **"contradiction-candidate retrieval"** — deterministically retrieve the most topically-relevant vault passages and *surface them for human judgment* with neutral framing, **without** asserting contradiction. Honest, deterministic, CI-testable — but a *retrieval aid*, not a *detector*. Calling it "contradiction-detection" would over-claim.

## 2.5 Status mapping — the critical asymmetry

| Situation | Resulting status of the NEW claim |
|---|---|
| Contradicts a `canonical_fact`/`operational_fact` note | **`contradicted`**, surfaced loudly, human-verify |
| Contradicts a `working_hypothesis`/`speculative` note | **flag as tension**, do *not* auto-demote — prior note may be the weaker party; `⚠️ contradiction` marker for human adjudication |
| NLI says "contradict" (model inference) | the *detection* is `corroborated_inference` at best; the *consequence* gates on human confirmation for clinical claims |

The detection itself is never a hard fact. Asymmetric-risk: contradiction flags against established medical knowledge are high-value (surface aggressively), but auto-demotion still gates on human confirmation — FP contradiction flags are cheap, FN are costly.

## 2.6 Layer placement

- **L0:** only the deterministic *retrieval* leg (BM25 candidate-finder).
- **L1:** extend `folder`/`obsidian` to expose candidate-retrieval; add optional `contradiction_nli` provider (off by default, model-gated, skip-if-unavailable).
- **L2:** `peer-reviewer` (reviewer-mode, local KB only — `egress_guard` keeps it offline) or a dedicated reasoning pass. NLI runs on the *local* model (Bielik/PLLuM/Qwen via vLLM) on the reviewer path, or Opus in author-mode — orchestrated, never granted egress.

## 2.7 Phasing & recommendation

- **v1.x (honest slice, optional):** deterministic contradiction-*candidate* retrieval, neutral framing, ships in L0; does *not* claim to detect contradiction.
- **v3 (the real feature):** NLI-backed detection, local-model-gated, canonical-vs-speculative asymmetry, emitting real `contradicted` statuses.

**Recommendation: keep true contradiction-detection at v3.** Feature 1 is higher-value, more tractable, and has a deterministic floor; Feature 2's honest core needs a model and belongs with v3 KB-deep-integration. Do not let the candidate-retrieval slice masquerade as the deferred capability.

---

# Cross-cutting honesty flags

- **Lexical ≠ semantic.** BM25 gives topicality, not meaning. Honest bounded floor for F1 (misses paraphrase — disclose); the *wrong half* for F2.
- **"Supported" is never proof.** A passage match is inference. The `corroborated_inference` ceiling is non-negotiable. The `folder` provider's 0.7-conf on any keyword hit is an over-claim *not* to replicate.
- **`uncheckable` must be loud.** Full-text-absent is the common case; a first-class visible verdict, not a silent pass.
- **The moat is the constraint.** Any option requiring the reviewer path to fetch a remote full-text is disqualified. The answer to "we don't have the full text" is `uncheckable`, always.

---

# Open decisions for the brainstorm

1. **Full-text sourcing policy.** Endorse (a) user-supplied + (d) KB-resident as reviewer-path sources, (b) abstract-only as labelled fallback, (c) OA-fetch author-mode-only behind `egress_guard` via `librarian` — never `peer-reviewer`?
2. **BM25 vs embedding default.** Confirm BM25/lexical as deterministic L0 floor (default, CI-tested), embeddings pluggable/off-by-default/model-gated? Or is paraphrase-robustness important enough to make an embedding backend near-term (accepting it cannot be the deterministic floor)?
3. **Partial-support representation.** `partially_supported` → `working_hypothesis`, or a richer coverage object (which sub-clauses are/aren't supported)?
4. **Confidence calibration for the lexical floor.** What term-overlap / BM25-score thresholds separate supported / partial / unsupported? (golden-fixture boundary — pin before coding.)
5. **Clinical asymmetric-risk parameters.** Confirm `source_independence ≥ 2` for "supported" on clinical claims, single hit → `working_hypothesis` max? Who flags a claim "clinical" (frontmatter tag, keyword, agent judgment)?
6. **Engine granularity.** One per-citation `citation_support.py` (matches `citation_parse` lineage) with L2 fan-out, or batch all citations in one call?
7. **Reviewer-path mechanics.** L0 engine invoked through the agent's existing Read (clean, no new grant), or via `statistician` Bash? Confirm we do **not** add any tool to `peer-reviewer`.
8. **CAG ceiling.** Ratify: CAG/cache caps at `corroborated_inference`, never `operational_fact` — in the status-mapping function, not docs.
9. **Feature 2 scope.** Keep true contradiction-detection at v3 (needs NLI/model)? And: do we ship the under-powered v1.x candidate-retrieval slice at all, or does it over-claim the name?
10. **`contradicted` consequence policy.** When detected (v3), auto-demote to `contradicted`, or only when conflicting with a `canonical`/`operational` note — always with human confirmation for clinical claims?
11. **Naming honesty.** Does "semantic citation-support" over-promise if the v1.x implementation is lexical BM25? Ship v1.x as "lexical citation-support", reserve "semantic" for the embedding layer?
