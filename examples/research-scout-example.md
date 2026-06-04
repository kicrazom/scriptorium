# research-scout — worked example (illustrative, synthetic)

> **⚠️ This is an illustrative synthetic transcript, not a real session.**
> The topic, findings, sources, authors, venues, DOIs, PMIDs, citation counts, and
> knowledge-base paths below are **fabricated for documentation purposes**. They do not
> reference any real publication, person, dataset, or patient. Do not cite anything here as
> a real source. It exists only to show the **shape** of a research-scout run.
>
> Neutral fictional domain: *soil microbiology / biochar amendment* (chosen as a
> non-clinical example; the agent's grading discipline is the same in any domain).

---

## User request

> Find what's recent on **biochar amendment and soil microbial diversity in temperate
> croplands** — last ~3 years. I want to know whether the "biochar reliably raises microbial
> diversity" claim holds up. Grade how solid each finding is. No knowledge base configured.

---

## Agent run (abbreviated)

**Config loaded.** No `./.scriptorium/profile.md` or `~/.scriptorium/profile.md` found →
universal defaults. `knowledge_base.path` unset → compare-to-KB **skipped**, KB columns
`n/a`. `shadow_library_optin` default **false** → no shadow links. `epistemic.asymmetric_risk`
default false; topic is non-clinical → standard promotion thresholds. Link style: `wikilink`.

**Scope.** Population/context: temperate cropland soils. Intervention: biochar amendment.
Outcome: microbial community diversity (alpha/beta, e.g. Shannon index, 16S/ITS).
Window: 2023–2026. Non-clinical → standard grading.

**Discover.** Tier-1/2 first (PubMed + OpenAlex + Crossref/Europe PMC), then Tier-3 preprints,
then grey/web. Deduplicated by DOI. *(Values below are synthetic placeholders.)*

---

## Output

### (a) Findings table

| # | Finding (1 line) | Source (venue, year) | PMID/DOI | Full text | epistemic / conf / indep | KB target | confirms / extends / contradicts |
|---|---|---|---|---|---|---|---|
| 1 | Biochar raised soil bacterial alpha-diversity (Shannon) at 1 yr in a temperate maize field | *Synth. J. Soil Biol.* 2024 | DOI 10.0000/synthetic.0001 | OA (link) | corroborated_inference / 0.7 / 3 | n/a (no KB configured) | n/a |
| 2 | Meta-analysis (k=38 fields): mean +0.21 Shannon, but high heterogeneity (I²≈74%) | *Synth. Rev. Agroecol.* 2025 | DOI 10.0000/synthetic.0002 | OA (link) | corroborated_inference / 0.65 / 1 (meta of many) | n/a | n/a |
| 3 | Effect direction depends on feedstock + pyrolysis temp; low-temp biochar showed no change | *Synth. Soil Microbiome Lett.* 2025 | DOI 10.0000/synthetic.0003 | resolver (DOI) | working_hypothesis / 0.5 / 2 | n/a | n/a |
| 4 | Fungal (ITS) diversity *decreased* in 2 of 4 sandy soils — contradicts the blanket claim | *Synth. Front. Edaphology* 2026 | DOI 10.0000/synthetic.0004 | OA (link) | working_hypothesis / 0.45 / 1 | n/a | n/a |
| 5 | Preprint: single-site, n=4 plots, large diversity gain reported | bioRxiv-style preprint 2026 | DOI 10.0000/synthetic.0005 | OA (preprint) | speculative_hypothesis / 0.25 / 1 `preprint` | n/a | n/a |
| 6 | Citation count for #1 | OpenAlex field | — | — | not-in-source | n/a | n/a |

Notes on grading:
- #1 reaches `corroborated_inference` (≥2 independent peer-reviewed sources concur: #1 + #2 + one
  Tier-2 index hit). #3 stays `working_hypothesis` — it qualifies, not confirms, the main claim.
- #5 is a lone preprint → capped at `speculative_hypothesis`, flagged `preprint`; it does **not**
  promote the claim on its own.
- #6: OpenAlex returned no citation count for #1 in the retrieved payload → `not-in-source`
  (not guessed).

### (b) Draft note bullets

Flat list (no KB configured → place anywhere), `wikilink` style:

```
- [[https://doi.org/10.0000/synthetic.0001|SynthAuthor 2024]] — biochar raised bacterial Shannon diversity at 1 yr in a temperate maize field. `epistemic: corroborated_inference, conf 0.7, indep 3` <!-- research-scout proposal -->
- [[https://doi.org/10.0000/synthetic.0002|SynthReview 2025]] — meta-analysis k=38: mean +0.21 Shannon but I²≈74% (high heterogeneity). `epistemic: corroborated_inference, conf 0.65, indep 1` <!-- research-scout proposal -->
- [[https://doi.org/10.0000/synthetic.0003|SynthAuthor 2025]] — effect contingent on feedstock + pyrolysis temperature; low-temp biochar showed no change. `epistemic: working_hypothesis, conf 0.5, indep 2` <!-- research-scout proposal -->
- [[https://doi.org/10.0000/synthetic.0004|SynthAuthor 2026]] — fungal (ITS) diversity decreased in 2/4 sandy soils; qualifies the blanket claim. `epistemic: working_hypothesis, conf 0.45, indep 1` <!-- research-scout proposal -->
```

`[AI-inferred]` synthesis (marked, not a fact-claim): across #2–#4 the "biochar reliably raises
microbial diversity" claim looks **directionally supported but conditional** (feedstock,
pyrolysis temperature, soil texture moderate it); the unconditional version is not well
supported. This is the scout's reading across sources, not a single source's stated conclusion.

### (c) Red flags

- **Preprint not promoted.** #5 (single site, n=4) reads as a strong positive but is one
  unreviewed source — kept at `speculative_hypothesis`; do not let it carry the claim.
- **Heterogeneity.** #2's I²≈74% means the pooled effect hides wide between-study variation —
  treat the mean as a summary, not a guarantee per field.
- **Apparent tension.** #4 (fungal decrease) vs the bacterial-increase findings — not a true
  contradiction (different taxa/soils), but it bounds the claim. No existing canonical claim to
  contradict (no KB configured).
- No prompt-injection text detected in fetched abstracts/metadata. No unreachable hosts this run.

### (d) Save recommendation

Would save bullets #1–#4 as a topic note (e.g. `biochar-soil-microbial-diversity`); hold #5
(preprint) until a peer-reviewed replication appears. The conditional `[AI-inferred]` synthesis
is worth recording as a working_hypothesis line, clearly marked as inference.

> Awaiting human approval — I do not write.

---

*End of synthetic example. All identifiers above are placeholders (`10.0000/synthetic.*`) and
resolve to nothing real.*
