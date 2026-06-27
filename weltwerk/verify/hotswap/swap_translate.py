# SPDX-License-Identifier: AGPL-3.0-only
"""
swap_translate.py — PO-11 (state-translation layer): the migration map μ: State_α → State_β must be
STREAM-PRESERVING. This is PO-10's admissibility (`abstract-CLOSED ⇒ exact-CLOSED`) reinstantiated with the
stream projection π as the property that must be preserved exactly, while non-stream state may be re-laid-out.

The exact proof logic. Let π project a program state onto its observable stream content (offsets + payload).
A swap is stream-correct iff the migration commutes with π on every reachable α-state:

        π ∘ μ = π            (the stream-preserving refinement / commuting square)

μ MAY lose or transform non-stream state (registers, allocator layout, internal indices — the "abstraction"),
but it MUST preserve the stream sub-state verbatim. A μ that drops, reorders, or duplicates stream items
breaks π∘μ=π and is caught here — the precise analogue of an inadmissible abstraction producing a false CLOSED.
`refinement-on-stream ≠ identity-on-everything`; `holds-here ≠ true`.

Guarantee: if `stream_preserving(μ)` over the reachable α-states, then the post-swap β-trajectory replays the
SAME stream the α-trajectory would have produced ⇒ no corruption across the swap point. A failing μ yields a
stream mismatch, which the harness reports rather than letting it pass as a silent "false restore".
"""
from __future__ import annotations


# ---- a small concrete program-state model (stream sub-state + opaque internal state) -------------
def make_state(stream, internal) -> dict:
    return {"stream": tuple(stream), "internal": list(internal)}


def pi(s) -> tuple:
    """The stream projection — the ONLY thing a swap must preserve. Everything else is free to change."""
    return tuple(s["stream"])


# ---- migration maps μ (candidates) --------------------------------------------------------------
def mu_good(s) -> dict:
    """Stream-preserving: stream verbatim, internal re-laid-out (lossy on internal is fine). π∘μ = π."""
    return {"stream": tuple(s["stream"]), "internal": list(reversed(s["internal"]))}


def mu_drop(s) -> dict:
    """FAULTY: loses the last stream item (a truncation bug). π∘μ ≠ π."""
    return {"stream": tuple(s["stream"][:-1]), "internal": list(s["internal"])}


def mu_reorder(s) -> dict:
    """FAULTY: reorders the stream (a race/duplication-class bug). π∘μ ≠ π."""
    return {"stream": tuple(reversed(s["stream"])), "internal": list(s["internal"])}


# ---- the commuting-square check (PO-10 admissibility, π as the preserved property) ----------------
def stream_preserving(mu, states) -> bool:
    """True iff π∘μ = π on every supplied (reachable) α-state. The checkable premise of swap-correctness."""
    return all(pi(mu(s)) == pi(s) for s in states)


def mismatch_witness(mu, states):
    """The first α-state where π∘μ ≠ π (None if μ is stream-preserving) — an auditable counterexample."""
    for s in states:
        if pi(mu(s)) != pi(s):
            return {"state": s, "pi_before": pi(s), "pi_after": pi(mu(s))}
    return None


def reachable_alpha_states(n: int = 6) -> list:
    """A small, deterministic sample of α program-states (stream + internal) standing in for the reachable
    set the migration must cover. Streams vary in length/content; internal state is arbitrary."""
    out = []
    for k in range(n):
        stream = tuple(range(k))                       # (), (0,), (0,1), ...
        internal = list(range(10, 10 + (k % 3)))       # arbitrary non-stream payload
        out.append(make_state(stream, internal))
    return out


def main():
    print("swap_translate.py — PO-11: stream-preserving migration μ (π∘μ = π); PO-10 commute reused\n")
    states = reachable_alpha_states()
    for label, mu in [("mu_good", mu_good), ("mu_drop", mu_drop), ("mu_reorder", mu_reorder)]:
        ok = stream_preserving(mu, states)
        w = mismatch_witness(mu, states)
        note = "preserves the stream (π∘μ=π)" if ok else f"BREAKS the stream at {w['state']['stream']}"
        print(f"  {label:10s} stream_preserving={ok!s:5s}  {note}")
    print("\n  a stream-preserving μ ⇒ β resumes the identical stream ⇒ no corruption across the swap.")
    print("  a faulty μ is caught with a witness, never passed as a silent false restore. refinement ≠ identity.")


if __name__ == "__main__":
    main()
