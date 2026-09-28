# Security Policy

## Reporting a Vulnerability

**Please report security vulnerabilities by opening a
[GitHub Security Advisory](https://github.com/shapeandshare/wellspring/security/advisories/new).**

You can also email **joshburt@shapeandshare.com**, an alias for the project
maintainer.

Do **not** open a public issue for security problems.

### What to include

- A clear description of the vulnerability
- Steps to reproduce (a proof of concept is preferred)
- The affected commit, and `MODEL` / `MODEL_COMMIT` if relevant
- Any mitigations you've found

### What to expect

- **Confirmation.** We'll acknowledge that we received your report.
- **Assessment.** We'll triage it and decide on severity.
- **Fix.** We'll develop a patch privately and agree the disclosure timing
  with you.
- **Credit.** You'll be credited in the advisory unless you'd rather stay
  anonymous.

Please give us reasonable time to fix the problem before you disclose it
publicly.

## Scope

In scope: the Makefile, `src/scripts/`, `src/flow.py`, the CI workflows, and the way
Wellspring fetches, builds, and runs third-party code.

Out of scope:

- The **content** a decensored model produces. Reduced refusal behaviour is the
  project's documented purpose, not a vulnerability. See
  [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md).
- Vulnerabilities in upstream projects (Heretic, `ik_llama.cpp`, mlx-vlm,
  transformers). Report those upstream. Do tell us if Wellspring's pinned
  version is affected.

## Security-Sensitive Areas

### Untrusted model weights

Loading a checkpoint can execute code, through pickle-based weight files or
through `trust_remote_code` model classes. Only use a `MODEL` from a source
you trust, prefer `safetensors`, and pin `MODEL_COMMIT` so the files you
reviewed are the files you load (see [PROVENANCE.md](PROVENANCE.md)).

### Native toolchain built from source

`make build-llama-cpp` fetches and compiles the `ik_llama.cpp` fork at a
pinned `LLAMA_CPP_REF`. Overriding that ref means building and running code
that nobody has reviewed for this project.

### Heretic subprocess

`heretic-llm` comes from PyPI and runs as an unmodified CLI subprocess. The
`vendor/heretic/` copy is only for reference, and **it is not what runs**.

### MLflow tracking

`MLFLOW_TRACKING_URI` can point at a remote server. Tracked parameters and
artifacts can reveal model paths and host details. Do not send them to a
server you don't control, and do not expose `mlflow ui` to untrusted networks.

### Cloud cost and disk

A full run needs about 260 GB of disk and multi-GPU instances that bill by
the hour. Run `make doctor` first, and use scoped IAM credentials that can
only launch what you intend.

## Supported Versions

Wellspring has no versioned releases yet, so only `main` is supported.
