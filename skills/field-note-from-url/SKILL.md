---
name: field-note-from-url
description: >
  Capture a URL — paper, preprint, blog post, GitHub/GitLab repo, documentation
  page, video, or podcast — as a structured field note with provenance
  frontmatter (source.url, source.author, source.type, retrieval date, epistemic
  status). Extracts clean reader-mode markdown (defuddle-style) for ingestible
  pages. For blocked sources (e.g. a video whose transcript is not yet
  available), applies the STUB PATTERN: writes a stub with URL + title +
  awaiting-content and does NOT halt — content is filled in later. The
  frontmatter schema is generic and configurable via
  profile.knowledge_base.frontmatter_schema; the output location and link style
  follow profile.knowledge_base.* with universal defaults when no profile is set.
allowed-tools: [Read, Write, WebFetch]
---

# field-note-from-url

Turn a single URL into a durable, self-describing **field note**: a markdown file
that carries (a) where the content came from, (b) what kind of source it is, (c)
when it was retrieved, (d) how much you currently trust it, and (e) a clean
extract of the content itself. The note is the atomic unit of an ingest pipeline
— small, sourced, and ready to be linked, graded, or promoted later.

This is the **INGEST** stage of the scientific knowledge lifecycle. It does not
judge credibility (that is `research-scout`), does not produce a structured
literature catalog (that is `literature-search`), and does not assign a formal
graduated epistemic label with promotion thresholds (that is `epistemic-status`).
It does exactly one thing well: capture a source with honest provenance.

---

## Configuration

This skill personalizes through an optional profile. At start, read the **first**
of these that exists; if none exists, use the universal defaults:

1. `./.scriptorium/profile.md`   (project-local)
2. `~/.scriptorium/profile.md`   (user-global)
3. none → universal defaults (below)

Fields read by this skill (all optional):

| Field | Effect | Universal default |
|---|---|---|
| `knowledge_base.path` | Directory the note is written to. Empty → return the note inline in the conversation, do not write a file. | `""` (return inline) |
| `knowledge_base.link_style` | `wikilink` → `[[...]]`; `markdown` → `[text](path)`. Governs how `related`/cross-links render. | `markdown` |
| `knowledge_base.frontmatter_schema` | Path to the user's note-frontmatter schema. If set, **read it** and emit the note's frontmatter in that shape (mapping the generic fields below onto the user's field names). If unset, use the generic schema below. | `""` (generic schema) |
| `epistemic.asymmetric_risk` | `true` → high-stakes/clinical content never opens above `working_hypothesis` from a single source; preprints are capped and explicitly caveated. | `false` |
| `style.units_inline` | Keep `value unit (qualifier)` on one line in any extracted summary (e.g. `12 mg/kg (n = 30)`). | `true` |
| `style.explain_jargon` | Briefly define a domain term on first use in the summary. | `false` |

Do **not** attempt to locate the profile via `${CLAUDE_PLUGIN_ROOT}` — that
variable is reliable only in hook context. Resolve the two conventional paths
above by plain Read.

Default working language is **English**. If the source content is in another
language, keep the extract in its original language but write frontmatter and
your own summary/caveats in English (note the source language in `caveat`).

---

## Anti-hallucination discipline (non-negotiable)

This component produces provenance metadata and a content extract — both are
factual claims about a real source. Therefore:

- **`source.url` is verbatim** from the user-provided link. Never edit, "correct",
  or normalize a URL into one you did not receive.
- **`source.author`, `source.published`, `title`** come **only** from the fetched
  page (HTML `<title>`, `<meta name="author">`, `<meta property="article:*">`,
  visible byline, repo owner) or from what the user explicitly stated. If a field
  is not present in the source, write `not-in-source` (or omit it) — **never
  infer an author or date from memory.** A plausible guess is a fabrication here.
- **The content extract is quotation, not paraphrase-as-fact.** Reproduce the
  page's own words in the summary; do not add claims, numbers, citations, or
  conclusions the page does not make.
- **Mark every AI inference.** Any sentence that is your own synthesis (e.g.
  "this appears relevant to X") is prefixed `[AI-inferred]` and is kept out of the
  provenance frontmatter.
- **Absence is a finding.** A missing author, missing date, or unreachable page is
  recorded explicitly (`not-in-source`, `extraction-failed`, `awaiting-content`),
  never silently filled.
- Default epistemic status is **`working_hypothesis`** — a captured source is a
  starting point, not an established fact. Promotion is a separate, human-gated
  step (see `epistemic-status`).

---

## Generic provenance frontmatter (default schema)

Used when `knowledge_base.frontmatter_schema` is unset. When it **is** set, read
that schema and map these fields onto the user's field names; preserve the
semantics (source, type, retrieval date, epistemic status) even if the keys
differ.

```yaml
---
type: field-note
title: "<descriptive title from the source>"
source:
  url: "https://..."                 # verbatim, as received
  author: "<from page metadata, or 'not-in-source'>"
  type: paper | preprint | repo | docs | blog | video | podcast | web
  published: "YYYY-MM-DD"            # from source metadata, else 'not-in-source'
retrieved: "YYYY-MM-DD"              # the date you fetched it (today)
status:
  epistemic: working_hypothesis      # default; speculative_hypothesis for un-extracted stubs
  confidence: 0.5                    # 0.0-1.0; lower for un-verified / un-extracted
  source_independence: 1             # this note = 1 source; bump on cross-reference
  caveat: ""                         # e.g. "preprint, not peer-reviewed" / "awaiting transcript"
tags:
  - field-note/<source.type>         # e.g. field-note/paper
  - topic/<domain>                   # 1-2; from the content, not invented
related: []                          # cross-links, rendered per knowledge_base.link_style
---
```

**Wikilink quoting note:** if `knowledge_base.link_style: wikilink`, every link in
a YAML list MUST be a quoted string — `- "[[Note Name]]"`, never `- [[Note Name]]`
— because an unquoted `[[...]]` (and any `|` alias inside it) breaks the YAML
block and silently hides the whole frontmatter from downstream tooling. This is
the single most common provenance-corruption bug; guard it.

**Status seeds by extraction outcome:**

| Outcome | epistemic | confidence | caveat |
|---|---|---|---|
| Clean extract obtained | `working_hypothesis` | 0.5 | type-specific (e.g. preprint caveat) |
| Stub (blocked / awaiting content) | `speculative_hypothesis` | 0.2 | `"awaiting-content — <reason>"` |
| Extraction failed (paywall / JS-only) | `speculative_hypothesis` | 0.2 | `"extraction-failed — <reason>"` |

If `epistemic.asymmetric_risk: true` and the content is clinical/high-stakes:
cap a single-source note at `working_hypothesis` regardless, force an explicit
`caveat`, and never seed higher even on a clean extract.

---

## Source-type routing

Detect the type from the URL host/path, then route:

| URL pattern | `source.type` | Extraction route |
|---|---|---|
| `arxiv.org`, `biorxiv.org`, `medrxiv.org` | `preprint` | WebFetch abstract page → extract title, authors, abstract. Caveat `"preprint, not peer-reviewed"`. |
| Publisher / journal article, DOI landing | `paper` | WebFetch the landing/abstract page (public metadata + abstract only). Do not bypass paywalls — see Boundaries. |
| `github.com`, `gitlab.com`, `huggingface.co/.../tree` | `repo` | WebFetch the repo/README page → extract description, README summary, owner. |
| Documentation site, API reference | `docs` | Defuddle-style clean extract of the page. |
| Blog post, newsletter, personal site | `blog` | Defuddle-style clean extract. |
| Video host (e.g. a watch/embed URL) | `video` | **STUB PATTERN** if the transcript is not fetchable (see below). |
| Podcast episode page | `podcast` | Extract show notes if present; else STUB if audio-only with no transcript. |
| Anything else, reachable | `web` | Defuddle-style clean extract. |

"Defuddle-style" = fetch the page and reduce it to reader-mode markdown: keep the
main article body, drop navigation, ads, cookie banners, related-links rails, and
boilerplate. With only `WebFetch` available, instruct the fetch to return the main
textual content and strip chrome; if a richer clean-extraction tool is present in
the host environment, prefer it. The goal is a token-lean, faithful capture — not
a screenshot of the whole DOM.

---

## STUB PATTERN (do NOT halt on blocked sources)

Some sources cannot be ingested at capture time — most commonly a **video or
podcast whose transcript is not yet available**, but also any page that is
unreachable, login-walled, or pure-JavaScript with no server-rendered text. When
that happens, **write a stub and keep going.** A blocked fetch is an expected
branch, not an error to abort on.

A stub note:

1. Records everything you **do** have: the verbatim `source.url`, a `title` (from
   the user's words or a visible page title; else `"<pending>"`), the channel /
   author / repo owner if derivable from the URL, and `retrieved` = today.
2. Sets `status.epistemic: speculative_hypothesis`, `confidence: 0.2`, and
   `caveat: "awaiting-content — <reason>"` (e.g. `awaiting transcript`,
   `login-walled`, `JS-only render`).
3. Adds a `tags:` marker `status/awaiting-content` (and, for transcript-pending
   media, `status/awaiting-transcript`) so a later pass can find and complete it.
4. Puts a placeholder in the body: a `## Content` heading with a single line —
   `TODO: paste transcript / full text here, then re-run extraction.`
5. **Returns normally.** Report that a stub was written and what is needed to
   complete it. Never raise the blocked fetch as a failure that stops the task.

When the user later supplies the missing content (e.g. pastes a transcript),
re-run: replace the placeholder body with the clean extract, raise
`epistemic` to `working_hypothesis`, set `confidence` ~0.5, drop the
`status/awaiting-*` tags, and clear the `awaiting-content` caveat.

---

## Procedure

1. **Read profile** (resolution order above). Note `knowledge_base.path`,
   `link_style`, `frontmatter_schema`, `epistemic.asymmetric_risk`, `style.*`.
2. **Detect source type** from the URL (routing table). If it is a known
   transcript-gated medium with no fetchable text → go straight to the stub flow.
3. **Fetch + extract** (non-stub path): WebFetch the URL, reduce to clean
   reader-mode markdown (drop chrome). Pull `title`, `author`, `published` from
   page metadata only; any field absent → `not-in-source`.
4. **Build frontmatter:** generic schema by default, or the user's schema if
   `frontmatter_schema` is set (map fields, preserve semantics). Seed `status`
   from the extraction-outcome table and `asymmetric_risk`. Quote all wikilinks
   in lists.
5. **Write the body:** a short `## Summary` (your own 2-4 sentence neutral
   description; mark synthesis as `[AI-inferred]`), then `## Content` with the
   clean extract (the source's own words). Honor `style.units_inline` and
   `style.explain_jargon` in the summary.
6. **Set tags:** mandatory `field-note/<source.type>`; 1-2 `topic/<domain>` drawn
   from the content (not invented); status markers for stubs/failures.
7. **Persist:** if `knowledge_base.path` is set, write
   `<knowledge_base.path>/<slug>.md` where slug = `YYYY-MM-DD-<author-or-topic>-<short-descriptor>`
   (lowercase, kebab-case, no diacritics, ~50 chars max). If `knowledge_base.path`
   is empty, **return the full note inline** in the conversation instead of
   writing a file.
8. **Report:** path (or "returned inline"), `source.type`, epistemic seed, and —
   for stubs — exactly what is needed to complete the note.

### Slug formation

`YYYY-MM-DD` (retrieval date) + a stable handle (author surname, repo owner, or
the dominant topic word) + a 1-3 word descriptor. Lowercase, hyphen-separated,
ASCII-fold diacritics, no spaces. Example shape: `2026-06-04-doe-attention-routing`.
Never embed query strings or tracking params from the URL into the slug.

---

## Boundaries (what this is NOT)

Per the lifecycle, this skill stays narrowly in INGEST. Hand off when:

- **vs `literature-search`** — that skill runs structured database queries
  (PEO/PICO suites, snowball, recall checks) and emits a catalog of records with
  PMIDs/DOIs from tool responses. This skill captures **one URL** the user already
  has. If the user wants to *find* sources, that is `literature-search`. If a URL
  is a bibliographic database record (e.g. a PubMed entry), suggest
  `literature-search` rather than scraping it here.
- **vs `research-scout`** — that agent grades credibility (tiered sources,
  epistemic + independence scoring) and compares findings to an existing knowledge
  base, returning a *proposal*. This skill does **not** judge how trustworthy the
  source is; it seeds a default `working_hypothesis` and stops. Promote credibility
  questions to `research-scout`.
- **vs `epistemic-status`** — that skill assigns the graduated label
  (`speculative → working → corroborated → operational → canonical`, with
  confidence, source-independence, and promotion thresholds, honoring
  `asymmetric_risk`). This skill only **seeds** a default status at capture; formal
  grading/promotion is `epistemic-status`'s job and is human-gated.
- **Personal-vault cataloging stays out of scope.** This skill writes a generic
  field note to `knowledge_base.path` (or returns it inline). It does not perform
  any vault-, MOC-, or schema-specific bookkeeping — that belongs to the user's own
  private skills, not this public component.

---

## Anti-patterns

- Do not abort on a blocked video/podcast/JS-only page — write a stub, return
  normally.
- Do not WebFetch with the intent of bypassing a paywall or login wall — capture
  only public metadata + abstract; if the body is gated, record
  `extraction-failed` and the public metadata you could see.
- Do not invent `author` or `published` from background knowledge — only the
  fetched page or the user's explicit statement; else `not-in-source`.
- Do not write unquoted `[[wikilinks]]` in YAML lists — it corrupts the
  frontmatter block.
- Do not seed an epistemic status above `working_hypothesis` at capture, and never
  above it from a single source when `asymmetric_risk: true`.
- Do not mix `[AI-inferred]` synthesis into the provenance frontmatter or present
  it as the source's claim.
- Do not write a file when `knowledge_base.path` is empty — return the note inline.

## Edge cases

- **Paywalled article** → capture title + authors + abstract from the public
  landing page; body `extraction-failed`, caveat names the paywall. No bypass.
- **Repo without a README** → scaffold from URL + owner + repo description + tags;
  no fabricated summary of code you could not read.
- **Multi-part series** → one note per part; cross-link them via `related`
  (quoted, per `link_style`).
- **Non-English source** → keep the extract in its original language; frontmatter,
  summary, and caveats in English; note the language in `caveat`.
- **Source language vs domain** → set `topic/<domain>` from content meaning, not
  from the site's section labels.
- **Author hub / cross-link target may not exist** → leave `source.author` as a
  plain string rather than minting a link to a note that does not exist; broken
  links are worse than plain text.
