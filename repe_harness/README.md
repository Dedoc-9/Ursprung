<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# repe_harness — RepE probe & steering (Phase 1) · an *adjacent* arc

`adjacent != on-mission`: an inference-time **representation-engineering** harness for open-weight models
(LLaMA-3 / Mistral). NOT part of the renderer/verification core. Anchored in RepE (Zou et al. 2023,
arXiv:2310.01405) and bounded by *No Red Lines* (formal safety guarantees for LLMs are impossible in general).

## What it is / is not
- **Is:** extract contrastive activations across decoder layers, fit a per-layer linear probe (held-out AUROC),
  extract steering vectors (mean harmful − mean benign). Reduces harmful outputs **probabilistically** at inference.
- **Is not:** a proof that unsafe states are unreachable. No "diamond-hard" guarantee. `measured != guaranteed`.

## Grades (honest, point-in-time)
- **Apparatus** (probe / AUROC / steering math): **MEASURED** — `python phase1_probe.py --selftest` recovers a
  known-separable synthetic signal (held-out AUROC ~0.999), aligns the steering vector with the true direction
  (cos ~0.98), and returns ~0.5 on random labels. 3/3. *Falsifier:* break any of those and the selftest fails.
- **Real-model probe** (held-out AUROC on your weights + data): **NOT_MEASURED here** — run `--extract` on a
  machine with a GPU + the weights; the number is yours to measure. `does_not_show` downstream safety or
  robustness to unseen/adaptive attacks.
- **The safety claim** ("this makes the model safer"): **SPECULATIVE** until Phase 4 measures attack-success-rate
  reduction on a **held-out** adversarial benchmark, with the defense **not tuned on the eval attacks**
  (neutral ruler / anti-Goodhart).

## Run
- Validate the apparatus (no GPU): `PYTHONHASHSEED=0 python phase1_probe.py --selftest`
- Extract on your model + data:
  `python phase1_probe.py --extract --model meta-llama/Meta-Llama-3-8B-Instruct --data your_contrastive.jsonl --layers 8,12,16,20`
- Windows + redirected output: `set $env:PYTHONUTF8="1"` (non-ASCII prints crash a redirected cp1252 stdout).

## Dataset
`--data` expects JSONL lines `{"text": "...", "label": 0|1}` (1 = the concept to detect). `data/contrastive_example.jsonl`
is a **neutral** demo axis (cooking vs math) that exercises the plumbing safely. For the safety use-case, supply
your own harmful/benign contrastive set from a standard benchmark (e.g. AdvBench / HarmBench) — deliberately
**not shipped here**.

## Roadmap
- Phase 2 — forward-hook engine (read the probe / add the steering vector at inference).
- Phase 3 — multi-turn representation monitor (the honest "drift" tracker).
- Phase 4 — falsification harness: ASR before/after on a held-out attack suite, with confidence intervals; the
  claim earns MEASURED only from that.

Refs: RepE (arXiv:2310.01405) · Circuit Breakers, Zou et al. 2024 · *No Red Lines* (impossibility). `integrity != truth`.
