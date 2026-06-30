<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Ursprung Channel Profiler — v0.1 spec note

**Status: design specification — SCOPED. The estimator primitives exist; the live profiler does not.** This is
the "wedge" artifact: not a renderer, not an engine — a tool that turns an existing interactive pipeline into a
**QIF-measured channel** and reports, with honest uncertainty, how many bits an observer learns about a secret
per interaction. It is **OBSERVER-class**: it measures and alerts; it never mutates the host loop. Adaptation is
an opt-in callback the *host* chooses to act on. `telemetry ≠ control`; `measured ≠ guaranteed`; `estimate ≠
capacity`.

> **Tagline that survives the sieve:** *"What your observer learns — in bits, with error bars."* Not "first,"
> not "guaranteed." The avoid-list (`❌ first system to…`, `❌ mathematical guarantee…`) is correct and adopted.

---

## 1. The wedge thesis

Ship the smallest thing that *measures what nobody profiles*: information-theoretic leakage for a **live**
interactive session. Performance profilers (RenderDoc, Nsight) measure fps; SAST/DAST scan for vulnerabilities;
IFC type systems (LIO/Jif/FlowCaml) answer the **binary** "does S reach O?"; research QIF tools (CHIEF,
model-counting) are **static** analyzers. None answer, at runtime, *how many bits does the observer learn about
the secret this window?* That is the gap, and it is real. The profiler is non-invasive (drop-in tags, exits
clean when disabled), so a user tries it tomorrow without migrating off their stack.

This is a genuinely good wedge **provided** it ships with its uncertainty, not as a false oracle (§4).

---

## 2. What it is

A Python library + CLI wrapping an existing loop:

```python
from ursprung import ChannelProfiler

profiler = ChannelProfiler(
    observer_budget=0.5,     # bits/window the host DECLARES acceptable (a policy, not a proof)
    window=4096,             # samples per estimate — NOT "every 60 frames" (see §4)
    estimator="ksg",         # named class; the result is "leakage per estimator E", never "the leakage"
    output="metrics.jsonl",
)
profiler.start()
while running:
    handle_events(); update(dt)
    profiler.tag_secret("enemy_ai_state", ai_internal_state)     # structural: this is hidden (Genealogy A)
    profiler.tag_observation("rendered_frame_digest", obs)        # structural: this is observable
    render()
    profiler.end_frame()
    # OBSERVER-class: a measurement + an ALERT, not a block. The host opts in to adapt.
    if profiler.over_budget():            # only true once a window has enough samples
        maybe_reduce_detail(profiler.estimate())   # .estimate() returns (point, lo, hi, n, estimator)
profiler.stop()
```

`metrics.jsonl` carries, per *window* (not per frame): the MI **point estimate with a confidence interval**, the
sample count, the estimator class, and whether the declared budget was crossed. It never emits a bare scalar.

---

## 3. The two-genealogy mapping (consistent with `INFORMATION_MEDIATION_RUNTIME_SPEC.md`)

| Profiler piece | Genealogy | Tier | Status in repo |
|---|---|---|---|
| `tag_secret` / `tag_observation` — *which values are secret vs observable* | **A — Goguen–Meseguer** (structure: does the channel exist?) | static / structural | `Grounded<T>` provenance tagging exists (Rust core) |
| residual MI estimate over the window | **B — Mestel / Alvim** (capacity: how many bits?) | runtime / measured | `residual_channel` (conditional-MI, **discrete binner**) exists — **needs the §4 work** |
| budget threshold + alert | declared policy + Shannon/g-vulnerability bound | runtime | thin adapter — to build |
| fidelity-adjust callback | adaptive-representation literature | host-side, opt-in | scaffolding — to build |

`tag` answers *structure* (typeable); the estimate answers *capacity* (measured). Conflating them is the
category error the whole project guards against.

---

## 4. The load-bearing caveat: estimator reliability (this is the actual v0.1 work)

The example's "measure every 60 frames" is the one thing that would sink the product if shipped naively. **MI
estimation from few samples is badly biased** (Paninski, 2003): a reliable estimate needs sample count *large
relative to the effective alphabet*; with `#bins ≈ #samples` the estimate is dominated by bias, not signal. A
60-sample window over any non-trivial observation space yields a number that *looks* like leakage and isn't.
Therefore v0.1 must:

- **Report confidence intervals, never point estimates.** Bootstrap CIs + the within-Z shuffle null the repo
  already uses; the headline is `(lo, hi, n, estimator)`. `point-estimate ≠ capacity`.
- **Window by sample sufficiency, not frame count.** Accumulate until the estimator's CI is tight enough, or
  declare `UNDERDETERMINED` for that window. A too-small window returns "don't know," not a fabricated bit-count.
- **Pick an estimator honestly and name it.** The shipped `residual_channel` is a **discrete binner** — fine for
  low-dimensional categorical channels, degrades on continuous/high-dim observation (real pixel/feature spaces).
  A continuous estimator (KSG k-NN, or a neural MI bound like MINE) is the upgrade — each is a *hypothesis class*
  (`I=0 under estimator E ≠ I=0`), so the class travels with every number.
- **Run off the hot path.** §6 of the gateway measured the CMI audit at **~9.7 MB/s** — too slow for per-frame
  inline use. The profiler samples (1-in-N) and estimates on a **background/windowed** cadence; the per-frame
  path does only the O(1) tag capture. `windowed-audit ≠ inline-filter`.

This section *is* the engineering. "Everything but the alert already exists / thin orchestration layer"
understates it: the primitives exist, but a *trustworthy live estimate with CIs at adequate sample sizes* is the
real build. `primitives-exist ≠ product-built`.

---

## 5. What it does NOT claim (does_not_show)

- **Not "first."** Prior art exists across both genealogies (§3) and in QIF tooling (CHIEF, model-counting).
  Novelty is the *closed-loop, runtime, interactive* composition — stated as composition, not invention.
- **Not a guarantee.** Every number is an estimate against a named estimator, observer class, and window —
  `tested ≠ safe`; `secure-against-this-observer ≠ secure` (a richer adversary sees more).
- **The "data moat / our vocabulary becomes the industry standard" idea is a *marketing hypothesis*, not a
  property of the artifact.** A user can re-run the profiler anytime; the data isn't locked in unless someone
  hosts it. Owning a measurement *standard* is an adoption outcome to earn, not a technical claim. Keeping it out
  of the spec is the point. `marketing = hypothesis`.
- **License is a conscious decision, not a default.** The repo is **AGPL-3.0**. The pitch's "Apache-2.0 + CLO for
  the open core" is a real strategic choice with real trade-offs (copyleft reach vs adoption friction) — flagged
  here as a decision the author must make deliberately, not silently inherit.

---

## 6. v0.1 scope

**Must-haves (the honest minimum that is actually trustworthy):**
1. `ChannelProfiler` Python wrapper — `tag_secret` / `tag_observation` / `end_frame` / `estimate` / `over_budget`.
2. The estimator behind a stable interface, **with CIs and an `UNDERDETERMINED` verdict** when samples are
   insufficient — reusing `residual_channel`; differential-tested for decision-parity against the reference.
3. Sampling + background/windowed estimation (off the hot path).
4. Metrics export: JSONL (point, lo, hi, n, estimator, budget-crossed) + optional Prometheus endpoint.
5. **One toy demo** (a seeded PyGame/sim scene) that shows a window go `UNDERDETERMINED → estimate-with-CI →
   over-budget → host reduces detail → back under` — the closed loop, end-to-end, on one scene. *This demo is
   the proof the loop exists* (the open item from the runtime spec).

**Deferred (post-v0.1):** continuous/neural estimator; VS Code overlay; CI budget-gate; cross-engine baseline
benchmark suite; the full adaptive renderer; the weltwerk verification track (separate messaging).

---

## 7. Risks & honest mitigations

| Risk | Mitigation |
|---|---|
| MI estimate unstable / biased at small N | CIs + bootstrap + shuffle-null; `UNDERDETERMINED` below sample sufficiency; never a bare scalar (§4) |
| Overhead stalls the host loop | 1-in-N sampling; estimate on a background thread; per-frame path is O(1) tag capture only |
| Adversary bypasses the measured channel | Publish the **threat model**: passive observer within the *declared* channel topology; out-of-band/side channels are out of scope and *said to be* (`undetected ≠ absent`); optional watermark probes to detect active tampering |
| "Competitor forks and ships faster" | This is a go-to-market hypothesis, not a technical moat. Reference-implementation authority is *earned* by being the most honest/calibrated, not asserted. License choice (§5) is the lever, consciously made |

---

## 8. The one milestone that matters

Build-path step from the runtime spec, made concrete: **close one loop on one seeded toy scene end-to-end**
(must-have #5). Until that demo runs, "closed-loop QIF profiling" is SCOPED; after it runs (with CIs, on one
scene), it is the smallest honest MEASURED instance of the thing no deployed tool does. Everything else in this
spec is scaffolding around that single proof.

---

Sources: Goguen & Meseguer, "Security Policies and Security Models," **IEEE S&P 1982** (noninterference) ·
[Mestel, "Quantifying information flow in interactive systems," CSF 2019 (arXiv 1905.04332)](https://arxiv.org/abs/1905.04332) ·
[Alvim et al., *The Science of Quantitative Information Flow*, Springer 2020](https://link.springer.com/book/10.1007/978-3-319-96131-6) ·
Paninski, "Estimation of Entropy and Mutual Information," **Neural Computation 2003** (the small-sample bias
result) · Kraskov, Stögbauer & Grassberger, "Estimating Mutual Information," **Phys. Rev. E 2004** (KSG k-NN
estimator) · Belghazi et al., "MINE: Mutual Information Neural Estimation," **ICML 2018** — all by name/venue.
