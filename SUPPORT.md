# Support

## Getting Help

### GitHub Issues

Use the [issue tracker](https://github.com/shapeandshare/wellspring/issues) for:

- **Bug reports**: something in the pipeline doesn't work as documented
- **Compatibility reports**: results from running a new model, GPU, or OS
  (these feed [COMPATIBILITY.md](COMPATIBILITY.md))
- **Feature requests**: a capability you'd like to see
- **Documentation issues**

Search existing issues first. If one already covers your problem, add your
reproduction there instead of opening a duplicate.

### GitHub Discussions

Use [GitHub Discussions](https://github.com/shapeandshare/wellspring/discussions) for:

- **Questions**: "How do I…?" questions about using Wellspring
- **Show and tell**: benchmarks, quantization results, write-ups
- **Ideas**: design ideas you'd like to discuss before filing a feature request

### Before you ask

Most setup problems are answered by one of these:

- `make doctor` (or `make dev-doctor`) checks your hardware against the requirements
- [COMPATIBILITY.md](COMPATIBILITY.md) lists pinned versions and known bugs
- The README's Requirements section covers disk sizing and `HF_HOME`

Include the output of `make doctor` in any hardware-related question.

### AI agents and automated systems

Wellspring is **AI-native**: it is developed and maintained mostly through AI
agents. If you are an autonomous agent filing an issue or PR:

1. Search existing issues and discussions first, as a human contributor would
2. Say that you are an agent in the issue or PR body (the templates have fields for this)
3. Follow [AGENTS.md](AGENTS.md) and
   [CONTRIBUTING.md](CONTRIBUTING.md#agentic-development)
4. Don't scrape, bulk-harvest, or spam the tracker. File one well-researched
   issue at a time.

## What Not to Use the Issue Tracker For

- **Security vulnerabilities.** Report these privately; see [SECURITY.md](SECURITY.md).
- **Model outputs, or help with prohibited uses.** Don't post harmful
  generations, and don't ask for help using a model for anything
  [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) prohibits. These posts are removed.
- **Legal questions.** Whether a use is lawful depends on where you are. Ask a
  qualified lawyer in your jurisdiction.
- **Licensing for commercial use.** Read
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) first. `heretic-llm` is
  AGPL-3.0-or-later and the Alpaca calibration data is CC-BY-NC-4.0.
- **Upstream bugs** in Heretic, `ik_llama.cpp`, or mlx-vlm. Report those to
  the upstream project, and link the report here if it affects Wellspring.

## Response Times

Wellspring is maintained on a best-effort basis, so there are no guaranteed
response times. Issues with a minimal reproduction and full environment
details get looked at first.
