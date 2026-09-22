<!-- ===== BEGIN G4 scanner-bypass ===== -->
<svg viewBox="0 0 1150 350" width="1150" xmlns="http://www.w3.org/2000/svg">
  <text x="460" y="55" class="g4-label" text-anchor="end">of unsafe-serialized HF model files were exploitable</text>
  <text x="460" y="75" class="g4-cite" text-anchor="end">arXiv:2410.04490</text>
  <rect x="480" y="45" width="480" height="24" rx="4" class="g4-bar-red"/>
  <text x="975" y="63" class="g4-val-red">96%</text>
  <text x="460" y="115" class="g4-label" text-anchor="end">gadget bypass vs. the BEST scanner</text>
  <text x="460" y="135" class="g4-cite" text-anchor="end">PickleCloak, arXiv:2508.19774</text>
  <rect x="480" y="105" width="445" height="24" rx="4" class="g4-bar-red"/>
  <text x="940" y="123" class="g4-val-red">89%</text>
  <text x="460" y="175" class="g4-label" text-anchor="end">ShadowPickle "overwritten module" evasion</text>
  <text x="460" y="195" class="g4-cite" text-anchor="end">arXiv:2607.17503</text>
  <rect x="480" y="165" width="315" height="24" rx="4" class="g4-bar-red"/>
  <text x="810" y="183" class="g4-val-red">63%</text>
  <text x="460" y="235" class="g4-label" text-anchor="end">of unsafe files NOT flagged by HF's scanner</text>
  <text x="460" y="255" class="g4-cite" text-anchor="end">arXiv:2410.04490</text>
  <rect x="480" y="225" width="310" height="24" rx="4" class="g4-bar-red"/>
  <text x="805" y="243" class="g4-val-red">62%</text>
  <text x="460" y="295" class="g4-label" text-anchor="end">safetensors: not an executable format</text>
  <rect x="480" y="285" width="6" height="24" rx="3" class="g4-bar-green"/>
  <text x="500" y="303" class="g4-val-green">0%</text>
</svg>
<!-- ===== END G4 ===== -->
<!-- ===== BEGIN G5 signing-flow ===== -->
<svg viewBox="0 0 1090 350" width="1090" xmlns="http://www.w3.org/2000/svg">
  <path id="g5-p1" d="M 180 150 L 250 150" fill="none" stroke="#2a3040" stroke-width="2"/>
  <path id="g5-p2" d="M 390 150 L 460 150" fill="none" stroke="#2a3040" stroke-width="2"/>
  <path id="g5-p3" d="M 620 150 L 690 150" fill="none" stroke="#2a3040" stroke-width="2"/>
  <path id="g5-p4" d="M 830 150 L 900 150" fill="none" stroke="#2a3040" stroke-width="2"/>
  <path id="g5-p5" d="M 970 125 C 970 60, 540 60, 540 125" fill="none" stroke="#4f8cff" stroke-width="2" stroke-dasharray="4 4"/>
  <polygon points="540,125 535,115 545,115" fill="#4f8cff"/>
  <text x="755" y="70" class="g5-verify-lbl" text-anchor="middle">inclusion proof</text>
  <circle class="g5-dot g5-dot-1" cx="0" cy="0" r="4" fill="#4f8cff" />
  <circle class="g5-dot g5-dot-2" cx="0" cy="0" r="4" fill="#4f8cff" />
  <circle class="g5-dot g5-dot-3" cx="0" cy="0" r="4" fill="#4f8cff" />
  <circle class="g5-dot g5-dot-4" cx="0" cy="0" r="4" fill="#4f8cff" />
  <rect x="40" y="125" width="140" height="50" rx="6" class="g5-node"/>
  <text x="110" y="154" class="g5-node-txt" text-anchor="middle">train / abliterate</text>
  <rect x="232" y="125" width="176" height="50" rx="6" class="g5-node"/>
  <text x="320" y="146" class="g5-node-txt" text-anchor="middle">sign</text>
  <text x="320" y="164" class="g5-node-sub" text-anchor="middle">short-lived cert via OIDC</text>
  <rect x="460" y="125" width="160" height="50" rx="6" class="g5-node g5-pulse"/>
  <text x="540" y="146" class="g5-node-txt" text-anchor="middle">transparency log</text>
  <text x="540" y="164" class="g5-node-sub" text-anchor="middle">append-only, public</text>
  <rect x="690" y="125" width="140" height="50" rx="6" class="g5-node"/>
  <text x="760" y="154" class="g5-node-txt" text-anchor="middle">upload to Hub</text>
  <rect x="884" y="125" width="176" height="50" rx="6" class="g5-node"/>
  <text x="972" y="146" class="g5-node-txt" text-anchor="middle">verify</text>
  <text x="972" y="164" class="g5-node-sub" text-anchor="middle">re-hash + check signature</text>
  <rect x="230" y="210" width="180" height="40" rx="4" class="g5-stack-box"/>
  <text x="320" y="228" class="g5-stack-txt" text-anchor="middle">manifest of every file</text>
  <text x="320" y="242" class="g5-stack-txt" text-anchor="middle">→ SHA-256</text>
  <path d="M 320 175 L 320 210" fill="none" stroke="#4ade80" stroke-width="1" stroke-dasharray="2 2"/>
  <rect x="290" y="290" width="500" height="30" rx="4" class="g5-callout-box"/>
  <text x="540" y="310" class="g5-callout-txt" text-anchor="middle">proves WHO made it and that it is UNCHANGED — not that it is SAFE</text>
</svg>
<!-- ===== END G5 ===== -->
<!-- ===== BEGIN G6 inference-vs-weights ===== -->
<svg viewBox="0 0 1040 380" width="1040" xmlns="http://www.w3.org/2000/svg">
  <line x1="500" y1="20" x2="500" y2="360" stroke="#2a3040" stroke-width="2" stroke-dasharray="4 4"/>
  <text x="250" y="40" class="g6-title" text-anchor="middle">inference-time</text>
  <rect x="120" y="90" width="140" height="30" rx="4" class="g6-layer-base"/>
  <rect x="120" y="130" width="140" height="30" rx="4" class="g6-layer-base"/>
  <rect x="120" y="170" width="140" height="30" rx="4" class="g6-layer-base"/>
  <text x="190" y="110" class="g6-layer-txt" text-anchor="middle">layer N-1</text>
  <text x="190" y="150" class="g6-layer-txt" text-anchor="middle">layer N</text>
  <text x="190" y="190" class="g6-layer-txt" text-anchor="middle">layer N+1</text>
  <g class="g6-hook">
    <path d="M 270 145 L 290 145 L 290 120 L 260 120 L 260 130" fill="none" stroke="#4f8cff" stroke-width="3"/>
    <circle cx="260" cy="130" r="4" fill="#4f8cff"/>
    <text x="300" y="135" class="g6-hook-txt">runtime hook</text>
  </g>
  <rect x="140" y="220" width="100" height="24" rx="12" class="g6-tag-green-bg"/>
  <text x="190" y="236" class="g6-tag-green-txt" text-anchor="middle">✓ unmodified</text>
  <circle cx="320" cy="200" r="3" fill="#9aa3b8"/>
  <text x="335" y="204" class="g6-micro">reversible</text>
  <circle cx="320" cy="225" r="3" fill="#9aa3b8"/>
  <text x="335" y="229" class="g6-micro">weights on disk unchanged</text>
  <circle cx="320" cy="250" r="3" fill="#9aa3b8"/>
  <text x="335" y="254" class="g6-micro">nothing to publish</text>
  <circle cx="320" cy="275" r="3" fill="#9aa3b8"/>
  <text x="335" y="279" class="g6-micro">dies with the runtime</text>
  <text x="750" y="40" class="g6-title" text-anchor="middle">weight orthogonalization</text>
  <rect x="620" y="90" width="140" height="30" rx="4" class="g6-layer-base"/>
  <rect x="620" y="130" width="140" height="30" rx="4" class="g6-layer-orange"/>
  <rect x="620" y="170" width="140" height="30" rx="4" class="g6-layer-base"/>
  <text x="690" y="110" class="g6-layer-txt" text-anchor="middle">layer N-1</text>
  <text x="690" y="150" class="g6-layer-txt-dark" text-anchor="middle">layer N (edited)</text>
  <text x="690" y="190" class="g6-layer-txt" text-anchor="middle">layer N+1</text>
  <rect x="640" y="220" width="100" height="24" rx="12" class="g6-tag-orange-bg"/>
  <text x="690" y="236" class="g6-tag-orange-txt" text-anchor="middle">rewritten</text>
  <circle cx="820" cy="125" r="3" fill="#9aa3b8"/>
  <text x="835" y="129" class="g6-micro">irreversible</text>
  <circle cx="820" cy="150" r="3" fill="#9aa3b8"/>
  <text x="835" y="154" class="g6-micro">rank-one weight edit</text>
  <circle cx="820" cy="175" r="3" fill="#9aa3b8"/>
  <text x="835" y="179" class="g6-micro">runs anywhere</text>
  <circle cx="820" cy="200" r="3" fill="#9aa3b8"/>
  <text x="835" y="204" class="g6-micro">THIS is what gets uploaded</text>
  <rect x="550" y="300" width="400" height="36" rx="6" class="g6-emp-bg"/>
  <text x="750" y="323" class="g6-emp-txt" text-anchor="middle">only this one creates a supply-chain artifact</text>
</svg>
<!-- ===== END G6 ===== -->
<!-- ===== BEGIN G7 hub-scale ===== -->
<svg viewBox="0 0 1120 420" width="1120" xmlns="http://www.w3.org/2000/svg">
  <rect x="100" y="20" width="800" height="320" rx="8" class="g7-box-1"/>
  <text x="115" y="45" class="g7-val">13,841</text>
  <text x="175" y="45" class="g7-lbl">uncensored</text>
  <rect x="145" y="60" width="710" height="280" rx="8" class="g7-box-2"/>
  <text x="160" y="85" class="g7-val">10,947</text>
  <text x="220" y="85" class="g7-lbl">abliterated</text>
  <rect x="240" y="100" width="520" height="240" rx="8" class="g7-box-3"/>
  <text x="255" y="125" class="g7-val">5,844</text>
  <text x="305" y="125" class="g7-lbl">heretic</text>
  <rect x="457" y="306" width="85" height="34" rx="4" class="g7-box-4 g7-pulse"/>
  <path d="M 499 340 L 499 372 L 540 372" fill="none" stroke="#4ade80" stroke-width="2"/>
  <circle cx="542" cy="323" r="3" fill="#4ade80"/>
  <text x="552" y="378" class="g7-val-green">158</text>
  <text x="590" y="378" class="g7-lbl-green">ship a reproduce.json</text>
  <text x="552" y="402" class="g7-callout">2.7% of Heretic models can prove how they were made</text>
</svg>
<!-- ===== END G7 ===== -->
<!-- ===== BEGIN CSS ===== -->
.g4-label { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 13px; }
.g4-cite { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 11px; }
.g4-val-red { fill: #f87171; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.g4-val-green { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.g4-bar-red { fill: #f87171; animation: g4-shimmer 3s infinite alternate ease-in-out; }
.g4-bar-green { fill: #4ade80; filter: drop-shadow(0 0 4px rgba(74,222,128,0.4)); }
@keyframes g4-shimmer {
  0% { filter: drop-shadow(0 0 2px rgba(248,113,113,0.2)); opacity: 0.9; }
  100% { filter: drop-shadow(0 0 8px rgba(248,113,113,0.6)); opacity: 1; }
}
.g5-node { fill: #171a23; stroke: #2a3040; stroke-width: 2; }
.g5-node-txt { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.g5-node-sub { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 10px; }
.g5-verify-lbl { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 11px; }
.g5-stack-box { fill: rgba(74,222,128,0.1); stroke: #4ade80; stroke-width: 1; }
.g5-stack-txt { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 11px; }
.g5-callout-box { fill: rgba(251,191,36,0.1); stroke: #fbbf24; stroke-width: 1; }
.g5-callout-txt { fill: #fbbf24; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; font-weight: bold; }
.g5-pulse { animation: g5-pulse-anim 2s infinite alternate ease-in-out; }
@keyframes g5-pulse-anim {
  0% { stroke: #2a3040; filter: drop-shadow(0 0 0px rgba(79,140,255,0)); }
  100% { stroke: #4f8cff; filter: drop-shadow(0 0 6px rgba(79,140,255,0.4)); }
}
.g5-dot { offset-distance: 0%; animation: g5-flow 2s linear infinite; }
@keyframes g5-flow {
  0% { offset-distance: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { offset-distance: 100%; opacity: 0; }
}
.g5-dot-1 { offset-path: path('M 180 150 L 250 150'); animation-delay: 0s; }
.g5-dot-2 { offset-path: path('M 390 150 L 460 150'); animation-delay: 0.5s; }
.g5-dot-3 { offset-path: path('M 620 150 L 690 150'); animation-delay: 1s; }
.g5-dot-4 { offset-path: path('M 830 150 L 900 150'); animation-delay: 1.5s; }
.g6-title { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 16px; font-weight: bold; }
.g6-layer-base { fill: #171a23; stroke: #2a3040; stroke-width: 2; }
.g6-layer-orange { fill: rgba(255,112,67,0.2); stroke: #ff7043; stroke-width: 2; filter: drop-shadow(0 0 6px rgba(255,112,67,0.4)); }
.g6-layer-txt { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.g6-layer-txt-dark { fill: #ff7043; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; font-weight: bold; }
.g6-hook { animation: g6-hook-pulse 2s infinite alternate ease-in-out; }
.g6-hook-txt { fill: #4f8cff; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 11px; }
.g6-tag-green-bg { fill: rgba(74,222,128,0.15); stroke: #4ade80; stroke-width: 1; }
.g6-tag-green-txt { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 11px; font-weight: bold; }
.g6-tag-orange-bg { fill: rgba(255,112,67,0.15); stroke: #ff7043; stroke-width: 1; }
.g6-tag-orange-txt { fill: #ff7043; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 11px; font-weight: bold; }
.g6-micro { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.g6-emp-bg { fill: rgba(248,113,113,0.15); stroke: #f87171; stroke-width: 2; }
.g6-emp-txt { fill: #f87171; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 13px; font-weight: bold; }
@keyframes g6-hook-pulse {
  0% { opacity: 0.4; }
  100% { opacity: 1; filter: drop-shadow(0 0 4px rgba(79,140,255,0.6)); }
}
.g7-box-1 { fill: rgba(42,48,64,0.2); stroke: #2a3040; stroke-width: 2; }
.g7-box-2 { fill: rgba(79,140,255,0.05); stroke: rgba(79,140,255,0.4); stroke-width: 2; }
.g7-box-3 { fill: rgba(79,140,255,0.1); stroke: #4f8cff; stroke-width: 2; }
.g7-box-4 { fill: rgba(74,222,128,0.2); stroke: #4ade80; stroke-width: 2; }
.g7-val { fill: #e6e9f0; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.g7-lbl { fill: #9aa3b8; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; }
.g7-val-green { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; font-weight: bold; }
.g7-lbl-green { fill: #4ade80; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 14px; }
.g7-callout { fill: #fbbf24; font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace; font-size: 12px; }
.g7-pulse { animation: g7-pulse-anim 2s infinite alternate ease-in-out; }
@keyframes g7-pulse-anim {
  0% { filter: drop-shadow(0 0 2px rgba(74,222,128,0.4)); }
  100% { filter: drop-shadow(0 0 8px rgba(74,222,128,0.8)); }
}
@media (prefers-reduced-motion: reduce) {
  .g4-bar-red, .g5-pulse, .g5-dot, .g6-hook, .g7-pulse { animation: none; }
}
<!-- ===== END CSS ===== -->