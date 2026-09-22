<!-- ===== BEGIN E1 pipeline ===== -->
<svg viewBox="0 0 1140 400" width="1140" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <path id="e1-p1" d="M 120 200 L 150 200" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p2" d="M 280 200 L 310 200" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p3a" d="M 480 190 C 495 190, 495 110, 510 110 L 510 110" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p4a" d="M 670 110 L 700 110" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p5a" d="M 830 110 L 860 110" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p3b" d="M 480 210 C 495 210, 495 290, 510 290 L 510 290" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p4b" d="M 670 290 L 700 290" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p5b" d="M 830 290 L 860 290" fill="none" stroke="#2a3040" stroke-width="2"/>
    <path id="e1-p6b" d="M 990 290 L 1020 290" fill="none" stroke="#2a3040" stroke-width="2"/>
  </defs>
  <use href="#e1-p1" />
  <use href="#e1-p2" />
  <use href="#e1-p3a" />
  <use href="#e1-p4a" />
  <use href="#e1-p5a" />
  <use href="#e1-p3b" />
  <use href="#e1-p4b" />
  <use href="#e1-p5b" />
  <use href="#e1-p6b" />
  <circle class="e1-dot e1-dot-1" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-2" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-3a" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-4a" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-5a" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-3b" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-4b" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-5b" r="3" fill="#4f8cff" />
  <circle class="e1-dot e1-dot-6b" r="3" fill="#4f8cff" />
  <rect x="10" y="170" width="110" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="65" y="195" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">HF Hub model</text>
  <text x="65" y="215" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">safetensors</text>
  <rect class="e1-pulse" x="150" y="170" width="130" height="60" rx="6" fill="#171a23" stroke="#ff7043" stroke-width="2"/>
  <text x="215" y="195" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">make abliterate</text>
  <text x="215" y="215" fill="#ff7043" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">heretic</text>
  <rect x="310" y="170" width="170" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="395" y="195" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">outputs/&lt;model&gt;-heretic/</text>
  <text x="395" y="215" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">decensored, merged</text>
  <rect x="510" y="80" width="160" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="590" y="105" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">make calibration-data</text>
  <text x="590" y="125" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">COCO images, AWQ</text>
  <rect x="700" y="80" width="130" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="765" y="115" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">make convert-mlx</text>
  <rect x="860" y="80" width="100" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="910" y="105" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">MLX</text>
  <text x="910" y="125" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">Apple Silicon</text>
  <rect x="510" y="260" width="160" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="590" y="285" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">make calibration-text</text>
  <text x="590" y="305" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">Alpaca text, imatrix</text>
  <rect x="700" y="260" width="130" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="765" y="295" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">make convert-gguf</text>
  <rect x="860" y="260" width="130" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="925" y="295" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">make quantize-gguf</text>
  <rect x="1020" y="260" width="80" height="60" rx="6" fill="#171a23" stroke="#2a3040" stroke-width="1"/>
  <text x="1060" y="285" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="middle">GGUF</text>
  <text x="1060" y="305" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="10" text-anchor="middle">llama.cpp / Ollama</text>
  <text x="510" y="200" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="11" text-anchor="start">two independent export paths — never cross-feed</text>
  <rect x="20" y="160" width="100" height="16" rx="4" fill="#11131a" stroke="#4ade80" stroke-width="1"/>
  <text x="70" y="171" fill="#4ade80" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="9" text-anchor="middle">.provenance.json</text>
  <rect x="380" y="160" width="100" height="16" rx="4" fill="#11131a" stroke="#4ade80" stroke-width="1"/>
  <text x="430" y="171" fill="#4ade80" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="9" text-anchor="middle">.provenance.json</text>
  <rect x="860" y="70" width="100" height="16" rx="4" fill="#11131a" stroke="#4ade80" stroke-width="1"/>
  <text x="910" y="81" fill="#4ade80" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="9" text-anchor="middle">.provenance.json</text>
  <rect x="1000" y="250" width="100" height="16" rx="4" fill="#11131a" stroke="#4ade80" stroke-width="1"/>
  <text x="1050" y="261" fill="#4ade80" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="9" text-anchor="middle">.provenance.json</text>
</svg>
<!-- ===== END E1 ===== -->

<!-- ===== BEGIN E2 custody-decay ===== -->
<svg viewBox="0 0 1100 452" width="1100" xmlns="http://www.w3.org/2000/svg">
<text x="48" y="26" class="e2-title">what is still provable at each hop</text>
<line x1="44" y1="285" x2="1046" y2="285" class="e2-track"/>
<rect x="30" y="238" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="250" class="e2-chip-txt" text-anchor="middle">commit</text>
<rect x="30" y="217" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="229" class="e2-chip-txt" text-anchor="middle">seed</text>
<rect x="30" y="196" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="208" class="e2-chip-txt" text-anchor="middle">trial</text>
<rect x="30" y="175" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="187" class="e2-chip-txt" text-anchor="middle">sha256</text>
<rect x="30" y="154" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="166" class="e2-chip-txt" text-anchor="middle">versions</text>
<rect x="30" y="133" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="145" class="e2-chip-txt" text-anchor="middle">datasets</text>
<rect x="30" y="112" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="78" y="124" class="e2-chip-txt" text-anchor="middle">license</text>
<circle cx="78" cy="285" r="6" class="e2-node"/>
<text x="78" y="320" class="e2-hop" text-anchor="middle">1 base model</text>
<text x="78" y="106" class="e2-count" text-anchor="middle">7</text>
<rect x="184" y="238" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="232" y="250" class="e2-chip-txt" text-anchor="middle">commit</text>
<rect x="184" y="217" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="232" y="229" class="e2-chip-txt" text-anchor="middle">seed</text>
<rect x="184" y="196" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="232" y="208" class="e2-chip-txt" text-anchor="middle">trial</text>
<rect x="184" y="175" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="232" y="187" class="e2-chip-txt" text-anchor="middle">sha256</text>
<rect x="184" y="154" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="232" y="166" class="e2-chip-txt" text-anchor="middle">versions</text>
<rect x="184" y="133" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="232" y="145" class="e2-chip-txt" text-anchor="middle">datasets</text>
<circle cx="232" cy="285" r="6" class="e2-node"/>
<text x="232" y="320" class="e2-hop" text-anchor="middle">2 prompt datasets</text>
<text x="232" y="127" class="e2-count" text-anchor="middle">6</text>
<rect x="338" y="238" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="386" y="250" class="e2-chip-txt" text-anchor="middle">commit</text>
<rect x="338" y="217" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="386" y="229" class="e2-chip-txt" text-anchor="middle">seed</text>
<rect x="338" y="196" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="386" y="208" class="e2-chip-txt" text-anchor="middle">trial</text>
<rect x="338" y="175" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="386" y="187" class="e2-chip-txt" text-anchor="middle">sha256</text>
<rect x="338" y="154" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="386" y="166" class="e2-chip-txt" text-anchor="middle">versions</text>
<circle cx="386" cy="285" r="6" class="e2-node"/>
<text x="386" y="320" class="e2-hop" text-anchor="middle">3 the tool</text>
<text x="386" y="148" class="e2-count" text-anchor="middle">5</text>
<rect x="492" y="238" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="540" y="250" class="e2-chip-txt" text-anchor="middle">commit</text>
<rect x="492" y="217" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="540" y="229" class="e2-chip-txt" text-anchor="middle">seed</text>
<rect x="492" y="196" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="540" y="208" class="e2-chip-txt" text-anchor="middle">trial</text>
<rect x="492" y="175" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="540" y="187" class="e2-chip-txt" text-anchor="middle">sha256</text>
<circle cx="540" cy="285" r="6" class="e2-node"/>
<text x="540" y="320" class="e2-hop" text-anchor="middle">4 parameters</text>
<text x="540" y="169" class="e2-count" text-anchor="middle">4</text>
<rect x="646" y="238" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="694" y="250" class="e2-chip-txt" text-anchor="middle">commit</text>
<rect x="646" y="217" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="694" y="229" class="e2-chip-txt" text-anchor="middle">seed</text>
<rect x="646" y="196" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="694" y="208" class="e2-chip-txt" text-anchor="middle">trial</text>
<circle cx="694" cy="285" r="6" class="e2-node"/>
<text x="694" y="320" class="e2-hop" text-anchor="middle">5 the merge</text>
<text x="694" y="190" class="e2-count" text-anchor="middle">3</text>
<rect x="800" y="238" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="848" y="250" class="e2-chip-txt" text-anchor="middle">commit</text>
<rect x="800" y="217" width="96" height="17" rx="4" class="e2-chip-live"/>
<text x="848" y="229" class="e2-chip-txt" text-anchor="middle">seed</text>
<circle cx="848" cy="285" r="6" class="e2-node"/>
<text x="848" y="320" class="e2-hop" text-anchor="middle">6 quantization</text>
<text x="848" y="211" class="e2-count" text-anchor="middle">2</text>
<rect x="954" y="238" width="96" height="17" rx="4" class="e2-chip-dead"/>
<text x="1002" y="250" class="e2-chip-txt-dead" text-anchor="middle">filename</text>
<circle cx="1002" cy="285" r="6" class="e2-node e2-node-last"/>
<text x="1002" y="320" class="e2-hop" text-anchor="middle">7 re-upload</text>
<text x="1002" y="232" class="e2-count" text-anchor="middle">1</text>
<g class="e2-ghost" style="animation-delay:0.0s" transform="rotate(-13 155 338)"><rect x="107" y="338" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="155" y="350" class="e2-ghost-txt" text-anchor="middle">license</text></g>
<g class="e2-ghost" style="animation-delay:-0.9s" transform="rotate(-5 309 338)"><rect x="261" y="338" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="309" y="350" class="e2-ghost-txt" text-anchor="middle">datasets</text></g>
<g class="e2-ghost" style="animation-delay:-1.8s" transform="rotate(3 463 338)"><rect x="415" y="338" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="463" y="350" class="e2-ghost-txt" text-anchor="middle">versions</text></g>
<g class="e2-ghost" style="animation-delay:-2.7s" transform="rotate(11 617 338)"><rect x="569" y="338" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="617" y="350" class="e2-ghost-txt" text-anchor="middle">trial</text></g>
<g class="e2-ghost" style="animation-delay:-3.6s" transform="rotate(-13 771 338)"><rect x="723" y="338" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="771" y="350" class="e2-ghost-txt" text-anchor="middle">sha256</text></g>
<g class="e2-ghost" style="animation-delay:-4.5s" transform="rotate(-5 925 338)"><rect x="877" y="338" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="925" y="350" class="e2-ghost-txt" text-anchor="middle">commit</text></g>
<g class="e2-ghost" style="animation-delay:-5.4s" transform="rotate(3 955 353)"><rect x="907" y="353" width="96" height="17" rx="4" class="e2-ghost-box"/><text x="955" y="365" class="e2-ghost-txt" text-anchor="middle">seed</text></g>
<text x="48" y="424" class="e2-lost">↓ evidence dropped at each hop — nothing downstream recreates it</text>
<text x="886" y="404" class="e2-end-cap" text-anchor="middle">the only provenance record that survived</text>
<rect x="700" y="414" width="372" height="26" rx="5" class="e2-end-box"/>
<text x="886" y="431" class="e2-end-txt" text-anchor="middle">Qwen3.6-40B-…-Heretic-Uncensored-NEO-MAX-GGUF</text>
</svg>
<!-- ===== END E2 ===== -->

<!-- ===== BEGIN E3 dot-grid ===== -->
<svg viewBox="0 0 1100 400" width="1100" xmlns="http://www.w3.org/2000/svg">
<g transform="translate(750, 50)" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">
<circle cx="0" cy="0" r="6" fill="#2a3040"/>
<text x="15" y="4" fill="#9aa3b8">no reproducibility claim  (5,484)</text>
<circle cx="0" cy="30" r="6" fill="#fbbf24"/>
<text x="15" y="34" fill="#e6e9f0">claim it, ship nothing    (202)</text>
<circle cx="0" cy="60" r="6" fill="#4ade80" class="e3-pulse"/>
<text x="15" y="64" fill="#e6e9f0">ship a `reproduce.json`   (158)</text>
</g>
<text x="750" y="200" fill="#4ade80" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="72" font-weight="bold">2.7%</text>
<text x="755" y="230" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="16">158 of 5,844 models</text>
<circle cx="50" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.0s"/>
<circle cx="66" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.1s"/>
<circle cx="82" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.2s"/>
<circle cx="98" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.30000000000000004s"/>
<circle cx="114" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.4s"/>
<circle cx="130" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.5s"/>
<circle cx="146" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.6000000000000001s"/>
<circle cx="162" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.7000000000000001s"/>
<circle cx="178" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.8s"/>
<circle cx="194" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 0.9s"/>
<circle cx="210" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 1.0s"/>
<circle cx="226" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 1.1s"/>
<circle cx="242" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 1.2000000000000002s"/>
<circle cx="258" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 1.3s"/>
<circle cx="274" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 1.4000000000000001s"/>
<circle cx="290" cy="50" r="4" fill="#4ade80" class="e3-pulse e3-dot" style="animation-delay: 1.5s"/>
<circle cx="306" cy="50" r="4" fill="#fbbf24"/>
<circle cx="322" cy="50" r="4" fill="#fbbf24"/>
<circle cx="338" cy="50" r="4" fill="#fbbf24"/>
<circle cx="354" cy="50" r="4" fill="#fbbf24"/>
<circle cx="370" cy="50" r="4" fill="#fbbf24"/>
<circle cx="386" cy="50" r="4" fill="#fbbf24"/>
<circle cx="402" cy="50" r="4" fill="#fbbf24"/>
<circle cx="418" cy="50" r="4" fill="#fbbf24"/>
<circle cx="434" cy="50" r="4" fill="#fbbf24"/>
<circle cx="450" cy="50" r="4" fill="#fbbf24"/>
<circle cx="466" cy="50" r="4" fill="#fbbf24"/>
<circle cx="482" cy="50" r="4" fill="#fbbf24"/>
<circle cx="498" cy="50" r="4" fill="#fbbf24"/>
<circle cx="514" cy="50" r="4" fill="#fbbf24"/>
<circle cx="530" cy="50" r="4" fill="#fbbf24"/>
<circle cx="546" cy="50" r="4" fill="#fbbf24"/>
<circle cx="562" cy="50" r="4" fill="#fbbf24"/>
<circle cx="578" cy="50" r="4" fill="#fbbf24"/>
<circle cx="594" cy="50" r="4" fill="#fbbf24"/>
<circle cx="610" cy="50" r="4" fill="#fbbf24"/>
<circle cx="50" cy="66" r="4" fill="#2a3040"/>
<circle cx="66" cy="66" r="4" fill="#2a3040"/>
<circle cx="82" cy="66" r="4" fill="#2a3040"/>
<circle cx="98" cy="66" r="4" fill="#2a3040"/>
<circle cx="114" cy="66" r="4" fill="#2a3040"/>
<circle cx="130" cy="66" r="4" fill="#2a3040"/>
<circle cx="146" cy="66" r="4" fill="#2a3040"/>
<circle cx="162" cy="66" r="4" fill="#2a3040"/>
<circle cx="178" cy="66" r="4" fill="#2a3040"/>
<circle cx="194" cy="66" r="4" fill="#2a3040"/>
<circle cx="210" cy="66" r="4" fill="#2a3040"/>
<circle cx="226" cy="66" r="4" fill="#2a3040"/>
<circle cx="242" cy="66" r="4" fill="#2a3040"/>
<circle cx="258" cy="66" r="4" fill="#2a3040"/>
<circle cx="274" cy="66" r="4" fill="#2a3040"/>
<circle cx="290" cy="66" r="4" fill="#2a3040"/>
<circle cx="306" cy="66" r="4" fill="#2a3040"/>
<circle cx="322" cy="66" r="4" fill="#2a3040"/>
<circle cx="338" cy="66" r="4" fill="#2a3040"/>
<circle cx="354" cy="66" r="4" fill="#2a3040"/>
<circle cx="370" cy="66" r="4" fill="#2a3040"/>
<circle cx="386" cy="66" r="4" fill="#2a3040"/>
<circle cx="402" cy="66" r="4" fill="#2a3040"/>
<circle cx="418" cy="66" r="4" fill="#2a3040"/>
<circle cx="434" cy="66" r="4" fill="#2a3040"/>
<circle cx="450" cy="66" r="4" fill="#2a3040"/>
<circle cx="466" cy="66" r="4" fill="#2a3040"/>
<circle cx="482" cy="66" r="4" fill="#2a3040"/>
<circle cx="498" cy="66" r="4" fill="#2a3040"/>
<circle cx="514" cy="66" r="4" fill="#2a3040"/>
<circle cx="530" cy="66" r="4" fill="#2a3040"/>
<circle cx="546" cy="66" r="4" fill="#2a3040"/>
<circle cx="562" cy="66" r="4" fill="#2a3040"/>
<circle cx="578" cy="66" r="4" fill="#2a3040"/>
<circle cx="594" cy="66" r="4" fill="#2a3040"/>
<circle cx="610" cy="66" r="4" fill="#2a3040"/>
<circle cx="50" cy="82" r="4" fill="#2a3040"/>
<circle cx="66" cy="82" r="4" fill="#2a3040"/>
<circle cx="82" cy="82" r="4" fill="#2a3040"/>
<circle cx="98" cy="82" r="4" fill="#2a3040"/>
<circle cx="114" cy="82" r="4" fill="#2a3040"/>
<circle cx="130" cy="82" r="4" fill="#2a3040"/>
<circle cx="146" cy="82" r="4" fill="#2a3040"/>
<circle cx="162" cy="82" r="4" fill="#2a3040"/>
<circle cx="178" cy="82" r="4" fill="#2a3040"/>
<circle cx="194" cy="82" r="4" fill="#2a3040"/>
<circle cx="210" cy="82" r="4" fill="#2a3040"/>
<circle cx="226" cy="82" r="4" fill="#2a3040"/>
<circle cx="242" cy="82" r="4" fill="#2a3040"/>
<circle cx="258" cy="82" r="4" fill="#2a3040"/>
<circle cx="274" cy="82" r="4" fill="#2a3040"/>
<circle cx="290" cy="82" r="4" fill="#2a3040"/>
<circle cx="306" cy="82" r="4" fill="#2a3040"/>
<circle cx="322" cy="82" r="4" fill="#2a3040"/>
<circle cx="338" cy="82" r="4" fill="#2a3040"/>
<circle cx="354" cy="82" r="4" fill="#2a3040"/>
<circle cx="370" cy="82" r="4" fill="#2a3040"/>
<circle cx="386" cy="82" r="4" fill="#2a3040"/>
<circle cx="402" cy="82" r="4" fill="#2a3040"/>
<circle cx="418" cy="82" r="4" fill="#2a3040"/>
<circle cx="434" cy="82" r="4" fill="#2a3040"/>
<circle cx="450" cy="82" r="4" fill="#2a3040"/>
<circle cx="466" cy="82" r="4" fill="#2a3040"/>
<circle cx="482" cy="82" r="4" fill="#2a3040"/>
<circle cx="498" cy="82" r="4" fill="#2a3040"/>
<circle cx="514" cy="82" r="4" fill="#2a3040"/>
<circle cx="530" cy="82" r="4" fill="#2a3040"/>
<circle cx="546" cy="82" r="4" fill="#2a3040"/>
<circle cx="562" cy="82" r="4" fill="#2a3040"/>
<circle cx="578" cy="82" r="4" fill="#2a3040"/>
<circle cx="594" cy="82" r="4" fill="#2a3040"/>
<circle cx="610" cy="82" r="4" fill="#2a3040"/>
<circle cx="50" cy="98" r="4" fill="#2a3040"/>
<circle cx="66" cy="98" r="4" fill="#2a3040"/>
<circle cx="82" cy="98" r="4" fill="#2a3040"/>
<circle cx="98" cy="98" r="4" fill="#2a3040"/>
<circle cx="114" cy="98" r="4" fill="#2a3040"/>
<circle cx="130" cy="98" r="4" fill="#2a3040"/>
<circle cx="146" cy="98" r="4" fill="#2a3040"/>
<circle cx="162" cy="98" r="4" fill="#2a3040"/>
<circle cx="178" cy="98" r="4" fill="#2a3040"/>
<circle cx="194" cy="98" r="4" fill="#2a3040"/>
<circle cx="210" cy="98" r="4" fill="#2a3040"/>
<circle cx="226" cy="98" r="4" fill="#2a3040"/>
<circle cx="242" cy="98" r="4" fill="#2a3040"/>
<circle cx="258" cy="98" r="4" fill="#2a3040"/>
<circle cx="274" cy="98" r="4" fill="#2a3040"/>
<circle cx="290" cy="98" r="4" fill="#2a3040"/>
<circle cx="306" cy="98" r="4" fill="#2a3040"/>
<circle cx="322" cy="98" r="4" fill="#2a3040"/>
<circle cx="338" cy="98" r="4" fill="#2a3040"/>
<circle cx="354" cy="98" r="4" fill="#2a3040"/>
<circle cx="370" cy="98" r="4" fill="#2a3040"/>
<circle cx="386" cy="98" r="4" fill="#2a3040"/>
<circle cx="402" cy="98" r="4" fill="#2a3040"/>
<circle cx="418" cy="98" r="4" fill="#2a3040"/>
<circle cx="434" cy="98" r="4" fill="#2a3040"/>
<circle cx="450" cy="98" r="4" fill="#2a3040"/>
<circle cx="466" cy="98" r="4" fill="#2a3040"/>
<circle cx="482" cy="98" r="4" fill="#2a3040"/>
<circle cx="498" cy="98" r="4" fill="#2a3040"/>
<circle cx="514" cy="98" r="4" fill="#2a3040"/>
<circle cx="530" cy="98" r="4" fill="#2a3040"/>
<circle cx="546" cy="98" r="4" fill="#2a3040"/>
<circle cx="562" cy="98" r="4" fill="#2a3040"/>
<circle cx="578" cy="98" r="4" fill="#2a3040"/>
<circle cx="594" cy="98" r="4" fill="#2a3040"/>
<circle cx="610" cy="98" r="4" fill="#2a3040"/>
<circle cx="50" cy="114" r="4" fill="#2a3040"/>
<circle cx="66" cy="114" r="4" fill="#2a3040"/>
<circle cx="82" cy="114" r="4" fill="#2a3040"/>
<circle cx="98" cy="114" r="4" fill="#2a3040"/>
<circle cx="114" cy="114" r="4" fill="#2a3040"/>
<circle cx="130" cy="114" r="4" fill="#2a3040"/>
<circle cx="146" cy="114" r="4" fill="#2a3040"/>
<circle cx="162" cy="114" r="4" fill="#2a3040"/>
<circle cx="178" cy="114" r="4" fill="#2a3040"/>
<circle cx="194" cy="114" r="4" fill="#2a3040"/>
<circle cx="210" cy="114" r="4" fill="#2a3040"/>
<circle cx="226" cy="114" r="4" fill="#2a3040"/>
<circle cx="242" cy="114" r="4" fill="#2a3040"/>
<circle cx="258" cy="114" r="4" fill="#2a3040"/>
<circle cx="274" cy="114" r="4" fill="#2a3040"/>
<circle cx="290" cy="114" r="4" fill="#2a3040"/>
<circle cx="306" cy="114" r="4" fill="#2a3040"/>
<circle cx="322" cy="114" r="4" fill="#2a3040"/>
<circle cx="338" cy="114" r="4" fill="#2a3040"/>
<circle cx="354" cy="114" r="4" fill="#2a3040"/>
<circle cx="370" cy="114" r="4" fill="#2a3040"/>
<circle cx="386" cy="114" r="4" fill="#2a3040"/>
<circle cx="402" cy="114" r="4" fill="#2a3040"/>
<circle cx="418" cy="114" r="4" fill="#2a3040"/>
<circle cx="434" cy="114" r="4" fill="#2a3040"/>
<circle cx="450" cy="114" r="4" fill="#2a3040"/>
<circle cx="466" cy="114" r="4" fill="#2a3040"/>
<circle cx="482" cy="114" r="4" fill="#2a3040"/>
<circle cx="498" cy="114" r="4" fill="#2a3040"/>
<circle cx="514" cy="114" r="4" fill="#2a3040"/>
<circle cx="530" cy="114" r="4" fill="#2a3040"/>
<circle cx="546" cy="114" r="4" fill="#2a3040"/>
<circle cx="562" cy="114" r="4" fill="#2a3040"/>
<circle cx="578" cy="114" r="4" fill="#2a3040"/>
<circle cx="594" cy="114" r="4" fill="#2a3040"/>
<circle cx="610" cy="114" r="4" fill="#2a3040"/>
<circle cx="50" cy="130" r="4" fill="#2a3040"/>
<circle cx="66" cy="130" r="4" fill="#2a3040"/>
<circle cx="82" cy="130" r="4" fill="#2a3040"/>
<circle cx="98" cy="130" r="4" fill="#2a3040"/>
<circle cx="114" cy="130" r="4" fill="#2a3040"/>
<circle cx="130" cy="130" r="4" fill="#2a3040"/>
<circle cx="146" cy="130" r="4" fill="#2a3040"/>
<circle cx="162" cy="130" r="4" fill="#2a3040"/>
<circle cx="178" cy="130" r="4" fill="#2a3040"/>
<circle cx="194" cy="130" r="4" fill="#2a3040"/>
<circle cx="210" cy="130" r="4" fill="#2a3040"/>
<circle cx="226" cy="130" r="4" fill="#2a3040"/>
<circle cx="242" cy="130" r="4" fill="#2a3040"/>
<circle cx="258" cy="130" r="4" fill="#2a3040"/>
<circle cx="274" cy="130" r="4" fill="#2a3040"/>
<circle cx="290" cy="130" r="4" fill="#2a3040"/>
<circle cx="306" cy="130" r="4" fill="#2a3040"/>
<circle cx="322" cy="130" r="4" fill="#2a3040"/>
<circle cx="338" cy="130" r="4" fill="#2a3040"/>
<circle cx="354" cy="130" r="4" fill="#2a3040"/>
<circle cx="370" cy="130" r="4" fill="#2a3040"/>
<circle cx="386" cy="130" r="4" fill="#2a3040"/>
<circle cx="402" cy="130" r="4" fill="#2a3040"/>
<circle cx="418" cy="130" r="4" fill="#2a3040"/>
<circle cx="434" cy="130" r="4" fill="#2a3040"/>
<circle cx="450" cy="130" r="4" fill="#2a3040"/>
<circle cx="466" cy="130" r="4" fill="#2a3040"/>
<circle cx="482" cy="130" r="4" fill="#2a3040"/>
<circle cx="498" cy="130" r="4" fill="#2a3040"/>
<circle cx="514" cy="130" r="4" fill="#2a3040"/>
<circle cx="530" cy="130" r="4" fill="#2a3040"/>
<circle cx="546" cy="130" r="4" fill="#2a3040"/>
<circle cx="562" cy="130" r="4" fill="#2a3040"/>
<circle cx="578" cy="130" r="4" fill="#2a3040"/>
<circle cx="594" cy="130" r="4" fill="#2a3040"/>
<circle cx="610" cy="130" r="4" fill="#2a3040"/>
<circle cx="50" cy="146" r="4" fill="#2a3040"/>
<circle cx="66" cy="146" r="4" fill="#2a3040"/>
<circle cx="82" cy="146" r="4" fill="#2a3040"/>
<circle cx="98" cy="146" r="4" fill="#2a3040"/>
<circle cx="114" cy="146" r="4" fill="#2a3040"/>
<circle cx="130" cy="146" r="4" fill="#2a3040"/>
<circle cx="146" cy="146" r="4" fill="#2a3040"/>
<circle cx="162" cy="146" r="4" fill="#2a3040"/>
<circle cx="178" cy="146" r="4" fill="#2a3040"/>
<circle cx="194" cy="146" r="4" fill="#2a3040"/>
<circle cx="210" cy="146" r="4" fill="#2a3040"/>
<circle cx="226" cy="146" r="4" fill="#2a3040"/>
<circle cx="242" cy="146" r="4" fill="#2a3040"/>
<circle cx="258" cy="146" r="4" fill="#2a3040"/>
<circle cx="274" cy="146" r="4" fill="#2a3040"/>
<circle cx="290" cy="146" r="4" fill="#2a3040"/>
<circle cx="306" cy="146" r="4" fill="#2a3040"/>
<circle cx="322" cy="146" r="4" fill="#2a3040"/>
<circle cx="338" cy="146" r="4" fill="#2a3040"/>
<circle cx="354" cy="146" r="4" fill="#2a3040"/>
<circle cx="370" cy="146" r="4" fill="#2a3040"/>
<circle cx="386" cy="146" r="4" fill="#2a3040"/>
<circle cx="402" cy="146" r="4" fill="#2a3040"/>
<circle cx="418" cy="146" r="4" fill="#2a3040"/>
<circle cx="434" cy="146" r="4" fill="#2a3040"/>
<circle cx="450" cy="146" r="4" fill="#2a3040"/>
<circle cx="466" cy="146" r="4" fill="#2a3040"/>
<circle cx="482" cy="146" r="4" fill="#2a3040"/>
<circle cx="498" cy="146" r="4" fill="#2a3040"/>
<circle cx="514" cy="146" r="4" fill="#2a3040"/>
<circle cx="530" cy="146" r="4" fill="#2a3040"/>
<circle cx="546" cy="146" r="4" fill="#2a3040"/>
<circle cx="562" cy="146" r="4" fill="#2a3040"/>
<circle cx="578" cy="146" r="4" fill="#2a3040"/>
<circle cx="594" cy="146" r="4" fill="#2a3040"/>
<circle cx="610" cy="146" r="4" fill="#2a3040"/>
<circle cx="50" cy="162" r="4" fill="#2a3040"/>
<circle cx="66" cy="162" r="4" fill="#2a3040"/>
<circle cx="82" cy="162" r="4" fill="#2a3040"/>
<circle cx="98" cy="162" r="4" fill="#2a3040"/>
<circle cx="114" cy="162" r="4" fill="#2a3040"/>
<circle cx="130" cy="162" r="4" fill="#2a3040"/>
<circle cx="146" cy="162" r="4" fill="#2a3040"/>
<circle cx="162" cy="162" r="4" fill="#2a3040"/>
<circle cx="178" cy="162" r="4" fill="#2a3040"/>
<circle cx="194" cy="162" r="4" fill="#2a3040"/>
<circle cx="210" cy="162" r="4" fill="#2a3040"/>
<circle cx="226" cy="162" r="4" fill="#2a3040"/>
<circle cx="242" cy="162" r="4" fill="#2a3040"/>
<circle cx="258" cy="162" r="4" fill="#2a3040"/>
<circle cx="274" cy="162" r="4" fill="#2a3040"/>
<circle cx="290" cy="162" r="4" fill="#2a3040"/>
<circle cx="306" cy="162" r="4" fill="#2a3040"/>
<circle cx="322" cy="162" r="4" fill="#2a3040"/>
<circle cx="338" cy="162" r="4" fill="#2a3040"/>
<circle cx="354" cy="162" r="4" fill="#2a3040"/>
<circle cx="370" cy="162" r="4" fill="#2a3040"/>
<circle cx="386" cy="162" r="4" fill="#2a3040"/>
<circle cx="402" cy="162" r="4" fill="#2a3040"/>
<circle cx="418" cy="162" r="4" fill="#2a3040"/>
<circle cx="434" cy="162" r="4" fill="#2a3040"/>
<circle cx="450" cy="162" r="4" fill="#2a3040"/>
<circle cx="466" cy="162" r="4" fill="#2a3040"/>
<circle cx="482" cy="162" r="4" fill="#2a3040"/>
<circle cx="498" cy="162" r="4" fill="#2a3040"/>
<circle cx="514" cy="162" r="4" fill="#2a3040"/>
<circle cx="530" cy="162" r="4" fill="#2a3040"/>
<circle cx="546" cy="162" r="4" fill="#2a3040"/>
<circle cx="562" cy="162" r="4" fill="#2a3040"/>
<circle cx="578" cy="162" r="4" fill="#2a3040"/>
<circle cx="594" cy="162" r="4" fill="#2a3040"/>
<circle cx="610" cy="162" r="4" fill="#2a3040"/>
<circle cx="50" cy="178" r="4" fill="#2a3040"/>
<circle cx="66" cy="178" r="4" fill="#2a3040"/>
<circle cx="82" cy="178" r="4" fill="#2a3040"/>
<circle cx="98" cy="178" r="4" fill="#2a3040"/>
<circle cx="114" cy="178" r="4" fill="#2a3040"/>
<circle cx="130" cy="178" r="4" fill="#2a3040"/>
<circle cx="146" cy="178" r="4" fill="#2a3040"/>
<circle cx="162" cy="178" r="4" fill="#2a3040"/>
<circle cx="178" cy="178" r="4" fill="#2a3040"/>
<circle cx="194" cy="178" r="4" fill="#2a3040"/>
<circle cx="210" cy="178" r="4" fill="#2a3040"/>
<circle cx="226" cy="178" r="4" fill="#2a3040"/>
<circle cx="242" cy="178" r="4" fill="#2a3040"/>
<circle cx="258" cy="178" r="4" fill="#2a3040"/>
<circle cx="274" cy="178" r="4" fill="#2a3040"/>
<circle cx="290" cy="178" r="4" fill="#2a3040"/>
<circle cx="306" cy="178" r="4" fill="#2a3040"/>
<circle cx="322" cy="178" r="4" fill="#2a3040"/>
<circle cx="338" cy="178" r="4" fill="#2a3040"/>
<circle cx="354" cy="178" r="4" fill="#2a3040"/>
<circle cx="370" cy="178" r="4" fill="#2a3040"/>
<circle cx="386" cy="178" r="4" fill="#2a3040"/>
<circle cx="402" cy="178" r="4" fill="#2a3040"/>
<circle cx="418" cy="178" r="4" fill="#2a3040"/>
<circle cx="434" cy="178" r="4" fill="#2a3040"/>
<circle cx="450" cy="178" r="4" fill="#2a3040"/>
<circle cx="466" cy="178" r="4" fill="#2a3040"/>
<circle cx="482" cy="178" r="4" fill="#2a3040"/>
<circle cx="498" cy="178" r="4" fill="#2a3040"/>
<circle cx="514" cy="178" r="4" fill="#2a3040"/>
<circle cx="530" cy="178" r="4" fill="#2a3040"/>
<circle cx="546" cy="178" r="4" fill="#2a3040"/>
<circle cx="562" cy="178" r="4" fill="#2a3040"/>
<circle cx="578" cy="178" r="4" fill="#2a3040"/>
<circle cx="594" cy="178" r="4" fill="#2a3040"/>
<circle cx="610" cy="178" r="4" fill="#2a3040"/>
<circle cx="50" cy="194" r="4" fill="#2a3040"/>
<circle cx="66" cy="194" r="4" fill="#2a3040"/>
<circle cx="82" cy="194" r="4" fill="#2a3040"/>
<circle cx="98" cy="194" r="4" fill="#2a3040"/>
<circle cx="114" cy="194" r="4" fill="#2a3040"/>
<circle cx="130" cy="194" r="4" fill="#2a3040"/>
<circle cx="146" cy="194" r="4" fill="#2a3040"/>
<circle cx="162" cy="194" r="4" fill="#2a3040"/>
<circle cx="178" cy="194" r="4" fill="#2a3040"/>
<circle cx="194" cy="194" r="4" fill="#2a3040"/>
<circle cx="210" cy="194" r="4" fill="#2a3040"/>
<circle cx="226" cy="194" r="4" fill="#2a3040"/>
<circle cx="242" cy="194" r="4" fill="#2a3040"/>
<circle cx="258" cy="194" r="4" fill="#2a3040"/>
<circle cx="274" cy="194" r="4" fill="#2a3040"/>
<circle cx="290" cy="194" r="4" fill="#2a3040"/>
<circle cx="306" cy="194" r="4" fill="#2a3040"/>
<circle cx="322" cy="194" r="4" fill="#2a3040"/>
<circle cx="338" cy="194" r="4" fill="#2a3040"/>
<circle cx="354" cy="194" r="4" fill="#2a3040"/>
<circle cx="370" cy="194" r="4" fill="#2a3040"/>
<circle cx="386" cy="194" r="4" fill="#2a3040"/>
<circle cx="402" cy="194" r="4" fill="#2a3040"/>
<circle cx="418" cy="194" r="4" fill="#2a3040"/>
<circle cx="434" cy="194" r="4" fill="#2a3040"/>
<circle cx="450" cy="194" r="4" fill="#2a3040"/>
<circle cx="466" cy="194" r="4" fill="#2a3040"/>
<circle cx="482" cy="194" r="4" fill="#2a3040"/>
<circle cx="498" cy="194" r="4" fill="#2a3040"/>
<circle cx="514" cy="194" r="4" fill="#2a3040"/>
<circle cx="530" cy="194" r="4" fill="#2a3040"/>
<circle cx="546" cy="194" r="4" fill="#2a3040"/>
<circle cx="562" cy="194" r="4" fill="#2a3040"/>
<circle cx="578" cy="194" r="4" fill="#2a3040"/>
<circle cx="594" cy="194" r="4" fill="#2a3040"/>
<circle cx="610" cy="194" r="4" fill="#2a3040"/>
<circle cx="50" cy="210" r="4" fill="#2a3040"/>
<circle cx="66" cy="210" r="4" fill="#2a3040"/>
<circle cx="82" cy="210" r="4" fill="#2a3040"/>
<circle cx="98" cy="210" r="4" fill="#2a3040"/>
<circle cx="114" cy="210" r="4" fill="#2a3040"/>
<circle cx="130" cy="210" r="4" fill="#2a3040"/>
<circle cx="146" cy="210" r="4" fill="#2a3040"/>
<circle cx="162" cy="210" r="4" fill="#2a3040"/>
<circle cx="178" cy="210" r="4" fill="#2a3040"/>
<circle cx="194" cy="210" r="4" fill="#2a3040"/>
<circle cx="210" cy="210" r="4" fill="#2a3040"/>
<circle cx="226" cy="210" r="4" fill="#2a3040"/>
<circle cx="242" cy="210" r="4" fill="#2a3040"/>
<circle cx="258" cy="210" r="4" fill="#2a3040"/>
<circle cx="274" cy="210" r="4" fill="#2a3040"/>
<circle cx="290" cy="210" r="4" fill="#2a3040"/>
<circle cx="306" cy="210" r="4" fill="#2a3040"/>
<circle cx="322" cy="210" r="4" fill="#2a3040"/>
<circle cx="338" cy="210" r="4" fill="#2a3040"/>
<circle cx="354" cy="210" r="4" fill="#2a3040"/>
<circle cx="370" cy="210" r="4" fill="#2a3040"/>
<circle cx="386" cy="210" r="4" fill="#2a3040"/>
<circle cx="402" cy="210" r="4" fill="#2a3040"/>
<circle cx="418" cy="210" r="4" fill="#2a3040"/>
<circle cx="434" cy="210" r="4" fill="#2a3040"/>
<circle cx="450" cy="210" r="4" fill="#2a3040"/>
<circle cx="466" cy="210" r="4" fill="#2a3040"/>
<circle cx="482" cy="210" r="4" fill="#2a3040"/>
<circle cx="498" cy="210" r="4" fill="#2a3040"/>
<circle cx="514" cy="210" r="4" fill="#2a3040"/>
<circle cx="530" cy="210" r="4" fill="#2a3040"/>
<circle cx="546" cy="210" r="4" fill="#2a3040"/>
<circle cx="562" cy="210" r="4" fill="#2a3040"/>
<circle cx="578" cy="210" r="4" fill="#2a3040"/>
<circle cx="594" cy="210" r="4" fill="#2a3040"/>
<circle cx="610" cy="210" r="4" fill="#2a3040"/>
<circle cx="50" cy="226" r="4" fill="#2a3040"/>
<circle cx="66" cy="226" r="4" fill="#2a3040"/>
<circle cx="82" cy="226" r="4" fill="#2a3040"/>
<circle cx="98" cy="226" r="4" fill="#2a3040"/>
<circle cx="114" cy="226" r="4" fill="#2a3040"/>
<circle cx="130" cy="226" r="4" fill="#2a3040"/>
<circle cx="146" cy="226" r="4" fill="#2a3040"/>
<circle cx="162" cy="226" r="4" fill="#2a3040"/>
<circle cx="178" cy="226" r="4" fill="#2a3040"/>
<circle cx="194" cy="226" r="4" fill="#2a3040"/>
<circle cx="210" cy="226" r="4" fill="#2a3040"/>
<circle cx="226" cy="226" r="4" fill="#2a3040"/>
<circle cx="242" cy="226" r="4" fill="#2a3040"/>
<circle cx="258" cy="226" r="4" fill="#2a3040"/>
<circle cx="274" cy="226" r="4" fill="#2a3040"/>
<circle cx="290" cy="226" r="4" fill="#2a3040"/>
<circle cx="306" cy="226" r="4" fill="#2a3040"/>
<circle cx="322" cy="226" r="4" fill="#2a3040"/>
<circle cx="338" cy="226" r="4" fill="#2a3040"/>
<circle cx="354" cy="226" r="4" fill="#2a3040"/>
<circle cx="370" cy="226" r="4" fill="#2a3040"/>
<circle cx="386" cy="226" r="4" fill="#2a3040"/>
<circle cx="402" cy="226" r="4" fill="#2a3040"/>
<circle cx="418" cy="226" r="4" fill="#2a3040"/>
<circle cx="434" cy="226" r="4" fill="#2a3040"/>
<circle cx="450" cy="226" r="4" fill="#2a3040"/>
<circle cx="466" cy="226" r="4" fill="#2a3040"/>
<circle cx="482" cy="226" r="4" fill="#2a3040"/>
<circle cx="498" cy="226" r="4" fill="#2a3040"/>
<circle cx="514" cy="226" r="4" fill="#2a3040"/>
<circle cx="530" cy="226" r="4" fill="#2a3040"/>
<circle cx="546" cy="226" r="4" fill="#2a3040"/>
<circle cx="562" cy="226" r="4" fill="#2a3040"/>
<circle cx="578" cy="226" r="4" fill="#2a3040"/>
<circle cx="594" cy="226" r="4" fill="#2a3040"/>
<circle cx="610" cy="226" r="4" fill="#2a3040"/>
<circle cx="50" cy="242" r="4" fill="#2a3040"/>
<circle cx="66" cy="242" r="4" fill="#2a3040"/>
<circle cx="82" cy="242" r="4" fill="#2a3040"/>
<circle cx="98" cy="242" r="4" fill="#2a3040"/>
<circle cx="114" cy="242" r="4" fill="#2a3040"/>
<circle cx="130" cy="242" r="4" fill="#2a3040"/>
<circle cx="146" cy="242" r="4" fill="#2a3040"/>
<circle cx="162" cy="242" r="4" fill="#2a3040"/>
<circle cx="178" cy="242" r="4" fill="#2a3040"/>
<circle cx="194" cy="242" r="4" fill="#2a3040"/>
<circle cx="210" cy="242" r="4" fill="#2a3040"/>
<circle cx="226" cy="242" r="4" fill="#2a3040"/>
<circle cx="242" cy="242" r="4" fill="#2a3040"/>
<circle cx="258" cy="242" r="4" fill="#2a3040"/>
<circle cx="274" cy="242" r="4" fill="#2a3040"/>
<circle cx="290" cy="242" r="4" fill="#2a3040"/>
<circle cx="306" cy="242" r="4" fill="#2a3040"/>
<circle cx="322" cy="242" r="4" fill="#2a3040"/>
<circle cx="338" cy="242" r="4" fill="#2a3040"/>
<circle cx="354" cy="242" r="4" fill="#2a3040"/>
<circle cx="370" cy="242" r="4" fill="#2a3040"/>
<circle cx="386" cy="242" r="4" fill="#2a3040"/>
<circle cx="402" cy="242" r="4" fill="#2a3040"/>
<circle cx="418" cy="242" r="4" fill="#2a3040"/>
<circle cx="434" cy="242" r="4" fill="#2a3040"/>
<circle cx="450" cy="242" r="4" fill="#2a3040"/>
<circle cx="466" cy="242" r="4" fill="#2a3040"/>
<circle cx="482" cy="242" r="4" fill="#2a3040"/>
<circle cx="498" cy="242" r="4" fill="#2a3040"/>
<circle cx="514" cy="242" r="4" fill="#2a3040"/>
<circle cx="530" cy="242" r="4" fill="#2a3040"/>
<circle cx="546" cy="242" r="4" fill="#2a3040"/>
<circle cx="562" cy="242" r="4" fill="#2a3040"/>
<circle cx="578" cy="242" r="4" fill="#2a3040"/>
<circle cx="594" cy="242" r="4" fill="#2a3040"/>
<circle cx="610" cy="242" r="4" fill="#2a3040"/>
<circle cx="50" cy="258" r="4" fill="#2a3040"/>
<circle cx="66" cy="258" r="4" fill="#2a3040"/>
<circle cx="82" cy="258" r="4" fill="#2a3040"/>
<circle cx="98" cy="258" r="4" fill="#2a3040"/>
<circle cx="114" cy="258" r="4" fill="#2a3040"/>
<circle cx="130" cy="258" r="4" fill="#2a3040"/>
<circle cx="146" cy="258" r="4" fill="#2a3040"/>
<circle cx="162" cy="258" r="4" fill="#2a3040"/>
<circle cx="178" cy="258" r="4" fill="#2a3040"/>
<circle cx="194" cy="258" r="4" fill="#2a3040"/>
<circle cx="210" cy="258" r="4" fill="#2a3040"/>
<circle cx="226" cy="258" r="4" fill="#2a3040"/>
<circle cx="242" cy="258" r="4" fill="#2a3040"/>
<circle cx="258" cy="258" r="4" fill="#2a3040"/>
<circle cx="274" cy="258" r="4" fill="#2a3040"/>
<circle cx="290" cy="258" r="4" fill="#2a3040"/>
<circle cx="306" cy="258" r="4" fill="#2a3040"/>
<circle cx="322" cy="258" r="4" fill="#2a3040"/>
<circle cx="338" cy="258" r="4" fill="#2a3040"/>
<circle cx="354" cy="258" r="4" fill="#2a3040"/>
<circle cx="370" cy="258" r="4" fill="#2a3040"/>
<circle cx="386" cy="258" r="4" fill="#2a3040"/>
<circle cx="402" cy="258" r="4" fill="#2a3040"/>
<circle cx="418" cy="258" r="4" fill="#2a3040"/>
<circle cx="434" cy="258" r="4" fill="#2a3040"/>
<circle cx="450" cy="258" r="4" fill="#2a3040"/>
<circle cx="466" cy="258" r="4" fill="#2a3040"/>
<circle cx="482" cy="258" r="4" fill="#2a3040"/>
<circle cx="498" cy="258" r="4" fill="#2a3040"/>
<circle cx="514" cy="258" r="4" fill="#2a3040"/>
<circle cx="530" cy="258" r="4" fill="#2a3040"/>
<circle cx="546" cy="258" r="4" fill="#2a3040"/>
<circle cx="562" cy="258" r="4" fill="#2a3040"/>
<circle cx="578" cy="258" r="4" fill="#2a3040"/>
<circle cx="594" cy="258" r="4" fill="#2a3040"/>
<circle cx="610" cy="258" r="4" fill="#2a3040"/>
<circle cx="50" cy="274" r="4" fill="#2a3040"/>
<circle cx="66" cy="274" r="4" fill="#2a3040"/>
<circle cx="82" cy="274" r="4" fill="#2a3040"/>
<circle cx="98" cy="274" r="4" fill="#2a3040"/>
<circle cx="114" cy="274" r="4" fill="#2a3040"/>
<circle cx="130" cy="274" r="4" fill="#2a3040"/>
<circle cx="146" cy="274" r="4" fill="#2a3040"/>
<circle cx="162" cy="274" r="4" fill="#2a3040"/>
<circle cx="178" cy="274" r="4" fill="#2a3040"/>
<circle cx="194" cy="274" r="4" fill="#2a3040"/>
<circle cx="210" cy="274" r="4" fill="#2a3040"/>
<circle cx="226" cy="274" r="4" fill="#2a3040"/>
<circle cx="242" cy="274" r="4" fill="#2a3040"/>
<circle cx="258" cy="274" r="4" fill="#2a3040"/>
<circle cx="274" cy="274" r="4" fill="#2a3040"/>
<circle cx="290" cy="274" r="4" fill="#2a3040"/>
<circle cx="306" cy="274" r="4" fill="#2a3040"/>
<circle cx="322" cy="274" r="4" fill="#2a3040"/>
<circle cx="338" cy="274" r="4" fill="#2a3040"/>
<circle cx="354" cy="274" r="4" fill="#2a3040"/>
<circle cx="370" cy="274" r="4" fill="#2a3040"/>
<circle cx="386" cy="274" r="4" fill="#2a3040"/>
<circle cx="402" cy="274" r="4" fill="#2a3040"/>
<circle cx="418" cy="274" r="4" fill="#2a3040"/>
<circle cx="434" cy="274" r="4" fill="#2a3040"/>
<circle cx="450" cy="274" r="4" fill="#2a3040"/>
<circle cx="466" cy="274" r="4" fill="#2a3040"/>
<circle cx="482" cy="274" r="4" fill="#2a3040"/>
<circle cx="498" cy="274" r="4" fill="#2a3040"/>
<circle cx="514" cy="274" r="4" fill="#2a3040"/>
<circle cx="530" cy="274" r="4" fill="#2a3040"/>
<circle cx="546" cy="274" r="4" fill="#2a3040"/>
<circle cx="562" cy="274" r="4" fill="#2a3040"/>
<circle cx="578" cy="274" r="4" fill="#2a3040"/>
<circle cx="594" cy="274" r="4" fill="#2a3040"/>
<circle cx="610" cy="274" r="4" fill="#2a3040"/>
<circle cx="50" cy="290" r="4" fill="#2a3040"/>
<circle cx="66" cy="290" r="4" fill="#2a3040"/>
<circle cx="82" cy="290" r="4" fill="#2a3040"/>
<circle cx="98" cy="290" r="4" fill="#2a3040"/>
<circle cx="114" cy="290" r="4" fill="#2a3040"/>
<circle cx="130" cy="290" r="4" fill="#2a3040"/>
<circle cx="146" cy="290" r="4" fill="#2a3040"/>
<circle cx="162" cy="290" r="4" fill="#2a3040"/>
<circle cx="178" cy="290" r="4" fill="#2a3040"/>
<circle cx="194" cy="290" r="4" fill="#2a3040"/>
<circle cx="210" cy="290" r="4" fill="#2a3040"/>
<circle cx="226" cy="290" r="4" fill="#2a3040"/>
<circle cx="242" cy="290" r="4" fill="#2a3040"/>
<circle cx="258" cy="290" r="4" fill="#2a3040"/>
<circle cx="274" cy="290" r="4" fill="#2a3040"/>
<circle cx="290" cy="290" r="4" fill="#2a3040"/>
<circle cx="306" cy="290" r="4" fill="#2a3040"/>
<circle cx="322" cy="290" r="4" fill="#2a3040"/>
<circle cx="338" cy="290" r="4" fill="#2a3040"/>
<circle cx="354" cy="290" r="4" fill="#2a3040"/>
<circle cx="370" cy="290" r="4" fill="#2a3040"/>
<circle cx="386" cy="290" r="4" fill="#2a3040"/>
<circle cx="402" cy="290" r="4" fill="#2a3040"/>
<circle cx="418" cy="290" r="4" fill="#2a3040"/>
<circle cx="434" cy="290" r="4" fill="#2a3040"/>
<circle cx="450" cy="290" r="4" fill="#2a3040"/>
<circle cx="466" cy="290" r="4" fill="#2a3040"/>
<circle cx="482" cy="290" r="4" fill="#2a3040"/>
<circle cx="498" cy="290" r="4" fill="#2a3040"/>
<circle cx="514" cy="290" r="4" fill="#2a3040"/>
<circle cx="530" cy="290" r="4" fill="#2a3040"/>
<circle cx="546" cy="290" r="4" fill="#2a3040"/>
<circle cx="562" cy="290" r="4" fill="#2a3040"/>
<circle cx="578" cy="290" r="4" fill="#2a3040"/>
<circle cx="594" cy="290" r="4" fill="#2a3040"/>
<circle cx="610" cy="290" r="4" fill="#2a3040"/>
<circle cx="50" cy="306" r="4" fill="#2a3040"/>
<circle cx="66" cy="306" r="4" fill="#2a3040"/>
<circle cx="82" cy="306" r="4" fill="#2a3040"/>
<circle cx="98" cy="306" r="4" fill="#2a3040"/>
<circle cx="114" cy="306" r="4" fill="#2a3040"/>
<circle cx="130" cy="306" r="4" fill="#2a3040"/>
<circle cx="146" cy="306" r="4" fill="#2a3040"/>
<circle cx="162" cy="306" r="4" fill="#2a3040"/>
</svg>
<!-- ===== END E3 ===== -->

<!-- ===== BEGIN E4 modality-bars ===== -->
<svg viewBox="0 0 1100 400" width="1100" xmlns="http://www.w3.org/2000/svg">
<text x="235" y="65" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">(none declared)</text>
<rect x="250" y="50" width="400" height="20" fill="#2a3040" rx="2"/>
<text x="660" y="65" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">2,506</text>
<text x="235" y="105" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">image-text-to-text</text>
<rect x="250" y="90" width="249" height="20" fill="#4f8cff" rx="2" class="e4-highlight"/>
<text x="509" y="105" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">1,562</text>
<path d="M 559 100 L 579 100" fill="none" stroke="#4f8cff" stroke-width="1" stroke-dasharray="4 4"/>
<text x="589" y="104" fill="#4f8cff" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">vision-language models are the single largest declared category</text>
<text x="589" y="120" fill="#4f8cff" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">— ahead of text generation</text>
<text x="235" y="145" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">text-generation</text>
<rect x="250" y="130" width="245" height="20" fill="#2a3040" rx="2"/>
<text x="505" y="145" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">1,541</text>
<text x="235" y="185" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">any-to-any</text>
<rect x="250" y="170" width="30" height="20" fill="#2a3040" rx="2"/>
<text x="290" y="185" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">193</text>
<text x="235" y="225" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">automatic-speech-recognition</text>
<rect x="250" y="210" width="2" height="20" fill="#2a3040" rx="2"/>
<text x="262" y="225" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">10</text>
<text x="235" y="265" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">translation</text>
<rect x="250" y="250" width="2" height="20" fill="#2a3040" rx="2"/>
<text x="262" y="265" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">10</text>
<text x="235" y="305" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">question-answering</text>
<rect x="250" y="290" width="2" height="20" fill="#2a3040" rx="2"/>
<text x="262" y="305" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">6</text>
<text x="235" y="345" fill="#e6e9f0" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12" text-anchor="end">image-text-to-image</text>
<rect x="250" y="330" width="2" height="20" fill="#2a3040" rx="2"/>
<text x="262" y="345" fill="#9aa3b8" font-family="'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="12">5</text>
</svg>
<!-- ===== END E4 ===== -->

<!-- ===== BEGIN CSS ===== -->
.e2-title{fill:#9aa3b8;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:13px;letter-spacing:.1em;text-transform:uppercase}
.e2-track{stroke:#2a3040;stroke-width:4;stroke-linecap:round}
.e2-node{fill:#171a23;stroke:#4f8cff;stroke-width:2}
.e2-node-last{stroke:#f87171}
.e2-hop{fill:#e6e9f0;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:12px}
.e2-count{fill:#4ade80;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:13px;font-weight:700}
.e2-chip-live{fill:rgba(74,222,128,.12);stroke:#4ade80;stroke-width:1}
.e2-chip-dead{fill:rgba(154,163,184,.10);stroke:#9aa3b8;stroke-width:1}
.e2-chip-txt{fill:#4ade80;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:11px}
.e2-chip-txt-dead{fill:#9aa3b8;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:11px}
.e2-ghost-box{fill:rgba(248,113,113,.08);stroke:#f87171;stroke-width:1;stroke-dasharray:3 2}
.e2-ghost-txt{fill:#f87171;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:11px}
.e2-ghost{opacity:.5;animation:e2-bob 5s ease-in-out infinite}
@keyframes e2-bob{0%,100%{opacity:.5;transform:translateY(0)}50%{opacity:.26;transform:translateY(7px)}}
.e2-lost{fill:#f87171;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:12px;opacity:.75}
.e2-end-box{fill:#171a23;stroke:#2a3040;stroke-width:1}
.e2-end-txt{fill:#e6e9f0;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:12px}
.e2-end-cap{fill:#f87171;font-family:'JetBrains Mono','SF Mono',Menlo,monospace;font-size:12px}
@media (prefers-reduced-motion: reduce){.e2-ghost{animation:none}}
/* all @keyframes + classes for E1-E4 */
@media (prefers-reduced-motion: no-preference) {
  /* E1 */
  .e1-pulse {
    animation: e1-pulse-anim 2s infinite alternate ease-in-out;
  }
  @keyframes e1-pulse-anim {
    0% { stroke: #ff7043; stroke-width: 2px; }
    100% { stroke: #ff9e80; stroke-width: 3px; }
  }
  .e1-dot {
    offset-distance: 0%;
    animation: e1-flow 2s linear infinite;
  }
  @keyframes e1-flow {
    0% { offset-distance: 0%; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { offset-distance: 100%; opacity: 0; }
  }
  .e1-dot-1 { offset-path: path('M 120 200 L 150 200'); }
  .e1-dot-2 { offset-path: path('M 280 200 L 310 200'); }
  .e1-dot-3a { offset-path: path('M 480 190 C 495 190, 495 110, 510 110'); }
  .e1-dot-4a { offset-path: path('M 670 110 L 700 110'); }
  .e1-dot-5a { offset-path: path('M 830 110 L 860 110'); }
  .e1-dot-3b { offset-path: path('M 480 210 C 495 210, 495 290, 510 290'); }
  .e1-dot-4b { offset-path: path('M 670 290 L 700 290'); }
  .e1-dot-5b { offset-path: path('M 830 290 L 860 290'); }
  .e1-dot-6b { offset-path: path('M 990 290 L 1020 290'); }

  /* E3 */
  .e3-pulse {
    animation: e3-pulse-anim 2s infinite alternate ease-in-out;
  }
  @keyframes e3-pulse-anim {
    0% { opacity: 0.6; filter: drop-shadow(0 0 2px rgba(74,222,128,0.2)); }
    100% { opacity: 1; filter: drop-shadow(0 0 6px rgba(74,222,128,0.8)); }
  }

  /* E4 */
  .e4-highlight {
    animation: e4-shimmer 3s infinite linear;
  }
  @keyframes e4-shimmer {
    0% { filter: brightness(1); }
    50% { filter: brightness(1.3) drop-shadow(0 0 4px rgba(79,140,255,0.5)); }
    100% { filter: brightness(1); }
  }
}
<!-- ===== END CSS ===== -->
