# Responsible Use

> [!CAUTION]
> **Wellspring removes safety behaviour from language models.** Models it
> produces will answer requests the original model refused. Read this whole
> document before you run the pipeline or use a model it produces.

## Purpose: education and research only

Wellspring is published **for educational and research purposes only**. It
exists to study how alignment behaviour is encoded in model weights, how
robust it is, and how it can be measured. Arditi et al. (2024) describe
refusal as mediated by a "one-dimensional subspace". This project reproduces
that line of work end to end, with provenance attached, so it can be studied
and audited.

Uses we consider in scope:

- Interpretability and alignment research into refusal mechanisms
- Red-teaming and safety evaluation of models and of downstream products
- Security research on systems **you own or are authorised to test**
- Benchmarking quantization and export quality (MLX / GGUF)
- Teaching, e.g. the conference talk in [`docs/presentation/`](docs/presentation/abliteration.md)

Wellspring is **not** a product. It is not intended to back a public service,
a hosted endpoint, or a consumer application.

## Legality depends on where you are

Laws governing AI models, the content they generate, and the use of that
content **differ by country, state, and region, and they are changing
quickly**. Something lawful in one jurisdiction may be a criminal offence in
another. Depending on where you live and what you do, the relevant law may
cover:

- AI-specific regulation, including transparency, labelling, and
  deployment obligations
- Content law: obscenity, hate speech, defamation, harassment, incitement
- Computer-misuse and anti-hacking statutes
- Export controls and sanctions on software, models, or technical data
- Copyright, database rights, and data-protection or privacy law
- Licence terms on the base model and datasets (see below)

**Before you download, modify, run, or share a model with Wellspring, you are
responsible for finding out which laws apply to you and following them.**
If you are unsure, get qualified legal advice where you live. Nothing in this
repository is legal advice.

## Prohibited uses

Whatever your jurisdiction, you may not use Wellspring or any model it
produces to:

1. Create, request, or distribute any content that sexualises, exploits, or
   endangers minors
2. Seek or provide real uplift toward chemical, biological, radiological,
   nuclear, or explosive weapons, or other mass-casualty harm
3. Attack, intrude on, or disrupt systems, networks, or critical
   infrastructure you are not explicitly authorised to test
4. Harass, stalk, dox, defame, impersonate, or defraud real people, or to
   produce non-consensual intimate imagery or deceptive deepfakes of them
5. Promote or facilitate self-harm or suicide
6. Produce anything that is illegal where you are, or where it will be
   received
7. Breach the licence or acceptable-use policy of the upstream model or any
   dataset used in the pipeline

## Your responsibilities as an operator

An abliterated model **has no built-in guardrails**. If you run one, you are
responsible for adding them:

- **Access control.** Keep models local or behind authentication. Do not
  expose them to anonymous or underage users.
- **Filtering and review.** Add input and output filtering, and have a human
  review output where it matters. The weights will not refuse on your behalf.
- **Labelling.** If you share a produced model, state clearly that it is
  abliterated and has reduced safety behaviour. Include its
  `.provenance.json` and a link to this document.
- **Licences.** Anything you produce inherits the upstream model's licence,
  and the licences in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
  Two flags matter here: `heretic-llm` is **AGPL-3.0-or-later**, and the
  `tatsu-lab/alpaca` calibration data is **CC-BY-NC-4.0** (non-commercial).
- **Age.** You must be at least 18, or the age of majority where you live if
  that is higher.

## No warranty, no liability

Wellspring is provided **"as is"** under the [MIT License](LICENSE), without
warranty of any kind. The maintainers and contributors are **not responsible**
for how you use the software or any model it produces, or for any output
those models generate. **You alone are responsible for your actions and their
consequences.**

## In the community

- Issues, PRs, and discussions are for **the tooling**: the pipeline,
  quantization, provenance, and compatibility. Do not post harmful model
  outputs, jailbreak transcripts aimed at real-world harm, or requests for
  help with prohibited uses. They will be removed, and may lead to a ban under
  the [Code of Conduct](CODE_OF_CONDUCT.md).
- If you believe Wellspring or a model it produced is being used for a
  prohibited purpose, report it privately to **joshburt@shapeandshare.com**.

By cloning, running, or distributing Wellspring or its outputs, you confirm
that you have read and accept this document.
