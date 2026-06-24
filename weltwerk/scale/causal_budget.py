# SPDX-License-Identifier: AGPL-3.0-only
"""
causal_budget.py — the Causal Budget Theorem: replicate by causality, not distance, provably losslessly.

This is the ONE network-shaped primitive the Weltwerk proofs actually support. It does NOT implement
networking. It answers, for a single authoritative event: *which chunk-deltas must be transmitted so
every client's local copy ends byte-identical to the authoritative future?* — and proves a cut criterion.

SETUP (snapshot replication of one event):
  The server holds line A (no event) and computes line B (after the event). A client already holds
  line A. The server transmits a set T of chunk-deltas; the client applies them: view = A overwritten
  with B on T. We ask which T make `view == B`.

  changed   = { c : A[c] ≠ B[c] }              the ACTUAL divergence (measured on the server)
  potential = the conservative causal envelope (topological reachability — computable a priori, no sim)
  broadcast = every chunk                        (distance-blind / send-everything)

THEOREM (machine-checked in test_causal_budget.py):
  (1) A transmission set T yields a correct client (view == B)  ⟺  T ⊇ changed.
  (2) Cutting a chunk y (y ∉ T) is SAFE  ⟺  y ∉ changed  ⟺  Δ(y) = 0.        [cut(x,y) ⟹ Δ(y)=0]
  (3) `potential ⊇ changed` (the central law), so the CONSERVATIVE cut — computed from the dependency
      graph WITHOUT simulating — is provably safe; the ACTUAL cut (T = changed) is safe AND minimal.
  (4) Budget:  |changed| ≤ |potential| ≤ |broadcast| = N.   The gap is the bandwidth saved.

This is "send everyone whose future state differs if this event exists" with a correctness guarantee —
distance replaced by causal relevance. The lossless case (ε = 0) is proven; the lossy/perceptual
extension `Δ(out_q | Δp) < ε` (cut small divergences under a tolerance) is DECLARED, not built.

OUT OF SCOPE (named, not solved): latency (a 100 ms ping is still 100 ms); packet loss / ordering;
distributed authority, trust, security, adversarial clients; client-side prediction; and HOW the server
computes B cheaply (that is the pruned allocator, a separate result). Replication ≠ networking.
`transmit-set-correct ≠ system-correct`.
"""
from __future__ import annotations

from dataclasses import dataclass

from cow_world import Edit, Rules, genesis
from teleport import Topology, full_sim_traced, reconstruct


def changed_set(line_a: dict, line_b: dict) -> frozenset:
    """The ACTUAL divergence: chunks the event truly moved. Measured, exact under the model."""
    return frozenset(c for c in line_a if line_a[c] != line_b[c])


def client_view(line_a: dict, line_b: dict, transmit: frozenset) -> dict:
    """A client holding line A, receiving deltas only for chunks in `transmit`."""
    view = dict(line_a)
    for c in transmit:
        view[c] = line_b[c]
    return view


@dataclass(frozen=True)
class Budget:
    line_a: dict
    line_b: dict
    changed: frozenset       # ACTUAL divergence (minimal safe transmit set)
    potential: frozenset     # conservative envelope (a-priori safe transmit set)
    n_chunks: int

    @property
    def broadcast(self) -> frozenset:
        return frozenset(range(self.n_chunks))

    def render(self) -> str:
        nc = self.n_chunks
        return (f"  transmit budget (chunks):  actual={len(self.changed)}  "
                f"potential={len(self.potential)}  broadcast={nc}\n"
                f"    actual/broadcast={len(self.changed) / nc:.1%}  "
                f"potential/broadcast={len(self.potential) / nc:.1%}  "
                f"(saved vs broadcast: {nc - len(self.changed)} chunks by causal cut)")


def compute_budget(snap: dict, topo: Topology, rules: Rules, seed: int, edit: Edit, horizon: int) -> Budget:
    line_a = full_sim_traced(snap, topo, rules, seed, horizon)[0][horizon]
    pruned = reconstruct(snap, topo, rules, seed, edit, horizon, prune=True)      # correct line_b
    cons = reconstruct(snap, topo, rules, seed, edit, horizon, prune=False)       # conservative envelope
    line_b = pruned.line_b
    return Budget(line_a=line_a, line_b=line_b,
                  changed=changed_set(line_a, line_b),
                  potential=cons.touched, n_chunks=topo.n)


if __name__ == "__main__":
    snap = genesis(4000, 200, 0)
    rules = Rules()
    edit = Edit("cull_pred_chunk", chunk=5)
    print("causal_budget.py — replicate by causality, not distance (lossless)\n")
    for name, topo in (("ring only", Topology(200)),
                       ("+1 teleport (5↔130)", Topology(200, ((5, 130),)))):
        b = compute_budget(snap, topo, rules, 0, edit, horizon=30)
        # demonstrate the theorem inline: actual-cut and conservative-cut both reconstruct B exactly
        ok_actual = client_view(b.line_a, b.line_b, b.changed) == b.line_b
        ok_cons = client_view(b.line_a, b.line_b, b.potential) == b.line_b
        print(f"  {name}:")
        print(b.render())
        print(f"    client correct under actual-cut={ok_actual}, conservative-cut={ok_cons}\n")
    print("  Distance would broadcast all 200 chunks; causal cut transmits only what actually changed.")
