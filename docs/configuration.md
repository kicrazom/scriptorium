# Configuration

Scriptorium works out-of-the-box with **zero configuration**: with no profile present, every
agent and skill runs on sensible **universal defaults** and is immediately useful to a stranger.
Default working language is **English**; the core is domain-neutral.

Personalization is **optional** and lives entirely in a single markdown file, `profile.md`.
Nothing about you, your institution, or your file layout is hardcoded anywhere in the plugin —
if you want components to know your target journals, your notes directory, or your preferred
statistics runtime, you put that in a profile, and components read it at start.

This document explains:

1. [How profiles are resolved](#1-profile-resolution-order) (project-local → user-global → defaults)
2. [Creating a profile](#2-creating-a-profile)
3. [Every field](#3-field-reference) — purpose, default, example
4. [Privacy](#4-privacy) — your real profile is git-ignored
5. [Per-component fallback](#5-per-component-fallback-when-no-profile-is-present) when no profile is present

---

## 1. Profile resolution order

At start, **each component independently** reads the **first** of these that exists and stops:

| Order | Path | Scope |
|-------|------|-------|
| 1 | `./.scriptorium/profile.md` | **Project-local** — relative to the current working directory; wins over everything else. |
| 2 | `~/.scriptorium/profile.md` | **User-global** — applies to every project unless a project-local profile overrides it. |
| 3 | *(none)* | **Universal defaults** — documented per component; no file needed. |

Resolution is **first-match-wins, not merge**. If a project-local profile exists, the
user-global one is ignored entirely (they are not combined field-by-field). To customize a
single project while keeping a global baseline, copy your global profile into the project and
edit the few fields that differ.

> **Why two locations?** The user-global profile (`~/.scriptorium/profile.md`) carries your
> stable preferences — runtime, link style, default guidelines. The project-local profile
> (`./.scriptorium/profile.md`) pins project-specific context — this project's knowledge-base
> root, this project's target venues — and overrides the global one for that working directory.

> **Note on path discovery.** Components locate the profile by reading these **conventional
> paths directly** (a plain Read/Glob), not via any plugin-root environment variable. This is
> deliberate: `${CLAUDE_PLUGIN_ROOT}` is reliable only in hook context, not inside agent/skill
> bodies, so the profile is never resolved relative to where the plugin happens to be installed.
> It is always resolved relative to your **current working directory** and your **home directory**.

---

## 2. Creating a profile

A profile is a markdown file containing a single fenced **YAML block**. The plugin ships
[`config/profile.example.md`](../config/profile.example.md) as both the documentation source and
the copy source.

**Automatic (recommended):**

```
/scriptorium-init
```

This copies `config/profile.example.md` to `./.scriptorium/profile.md` in the current project.
Open it and fill in the values you care about.

**Manual:**

```bash
mkdir -p .scriptorium
cp <plugin>/config/profile.example.md .scriptorium/profile.md   # project-local
# or, for a user-global profile:
mkdir -p ~/.scriptorium
cp <plugin>/config/profile.example.md ~/.scriptorium/profile.md
```

Every field is **optional**. An empty value (`""`, `[]`, or an omitted key) means "use the
universal default". You only need to set the handful of fields relevant to how you work.

The full template (matching `config/profile.example.md`):

```yaml
reviewer:
  journals: []            # [{name, scope}] for peer-reviewer scope-fit; empty → generic venue-fit
  default_guidelines: [STROBE, CONSORT, PRISMA, TRIPOD]
  language: en            # referee-report language

knowledge_base:
  path: ""                # root of your notes; empty → no compare / no auto-write
  link_style: wikilink    # wikilink | markdown
  frontmatter_schema: ""  # optional path to your note schema

research:
  sources: [pubmed, openalex, crossref, arxiv, europepmc]
  full_text_resolver: ""  # institutional proxy/login URL; empty → DOI resolver only
  shadow_library_optin: false   # PUBLIC DEFAULT: off

librarian:
  domains: []             # your interest areas → strategic-fit scoring
  catalog_path: ""        # optional; empty → return evaluation only, no write

statistics:
  prefer_runtime: python  # python | r | none
  bayesian_backend: pymc  # pymc | bambi | brms

epistemic:
  asymmetric_risk: false  # true → strict promotion thresholds (clinical / high-stakes)

style:
  units_inline: true
  explain_jargon: false
```

---

## 3. Field reference

Every field below is optional. The **Default** column is what the component uses when the field
is empty or the profile is absent. Examples are neutral and illustrative.

### `reviewer.*` — peer-reviewer (A1) and reporting checks (S2)

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `reviewer.journals` | Target-venue profiles for the peer-reviewer's **scope-fit** assessment. A list of `{name, scope}` objects. | `[]` → generic "fit to a target venue, novelty, contribution" | `[{name: "Journal of Applied X", scope: "applied methods, empirical studies"}]` |
| `reviewer.default_guidelines` | Reporting guidelines to consider **first** when classifying a study design. | `[STROBE, CONSORT, PRISMA, TRIPOD]` | `[STROBE, CONSORT, PRISMA, TRIPOD, CARE]` |
| `reviewer.language` | Language of the referee report. | `en` | `de` |

### `knowledge_base.*` — research-scout (A3), literature-search (S1), field-note-from-url (S4)

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `knowledge_base.path` | Root directory of **your** markdown notes. Enables research-scout's compare-to-KB step and the skills' optional auto-write. | `""` → no compare, no auto-write (return inline only) | `"./notes"` |
| `knowledge_base.link_style` | Wikilink style used when components draft note bullets and cross-links. `wikilink` emits `[[...]]`; `markdown` emits `[](...)`. | `wikilink` | `markdown` |
| `knowledge_base.frontmatter_schema` | Optional path to **your** note-frontmatter schema, so generated notes match your conventions. | `""` → generic provenance frontmatter | `"./templates/note-schema.yaml"` |

### `research.*` — research-scout (A3), literature-search (S1)

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `research.sources` | Retrieval backends the discovery components prefer, in priority order. | `[pubmed, openalex, crossref, arxiv, europepmc]` | `[openalex, crossref, semanticscholar]` |
| `research.full_text_resolver` | Your **institutional proxy / login URL** for resolving paywalled full text. | `""` → public DOI resolver only | `"https://proxy.example.org/login?url="` |
| `research.shadow_library_optin` | Whether to surface shadow-library links (clearly labelled, never as a peer-reviewed source). | `false` (**public default: off**) | `false` |

> **`research.shadow_library_optin` stays `false`** for public, shared, or institutional use.
> When `false`, paywalled items fall back to legal open-access routes (Unpaywall / OpenAlex)
> and, if set, your `full_text_resolver`.

### `librarian.*` — librarian (A2)

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `librarian.domains` | Your fields of interest, used to compute the **strategic-fit** score of a book / course / resource. | `[]` → asks for / uses your stated goal | `[data-analysis, study-design, scientific-writing]` |
| `librarian.catalog_path` | If set, the librarian **may write** an evaluation note here (dedupe-checked first). If empty, it returns the evaluation only. | `""` → return evaluation only, no write | `"./library"` |

### `statistics.*` — statistician (A6), power-sample-size (S7)

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `statistics.prefer_runtime` | Preferred analysis runtime. `none` (or an unavailable runtime) makes the statistician **degrade to advisory** — it names the correct test, states assumptions, and emits a ready-to-run script instead of executing. | `python` | `r` |
| `statistics.bayesian_backend` | Preferred Bayesian backend when a Bayesian analysis is requested. | `pymc` | `brms` |

### `epistemic.*` — epistemic-status (S3) and all components

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `epistemic.asymmetric_risk` | When `true`, enforces **strict evidence-promotion thresholds**: a single source or a preprint never exceeds `working_hypothesis` for a high-stakes / clinical claim, and new claims are checked against existing canonical claims for contradiction. | `false` | `true` |

### `style.*` — applies to every component

| Field | Purpose | Default | Example |
|-------|---------|---------|---------|
| `style.units_inline` | Keep a parameter and its unit on one line (do not wrap), e.g. a measurement written as `value unit (percent)`. | `true` | `true` |
| `style.explain_jargon` | Briefly define a technical term on first use (short plain-language gloss in parentheses). | `false` | `true` |

---

## 4. Privacy

The shipped template `config/profile.example.md` contains only **empty or neutral values** — no
personal or institutional identity. Personal settings never enter this public repository.

**Your real profile is git-ignored by default.** Add these patterns to the `.gitignore` of any
consuming project (and they are recommended in projects you generate with this plugin):

```gitignore
.scriptorium/profile.md
.scriptorium/
```

The user-global profile lives at `~/.scriptorium/profile.md`, outside any repository, so it is
never tracked.

**What this means in practice:**

- The template is documentation and is safe to commit.
- The profile you actually fill in (target venues, institutional resolver URL, notes path,
  interest areas) is treated as private and stays out of version control.
- Because resolution is relative to your working directory and home directory — never relative
  to the plugin install location — sharing the plugin never shares your profile.

---

## 5. Per-component fallback when no profile is present

Every component is designed to run with **no profile at all**. The table below states, per
component, exactly what it does on universal defaults.

| Component | Type | Behavior with **no profile** |
|-----------|------|------------------------------|
| **peer-reviewer** (A1) | agent | Generic scope-fit — "fit to a target venue, novelty, contribution" instead of named journals. Default guideline set (STROBE / CONSORT / PRISMA / TRIPOD as starting points) auto-selected from detected study design. Referee report in **English**. Always offline, read-only, confidential. |
| **librarian** (A2) | agent | Strategic-fit scoring asks for / uses your **stated goal** instead of preset interest domains. Returns the **evaluation only** — no note is written (no `catalog_path`). All five evaluation layers and the anti-hype scoring still apply. |
| **research-scout** (A3) | agent | Retrieves from the default source set (PubMed, OpenAlex, Crossref, arXiv, Europe PMC) and grades findings. **Compare-to-KB is skipped** (no `knowledge_base.path`) — it returns graded findings only. Paywalled items resolve via public DOI / open-access routes; **shadow-library links stay off**. Draft note bullets use **wikilink** style. Read-only, proposal only. |
| **statistician** (A6) | agent | Uses the **python** runtime if available (statsmodels / pingouin / scipy / lifelines; PyMC + ArviZ for Bayesian). If no runtime is available, **degrades to advisory** — names the correct test, states assumptions, emits a ready-to-run script. Never fabricates a statistic. |
| **literature-search** (S1) | skill | Runs the query suite against the default sources and **returns the catalog inline** — no auto-write (no `knowledge_base.path`). PMIDs / DOIs come only from tool responses. |
| **reporting-guideline-check** (S2) | skill | Applies the requested (or design-detected) reporting checklist item-by-item. No profile field required; works standalone on any draft. |
| **epistemic-status** (S3) | skill | Assigns graduated status + confidence + source-independence using **standard** promotion thresholds. With `asymmetric_risk` unset (default `false`), it does **not** apply the strict clinical/high-stakes thresholds. |
| **field-note-from-url** (S4) | skill | Extracts a clean-markdown note with **generic provenance frontmatter** (no `frontmatter_schema`). Returns the note inline unless a knowledge-base path is configured. Stub pattern applies for blocked sources. |
| **manuscript-imrad** (S5) | skill | Structure-lints a draft against IMRaD and emits a structure report (optional scaffold). No profile field required. |
| **peer-paraphrase** (S6) | skill | Paraphrases by the PEER framework. No profile field required. |
| **power-sample-size** (S7) | skill | Computes a-priori N / power / minimum detectable effect using the **python** runtime if available, else degrades to **explicit formulas** plus a ready-to-run script. No profile field required. |
| **interim-analysis-reviewer** (S8) | skill | Reviews interim-analysis methodology (read-only, clinical scope). No profile field required; never fabricates statistics. |

**General rule.** An empty or absent profile field always selects the **safe, public-friendly
default**: no writes, no compare-to-KB, no institutional resolver, shadow-library off, standard
(non-strict) epistemic thresholds, English output. Setting a field only ever **adds**
personalization — it never relaxes the anti-hallucination, read-only-by-default, or
confidentiality guarantees, which are fixed and not configurable.

---

## See also

- [`config/profile.example.md`](../config/profile.example.md) — the template you copy.
- [`docs/philosophy.md`](./philosophy.md) — the design principles behind the defaults.
- [`docs/lifecycle.md`](./lifecycle.md) — which component serves each lifecycle stage.
