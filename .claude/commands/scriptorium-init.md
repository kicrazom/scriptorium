---
description: Initialize a local scriptorium profile (./.scriptorium/profile.md) from the bundled template.
---

# /scriptorium-init

Create a project-local scriptorium profile so the agents and skills can be personalized.

Do the following:

1. **Check for an existing profile.** If `./.scriptorium/profile.md` already exists, report
   its path and **stop** — do not overwrite it.

2. **Locate the template.** Find `config/profile.example.md` inside the installed
   `scriptorium` plugin directory. (Do not rely on `${CLAUDE_PLUGIN_ROOT}` from bash — it is
   only reliable in hook context. Locate the plugin directory by reading the bundled
   `config/profile.example.md` path from the plugin install location.)

3. **Create the profile.** Make the directory `./.scriptorium/` and copy the contents of
   `config/profile.example.md` to `./.scriptorium/profile.md`.

4. **Remind the user.** Tell them:
   - The file is **git-ignored by default** — their personal settings stay out of version control.
   - Fill in the fields they care about: `reviewer.journals`, `knowledge_base.path`,
     `librarian.domains`, `research.full_text_resolver`, `epistemic.asymmetric_risk`.
   - Every field is optional; empty values fall back to universal defaults.

Keep the output short: confirm the path created and list the 3–4 highest-value fields to fill.
