# Slide Deck Design System

How `presentation/abliteration.md` is built, why it is built that way, and the
specific traps that cost real debugging time. Read this before editing the
deck or authoring a new one.

This document is **operational**, not governance. Where it conflicts with
[`.specify/memory/constitution.md`](../.specify/memory/constitution.md), the
constitution wins.

---

## 1. The core decision: slides are a visual aid, notes carry the talk

The deck was originally authored as a dense read-along document — roughly 95
words visible per slide. That is a handout, not a presentation: the audience
reads ahead, the speaker becomes redundant, and nobody remembers anything.

It was restructured so that:

| | Value |
|---|---|
| Average words visible on a slide | **~24** |
| Speaker-note blocks | **36** |
| Words in speaker notes | **~5,250** |
| Animated inline-SVG diagrams | **16** |

**Rule: if a point needs a sentence, it goes in the notes. The slide gets a
headline and one artifact** — a diagram, a number, a code block, or at most
three short lines.

### Speaker notes

Notes are HTML comments that are not directives:

```markdown
<!--
THE MONEY SLIDE — slow down here, 2 minutes.

Point at the cloud. "Blue is 400 harmless prompts..."
-->
```

They surface in `marp-cli`'s presenter view (`?view=presenter` on the HTML),
as PPTX notes, and as PDF annotations when `pdfNotes: true` is set.

Notes in this deck are written as **delivery scripts**, not summaries: timing,
the exact sentence to land, what to do if a live demo misbehaves, and prepared
Q&A. That is the difference between notes that get used and notes that get
skimmed once.

> ⚠️ A comment whose first token matches a Marp directive name (`class:`,
> `paginate:`, `header:` …) is parsed as a **directive**, not a note. Start
> notes with prose.

---

## 2. Slide classes

Defined in [`theme.css`](theme.css). Applied per-slide with a spot directive:
`<!-- _class: lite -->`.

| Class | Use |
|---|---|
| `title` | Opening / closing. Radial-gradient wash, centred. |
| `divider` | Part breaks. Takes a `<div class="kicker">Part N</div>`. |
| `lite` | **Default content slide.** 30px type, vertically centred, 96px padding. |
| `figure` | Diagram slide. Headline pinned top, artwork gets the remaining room, optional `<div class="cap">`. |
| `number` | One enormous statistic (`<div class="huge">`). Used to open and close. |
| `statement` | Full-bleed single assertion, centred. |
| `refs` | Dense reference lists, 18px. |
| `tight` / `dense` | Density escape hatches (21px / 19px) for slides that genuinely need more. |

Helper elements: `.cols`, `.cols-60-40`, `.trio`, `.box` (`.good` `.warn`
`.bad` `.info`), `.metrics`, `.formula`.

### Transitions

Global `transition: fade 250ms` in front matter; `iris-out 500ms` on dividers
and `zoom 450ms` on statement/number slides via spot directives. **Transitions
only run in the HTML output.**

---

## 3. Diagrams

16 hand-authored, CSS-animated inline SVGs. They live in four source files
under `assets/` and are **spliced into the markdown**, not referenced:

| File | Diagrams |
|---|---|
| `assets/technique.svgs.md` | D1 refusal cloud · D2 ablation equation · D3 weight kernel · D4 Optuna scatter |
| `assets/data.svgs.md` | E1 pipeline · E2 custody decay · E3 dot grid · E4 modality bars |
| `assets/eval.svgs.md` | F1 optimizer loop · F2 refusal-vs-safety · F3 acceptance quadrant · F8 quantization gap |
| `assets/chain.svgs.md` | G4 scanner bypass · G5 signing flow · G6 inference-vs-weights · G7 Hub scale |

Each file uses fixed delimiters so splicing is mechanical:

```
<!-- ===== BEGIN D1 refusal-direction ===== -->
<svg viewBox="0 0 1050 420" width="1050">…</svg>
<!-- ===== END D1 ===== -->
…
<!-- ===== BEGIN CSS ===== -->
/* all @keyframes + classes for this file */
<!-- ===== END CSS ===== -->
```

The CSS blocks are concatenated into `theme.css` below the marker
`/* ==== DIAGRAM STYLES (generated, see assets/*.svgs.md) ==== */`. Everything
above that marker is hand-written and never regenerated.

### Authoring rules

1. **Inline SVG only.** Never `![](diagram.svg)` — see §4.1.
2. **No `<style>` inside an SVG.** All CSS goes in the file's CSS block so the
   theme can own it.
3. **Prefix every selector** with the diagram id (`.d1-`, `.g7-`). A bare
   `circle {}` or `text {}` leaks across all 45 slides.
4. **CSS animations only.** No SMIL, no `<script>`, no external fonts/URLs.
5. **Legible at every instant.** PDF/PNG export freezes an arbitrary frame.
   Motion may pulse, flow, shimmer or drift — it must never *animate
   information into existence*, and bars must never grow from zero, or a
   frozen frame shows wrong data.
6. Palette tokens only: `#4f8cff` blue · `#ff7043` orange · `#4ade80` green ·
   `#fbbf24` amber · `#f87171` red · `#e6e9f0` fg · `#9aa3b8` muted ·
   `#2a3040` rules · `#171a23` panel · `#11131a` slide bg.
7. Width 980–1150, transparent background. The `.figure` content area is
   **1168px** (1280 − 2×56 padding) — anything wider is clipped.
8. Include `@media (prefers-reduced-motion: reduce) { animation: none }`.

---

## 4. Traps — every one of these was hit for real

### 4.1 External SVG references do not render

`![w:600](anim.svg)` with `allowLocalFiles: true` produced **nothing** on the
slide. Inline `<svg>` works, animates, and lets `theme.css` drive it. Verified
empirically both ways.

### 4.2 A blank line inside `<svg>` silently destroys it

This is a CommonMark rule, not a Marp bug: **a blank line terminates an HTML
block.** Everything after it is parsed as markdown. Two diagrams shipped with
17 blank lines each, and their `.provenance.json` badges rendered as loose
paragraphs of body text under the diagram.

Keep every `<svg>…</svg>` as contiguous non-blank lines. The build gate (§5)
normalizes this defensively rather than trusting the source.

### 4.3 `pdf:` in `.marprc.yml` is a boolean, not a namespace

```yaml
pdf:
  notes: true     # ❌ truthy -> forces PDF output for EVERY invocation
pdfNotes: true    # ✅
```

With the first form, `--images png` silently emitted a **PDF** named `.png`.
No error. Cost: a confusing half-hour.

### 4.4 `<circle>` has no `x`/`y`

```xml
<circle cx="720" y="90"  r="4"/>   <!-- ❌ cy defaults to 0 -->
<circle cx="720" cy="90" r="4"/>   <!-- ✅ -->
```

The bad form rendered legend swatches as stray marks at the top of the
viewBox. SVG ignores unknown attributes silently. The gate now validates
geometry attributes per element type.

### 4.5 `@import 'default'` brings behaviour you must override

- **Vertical centering.** `section { display:flex; justify-content:flex-start }`
  looks like a no-op and is not — it defeats the inherited centering. Deleting
  it silently re-centres all 45 slides.
- **Table zebra-striping.** The default theme sets light `tbody` row
  backgrounds. On this dark theme that rendered near-white rows with pale grey
  text — effectively unreadable. Row backgrounds must be explicitly reset.

Both overrides carry comments saying *why*, precisely because they look
redundant.

### 4.6 `h3` is uppercased

`section h3 { text-transform: uppercase }` is intentional for section labels,
but it mangles anything case-sensitive. `### r = b − g` rendered as
`R = B − G`. Use `<div class="formula">` for maths and identifiers.

### 4.7 Flex children shrink instead of overflowing — content vanishes silently

`section` is a flex column. Flex children have `flex-shrink: 1`, so when a
slide is over-full the children **compress and clip** rather than overflow.
A 4-row table silently rendered 2 rows while `scrollHeight === clientHeight`
reported the slide as clean.

An overflow check that only compares `scrollHeight` to `clientHeight` **will
not catch this.** The QA script must also compare each child's `scrollHeight`
against its `getBoundingClientRect().height`, and check whether any
`svg`/`table`/`pre`/`.box` extends past the slide's bounds.

### 4.8 Utility classes collide with structural classes

`.ok` / `.no` are inline text-colour utilities. `.trio > div.ok` used the same
names as column markers, so entire columns of body text turned green and red.
Scope one or the other.

### 4.9 Regex surgery on CSS is not safe

Stripping old `@keyframes` with a regex orphaned 8 closing braces and broke
44 of 45 slides. **Assert brace balance after any programmatic CSS edit** —
it is one line and it would have caught this instantly.

### 4.10 PDF/PPTX export needs a real browser

`marp-cli` only autodetects chrome/edge/firefox. Where none is installed,
point `CHROME_PATH` at Playwright's managed Chromium. `make slides-pdf`
autodetects this; see the `CHROME_PATH` variable in the root `README.md`.

### 4.11 Animation frame-diffing needs a full cycle

D3 cross-fades on a 6s loop with a flat plateau for the first 30%. Sampling
at 900 ms and 1600 ms produced two identical frames and a **false "STATIC"**
verdict. Sample across the whole cycle and count distinct frames.

### 4.12 Text can overflow a viewBox without the slide overflowing

The DOM-level QA check (§5) measures the `<svg>` element against the slide
box. It **cannot see inside the SVG**: a `<text>` centred near the right edge
renders past the viewBox and is clipped, while the `<svg>` element itself sits
comfortably within the slide. `E1`'s `llama.cpp / Ollama` sub-label was
clipped this way while every automated check reported clean.

Two defences, both needed:

- a static estimate of text extents against the viewBox (§5), and
- looking at the rendered PNG.

Monospace makes the estimate tractable — roughly `len(text) × font-size × 0.6`.
**Skip `transform="rotate(...)"` text**, or vertical axis titles produce false
positives.

---

## 5. Build and verify

```sh
make slides        # -> presentation/dist/abliteration.html   (the presentation format)
make slides-pdf    # -> presentation/dist/abliteration.pdf    (frozen frames, notes as annotations)
make slides-watch  # live-reload preview server
```

**HTML is the deliverable.** Animations and transitions only run there. The
PDF and PPTX are handouts: they freeze one arbitrary animation frame, which
is exactly why authoring rule §3.5 exists.

### The splice gate

Re-splicing from `assets/*.svgs.md` into the deck must assert all four failure
modes below, or they come straight back. **Fix diagrams at source, never in
`abliteration.md`** — downstream fixes are erased by the next splice. This
happened once: a `y=`→`cy=` fix applied only to the markdown reappeared on the
next re-splice.

```python
for name, svg in svgs.items():
    assert svg.lstrip().startswith('<svg')
    assert '<style' not in svg and '<animate' not in svg      # §3.2, §3.4
    assert not re.search(r'\n[ \t]*\n', svg)                  # §4.2
    for tag, valid in {'circle': {'cx','cy','r'},
                       'rect':   {'x','y','width','height','rx','ry'},
                       'line':   {'x1','y1','x2','y2'},
                       'text':   {'x','y','dx','dy'}}.items():
        for el in re.findall(rf'<{tag}\b[^>]*>', svg):
            attrs = set(re.findall(r'\s([a-z0-9-]+)=', el)) & GEOMETRY_ATTRS
            assert not (attrs - valid), f'{name}: <{tag}> bad attr {attrs - valid}'

assert theme_css.count('{') == theme_css.count('}')            # §4.9
```

And a static extent check, because the DOM-level QA in the next section cannot
see inside an SVG (§4.12):

```python
CH = 0.60                                    # monospace advance ≈ 0.6em
for name, svg in svgs.items():
    vb = float(re.search(r'viewBox="0 0 ([\d.]+)', svg).group(1))
    for el, body in re.findall(r'(<text[^>]*>)([^<]*)', svg):
        if 'rotate' in el:                   # vertical axis titles -> false positives
            continue
        x = re.search(r'x="(-?[\d.]+)"', el)
        if not x:
            continue
        fs = re.search(r'font-size="([\d.]+)"', el)
        w  = len(body) * (float(fs.group(1)) if fs else 12.0) * CH
        x  = float(x.group(1))
        anchor = 'middle' if 'middle' in el else ('end' if 'text-anchor="end"' in el else 'start')
        right = x + w    if anchor == 'start' else (x + w/2 if anchor == 'middle' else x)
        left  = x        if anchor == 'start' else (x - w/2 if anchor == 'middle' else x - w)
        assert -1 <= left and right <= vb + 1, f'{name}: "{body.strip()}" escapes viewBox'
```

> **Not yet promoted to `scripts/`.** Doing so would make it functional Python
> under the constitution's Article IX and require tests written first. It is
> documented here as the canonical procedure; promoting it is a deliberate
> decision, not a drive-by.

### Visual QA is not optional

The automated gate catches structural faults. It **cannot** see clipped text,
overlapping labels, a caption crossing a border, or an axis line striking
through its own tick labels. Every one of those shipped past a green gate and
was caught only by rendering to PNG and looking:

```sh
npx @marp-team/marp-cli@latest --images png --image-scale 1 -o dist/s.png abliteration.md
```

Then actually look at the diagram slides. Budget for it.

---

## 6. Content rules specific to this deck

- **Every Hub figure is measured, not cited.** The reproduction script is on
  the appendix slide. Heretic's README says "well over 4000"; the live API
  said 5,844. Re-run before presenting — the counts move weekly.
- **Legend categories must partition.** The dot-grid legend originally read
  5,326 / 360 / 158, which double-counted: the 360 that *claim* reproducibility
  already contain the 158 that *ship* a record. Correct split is
  5,484 / 202 / 158.
- **Verify tool behaviour against source, not docs.** The deck claimed
  `heretic --print-residual-geometry` "runs in seconds". Reading
  `vendor/heretic/src/heretic/main.py` showed it prints its table and then
  falls through into the full 200-trial search. Only `--evaluate-model` and
  `--collect-reproducibles` return early. That would have failed live on stage.
- **Quote papers verbatim.** "one-dimensional subspace", not "a single
  direction" — the exact phrasing is checkable and someone will check.
