<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# PROVENANCE — origin of every major subsystem

This file records **where each major subsystem came from**: who authored it, whether any third-party
source was copied, and — for anything built from someone else's published *idea* — a reference to the
paper/spec rather than to their source code. It is the companion to
[LICENSE_DECISIONS.md](LICENSE_DECISIONS.md) and exists so that a due-diligence reviewer (or future-me)
can trace IP cleanly. `attribution ≠ truth`, but attribution is what survives an audit.

## Top-line claims (verified at time of writing)

1. **All code in this repository is original work** by Daniel J. Dillberg, written for this project.
   No third-party source has been copied or vendored into the tree.
2. **Reality_Engine is imported read-only, never vendored.** Per the workbench "Sibling Law", Ursprung
   imports the Chronicle/Dentatus workbench through `ursprung/_workbench.py` and never edits, copies, or
   relicenses any workbench file. The workbench is the verification substrate; this repo is the consumer.
   (See root `NOTICE`.)
3. **Established algorithms are reimplemented from the literature**, not lifted from any specific
   codebase. Where a subsystem implements a known algorithm, the paper is cited below.
4. **No NASA source is present.** The NASA-derived items in the register are *ideas to reimplement*,
   and are marked **PLANNED / NOT-YET-IMPLEMENTED** until built. `considered ≠ implemented`.

## Major subsystems

| Subsystem (family) | Origin | Third-party source copied? | Reference for the *idea* (not source) |
|---|---|---|---|
| Reality_Engine workbench | External (Chronicle/Dentatus) | **No** — read-only import (Sibling Law) | Root `NOTICE`; workbench's own `agent.md` |
| Ursprung renderer core (CORE loop, VIEW boundary, ghost reporter) | Original | No | — |
| Prediction/temporal observers (divergence classifier, Dini-style observer, Temporal Prediction Membrane, PFAL, TCFF/PCJ) | Original | No | Dini-derivative framing is our own; standard numerical-analysis vocabulary only |
| Renderer "laws" (Polygon Reconciliation, Temporal Fidelity Conservation, Reality Debt, Causal Continuity Hypothesis) | Original (project's own constructs) | No | — |
| RealityKernel + stress suites | Original | No | — |
| weltwerk causal core (`world.py`/Weltlinie, `fork.py`, observer protocol, `cow_world`, `light_cone`, `teleport`, `reachability_algebra`, `agent_transport`) | Original | No | Copy-on-write & reachability are textbook CS, implemented from first principles |
| weltwerk authoring (`world_design`, `causal_net`, `world_lint`, `world_validate`, `geometry_boundary`, `causal_metrics`) | Original | No | — |
| weltwerk sim (`world_sim`, `world_diff`, `world_ai`, `world_edit`, `causal_scale_bench`) | Original | No | A* search and FSMs in `world_ai` are standard, reimplemented from common references |
| splat lens (`splat_format`, `splat_dsl`, `splat_adapter`, WebGL editor) | Original | No | 3D Gaussian splatting concept: Kerbl et al., SIGGRAPH 2023 — math reimplemented, no source copied |
| allostery (`allostery`, `pdb_rin`, `rin_analysis`, `eval_harness`) | Original | No | Brandes betweenness (Brandes 2001); RIN/contact-map construction is standard biophysics; no Biopython dependency |
| VIEW HTML projections (designer/studio/voxel/FPS/times_square) | Original | No | three.js loaded as a standard dependency, not vendored into the tree |

If any row ever changes from "No", the copied component must appear in
[LICENSE_DECISIONS.md](LICENSE_DECISIONS.md) **and** `THIRD_PARTY_NOTICES.md` *before* the commit lands.

## NASA-derived idea register (clean-room)

These are NASA projects whose **published ideas** may inform future Weltwerk subsystems. None is
implemented yet; none has had source copied. Each, when built, will be a clean-room reimplementation
from the cited paper/spec, recorded here with a date.

| Idea | NASA origin (license) | Status | Clean-room basis (cite, don't copy) |
|---|---|---|---|
| Abstract-interpretation lint for `world_lint` | IKOS (**NOSA 1.3**) | PLANNED | Cousot & Cousot, "Abstract Interpretation" (POPL 1977). Reimplement theory; **do not read IKOS source for implementation**. |
| Coupling-driven AMR / LOD | PARAMESH (**NOSA 1.1+**) | PLANNED | AMR literature (Berger & Oliger 1984; Berger & Colella 1989). Idea only. |
| Model-based causal diagnosis | Livingstone 2 (unverified, treat NOSA) | **IMPLEMENTED 2026-06** — `weltwerk/verify/diagnose.py`, clean-room | de Kleer & Williams, "Diagnosing Multiple Faults" (AI 1987); Reiter 1987. Consistency-based diagnosis reimplemented from theory; **no Livingstone source consulted**. |
| State-space / bounded model checking of the kernel | Java Pathfinder (**Apache-2.0**) | **IMPLEMENTED 2026-06** — `weltwerk/verify/kernel_check.py`, clean-room | Explicit-state model-checking literature. Apache ⇒ source *could* be read, but it targets Java; reimplemented for the Python kernel regardless. No JPF source consulted. |
| Multi-fidelity selection | MFSim (unverified, treat NOSA) | PLANNED | Multi-fidelity modeling literature (e.g. Peherstorfer, Willcox, Gunzburger 2018). Idea only. |

### Clean-room procedure for NOSA-derived ideas

1. Read the **paper / public spec**, not the NOSA source. Note the citation here.
2. Implement from the specification in original AGPL code.
3. Do not copy identifiers, comments, file structure, or test fixtures from the NOSA project.
4. Record the date, the citation, and "no source consulted" in this register on the implementing commit.
5. If in doubt about whether something is an idea (free to use) or an expression (copyrighted), treat it
   as expression and reimplement around it. `algorithm ≠ code`.

## Change log

- 2026-06 — Initial provenance record. State: all subsystems original; Reality_Engine read-only; zero
  third-party source vendored; NASA items are PLANNED ideas only.
