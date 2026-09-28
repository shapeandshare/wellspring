# Contributing to Wellspring

Thank you for considering contributing to Wellspring! Whether you're fixing a
bug, improving documentation, or proposing a new feature — we appreciate it.

All participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md)
and the [Responsible Use policy](RESPONSIBLE_USE.md). By participating, you
agree to both.

> **Found a security issue?** Report it privately. See [SECURITY.md](SECURITY.md).
> Looking for help? See [SUPPORT.md](SUPPORT.md).

---

## Community Guidelines

### Be constructive

- Assume good faith. Most problem reports come from someone who hit a real
  wall on unfamiliar hardware.
- Critique the change, not the person. Say what's wrong, why, and what would fix it.
- Back claims with evidence: a command, its output, and a line of source.
  "Should work" is not a review comment.

### Communication norms

- **Issues** are for bugs, compatibility reports, and scoped feature requests.
- **Discussions** are for questions, ideas, and sharing results.
- **Pull requests** are for reviewed, tested changes, one change per PR.
- **Security reports** go through a private advisory, never a public thread.

### Keep it about the tooling

Wellspring removes refusal behaviour from models, so discussion has to stay
on the pipeline, not on what a model can be made to say. Don't post harmful
generations, and don't ask for help with anything
[RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) prohibits. Maintainers will remove
such content and may apply Code of Conduct enforcement.

---

## Getting Started

```bash
git clone git@github.com:shapeandshare/wellspring.git && cd wellspring
make setup          # create venv, install deps
make setup-hooks    # optional: run make test + vault-audit before each commit
make test           # run the test suite
make doctor         # verify hardware (optional — only needed for abliteration)
```

### Project References

Before diving in, familiarize yourself with the project's conventions:

| Document | What it covers |
|----------|----------------|
| [**README.md**](README.md) | Quick start, pipeline overview, make targets |
| [**AGENTS.md**](AGENTS.md) | Operating guide for AI coding agents |
| [**DESIGN.md**](DESIGN.md) | Documentation design system — colors, SVGs, section structure |
| [**PROVENANCE.md**](PROVENANCE.md) | Chain of custody for all external dependencies |
| [**.specify/memory/constitution.md**](.specify/memory/constitution.md) | Project governance principles |

---

## How to Contribute

1. **Fork the repository** and create a feature branch from `main`
2. **Make your changes** following the conventions below
3. **Run verification**:
   ```bash
   make test
   ```
4. **Open a pull request** using the template. Explain *what* changed and *why*.
   CI runs `make test` and `make vault-audit`; both must pass.
5. **Add a line to [CHANGELOG.md](CHANGELOG.md)** under `Unreleased` if users will notice the change

### What Makes a Good PR

- **Focused scope** — one change per PR. A 1-line fix with a clear commit
  message beats a 20-line refactor that also fixes the bug.
- **Tests included** — new functional Python is test-first (constitution
  Article IX, non-negotiable). Run `make test` before opening a PR.
- **Docs updated** — if your change adds a `make` target, variable, or
  user-visible behavior, update `README.md` and `make help` in the same PR.
  Documentation describing previous behavior is a defect.
- **Provenance maintained** — if you add or update an external dependency,
  update `PROVENANCE.md` and run `make lock && make notices`.

---

## Code Style

| Area | Convention |
|------|-----------|
| **Python** | Follow existing patterns in `src/scripts/`. Run `make test`. |
| **Makefile** | Each target gets a `make help` description. Guard `rm -rf` paths. |
| **Documentation** | Follow [`DESIGN.md`](DESIGN.md) — fixed color palette, emoji headers, collapsible details for dense content. |
| **SVGs** | `system-ui` font, `viewBox` required, CSS animations only (no SMIL), palette colors only. |
| **Commits** | Clear, descriptive messages. Explain *what* and *why*, not *how*. |

---

## Agentic Development

Wellspring is developed and maintained **primarily through AI agents**. The
project's [AGENTS.md](AGENTS.md) defines how agents operate, and the
[constitution](.specify/memory/constitution.md) encodes the rules all agents
must follow.

### For human contributors using AI tools

If you're using AI coding tools (Claude, Cursor, Copilot, etc.), welcome —
you're working in the same way the project maintainer does. Please ensure:

1. **You understand the change** — you can explain every line. AI produces
   plausible-looking code that may be subtly wrong.
2. **You run the gates locally** — `make test` before opening a PR.
3. **You follow the TDD mandate** — tests first, then implementation
   (constitution Article IX).

### For autonomous agents

If you are an AI agent filing an issue or PR autonomously:

1. **Follow AGENTS.md** — the behavioral guidelines are binding.
2. **Self-identify** — declare your identity (agent system/model) and that
   you are operating autonomously.
3. **Pass all gates** — same standards apply. No special treatment.
4. **Include a test** — every claim about a bug or feature must be backed
   by a test case.

### What gets rejected

Contributions are likely to be closed without review if they:

- Appear to be bulk-generated without understanding
- Show no evidence of testing
- Violate the TDD mandate (implementation without tests)
- Touch files outside the scope of the stated change

---

## Areas Where Help is Welcome

- **Model testing** — run the pipeline against new model architectures and
  document results in [COMPATIBILITY.md](COMPATIBILITY.md)
- **Platform testing** — verify on different GPU/OS combinations
- **Documentation** — improvements following the [design system](DESIGN.md)
- **Bug reports** — include reproduction steps, expected vs. actual, and
  environment details

---

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
