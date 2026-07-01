<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# repe_harness — an inference-time RepE alignment harness (an *adjacent* arc)

`adjacent != on-mission`: a representation-engineering harness for open-weight models (LLaMA-3 / Mistral) —
NOT part of the renderer/verification core. Anchored in RepE (Zou et al. 2023, arXiv:2310.01405); bounded by
*No Red Lines* (formal LLM safety guarantees are impossible in general). It **reduces harmful outputs
probabilistically** at inference — it does not, and cannot, prove unsafe states unreachable. `measured != guaranteed`.

## The two-status rule (never conflate them)
Every phase carries two separate statuses:

- **Apparatus** — does the mechanism itself work? Verified here by a **GPU-free `--selftest`** on synthetic
  ground truth.
- **Real-model number** — does it help on *your* weights + data? **NOT_MEASURED here**; you run it, the number
  decides. This tree asserts no number it did not compute.

The safety **claim** ("this makes the model safer") is **SPECULATIVE** until Phase 4's held-out ASR earns otherwise.

## Phases (apparatus, GPU-free)
| # | file | apparatus (verified, GPU-free) | the real number *you* measure |
|---|---|---|---|
| 1 probe | `phase1_probe.py` | MEASURED 3/3 — separable signal (AUROC 0.999), steering cos 0.976 | held-out probe AUROC on your model |
| 2 engine | `phase2_engine.py` | MEASURED 4/4 — zero-distortion observe, exact `α·v` steer, dual-metric | refusal-rate shift + benign retention |
| 3 monitor | `phase3_monitor.py` | MEASURED 5/5 — escalation AUROC 1.0, 0% benign FPR, causal, panel | multi-turn detection rate |
| 4 falsify | `phase4_falsify.py` | MEASURED 6/6 — grades success/null/regression, Wilson CIs, neutral-ruler | ASR reduction ± CI on held-out attacks |
| 5 governor | `phase5_closed_loop.py` | MEASURED 6/6 — damping = f(live CUSUM); simulator maps caught-vs-evaded | real-attack evasion boundary |
| 6 coherent-negative | `phase6_coherent_negative.py` | MEASURED 6/6 — space-pooled 0.89 vs trajectory 0.00, gap surfaced | the gap on real adaptive attacks |
| 7 regression-filter | `phase7_regression_filter.py` | MEASURED 8/8 — promotes genuine, rejects overfit/lucky/no-gain | real vector regression / drift |
| 8 confounder-firewall | `phase8_confounder_firewall.py` | MEASURED 5/5 — real→HEALTHY, confounded→CONFOUNDED, noise→NO_SIGNAL | which probe directions survive conditioning |
| 9 grounded-steer | `phase9_grounded_steer.py` | MEASURED 5/5 — healthy+tight→applied; confounded/loose→UngroundedError | structural guard (composes P8 + P1 CI) |
| 10 air-gap | `phase10_airgap.py` | MEASURED 6/6 — no-write-back, grounded-only commit (real `Grounded.value` **or** stub `.get()`), tamper→fail-closed | tamper/drift on your deployed run |

Run one gate: `PYTHONHASHSEED=0 python phaseN_*.py --selftest` (Windows + redirected output: `$env:PYTHONUTF8="1"`).

## Composition & verification (the spine that ties the phases to the kernel)
- **`orchestrator.py`** — the execution coordinator. Composes the proposed order
  `P8 → P9 → P3 → P4 → P10` on the **real** `weltwerk/verify` kernel: `residual_channel.audit` for the
  firewall and the real `ChannelEstablished` + `Grounded[T]` for the gate. A confounded/unstable direction
  **HALTS at P9** (`UngroundedError` before any effect); it returns a **panel, never a single "safe" scalar**.
  Apparatus MEASURED (selftest 11/11). This is the harness *consuming* the kernel — not
  `weltwerk/verify/orchestrator.py` (the kernel's own claim/action gate). `adjacent != on-mission`.
- **`epistemic_monad.py`** — a **law-checked** grounding monad (the adapter layer). `unit` / `bind` compose
  grounded steps as `EM.ok(Grounded[T]) | EM.fail(reason)`, short-circuiting **fail-closed** on the first
  ungrounded step — the same halt-on-ungrounded semantics as the orchestrator, expressed as an algebra. The
  three monad laws (left identity, right identity, associativity) are **VERIFIED by `--selftest` (8/8), not
  asserted**; if a law failed it would be relabelled (applicative / Kleisli arrow). It also absorbs the
  `.value/.get` seam via `value_of()`. `claim != code`.
- **`session_verifier.py` + `session_symbols.txt`** — grep-verify that every cited symbol appears **verbatim**
  in source (`claim != code`); per-symbol `VERIFIED / GHOST / UNREADABLE`, ambiguous basenames refused (no
  `head -1` trap). `python ../session_verifier.py --manifest ../session_symbols.txt` re-checks the whole set
  (currently **56 symbols VERIFIED**) as a gate.
- **`ingest_activations.py`** (Lever A) — real activations → held-out **probe AUROC** → real `audit` verdict →
  `Grounded` steer. Batched last-token extraction on CPU or the AMD 890M iGPU (no CUDA). `--selftest` (8/8,
  GPU-free) proves the chain rejects a length-confounder *even when raw AUROC is fooled high* (`AUROC != channel`).
  `data/make_neutral_contrastive.py` generates a balanced NEUTRAL cooking/math set for a stable demo AUROC.
- **`gen_index.py`** — drift-proof AST function index (`--check` fails if a committed `index.json` is stale).

## The bridge to the weltwerk kernel (real types)
`P8` runs `residual_channel.audit(samples_xyz, *, misspec_fns=…)` → a typed `ResidualChannelResult`. `P9`
wraps it as `ChannelEstablished(result)` and builds `Grounded.ground(steer, proof)` — which **grounds iff
`result.decision == "RESIDUAL_MISSPEC_STABLE"`** (a mis-specification-stable channel). `residual-CMI != channel`
until MISSPEC_STABLE; `misspec_fns` are **required** to reach it (a bare positive is only `RESIDUAL_DEPENDENCE`
and will not ground). The seam where the real `Grounded` (exposing `.value`) meets `phase10.commit` is now
**closed** — `commit` accepts a real `Grounded[T]` (`.value`) or a Phase-9 stub (`.get()`), no shim.

## Standing honest status
- **Apparatus — MEASURED** across phases 1–10 **plus** `orchestrator` (11/11), `epistemic_monad` (8/8, laws
  included), and `ingest_activations` (8/8). Every `--selftest` green, GPU-free, `PYTHONHASHSEED=0`. **On real
  weights:** the ingestion→audit→ground path is also MEASURED on Qwen2.5-1.5B — see *Real-model smoke result* below.
- **Safety claim — SPECULATIVE.** No phase, no coordinator, no monad changes this; only Phase 4 on real
  held-out attacks can. `integration != safety`.
- **Governor security — UNDERDETERMINED.** Phase 5 catches naive escalation + spikes but is **EVADED** by
  sub-threshold drift and pump/reset (2 of 4). `detection != prevention`.
- **Capstone (Phase 6) — a coherent negative** (weltwerk's sense): ~0.89 pooled vs ~0.00 along the adaptive
  trajectory; the harness reports **both views and refuses to average**. `panel != scalar`.
- **Hardenings 8/9/10** — confounder firewall (`confounded-MI != channel`), type-gated steer
  (`grounded != true`, a runtime pre-effect guard), air-gap (tamper-**evident**, **not** immutable;
  `detection != prevention`).

## What would earn MEASURED for the safety claim
Run Phase 1 `--extract` on your weights, feed real `(label, score, confounder)` to the audit, promote only a
`RESIDUAL_MISSPEC_STABLE` direction, then Phase 4's ASR-reduction CI on a **held-out** adversarial benchmark
(AdvBench / HarmBench — the shipped `data/contrastive_example.jsonl` is a **neutral** cooking-vs-math demo).
The claim earns MEASURED only from `phase4_falsify.grade()=="MEASURED"` with `neutral_ruler_ok(tune, eval)`, and
it carries a permanent `does_not_show`: robustness to *adaptive* attacks (Phases 5–6 show the arms race defeats it).

**Lever A — `ingest_activations.py`** turns real activations into this path: `--extract` (CPU or the AMD 890M
iGPU via ROCm-on-Windows; no CUDA needed; use a small 1–3B instruct model) → held-out **probe AUROC** (your
first real-model number) → the real `residual_channel.audit` verdict on your direction; a `RESIDUAL_MISSPEC_STABLE`
one grounds a steer. Its `--selftest` verifies the ingestion+audit chain GPU-free, including that a length-style
confounder is **rejected even when raw AUROC is fooled high** — `AUROC != channel`.

### Real-model smoke result — first real number (Qwen2.5-1.5B, CPU)
`python ingest_activations.py --extract --model Qwen/Qwen2.5-1.5B-Instruct --data data/neutral_contrastive.jsonl --layers 6,12,18 --device auto`
on an AMD Ryzen Z2 Extreme (Radeon 890M, 24 GB) — torch 2.12.1+cpu / transformers 5.12.1, `device=cpu`, `n_test=72`:

| layer | probe AUROC | audit decision | cmi | z | grounded | steer dim |
|---|---|---|---|---|---|---|
| 6 | 1.000 | `RESIDUAL_MISSPEC_STABLE` | 0.942 | 19.7 | yes | 1536 |
| 12 | 1.000 | `RESIDUAL_MISSPEC_STABLE` | 0.942 | 17.6 | yes | 1536 |
| 18 | 1.000 | `RESIDUAL_MISSPEC_STABLE` | 0.932 | 18.3 | yes | 1536 |

**Grade: MEASURED (apparatus, real model).** The extraction → probe → `audit` → `Grounded` chain runs on real
Qwen2.5-1.5B activations and returns real numbers (`steer_dim=1536` = true hidden size; `n_test=72` = a real
held-out split). This moves the *apparatus* from synthetic-only to **measured on real weights**.

**`does_not_show` (caveats nailed on — a perfect score is where inflation sneaks in):**
1. **Trivial task.** Cooking-vs-math is maximally separable; AUROC 1.0 shows the apparatus *fires*, not that the
   probe is powerful. `easy-task != capability`.
2. **Possible mild leakage.** The generator makes 240 rows but ~150 unique (template collisions), so identical
   strings can straddle the split. Mostly the easy task — but not ruled out; dedup for a clean number.
3. **Firewall unchallenged.** `RESIDUAL_MISSPEC_STABLE` here only means the topic channel isn't explained by
   *prompt length* — irrelevant to this task, so nothing to bite (identical `cmi` on layers 6/12 is the tell:
   perfect separation → identical discretized samples). A real confounder is needed to exercise the firewall.
4. **Not safety.** `separable != steerable`; `topic != harm`. The safety claim is untouched — still **SPECULATIVE**.

> The `--selftest` numbers remain apparatus on synthetic ground truth. The table above is a real-model **apparatus**
> smoke on a NEUTRAL dataset — it is **not** a safety measurement. A safety number needs a real harmful/benign set +
> held-out attacks + `phase4_falsify.grade()=="MEASURED"`. `apparatus != safety`.

## Run all gates
`PYTHONHASHSEED=0` on every run; on Windows with redirected output also `PYTHONUTF8=1`. Point the
`engineering-rigor` runner at this folder's `gates.txt` — which now includes `selftest-orch`, `selftest-monad`,
`selftest-ingest`, and the `session-symbols` manifest check alongside the ten phase selftests.

## References
RepE (arXiv:2310.01405) · Circuit Breakers, Zou et al. 2024 · *No Red Lines* (impossibility of formal LLM safety
guarantees) · `weltwerk/verify` (the coherent-negative / panel-not-scalar / `Grounded[T]` discipline this arc
borrows). `integrity != truth`; grades are point-in-time and re-checkable — re-run the gates.
