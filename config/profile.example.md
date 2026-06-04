# Scriptorium profile (example)
#
# Copy this file to `./.scriptorium/profile.md` (project-local) or
# `~/.scriptorium/profile.md` (user-global), then fill in the values you want.
# Run `/scriptorium-init` to create the project-local copy automatically.
#
# Resolution order each component uses at start:
#   1. ./.scriptorium/profile.md   (project-local)
#   2. ~/.scriptorium/profile.md   (user-global)
#   3. none  → universal defaults documented in each component.
#
# Your real profile is git-ignored by default — personal settings never enter the repo.
# Every field is OPTIONAL; empty values mean "use the universal default".

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

## Field reference

- **reviewer.journals** — list of `{name, scope}`; peer-reviewer uses these for scope-fit.
  Empty → generic "fit to a target venue".
- **reviewer.default_guidelines** — reporting guidelines to consider first.
- **reviewer.language** — language of the referee report (default `en`).
- **knowledge_base.path** — root of your markdown notes; enables research-scout's
  compare-to-KB and skills' auto-write. Empty → those steps are skipped.
- **knowledge_base.link_style** — `wikilink` (`[[...]]`) or `markdown` (`[](...)`).
- **knowledge_base.frontmatter_schema** — optional path to your note-frontmatter schema.
- **research.sources** — retrieval backends research-scout / literature-search prefer.
- **research.full_text_resolver** — your institutional proxy URL for paywalled full text.
- **research.shadow_library_optin** — leave `false` for public/shared use.
- **librarian.domains** — your fields of interest; drive strategic-fit scoring.
- **librarian.catalog_path** — if set, librarian may write an evaluation note (dedupe-first).
- **statistics.prefer_runtime** — `python`, `r`, or `none` (advisory + emit script).
- **statistics.bayesian_backend** — `pymc`, `bambi`, or `brms`.
- **epistemic.asymmetric_risk** — `true` enforces strict evidence-promotion thresholds.
- **style.units_inline** — keep parameter+unit on one line (e.g. `FEV1 2.4 L (72%)`).
- **style.explain_jargon** — briefly define technical terms on first use.
