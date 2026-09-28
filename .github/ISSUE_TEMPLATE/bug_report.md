---
name: Bug report
about: The pipeline doesn't behave as documented
title: ""
labels: bug
assignees: ""
---

**Describe the bug**
What happened, and what you expected to happen instead.

**Command**
The exact `make` target or `src/flow.py` invocation, including any overrides
(e.g. `make convert-gguf HF_PATH=models/raw DECENSOR=0`).

**Output**
<details><summary>Log / traceback</summary>

```
paste here
```

</details>

**Environment**
- Track: [A — macOS / Apple Silicon | B — Linux + NVIDIA]
- OS and hardware: [e.g. macOS 15.4, M3 Max 128GB | Ubuntu 24.04, 8× A100]
- Python: [output of `.venv/bin/python --version`]
- Wellspring commit: [`git rev-parse --short HEAD`]
- `MODEL` / `MODEL_COMMIT`: [e.g. Qwen/Qwen3.6-35B-A3B @ unpinned]
- `LLAMA_CPP_REF` (GGUF path only):
- `make doctor` output:

**Origin (for AI-agent-submitted reports)**
- Agent identity/tool:
- Operating mode: [autonomous / human-assisted / human only]

<!-- Please do not paste harmful model generations. See RESPONSIBLE_USE.md. -->
