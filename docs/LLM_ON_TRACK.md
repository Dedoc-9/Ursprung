# Keeping an LLM on track with the Reality_Engine workbench

> Source-derived. This synthesizes the *specific* mechanisms the sealed `Reality_Engine`
> (Chronicle/Dentatus) workbench exposes for running an LLM coding partner at high velocity **without** it
> drifting off the Ursprung renderer track. Each entry maps a workbench mechanism → how Ursprung uses it →
> its honest bound. Drawn from the workbench's `README.md`, `OVERVIEW.md`, `AGENTS.md`, and the subfolder
> READMEs (`llm_toolkit`, `guard_server`, `selfaudit`, `glitch`, `dini`, `ration`, `lockstep`, `anti_cheat`,
> `salience`, `causal_runtime`).

The operating posture the workbench is built for: **the LLM is the engine, the frozen cores are the
chassis, a single replayable gate is the definition of done.** You stop reading diffs for the failure
classes the gate covers and spend attention only on what a machine cannot certify — whether the new logic is
*right*. The standing limit on all of it: `integrity ≠ truth`. A green gate means no regression + frozen
substrate + lawful structure — never "the code is good, fast, or pretty."

---

## The track, in one line

```
authoritative world state → deterministic snapshot → visual interpretation → GPU execution → presented frame
```

Every mechanism below exists to keep an LLM's contributions on the correct side of the membrane: **only CORE
moves committed state; VIEW/ALLOCATOR/OBSERVER may read, rank, and render, never declare.** An LLM reliably
tries to "help" by letting a renderer optimization write back into state, by editing a frozen file to add a
feature, or by introducing a float/clock/iteration-order leak. The workbench catches exactly those.

---

## 1. One replayable gate = definition of done

**Mechanism.** `integration/preflight_check.py` runs all 36 suites + the coupled/uncoupled parity proof as
real subprocesses under `PYTHONHASHSEED=0` and prints `[FOUNDRY VERIFIED]` only if everything actually ran
green; otherwise `[FOUNDRY BLOCKED]`, non-zero exit. A status you didn't earn by running is integrity-theater
(`AGENTS.md §5`).

**Ursprung use.** Two gates, layered:
- *Substrate gate* — the workbench preflight proves `Reality_Engine` itself hasn't drifted under us.
- *Project gate* — `ursprung/verify.py::run_milestone_1()` is our local preflight: replay-identity +
  view-perturbation invariance + ordering invariance, plus the ghost sweep. An LLM change is "done" only when
  this prints `MILESTONE … ACHIEVED`. We never accept a change on a banner the model typed.

**Bound.** The gate asserts what the suites assert — not that uncovered new logic is correct.

## 2. Core-drift detection — the sealed engine stays sealed

**Mechanism.** `selfaudit/evaluate.py` pins a SHA-256 baseline of every frozen-core file (`core_baseline.json`)
and fails the audit if any byte drifts, or if a core is copied under a new filename (the Sibling Law, checked
by content hash, no allow-list). It also runs a *drift-caught demonstration* — forges a baseline entry and
confirms the detector flags it, so the audit proves the detector detects.

**Ursprung use.** `Reality_Engine` is immutable for this project. The single most common LLM failure here is
"I'll just tweak the kernel to make rendering easier." The Sibling Law forbids it: Ursprung imports the
workbench read-only via `ursprung/_workbench.py` and adds capability only as new `ursprung.*` modules. A CI
step that re-runs the workbench's `selfaudit` against its pinned baseline turns "the engine didn't change"
from a promise into a checkable, signed fact.

**Bound.** Catches core drift + parity + suite regressions — not a logic bug in *new* Ursprung code that still
passes every check.

## 3. Fail-closed invariants — precommit the predicate, let the LLM crash into it

**Mechanism.** `chronicle` enforces host-side, precommitted validity predicates at the commit boundary; a
breaching state is refused (`InvariantViolation` / `TransitionRefused`) and rolled back. Safety lives in the
gate, never in the model's good intentions (`AGENTS.md §3`).

**Ursprung use.** Our precommitted predicates are:
- the **layer law** (`ursprung/registry.py`): a non-CORE system that declares `mutates_core=True` is rejected
  at registration — the LLM cannot quietly classify a renderer optimization as authoritative;
- the **cardinal invariant** (`verify.view_perturbation_invariance`): the committed hash trajectory must be
  byte-identical with the VIEW active and *deliberately corrupted every tick*. If an LLM-written renderer
  feature can touch state, this check diverges and names the tick.

Write the predicate **first**, then let the model generate fast against it. The agent gets an explicit error
to self-correct instead of you reading the diff.

**Bound.** The gate enforces exactly what the predicate encodes — not unsafety you never wrote down.

## 4. Bounded-authority autonomy — the agent writes fast, inside a fence

**Mechanism.** `guard_server/isolated_pep.py` is an out-of-process Policy Enforcement Point: run it under a
separate OS user, route every disk write / command through it; a symlink-proof `realpath` directory clamp
confines the agent to an allow-listed folder, and verdicts are Ed25519-signed and bound to the SHA-256 of the
exact action, so the agent cannot forge an `allow`.

**Ursprung use.** When an AI coding partner edits Ursprung, clamp its writes to the Ursprung folder so it
*cannot* reach into the sealed `Reality_Engine` tree at all — drift prevention by privilege, not vigilance.

**Bound.** OS privilege separation, not magic — it only holds if the PEP truly runs as a different user and
the agent has no path that bypasses it. On a single user it is bounded authority + tamper-evidence.

## 5. Forensic replay over model drift — debug the renderer, not the weather

**Mechanism.** `llm_toolkit/agent_capture.py` freezes the model boundary (prompt, system, seed, tokens,
logprobs, fingerprint) into the ledger; the Replay Court re-runs the workflow against frozen telemetry with no
live API/GPU. You replay the *captured output*, so you never need the model itself to be deterministic.

**Ursprung use.** When a renderer behaves differently than yesterday, capture isolates *your* logic change
from an upstream model swap or a GPU float-reassociation. This is also the template for the VIEW layer's own
debugging: the CORE trajectory is already replayable bit-for-bit, so a visual regression is provably in VIEW,
not in the world.

**Bound.** Replay is exact only for captured reads.

## 6. Deterministic state-space fuzzing — find the latent renderer bug

**Mechanism.** `glitch/explorer.py` does BFS over a state machine, **dedups states by content hash** (cost is
bounded by distinct states, not paths), shrinks any violating run to a minimal counterexample, and seals it
into a replayable ledger.

**Ursprung use.** Point it at sequence-dependent VIEW/ALLOCATOR state (camera transitions, LOD switches,
streaming in/out) to find the interleaving that breaks an invariant — and get a minimal, signed, replayable
repro instead of "sometimes it flickers."

**Bound.** A bounded model-check: no counterexample at depth *k* is **not** proof of absence.

## 7. Novelty compass — navigate the codebase without dumping it into context

**Mechanism.** `dini/compass.py` embeds the execution/state DAG in the Poincaré disk and returns a captured
`dini_distance` observable (grows with depth/novelty). A **sensor, never a gate**; the float never enters a
commit hash.

**Ursprung use.** Give the coding agent a cheap sense of "am I re-treading the happy path or diving into new
branches?" If distance stalls, push into untested branches; if it spikes past a *pinned* threshold, log a
topological anomaly and roll back to the last stable state. Lets the agent reason over compact coordinates
instead of huge directory listings.

**Bound.** Direction-agnostic and dual-use; it points, it doesn't authorize. Correlates with drift, doesn't
prove it.

## 8. Hardware-invariant budgets — stop runaway loops the same way on every machine

**Mechanism.** `ration/meter.py` gates on **exact integer logical steps** (iterations, tokens, nodes) against
a pinned ceiling, fail-closed (`QuotaBreached`); physical CPU/ms is a *captured observable*, never the gate.

**Ursprung use.** Critical for our perf work, because it forces the right split (see §11): logical step
budgets *gate* (reproducible across machines), while the 4.13 ms wall-clock target is an *observable* we
measure — never a gate that could make the build pass on a fast box and fail on a slow one.

**Bound.** Stops *logical* runaway; won't stop an OS OOM-kill, doesn't measure real cost.

## 9. Multi-model arbitration — shrink review to where models disagree

**Mechanism.** `quorum` (exact integer k-of-n consensus on content hashes) + `pact` (temporal covenant)
compose a 2D attestation lattice. Run N independently-seeded paths or different vendors as witnesses; commit
only on agreement, and the lattice surfaces the exact node/input that forked. Dissent is kept as a *ghost*
(`S_t` pressure) — an early drift radar.

**Ursprung use.** Route a renderer refactor through several model paths; review shifts from "read every diff"
to "look only where they disagreed." A rising dissent ghost warns of upstream model drift before a hard
failure.

**Bound.** Catches divergence *among* witnesses, not an error they all share; consensus ≠ truth (a colluding
≥k majority agrees on a falsehood). Independence is a trust input.

## 10. Audit-ready by construction — the Verification Record

**Mechanism.** Because every consequential step is recorded/replayable/signed as it runs, the audit trail is a
byproduct of execution. The workbench ships a copy-paste **Verification Record** template (`README.md` →
"Using this in a project").

**Ursprung use.** Each milestone/change carries a short record a reviewer can check (see the template at the
end of this doc). It states scope honestly: the record attests the work is reproducible and lawful, *not* that
the renderer is correct.

**Bound.** Evidence *toward* a standard, never satisfaction of it.

---

## Renderer-specific track-keepers (the pioneering edge)

The goal is to **beat traditional renderers on visual fidelity and response time (≈4.13 ms/frame, ~242 fps)**.
The workbench gives Ursprung two structural advantages incumbents don't offer, plus the discipline to chase
the frame budget honestly.

## 11. Truth-rate ⟂ frame-rate — `lockstep`

**Mechanism.** `lockstep` decouples an integer, content-addressed **truth-tick** stream from the **render**
rate. Truth advances in integer tick indices (exact rational arithmetic, gated, hashed); a render frame at
phase α between ticks is an **integer-exact interpolated observable**, explicitly excluded from the truth
hash. Rollback = "revert to the last valid hashed state and re-simulate" — GGPO-style netcode as the
workbench's own rule. The mispredict residual is a *rollback ghost*: recorded, bounded, never committed; and
**no backreaction** — an interpolated render position must never flow back into the sim.

**Ursprung use.** This is the spine of the 4.13 ms target. The world can tick at, say, 120 Hz while we present
at 242 fps; the extra frames are exact interpolations, so chasing frame-time **never** risks the committed
trajectory. The 4.13 ms is a *render-budget observable* measured against a baseline, not a gate on truth.

**Bound.** `lockstep` is the reconciliation core, **not a GPU renderer** — it produces the stream a render
thread consumes. Deterministic convergence holds only if the sim stays pure integer logic.

## 12. Culling that cannot leak information — `anti_cheat` + `lod`

**Mechanism.** `anti_cheat` separates **culling** (the server omits occluded entities from a packet — what
actually defeats wallhacks) from **accountability** (an exact occlusion invariant refuses impossible hits).
`causal_runtime/lod.py` carries the fairness law into rendering: `render_priority = future_surface ×
perceptual_sensitivity`, where sensitivity is gated by **legal visibility**, so an occluded object scores 0
no matter how future-critical — `future_surface → fidelity` ALLOWED, `→ hidden information` FORBIDDEN.

**Ursprung use.** Every VIEW/ALLOCATOR culling decision is structured so raising fidelity can never reveal
information the player shouldn't have. An LLM that "optimizes" culling into an aimbot-adjacent info leak trips
this by construction.

**Bound.** Proves mathematical deviation on a server-authoritative model; not a kernel anti-cheat, doesn't
catch a legitimately-visible aimbot.

## 13. Spend compute where the future is dense, not where the polygons are — `salience` / `consequence` / `causal_runtime`

**Mechanism.** The possibility-aware runtime allocates compute by **future-consequence density**, not distance
or screen size. Measured: possibility-driven attention captures **3–5× more of the truly-consequential future
than distance/visibility** (which are *slightly anti-correlated* with consequence), and **matches
hand-authored importance automatically, at scale, self-updating**, via a cheap `O(local)` atlas at **0.08% of
the exact cost**, refreshed in 1 frame vs 366. Split for safety into a **Truth scheduler** (never
possibility-aware) and an **Attention scheduler** (AI/streaming/rendering — possibility-aware), under
`possibility → allocation`, never `possibility → physics`.

**Ursprung pioneering angle.** This is the fidelity lever incumbents structurally lack: the same atlas signal
drives AI tick-rate, streaming, and render LOD from one field, so the budget lands on the doorway, not the
empty valley — *designer-quality attention without the designer*. The honest payoff is **more felt potential
per frame**, not more polygons.

**Bound — and the burden of proof.** This is the one renderer area the workbench labels a **hypothesis until
proven**: `consequence ≠ visibility`, and rasterization benefit from the field is *not yet measured on real
silicon*. The genealogy's verdict on the shared field is **Outcome C — a cross-domain *coordinator*, not a
universal allocator** (a domain specialist wins within its own domain; the field wins the cross-domain budget
split while it is *fresh, probability-weighted, independently-evidenced*). So any Ursprung ALLOCATOR built on
this ships only with a **comparative benchmark + negative control** answering "did this allocation preserve
more future-relevant fidelity per triangle than distance/screen-space LOD, at equal budget?" — never "did it
find what's objectively important" (a truth claim in disguise). `possibility ≠ likelihood`; a stale or
self-generated-consequence field fails, and must lose to a safe floor when it does.

---

## How to do performance work without lying (the 4.13 ms target)

Frame-time and fidelity are pursued by **measurable experiment, never assertion**:

```
baseline → change → replay → benchmark → compare
```

1. **Baseline first.** Build the frame-time profiler before optimizing. (The workbench's own history: a
   profiler showed ~7× headroom and *refused* a tempting kernel rewrite as premature; the real bottleneck
   turned out to be redundant hashing, not the eigensolver everyone assumed.)
2. **4.13 ms is an observable, not a gate.** It is measured wall-clock per frame, captured like
   `lockstep`'s α and `ration`'s CPU-ms — it informs allocation, it never gates the committed trajectory
   (`telemetry ≠ control`).
3. **Replay confirms the world didn't move.** After any optimization, the cardinal invariant must still hold:
   same trajectory hashes, different resource allocation. An optimization that changes the trajectory is not
   faster — it is wrong.
4. **Compare at equal budget, with a negative control.** A speedup claim survives only against a baseline and
   a control that *can* lose. A benchmark that can no longer fail a policy is decoration.
5. **Preserve failed branches.** Record the optimization you rejected and why — a failed branch carries
   architectural information (it tells the next person which assumption broke). Never silently delete a dead
   approach.
6. **Never paste a number you didn't measure.** Fabricated results are the cardinal sin here; the workbench
   has a documented history of running speculative "pre-written results" and disproving them (a claimed
   30.92% became ~5% and sometimes negative). State the measured value or state "not measured."

---

## Ghost discipline — classify the layer before patching the symptom

When an artifact appears (flicker, jitter, a hash mismatch, a stale frame, a reconstruction seam), classify it
on two axes **before** touching code (`ursprung/ghost_report.py`):

- **category**: temporal · spatial · numerical · perceptual · causal · pipeline-ordering
- **origin**: measurement · approximation · timing · data_loss · model_limit · implementation_error

A ghost allocates investigation; it never certifies a cause and never gates the trajectory. A persistent ghost
earns *more* investigation, not a conclusion — the model is a **falsifiable structure-maintenance system**, not
a causal oracle (`prediction → truth` FORBIDDEN). Example already live: VIEW reconstruction loss
(off-screen/behind-camera sprites) is `perceptual / approximation` — *expected*, recorded for a downstream
ALLOCATOR to weigh, not a bug to "fix."

---

## Verification Record template (paste alongside each Ursprung change)

```markdown
## Ursprung Verification Record — <change id> — <date>

- Project gate:   PYTHONHASHSEED=0 python3 loop.py   → MILESTONE … ACHIEVED   (or the FAIL line)
- Tests:          PYTHONHASHSEED=0 python3 tests/test_ursprung.py → N checks passed
- Substrate:      Reality_Engine selfaudit unchanged vs pinned baseline (yes/no)
- Cardinal inv.:  CORE trajectory byte-identical with VIEW active+perturbed (yes/no)
- Layer changes:  <new systems> classified CORE/VIEW/ALLOCATOR/OBSERVER; only CORE mutates_core
- Perf (observable, not a gate): frame-time mean=<…> ms vs baseline=<…> ms; same trajectory hashes? yes/no
- Ghosts:         <category/origin> … (attention signals; none gate the trajectory)
- Scope:          integrity ≠ truth — attests reproducible + lawful + observer-only, NOT correct/fast/pretty.
```
