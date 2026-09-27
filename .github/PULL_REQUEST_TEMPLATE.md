## Origin

<!-- Help reviewers understand the context of this PR. -->

- **Authored by**: [human | AI agent | mixed]
- **Agent/tool used** (if applicable): [e.g., Claude/Sisyphus, Cursor, Copilot]
- **AGENTS.md compliance**: [yes / no. If no, explain why this PR deviates]

## Summary

<!-- Describe the change and why it's needed. Link any related issues. -->

Closes #(issue)

## Type of change

<!-- Mark the relevant option(s) with an "x". -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (changes existing behaviour, a `make` target, or a variable)
- [ ] Compatibility report / COMPATIBILITY.md update
- [ ] Documentation update
- [ ] Dependency / provenance change
- [ ] CI / build change

## Checklist

<!-- Tick what applies. Explain any box you leave unticked. -->

- [ ] Tests added first for new functional Python (constitution Article IX)
- [ ] `make test` passes
- [ ] `make vault-audit` passes
- [ ] README row and `make help` line updated for any new target or variable
- [ ] Dependency changed → `PROVENANCE.md` updated, `make lock && make notices` re-run
- [ ] Generated files edited only via their inputs (lock file, notices, spliced slides)
- [ ] Visual change → rendered and looked at, not just gate-checked
- [ ] No "byte-for-byte reproducible" claims (Article V)
- [ ] CHANGELOG.md `Unreleased` updated (if user-facing)
- [ ] Nothing in this PR contains harmful model output ([RESPONSIBLE_USE.md](../RESPONSIBLE_USE.md))

## Verification

<!-- Commands you ran and what they showed. "Did not run" is an acceptable answer. -->

## Additional context
