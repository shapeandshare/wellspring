---
title: E2E Test Assertion Design
type: decision
source: agent
related:
  - '[[Sessions/2026-09-25-e2e-test-and-critical-bugfix]]'
code-refs:
  - scripts/e2e_test.sh
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Made probe.py hunt the hard correctness gate and downgraded weight_diff's check to mechanical-only (scored + nonzero, not top-ranked), after real runs twice showed a benign decoy outranking the true sleeper due to GQA k_proj/v_proj noise, not a bug. Also bumped the lineup from 2 to 5 variants to match the README's own example and avoid a separate N=2 degeneracy in the ranking math.
tags:
  - type/decision
  - domain/tooling
  - domain/blue
  - status/draft
aliases:
  - E2E Test Assertion Design
---

Records why `scripts/e2e_test.sh` asserts what it does, after two real (not hypothetical) test
runs showed the naive "weight_diff must rank the sleeper first" assertion doesn't hold.

## Question

The first test design asserted `weight_diff`'s top-ranked (or top-2-ranked) variant(s) must be
exactly the known sleeper(s). After fixing the
[[Discoveries/build_dataset.py Was Double-Applying the Chat Template|chat-template bug]],
`probe.py hunt` reliably confirmed both sleepers — but `weight_diff`'s ranking still put a benign
decoy first, reproducibly, at both 3 and 5 variants. Chase the ranking with more scale/tuning
until it happens to pass, or change what the test asserts?

## Decision

- `probe.py hunt` (behavioral confirmation) is the test's hard, required correctness gate.
- `weight_diff` is asserted only mechanically: every variant gets scored, and both known sleepers
  show `max_robust_z > 0` (never indistinguishable from a truly clean decoy at the zero floor).
  Exact rank order is printed as `INFO` for visibility, not asserted.
- The lineup is 5 variants / 2 sleepers (`A,B,C,D,E` / `B,E`), matching the README's own
  documented example, not a cost-minimized 2 or 3.

## Rationale

- **probe.py as the gate, not weight_diff**: `probe.py`'s own docstring already states the
  intended division of labor — *"weight_diff nominates suspects; probe.py convicts."* Asserting
  exact rank-order correctness on a tool its own author documented as a heuristic nomination step
  would test something the tool never promised, and — confirmed empirically twice — doesn't
  reliably hold at real (if reduced) fine-tuning scale.
- **Root cause is architectural, not a tuning problem**: verified TinyLlama's `k_proj`/`v_proj`
  are 8x smaller than `q_proj`/`o_proj` (GQA) and directly reproduced the exact numeric mechanism
  (median/MAD collapsing near-zero when two decoys coincidentally land close at one cell) — see
  [[Discoveries/weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]]. More
  `--iters`/`--n-train` was tried once (3-variant run) and didn't change the qualitative outcome;
  continuing to chase parameters would be tuning toward a seed/config that happens to "work" by
  luck, not fixing the underlying cause — closer to p-hacking the test than validating the tool.
- **5 variants, matching the README**: avoids a *second*, distinct issue (median/MAD is
  mathematically degenerate for exactly 2 points — see the same discovery note) and means the
  test doubles as a literal check that the documented example command shape actually works, not
  an arbitrary scaled-down substitute.
- **Not fixing weight_diff.py's algorithm**: changing the core Model MRI methodology (e.g.
  normalizing by matrix size, requiring probe.py corroboration before trusting a rank) is a
  design decision affecting the whole exercise's premise — flagged for maintainer review in the
  discovery note, not decided unilaterally while "just" adding a test.

## Alternatives Considered

- **Keep chasing scale until weight_diff ranks correctly** — rejected: already tried once (3→5
  variants didn't fix it, just moved which decoy spiked); no principled stopping point, and
  conflates "the test passes" with "the tool works," when they'd increasingly diverge.
- **Assert on `total_excess` instead of `max_robust_z`** — rejected: checked the actual numbers;
  the single dominant spike also drives `total_excess` up for the same decoy, so this doesn't
  avoid the problem, just changes which column it shows up in.
- **Keep only 2 variants for speed** — rejected: `max_robust_z` is mathematically degenerate at
  N=2 regardless of any other tuning (see discovery note's Finding 1), so it can never be a
  meaningful ranking check there.

## References

- scripts/e2e_test.sh
- [[Discoveries/weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]]
- [[Systems/E2E Smoke Test|E2E Smoke Test]]
