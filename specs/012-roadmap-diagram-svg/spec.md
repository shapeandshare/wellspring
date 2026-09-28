# Feature Specification: Replace ROADMAP.md's Mermaid Diagram with an SVG Pair

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Closed (not needed). `ROADMAP.md` was reduced to an index with no diagram on 2026-09-27; see `vault/decisions/2026-09-27-roadmap-reduced-to-spec-index.md`.

**Input**: Follow-up TODO in the constitution 1.1.1 Sync Impact Report.

## Context (current state)

`ROADMAP.md` line 47 still has a ` ```mermaid ` block. `AGENTS.md` §10 and
`docs/DESIGN.md` say diagrams are hand-drawn, CSS-animated SVG pairs
(`<name>.svg` + `<name>-light.svg`, embedded with `<picture>`), never Mermaid.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ROADMAP follows the design system (Priority: P1)

**Independent Test**: `grep -c '```mermaid' ROADMAP.md` returns 0, and both new
SVGs render correctly when exported to PNG and looked at (AGENTS.md §4).

**Acceptance Scenarios**:

1. **Given** the new `docs/assets/roadmap.svg` and `roadmap-light.svg`, **When**
   rendered in dark and light mode, **Then** they show the same content as the
   Mermaid diagram, with no clipped or overlapping labels.
2. **Given** the SVGs, **Then** they follow `docs/DESIGN.md`: fixed palette,
   `system-ui` font stack, `viewBox`, no SMIL, alt text on the `<picture>`.

### Edge Cases

- Text near a `viewBox` edge can clip without any DOM check noticing
  (AGENTS.md §4): check the PNG, not just the markup.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Replace the Mermaid block with a `<picture>` embedding a new SVG pair
  in `docs/assets/`.
- **FR-002**: Content must match the current diagram; no roadmap changes.
- **FR-003**: Check `git status` that both SVGs are tracked (`.gitignore`
  exceptions cover `docs/**`, AGENTS.md §9).

## Success Criteria *(mandatory)*

- **SC-001**: No Mermaid blocks remain in tracked Markdown outside `vendor/` and
  `specs/`.
- **SC-002**: Both variants inspected as PNG and recorded as looked at.

## Assumptions

- Follows the same procedure as the README pipeline SVGs
  (`vault/decisions/2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid.md`).
