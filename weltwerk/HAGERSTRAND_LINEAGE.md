<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk as computational time-geography — the Hägerstrand lineage

Weltwerk was built bottom-up (text → causal graph → runtime → projection), not from a theory of geography.
But its core vocabulary turns out to be a near-isomorphism of **time geography**, founded by the Swedish
geographer **Torsten Hägerstrand** (Lund University) around 1970 — most famously in *"What about people in
regional science?"* (Papers of the Regional Science Association, 1970). This note records that lineage
honestly: as a retrospective structural correspondence, not a derivation and not a validation.

## The "space-time aquarium"

Hägerstrand visualized society as a **space-time cube** — geographic space on the floor, time rising
vertically — in which each individual's life is drawn as a continuous **path** moving upward through the
box. You watch the trajectories the way you watch fish in a tank: bundling together, dispersing, halting at
places. That viewing-box is the "aquarium." Crucially, it is a *view*: you observe the paths; the diagram
does not move them.

## The mapping

| Time geography (Hägerstrand, ~1970) | Weltwerk |
|---|---|
| **space-time path** (a life-path / trajectory) | `Weltlinie` / worldline; *the committed trajectory records what occurred* |
| **space-time prism** (everywhere reachable under a time budget + speed) | the **Potential** set: `reach_ge1`, the light-cone, `reachability_algebra` — *Potential ⊇ Actual* |
| **bundle** (paths converging at a station to act together) | **causal coupling**; shared reach (contested control); the coupling→headroom-collapse envelope |
| **station** (a place where paths meet) | an **entity / node** in the `CausalGraph` |
| **capability constraint** (biological/physical limits, finite time) | per-event cost / budgets; AI capability limits (view range, speed) |
| **coupling constraint** (must be co-present with people/tools) | typed **relations** (`powers`/`feeds`/`depends_on`); the coupling regime |
| **authority constraint** (domains controlled, access-gated) | **authority itself** — `controller()`, the pre-play validation gate, capture/control, and the spine `observation ≠ authority` |
| **the aquarium** (the cube you view paths in) | the **renderer / GeometryAdapter / lenses** (voxel · FPS · splats): you view, you cannot alter |

The sharpest single correspondence: Hägerstrand named **authority** as the third force constraining
trajectories in 1970. Weltwerk's whole discipline is built on keeping *authority* distinct from the *view*.
The second-sharpest: his **prism** is reachability-under-constraint — exactly Weltwerk's Potential set, the
thing every lens projects and every cost measurement bounds.

## Where it is tight, and where it diverges (honest scope)

**Tight (real correspondence):** trajectory, reachability-under-constraint, coupling/bundling,
authority-as-constraint, and observation-as-non-altering-view. These aren't decorative — the structures line
up term for term.

**Loose / divergent (do not over-read):**
- Time geography is a **descriptive** framework for human mobility + a **visualization**; it is not a formal
  causality, a physics, or a computation. Weltwerk is a deterministic computational substrate.
- Weltwerk adds machinery Hägerstrand had no notion of: deterministic **replay**, **content-hashed**
  provenance, discrete **causal events**, **forks / counterfactuals**, consequence **diffs**, and the
  machine-checked **renderer-authority invariant**.
- Conversely, Weltwerk is not an empirical study of real human movement; it makes no claim about people.
- This lineage **does not validate** Weltwerk (an old framework agreeing with you isn't evidence), nor does
  Weltwerk validate time geography. `resonance ≠ proof`.

## Why record it

It gives the project an honest intellectual ancestor and a precise way to describe what it is:
**a computational, causal time-geography** — life-paths (trajectories) over a graph, with prisms
(reachability), bundles (coupling), and authority as a first-class constraint, rendered into a literal
aquarium you can orbit. That is a truer one-line description than "a game engine" or "a splat editor," and
it places the `observation ≠ authority` boundary in a tradition fifty years older than the code.

> Reference to verify if cited formally: T. Hägerstrand, "What about people in regional science?",
> *Papers of the Regional Science Association* 24 (1970), 7–21. (Attribution recalled, not re-checked here.)
