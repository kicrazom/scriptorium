# Contributing to Scriptorium

Scriptorium is a Claude Code plugin of agents and skills for the **scientific knowledge
lifecycle** (`DISCOVER → EVALUATE → INGEST → ANALYZE → WRITE → REVIEW → MAINTAIN`).
Contributions are welcome — new components, fixes, and documentation. This guide covers the
**roster process** and the conventions every component must follow.

## Principles every component must uphold

These are non-negotiable (see [`docs/philosophy.md`](docs/philosophy.md)):

1. **Anti-hallucination first.** Numbers, citations, and quantitative claims come only from
   tool responses — never from the model. Mark every AI inference. Report "absent" /
   "not-in-source" instead of guessing.
2. **Graduated epistemics.** Where claims are produced, label evidence on a scale (see the
   `epistemic-status` skill), not as binary fact/inference.
3. **Read-only / propose-don't-write by default.** Retrieval and review components return
   proposals; writes are human-gated or enabled via the profile.
4. **Universality.** No personal names, institutions, or local paths anywhere. All
   personalization routes through `profile.*` (see [`config/profile.example.md`](config/profile.example.md)).
   Default working language is English.
5. **No paywall bypass, no piracy, no ToS-violating scraping.** Public data only.

## Roster process (proposing a new agent or skill)

1. **Open an issue** describing the component: which lifecycle stage it serves, what gap it
   fills, why it is not covered by an existing component (state the boundary).
2. **Decide agent vs skill.** Agent = autonomous, separate-context work (research, review,
   multi-step analysis). Skill = a reusable procedure/checklist/output format.
3. **Write a short spec** (a section in the issue or a file under `docs/specs/`): purpose,
   inputs, outputs, tools, hard boundaries, which `profile.*` fields it reads, and how it
   differs from neighbouring components.
4. **Implement** following the conventions below.
5. **Validate and open a PR.**

## Conventions

### Agents — `agents/<name>.md`

```yaml
---
name: <slug>            # lowercase-hyphen; must equal the filename stem
description: <one or two sentences; when to use it>
tools: Read, Grep, Glob # only what it needs
model: opus             # opus | sonnet | haiku
---
```
Body should include: purpose, hard boundaries, a **Configuration** note (profile resolution
order), a **Boundaries** note vs related components, the output format, and the
anti-hallucination discipline where it produces claims.

### Skills — `skills/<name>/SKILL.md`

```yaml
---
name: <slug>            # must equal the directory name
description: <one or two sentences>   # quote it if it contains a colon
allowed-tools: [Read, Grep, Glob]
---
```

### Configuration

If a component is personalizable, it reads the **first** profile that exists:
`./.scriptorium/profile.md` → `~/.scriptorium/profile.md` → universal defaults. Do **not**
depend on `${CLAUDE_PLUGIN_ROOT}` in an agent/skill body (it is reliable only in hooks). Add
any new field to `config/profile.example.md` and document it in `docs/configuration.md`.

## Validation (run before every PR)

```bash
bash   scripts/validate_json.sh          # manifests are valid JSON
python3 scripts/validate_frontmatter.py  # frontmatter parses; required fields; slug matches
bash   scripts/validate_structure.sh     # every roster component exists
# universality gate — must print nothing:
grep -rIEn "TODO|TBD|FIXME" agents/ skills/
```

Also run the **install smoke** locally: `/plugin marketplace add ~/code/scriptorium` then
`/plugin install scriptorium@scriptorium`, and confirm the agents/skills appear.

## Commit & PR

- Conventional-commit style (`feat(skill): …`, `fix(agent): …`, `docs: …`).
- One component or one concern per PR where practical.
- Update `CHANGELOG.md` under the current unreleased/next version.

## License

By contributing you agree your work is released under the [MIT License](LICENSE).
