---
description: Run the mechanical vault audit — frontmatter validation, wikilink resolution, tag vocabulary, tag cardinality, orphan detection, code-refs — and triage the findings.
---

# Vault Health — Mechanical Audit

## User Input

```text
$ARGUMENTS
```

Any argument is treated as an alternate vault directory (default: `vault/`).

## Execution

1. Run the audit (requires PyYAML, already in `requirements.txt`):

   ```bash
   make vault-audit          # report only
   ```

   Or directly: `.venv/bin/python scripts/vault_audit.py vault`.

2. **Triage the output.** For each finding:
   - Broken wikilink → fix the link or create the missing note (never
     delete the reference silently).
   - Frontmatter violation → conform to the contract in
     `vault/_meta/tags.md` and constitution Article XIV.
   - Unknown tag → either correct the tag, or (deliberately) add it to
     `vault/_meta/tags.md` first, then use it.
   - Tag cardinality error → ensure exactly one `type/*`, at least one
     `domain/*`, and at most one `status/*` tag per note.
   - Orphan note → add a wikilink from `vault/wellspring.md` (or another
     reachable note) to the flagged note; do not weaken the check.
   - Broken `code-refs` path → update the ref to the moved/renamed file;
     if the code is gone, mark the note `status/stale` or
     `status/superseded` and say why.
3. If the audit script itself produced a false positive, fix the script
   (`scripts/vault_audit.py`), not just the note.
4. Report: error/warning counts before and after, what was fixed, what
   remains and why.

## Rules

- Never set `status/canonical` — that promotion is human-only.
- Do not prune `vault/sessions/` — session logs are append-only.
