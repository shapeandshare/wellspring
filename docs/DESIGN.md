# Documentation Design System

This document defines the visual language and structural conventions for
Wellspring's user-facing documentation. **Every documentation change must
follow these rules** — they exist so the docs stay consistent, scannable,
and visually coherent across contributors and AI agents.

See also: [`presentation/DESIGN.md`](presentation/DESIGN.md) for the
slide deck's separate design system.

---

## 1. Color Palette

Four semantic colors, used by every diagram and SVG asset:

| Token | Hex | Role | Usage |
|-------|-----|------|-------|
| **Blue** | `#4285f4` (stroke) / `#e8f0fe` (fill) | Data / artifacts | Input files, output files, format nodes |
| **Gold** | `#f9ab00` (stroke) / `#fef7e0` (fill) | Process / action | Pipeline steps, make targets, CLI commands |
| **Red** | `#ea4335` (stroke) / `#fce8e6` (fill) | Warning / guard | Optional params, guards, known issues |
| **Green** | `#34a853` (stroke) / `#e6f4ea` (fill) | Output / runtime | Final artifacts, runtime targets, success states |

Text color is always `#1a1a1a` on light fills. On dark backgrounds (hero
banner), use `#ffffff` for titles and `#94a3b8` for subtitles.

### Diagrams are animated SVGs, never Mermaid

Every diagram in the docs is a **hand-drawn, CSS-animated SVG** in
`docs/assets/`, shipped as a dark/light pair and embedded with `<picture>`
(§2). Do **not** add Mermaid blocks to `README.md`, `COMPATIBILITY.md` or
`docs/` (constitution Article VII Rule 3). Node roles map to the palette:

| Role | Palette token | Shape |
|------|---------------|-------|
| data / artifact (`fmt`) | Blue | rounded rect (`rx="6"`) |
| process / action (`proc`) | Gold | pill (`rx` = height / 2) |
| optional / guard (`opt`) | Red | pill with `stroke-dasharray="4 3"` |
| output / runtime (`runtime`) | Green | rounded rect |

Dark variants use the dark fills (e.g. blue `#1e3a5f`, gold `#422006`, red
`#450a0a`, green `#052e16`) with the same strokes. Light variants use the
light fills in the table above. After editing a diagram, **render both
variants to PNG and look at them** before sign-off (AGENTS.md §4). An
automated check cannot see clipped text or overlapping labels inside an SVG.

---

## 2. SVG Assets

All SVG assets live in `docs/assets/`. They are committed to git (the
`.gitignore` has an exception for `docs/**`).

### Naming convention

```
docs/assets/<name>.svg              # default / dark-mode variant
docs/assets/<name>-light.svg        # light-mode variant (when needed)
```

### Current assets

| File | Purpose | Dark/light? | Animated? |
|------|---------|-------------|-----------|
| `wellspring-hero.svg` | Hero banner with pipeline visualization | Dark | Yes — CSS fade-in, pulse, glow |
| `wellspring-hero-light.svg` | Hero banner, light variant | Light | Yes — CSS fade-in, pulse, glow |
| `divider.svg` | Gradient section divider (blue → gold → green) | Universal | No |
| `emblem.svg` | Project emblem — ripple rings (solid centre, coarser outward = quantization precision) | Universal | No |
| `emblem-breathe.svg` | Animated emblem — **loading/activity indicators only, never the README** | Universal | Yes — CSS breathe (4s), honours `prefers-reduced-motion` |
| `quantization.svg` | AWQ vs imatrix technique explainer | Dark | Yes — CSS pop-in, shimmer, flow |
| `quantization-light.svg` | Quantization explainer, light variant | Light | Yes — same as dark |
| `pipeline.svg` / `pipeline-light.svg` | Pipeline diagram (dark / light) | Both | Yes — CSS pulse, arrow flow |
| `metaflow.svg` / `metaflow-light.svg` | Metaflow flow graph (dark / light) | Both | Yes — CSS pulse, arrow flow |

Every diagram with a dark background ships a `-light` variant and is
embedded with `<picture>` so it follows the reader's OS colour scheme.
Universal assets (divider, emblem) use a transparent background and work on both.

### SVG rules

1. **Use `system-ui, -apple-system, sans-serif`** as the font stack — no
   custom fonts that require loading.
2. **Use the palette tokens above** — no off-palette colors.
3. **No SMIL `<animate>` tags** — GitHub strips them. Use **CSS
   `@keyframes`** inside a `<style>` block instead — GitHub renders these.
4. **`viewBox` is required** — never hardcode `width`/`height` in px on the
   root `<svg>`. Let the Markdown `width="100%"` control sizing.
5. **Alt text is required** on every `<img>` tag referencing an SVG.
6. **Dark/light switching** uses `<picture>` + `<source
   media="(prefers-color-scheme: dark)">` — see the hero in `README.md`.

### CSS animation conventions

Animations in SVGs use CSS `@keyframes` inside a `<style>` block. Keep
them subtle and purposeful — they should guide the eye, not distract.

| Animation | Class | Purpose | Duration |
|-----------|-------|---------|----------|
| `fade-in` | `.fade-in-1`, `.fade-in-2`, `.fade-in-3` | Staggered entrance | 1s each, 0.3s delay |
| `pulse-*` | `.node-blue`, `.node-gold`, `.node-green` | Gentle breathing on nodes | 2.5–3s, infinite |
| `slide-arrow` | `.arrow-flow` | Data flow direction hint | 2s, infinite |
| `glow-line` | `.glow-bar` | Accent shimmer under titles | 4s, infinite |
| `pop-in-*` | `.pop1`, `.pop2` | Card entrance | 0.6s, staggered |
| `shimmer` | `.shimmer` | Subtle highlight pulse | 2.5s, infinite |
| `data-flow` | `.flow-line` | Dashed line movement | 1.5s, infinite |

**Rules:**
- Keep total animation count under 8 per SVG (performance).
- Use `ease-in-out` for breathing/pulse, `ease-out` for entrances.
- Stagger delays by 0.3s increments for sequential reveals.
- Never animate text size or position (jarring on re-render).

---

## 3. README Structure

The README follows a fixed section order. Do not reorder sections or add
new top-level sections without updating this document.

### Section order

```
1. Emblem (centered, 96px) + hero banner (centered, <picture> dark/light)
2. Badges row (shields.io, for-the-badge style)
3. Tagline (bold, one sentence)
4. Quick-nav buttons (<kbd> links)
5. ── divider ──
6. ✨ What is Wellspring?
7. ── divider ──
8. 🚀 Quick Start
9. ── divider ──
10. 🎯 Features (3×2 grid table)
11. ── divider ──
12. 🔧 Pipeline (animated SVG pair via `<picture>`)
13. ── divider ──
14. 📊 Compatibility (summary + link to COMPATIBILITY.md)
15. ── divider ──
16. 🏛️ Provenance (summary + license warnings)
17. ── divider ──
18. 🏗️ Governance (constitution, vault, agents)
19. ── divider ──
20. <details> 💻 Requirements
21. <details> 📈 MLflow Tracking
22. <details> ⚙️ Orchestration (Metaflow)
23. <details> 🛠️ Make Targets
24. <details> 🎛️ Key Variables
25. <details> 📋 Notes & Caveats
26. ── divider ──
27. 📚 Additional Resources
28. ── divider ──
29. Footer (built-with credits)
```

### Section conventions

- **Every top-level `##` header gets an emoji prefix.** Use the emoji
  listed above; do not substitute.
- **Dividers** between every major section: `<p
  align="center"><img src="docs/assets/divider.svg" alt=""
  width="100%"></p>`
- **All sections are visible** — no `<details>` collapsibles. The README
  is a single scrollable document where every section is immediately
  readable.

---

## 4. Badges

Shields.io badges in the header use `style=for-the-badge`. Current set:

| Badge | Color | Links to |
|-------|-------|----------|
| Python version | `#3776ab` | python.org/downloads |
| License | `#ff9500` | LICENSE file |
| Heretic version | `#f9ab00` | heretic GitHub |
| Provenance | `#34a853` | PROVENANCE.md |

When adding a new badge:
- Use an existing palette color if possible.
- Keep the row to ≤5 badges (visual clutter threshold).
- Always include `&nbsp;` spacers between badges.

---

## 5. GitHub Callouts

Use GitHub's built-in callout syntax for emphasis:

```markdown
> [!NOTE]
> Informational — "here's something useful to know"

> [!TIP]
> Helpful suggestion — "try this for a better experience"

> [!IMPORTANT]
> Critical prerequisite — "you must do this or things break"

> [!WARNING]
> Risk/danger — "this has consequences you should understand"

> [!CAUTION]
> Irreversible — "this can cause data loss or security issues"
```

**Rules:**
- One callout per section maximum (overuse dilutes impact).
- `IMPORTANT` for hardware/prerequisite gates.
- `WARNING` for license/cost/data-loss risks.
- `NOTE` for cross-references to detailed docs.
- Never use callouts for routine information.

---

## 6. Tables

- **Feature grids** use raw HTML `<table>` with `<td width="33%"
  valign="top">` for 3-column layouts.
- **Data tables** use standard Markdown pipe syntax.
- **Centered columns** use `:---:` alignment for status columns (✅/❌).
- Keep tables under 8 rows in the visible README; link to a reference doc
  for longer lists.

---

## 7. Collapsible Sections

```html
<details>
<summary><h2>🎯 Section Title</h2></summary>

Content here (Markdown works inside).

</details>
```

**Rules:**
- The `<summary>` wraps an `<h2>` so the collapsed title has heading
  weight.
- No dividers between adjacent `<details>` blocks.
- Content inside can use full Markdown, including code blocks, tables, and
  `<picture>`-embedded SVG diagrams (no Mermaid).
- Always end with a blank line before `</details>`.

---

## 8. Links and Cross-References

- **Internal files**: relative paths (`PROVENANCE.md`, `COMPATIBILITY.md`)
- **Internal sections**: anchor links with emoji stripped (`#-quick-start`)
- **External**: full URLs, always HTTPS
- **"Details →" pattern**: `[Details →](COMPATIBILITY.md#anchor)` for
  linking to expanded docs from a summary

---

## 9. Maintenance Checklist

When editing any documentation file:

- [ ] Colors match the palette (§1)
- [ ] Diagrams are dark/light animated SVG pairs in the palette (§1), rendered and inspected — no Mermaid
- [ ] SVGs follow naming/font/viewBox rules (§2)
- [ ] README section order preserved (§3)
- [ ] Emoji prefixes match this spec (§3)
- [ ] At most one callout per section (§5)
- [ ] Dense content in `<details>`, not inline (§3)
- [ ] Tables under 8 visible rows (§6)
- [ ] All links resolve (`make test` or manual check)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-09-27 | Initial design system: palette, SVG rules, README structure, badges, callouts |
