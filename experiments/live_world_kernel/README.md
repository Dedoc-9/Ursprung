<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# live_world_kernel — the smallest adversarial embedded-authoring kernel

Not an editor, a renderer, or an MMO. The smallest thing that can **kill or vindicate** the embedded-authoring
idea from [`docs/EMBEDDED_AUTHORING.md`](../../docs/EMBEDDED_AUTHORING.md). It answers exactly one question:

> **Can a running world accept, reject, and rewind creator actions without losing causal truth?**

If yes, the editor is a UI problem. If no, the larger engine vision collapses before it needs a renderer.

**Status.** The commit / speculative layer was VERIFIED **9/9** on 2026-06-22 (`PYTHONHASHSEED=0`, Python 3,
Windows). The kernel has since been **hardened** to make the *three states of a fact* explicit — committed /
irreversible / durable — adding **+7 checks (16 total)**; re-run to confirm 16/16. `declared ≠ verified`: the
YES is a property of single-process *logic*, not yet of a system under concurrency, latency, or scale.

```bash
PYTHONHASHSEED=0 python3 live_world_kernel.py
```

## Result — verified (9/9)

The reference passed its own adversarial self-test on the author's machine (the machine that runs it is the
verifier):

```
[PASS] speculative_isolation             A sees its speculative wall; B and shared truth do not
[PASS] commit_promotes_to_truth          accepted → B now sees the wall; it left A's speculation
[PASS] causal_subtree_rollback           reject e1b → removed exactly {e1b,e2b,e3b}; unrelated torch survives
[PASS] no_leak_on_reject                 rejected speculation never entered committed truth or B's view
[PASS] replay_from_zero                  world rebuilt from 2 committed events == live state (log 98a401876bd92998)
[PASS] authority_from_history            e1 authorized by grant g1; after revoke, the same edit is rejected
[PASS] duplicate_idempotent              re-committing e1 is a no-op
[PASS] disconnect_discards_speculation   disconnect drops private speculation; committed truth untouched
[PASS] latency_irreversibility_frontier  rolled-back work = causal depth; expected thrash = depth × reject_prob
9/9 checks — answer: YES (within scope)
```

**What it proves** (under the stated conditions): the causal-truth machinery is sound *in the small* —
speculation is private and disposable, shared truth grows only by committed events, **rejection rewinds exactly
the causal subtree and nothing else**, authority is replayable history (not an annotation), and the world
reconstructs from its log (digest `98a401876bd92998`). The load-bearing claim — *causal-subtree rollback
without corrupting unrelated state* — held against the adversarial case (`e1b → e2b → e3b` rejected while the
unrelated `e4b` survived). That is the provenance claim, made measurable and passed.

**What it does NOT prove** (`declared ≠ verified`): nothing about *scale*. This is single-process logic — no
concurrency-at-scale (the common lethal failure: many actors, one region), no networking or real latency
(check 9's frontier is a **surrogate**, not a measured human-trust threshold), external-root authority only
(the embedded-root / genesis case is open), and no performance claim. So "the editor is a UI problem" is true
*conditional on unscaled, single-process logic*; the boundary that actually decides the engine vision —
concurrency — is the next probe, not this one. The pass means the idea **earned the right to be scaled**, not
that it has been.

## What it changes — editor and runtime are one state of matter

Historically, engines treat **editing** and **playing** as two different states of matter, separated by a
*phase transition*: an authoring tool mutates an offline world (Unreal Editor, Maya, Blender) → build → export
→ deploy → a running game nobody can author without breaking it. The arrow runs one way. A runtime edit is a
hot-reload hack or simply impossible, because a live world has no honest way to accept an authored change while
preserving determinism, authority, and replay — so the two states are kept in separate phases, with a wall
between them.

**This kernel collapses the phase transition.** An editing action and a gameplay action are the *same
primitive* — an `EditEvent` committed to the one trajectory — differing only in (a) the capability the event
requires and (b) the source that emitted it. There is no offline state to build from and ship: the world never
leaves "running" in order to be edited. "Editing" is just a *privileged event stream into the live world*, and
because it is the identical primitive to a gameplay mutation, it inherits replay, provenance, authority, and
undo **for free** — as consequences of the substrate, not as bolted-on tooling. The build/deploy wall —
historically a change of *state* — becomes a **capability check**, not a phase change.

So editor and runtime are not two states of matter bridged by a pipeline; they are **one substrate**,
distinguished only by who is allowed to emit what. The prototype shows this directly: "move the wall" and any
in-world mutation travel the identical `propose → commit` path through the same kernel — there is no second
code path for "edit mode." (Scope, as above: demonstrated in single-process logic. The collapse is a property
of the substrate, shown in the small; whether it survives concurrency and scale is the next probe.
`declared ≠ verified`.)

## The three states of a fact — committed ⟂ irreversible ⟂ durable

"Is it real yet?" is not one question. Objectivity is at least two **orthogonal axes** — *causal dependence*
and *replica redundancy* — so the kernel tracks three distinct transitions, each stamped on a logical clock:

- **COMMITTED** `= authority_valid ∧ in shared log ∧ replay_integrity`. Binary, at the authority gate.
  (`t_commit`)
- **IRREVERSIBLE** `= ∃ committed dependent`. Causal: the *first* committed event that builds on it crosses
  its irreversibility frontier. Not a tunable count — the threshold is one. (`t_dep`)
- **DURABLE** `= ∃ recovery path independent of the failure`. Redundancy: a replica, **or** deterministic
  regeneration, **or** archival — **quorum is only one such path**. The invariant is the *existence* of a path
  the failure cannot also remove, never a specific strategy. (`t_durable`)

These come apart, and the self-test exhibits each: *committed but not irreversible* (nobody depends on it
yet); *irreversible but not durable* (depended-on but single-copy — a failure destroys it); *durable but not
irreversible* (a replicated/regenerable asset nothing yet depends on). Then a deliberate **durability
failure** — destroy the primary store — confirms that facts with an independent path recover (`a2` via
replica, `a3` via **regeneration, no quorum**), while a primary-only fact is reported as **severance, never a
fabricated value** (`compress ≠ sever`). It instruments the two separate latency budgets —
`commit → dependency` (controls *feel*) and `dependency → durable` (controls *survivability*) — and shows a
fact reaching durable with *no* dependency, proving the axes are independent.

## Three stores, kept distinct

The load-bearing correction this prototype enforces — blurring these is what makes rollback expensive:

| Store | Role | Properties |
|---|---|---|
| **committed** | shared truth | the canonical event log; the only thing other clients observe; grows only by accepted events |
| **speculative** | private hot belief | a per-client scratchpad: fast, mutable, **disposable**; never observed by others or made a contract until a commit promotes it |
| **recovery** | replayable history | the committed log itself — "why is the world this way?" is answered by re-folding it, never by trusting live state |

Prediction is a *scratchpad*, not a sealed reserve. An edit is an **event**, never a direct mutation:
`propose()` touches only private speculation (felt reality, instant); `commit()` runs the authority gate and
either **promotes** the event into shared truth or **rejects** it and rewinds the rejected event with its
entire **causal subtree** — exactly its transitive descendants, nothing unrelated.

## What the self-test proves (16 checks: 9 commit/speculative + 7 three-state)

1. **speculative_isolation** — a proposed edit is private; no other client and no committed truth sees it.
2. **commit_promotes_to_truth** — an accepted edit becomes shared truth; other clients now see it.
3. **causal_subtree_rollback** — rejecting `E1` (with `E2`→`E3` depending on it, plus an unrelated `E4`)
   removes *exactly* `{E1,E2,E3}` and leaves `E4` intact. The provenance claim, made measurable.
4. **no_leak_on_reject** — the rejected subtree never entered committed truth or any other client's view.
5. **replay_from_zero** — delete the world, rebuild from the committed log → identical state.
6. **authority_from_history** — "why was this edit allowed?" resolves to the committed grant that licensed it;
   a revoke makes the same edit fail afterward (authority is an event, not an annotation).
7. **duplicate_idempotent** — committing an already-committed event is a no-op.
8. **disconnect_discards_speculation** — the private scratchpad is disposable; shared truth is untouched.
9. **latency_irreversibility_frontier** — rolled-back work equals causal depth; expected thrash is
   `depth × reject_probability`. The *felt-reality* analogue of the irreversibility frontier — the quantity to
   measure next: how much speculative divergence a creator tolerates before trust collapses.

*The three-state layer:*

10. **committed_not_irreversible** — an accepted fact with no committed dependents is committed, not yet
    irreversible (the two are different transitions).
11. **dependency_makes_irreversible** — committing a dependent crosses the parent's irreversibility frontier
    and stamps `t_dep`.
12. **durable_by_independent_path_not_quorum** — durability is satisfied by a replica *or* deterministic
    regeneration (with zero replicas) *or* archival; the invariant is an independent recovery path, not a quorum.
13. **axes_are_orthogonal** — one fact is irreversible-not-durable, another durable-not-irreversible (causal
    load ⟂ replica redundancy — objectivity is not one scalar).
14. **durability_failure_recovers_independent** — destroy the primary store; facts with an independent path
    (replica / regeneration) recover via it.
15. **loss_is_severance_not_a_guess** — a primary-only fact with no independent path is reported as severance,
    never a fabricated value (`compress ≠ sever`).
16. **three_timestamps_two_budgets** — `t_commit ≤ t_dep ≤ t_durable`; `commit→dependency` (feel) and
    `dependency→durable` (survivability) are separate budgets, and a fact can reach durable with no dependency.

## The residue — causal reconstruction as a first-class boundary

The durable output of the physics/architecture debate is not an analogy; it is a **sorting rule** and the
boundary it enforces. The one object common to every surviving correspondence (gauge freedom, the light cone,
the field equation) is a single statement:

> **A representation exposes a projection of reality; recovering the causal generator requires additional
> structure.** Observable ≠ generator — a snapshot tells you *what is*, never *why it is*.

So every subsystem that claims replay, recovery, or trustworthy editing must answer three questions, and this
kernel is the smallest worked example of answering them:

1. **What is externally observable?** — the contract surface. Keep it minimal; everything here accrues
   dependencies (Hyrum's Law).
2. **What invariants must survive representation changes?** — what stays fixed under LOD, serialization,
   coordinate system, partitioning: the gauge-invariant content.
3. **What hidden causal information is required to reconstruct or audit?** — lineage, authority, ordering: the
   cold reserve. *And it must be capturable at the **irreversibility frontier**, not retroactively* — once an
   output is depended upon, the causal information it needed had to already exist (see
   [`docs/EMBEDDED_AUTHORING.md`](../../docs/EMBEDDED_AUTHORING.md)).

**If a subsystem cannot answer #3, it cannot honestly promise replay, recovery, or trustworthy editing.**

The gauge diagnostic, which is a *proof obligation*, not an isomorphism:

> **A representation is a gauge only after you prove it cannot become causal.**

In gauge theory `A ∼ A + ∇χ` is a defined equivalence class with invariant observables. In an engine, a
representation choice (LOD, serialization, coordinates, partitioning) is a gauge *only* once `VIEW ↛ CORE` is
proven (the cardinal invariant). If a "mere representation" leaks into authority, ordering, determinism, or
collision outcomes, it was never gauge — it was **hidden state**. Gauge-ness is earned by proof, never assumed.

*(The physics that generated this — Faraday induction, gauge freedom, retarded potentials — stays in the cold
layer as an **analogy generator**, never a design proof. The proof is the 16/16 self-test above. The reusable
lesson is only that observable state and generative history are different objects, in physics and in engines
alike. `declared ≠ verified`.)*

## The frontier probe — observe, don't enforce (`frontier_probe.py`)

The barrier — *no committed fact may depend on an uncommitted possibility* — is deliberately **not** a law
here. Promoting a frontier discovery into a kernel rule before measuring where the frontier lives would
violate the discipline that earns boundaries. So `frontier_probe.py` is the **instrument**, not the rule: it
lets dependency *outrun* commitment and asks where the failure comes from.

It tracks candidate creation, reads, derived commits, externalization, and rollback attempts through a
**sealed observer** — append-only telemetry never read back by world ops; classification is a *pure* function
over it (`telemetry ≠ control`, `observation ≠ intervention`; an instrument that moved the world it measures
would be measuring its own shadow). The failure signal is a **contradicted dependency** — a dependent
referenced a candidate that then changed or vanished without compensation — tagged by source. Three scenarios
exhibit the three outcomes:

```
scenario             outcome             source     commit-barrier would prevent?
aligned              ALIGNED             —          n/a (frontier already = commit)
needs_promotion      NEEDS_PROMOTION     commit     yes (promote-first)
observer_dependent   OBSERVER_DEPENDENT  observer   no (out of band — policy only)
```

So the instrument tells whether the barrier would be **redundant**, **earned**, or **insufficient** — and
emits that classification with **no verdict** on whether to build it. `observe → measure → locate frontier →
choose mechanism`, never `choose → build → justify`. Run: `PYTHONHASHSEED=0 python3 frontier_probe.py` (7/7
self-checks verify the *instrument* — correct classification, dependency-allowed-to-outrun, source
attribution, and that the observer is sealed).

## The concurrency probe — geometry proposes, dependencies judge, convergence reveals (`concurrency_probe.py`)

The frontier after the single-process kernel is concurrency, and the temptation there is to import a physics
*guarantee* (Dini's theorem → "uniform convergence kills stragglers"). Graded honestly, Dini gives a *shape*,
not a guarantee: its hypotheses (monotone convergence on a compact space) fail for live edits (not monotone)
and for dependency surfaces (`geometric locality ≠ dependency locality`). So `concurrency_probe.py` keeps only
what survives — **a partition is a hypothesis; the dependency graph is the judge; convergence is the
measurement** — and enforces nothing.

For a given partition and dependency graph it measures **boundary leakage** (cross-region dependencies — the
optimization boundary becoming semantic) and whether the residual **settles** (the Dini-shaped metric,
*unresolved cross-boundary dependencies*, but only in the **quiescent** phase; under live overload it is
allowed to diverge, and that divergence is the repartition signal). Same world, two partitions:

```
partition            leakage   converges?   classification
aligned              0.00      yes          GOOD_GAUGE        (boundary carries no causal traffic)
split (quiescent)    0.25      yes          GAUGE_WITH_COST   (leaks, but settles)
split (overloaded)   0.25      no           SEMANTIC_LEAK     (leaks faster than it settles → repartition)
```

It shows leakage is a *representation choice* not ontology (identical deps, different partition → different
leak — Arbitrary-Boundary), that geometric and dependency locality are different relations, and that
Dini-style convergence holds *only* in quiescence. Pure functions (sealed — no state, no enforcement); **no
verdict** on which partition to adopt. Run: `PYTHONHASHSEED=0 python3 concurrency_probe.py` (7/7). It is the
reconciliation-layer cousin of `prediction.py`'s Dini-style observer.

## The Klein probe — orientability test for false global boundaries (`klein_probe.py`)

Graded all the way down, the Klein-bottle intuition stops being poetry and becomes an *exact, computable
test* — because "non-orientable" has a precise discrete form: a **signed graph with a frustrated cycle**
(sign-product −1 around a loop). Following such a cycle returns you to the start with the side reversed, which
is exactly *"if I follow this boundary through its consequences, does it return me with the meanings
reversed?"* This is the one place a topology analogy survives as real mathematics rather than metaphor.

`klein_probe.py` models architectural boundaries as signed edges (+1 = same side, −1 = opposite side under
that boundary) and tests for a consistent **global** side-assignment:

```
system               classification    meaning
coherent boundaries  ORIENTABLE        the locals cohere into one global cut — safe to unify
embedded observer    NON_ORIENTABLE    world→observer→event→world reverses orientation — no global 'outside'
```

It shows: every boundary is orientable *locally* (single edges are always 2-colorable); the failure is
**global, not local** (removing any one edge of the frustrated cycle restores orientability — the locality
escape); and it fires **only on the global-promotion claim** (each boundary kept separate is fine; only "these
imply one global boundary" fails). Pure functions (sealed); **no verdict** — it never says merge or split,
only whether the single-global-boundary claim is a lie. The orientability test is exact topology; encoding a
boundary into a sign is a declared model (`declared ≠ verified`). It is the **Arbitrary-Boundary Law's
adversarial test** — it catches the moment the architecture worships a boundary it only needed to draw. Run:
`PYTHONHASHSEED=0 python3 klein_probe.py` (7/7).

## The integrated audit — `topology_provenance_engine.py`

The three probes bundle into one **audit harness** that runs all of them over a *single* declared system
model and reports **three independent coherence dimensions** — not a performance metric, but the *health,
safety, and coherence of data flows*:

```
dimension    probe               question                                       verdicts
structural   klein_probe         do the boundaries cohere, or is one a false    ORIENTABLE / NON_ORIENTABLE
                                  global claim?
provenance   frontier_probe      where does possibility become obligation;      ALIGNED / NEEDS_PROMOTION /
                                  did a dependency outrun commitment?            OBSERVER_DEPENDENT
spatial      concurrency_probe   is a chosen partition a clean gauge or a       GOOD_GAUGE / GAUGE_WITH_COST /
                                  semantic leak?                                 SEMANTIC_LEAK
```

The feature that makes it *faithful* rather than a dashboard that lies: **it refuses to collapse the three
into a single "coherence score."** Objectivity is not one scalar — not even for the auditor. The report is a
**vector** of three categorical verdicts plus per-axis attention flags; the only legitimate rollup is the
unweighted conjunction "all axes clean?", never a weighted number. It bundles the three *verified* probes
without re-deriving them, surfaces **attention signals** ("look here") rather than **verdicts** ("broken" /
"safe" / "merge" / "fix"), and enforces nothing. Its self-test shows the axes are **independent** — a model
can be clean on two and leak on the third — so all three are needed; one green never implies another.

*"Continuous" is a usage* (run it per-commit / in CI), not a new runtime — this is a single-pass harness. The
encodings (which boundaries become signed edges, which flow ops, which partition) are **declared models**:
`declared ≠ verified`, and a clean audit means "no attention signal under this declared model," never `safe`
(`tested ≠ safe`). Run (from this directory): `PYTHONHASHSEED=0 python3 topology_provenance_engine.py` (7/7).

## The self-extraction probe — `module_graph.py` (audit what it didn't author)

The first artifact that turns a *real* artifact into a model instead of hand-declaring one — and so the first
test of the hardest assumption: **`SystemModel` is an interpretation of evidence, not reality.** It is
deliberately dumb (AST only; module → node, intra-repo import → edge, package dir → partition; no inference, no
scores). Pointed at this subfolder's own source, it rediscovers the import structure
(`topology_provenance_engine → {klein, frontier, concurrency}`) **without having authored it**.

Its first success is **negative — knowing what it cannot see:**

- **spatial** lens *applies* — cross-package imports = the directory boundary going semantic (does the org
  chart match the dependency graph?).
- **structural** uses a *fit-for-purpose* check — directed dependency **cycles** — and explicitly does **not**
  force klein signed-orientability (bare imports carry no signed trust/authority boundary).
- **provenance** is **declared NOT APPLICABLE** — a static import graph has no temporal candidate→commit flow;
  it refuses to fabricate a provenance verdict (that would need git history or runtime traces).
- **blind spots** (dynamic imports, relative imports, unparseable files, basename collisions) are *recorded,
  not dropped* — the extraction-fidelity metric, *"does it know what it doesn't know?"*

Sealed / observe-only: `ast`-only (never executes scanned code), never writes, no verdict. Run (from this
directory): `PYTHONHASHSEED=0 python3 module_graph.py` (7/7; optional path arg to scan a broader tree). It is
the threshold the subfolder was built toward — auditing a system it did not author, honest about the gap
between the model and the evidence.

## The breakthrough probe — `fidelity_gap.py` (why the model came back blind, and what crosses)

Pointed at two real open-source repos (`psf/requests`, `pallets/click`), `module_graph` came back almost
entirely **blind** — 91 and 197 blind spots, ~0 resolvable edges. That is not a finding about requests/click;
it is a finding about *our model*. `fidelity_gap.py` reads the blindness, names its cause, and **proves what is
recoverable** without overclaiming what is not.

**The diagnosis — one root cause.** The dumb extractor's identity is the file *basename* and its resolution is
*absolute-imports-only*; real packaged code is overwhelmingly *relative imports* (`from . import x`) over a
*package-dotted identity*. So ~95% of the blindness is a single defect — wrong module identity — not a property
of the code. The corrected model (package-path dotted identity + relative-level math) turns those blind spots
into real edges and makes basename collisions vanish. It then **fences the irreducible residual**: dynamic
imports (`__import__` / `import_module`) are a *runtime frontier* a static parser can never cross — declared and
handed to provenance, never faked into an edge.

Verified on `pallets/click` (2026-06-22; the machine that runs it is the verifier):

```
dumb model (basename, absolute-only):   modules 60   edges 6     blind 197   collisions 3
corrected (package-path, relative):     modules 63   edges 131   collisions 0
  recovered relative edges 196   |   spatial leak 0.52 (68 cross-package)
  structural cycle: click._compat → click._winconsole → click._compat
  failure mode        count  verdict           why
  RELATIVE_IMPORT       196  RECOVERABLE       wrong identity; package-path + level math resolves these
  BASENAME_COLLISION      3  RECOVERABLE       dotted names make them unique (now 0)
  DYNAMIC_IMPORT          1  RUNTIME_FRONTIER  target computed at runtime — needs a trace, not a parser
  BREAKTHROUGH: 199 blind spots were a MODEL DEFECT — edges 6 → 131, collisions 3 → 0
  RESIDUAL: 1 dynamic import is a runtime frontier (complex.cli __import__) — handed to provenance, not faked
7/7 checks
```

(`psf/requests` scans the same way: 91 blind → relative recovered, basename-collisions 4 → 0, residual = 2
dynamic imports — `compat.import_module`, `packages.__import__`.)

**What it proves:** the blindness was *read, not lamented* — almost all of it was one model defect, and the fix
is **demonstrated** (relative imports become real edges; collisions disappear under dotted names), not asserted.
**What it refuses:** `declared ≠ verified` (the import model is the common case, not CPython — namespace
packages, `sys.path` edits, conditional imports stay in the declared residual); `resolved ≠ executed` (a
recovered edge means one module *names* another, never that a call path runs); and the **runtime frontier is
never counted as recovered** (the self-test's 7th check enforces exactly this). The gap is mapped: push the
static model up to the frontier, stop pushing it past — *that boundary is where the committed Weltlinie begins.*
Run (from this directory): `PYTHONHASHSEED=0 python3 fidelity_gap.py [path]` (7/7; the self-test runs on
synthetic cases + this folder, so it passes without requests/click present — the *report* is for the path you pass).

## Defensive use — structural reconnaissance (authorized red-team / architecture review)

These probes are observe-only diagnostics, but *structural reconnaissance* is exactly what an authorized red
team or architecture review does first — and `module_graph` (+ the engine) surfaces a class of finding that
CVE scanners, port scanners, and SAST pattern-matchers miss: **architectural / boundary** weakness, not
code-level bugs. Run on a codebase you own or are authorized to assess, the structural signals map to
defensive questions — *findings to close*, not attacks to launch:

- **Semantic leak (a cross-package import that violates intended isolation)** → a *privilege-boundary smell*:
  a low-trust component (logging, a utility) importing a high-trust one (credential store, config loader) is a
  structural bridge that should not exist. For a defender it is a **lateral-movement surface to remove** — fix
  the dependency or the partition before it becomes one. (engine spatial axis / `concurrency_probe`.)
- **Dependency cycle (a non-coherent directed loop)** → a *resilience / availability risk*: circular chains
  are where unhandled re-entrancy, deadlocks, and unbounded loops hide — a **denial-of-service and
  stack-exhaustion surface to harden**. (`module_graph`'s structural cycle check.)
- **High fan-in modules** (in-degree over the import edges) → *blast-radius concentration*: the
  most-depended-upon internal modules are the highest-value review targets, where one compromise propagates
  farthest. (The edge data supports this; centrality is a natural extension of the current output.)

The discipline binds here too — and it is what keeps this honest rather than alarmist:

- **`flagged ≠ exploitable`.** Every output is an *attention signal*, never a confirmed vulnerability: a
  cross-package import may be intentional; a cycle may be benign. The tool surfaces structure; a human confirms
  whether it is a real weakness. No verdict — same stance as everywhere else.
- **It does NOT reveal the irreversibility frontier.** A *static* import graph has no temporal flow, so it
  **cannot** identify "the module just before the point of no return" (payment gateway, DB writer) — the
  provenance lens is declared `NOT_APPLICABLE`. Finding those needs runtime traces or git history; claiming the
  static graph finds them is the extraction lie the probe exists to refuse.
- **Dual-use, defensively framed.** Like any dependency/architecture analyzer (SAST, SBOM / dependency-graph
  tooling), this is dual-use; it is documented for **authorized** defensive use — mapping and closing your own
  architectural attack surface before an adversary maps it from a leak. It ships no exploit, no payload, and no
  targeting; it reads source you are entitled to read and reports structure.

The defensive wedge: most security tooling asks *"is there a known-bad pattern or CVE here?"*; this asks
*"does the architecture's **real** boundary structure match its **intended** one — and where doesn't it?"*
That gap is where isolation failures and resilience risks live, and it is invisible to pattern-matchers.

## Target areas — where these patterns are already load-bearing (resonance, not validation)

The mathematics these instruments compute is not invented here; it is established and load-bearing across real
distributed systems. That is a reason to get the instruments *right* — **not** a claim that any production
system implements these probes, and **not** validation of the architecture. `resemblance ≠ implementation`;
`declared ≠ verified`. Graded honestly, with the common over-claims corrected:

- **Signed-cycle frustration (the `klein_probe` math) is real and broadly applied.** The frustration index —
  the minimum edge sign-flips so that every cycle's sign-product is positive, *exactly* `klein_probe`'s
  orientability test — is established graph theory (Cartwright–Harary structural balance), with genuine uses in
  social/political networks, **biological** networks (monotone-subsystem decomposition), **physics** (spin-glass
  / atomic-magnet ground states), international relations, **finance** (portfolio bipolarization), and chemistry
  (fullerene stability). *Correction:* a *deployed BGP / traffic-engineering "frustration-index" tool* is **not**
  among the verified applications — treat that specific claim as unverified. The durable fact is the underlying
  mathematics is real and used for consistency/conflict detection.
- **Speculate-then-commit-at-a-point-of-no-return (the kernel + `frontier_probe`) is a standard pattern.** CPU
  speculative execution with rollback, database optimistic concurrency / MVCC, and the irreversible *commit
  point* of a distributed transaction or an exchange gateway all match the irreversibility frontier: branches
  are pruned freely until an external boundary makes them load-bearing. *Honest scope:* the five-stage
  vocabulary (creation → observation → dependency → commitment → consequence) is ours; the *pattern* is the
  established one — a resonance, not a claim those systems use our terms.
- **Optimistic replication for collaborative editing (the `concurrency_probe` area) is real — but not quantum.**
  Collaborative editors converge via optimistic replication + conflict resolution: CRDTs, operational
  transforms, or server-authoritative last-writer-wins. *Correction:* Figma's published design is a
  **server-authoritative, CRDT-*inspired* last-writer-wins** model — explicitly *not* true CRDTs, *not* OT, and
  *centrally ordered* (the server is the authority). That is the **opposite** of "no master clock / emergent
  environmental consensus," so the "quantum-Darwinism / environmental-witness" framing is **wrong as a
  mechanism**; the Zurek "redundant recording → objectivity" resemblance is a *shape* this project already
  graded down, not how these systems work. The real mechanisms are CRDTs / OT / LWW, with consensus (Raft /
  Paxos) where genuinely decentralized.

The honest takeaway: these probes instrument mathematics the field already relies on — *evidence the
abstractions are real*, never *proof that elite systems run them*, and never *validation*. Resemblance is a
reason to look, not a reason to believe.

*Sources: [Figma — How Figma's multiplayer technology works](https://www.figma.com/blog/how-figmas-multiplayer-technology-works/);
[Aref & Wilson, Balance and Frustration in Signed Networks](https://arxiv.org/abs/1712.04628).*

## Honest scope (what this is NOT)

A **logic reference**, not a performance system. No concurrency-at-scale, no networking, no UI, no renderer.
Authority uses an **external root** anchor (the embedded-root / genesis variant is left open). The latency
frontier is a *surrogate metric*, not a measured human-trust threshold. A Rust port (validated against this
reference via conformance vectors, the same method used for `reality_kernel/core_rs`) is the natural next
step. `declared ≠ verified`. This prototype exists to force the boundary to reveal itself — and if it fails,
the failure (concurrency, authority, provenance cost, contract leak) answers the theory directly.
