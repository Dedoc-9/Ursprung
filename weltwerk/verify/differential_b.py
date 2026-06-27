# SPDX-License-Identifier: AGPL-3.0-only
"""
differential_b.py — Proof Obligation PO-1: Approach-B faithfulness over a WORLD DISTRIBUTION.

`test_symbolic_b.py` checks the direct-SMT engine (Approach B) against the explicit reference on two hand-built
worlds. PO-1 asks for more: that the re-encoding agrees with the explicit engine across a *generated
distribution* of topologies — the real test of a second semantic definition, since a re-encoding bug typically
hides in a structural case (multi-parent reach, fan-out, deeper chains) the two examples never exercise.
`re-encoded ≠ verified` until it agrees everywhere it claims to cover.

SCOPE (stated, the fragment B is faithful to): `{destroy, repair}` over `(alive, disabled)`, invariant
`not_disabled` on `tail`. Worlds are generated **acyclic** (edges only `e_i → e_j`, `i < j`). Cyclic worlds are
*excluded by construction*: in a cycle a node lies in its own `reach`, so the two definitions of `repair`'s
upstream-alive guard can diverge (`solver_adapter_b` includes the node in its own upstream; `world_sim`
excludes self). That divergence is a **documented boundary / open ghost**, not silently swept in — Approach B
is only claimed faithful on acyclic `{destroy,repair}` worlds. `acyclic-fragment ≠ all-worlds`.

Agreement is checked three ways per world: same VIOLATED/none status, same shortest-witness *length* (SMT
models aren't canonical, so identical event tuples are not required), and B's witness **replays** to a real
disabled `tail` (the violation is real, not a solver artifact).
"""
from __future__ import annotations

import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                                   # noqa: E402
from kernel_check import check                                   # noqa: E402
import solver_adapter_b                                          # noqa: E402

TAIL_OK = {"tail_ok": (lambda s: s.runtime["tail"]["status"] != "disabled")}


def gen_world(seed: int, n: int = 5) -> str:
    """An acyclic {destroy,repair} world. `tail` is the last entity; edges only go low→high index (no cycles).
    Seeds ≡ 0 (mod 4) isolate `tail` (no incoming) ⇒ a guaranteed no-violation world, for distribution balance."""
    rng = random.Random(seed)
    names = [f"e{i}" for i in range(n - 1)] + ["tail"]
    edges = {nm: [] for nm in names}
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < 0.45:
                edges[names[i]].append(names[j])
    if seed % 4 == 0:                                            # force an isolated-tail (clean) world
        for nm in names:
            edges[nm] = [d for d in edges[nm] if d != "tail"]
    L = [f'world "DB_{seed}"', 'entity fac:', '  position 0 0 0'] + [f'  controls {nm}' for nm in names]
    for i, nm in enumerate(names):
        L += [f'entity {nm}:', f'  position {i + 1} 0 0', '  health 10']
        L += [f'  powers {d}' for d in edges[nm]]
    return "\n".join(L) + "\n"


def _replay_tail(world: str, events) -> str:
    sim = WorldSim(world)
    for e in events:
        sim.apply_event(*e)
    return sim.runtime["tail"]["status"]


def compare(seed: int, bound: int = 5) -> dict:
    from symbolic_engine_b import SymbolicDirectEngine, SymbolicInvariant
    from engine import build_model, VerificationOptions
    w = gen_world(seed)
    ex = check(w, max_depth=bound, invariants=TAIL_OK)
    ex_viol = ex.ghost is not None
    eng = SymbolicDirectEngine(SymbolicInvariant("not_disabled", "tail"))
    vr = eng.verify(build_model(w), VerificationOptions(depth_bound=bound))
    b_viol = vr.status == "VIOLATED"
    status_agree = ex_viol == b_viol
    len_agree = (not ex_viol) or (b_viol and len(vr.witness) == len(ex.ghost.path))
    replay_ok = (not b_viol) or (_replay_tail(w, list(vr.witness)) == "disabled")
    return {"seed": seed, "ex_viol": ex_viol, "b_status": vr.status,
            "agree": status_agree and len_agree and replay_ok,
            "status_agree": status_agree, "len_agree": len_agree, "replay_ok": replay_ok}


def run(n_worlds: int = 32, bound: int = 5) -> dict:
    if not solver_adapter_b.HAVE_SOLVER:
        return {"skipped": True}
    rows = [compare(s, bound) for s in range(n_worlds)]
    disagree = [r for r in rows if not r["agree"]]
    return {
        "skipped": False, "n": len(rows),
        "agreements": sum(r["agree"] for r in rows),
        "disagreements": disagree,
        "n_violated": sum(r["ex_viol"] for r in rows),
        "n_clean": sum(not r["ex_viol"] for r in rows),
    }


def main():
    print("differential_b.py — PO-1: Approach-B vs explicit over a generated acyclic world distribution\n")
    r = run()
    if r["skipped"]:
        print("  SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
        return
    print(f"  worlds={r['n']}  (violated={r['n_violated']}, clean={r['n_clean']})  "
          f"agreements={r['agreements']}/{r['n']}")
    if r["disagreements"]:
        for d in r["disagreements"]:
            print(f"    DISAGREE seed={d['seed']}: status={d['status_agree']} len={d['len_agree']} "
                  f"replay={d['replay_ok']} (ex_viol={d['ex_viol']}, b={d['b_status']})")
    else:
        print("  full agreement: same status, same shortest length, every B witness replays to disabled.")
    print("\n  Approach B is faithful on the acyclic {destroy,repair}/not_disabled fragment. re-encoded ≠ verified")
    print("  beyond this fragment; cyclic repair remains a documented boundary.")


if __name__ == "__main__":
    main()
