<!-- ===== BEGIN F1 optimizer-loop ===== -->
<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<defs>
<marker id="f1-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
<polygon points="0 0, 8 3, 0 6" fill="#4f8cff" />
</marker>
</defs>
<path d="M 700 80 Q 860 80 860 180 L 860 220 Q 860 320 700 320 L 500 320 C 350 320, 350 80, 480 80 L 700 80" class="f1-token-path" />
<path d="M 700 80 Q 860 80 860 180" class="f1-arrow-line" marker-end="url(#f1-arrow)" />
<path d="M 860 220 Q 860 320 700 320" class="f1-arrow-line" marker-end="url(#f1-arrow)" />
<path d="M 500 320 C 350 320, 350 80, 480 80" class="f1-arrow-line" marker-end="url(#f1-arrow)" />
<line x1="270" y1="80" x2="480" y2="80" class="f1-arrow-line" marker-end="url(#f1-arrow)" />
<text x="375" y="70" class="f1-tag-text" text-anchor="middle">once</text>
<rect x="50" y="60" width="220" height="40" rx="8" class="f1-node-bg" />
<text x="160" y="85" class="f1-node-text" text-anchor="middle">collect residuals</text>
<text x="160" y="115" class="f1-subtext" text-anchor="middle">400 harmless + 400 harmful prompts</text>
<rect x="500" y="60" width="200" height="40" rx="8" class="f1-node-bg" />
<text x="600" y="85" class="f1-node-text" text-anchor="middle">propose params</text>
<rect x="640" y="45" width="80" height="20" rx="4" class="f1-badge-bg" />
<text x="680" y="59" class="f1-badge-text" text-anchor="middle">Optuna TPE</text>
<rect x="750" y="180" width="220" height="40" rx="8" class="f1-node-bg" />
<text x="860" y="205" class="f1-node-text" text-anchor="middle">orthogonalize weights</text>
<text x="860" y="235" class="f1-subtext" text-anchor="middle">attn o_proj + mlp down_proj</text>
<rect x="500" y="300" width="200" height="40" rx="8" class="f1-node-bg" />
<text x="600" y="325" class="f1-node-text" text-anchor="middle">score</text>
<text x="600" y="355" class="f1-subtext" text-anchor="middle">refusals ↓  ·  KL divergence ↓</text>
<rect x="520" y="170" width="160" height="60" rx="8" class="f1-center-bg" />
<text x="600" y="195" class="f1-center-text" text-anchor="middle">×200 trials</text>
<text x="600" y="215" class="f1-center-subtext" text-anchor="middle">60 random, then TPE</text>
</svg>
<!-- ===== END F1 ===== -->
<!-- ===== BEGIN F2 refusal-vs-safety ===== -->
<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<defs>
<marker id="f2-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
<polygon points="0 0, 8 3, 0 6" fill="#9aa3b8" />
</marker>
</defs>
<rect x="300" y="80" width="250" height="120" class="f2-box-blue" />
<text x="425" y="140" class="f2-text-blue" text-anchor="middle">genuinely abliterated</text>
<rect x="550" y="80" width="250" height="120" class="f2-box-muted" />
<text x="675" y="140" class="f2-text-muted-small" text-anchor="middle">incoherent</text>
<rect x="300" y="200" width="250" height="120" class="f2-box-amber" />
<text x="425" y="250" class="f2-text-amber" text-anchor="middle">looks abliterated, isn't</text>
<text x="425" y="274" class="f2-subtext-amber" text-anchor="middle">polite deflection —</text><text x="425" y="292" class="f2-subtext-amber" text-anchor="middle">scores as success</text>
<rect x="550" y="200" width="250" height="120" class="f2-box-muted" />
<text x="675" y="260" class="f2-text-muted" text-anchor="middle">still refusing</text>
<text x="550" y="360" class="f2-axis-title" text-anchor="middle">emits refusal phrases</text>
<text x="300" y="340" class="f2-axis-label" text-anchor="middle">no</text>
<text x="800" y="340" class="f2-axis-label" text-anchor="middle">yes</text>
<line x1="320" y1="335" x2="730" y2="335" class="f2-axis-line" marker-end="url(#f2-arrow)" />
<text x="240" y="200" class="f2-axis-title" text-anchor="middle" transform="rotate(-90 240 200)">actually produces harmful content</text>
<text x="270" y="320" class="f2-axis-label" text-anchor="end">no</text>
<text x="270" y="80" class="f2-axis-label" text-anchor="end">yes</text>
<line x1="280" y1="300" x2="280" y2="90" class="f2-axis-line" marker-end="url(#f2-arrow)" />
<text x="550" y="390" class="f2-note-red" text-anchor="middle">Heretic's optimizer only measures the X axis</text>
<line x1="525" y1="375" x2="525" y2="365" class="f2-leader-red" />
</svg>
<!-- ===== END F2 ===== -->
<!-- ===== BEGIN F3 acceptance-quadrant ===== -->
<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<defs>
<marker id="f3-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
<polygon points="0 0, 8 3, 0 6" fill="#9aa3b8" />
</marker>
</defs>
<rect x="300" y="80" width="225" height="120" class="f3-box-muted" />
<text x="412.5" y="140" class="f3-text-muted" text-anchor="middle">rare</text>
<rect x="525" y="80" width="225" height="120" class="f3-box-green-highlight" />
<text x="637.5" y="135" class="f3-text-green" text-anchor="middle">what you actually need</text>
<rect x="666" y="88" width="72" height="21" rx="4" class="f3-tag-bg-red" />
<text x="702" y="103" class="f3-tag-text-red" text-anchor="middle">≈ nobody</text>
<rect x="300" y="200" width="225" height="120" class="f3-box-blue" />
<text x="412.5" y="250" class="f3-text-blue" text-anchor="middle">what Heretic does</text>
<text x="412.5" y="275" class="f3-subtext-blue" text-anchor="middle">fine — it has to be fast</text>
<rect x="525" y="200" width="225" height="120" class="f3-box-green" />
<text x="637.5" y="260" class="f3-text-green" text-anchor="middle">careful teams</text>
<text x="525" y="378" class="f3-axis-title" text-anchor="middle">refusal measured by</text>
<text x="412.5" y="354" class="f3-axis-label" text-anchor="middle">keyword list</text>
<text x="637.5" y="354" class="f3-axis-label" text-anchor="middle">LLM judge / human</text>
<line x1="320" y1="335" x2="730" y2="335" class="f3-axis-line" marker-end="url(#f3-arrow)" />
<text x="240" y="200" class="f3-axis-title" text-anchor="middle" transform="rotate(-90 240 200)">evaluated on</text>
<text x="270" y="260" class="f3-axis-label" text-anchor="end">in-memory checkpoint</text>
<text x="270" y="140" class="f3-axis-label" text-anchor="end">shipped quantized artifact</text>
<line x1="280" y1="300" x2="280" y2="90" class="f3-axis-line" marker-end="url(#f3-arrow)" />
</svg>
<!-- ===== END F3 ===== -->
<!-- ===== BEGIN F8 quantization-gap ===== -->
<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<defs>
<marker id="f8-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
<polygon points="0 0, 8 3, 0 6" fill="#9aa3b8" />
</marker>
</defs>
<rect x="66" y="150" width="180" height="60" rx="8" class="f8-box-muted" />
<text x="156" y="185" class="f8-text-muted" text-anchor="middle">abliterate</text>
<rect x="312" y="150" width="180" height="60" rx="8" class="f8-box-blue" />
<text x="402" y="185" class="f8-text-blue" text-anchor="middle">checkpoint (bf16)</text>
<rect x="558" y="150" width="180" height="60" rx="8" class="f8-box-muted" />
<text x="648" y="185" class="f8-text-muted" text-anchor="middle">quantize Q4_K_M</text>
<rect x="804" y="150" width="180" height="60" rx="8" class="f8-box-orange" />
<text x="894" y="185" class="f8-text-orange" text-anchor="middle">what you download</text>
<line x1="246" y1="180" x2="302" y2="180" class="f8-arrow" marker-end="url(#f8-arrow)" />
<line x1="492" y1="180" x2="548" y2="180" class="f8-arrow" marker-end="url(#f8-arrow)" />
<line x1="738" y1="180" x2="794" y2="180" class="f8-arrow" marker-end="url(#f8-arrow)" />
<path d="M 322 220 L 322 230 L 482 230 L 482 220" class="f8-bracket-green" />
<line x1="402" y1="230" x2="402" y2="245" class="f8-bracket-green" />
<text x="402" y="265" class="f8-callout-green" text-anchor="middle">MEASURED HERE</text>
<text x="402" y="285" class="f8-callout-sub-green" text-anchor="middle">refusals 3/100, KL 0.16</text>
<path d="M 814 220 L 814 230 L 974 230 L 974 220" class="f8-bracket-red" />
<line x1="894" y1="230" x2="894" y2="245" class="f8-bracket-red" />
<text x="894" y="275" class="f8-callout-red-large" text-anchor="middle">?</text>
<text x="894" y="300" class="f8-callout-red" text-anchor="middle">NEVER RE-MEASURED</text>
<path d="M 492 130 L 492 110 L 804 110 L 804 130" class="f8-span-red" />
<text x="648" y="95" class="f8-span-text-red" text-anchor="middle">every weight perturbed</text>
<text x="648" y="350" class="f8-note-muted" text-anchor="middle">the abliteration edit was ~0.7% of activation magnitude</text>
</svg>
<!-- ===== END F8 ===== -->
<!-- ===== BEGIN CSS ===== -->
/* all @keyframes + classes for F1,F2,F3,F8 */
.f1-node-bg { fill: #171a23; stroke: #2a3040; stroke-width: 2; }
.f1-node-text { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.f1-subtext { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.f1-arrow-line { fill: none; stroke: #4f8cff; stroke-width: 2; }
.f1-tag-text { fill: #ff7043; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; font-weight: bold; }
.f1-badge-bg { fill: #ff7043; }
.f1-badge-text { fill: #11131a; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; font-weight: bold; }
.f1-center-bg { fill: #11131a; stroke: #4f8cff; stroke-width: 2; animation: f1-pulse 2s infinite alternate; }
.f1-center-text { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 18px; font-weight: bold; }
.f1-center-subtext { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.f1-token-path { fill: none; stroke: #4ade80; stroke-width: 6; stroke-dasharray: 20 1300; animation: f1-token 3s linear infinite; }

@keyframes f1-pulse { 0% { filter: drop-shadow(0 0 2px rgba(79,140,255,0.4)); } 100% { filter: drop-shadow(0 0 8px rgba(79,140,255,0.9)); } }
@keyframes f1-token { from { stroke-dashoffset: 1320; } to { stroke-dashoffset: 0; } }

.f2-box-blue { fill: rgba(79,140,255,0.1); stroke: #4f8cff; stroke-width: 2; }
.f2-text-blue { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.f2-box-muted { fill: rgba(154,163,184,0.05); stroke: #2a3040; stroke-width: 2; }
.f2-text-muted { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; }
.f2-text-muted-small { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; }
.f2-box-amber { fill: rgba(251,191,36,0.1); stroke: #fbbf24; stroke-width: 4; animation: f2-pulse 2s infinite alternate; }
.f2-text-amber { fill: #fbbf24; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.f2-subtext-amber { fill: #fbbf24; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; opacity: 0.8; }
.f2-axis-title { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f2-axis-label { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.f2-axis-line { fill: none; stroke: #9aa3b8; stroke-width: 2; }
.f2-note-red { fill: #f87171; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f2-leader-red { fill: none; stroke: #f87171; stroke-width: 2; stroke-dasharray: 4 4; }

@keyframes f2-pulse { 0% { filter: drop-shadow(0 0 2px rgba(251,191,36,0.2)); } 100% { filter: drop-shadow(0 0 10px rgba(251,191,36,0.6)); } }

.f3-box-blue { fill: rgba(79,140,255,0.1); stroke: #4f8cff; stroke-width: 2; }
.f3-text-blue { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.f3-subtext-blue { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; opacity: 0.8; }
.f3-box-green { fill: rgba(74,222,128,0.1); stroke: #4ade80; stroke-width: 2; }
.f3-text-green { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.f3-box-muted { fill: rgba(154,163,184,0.05); stroke: #2a3040; stroke-width: 2; }
.f3-text-muted { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; }
.f3-box-green-highlight { fill: rgba(74,222,128,0.15); stroke: #4ade80; stroke-width: 4; animation: f3-pulse 2s infinite alternate; }
.f3-tag-bg-red { fill: #f87171; }
.f3-tag-text-red { fill: #11131a; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; font-weight: bold; }
.f3-axis-title { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f3-axis-label { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.f3-axis-line { fill: none; stroke: #9aa3b8; stroke-width: 2; }

@keyframes f3-pulse { 0% { filter: drop-shadow(0 0 2px rgba(74,222,128,0.2)); } 100% { filter: drop-shadow(0 0 10px rgba(74,222,128,0.6)); } }

.f8-box-muted { fill: #171a23; stroke: #2a3040; stroke-width: 2; }
.f8-text-muted { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f8-box-blue { fill: #171a23; stroke: #4f8cff; stroke-width: 2; }
.f8-text-blue { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f8-box-orange { fill: #171a23; stroke: #ff7043; stroke-width: 2; }
.f8-text-orange { fill: #ff7043; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f8-arrow { fill: none; stroke: #9aa3b8; stroke-width: 2; }
.f8-bracket-green { fill: none; stroke: #4ade80; stroke-width: 2; }
.f8-callout-green { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f8-callout-sub-green { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; opacity: 0.8; }
.f8-bracket-red { fill: none; stroke: #f87171; stroke-width: 2; }
.f8-callout-red { fill: #f87171; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.f8-callout-red-large { fill: #f87171; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 32px; font-weight: bold; animation: f8-pulse 1s infinite alternate; }
.f8-span-red { fill: none; stroke: #f87171; stroke-width: 2; stroke-dasharray: 8 8; animation: f8-flow 1s linear infinite; }
.f8-span-text-red { fill: #f87171; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; font-weight: bold; }
.f8-note-muted { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }

@keyframes f8-pulse { 0% { filter: drop-shadow(0 0 2px rgba(248,113,113,0.4)); } 100% { filter: drop-shadow(0 0 8px rgba(248,113,113,0.9)); } }
@keyframes f8-flow { to { stroke-dashoffset: -16; } }

@media (prefers-reduced-motion: reduce) {
  .f1-center-bg, .f1-token-path, .f2-box-amber, .f3-box-green-highlight, .f8-callout-red-large, .f8-span-red {
    animation: none !important;
  }
}
<!-- ===== END CSS ===== -->