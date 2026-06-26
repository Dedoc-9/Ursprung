<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# LICENSE_DECISIONS — external projects considered for Ursprung / Weltwerk

This is the decision ledger for every third-party (here, NASA open-source) project evaluated for
merging into this repository. It records the **verified license**, the **decision**
(*vendor* / *interoperate* / *reimplement*), and the **rationale**. It is due-diligence evidence:
if this repo is ever commercialized or dual-licensed, this file shows that license boundaries were
considered before any code crossed them.

> **Not legal advice.** Licenses change and per-repository facts vary. Re-verify the actual `LICENSE`
> file of the specific repository and commit you intend to use before relying on anything here.
> `verified-here ≠ still-true-at-use-time`.

This repository is **AGPL-3.0-only**. Daniel J. Dillberg holds copyright in the original code and may
therefore offer it under additional terms (e.g. a commercial license) in future. That dual-license
option only survives if every component that ships *inside* the repo is either (a) original work, or
(b) permissively licensed (Apache-2.0 / BSD / MIT). Copyleft or GPL-incompatible code vendored into
the tree would forfeit it.

## Compatibility rules used in this ledger

| Source license | Into an AGPL-3.0 work? | Keeps dual-license option? | Mechanism |
|---|---|---|---|
| **Apache-2.0** | **Yes** (one-way). GPLv3/AGPLv3 contain the provisions that reconcile Apache's patent-termination clause. | **Yes** — Apache permits commercial relicensing of the combined product; the Apache files stay Apache. | Preserve Apache copyright headers + any `NOTICE`; state changes; list in `THIRD_PARTY_NOTICES.md`. |
| **NASA Open Source Agreement (NOSA 1.1 / 1.3)** | **No.** FSF lists NOSA as **GPL-incompatible** (the "original creation" representation clause). | n/a — cannot be vendored. | **Do not copy source.** Reimplement the *published algorithm* clean-room (ideas/algorithms are not copyrightable). |
| **BSD / MIT** | Yes | Yes | Preserve notice; list in `THIRD_PARTY_NOTICES.md`. |
| **US Government work (17 USC §105)** | Usually yes, but **do not assume.** NASA releases under NOSA/Apache precisely because contractor contributions and ex-US copyright exist. | — | Treat the repo's stated `LICENSE` as authoritative, not the §105 presumption. |

Three decision verbs:

- **Vendor** — copy source into the tree. Only for permissive (Apache/BSD/MIT). Adds attribution duty.
- **Interoperate** — run as a separate program/service across a process or network boundary; exchange
  data, never link/copy. Zero license entanglement (AGPL reaches *our* served code, not separate
  programs we merely talk to). Safest for NOSA and for heavyweight systems.
- **Reimplement** — write our own AGPL code from the published paper/spec. Required for NOSA; also the
  path that keeps a subsystem 100% our copyright (so it stays dual-licensable). Record in
  [PROVENANCE.md](PROVENANCE.md).

## Decision table

| Project | Verified license | Decision | Rationale |
|---|---|---|---|
| **Open MCT** (`nasa/openmct`) | Apache-2.0 ✓ | **Interoperate** (vendor allowed) | Web telemetry/visualization framework — a VIEW that already respects `observation ≠ authority`. Run as a separate dashboard consuming Weltwerk runtime telemetry; lighter coupling than embedding a large JS app. Either path is license-clean. |
| **Java Pathfinder** (`javapathfinder/jpf-core`) | Apache-2.0 ✓ (orig. NOSA 1.3, relicensed) | **Reimplement concepts** | Vendoring is *legal* but pointless: JPF checks Java bytecode; Weltwerk is Python. Reimplement the **explicit-state / bounded model-checking** discipline over the causal kernel's transition function. Stays our copyright → dual-safe. |
| **Ames Stereo Pipeline / Neo-Geography Toolkit** (`NeoGeographyToolkit/StereoPipeline`) | Apache-2.0 ✓ (since v2.0, 2012) | **Interoperate** (vendor sub-libs allowed) | Stereo terrain/3D reconstruction → point clouds → feeds the gaussian-splat lens. Heavyweight C++; run as an external reconstruction tool, ingest outputs. Reconstruction mismatches become recorded ghosts. |
| **GMAT** (`nasa/GMAT`) | Apache-2.0 ✓ (current; legacy NOSA 1.1) | **Interoperate** | Modern GMAT is Apache, but it is a large C++ application. Architecturally cleaner to invoke as an **external trajectory authority** and ingest trajectories as authoritative Weltlinie data than to embed it. |
| **Core Flight System** (`nasa/cFS` and component repos) | **Per-repository.** Modern `cFE`, `osal`, `psp`, `SBN`, app repos = Apache-2.0 ✓; the 2015 bundle release was NOSA; ancillary/older branches vary. | **Interoperate / reimplement; verify each repo** | Do **not** treat "cFS = one license." For the **Software Bus (SBN)** pub/sub-with-integrity pattern, reimplement the architecture (we already have parts) or interoperate; vendor only a specific Apache-2.0 component after confirming *that* repo+commit. |
| **IKOS** (`NASA-SW-VnV/ikos`) | **NOSA 1.3** ✗ | **Reimplement** | Sound static analysis via abstract interpretation. NOSA ⇒ do not copy. Reimplement an **abstract-interpretation pass for `world_lint`** (prove properties vs. heuristically flag them). The theory (Cousot & Cousot) is citable; the code is not copyable. |
| **PARAMESH** (`opensource.gsfc.nasa.gov/projects/paramesh`) | **NOSA 1.1+** ✗ | **Reimplement** | Parallel adaptive mesh refinement. NOSA ⇒ reimplement the **AMR idea** as a coupling-driven LOD allocator (refine where `Actual ≪ Potential`), our own code. |
| **Livingstone 2** (ARC) | Unverified — **treat as NOSA / restrictive** | **Reimplement** | Model-based diagnosis of complex systems. Until the repo license is confirmed, assume non-vendorable; reimplement the **model-based-diagnosis idea** on top of the existing divergence classifier. |
| **VERVE** (ARC) | Unverified — **treat as NOSA / restrictive** | **Reimplement / reference only** | 3D scene-graph viewer over robot state. Use only as a **design reference** for the multi-lens GeometryAdapter; do not copy until license confirmed. |
| **MFSim — Multi-fidelity Simulation** (ARC) | Unverified — **treat as NOSA / restrictive** | **Reimplement** | Multi-fidelity scheduling. Reimplement the **fidelity-selection idea**, bound to causal salience. |
| **Scalable Gaussian Process Regression** (ARC) | Unverified | **Use a permissive library instead** | For calibrated uncertainty in the prediction observer, prefer an existing **permissive** GP library (e.g. scikit-learn / GPy, BSD-family) over NASA's — better maintained and unambiguously vendorable. Decision recorded so the NASA option is not silently revisited. |

Legend: ✓ verified at time of writing · ✗ verified incompatible · *Unverified* = not yet confirmed, treated conservatively.

## Buckets (summary)

- **Vendor (permissive, clean):** Open MCT, Ames Stereo Pipeline, specific Apache-2.0 cFS components. Dual-license-safe.
- **Interoperate (no entanglement):** Open MCT server, GMAT, Ames Stereo Pipeline, cFS — and JPF as an external check in CI.
- **Reimplement (clean-room, stays our copyright — where the novelty lives):** IKOS-style abstract-interpretation lint, PARAMESH-style coupling-driven AMR/LOD, Livingstone-style causal diagnosis, JPF-style state-space exploration of the kernel.

The reimplement bucket is deliberately where Weltwerk's **differentiating IP** lives: binding each borrowed *idea* to causal salience (`Actual ≪ Potential`) is the original contribution, and keeping it as own-copyright preserves the commercial dual-license option.

## Change log

- 2026-06 — Initial ledger. Verified: Open MCT, JPF, IKOS, GMAT, Ames Stereo Pipeline, cFS (cFE/osal/psp Apache-2.0). Unverified: Livingstone 2, VERVE, MFSim, NASA GP regression. Sources in commit message / `THIRD_PARTY_NOTICES.md`.
