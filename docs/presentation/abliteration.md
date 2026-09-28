---
marp: true
theme: wellspring
paginate: true
size: 16:9
transition: fade 250ms
header: 'Abliteration in Practice'
footer: 'Wellspring · Heretic → MLX/GGUF'
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Abliteration in Practice

## Removing refusal from open-weight models — and why the chain of custody matters more than the technique

<div class="meta">

Arditi et al. 2024 (arXiv:2406.11717v3, NeurIPS) · Heretic v1.4.0 · Wellspring<br>
Hugging Face figures measured live via the HF API, September 2026

</div>

<!--
OPENING — 60 seconds, no slides needed.

Ask the room: "Who here has downloaded a model off Hugging Face and run it
locally?" Most hands. "Who checked what commit it was built from?" Almost none.

That gap is the talk. Abliteration is the worked example, not the subject.

Set expectations explicitly so nobody thinks this is a jailbreaking tutorial:
we're going to cover how refusal removal actually works mathematically, the
tool that automated it, and then spend the back half on the part that
actually matters — proving what is in a set of weights.

Housekeeping: every Hugging Face number was measured against the live API
this morning. The script is in the appendix. Don't trust me, re-run it.
-->

---

<!-- _class: number -->
<!-- _transition: zoom 450ms -->
<!-- _header: '' -->

<div class="huge">5,844 <em>/</em> 158</div>

<div class="sub">

models on Hugging Face built with Heretic<br>
— and the number that can **prove how they were made**

</div>

<!--
THE HOOK. Let this sit in silence for a beat before speaking.

5,844 models carry the `heretic` tag. 158 ship a reproduce.json — the file
that records the base model commit, the seed, the winning trial, the package
versions, and a SHA-256 of every output shard.

That is 2.7%.

Say plainly: "Everything else in this talk is context for that ratio."

Do NOT explain reproduce.json yet — that's Part 6. Right now they only need
the shape of the problem: a very large number of published artifacts, a very
small number of verifiable ones.

If someone asks "is 158 low because the feature is new?" — good question,
park it, we cover it at the dot-grid slide: 186 repos actively claim to be
reproducible while shipping nothing.
-->

---

<!-- _class: lite -->

# Two halves

<div class="cols">
<div>

### The technique
How refusal is removed
Why people do it
The tool that automated it

</div>
<div>

### The consequence
What is on the Hub
What survives the pipeline
What "it works" has to mean

</div>
</div>

<!--
ROADMAP — 30 seconds. Don't read it out.

Just signal the shape: first half is mechanism, second half is supply chain.
Tell them the second half is the part you care about, and the first half
exists so the second half lands.

Flag the demo: there is a live terminal segment around the halfway mark.
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 1</div>

# What it is

## Refusal is one direction. You can subtract it.

---

<!-- _class: lite -->

# The finding

> "refusal is mediated by a **one-dimensional subspace**, across 13 popular open-source chat models up to 72B parameters"

**Arditi et al.**, NeurIPS 2024 — arXiv:2406.11717v3

<!--
THE PAPER — 90 seconds.

Read the quote out loud. The precise phrase is "one-dimensional subspace" —
not a neuron, not a layer. One direction in the residual stream.

The 13 models: Qwen 1.8B through 72B, Yi 6B/34B, Gemma 2B/7B, Llama-2
7B/13B/70B, Llama-3 8B/70B. Evaluated on JailbreakBench — 100 harmful
instructions.

The finding is bidirectional and that's what makes it strong:
  - ERASE the direction and the model stops refusing harmful prompts
  - ADD the direction and it starts refusing HARMLESS ones
Necessary AND sufficient. That's a real mechanistic claim, not a correlation.

The authors' own closing line — worth quoting verbatim: "Our findings
underscore the brittleness of current safety fine-tuning methods."

Provenance aside, if the room is that kind of room: this repo pins the paper
to v3 specifically. arXiv has no commit hashes, so the version suffix IS the
pin. `make paper` fetches it and writes a tracked manifest with a SHA-256,
but git-ignores the PDF because arXiv's licence grants no redistribution
right. That discipline is the whole back half of the talk in miniature.
-->

---

<!-- _class: figure -->

# What the refusal direction looks like

<svg viewBox="0 0 1050 420" width="1050" xmlns="http://www.w3.org/2000/svg">
<defs>
<marker id="d1-arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
<polygon points="0 0, 8 3, 0 6" fill="#fbbf24" />
</marker>
</defs>
<circle cx="371.3" cy="203.8" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="425.6" cy="319.7" r="4" class="d1-dot-blue" style="animation-delay: -1.7s" />
<circle cx="433.2" cy="197.6" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="479.7" cy="223.5" r="4" class="d1-dot-blue" style="animation-delay: -1.3s" />
<circle cx="475.4" cy="222.2" r="4" class="d1-dot-blue" style="animation-delay: -1.6s" />
<circle cx="301.9" cy="202.2" r="4" class="d1-dot-blue" style="animation-delay: -1.5s" />
<circle cx="395.4" cy="208.1" r="4" class="d1-dot-blue" style="animation-delay: -2.0s" />
<circle cx="352.0" cy="158.8" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="503.5" cy="199.4" r="4" class="d1-dot-blue" style="animation-delay: -0.2s" />
<circle cx="597.0" cy="287.0" r="4" class="d1-dot-blue" style="animation-delay: -1.5s" />
<circle cx="463.9" cy="116.6" r="4" class="d1-dot-blue" style="animation-delay: -1.3s" />
<circle cx="515.0" cy="204.3" r="4" class="d1-dot-blue" style="animation-delay: -1.4s" />
<circle cx="476.4" cy="135.8" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="210.5" cy="167.6" r="4" class="d1-dot-blue" style="animation-delay: -0.1s" />
<circle cx="404.9" cy="268.2" r="4" class="d1-dot-blue" style="animation-delay: -0.2s" />
<circle cx="396.5" cy="244.8" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="308.5" cy="168.4" r="4" class="d1-dot-blue" style="animation-delay: -0.9s" />
<circle cx="415.8" cy="264.6" r="4" class="d1-dot-blue" style="animation-delay: -2.3s" />
<circle cx="283.5" cy="143.6" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="379.8" cy="176.5" r="4" class="d1-dot-blue" style="animation-delay: -0.9s" />
<circle cx="575.4" cy="208.9" r="4" class="d1-dot-blue" style="animation-delay: -1.4s" />
<circle cx="290.1" cy="100.4" r="4" class="d1-dot-blue" style="animation-delay: -1.9s" />
<circle cx="394.4" cy="231.5" r="4" class="d1-dot-blue" style="animation-delay: -0.8s" />
<circle cx="380.0" cy="259.5" r="4" class="d1-dot-blue" style="animation-delay: -2.4s" />
<circle cx="470.6" cy="175.4" r="4" class="d1-dot-blue" style="animation-delay: -1.6s" />
<circle cx="161.5" cy="302.9" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="380.9" cy="263.7" r="4" class="d1-dot-blue" style="animation-delay: -1.4s" />
<circle cx="376.2" cy="300.9" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="316.2" cy="242.0" r="4" class="d1-dot-blue" style="animation-delay: -2.5s" />
<circle cx="333.3" cy="213.3" r="4" class="d1-dot-blue" style="animation-delay: -0.1s" />
<circle cx="531.0" cy="273.1" r="4" class="d1-dot-blue" style="animation-delay: -2.0s" />
<circle cx="348.4" cy="226.1" r="4" class="d1-dot-blue" style="animation-delay: -1.0s" />
<circle cx="549.5" cy="213.1" r="4" class="d1-dot-blue" style="animation-delay: -2.4s" />
<circle cx="402.7" cy="207.4" r="4" class="d1-dot-blue" style="animation-delay: -1.8s" />
<circle cx="322.9" cy="141.7" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="350.0" cy="190.5" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="120.0" cy="261.2" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="377.1" cy="291.3" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="614.2" cy="146.4" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="275.5" cy="146.7" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="402.7" cy="134.3" r="4" class="d1-dot-blue" style="animation-delay: -1.9s" />
<circle cx="385.7" cy="214.6" r="4" class="d1-dot-blue" style="animation-delay: -0.8s" />
<circle cx="680.0" cy="233.3" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="444.7" cy="166.5" r="4" class="d1-dot-blue" style="animation-delay: -0.1s" />
<circle cx="616.9" cy="105.7" r="4" class="d1-dot-blue" style="animation-delay: -0.2s" />
<circle cx="341.0" cy="217.2" r="4" class="d1-dot-blue" style="animation-delay: -1.9s" />
<circle cx="396.8" cy="181.1" r="4" class="d1-dot-blue" style="animation-delay: -1.2s" />
<circle cx="292.9" cy="199.3" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="310.6" cy="235.8" r="4" class="d1-dot-blue" style="animation-delay: -1.3s" />
<circle cx="379.0" cy="171.8" r="4" class="d1-dot-blue" style="animation-delay: -0.8s" />
<circle cx="578.3" cy="212.1" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="324.4" cy="211.4" r="4" class="d1-dot-blue" style="animation-delay: -0.6s" />
<circle cx="299.0" cy="288.7" r="4" class="d1-dot-blue" style="animation-delay: -0.6s" />
<circle cx="399.3" cy="239.5" r="4" class="d1-dot-blue" style="animation-delay: -1.6s" />
<circle cx="427.2" cy="354.9" r="4" class="d1-dot-blue" style="animation-delay: -2.1s" />
<circle cx="476.5" cy="235.6" r="4" class="d1-dot-blue" style="animation-delay: -1.7s" />
<circle cx="405.4" cy="248.8" r="4" class="d1-dot-blue" style="animation-delay: -2.3s" />
<circle cx="257.3" cy="183.3" r="4" class="d1-dot-blue" style="animation-delay: -2.0s" />
<circle cx="419.9" cy="175.5" r="4" class="d1-dot-blue" style="animation-delay: -0.2s" />
<circle cx="266.1" cy="243.6" r="4" class="d1-dot-blue" style="animation-delay: -1.2s" />
<circle cx="364.5" cy="118.6" r="4" class="d1-dot-blue" style="animation-delay: -2.5s" />
<circle cx="497.5" cy="253.3" r="4" class="d1-dot-blue" style="animation-delay: -0.8s" />
<circle cx="453.5" cy="177.5" r="4" class="d1-dot-blue" style="animation-delay: -0.5s" />
<circle cx="260.9" cy="236.6" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="390.4" cy="360.0" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="495.8" cy="152.1" r="4" class="d1-dot-blue" style="animation-delay: -0.1s" />
<circle cx="637.2" cy="214.4" r="4" class="d1-dot-blue" style="animation-delay: -2.4s" />
<circle cx="616.1" cy="158.6" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="300.2" cy="219.1" r="4" class="d1-dot-blue" style="animation-delay: -1.0s" />
<circle cx="508.4" cy="237.8" r="4" class="d1-dot-blue" style="animation-delay: -2.5s" />
<circle cx="368.3" cy="328.3" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="120.0" cy="290.9" r="4" class="d1-dot-blue" style="animation-delay: -2.5s" />
<circle cx="195.6" cy="179.5" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="291.0" cy="360.0" r="4" class="d1-dot-blue" style="animation-delay: -1.4s" />
<circle cx="181.7" cy="186.7" r="4" class="d1-dot-blue" style="animation-delay: -0.1s" />
<circle cx="257.3" cy="176.2" r="4" class="d1-dot-blue" style="animation-delay: -2.1s" />
<circle cx="571.8" cy="353.2" r="4" class="d1-dot-blue" style="animation-delay: -0.2s" />
<circle cx="458.6" cy="295.4" r="4" class="d1-dot-blue" style="animation-delay: -1.7s" />
<circle cx="396.1" cy="247.7" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="394.2" cy="302.3" r="4" class="d1-dot-blue" style="animation-delay: -1.5s" />
<circle cx="239.6" cy="256.8" r="4" class="d1-dot-blue" style="animation-delay: -1.3s" />
<circle cx="470.6" cy="197.5" r="4" class="d1-dot-blue" style="animation-delay: -1.8s" />
<circle cx="399.3" cy="280.1" r="4" class="d1-dot-blue" style="animation-delay: -1.7s" />
<circle cx="355.0" cy="268.9" r="4" class="d1-dot-blue" style="animation-delay: -1.9s" />
<circle cx="519.2" cy="246.7" r="4" class="d1-dot-blue" style="animation-delay: -2.5s" />
<circle cx="440.7" cy="214.4" r="4" class="d1-dot-blue" style="animation-delay: -0.5s" />
<circle cx="361.2" cy="360.0" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="480.6" cy="172.1" r="4" class="d1-dot-blue" style="animation-delay: -0.4s" />
<circle cx="491.8" cy="127.4" r="4" class="d1-dot-blue" style="animation-delay: -1.5s" />
<circle cx="578.8" cy="207.4" r="4" class="d1-dot-blue" style="animation-delay: -0.0s" />
<circle cx="434.9" cy="165.0" r="4" class="d1-dot-blue" style="animation-delay: -1.7s" />
<circle cx="454.7" cy="201.9" r="4" class="d1-dot-blue" style="animation-delay: -0.3s" />
<circle cx="519.1" cy="266.4" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="226.5" cy="151.7" r="4" class="d1-dot-blue" style="animation-delay: -0.5s" />
<circle cx="322.3" cy="177.0" r="4" class="d1-dot-blue" style="animation-delay: -1.2s" />
<circle cx="598.3" cy="144.5" r="4" class="d1-dot-blue" style="animation-delay: -0.2s" />
<circle cx="297.2" cy="239.2" r="4" class="d1-dot-blue" style="animation-delay: -0.0s" />
<circle cx="414.5" cy="123.3" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="380.9" cy="132.8" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="441.3" cy="216.6" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="524.4" cy="168.7" r="4" class="d1-dot-blue" style="animation-delay: -2.1s" />
<circle cx="326.1" cy="196.8" r="4" class="d1-dot-blue" style="animation-delay: -0.3s" />
<circle cx="290.4" cy="345.0" r="4" class="d1-dot-blue" style="animation-delay: -2.0s" />
<circle cx="568.4" cy="108.2" r="4" class="d1-dot-blue" style="animation-delay: -0.5s" />
<circle cx="390.2" cy="245.3" r="4" class="d1-dot-blue" style="animation-delay: -2.0s" />
<circle cx="489.1" cy="170.8" r="4" class="d1-dot-blue" style="animation-delay: -1.6s" />
<circle cx="559.2" cy="338.7" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="624.6" cy="197.3" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="599.8" cy="231.5" r="4" class="d1-dot-blue" style="animation-delay: -0.8s" />
<circle cx="602.3" cy="165.7" r="4" class="d1-dot-blue" style="animation-delay: -2.2s" />
<circle cx="428.2" cy="167.5" r="4" class="d1-dot-blue" style="animation-delay: -2.0s" />
<circle cx="595.2" cy="297.8" r="4" class="d1-dot-blue" style="animation-delay: -2.1s" />
<circle cx="431.3" cy="332.9" r="4" class="d1-dot-blue" style="animation-delay: -1.2s" />
<circle cx="311.3" cy="323.9" r="4" class="d1-dot-blue" style="animation-delay: -0.6s" />
<circle cx="474.2" cy="221.3" r="4" class="d1-dot-blue" style="animation-delay: -0.8s" />
<circle cx="613.4" cy="87.3" r="4" class="d1-dot-blue" style="animation-delay: -0.7s" />
<circle cx="307.2" cy="164.0" r="4" class="d1-dot-blue" style="animation-delay: -2.5s" />
<circle cx="120.0" cy="180.3" r="4" class="d1-dot-blue" style="animation-delay: -0.3s" />
<circle cx="470.1" cy="207.5" r="4" class="d1-dot-blue" style="animation-delay: -2.4s" />
<circle cx="384.0" cy="246.0" r="4" class="d1-dot-blue" style="animation-delay: -1.1s" />
<circle cx="399.8" cy="139.1" r="4" class="d1-dot-orange" style="animation-delay: -1.5s" />
<circle cx="287.1" cy="190.4" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="408.9" cy="297.1" r="4" class="d1-dot-orange" style="animation-delay: -0.0s" />
<circle cx="559.3" cy="158.6" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="405.2" cy="98.3" r="4" class="d1-dot-orange" style="animation-delay: -0.9s" />
<circle cx="588.8" cy="235.9" r="4" class="d1-dot-orange" style="animation-delay: -0.8s" />
<circle cx="316.4" cy="311.1" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="380.2" cy="248.1" r="4" class="d1-dot-orange" style="animation-delay: -1.0s" />
<circle cx="326.0" cy="226.3" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="144.1" cy="269.0" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="562.3" cy="143.5" r="4" class="d1-dot-orange" style="animation-delay: -0.8s" />
<circle cx="411.5" cy="194.5" r="4" class="d1-dot-orange" style="animation-delay: -0.7s" />
<circle cx="260.1" cy="231.5" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="277.9" cy="210.3" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="139.3" cy="218.4" r="4" class="d1-dot-orange" style="animation-delay: -2.0s" />
<circle cx="441.5" cy="219.0" r="4" class="d1-dot-orange" style="animation-delay: -1.3s" />
<circle cx="336.2" cy="151.4" r="4" class="d1-dot-orange" style="animation-delay: -2.0s" />
<circle cx="416.4" cy="97.8" r="4" class="d1-dot-orange" style="animation-delay: -0.6s" />
<circle cx="424.1" cy="208.7" r="4" class="d1-dot-orange" style="animation-delay: -0.6s" />
<circle cx="165.0" cy="214.7" r="4" class="d1-dot-orange" style="animation-delay: -0.2s" />
<circle cx="257.6" cy="241.9" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="364.8" cy="123.4" r="4" class="d1-dot-orange" style="animation-delay: -0.6s" />
<circle cx="407.4" cy="189.3" r="4" class="d1-dot-orange" style="animation-delay: -1.9s" />
<circle cx="422.8" cy="164.4" r="4" class="d1-dot-orange" style="animation-delay: -1.1s" />
<circle cx="562.0" cy="341.2" r="4" class="d1-dot-orange" style="animation-delay: -1.3s" />
<circle cx="508.6" cy="210.3" r="4" class="d1-dot-orange" style="animation-delay: -2.1s" />
<circle cx="189.9" cy="226.6" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="589.4" cy="188.4" r="4" class="d1-dot-orange" style="animation-delay: -2.4s" />
<circle cx="554.0" cy="138.6" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="170.2" cy="191.3" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="586.3" cy="130.4" r="4" class="d1-dot-orange" style="animation-delay: -1.2s" />
<circle cx="409.3" cy="243.9" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="430.7" cy="116.5" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="407.0" cy="220.8" r="4" class="d1-dot-orange" style="animation-delay: -0.7s" />
<circle cx="399.5" cy="251.5" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="475.8" cy="231.0" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="402.2" cy="172.2" r="4" class="d1-dot-orange" style="animation-delay: -1.0s" />
<circle cx="285.0" cy="177.2" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="167.8" cy="262.8" r="4" class="d1-dot-orange" style="animation-delay: -1.5s" />
<circle cx="329.0" cy="74.3" r="4" class="d1-dot-orange" style="animation-delay: -1.9s" />
<circle cx="404.7" cy="199.8" r="4" class="d1-dot-orange" style="animation-delay: -0.9s" />
<circle cx="420.6" cy="67.6" r="4" class="d1-dot-orange" style="animation-delay: -2.4s" />
<circle cx="226.6" cy="247.5" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="341.9" cy="167.3" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="386.0" cy="201.2" r="4" class="d1-dot-orange" style="animation-delay: -0.8s" />
<circle cx="358.0" cy="135.3" r="4" class="d1-dot-orange" style="animation-delay: -0.4s" />
<circle cx="348.5" cy="201.9" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="543.3" cy="206.0" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="598.8" cy="210.8" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="374.4" cy="200.0" r="4" class="d1-dot-orange" style="animation-delay: -0.9s" />
<circle cx="442.6" cy="251.2" r="4" class="d1-dot-orange" style="animation-delay: -1.9s" />
<circle cx="257.6" cy="269.7" r="4" class="d1-dot-orange" style="animation-delay: -2.1s" />
<circle cx="414.2" cy="221.9" r="4" class="d1-dot-orange" style="animation-delay: -0.0s" />
<circle cx="120.0" cy="126.3" r="4" class="d1-dot-orange" style="animation-delay: -0.9s" />
<circle cx="281.9" cy="103.3" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="423.5" cy="60.0" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="489.1" cy="199.8" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="333.8" cy="121.7" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="345.7" cy="89.6" r="4" class="d1-dot-orange" style="animation-delay: -0.4s" />
<circle cx="246.4" cy="127.7" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="556.8" cy="60.0" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="526.0" cy="204.0" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="541.2" cy="178.0" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="591.9" cy="240.8" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="594.4" cy="261.8" r="4" class="d1-dot-orange" style="animation-delay: -2.1s" />
<circle cx="361.7" cy="175.5" r="4" class="d1-dot-orange" style="animation-delay: -2.5s" />
<circle cx="439.4" cy="136.2" r="4" class="d1-dot-orange" style="animation-delay: -1.1s" />
<circle cx="308.9" cy="251.1" r="4" class="d1-dot-orange" style="animation-delay: -0.9s" />
<circle cx="556.5" cy="97.1" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="594.1" cy="172.5" r="4" class="d1-dot-orange" style="animation-delay: -2.1s" />
<circle cx="378.2" cy="128.0" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="515.7" cy="183.9" r="4" class="d1-dot-orange" style="animation-delay: -2.0s" />
<circle cx="269.8" cy="177.3" r="4" class="d1-dot-orange" style="animation-delay: -1.1s" />
<circle cx="402.8" cy="144.0" r="4" class="d1-dot-orange" style="animation-delay: -2.1s" />
<circle cx="441.9" cy="170.8" r="4" class="d1-dot-orange" style="animation-delay: -2.2s" />
<circle cx="420.6" cy="267.6" r="4" class="d1-dot-orange" style="animation-delay: -1.5s" />
<circle cx="392.3" cy="205.8" r="4" class="d1-dot-orange" style="animation-delay: -2.1s" />
<circle cx="452.3" cy="235.8" r="4" class="d1-dot-orange" style="animation-delay: -2.0s" />
<circle cx="271.0" cy="307.9" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="411.9" cy="204.2" r="4" class="d1-dot-orange" style="animation-delay: -2.4s" />
<circle cx="593.2" cy="248.1" r="4" class="d1-dot-orange" style="animation-delay: -1.2s" />
<circle cx="425.2" cy="95.6" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="184.7" cy="201.6" r="4" class="d1-dot-orange" style="animation-delay: -0.2s" />
<circle cx="450.4" cy="293.1" r="4" class="d1-dot-orange" style="animation-delay: -0.8s" />
<circle cx="286.7" cy="158.9" r="4" class="d1-dot-orange" style="animation-delay: -1.3s" />
<circle cx="222.9" cy="243.5" r="4" class="d1-dot-orange" style="animation-delay: -0.8s" />
<circle cx="384.8" cy="145.6" r="4" class="d1-dot-orange" style="animation-delay: -0.6s" />
<circle cx="476.7" cy="224.2" r="4" class="d1-dot-orange" style="animation-delay: -0.3s" />
<circle cx="200.2" cy="170.4" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="446.4" cy="268.1" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="571.8" cy="183.4" r="4" class="d1-dot-orange" style="animation-delay: -0.7s" />
<circle cx="483.9" cy="220.2" r="4" class="d1-dot-orange" style="animation-delay: -0.6s" />
<circle cx="424.4" cy="204.9" r="4" class="d1-dot-orange" style="animation-delay: -1.3s" />
<circle cx="361.5" cy="360.0" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="393.1" cy="163.1" r="4" class="d1-dot-orange" style="animation-delay: -2.2s" />
<circle cx="151.5" cy="202.6" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="277.5" cy="208.4" r="4" class="d1-dot-orange" style="animation-delay: -0.5s" />
<circle cx="680.0" cy="244.1" r="4" class="d1-dot-orange" style="animation-delay: -1.2s" />
<circle cx="472.6" cy="135.9" r="4" class="d1-dot-orange" style="animation-delay: -0.2s" />
<circle cx="385.3" cy="179.3" r="4" class="d1-dot-orange" style="animation-delay: -0.4s" />
<circle cx="312.9" cy="173.7" r="4" class="d1-dot-orange" style="animation-delay: -2.5s" />
<circle cx="577.6" cy="269.9" r="4" class="d1-dot-orange" style="animation-delay: -1.5s" />
<circle cx="438.5" cy="150.0" r="4" class="d1-dot-orange" style="animation-delay: -1.3s" />
<circle cx="281.2" cy="216.5" r="4" class="d1-dot-orange" style="animation-delay: -2.2s" />
<circle cx="525.8" cy="191.5" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="250.3" cy="127.2" r="4" class="d1-dot-orange" style="animation-delay: -2.4s" />
<circle cx="438.5" cy="238.2" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="459.3" cy="228.5" r="4" class="d1-dot-orange" style="animation-delay: -0.2s" />
<circle cx="557.2" cy="196.2" r="4" class="d1-dot-orange" style="animation-delay: -1.5s" />
<circle cx="390.8" cy="240.6" r="4" class="d1-dot-orange" style="animation-delay: -1.8s" />
<circle cx="373.4" cy="126.6" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="618.2" cy="142.3" r="4" class="d1-dot-orange" style="animation-delay: -1.6s" />
<circle cx="254.6" cy="66.6" r="4" class="d1-dot-orange" style="animation-delay: -1.1s" />
<circle cx="234.5" cy="169.1" r="4" class="d1-dot-orange" style="animation-delay: -2.3s" />
<circle cx="438.2" cy="172.8" r="4" class="d1-dot-orange" style="animation-delay: -0.4s" />
<circle cx="338.5" cy="296.1" r="4" class="d1-dot-orange" style="animation-delay: -1.4s" />
<circle cx="398.9" cy="227.5" r="4" class="d1-dot-orange" style="animation-delay: -1.7s" />
<circle cx="318.4" cy="60.0" r="4" class="d1-dot-orange" style="animation-delay: -1.3s" />
<circle cx="361.8" cy="196.0" r="4" class="d1-dot-orange" style="animation-delay: -0.1s" />
<circle cx="310.6" cy="218.8" r="4" class="d1-dot-orange" style="animation-delay: -0.6s" />
<line x1="390" y1="215" x2="850" y2="140" class="d1-leader" />
<line x1="415" y1="195" x2="850" y2="140" class="d1-leader" />
<circle cx="390" cy="215" r="14" class="d1-centroid-halo-blue" />
<circle cx="390" cy="215" r="8" class="d1-centroid-bg" />
<circle cx="390" cy="215" r="8" class="d1-centroid-blue" />
<rect x="362" y="227" width="20" height="20" rx="4" class="d1-label-bg" />
<text x="372" y="242" class="d1-label-blue" text-anchor="middle">g</text>
<circle cx="415" cy="195" r="14" class="d1-centroid-halo-orange" />
<circle cx="415" cy="195" r="8" class="d1-centroid-bg" />
<circle cx="415" cy="195" r="8" class="d1-centroid-orange" />
<rect x="423" y="163" width="20" height="20" rx="4" class="d1-label-bg" />
<text x="433" y="178" class="d1-label-orange" text-anchor="middle">b</text>
<line x1="396.2469504755442" y1="210.0024396195646" x2="407.1913119055697" y2="201.24695047554425" class="d1-arrow" marker-end="url(#d1-arrowhead)" />
<circle cx="850" cy="140" r="85" class="d1-inset-bg" />
<circle cx="850" cy="140" r="85" class="d1-inset-border" />
<rect x="900" y="200" width="36" height="20" rx="4" class="d1-label-bg" />
<text x="918" y="214" class="d1-inset-label" text-anchor="middle">×20</text>
<circle cx="818.75" cy="165.0" r="24" class="d1-centroid-halo-blue" />
<circle cx="818.75" cy="165.0" r="12" class="d1-centroid-bg" />
<circle cx="818.75" cy="165.0" r="12" class="d1-centroid-blue" />
<text x="793.75" y="170.0" class="d1-label-blue" text-anchor="end">g</text>
<circle cx="881.25" cy="115.0" r="24" class="d1-centroid-halo-orange" />
<circle cx="881.25" cy="115.0" r="12" class="d1-centroid-bg" />
<circle cx="881.25" cy="115.0" r="12" class="d1-centroid-orange" />
<text x="906.25" y="120.0" class="d1-label-orange" text-anchor="start">b</text>
<line x1="828.1204257133163" y1="157.5036594293469" x2="870.3178366677976" y2="123.74573066576194" class="d1-arrow-zoomed" marker-end="url(#d1-arrowhead)" />
<text x="850" y="260" class="d1-anno-primary" text-anchor="middle">r = b − g</text>
<text x="850" y="280" class="d1-anno-secondary" text-anchor="middle">the refusal direction</text>
<line x1="850" y1="225" x2="850" y2="240" class="d1-leader" />
<text x="850" y="320" class="d1-anno-primary" text-anchor="middle">|r| ≈ 0.7% of |g|</text>
<text x="850" y="345" class="d1-anno-primary" text-anchor="middle">cos(g, b) = 0.9990</text>
<text x="850" y="380" class="d1-anno-secondary" text-anchor="middle">the entire difference between</text>
<text x="850" y="400" class="d1-anno-secondary" text-anchor="middle">"harmful" and "harmless"</text>
</svg>

<div class="cap">

cosine similarity between the two cluster means: <b>0.9990</b> at layer 8, never below <b>0.91</b> at any layer

</div>

<!--
THE MONEY SLIDE — slow down here, 2 minutes.

Point at the cloud. "Blue is 400 harmless prompts. Orange is 400 harmful
ones. These are the model's own internal activations at one layer."

Then the key beat: "Notice you cannot separate them by eye. That's not an
artistic choice — the measured cosine similarity between those two cluster
means is 0.9990."

Point at the ×20 inset. "We have to magnify twenty times to even SEE the
offset. The length of that arrow is about 0.7% of the length of the vectors
themselves."

Land it: "Refusal is not a region of activation space. It is a faint,
consistent offset between two distributions that are otherwise the same."

Then the implication, which is the whole talk: "Something that small is
something you can subtract with one line of linear algebra. And something
that small is also something a 4-bit quantizer might perturb — hold that
thought, we come back to it at the end."
-->

---

<!-- _class: lite -->

# Finding it

**harmless** prompts → mean activation **g**
**harmful** prompts → mean activation **b**

<div class="formula">r = b − g</div>

No gradients. No training. One forward pass.

<!--
DIFFERENCE-OF-MEANS — 90 seconds.

This is the entire derivation. Run two sets of prompts, take the mean
first-token residual of each, subtract. That difference IS the refusal
direction for that layer.

Emphasise the cost: no backprop, no optimizer, no labelled data beyond "these
prompts tend to get refused and these don't." On a small model this is
seconds of compute.

Heretic's defaults are mlabonne/harmless_alpaca and
mlabonne/harmful_behaviors, 400 prompts each, train split.

NOW THE POINT MOST TALKS MISS — say this deliberately:

Those 400 prompts are the complete definition of "harmful" for the resulting
model. Not a policy document. Not a review board. 400 rows in a dataset that
most people never open, pinned to a commit that most people never record.

"This is a policy decision wearing a hyperparameter's clothing."

That line usually gets the room. Pause after it.
-->

---

<!-- _class: figure -->

# The whole technique, in one equation

<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<line x1="250" y1="300" x2="900" y2="300" class="d2-axis" />
<line x1="300" y1="350" x2="300" y2="50" class="d2-axis" />
<line x1="300" y1="300" x2="733.0127018922194" y2="50.00000000000003" class="d2-r-axis" />
<text x="743.0127018922194" y="50.00000000000003" class="d2-label-orange">r̂</text>
<line x1="300" y1="300" x2="475.0" y2="-3.108891324553497" class="d2-x-vec" />
<polygon points="475.0,-3.108891324553497 474.7640341470909,6.888324293620441 466.4601402340054,2.094068907578409" class="d2-x-arrow" />
<text x="465.0" y="-18.108891324553497" class="d2-label-blue">x</text>
<line x1="300" y1="300" x2="562.5" y2="148.44555433772325" class="d2-proj-vec" />
<text x="572.5" y="173.44555433772325" class="d2-label-amber">r̂ r̂ᵀ x</text>
<line x1="475.0" y1="-3.108891324553497" x2="562.5" y2="148.44555433772325" class="d2-dash-line" />
<polyline points="549.5096189432334,155.94555433772325 557.0096189432334,168.93593539448983 570.0,161.43593539448983" class="d2-right-angle" />
<line x1="300" y1="300" x2="212.5" y2="148.44555433772325" class="d2-x-prime-vec" />
<polygon points="212.5,148.44555433772325 221.03985976599463,153.64851456985517 212.7359658529091,158.44276995589718" class="d2-x-prime-arrow" />
<text x="182.5" y="138.44555433772325" class="d2-label-green">x′</text>
<polyline points="312.9903810567666,292.5 305.4903810567666,279.5096189432334 292.5,287.0096189432334" class="d2-ortho-marker" />
<text x="700" y="100" class="d2-equation">x′ ← x − r̂ r̂ᵀ x</text>
<text x="20" y="380" class="d2-caption">every layer, every token position</text>
</svg>

<div class="cap">

applied at <b>every layer</b>, <b>every token position</b>

</div>

<!--
THE EQUATION — 90 seconds. This is from the paper, equation 4.

Walk the geometry left to right:
  - x is any activation vector
  - r-hat is the unit refusal direction
  - r-hat r-hat-transpose x is the component of x that points along refusal
  - subtract it, and what's left is orthogonal to refusal

"The model can no longer represent that direction. Not 'is discouraged from' —
cannot. It's been projected out of the space."

Say the cost out loud: that's ONE projection and ONE subtraction. The paper
calls the resulting jailbreak "an interpretable rank-one weight edit."

If someone asks why this doesn't destroy the model: because it's rank one.
You removed a single direction out of several thousand dimensions. Everything
orthogonal to refusal is untouched — which is exactly why the capability
benchmarks barely move, which is the next problem we'll hit.
-->

---

<!-- _class: figure -->

# Two ways to apply it — only one ships

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

<!--
THE FORK IN THE ROAD — 90 seconds. This slide sets up the entire back half.

Left: inference-time ablation. You hook the forward pass and project the
direction out as the model runs. The weights on disk never change. It's
reversible, it's a research tool, and it dies the moment you switch runtime.

Right: weight orthogonalization. You bake it into the attention
out-projection and MLP down-projection matrices permanently. New checkpoint.

"Only the right-hand one creates a file. And a file gets uploaded, renamed,
quantized, re-uploaded, and downloaded a million times."

The critical line — deliver it slowly:

"An abliterated checkpoint and a backdoored checkpoint are the same shape.
A directory of safetensors and a config. There is no diff you can read.
Code review works because humans can read diffs. There is no equivalent
for weights."

That is the thesis. Everything from Part 6 onward is consequences of it.
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 2</div>

# Why anyone does it

## Including the part that argues against it

---

<!-- _class: lite -->

# The honest split

<div class="trio">
<div class="ok">

### Defensible
security research · interpretability · over-refusal in medical, legal, infosec work · sovereignty over your own weights

</div>
<div class="on">

### Arguable
"uncensored" as a product · creative writing · removing vendor policy you disagree with

</div>
<div class="no">

### Not
content the publisher declined to allow, with no evaluation at all

</div>
</div>

<!--
WHY — 2 minutes. Be even-handed; you lose the room if you moralise.

Defensible, with concrete examples:
  - A malware-analysis assistant that refuses to discuss malware is useless.
  - Toxicology, forensic medicine, penetration testing — practitioners hit
    refusals on their ordinary daily workload.
  - Interpretability: refusal is the best-studied linear behaviour we have.
    Ablation IS the experiment.
  - Sovereignty: you run the weights on your hardware; a reasonable person
    can argue vendor policy shouldn't be immutable.

Then be straight about the other side:

"The same eight lines of linear algebra serve the security researcher and
the abuser. Nothing in the technique distinguishes them. I'm not going to
pretend otherwise."

And the pragmatic point that makes the argument moot:

"This is 5,844 models and one pip install. Whatever you think about whether
it SHOULD happen, it HAS happened. The actionable question is whether you
can tell what you've downloaded."
-->

---

<!-- _class: statement -->
<!-- _transition: zoom 450ms -->

# Safety alignment is a *direction*, not a *wall*

<p>400 prompts and a difference-of-means undo a post-training pipeline that cost millions.</p>

<!--
LET IT LAND — 30 seconds of talking, then silence.

The uncomfortable research result is not that abliteration works. It's what
its cheapness implies about what RLHF actually did.

If safety were deeply entangled with capability, removing it would break the
model. It mostly doesn't. That tells you refusal was learned as a separable,
linearly-represented feature sitting on top of the model — not woven through
it.

The constructive reading, and say this because it's the useful one:

"This is an argument for defence in depth at the SYSTEM level. If your safety
story depends entirely on weights behaving, your safety story has a
single point of failure that costs twenty minutes on a 3090 to remove."
-->

---

<!-- _class: lite -->

# It's surgical — and that's the problem

**MMLU · ARC · GSM8K** — <span class="ok">essentially unchanged</span>

**TruthfulQA** — <span class="mid">moves, and not by accident</span>

<div class="box bad">

Capability benchmarks **do not detect** abliteration.

</div>

<!--
THE MEASUREMENT TRAP — 2 minutes. This is a genuinely underappreciated point.

Arditi et al. ran every orthogonalized model against its baseline on LM
Evaluation Harness with Open-LLM-Leaderboard settings. MMLU, ARC, GSM8K all
came out "similar to baseline." Only Qwen 7B and Yi 34B degraded notably.

TruthfulQA is the interesting exception. Its categories include
misinformation, stereotypes and conspiracies — which is precisely the content
refusal was suppressing. So that benchmark was partly measuring refusal, and
when you remove refusal the score moves. It isn't damage; it's the benchmark
revealing what it was really scoring.

They also measured cross-entropy loss on standard corpora and concluded
directional ablation is MORE surgical than activation-addition steering.

Now the operational consequence, which is what your audience should take:

"A model can hold its MMLU score and have had its refusal behaviour deleted.
If your model-acceptance gate is 'the benchmarks didn't move', you will never
detect this. Not rarely — never. It is not what those benchmarks measure."
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 3</div>

# Heretic

## One command. No expertise required.

---

<!-- _class: lite -->

# Heretic

```
pip install -U heretic-llm
heretic Qwen/Qwen3-4B-Instruct-2507
```

Philipp Emanuel Weidmann · **AGPL-3.0-or-later**

<!--
THE TOOL — 90 seconds.

Two lines. That's the whole interface. The author's framing is "removes
censorship without expensive post-training", and the real contribution is
NOT the ablation maths — that's the 2024 paper.

The contribution is that it's fully automatic. Before Heretic you hand-picked
a layer, hand-tuned an ablation strength, eyeballed the result. Heretic
searches for you.

"Anyone who can run a command-line program can now decensor a language model.
That is the actual news."

Requirements: Python 3.10+, PyTorch 2.2+ (2.6+ for MXFP4 models like gpt-oss).
20-30 minutes for a 4B model on an RTX 3090. bitsandbytes 4-bit loading if
you're VRAM-constrained. device_map=auto shards across every visible GPU
with no flags.

Licence note — flag it, it matters commercially: AGPL-3.0-or-later. Running
an unmodified CLI as a subprocess is materially different from importing it
or running a MODIFIED copy as a network service, which is what section 13
targets. Get that looked at before you build a product on it.
-->

---

<!-- _class: figure -->

# It doesn't ablate once — it searches

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

<!--
THE OPTIMIZER — 2 minutes. This is what separates Heretic from its prior art.

Walk the loop:
  - Residuals get collected ONCE — 400 harmless, 400 harmful.
  - Then 200 trials. Each trial: Optuna's TPE sampler proposes ablation
    parameters, Heretic orthogonalizes the weights, and scores the result.
  - First 60 trials are random — mapping the space. The remaining 140 are
    TPE-guided.

The objective is the interesting part. It co-minimizes TWO things:
  - the refusal count on held-out harmful prompts
  - the KL divergence from the ORIGINAL model on harmless prompts

That second term is the quality guard. It asks: on prompts that were never
supposed to be refused, how far has the edited model's output distribution
drifted? That's collateral damage, quantified.

There's a nice detail: below kl_divergence_target = 0.01 the objective
switches to pure refusal count, so the sampler stops burning trials on
parameter sets that do nothing.

"Each dot in the next slide is a full abliteration of a multi-billion
parameter model, scored on both axes. Two hundred of them."
-->

---

<!-- _class: figure -->

# The search space

<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<line x1="100" y1="320" x2="900" y2="320" class="d3-axis" />
<line x1="100" y1="320" x2="100" y2="70" class="d3-axis" />
<text x="500.0" y="392" class="d3-axis-label" text-anchor="middle">transformer layer index (0 → N)</text>
<text x="60" y="195.0" class="d3-axis-label" text-anchor="middle" transform="rotate(-90 60 195.0)">ablation weight (0 → 1)</text>
<text x="90" y="320" class="d3-tick" text-anchor="end">0</text>
<text x="90" y="70" class="d3-tick" text-anchor="end">1</text>
<text x="100" y="340" class="d3-tick" text-anchor="middle">0</text>
<text x="900" y="340" class="d3-tick" text-anchor="middle">N</text>
<path d="M 100.0,295.0 L 108.0,295.0 L 116.0,295.0 L 124.0,295.0 L 132.0,295.0 L 140.0,295.0 L 148.0,295.0 L 156.0,295.0 L 164.0,295.0 L 172.0,295.0 L 180.0,295.0 L 188.0,294.5206658447239 L 196.0,293.087915064208 L 204.0,290.71744517582596 L 212.0,287.4352275437276 L 220.0,283.2772228311384 L 228.0,278.2889870078079 L 236.0,272.525172229272 L 244.0,266.0489280564001 L 252.0,258.93120957559137 L 260.0,251.25000000000003 L 268.0,243.08945626913254 L 276.0,234.53898700780792 L 284.0,225.69227294655397 L 292.0,216.64624053591967 L 300.0,207.5 L 308.0,198.35375946408033 L 316.0,189.30772705344606 L 324.0,180.46101299219208 L 332.0,171.91054373086752 L 340.0,163.75 L 348.0,156.06879042440863 L 356.0,148.9510719435999 L 364.0,142.474827770728 L 372.0,136.71101299219208 L 380.0,131.72277716886163 L 388.0,127.56477245627244 L 396.0,124.28255482417404 L 404.0,121.912084935792 L 412.0,120.47933415527609 L 420.0,120.0 L 428.0,120.47933415527606 L 436.0,121.912084935792 L 444.0,124.28255482417404 L 452.0,127.56477245627241 L 460.0,131.7227771688616 L 468.0,136.71101299219208 L 476.0,142.47482777072798 L 484.0,148.95107194359989 L 492.0,156.06879042440858 L 500.0,163.74999999999994 L 508.0,171.91054373086743 L 516.0,180.46101299219208 L 524.0,189.30772705344606 L 532.0,198.35375946408033 L 540.0,207.5 L 548.0,216.64624053591967 L 556.0,225.69227294655386 L 564.0,234.53898700780786 L 572.0,243.08945626913248 L 580.0,251.24999999999994 L 588.0,258.93120957559137 L 596.0,266.0489280564001 L 604.0,272.52517222927196 L 612.0,278.2889870078079 L 620.0,283.2772228311384 L 628.0,287.4352275437276 L 636.0,290.71744517582596 L 644.0,293.087915064208 L 652.0,294.5206658447239 L 660.0,295.0 L 668.0,295.0 L 676.0,295.0 L 684.0,295.0 L 692.0,295.0 L 700.0,295.0 L 708.0,295.0 L 716.0,295.0 L 724.0,295.0 L 732.0,295.0 L 740.0,295.0 L 748.0,295.0 L 756.0,295.0 L 764.0,295.0 L 772.0,295.0 L 780.0,295.0 L 788.0,295.0 L 796.0,295.0 L 804.0,295.0 L 812.0,295.0 L 820.0,295.0 L 828.0,295.0 L 836.0,295.0 L 844.0,295.0 L 852.0,295.0 L 860.0,295.0 L 868.0,295.0 L 876.0,295.0 L 884.0,295.0 L 892.0,295.0 L 900.0,295.0" class="d3-curve-blue d3-curve-1" />
<path d="M 100.0,282.5 L 108.0,282.5 L 116.0,282.5 L 124.0,282.5 L 132.0,282.5 L 140.0,282.5 L 148.0,282.5 L 156.0,282.5 L 164.0,282.5 L 172.0,282.5 L 180.0,282.5 L 188.0,282.5 L 196.0,282.5 L 204.0,282.5 L 212.0,282.5 L 220.0,282.5 L 228.0,282.5 L 236.0,282.5 L 244.0,282.5 L 252.0,282.5 L 260.0,282.5 L 268.0,281.8100363650168 L 276.0,279.75102659875523 L 284.0,276.35544251522197 L 292.0,271.67683450383805 L 300.0,265.7889870078079 L 308.0,258.78475489937347 L 316.0,250.77459910301036 L 324.0,241.8848445606622 L 332.0,232.25568801194387 L 340.0,222.03898700780792 L 348.0,211.39586502625093 L 356.0,200.49417045881492 L 364.0,189.50582954118508 L 372.0,178.60413497374907 L 380.0,167.96101299219214 L 388.0,157.74431198805618 L 396.0,148.1151554393378 L 404.0,139.22540089698964 L 412.0,131.21524510062648 L 420.0,124.21101299219211 L 428.0,118.32316549616195 L 436.0,113.64455748477803 L 444.0,110.24897340124477 L 452.0,108.1899636349832 L 460.0,107.5 L 468.0,108.1899636349832 L 476.0,110.24897340124474 L 484.0,113.644557484778 L 492.0,118.32316549616192 L 500.0,124.21101299219211 L 508.0,131.21524510062648 L 516.0,139.22540089698964 L 524.0,148.1151554393378 L 532.0,157.74431198805618 L 540.0,167.96101299219214 L 548.0,178.60413497374915 L 556.0,189.50582954118502 L 564.0,200.49417045881486 L 572.0,211.39586502625085 L 580.0,222.03898700780786 L 588.0,232.25568801194385 L 596.0,241.8848445606622 L 604.0,250.77459910301036 L 612.0,258.78475489937347 L 620.0,265.7889870078079 L 628.0,271.67683450383805 L 636.0,276.355442515222 L 644.0,279.75102659875523 L 652.0,281.8100363650168 L 660.0,282.5 L 668.0,282.5 L 676.0,282.5 L 684.0,282.5 L 692.0,282.5 L 700.0,282.5 L 708.0,282.5 L 716.0,282.5 L 724.0,282.5 L 732.0,282.5 L 740.0,282.5 L 748.0,282.5 L 756.0,282.5 L 764.0,282.5 L 772.0,282.5 L 780.0,282.5 L 788.0,282.5 L 796.0,282.5 L 804.0,282.5 L 812.0,282.5 L 820.0,282.5 L 828.0,282.5 L 836.0,282.5 L 844.0,282.5 L 852.0,282.5 L 860.0,282.5 L 868.0,282.5 L 876.0,282.5 L 884.0,282.5 L 892.0,282.5 L 900.0,282.5" class="d3-curve-blue d3-curve-2" />
<path d="M 100.0,307.5 L 108.0,307.5 L 116.0,307.5 L 124.0,307.5 L 132.0,307.5 L 140.0,307.5 L 148.0,307.5 L 156.0,307.5 L 164.0,307.5 L 172.0,307.5 L 180.0,307.5 L 188.0,307.5 L 196.0,307.5 L 204.0,307.5 L 212.0,307.5 L 220.0,307.5 L 228.0,307.5 L 236.0,307.5 L 244.0,307.5 L 252.0,307.5 L 260.0,307.5 L 268.0,307.32660002248844 L 276.0,306.80746915847647 L 284.0,305.9458080223693 L 292.0,304.74692904160236 L 300.0,303.21822370375986 L 308.0,301.36911698559567 L 316.0,299.21100924491765 L 324.0,296.7572059335908 L 332.0,294.02283556500174 L 340.0,291.02475644174325 L 348.0,287.78145271857284 L 356.0,284.3129204414516 L 364.0,280.64054426527207 L 372.0,276.7869656103495 L 380.0,272.7759430705363 L 388.0,268.6322059335908 L 396.0,264.38130171689465 L 404.0,260.04943865851294 L 412.0,255.66332413469127 L 420.0,251.24999999999997 L 428.0,246.8366758653087 L 436.0,242.450561341487 L 444.0,238.1186982831053 L 452.0,233.8677940664092 L 460.0,229.72405692946367 L 468.0,225.71303438965046 L 476.0,221.85945573472787 L 484.0,218.1870795585484 L 492.0,214.71854728142716 L 500.0,211.4752435582567 L 508.0,208.47716443499826 L 516.0,205.7427940664092 L 524.0,203.2889907550823 L 532.0,201.13088301440428 L 540.0,199.28177629624008 L 548.0,197.75307095839761 L 556.0,196.5541919776307 L 564.0,195.6925308415235 L 572.0,195.17339997751156 L 580.0,195.0 L 588.0,195.17339997751156 L 596.0,195.6925308415235 L 604.0,196.5541919776307 L 612.0,197.75307095839761 L 620.0,199.28177629624014 L 628.0,201.13088301440433 L 636.0,203.28899075508232 L 644.0,205.74279406640923 L 652.0,208.47716443499826 L 660.0,211.4752435582567 L 668.0,214.71854728142716 L 676.0,218.1870795585484 L 684.0,221.85945573472787 L 692.0,225.7130343896505 L 700.0,229.7240569294637 L 708.0,233.8677940664092 L 716.0,238.11869828310535 L 724.0,242.45056134148703 L 732.0,246.83667586530873 L 740.0,251.25000000000003 L 748.0,255.6633241346913 L 756.0,260.04943865851294 L 764.0,264.38130171689465 L 772.0,268.6322059335908 L 780.0,272.7759430705363 L 788.0,276.7869656103495 L 796.0,280.6405442652721 L 804.0,284.3129204414516 L 812.0,287.78145271857284 L 820.0,291.0247564417433 L 828.0,294.02283556500174 L 836.0,296.7572059335908 L 844.0,299.2110092449177 L 852.0,301.36911698559567 L 860.0,303.21822370375986 L 868.0,304.74692904160236 L 876.0,305.9458080223693 L 884.0,306.80746915847647 L 892.0,307.32660002248844 L 900.0,307.5" class="d3-curve-orange d3-curve-1" />
<path d="M 100.0,320.0 L 108.0,320.0 L 116.0,320.0 L 124.0,320.0 L 132.0,320.0 L 140.0,320.0 L 148.0,320.0 L 156.0,320.0 L 164.0,320.0 L 172.0,320.0 L 180.0,320.0 L 188.0,320.0 L 196.0,320.0 L 204.0,320.0 L 212.0,320.0 L 220.0,320.0 L 228.0,320.0 L 236.0,320.0 L 244.0,320.0 L 252.0,320.0 L 260.0,320.0 L 268.0,319.7735540372322 L 276.0,319.0960393586729 L 284.0,317.9729109141418 L 292.0,316.4132114734852 L 300.0,314.4294988195111 L 308.0,312.03774464010496 L 316.0,309.2572059335908 L 324.0,306.1102699627031 L 332.0,302.62227400551114 L 340.0,298.8213013545538 L 348.0,294.7379552066808 L 356.0,290.4051122641062 L 364.0,285.85765803053323 L 372.0,281.1322059335908 L 380.0,276.2668025350427 L 388.0,271.3006212022432 L 396.0,266.27364670721647 L 404.0,261.22635329278353 L 412.0,256.1993787977569 L 420.0,251.23319746495733 L 428.0,246.36779406640926 L 436.0,241.64234196946683 L 444.0,237.09488773589385 L 452.0,232.76204479331926 L 460.0,228.67869864544625 L 468.0,224.87772599448886 L 476.0,221.38973003729689 L 484.0,218.2427940664092 L 492.0,215.46225535989504 L 500.0,213.07050118048892 L 508.0,211.0867885265148 L 516.0,209.52708908585828 L 524.0,208.40396064132707 L 532.0,207.7264459627678 L 540.0,207.5 L 548.0,207.7264459627678 L 556.0,208.40396064132707 L 564.0,209.52708908585825 L 572.0,211.08678852651477 L 580.0,213.07050118048892 L 588.0,215.46225535989498 L 596.0,218.2427940664092 L 604.0,221.38973003729689 L 612.0,224.87772599448886 L 620.0,228.67869864544622 L 628.0,232.7620447933192 L 636.0,237.09488773589385 L 644.0,241.64234196946677 L 652.0,246.36779406640915 L 660.0,251.23319746495727 L 668.0,256.1993787977568 L 676.0,261.22635329278353 L 684.0,266.2736467072164 L 692.0,271.30062120224306 L 700.0,276.26680253504264 L 708.0,281.1322059335908 L 716.0,285.85765803053323 L 724.0,290.40511226410615 L 732.0,294.73795520668074 L 740.0,298.8213013545538 L 748.0,302.62227400551114 L 756.0,306.1102699627031 L 764.0,309.2572059335908 L 772.0,312.03774464010496 L 780.0,314.4294988195111 L 788.0,316.4132114734852 L 796.0,317.9729109141417 L 804.0,319.0960393586729 L 812.0,319.7735540372322 L 820.0,320.0 L 828.0,320.0 L 836.0,320.0 L 844.0,320.0 L 852.0,320.0 L 860.0,320.0 L 868.0,320.0 L 876.0,320.0 L 884.0,320.0 L 892.0,320.0 L 900.0,320.0" class="d3-curve-orange d3-curve-2" />
<line x1="750" y1="90" x2="780" y2="90" class="d3-curve-blue" style="stroke-width:3px" />
<text x="790" y="95" class="d3-legend-text">attn o_proj</text>
<line x1="750" y1="115" x2="780" y2="115" class="d3-curve-orange" style="stroke-width:3px" />
<text x="790" y="120" class="d3-legend-text">mlp down_proj</text>
<line x1="420.0" y1="120.0" x2="470.0" y2="90.0" class="d3-leader" />
<text x="475.0" y="85.0" class="d3-annotation">max_weight</text>
<line x1="420.0" y1="320" x2="420.0" y2="350" class="d3-leader" />
<text x="420.0" y="365" class="d3-annotation" text-anchor="middle">max_weight_position</text>
<line x1="660.0" y1="295.0" x2="710.0" y2="265.0" class="d3-leader" />
<text x="715.0" y="260.0" class="d3-annotation">min_weight</text>
<line x1="420.0" y1="170.0" x2="660.0" y2="170.0" class="d3-leader" />
<line x1="420.0" y1="165.0" x2="420.0" y2="175.0" class="d3-leader" />
<line x1="660.0" y1="165.0" x2="660.0" y2="175.0" class="d3-leader" />
<text x="540.0" y="165.0" class="d3-annotation" text-anchor="middle">min_weight_distance</text>
</svg>

<div class="cap">

chosen <b>independently</b> for attention out-projection and MLP down-projection

</div>

<!--
THE KERNEL — 90 seconds. Don't enumerate parameters; show the shape.

The ablation strength is not constant across layers. It's a shaped curve, and
four parameters define it: peak height, peak position, floor, and falloff
distance. Maxime Labonne first explored non-constant weights; Heretic makes
them searchable.

Point at the two curves. They're independent per component type. The author
found MLP interventions damage the model more than attention interventions —
so the optimizer naturally learns to ablate MLPs more gently. That asymmetry
is one of three stated innovations.

The sharpest idea on this slide, and worth calling out:

"direction_index is a FLOAT, not an integer. Non-integral values linearly
interpolate between the two nearest layer directions. So the search isn't
limited to the directions that difference-of-means actually found — it can
find a better direction that belongs to no individual layer."

That's genuinely clever and it's why Heretic beats hand-tuning.
-->

---

<!-- _class: figure -->

# The result

<svg viewBox="0 0 1050 400" width="1050" xmlns="http://www.w3.org/2000/svg">
<line x1="100" y1="320" x2="900" y2="320" class="d4-axis" />
<line x1="100" y1="320" x2="100" y2="70" class="d4-axis" />
<text x="500.0" y="360" class="d4-axis-label" text-anchor="middle">KL divergence from original (0 → 1.2)</text>
<text x="60" y="195.0" class="d4-axis-label" text-anchor="middle" transform="rotate(-90 60 195.0)">refusals / 100 (0 → 100)</text>
<text x="90" y="320" class="d4-tick" text-anchor="end">0</text>
<text x="90" y="70" class="d4-tick" text-anchor="end">100</text>
<text x="100" y="340" class="d4-tick" text-anchor="middle">0</text>
<text x="900" y="340" class="d4-tick" text-anchor="middle">1.2</text>
<text x="118" y="296" class="d4-better-label">better ↙</text>
<line x1="106.66666666666667" y1="320" x2="106.66666666666667" y2="70" class="d4-kl-target" />
<text x="118" y="168" class="d4-kl-label">kl_divergence_target = 0.01</text>
<circle cx="264.8" cy="254.7" r="4" class="d4-dot-random" style="animation-delay: -1.6s" />
<circle cx="298.0" cy="112.3" r="4" class="d4-dot-random" style="animation-delay: -0.2s" />
<circle cx="555.1" cy="211.9" r="4" class="d4-dot-random" style="animation-delay: -3.4s" />
<circle cx="329.1" cy="211.0" r="4" class="d4-dot-random" style="animation-delay: -1.3s" />
<circle cx="380.4" cy="269.7" r="4" class="d4-dot-random" style="animation-delay: -1.7s" />
<circle cx="285.9" cy="165.4" r="4" class="d4-dot-random" style="animation-delay: -0.3s" />
<circle cx="422.6" cy="191.5" r="4" class="d4-dot-random" style="animation-delay: -3.6s" />
<circle cx="289.0" cy="245.1" r="4" class="d4-dot-random" style="animation-delay: -3.2s" />
<circle cx="246.1" cy="110.5" r="4" class="d4-dot-random" style="animation-delay: -2.3s" />
<circle cx="392.5" cy="123.4" r="4" class="d4-dot-random" style="animation-delay: -3.1s" />
<circle cx="439.4" cy="129.7" r="4" class="d4-dot-random" style="animation-delay: -0.8s" />
<circle cx="598.7" cy="177.8" r="4" class="d4-dot-random" style="animation-delay: -3.2s" />
<circle cx="169.3" cy="261.6" r="4" class="d4-dot-tpe" style="animation-delay: -1.9s" />
<circle cx="503.9" cy="311.0" r="4" class="d4-dot-tpe" style="animation-delay: -0.7s" />
<circle cx="301.4" cy="245.0" r="4" class="d4-dot-tpe" style="animation-delay: -2.5s" />
<circle cx="113.6" cy="254.2" r="4" class="d4-dot-tpe" style="animation-delay: -3.9s" />
<circle cx="305.8" cy="299.4" r="4" class="d4-dot-tpe" style="animation-delay: -1.1s" />
<circle cx="322.8" cy="284.6" r="4" class="d4-dot-tpe" style="animation-delay: -2.1s" />
<circle cx="135.9" cy="301.8" r="4" class="d4-dot-tpe" style="animation-delay: -1.4s" />
<circle cx="265.1" cy="255.9" r="4" class="d4-dot-tpe" style="animation-delay: -0.2s" />
<circle cx="342.0" cy="289.1" r="4" class="d4-dot-tpe" style="animation-delay: -1.5s" />
<circle cx="122.4" cy="249.6" r="4" class="d4-dot-tpe" style="animation-delay: -3.5s" />
<circle cx="258.8" cy="279.2" r="4" class="d4-dot-tpe" style="animation-delay: -2.0s" />
<circle cx="177.2" cy="304.3" r="4" class="d4-dot-tpe" style="animation-delay: -3.6s" />
<circle cx="229.9" cy="305.2" r="4" class="d4-dot-tpe" style="animation-delay: -2.1s" />
<circle cx="333.8" cy="297.4" r="4" class="d4-dot-tpe" style="animation-delay: -1.6s" />
<circle cx="228.0" cy="272.5" r="4" class="d4-dot-tpe" style="animation-delay: -0.2s" />
<circle cx="349.7" cy="284.9" r="4" class="d4-dot-tpe" style="animation-delay: -3.3s" />
<circle cx="171.4" cy="311.4" r="4" class="d4-dot-tpe" style="animation-delay: -3.8s" />
<circle cx="148.0" cy="253.4" r="4" class="d4-dot-tpe" style="animation-delay: -1.0s" />
<circle cx="539.8" cy="193.2" r="4" class="d4-dot-tpe" style="animation-delay: -0.6s" />
<circle cx="524.8" cy="296.1" r="4" class="d4-dot-tpe" style="animation-delay: -1.2s" />
<circle cx="317.5" cy="292.9" r="4" class="d4-dot-tpe" style="animation-delay: -2.4s" />
<circle cx="399.0" cy="263.2" r="4" class="d4-dot-tpe" style="animation-delay: -3.5s" />
<circle cx="346.4" cy="249.3" r="4" class="d4-dot-tpe" style="animation-delay: -0.3s" />
<circle cx="290.1" cy="257.3" r="4" class="d4-dot-tpe" style="animation-delay: -0.2s" />
<circle cx="482.4" cy="240.3" r="4" class="d4-dot-tpe" style="animation-delay: -0.7s" />
<circle cx="226.2" cy="296.1" r="4" class="d4-dot-tpe" style="animation-delay: -1.7s" />
<circle cx="434.2" cy="212.5" r="4" class="d4-dot-tpe" style="animation-delay: -3.4s" />
<circle cx="268.4" cy="280.9" r="4" class="d4-dot-tpe" style="animation-delay: -3.0s" />
<circle cx="100.0" cy="77.5" r="5" class="d4-dot-original" />
<text x="110.0" y="81.5" class="d4-ref-label">original</text>
<circle cx="793.3" cy="312.5" r="5" class="d4-dot-ref" />
<text x="803.3333333333334" y="316.5" class="d4-ref-label">mlabonne v2</text>
<circle cx="400.0" cy="312.5" r="5" class="d4-dot-ref" />
<text x="410.0" y="316.5" class="d4-ref-label">huihui-ai</text>
<circle cx="206.7" cy="312.5" r="10" class="d4-dot-best-pulse" />
<circle cx="206.7" cy="312.5" r="6" class="d4-dot-best" />
<text x="216.66666666666669" y="316.5" class="d4-ref-label">heretic (best trial)</text>
<circle cx="720" cy="90" r="4" class="d4-dot-random" />
<text x="730" y="94" class="d4-legend-text">random exploration</text>
<circle cx="720" cy="115" r="4" class="d4-dot-tpe" />
<text x="730" y="119" class="d4-legend-text">TPE-guided</text>
</svg>

<div class="cap">

all three competitors sit at <b>3/100 refusals</b> — the contest is the horizontal axis

</div>

<!--
THE BENCHMARK — 2 minutes. Numbers from Heretic's own README, on gemma-3-12b-it.

  original            97/100 refusals    KL 0
  mlabonne v2          3/100             KL 1.04
  huihui-ai            3/100             KL 0.45
  p-e-w heretic        3/100             KL 0.16

Make the point about the axes: everyone lands on the same refusal number.
Refusal suppression is easy. The entire competition is horizontal — how much
damage did you do getting there.

Heretic is roughly 3x less divergence than the best hand-made abliteration,
with zero human effort.

Caveat honestly, because the author does: these values are platform- and
hardware-dependent. That table was PyTorch 2.8 on an RTX 5090.

And the reproduce line — you'll actually run this in the demo:
  heretic --model google/gemma-3-12b-it --evaluate-model p-e-w/gemma-3-12b-it-heretic
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 4</div>

# What's actually on the Hub

## Measured, not estimated

---

<!-- _class: figure -->

# The scale

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

<!--
SCALE — 90 seconds.

13,841 models tagged uncensored. 10,947 tagged abliterated. 5,844 tagged
heretic. Heretic's own README still says "well over 4000" — it's 5,844 and
climbing weekly.

Then point at the sliver: 158.

"Same axis. Same ecosystem. That green sliver is every Heretic model that
ships a reproduction record."

Who's publishing: p-e-w and heretic-org are the reference models. mlabonne
and huihui-ai have large hand-made catalogues. failspy is the original
abliterator lineage. And then mradermacher and DavidAU, who are mass
re-quantizers — they take other people's models and ship GGUF conversions
at enormous volume.

That last category is the one that matters for Part 6. Hold it.
-->

---

<!-- _class: lite -->

# What people actually download

```
DavidAU/Qwen3.6-40B-Claude-4.6-Opus-Deckard-Heretic-
Uncensored-Thinking-NEO-CODE-Di-IMatrix-MAX-GGUF
```

460,419 downloads

<!--
THE FILENAME — 90 seconds. This slide is funnier and darker than it looks.

Read the name out loud. Slowly. Let them hear how long it is.

Now decode it: a base model (Qwen3.6-40B), a distillation from Claude 4.6
Opus, a merge, an abliteration (Heretic), a thinking variant, a code
fine-tune, an importance-matrix quantization, and a "MAX" variant.

That's roughly eight transformations.

"Every one of those is encoded in the filename. Why? Because the filename is
the only provenance record that survived."

For scale, the top heretic-tagged model has 1.74 million downloads. These are
not curiosities. This is what the local-LLM ecosystem actually runs.

If you want the uncomfortable follow-up: nobody in this chain is malicious.
They're enthusiasts shipping useful things fast. The evidence just falls on
the floor at every hop, and no one notices because nothing breaks.
-->

---

<!-- _class: figure -->

# The modality surprise

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

<!--
VLMs — 2 minutes. This one genuinely surprises people, including me.

Across all 5,844 heretic models, the single largest DECLARED pipeline tag is
image-text-to-text at 1,562 — ahead of plain text-generation at 1,541.

Vision-language models are the most abliterated category on the Hub.

Why it works — and this is the part worth saying carefully:

"The refusal direction lives in the shared residual stream of the language
backbone. The vision encoder feeds into that same stream. So when you
orthogonalize the backbone, you have removed refusal for image-conditioned
prompts too."

Then the consequence: "That's a safety surface nobody evaluated separately.
The refusal benchmark was 400 text prompts. The deployed model accepts
images."

There are also any-to-any models (255k downloads on one gemma variant),
ASR-tagged repos, and translation models in there. Heretic supports dense
models, several MoE architectures, hybrids like Qwen3.5, and many multimodal
models. Pure state-space models are the main thing it doesn't handle.
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 5</div>

# Live

## Let's actually run it

---

<!-- _class: figure -->

# The pipeline

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

<!--
THE DEMO SETUP — 60 seconds, then switch to the terminal.

This is Wellspring — the repo this talk came out of. Heretic in the middle,
then two completely independent export paths: MLX for Apple Silicon, GGUF for
llama.cpp and Ollama.

They never cross-feed. Same source checkpoint, separate calibration data,
separate tooling, separate output directories. That's deliberate — if they
shared anything, a regression in one would show up as a regression in the
other with no way to tell which stage caused it.

Point at the green badges: every artifact emits a .provenance.json sidecar
recording commits, seeds, parameters, and this repo's own git state.

What the diagram doesn't show — say it in one breath, don't dwell:
  - `DECENSOR=0` skips Heretic and exports any local model as-is; manifests
    are tagged decensored=false, so the sidecar can't lie about it.
  - Every stage is tracked in MLflow, and the whole pipeline also runs as a
    Metaflow flow — `python src/flow.py resume` retries only the failed step,
    which matters when one step is a multi-hour GPU run.
  - `FINETUNE=1` adds an optional Red-vs-Blue backdoor exercise to the same
    flow. That's the detection slide in Part 7.

Now go to the terminal. DEMO ORDER ON THE NEXT SLIDE.
-->

---

<!-- _class: lite -->

# Demo

```sh
make doctor
heretic --model google/gemma-3-12b-it \
        --evaluate-model p-e-w/gemma-3-12b-it-heretic
```

<!--
LIVE TERMINAL — 5 minutes. THIS IS THE SAFE DEMO. Rehearse it.

1. `make doctor` — preflight. Checks CPU/RAM/disk/VRAM before you spend
   hours. Note it has NO prerequisites: it runs before .venv exists, because
   the point is answering "is this box even worth setting up." Show that it
   checks free space at BOTH the output path and the resolved HF_HOME cache,
   and warns if they share a filesystem. A full default run is ~260GB.

2. `--evaluate-model` — THE demo. It skips the entire 200-trial search and
   just scores an existing model against its base. Minutes, not hours. It
   regenerates the exact benchmark numbers from the slide earlier, live.
   This is the whole point: the claim is CHECKABLE.

   In main.py this path returns early at line 488 — it's a genuine standalone
   mode, unlike the flags below.

TRAP — do not run this live unless you mean it:
   `--print-residual-geometry` prints the per-layer geometry table and then
   FALLS THROUGH into the full 200-trial search. It does not exit. If you
   want just the table, Ctrl+C after it prints, or cap it with
   `--n-trials 1 --n-startup-trials 1`.
   Same for `--plot-residuals` — it's CPU-bound PaCMAP, pre-render it.

If you have a pre-baked run: show the saved GGUF loaded in LM Studio and ask
it something the base model refuses. Qualitative beats quantitative here.

3. Then `cat outputs/<model>-heretic.provenance.json` and point at
   `wellspring_dirty: true`. One boolean that says the pipeline that produced
   this artifact had uncommitted changes. That's the bridge to Part 6.

OPTIONAL, only with a pre-baked run and a spare minute: `mlflow ui` on an
existing `make optimize-gguf` study. It shows perplexity vs. refusal rate
measured on each QUANTIZED file. Keep it for the Part 7 payoff if you're
short on time. Don't launch a search live; each trial re-quantizes.
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 6</div>

# Chain of custody

## The part that actually matters

---

<!-- _class: statement -->
<!-- _transition: zoom 450ms -->

# You cannot read a 72 GB diff

<p>An abliterated checkpoint and a backdoored one are the same shape.</p>

<!--
THE PIVOT — 45 seconds. Slow down. This is the turn of the talk.

Everything up to here was mechanism. From here it's supply chain.

Code review works because a human can read a diff. There is no equivalent
artifact for weights. You cannot eyeball a tensor. You cannot review a
safetensors shard.

So the only thing that can distinguish a benign edit from a malicious one is
EVIDENCE ABOUT HOW IT WAS MADE. Not inspection of the thing itself.

"Provenance isn't bureaucracy here. It's the only available substitute for
review."
-->

---

<!-- _class: figure -->

# Seven hops, and evidence falls off at every one

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

<!--
THE DECAY — 2 minutes. Walk it left to right, naming what dies.

Hop 1, base model: which commit? Hub repos are MUTABLE. "Qwen/Qwen3-4B" is
not a version, it's a moving pointer.
Hop 2, prompt datasets: which commit defined "harmful"?
Hop 3, the tool: which Heretic version? Was it forked?
Hop 4, parameters: which trial won, and under which seed?
Hop 5, merge vs adapter.
Hop 6, quantization: by WHOM, with what calibration corpus?
Hop 7, re-upload: by a fourth party, renamed.

Point at the red chips falling. "Nothing downstream recreates these. Once
the hash is gone, it's gone — you can't re-derive it from the weights."

Where it usually breaks is hops 1 and 6.

Worth being fair about hop 1: Wellspring deliberately leaves MODEL_COMMIT
unpinned by default, and documents why. A fixed SHA is only valid for ONE
specific model — so a hardcoded default would silently point at the wrong
repo the moment someone overrides MODEL. Null is the safe default. Pinning
per-run is the operator's job.
-->

---

<!-- _class: lite -->

# Heretic ships a real answer

```json
{ "model": "Qwen/Qwen3.8-27B",
  "model_commit": "1d4bf0f2ff6012fd82039f2f…",
  "seed": 705085018,
  "fork": "github.com/timrohrbaugh/heretic",
  "weights_sha256": { "model-00001-of-00006…": "55a4ad…" } }
```

<!--
reproduce.json — 2 minutes. This is a REAL file, pulled from
heretic-org/Qwen3.8-27B-heretic-ara. About 10 KB.

What's in it, beyond what's on the slide:
  - the exact base model COMMIT, not just the repo name
  - the random seed
  - the winning Optuna trial number and its parameters
  - metrics: refusals 0, KL divergence 0.0534, broken down per harm category
  - full package versions: heretic-llm, torch, transformers, optuna...
  - the system: CPU model, GPU (NVIDIA H200 NVL), driver/API versions
  - SHA-256 of EVERY output safetensors shard

And look at the `fork` field. This model was built from a fork of Heretic,
and it says so, unprompted.

"That is what good looks like. Not a model card paragraph — a machine-readable
record that a third party can act on."

Heretic even ships `--collect-reproducibles`, which walks the Hub and
archives every public reproduce.json it can find.
-->

---

<!-- _class: lite -->

# And it grades the mismatch

| | |
|:---|:---|
| <span class="no">critical</span> | `heretic-llm` differs |
| <span class="no">high</span> | `torch` / `transformers`; accelerator type |
| <span class="mid">medium</span> | `optuna`, `peft`, driver, device list |
| <span class="ok">low</span> | Python, OS, CPU |

<!--
VERIFICATION — 90 seconds.

  heretic --reproduce <url-to-reproduce.json>

It re-checks YOUR environment against the original and grades every mismatch
on this four-level scale before it will proceed.

Then it tells you, plainly: "There is a {severity} chance that reproduction
won't produce a byte-for-byte identical model" — and asks whether to continue.

Make the point about intellectual honesty, because it's rare:

"It refuses to overclaim. It does not promise bit-exact reproduction, because
GPU floating-point reduction order isn't something a seed controls. It tells
you the probability class and lets you decide."

That posture — state what you control, state what you don't — is the standard
the rest of this ecosystem should be held to. Wellspring's own docs do the
same thing: seeds cover Python, NumPy, PyTorch and Optuna's search order, and
the docs say explicitly that bit-exactness across hardware is NOT guaranteed.
-->

---

<!-- _class: figure -->

# But almost nobody uses it

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

<!--
THE PAYOFF — 2 minutes. Callback to the opening number.

Every dot is ten models. 5,844 total.

360 claim the `reproducible` tag. Break that down, because the breakdown is
the story:
  - 186 are GGUF re-quantizations. They inherited the tag from their parent
    model card and shipped no reproduce.json at all.
  - 14 have the tag and no file.
  - 2 are gated.
  - 158 genuinely carry the record.

So the amber band is "claims it, ships nothing" — 202 models. The green sliver
is real: 158. That's 2.7%.

The killer detail, and Heretic's own source anticipates it: its
collect_reproducibles() function explicitly SKIPS repos tagged gguf, and
handles "tag present but no file" as a normal case. The author knew this
would happen.

"A metadata tag is a string that gets copied. A chain of custody is work that
has to be redone at every single hop. Guess which one survives."
-->

---

<!-- _class: statement -->
<!-- _transition: zoom 450ms -->

# The tag survived. The evidence did not.

<p>186 repos advertise <code>reproducible</code> while shipping no reproduction record.</p>

<!--
20 seconds. Say it, pause, move on. Don't over-explain — the previous slide
did the work.

If you want one extra beat: "Nobody lied. The tag was just... copied. That's
how provenance dies — not fraud, entropy."
-->

---

<!-- _class: figure -->

# Meanwhile the format itself is hostile

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

<!--
SUPPLY CHAIN — 2 minutes. These are all real, cited, published figures.

  96%  of unsafe-serialized HF model files were exploitable (arXiv:2410.04490)
  89%  gadget bypass rate against the BEST available scanner (arXiv:2508.19774)
  63%  ShadowPickle "overwritten module" evasion (arXiv:2607.17503)
  62%  of unsafe files not flagged by HF's own scanner (arXiv:2410.04490)

Real incidents, not theory:
  - JFrog, 2024: roughly 100 genuinely malicious models on the Hub. One,
    baller423/goober2, carried a reverse shell via pickle __reduce__.
  - ReversingLabs, Feb 2025 — "nullifAI": PyTorch pickles compressed with 7z
    so torch.load() couldn't open them, which meant Picklescan never flagged
    them. The payload executed BEFORE the stream broke. HF fixed it in 24h.
  - PickleCloak disclosed 22 pickle load paths, 19 of which every scanner
    missed, plus 133 exploitable gadgets. $6,000 bounty paid.
  - ShadowPickle is the first attack to evade PyTorch's weights-only unpickler.

Then the green bar — the one piece of genuinely good news:

"safetensors is not an executable format. There is no code path. Heretic
outputs it by default. This is the one free win on the slide — take it."

Caveat so you're not overselling: safetensors solves arbitrary code execution
at load time. It does nothing about whether the weights themselves were
tampered with. That's the next slide.
-->

---

<!-- _class: figure -->

# What a real chain of custody looks like

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

<!--
SIGNING — 2 minutes.

OpenSSF Model Signing — the OMS spec, with sigstore/model-transparency as the
reference implementation.

  pip install model-signing
  model_signing sign <MODEL_PATH>
  model_signing verify <MODEL_PATH> --signature <SIG> \
      --identity <ID> --identity_provider <OIDC>

What it actually produces: a DETACHED Sigstore bundle. Inside is a DSSE
envelope wrapping an in-toto statement, which contains a manifest of every
file in the model keyed by SHA-256. It's PKI-agnostic — bare keys,
self-signed certs, enterprise PKI, or keyless Sigstore.

The transparency log is the part worth dwelling on: keyless signing events go
into Sigstore's append-only public log. So a verifier can check an inclusion
proof, and a publisher can MONITOR the log for signing events under their own
identity — which catches a rogue insider shipping something in your name.

Now the caveat, and it's the whole reason this slide is amber not green:

"Signing proves WHO made it and that it HASN'T CHANGED. It does not prove it
is safe. A correctly signed abliterated model is still abliterated."

Provenance answers "who made this, from what". It never answers "should I run
it." For that, you need Part 7.

Also worth naming: AI-BOM / ML-BOM via CycloneDX 1.6, and SLSA provenance
for the build. And the legal layer people forget — an abliterated model is a
derivative work with an inherited licence graph. In this repo alone that
means AGPL on heretic-llm and CC-BY-NC-4.0 on the default Alpaca calibration
corpus. Answer those before you ship commercially, not after.
-->

---

<!-- _class: divider -->
<!-- _transition: iris-out 500ms -->

<div class="kicker">Part 7</div>

# What "it works" has to mean

## Evaluation

---

<!-- _class: lite -->

# The metric being optimized is a keyword search

```toml
refusal_markers = [ "sorry", "i cannot", "as an ai",
                    "illegal", "unethical", … ]   # 33 total
```

<!--
THE PROXY — 90 seconds.

Heretic decides whether a response is a refusal by substring-matching against
exactly 33 strings. That's the entire definition.

Be fair first — this is a defensible engineering choice:
  - it's fast enough to run 200 times inside an optimization loop
  - it's completely transparent; you can read the whole definition in one
    screen. Compare that to an opaque learned classifier.

Then the problems:
  - FALSE NEGATIVE: a polite deflection containing none of those words scores
    as compliance.
  - FALSE POSITIVE: a genuinely helpful answer that happens to mention "this
    is illegal in most jurisdictions" scores as a refusal.
  - And the structural one: it is the OPTIMIZER'S TARGET. Two hundred TPE
    trials are searching for parameters that minimize keyword hits.
-->

---

<!-- _class: figure -->

# The quadrant that keyword matching can't see

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

<!--
THE STRONGEST ARGUMENT IN THE TALK — 2 minutes. Take your time.

Arditi et al. deliberately scored every completion on TWO independent axes:
  - REFUSAL SCORE: does it contain a characteristic refusal substring?
  - SAFETY SCORE: does it actually contain harmful content?

Two axes because one was not enough. The authors knew.

Point at the amber quadrant: no refusal phrases, and no harmful content.
A model that has learned to stop SAYING "I'm sorry" while still declining to
actually help. Keyword matching scores that as total success. It is not.

"Heretic's optimizer only measures the horizontal axis. That second metric —
the one the original paper considered essential — did not survive into the
tool the entire ecosystem now uses."

Be scrupulously fair here, because the criticism is stronger when it's fair:

"That's a defensible engineering tradeoff. You cannot run an LLM judge inside
200 optimization trials; it would take days. The problem isn't that Heretic
optimizes a proxy. The problem is that for almost everybody, the proxy is
also the acceptance test. The judge has to come back at the END."
-->

---

<!-- _class: statement -->
<!-- _transition: zoom 450ms -->

# Optimizing against a proxy optimizes the proxy

<p>The metric that guides the search can never be the metric that validates the result.</p>

<!--
30 seconds. This is Goodhart, stated for this specific case.

200 trials searching for "fewest keyword matches" will happily find
parameters that suppress the WORDS rather than the BEHAVIOUR. Not because
anything is broken — because that is literally what you asked for.

This generalises well beyond abliteration, and if your audience is ML
platform people, say so: any time your training objective and your
acceptance gate are the same function, you have no acceptance gate.
-->

---

<!-- _class: figure -->

# Where you actually need to be

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

<!--
ACCEPTANCE TESTING — 90 seconds.

Two axes that matter:
  - HOW you measure refusal: keyword list vs. an LLM judge or human review
  - WHAT you measure it on: the in-memory checkpoint vs. the shipped,
    quantized artifact

Bottom-left is where Heretic operates, and that's correct for a search loop.
Top-right is where an acceptance gate has to live. Essentially nobody is there.

Concretely, axis one — use real harness work, not substrings:
  JailbreakBench, HarmBench, StrongREJECT (built specifically to correct
  overstated jailbreak success rates), AdvBench.

And axis two is the next slide, which is the gap I care most about.

Also run capability regression against the base — MMLU, GSM8K, HellaSwag,
PIQA, perplexity on a held-out corpus. Heretic has --benchmarks (lm-eval)
built in. Run both axes or you have measured nothing.
-->

---

<!-- _class: figure -->

# Nobody measures the thing they ship

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

<!--
THE GAP — 2 minutes. This is the closing technical argument. Callback to D1.

Heretic scores its own in-memory, full-precision model. Refusals 3/100,
KL 0.16. Those numbers are real and they're honestly measured.

Then that checkpoint gets quantized to Q4_K_M or AWQ 4-bit, and shipped.
And nothing re-checks it. Ever.

Why that isn't pedantry — and this is where the first diagram pays off:

"Remember the refusal direction was about 0.7% of activation magnitude. It is
a tiny, targeted, low-magnitude edit. Then you run every weight in the model
through a 4-bit quantizer."

An edit that small is precisely the kind of signal quantization can partially
undo — or amplify. So the shipped model might refuse MORE than measured,
might refuse LESS, might be meaningfully dumber.

"Nobody knows. Because the measurement was taken on a different artifact than
the one you downloaded."

And recall the earlier number: 56% of heretic-tagged repos — 3,292 of them —
are GGUF re-quantizations. The quantized copy is not an edge case. It is the
majority of what ships.

This is what Wellspring now does (spec 001, implemented): `make optimize-mlx`
and `make optimize-gguf` score perplexity AND refusal rate on the real
quantized MLX/GGUF file. Optuna runs a two-objective search over quantization
parameters, the objectives are never collapsed into one score, and MLflow
logs every trial.

Be honest about the limit, because someone will ask: the refusal scorer
there copies Heretic's keyword markers verbatim. So it closes the "which
artifact" axis, but not the "keywords vs. judge" axis from the previous slide.
It moves you from bottom-left to top-left, not top-right.
-->

---

<!-- _class: lite -->

# Can you spot a tampered checkpoint?

<div class="cols">
<div>

### Weight-diff "MRI"
precision@2: **2/2 · 0/2 · 1/2**
same code, different runs

</div>
<div>

### Behavioural probe
correct **every run**
decoys 0 hits, sleepers ≥ 1

</div>
</div>

<!--
DETECTION — 2 minutes. This answers the question the room is already asking.

Wellspring has an optional exercise called "Spot the Sleeper". Red fine-tunes
a lineup of five variants of the same base using an identical recipe. Two of
them carry a hidden trigger that emits a harmless, labelled canary. Blue gets
only the weights and has to say which ones are the sleepers.

Blue has two tools.

LEFT — the MRI. Diff every variant's weights against the base and rank by
robust z-score. It sounds like exactly the structural check you'd want. On
the same code, precision@2 came out 2 of 2, 0 of 2, and 1 of 2 as we varied
the base, the scale, the number of adapted layers and the poison rate. At
full scale on BOTH bases it ranked two decoys first. LoRA training noise in
the small GQA k/v matrices outranks the signal.

RIGHT — the probe. Feed candidate triggers and count how often the payload
fires. Decoys scored 0 and sleepers at least 1, in every run, at every
scale, on both bases (measured 0,1,0,0,9 on TinyLlama and 0,2,0,0,10 on
SmolLM2).

The line to land:
"The weights nominate. Behaviour convicts."

Then the catch, which ties back to Part 6: the probe only finds a trigger in
its wordlist. With a custom trigger and the built-in list it flagged 0 of 5
models. Structural diffing also needs the exact base commit. Detection
depends on provenance too.

Source: vault/references/2026-09-25-methodology-register.md. Small models,
our runs. Frame it as "what we measured", not as a general law.
-->

---

<!-- _class: lite -->

# Two lists

<div class="cols">
<div>

### Publishing
pin the base commit
pin the dataset commits
record seed + trial
ship `reproduce.json`
safetensors, never pickle
sign it

</div>
<div>

### Deploying
judge, not keywords
capability vs. base
**test the quantized file**
verify the signature
guardrails are yours now

</div>
</div>

<!--
THE ACTIONABLE SLIDE — 90 seconds. This is what people photograph.

Left column is cheap. Every item is minutes of work, and Heretic or the Hub
already supports all of it. Pinning MODEL_COMMIT is one flag.

Right column is the one people skip. Call out the bolded item specifically:

"Test the artifact you will actually load. Not the checkpoint it came from.
If you take one operational thing from this talk, take that."

And the last line is a mindset shift, not a task:

"Once refusal is orthogonalized out of the weights, every guardrail your
deployment has is one YOU built. Input filtering, output classification,
monitoring, access control. That's a completely legitimate architecture —
plenty of serious systems run exactly that way.

It's only a problem when it happens BY ACCIDENT, because somebody downloaded
a checkpoint whose provenance nobody checked."
-->

---

<!-- _class: number -->
<!-- _transition: zoom 450ms -->
<!-- _header: '' -->

<div class="huge">2.7<em>%</em></div>

<div class="sub">

of Heretic models on Hugging Face can prove how they were made.<br>
**The tooling to fix this already exists.**

</div>

<!--
CLOSE — 60 seconds. Bring it back to the opening number.

Everything needed already exists and is free:
  - reproduce.json is built into the tool
  - safetensors is the default output
  - OpenSSF model signing is a pip install
  - AI-BOM has a CycloneDX spec

None of this is a research problem. It's a discipline problem.

FINAL LINE — land it and stop talking:

"The interesting question was never 'can you remove refusal from a model.'
Obviously you can — 5,844 times over. The interesting question is whether you
can prove what's in the weights you're about to run. Today, for 97% of this
ecosystem, the answer is no."

Then take questions.
-->

---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Thank you

## *"Can you prove what's in the weights you're about to run?"*

<div class="meta">

Wellspring — Heretic → MLX / GGUF pipeline · MLflow · Metaflow · Spot the Sleeper<br>
`README.md` · `PROVENANCE.md` · `COMPATIBILITY.md` · `docs/finetuning/`

</div>

<!--
LIKELY QUESTIONS — prepared answers:

Q: Isn't this just a jailbreak?
A: No. A jailbreak is a prompt-time attack on a model you don't control.
   This is a permanent weight edit producing a new checkpoint that you
   redistribute. Different threat model entirely — that's why it's a supply
   chain problem and not a prompt-filtering problem.

Q: Can you detect abliteration in a checkpoint?
A: Partially. You can compare against the base model's weights if you know
   which base and which commit — which is exactly the provenance problem.
   Tensor-level comparisons have been published. But without the base
   reference, you're measuring behaviour, not structure. And our own
   Spot-the-Sleeper runs (the detection slide) found weight-diff ranking
   unreliable for fine-tuned backdoors even WITH the base. Behavioural
   probing is what held up.

Q: Does quantization remove the abliteration?
A: Not established in general. I know of no published systematic study.
   Wellspring can now measure it for YOUR checkpoint: `make optimize-gguf` /
   `make optimize-mlx` score refusal rate and perplexity on each quantized
   file, logged to MLflow. Caveat: that refusal score is still keyword-based.
   Don't quote numbers you haven't run.

Q: What's in the repo beyond this talk?
A: The Heretic → MLX/GGUF pipeline with provenance sidecars, MLflow tracking,
   a resumable Metaflow flow, the Spot-the-Sleeper Red/Blue exercise, and a
   spec index (ROADMAP.md) for what's next: export dispatch, Pareto reporting,
   a meta-search over Heretic's settings.

Q: Should Hugging Face ban these?
A: Not my call, and I'd push back on the framing. 13,841 models carry an
   uncensored tag. The enforceable ask is provenance, not prohibition —
   require signed artifacts and machine-readable lineage.

Q: What about closed models?
A: Doesn't apply — you need the weights. This is exclusively an open-weights
   phenomenon, which is part of why open-weight governance is a distinct
   problem from API governance.

Q: How do I know YOUR numbers are right?
A: You don't — re-run them. The script is in the appendix and it hits the
   live API. That's the whole ethic of the talk.
-->

---

<!-- _class: refs -->

# References

- **Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, Nanda (2024)** — *Refusal in Language Models Is Mediated by a Single Direction* — arXiv:2406.11717v3 · NeurIPS 2024
- **Heretic** — github.com/p-e-w/heretic · `heretic-llm` · AGPL-3.0-or-later · huggingface.co/heretic-org
- **Labonne** — huggingface.co/blog/mlabonne/abliteration · **Lai (grimjim)** — projected / norm-preserving biprojected abliteration
- **Prior art** — FailSpy/abliterator · wassname/abliterator · Tsadoq/ErisForge · Sumandora/remove-refusals-with-transformers · AUGMXNT/deccp
- **JFrog (2024)** — malicious HF models with silent backdoor · **ReversingLabs (2025)** — *nullifAI*
- **Casey, Santos, Mirakhorli (2024)** — arXiv:2410.04490 · **PickleCloak (2025)** — arXiv:2508.19774 · **ShadowPickle** — arXiv:2607.17503
- **OpenSSF Model Signing (OMS)** — openssf.org/projects/model-signing · github.com/sigstore/model-transparency
- **Evaluation** — JailbreakBench · HarmBench · StrongREJECT · AdvBench · lm-evaluation-harness · CycloneDX 1.6 ML-BOM · SLSA

---

<!-- _class: refs -->

# Appendix — reproduce the Hub figures

```python
from huggingface_hub import HfApi
api = HfApi()

for tag in ("heretic", "abliterated", "uncensored"):
    print(tag, sum(1 for _ in api.list_models(filter=[tag])))

tagged = ok = missing = gguf = gated = 0
for m in api.list_models(filter=["heretic", "reproducible"], expand=["tags", "gated"]):
    tagged += 1
    if m.tags and "gguf" in m.tags:   gguf += 1;  continue
    if m.gated:                       gated += 1; continue
    try:
        info = api.get_paths_info(m.id, "reproduce/reproduce.json")
    except Exception:
        gated += 1; continue
    ok, missing = (ok + 1, missing) if info else (ok, missing + 1)

print(f"{tagged=} {gguf=} {gated=} {ok=} {missing=}")
```

**Re-run before presenting.** Counts move weekly — and the point of the talk is that claims should be checkable.
