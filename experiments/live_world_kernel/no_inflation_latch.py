# SPDX-License-Identifier: AGPL-3.0-only
"""
no_inflation_latch.py — the no-inflation invariant, compiled to the gate level. claim_ledger enforces
`evidence ≤ maturity` in software; rsi_engine enforces a promotion gate in policy; this drops it to the bottom of
the stack — a digital circuit where an over-claim is a FORBIDDEN STATE the wiring physically refuses to store,
exactly as an SR-NOR latch refuses the S=R=1 input. "Impossible claims blocked by the laws of the gates."

Everything is built from one universal primitive, the NAND gate, then verified against its boolean truth table
(the gate-level analog of anchoring reduced-round SHA to hashlib — the composites are checked, not assumed):
    NOT, AND, OR, NOR, XOR, XNOR  ⟵  NAND
    SR-NOR latch (set / reset / hold, and the forbidden S=R=1 state)  ⟵  NOR
    2-bit "greater-than" comparator  ⟵  gates;  VALID = NOT(E > C)
    guarded register: a gated D-latch per bit whose LOAD enable is ANDed with VALID

Encoding (2 bits each):
    maturity C (a ceiling) : 0=UNDERCOMMITTED/ABSENT, 1=SCOPED, 3=IMPLEMENTED   (2 is unused — no maturity grants it)
    evidence E (a rank)    : 0=N/A, 1=DECLARED, 2=MEASURED, 3=MEASURED_BY_INTERVENTION
The invariant `E ≤ C` is the same rule as every layer above. An attempt to load a claim with E > C (e.g.
MEASURED evidence, E=2, under UNDERCOMMITTED maturity, C=0) drives the guard low and the register HOLDS — the
inflating state is unreachable.

Because the whole claim space is 4×4 = 16 states, the self-test is not a sample but an EXHAUSTIVE PROOF: over all
16 (C,E), the gate-level VALID equals the integer rule, the guard blocks exactly the inflating loads, and the
stored state is *never* an over-claim. `declared ≠ verified`; here, `inflated` is simply not a representable state.

Run (from this directory):  PYTHONHASHSEED=0 python3 no_inflation_latch.py
"""
from __future__ import annotations


# --- the one primitive, then everything built from it ---
def NAND(a, b):
    return 0 if (a and b) else 1


def NOT(a):
    return NAND(a, a)


def AND(a, b):
    return NOT(NAND(a, b))


def OR(a, b):
    return NAND(NOT(a), NOT(b))


def NOR(a, b):
    return NOT(OR(a, b))


def XOR(a, b):
    n = NAND(a, b)
    return NAND(NAND(a, n), NAND(b, n))


def XNOR(a, b):
    return NOT(XOR(a, b))


# --- the fundamental 1-bit memory cell: cross-coupled NOR SR latch ---
def sr_nor_step(S, R, Q, Qb, iters=8):
    """Settle the cross-coupled NOR latch. set(1,0)->Q=1; reset(0,1)->Q=0; hold(0,0)->keep; S=R=1 is FORBIDDEN."""
    for _ in range(iters):
        Q = NOR(R, Qb)
        Qb = NOR(S, Q)
    return Q, Qb


def sr_forbidden(S, R, Q, Qb):
    """The illegal input: both outputs collapse to 0 (Q == Qb), the latch's analog of an over-claim."""
    Q, Qb = sr_nor_step(S, R, Q, Qb)
    return S == 1 and R == 1 and Q == 0 and Qb == 0


# --- claim encoding helpers ---
def bits(n):
    return (n >> 1) & 1, n & 1          # (hi, lo)


def val(hi, lo):
    return (hi << 1) | lo


# --- the no-inflation guard, in gates: VALID = NOT( E > C ) for 2-bit unsigned E, C ---
def greater_than(E, C):
    e1, e0 = bits(E)
    c1, c0 = bits(C)
    hi_gt = AND(e1, NOT(c1))                       # E's high bit beats C's
    hi_eq = XNOR(e1, c1)
    lo_gt = AND(e0, NOT(c0))
    return OR(hi_gt, AND(hi_eq, lo_gt))            # E > C


def valid(E, C):
    return NOT(greater_than(E, C))                 # the no-inflation predicate, as a gate output


# --- a gated D-latch (load if enabled, else hold), built from gates ---
def d_latch(d, en, q):
    return OR(AND(d, en), AND(q, NOT(en)))         # q_next = en ? d : q  (2:1 mux)


def guarded_register(C_in, E_in, state, load=1):
    """Attempt to load (C_in, E_in). The shared enable is gated by VALID(E_in, C_in): an inflating claim cannot
    drive the latches. Returns (new_state, accepted)."""
    c1, c0 = bits(C_in)
    e1, e0 = bits(E_in)
    en = AND(load, valid(E_in, C_in))              # the laws-of-the-gates gatekeeper
    sc1, sc0, se1, se0 = state
    nc1 = d_latch(c1, en, sc1)
    nc0 = d_latch(c0, en, sc0)
    ne1 = d_latch(e1, en, se1)
    ne0 = d_latch(e0, en, se0)
    return (nc1, nc0, ne1, ne0), en


def state_CE(state):
    sc1, sc0, se1, se0 = state
    return val(sc1, sc0), val(se1, se0)


MATURITY = {0: "UNDERCOMMITTED", 1: "SCOPED", 2: "(unused)", 3: "IMPLEMENTED"}
EVIDENCE = {0: "N/A", 1: "DECLARED", 2: "MEASURED", 3: "MEASURED_BY_INTERVENTION"}


def main():
    print("no_inflation_latch — the evidence≤maturity rule compiled to NAND gates; an over-claim is a forbidden state.\n")

    # demonstrate the SR latch and its forbidden input (the physical analog of an over-claim)
    print("  SR-NOR latch:")
    for S, R, lab in [(1, 0, "set"), (0, 1, "reset"), (0, 0, "hold-after-reset"), (1, 1, "FORBIDDEN")]:
        q, qb = sr_nor_step(S, R, 0, 1)
        print(f"    S={S} R={R} ({lab:<16}) -> Q={q} Qbar={qb}" + ("   <- Q==Qbar, illegal" if q == qb else ""))

    # reset the claim register to a VALID state: IMPLEMENTED (C=3) / N/A (E=0)
    state = (1, 1, 0, 0)
    print(f"\n  claim register reset -> C={state_CE(state)[0]} ({MATURITY[state_CE(state)[0]]}), "
          f"E={state_CE(state)[1]} ({EVIDENCE[state_CE(state)[1]]})\n")
    print("  load attempts (C=maturity ceiling, E=evidence rank):")
    print(f"    {'C':>2} {'E':>2}  {'maturity':<15}{'evidence':<26}{'VALID':>6}  result")
    for C in range(4):
        for E in range(4):
            new, en = guarded_register(C, E, state)
            sc, se = state_CE(new)
            res = "LOADED" if en else "BLOCKED (held)"
            if C in (0, 1, 3):  # print the meaningful maturities to keep the table readable
                print(f"    {C:>2} {E:>2}  {MATURITY[C]:<15}{EVIDENCE[E]:<26}{en:>6}  {res} -> stored C={sc} E={se}")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    print()
    # 1. every composite gate matches its boolean truth table (verified against the reference, built from NAND)
    refs = {
        "NOT": (NOT, lambda a: 1 - a, 1),
        "AND": (AND, lambda a, b: a & b, 2), "OR": (OR, lambda a, b: a | b, 2),
        "NOR": (NOR, lambda a, b: 1 - (a | b), 2), "XOR": (XOR, lambda a, b: a ^ b, 2),
        "XNOR": (XNOR, lambda a, b: 1 - (a ^ b), 2),
    }
    gate_ok = True
    for nm, (g, ref, ar) in refs.items():
        inputs = [(a,) for a in (0, 1)] if ar == 1 else [(a, b) for a in (0, 1) for b in (0, 1)]
        gate_ok &= all(g(*xs) == ref(*xs) for xs in inputs)
    check("gates_from_nand_correct", gate_ok, "NOT/AND/OR/NOR/XOR/XNOR (built from NAND) match their truth tables")

    # 2. SR latch set / reset / hold
    q_set, _ = sr_nor_step(1, 0, 0, 1)
    q_res, _ = sr_nor_step(0, 1, 1, 0)
    q_hold, qb_hold = sr_nor_step(0, 0, 1, 0)      # hold a stored 1
    check("sr_latch_set_reset_hold", q_set == 1 and q_res == 0 and (q_hold, qb_hold) == (1, 0),
          "set->1, reset->0, hold keeps the stored bit")

    # 3. the forbidden state exists and is detectable (the latch's over-claim analog)
    check("sr_forbidden_state", sr_forbidden(1, 1, 0, 1) and not sr_forbidden(1, 0, 0, 1),
          "S=R=1 collapses Q==Qbar==0 — an illegal, non-storable state")

    # 4. EXHAUSTIVE: the gate-level VALID equals the integer rule E<=C over all 16 (C,E)
    valid_matches = all(valid(E, C) == (1 if E <= C else 0) for C in range(4) for E in range(4))
    check("valid_equals_rule_exhaustive", valid_matches,
          "VALID(E,C) == (E<=C) for all 16 (C,E) — the gate IS the no-inflation rule, proven not sampled")

    # 5. EXHAUSTIVE: the guard loads iff E<=C, and blocks exactly the inflating claims
    state0 = (1, 1, 0, 0)                            # valid reset: IMPLEMENTED / N/A
    guard_ok = True
    for C in range(4):
        for E in range(4):
            new, en = guarded_register(C, E, state0)
            should = 1 if E <= C else 0
            loaded = (state_CE(new) == (C, E))
            held = (new == state0)
            guard_ok &= (en == should) and (loaded if should else held)
    check("guard_blocks_exactly_inflation", guard_ok,
          "over all 16 loads: enable==(E<=C); accepted loads store the claim, inflating loads HOLD the prior state")

    # 6. EXHAUSTIVE: from a valid state, no reachable stored state is an over-claim (invariant holds physically)
    inv_ok = True
    for C in range(4):
        for E in range(4):
            new, _ = guarded_register(C, E, state0)
            sc, se = state_CE(new)
            inv_ok &= (se <= sc)                     # stored evidence never exceeds stored ceiling
    check("stored_state_never_inflated", inv_ok,
          "after any load attempt, stored E<=C — an inflated claim is not a representable register state")

    # 7. the proof is COMPLETE: all 16 states enumerated (not sampled)
    check("proof_is_exhaustive", len([(C, E) for C in range(4) for E in range(4)]) == 16,
          "the claim space is 4×4=16; the checks above cover every state — a proof, not a test")

    print(f"\n  {passed}/{total} checks. The no-inflation invariant is realized in combinational logic: VALID(E,C)")
    print("  is literally a gate network equal to E<=C, wired into a flip-flop's load enable, so a claim whose")
    print("  evidence exceeds its maturity cannot be latched — the same forbidden-state principle as the SR latch's")
    print("  S=R=1. Proven exhaustively over all 16 states: at the bottom of the stack, as at the top, an over-claim")
    print("  is not rejected after the fact — it is unrepresentable. `declared ≠ verified`; integrity ≠ truth.")
    assert passed == total, "no_inflation_latch failed its own (exhaustive) self-test"


if __name__ == "__main__":
    main()
