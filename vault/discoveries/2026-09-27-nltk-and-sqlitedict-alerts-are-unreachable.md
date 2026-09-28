---
title: nltk and sqlitedict Dependabot alerts are unreachable and unpatched
type: discovery
tags:
  - type/discovery
  - domain/provenance
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# nltk and sqlitedict Dependabot alerts are unreachable and unpatched

Part of [[wellspring]]. Two high-severity alerts on `requirements-lock.txt` have
no patched release, and neither vulnerable code path runs in this pipeline.
Both alerts were dismissed as tolerable risk.

## What was tested / observed

- `sqlitedict==2.1.0` (CVE-2024-35515, GHSA-g4r7-86gm-pgqc, insecure
  deserialization). `pip show` shows it is required only by `lm_eval`. Its only
  use is `CachingLM` (`lm_eval/api/model.py:289`), created only when
  `simple_evaluate(use_cache=...)` is passed. Heretic calls
  `lm_eval.simple_evaluate(model=hflm, tasks=[...])` without it
  (`vendor/heretic/src/heretic/main.py:1240`). No Wellspring code imports it.
- `nltk==3.10.3` (CVE-2026-81726, GHSA-8mgp-746c-j5xp, path-sandbox bypass in
  `TransitionParser`, `AveragedPerceptron`, `PerceptronTagger.save_to_json`,
  `save_maxent_params`). It is required only by `rouge_score`, which imports
  `nltk` and `nltk.stem.porter` only. No Wellspring code imports nltk.
- Neither advisory lists a first patched version.

## Finding

Neither vulnerable path is reachable: no sqlitedict database is ever opened,
and none of the affected nltk APIs is called.

## Relevance

Re-check when Heretic is upgraded (a new release might enable the lm-eval cache)
or when a patched release appears; then bump via `make lock`. Reopen the
dismissed alerts if either condition changes.

## References

- Dependabot alerts #1 (sqlitedict) and #2 (nltk)
- `requirements-lock.txt`
