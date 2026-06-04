# Scriptorium v0.1 Build — Implementation Plan

> **For agentic workers:** This plan is executed as a deterministic **Workflow** (ultracode)
> — pipeline over components, each `draft → validate`. Equivalent to
> superpowers:subagent-driven-development with deterministic orchestration. Steps use
> checkbox (`- [ ]`) syntax.

**Goal:** Build the public `scriptorium` Claude Code plugin (single-plugin marketplace repo)
— 4 agents + 8 skills + config + manifests + docs — generalized from the author's private
agents, fully universal (config-driven), MIT.

**Architecture:** Repo root = the plugin; co-located `marketplace.json` makes it installable.
Agents/skills auto-discovered from `agents/` and `skills/<name>/SKILL.md`. Personalization
lives in an optional `profile.md` resolved at runtime (`./.scriptorium/` → `~/.scriptorium/`
→ universal defaults); no dependence on `${CLAUDE_PLUGIN_ROOT}` in agent/skill bodies.

**Tech stack:** Markdown (agent/skill docs), JSON (manifests), Bash (validation), Python
(JSON/YAML validation). No application code, no pytest. **"Tests" = ** (a) JSON validity,
(b) frontmatter present + parseable + required fields, (c) plugin/marketplace structural
load, (d) end-user `/plugin` install smoke (manual — documented, not Bash-runnable).

**Spec:** `docs/specs/2026-06-04-scriptorium-design.md` is the contract. Every component's
required behavior is in spec §4; universality mapping in §8; shared principles in §6.

---

## Build philosophy & validation tooling

- **Content-generation tasks** (the 12 component docs): the deliverable IS the prose. The
  plan gives, per component: exact path, source basis, the spec §4 contract, hard
  boundaries, and acceptance criteria. The Workflow agent writes the full doc from those.
- **Deterministic artifacts** (manifests, config, init command, .gitignore, LICENSE): full
  content is in this plan — copy verbatim.
- **Validation helpers** (create once in Task 0.3, reuse):
  - `scripts/validate_json.sh` — `python3 -m json.tool` over both manifests.
  - `scripts/validate_frontmatter.py` — for each `agents/*.md` + `skills/*/SKILL.md`:
    YAML frontmatter parses; required keys present (`name`, `description`); `name` is
    slug-safe and matches dir/file; no tabs in YAML.
  - `scripts/validate_structure.sh` — asserts the discovery layout exists and every roster
    component from the spec has a file.

---

## File structure (decomposition lock-in)

```
scriptorium/
├── .claude-plugin/{plugin.json, marketplace.json}     # Task 0.4
├── agents/{peer-reviewer, librarian, research-scout, statistician}.md   # Phase 2
├── skills/<8 dirs>/SKILL.md                            # Phase 3
├── .claude/commands/scriptorium-init.md               # Task 1.2
├── config/profile.example.md                          # Task 1.1
├── scripts/{validate_json.sh, validate_frontmatter.py, validate_structure.sh}  # Task 0.3
├── docs/{specs/…(done), plans/…(this), philosophy.md, lifecycle.md, configuration.md}  # Phase 4
├── examples/{peer-review, librarian, research-scout, statistician}-example.md  # Phase 4
├── README.md, LICENSE, CHANGELOG.md, .gitignore       # Task 0.1–0.2, Phase 5
```

One responsibility per file. Skills are self-contained dirs. Agents are single files.

---

## Phase 0 — Scaffolding

### Task 0.1: Repo metadata files
**Files:** Create `LICENSE`, `.gitignore`, `CHANGELOG.md`

- [ ] **Step 1: LICENSE** — MIT, copyright `2026 Łukasz Minarowski`. (Standard MIT text.)
- [ ] **Step 2: .gitignore**
```gitignore
# user's real profile must never be committed (privacy)
.scriptorium/
**/.scriptorium/profile.md
# OS / editor
.DS_Store
*.swp
.obsidian/
```
- [ ] **Step 3: CHANGELOG.md**
```markdown
# Changelog

## [0.1.0] — 2026-06-04
### Added
- 4 agents: peer-reviewer, librarian, research-scout, statistician (classical + Bayesian).
- 8 skills: literature-search, reporting-guideline-check, epistemic-status,
  field-note-from-url, manuscript-imrad, peer-paraphrase, power-sample-size,
  interim-analysis-reviewer.
- Config-driven universality via `profile.md` (project-local → user-global → defaults).
- `/scriptorium-init` command; plugin + marketplace manifests; MIT license.
```
- [ ] **Step 4: Commit** — `git add LICENSE .gitignore CHANGELOG.md && git commit -m "chore: repo metadata (MIT, gitignore, changelog)"`

### Task 0.2: README skeleton
**Files:** Create `README.md` (final pass in Phase 5)
- [ ] **Step 1:** Write README with: tagline ("Protect your time, attention, and rigor — a Claude Code toolkit for the scientific knowledge lifecycle"), install block, component table (from spec §3), the lifecycle diagram, config quickstart, "no piracy / anti-hallucination" ethos line, cross-link to the author's separate scientific-writing project, license. Leave per-component deep links as relative paths.
- [ ] **Step 2: Commit** — `git commit -am "docs: README skeleton"`

### Task 0.3: Validation helpers
**Files:** Create `scripts/validate_json.sh`, `scripts/validate_frontmatter.py`, `scripts/validate_structure.sh`
- [ ] **Step 1:** `validate_json.sh` — loops both manifests through `python3 -m json.tool >/dev/null`, non-zero on failure, prints OK per file.
- [ ] **Step 2:** `validate_frontmatter.py` — globs `agents/*.md` + `skills/*/SKILL.md`; for each: split `---` frontmatter, `yaml.safe_load`, assert `name` + `description` present, `name` matches `[a-z0-9-]+` and equals filename/dirname stem; exit 1 with a per-file report on any failure.
- [ ] **Step 3:** `validate_structure.sh` — asserts the 4 agent files + 8 skill dirs (each with SKILL.md) + both manifests + config + init command exist; lists any missing.
- [ ] **Step 4: Run all three** — expected: they run (will report missing components until Phases 2–3 land; that's fine now).
- [ ] **Step 5: Commit** — `git commit -am "build: json + frontmatter + structure validators"`

### Task 0.4: Manifests
**Files:** Create `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- [ ] **Step 1: plugin.json** — verbatim from spec §2.2.
- [ ] **Step 2: marketplace.json** — verbatim from spec §2.3 (`source: "./"`).
- [ ] **Step 3: Validate** — `bash scripts/validate_json.sh` → expected: both OK.
- [ ] **Step 4: Commit** — `git commit -am "feat: plugin + marketplace manifests"`

---

## Phase 1 — Config layer

### Task 1.1: profile.example.md
**Files:** Create `config/profile.example.md`
- [ ] **Step 1:** Header comment + the YAML block verbatim from spec §5 (empty/neutral values; `shadow_library_optin: false`). Below the block: one-line doc per field.
- [ ] **Step 2: Validate** — `python3 -c "import yaml,sys; yaml.safe_load(open('config/profile.example.md').read().split('\`\`\`yaml')[1].split('\`\`\`')[0])"` → no error.
- [ ] **Step 3: Commit** — `git commit -am "feat(config): profile.example.md universal template"`

### Task 1.2: scriptorium-init command
**Files:** Create `.claude/commands/scriptorium-init.md`
- [ ] **Step 1:** Frontmatter `description: Initialize a local scriptorium profile (./.scriptorium/profile.md) from the bundled template.` Body: instruct to (a) check if `./.scriptorium/profile.md` exists → if so, report and stop (no overwrite); (b) else create `./.scriptorium/` and copy the contents of the plugin's `config/profile.example.md` into `./.scriptorium/profile.md`; (c) remind the user it is git-ignored and to fill journals / KB path / domains. Note the `${CLAUDE_PLUGIN_ROOT}` caveat: the command instructs Claude to locate `config/profile.example.md` within the installed plugin dir (documented fallback), not via env var in bash.
- [ ] **Step 2: Validate** — `bash scripts/validate_json.sh` (unaffected) + manual read.
- [ ] **Step 3: Commit** — `git commit -am "feat(command): /scriptorium-init"`

### Task 1.3: configuration.md
**Files:** Create `docs/configuration.md`
- [ ] **Step 1:** Document the resolution order, every `profile.*` field (purpose, default, example), the privacy note (real profile git-ignored), and the per-component fallback behavior when no profile is present.
- [ ] **Step 2: Commit** — `git commit -am "docs: configuration guide"`

---

## Phase 2 — Agents (pipeline; each: draft → frontmatter-validate → commit)

Each agent doc: YAML frontmatter (`name`, `description`, `tools`, `model`, optional `color`)
+ body per spec §4. All inherit shared principles (spec §6). Generalize per spec §8 — **no
personal names, institutions, or vault paths**; route them to `profile.*`. Default language
English. Acceptance (all agents): (i) frontmatter valid; (ii) zero strings matching
the author's personal identifiers, institutions, journals, vault paths, and other private
project names (grep gate); (iii)
profile-resolution paragraph present; (iv) anti-hallucination + boundaries section present.

### Task 2.1: peer-reviewer
**Files:** Create `agents/peer-reviewer.md` · **Source:** the author's private peer-reviewer agent
- [ ] **Step 1:** Generalize the source: keep the full rubric (guideline detection, stats, IMRaD, ethics, integrity red-flags, injection-as-data), the offline/read-only/COPE stance, the report structure. Replace the author's journal/institution scope-fit with `profile.reviewer.journals` (fallback: generic venue-fit). Report language from `profile.reviewer.language` (default en). `tools: Read, Grep, Glob`, `model: opus`.
- [ ] **Step 2: Validate** — frontmatter + grep gate (expected: no personal strings).
- [ ] **Step 3: Commit** — `git commit -am "feat(agent): peer-reviewer (generalized, offline confidential)"`

### Task 2.2: librarian
**Files:** Create `agents/librarian.md` · **Source:** a local librarian-agent concept note + the author's private library-cataloging skill (dedupe logic) + spec §4 A2
- [ ] **Step 1:** Write fresh in English. Five-layer separation (facts / publisher-claims / public-opinions / agent-critique / verdict), 0–100 weighted scoring, verdict labels, time+money cost, sources-checked disclosure. Hard boundaries: no paywall bypass / piracy / ToS-scraping / fabricated review counts; "access limited" honesty. Strategic-fit from `profile.librarian.domains`. Optional write only if `profile.librarian.catalog_path` set (dedupe-first). `tools: Read, Grep, Glob, WebSearch, WebFetch, Write`, `model: sonnet`.
- [ ] **Step 2: Validate** — frontmatter + grep gate + assert the 5-layer separation and the "no fabricated reviews" rule are present.
- [ ] **Step 3: Commit** — `git commit -am "feat(agent): librarian (acquisition advisor)"`

### Task 2.3: research-scout
**Files:** Create `agents/research-scout.md` · **Source:** the author's private research-scout agent
- [ ] **Step 1:** Generalize: keep tiered sources (T1–T4), prudence/epistemic grading, dedup-by-DOI, OA-resolution (Unpaywall/OpenAlex), data-not-instructions, no-fabrication, propose-don't-write. Replace vault-project matching with `profile.knowledge_base.path` (skip compare if unset). Institutional resolver from `profile.research.full_text_resolver`. Shadow-library links **only if** `profile.research.shadow_library_optin: true` (default false), clearly labelled. PubMed/HF MCP tools listed but optional (degrade if absent). `model: sonnet`.
- [ ] **Step 2: Validate** — frontmatter + grep gate + assert shadow-optin defaults false.
- [ ] **Step 3: Commit** — `git commit -am "feat(agent): research-scout (retrieval + epistemic grading)"`

### Task 2.4: statistician
**Files:** Create `agents/statistician.md` · **Source:** new, spec §4 A6
- [ ] **Step 1:** Write fresh. Classical block (descriptives, t/MW, paired, ANOVA/KW + post-hoc, χ²/Fisher, correlation, linear/logistic/Cox, mixed, multiplicity Bonferroni/Holm/BH-FDR, diagnostics, survival). Bayesian block (weakly-informative priors stated, posterior, credible intervals, Bayes factors, WAIC/PSIS-LOO, R-hat/ESS/divergences, PPC). Runtime from `profile.statistics.prefer_runtime` (python: statsmodels/pingouin/scipy/lifelines; bayes: PyMC+ArviZ or bambi; or R brms) → degrade to advisory + emit script if `none`/absent. Discipline: never fabricate a statistic; report verbatim; state assumptions checked; flag underpower / violated assumptions / post-hoc power invalid; exploratory vs confirmatory; effect sizes + uncertainty. Include the ML scope-note (optional-stopping/multiplicity for repeated evaluations lives here, distinct from clinical S8). `tools: Read, Grep, Glob, Bash, Write`, `model: opus`.
- [ ] **Step 2: Validate** — frontmatter + grep gate + assert both classical & Bayesian blocks + "never fabricate" rule.
- [ ] **Step 3: Commit** — `git commit -am "feat(agent): statistician (classical + Bayesian)"`

---

## Phase 3 — Skills (pipeline; each: draft → frontmatter-validate → commit)

Each skill: `skills/<name>/SKILL.md`, frontmatter (`name`, `description`, `allowed-tools`
array). Body per spec §4. Same grep gate + universality as agents. Acceptance: frontmatter
valid; no personal strings; anti-hallucination rule present where claims/citations are produced.

### Task 3.1: literature-search
**Source:** the author's private pubmed-to-literature-note skill → generalize (vault path → `profile.knowledge_base.path`; PMIDs/DOIs only from tool responses; PEO/PICO suites, snowball, recall). `allowed-tools: [Read, Write, WebSearch, WebFetch]`. Commit `feat(skill): literature-search`.

### Task 3.2: reporting-guideline-check
**Source:** extract the guideline rubric from peer-reviewer (STROBE/CONSORT(+AI)/PRISMA(2020/-DTA)/TRIPOD(+AI)/STARD/CLAIM/SPIRIT/CHEERS/CARE/ARRIVE/GRADE/SPIN). Item-by-item compliance table + gaps + fix suggestions. Standalone-usable on own draft. `allowed-tools: [Read, Grep, Glob]`. Commit `feat(skill): reporting-guideline-check`.

### Task 3.3: epistemic-status
**Source:** the author's private vault evidence-status note (read if present) + spec §4 S3. Graduated labels + confidence + source_independence + promotion thresholds; `profile.epistemic.asymmetric_risk` strict mode; contradiction check. `allowed-tools: [Read, Grep, Glob]`. Commit `feat(skill): epistemic-status`.

### Task 3.4: field-note-from-url
**Source:** the author's private field-note-from-url skill → generalize (generic frontmatter via `profile.knowledge_base.frontmatter_schema`; defuddle-style extraction; **stub pattern** for blocked sources, do not halt). `allowed-tools: [Read, Write, WebFetch]`. Commit `feat(skill): field-note-from-url`.

### Task 3.5: manuscript-imrad
**Source:** new, spec §4 S5. IMRaD scaffold + structure-lint (section presence/order, hypothesis→methods→results→conclusion coherence, claims-vs-data, explicit Limitations, spin-flag). `allowed-tools: [Read, Grep, Glob]`. Commit `feat(skill): manuscript-imrad`.

### Task 3.6: peer-paraphrase
**Source:** new. **PEER framework (verbatim contract — no placeholder):**
- **P — Point:** identify the single main point first (not synonym-swap); make it a strong first sentence.
- **E — Evidence:** identify supporting data/studies/quotes/results; **never distort evidence or argument strength**; restructure language, not meaning.
- **E — Explanation:** add/repair the "why this evidence matters" link (the part weak paraphrase omits).
- **R — Repeat/Link:** close by returning to the point or bridging to the next paragraph.
- **Rules:** decompose into functions before rewriting; **one-point rule** (1 paragraph = 1 idea; split if >1); shorter/clearer/more academic but **not more complex**; **skip test** (first sentences alone convey structure); **no new claims, no changed argument strength**; keep citations attached to their evidence; this is paraphrase, not patchwriting.
- **Output:** paraphrased text + optional P/E/E/R map + flag when source paragraph has >1 point (suggest split). Include the worked mini-example (social-media/anxiety) from the spec discussion.
- `allowed-tools: [Read]`. Commit `feat(skill): peer-paraphrase (PEER)`.

### Task 3.7: power-sample-size
**Source:** new, spec §4 S7. Inputs (design family, effect size/means+SD/rates, α, power, allocation, dropout) → N | power | MDE; sensitivity table; ready Methods sentence; flags post-hoc/observed power invalid; statistical vs clinical significance. Runtime python (statsmodels.stats.power/pingouin) or R; degrade to formulas. `allowed-tools: [Read, Bash, Write]`. Commit `feat(skill): power-sample-size`.

### Task 3.8: interim-analysis-reviewer
**Source:** a contributed interim-analysis-reviewer skill file — **drop-in**. Copy body verbatim; **normalize frontmatter** to `allowed-tools: [Read, Grep, Glob]` (from space-form), retain `name`, `description`, `when_to_use`, `argument-hint`. Add a one-line cross-ref to A6/S2 boundary (clinical-only; non-clinical sequential testing → statistician). `allowed-tools: [Read, Grep, Glob]`. Commit `feat(skill): interim-analysis-reviewer (contributed)`.

---

## Phase 4 — Docs & examples

### Task 4.1: philosophy.md + lifecycle.md
- [ ] **Step 1:** `docs/philosophy.md` — expand the 5 Design-DNA principles (spec §1) with rationale + how each shows up in components.
- [ ] **Step 2:** `docs/lifecycle.md` — the 7 stages, which component(s) serve each, the data-flow (scout→literature-search→…→peer-reviewer/S2/S8→knowledge-gardener[v2]).
- [ ] **Step 3: Commit** — `git commit -am "docs: philosophy + lifecycle"`

### Task 4.2: examples (4 agent transcripts)
- [ ] **Step 1:** `examples/{peer-review, librarian, research-scout, statistician}-example.md` — one short, realistic, **synthetic** transcript each (neutral domain, no real patient/manuscript data), showing input → output shape. Mark as illustrative.
- [ ] **Step 2: Commit** — `git commit -am "docs: worked examples per agent"`

---

## Phase 5 — Validation, smoke, release

### Task 5.1: Full validation gate
- [ ] **Step 1:** `bash scripts/validate_json.sh` → both OK.
- [ ] **Step 2:** `python3 scripts/validate_frontmatter.py` → all 12 components pass.
- [ ] **Step 3:** `bash scripts/validate_structure.sh` → no missing components.
- [ ] **Step 4:** Grep gate across `agents/ skills/` for personal strings → **zero hits** (privacy/universality). Command: run a private wordlist (the author's name, institutions, journals, vault paths, other private project names) as a regex over `agents/ skills/` — kept out of this public plan by design.
- [ ] **Step 5:** Quality-oversight pass (per author preference): dispatch halucynacja-watch + code-watch over the generated docs → fix flagged items.

### Task 5.2: README final + install smoke instructions
- [ ] **Step 1:** Finalize README: component deep-links, config quickstart, and the **install smoke** the user runs manually: `/plugin marketplace add ~/code/scriptorium` (local) → `/plugin install scriptorium@scriptorium` → confirm agents/skills appear. (Cannot be run from Bash — documented as a user step.)
- [ ] **Step 2: Commit** — `git commit -am "docs: README final + install smoke"`

### Task 5.3: Release tag + GitHub (gated)
- [ ] **Step 1:** `git tag v0.1.0`.
- [ ] **Step 2 (gated on user):** create public GH repo `kicrazom/scriptorium` and push — **ask before pushing** (outward-facing, hard to reverse). Provide: `gh repo create kicrazom/scriptorium --public --source=. --description "…" --push`.
- [ ] **Step 3 (gated on user):** add a hub note in the author's private vault with `code_path: ~/code/scriptorium`, `github:`, link to spec — separate vault commit, proposed not auto-run.

---

## Self-Review (spec coverage)

- spec §3 roster (4 agents + 8 skills) → Tasks 2.1–2.4, 3.1–3.8 ✓
- §2 packaging (manifests, auto-discovery, install) → Tasks 0.4, 5.2 ✓
- §5 config mechanism (profile resolution, init, privacy) → Tasks 1.1–1.3, 0.1(.gitignore) ✓
- §6 shared principles → enforced via per-component acceptance + grep gate (Tasks 2.x/3.x/5.1) ✓
- §7 boundaries → embedded in each component body (acceptance asserts boundary sections) ✓
- §8 universality mapping → grep gate (Task 5.1 Step 4) + per-task generalization ✓
- §9 license/versioning → Tasks 0.1, 5.3 ✓
- §11 open questions (all defaulted: repo home, init in v1, 4 examples, identity) → Tasks 1.2, 4.2, 0.4, 5.3 ✓

**Placeholder scan:** deterministic artifacts have full content; generative tasks carry
explicit contracts + acceptance (justified adaptation for content generation). PEER contract
embedded verbatim (no placeholder). **Type consistency:** `profile.*` field names match spec
§5 across all tasks; validator script names consistent (validate_json/frontmatter/structure).
