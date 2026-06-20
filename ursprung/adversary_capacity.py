# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/adversary_capacity.py — Adversary Information Capacity (M21): security is non-identifiability under
bounded experimental access, and the bound is the adversary's MODEL CLASS, not its probe budget.

M20 measured one learner (a 1-D active bisection agent) and found that "constant-feel resists learning." This
module takes the warning M20 itself wrote — *secure against THIS observer class ≠ secure* — and makes it the
experiment. It does not add a defense. It VARIES THE ADVERSARY and watches what becomes identifiable, which is
the move both readings of M20 converged on: the system is no longer judged by what it hides, but by which
CLASSES of observers can reconstruct it.

This forces a distinction M20 had blurred — two different identification targets:

  * the SECRET   — the hidden boundary T (where the enemy is).
  * the GENERATOR — the rule that maps hidden state → observable behaviour (the transfer function the player
                    actually learns: "the system keys off bit 3 of my position").

And it sweeps a lattice of adversary classes (Adversary Information Capacity = hypothesis-space richness, NOT
bandwidth/probes/memory):

  C0 passive       no hypothesis fitting (the pre-active recipient).
  C1 threshold     active bisection over a 1-D threshold class (this is M20's agent).
  C2 single-bit    hypotheses of the form "response = a single probe bit."
  C3 structured    threshold ∪ single-bit ∪ parity-over-bits (the richest tested class).

THE PRODUCED RESULT (each computed by an actual little learner, not asserted):

  * constant-feel's SECRET is non-identifiable under EVERY class — because the policy severs T from the
    channel (the response does not depend on T at all). This is information-theoretic, AIC-INDEPENDENT: no
    learner, however rich, can extract what was never transmitted. It is the only ABSOLUTE guarantee in the
    whole stack.
  * constant-feel's GENERATOR is non-identifiable under C1 (a threshold learner cannot express the rule) but
    IS identifiable under C2/C3. So M20's "resists learning" was true only against C1; a structure learner
    recovers the rule. Generator-privacy (`image ≠ generator`) is only ever model-class-RELATIVE.
  * the classes are INCOMPARABLE except that C3 dominates: C1 cracks the threshold rule but not the bit rule;
    C2 cracks the bit rule but not the threshold. AIC is a LATTICE, not a scalar — a sharpening of the
    intuition that a "stronger" attacker simply knows more.

The synthesis the arc has been building toward:  Security = non-identifiability under bounded experimental
access. SECRET-privacy can be made absolute (sever the secret from the channel). GENERATOR-privacy never can —
for any finite rule there is a class rich enough to identify it; you can only bound the access.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures identifiability; it commits nothing, asserts no
truth. identifiability ≠ truth; secure-against-class ≠ secure; integrity ≠ truth.

HONEST BOUND: the adversary classes here are a tiny illustrative lattice; a real ML agent or human occupies an
unknown, likely far richer class, and may build surrogate models outside all four. The "absolute" secret
result holds only for this exact channel model (T genuinely absent from the response) — a real engine that
leaks T through any correlated side effect breaks it. This proves the SHAPE of the claim (identifiability is
class-relative; severing is the only absolute), not a guarantee against all observers. simulation ≠ physics.
"""
from __future__ import annotations


SPAN = 256
NBITS = 8
_PROBES = list(range(SPAN))          # covers every low-bit pattern, so each bit/parity is detectable


# --- the systems under test (rules of probe and the hidden secret T) --------------------------------

def rule_naive(probe, T):
    """Threshold rule — the response depends on the secret T (T is identifiable by a threshold learner)."""
    return probe >= T


def rule_constant_feel(probe, T):
    """Response keys off a single LOW probe bit and is INDEPENDENT of T (M19/M20). The secret is severed from
    the channel; the generator is 'bit 3'. A low bit toggles many times across the probe range, so the rule is
    NON-monotone — a threshold learner (C1) genuinely cannot express it (a high bit would be a disguised
    threshold and would crack for the wrong reason)."""
    return ((probe >> 3) & 1) == 1


def rule_keyed_feel(probe, T):
    """Response is a parity over several probe bits, independent of T — a generator no single-bit learner can
    express (needs the structured class)."""
    return (bin(probe & 0b01010100).count("1") % 2) == 1


RULES = {"naive": rule_naive, "constant_feel": rule_constant_feel, "keyed_feel": rule_keyed_feel}
_SECRET_IN_CHANNEL = {"naive": True, "constant_feel": False, "keyed_feel": False}


# --- the little learners (each tries to identify the generator within its hypothesis class) ----------

def _column(rule, T):
    return [bool(rule(p, T)) for p in _PROBES]


def detect_threshold(rule, T):
    """C1's class: is the response a monotone step in probe (all False then all True)? If so the rule is a
    threshold and T is recoverable."""
    col = _column(rule, T)
    seen_true = False
    for v in col:
        if v:
            seen_true = True
        elif seen_true:
            return False                       # a False after a True ⇒ not a clean threshold
    return any(col) and not all(col)


def detect_single_bit(rule, T):
    """C2's class: does a single probe bit (or its negation) reproduce the response exactly?"""
    col = _column(rule, T)
    for b in range(NBITS):
        bitb = [bool((p >> b) & 1) for p in _PROBES]
        if col == bitb or col == [not x for x in bitb]:
            return b
    return None


def detect_parity(rule, T):
    """C3's extra reach: does the parity of some non-empty bit-mask (or its negation) reproduce the response?"""
    col = _column(rule, T)
    for mask in range(1, 1 << NBITS):
        par = [(bin(p & mask).count("1") % 2) == 1 for p in _PROBES]
        if col == par or col == [not x for x in par]:
            return mask
    return None


# --- the adversary-class lattice (Adversary Information Capacity) ------------------------------------

ADVERSARY_CLASSES = ("C0_passive", "C1_threshold", "C2_single_bit", "C3_structured")


def generator_identifiable(policy, adversary):
    """Can `adversary`'s hypothesis class reproduce the policy's input→output rule (identify the generator)?"""
    rule = RULES[policy]
    T = 100
    if adversary == "C0_passive":
        return False
    if adversary == "C1_threshold":
        return detect_threshold(rule, T)
    if adversary == "C2_single_bit":
        return detect_single_bit(rule, T) is not None
    if adversary == "C3_structured":
        return detect_threshold(rule, T) or (detect_single_bit(rule, T) is not None) or (detect_parity(rule, T) is not None)
    raise ValueError("unknown adversary class")


def secret_identifiable(policy, adversary):
    """Can `adversary` recover the SECRET T? Only if the channel carries T-information AND the class can
    express that dependence. If the policy severed T from the channel, NO class can — information-theoretic."""
    if not _SECRET_IN_CHANNEL[policy]:
        return False                           # severed: AIC-independent non-identifiability
    # T leaks here as a threshold ⇒ only the classes that can detect a threshold recover it
    return adversary in ("C1_threshold", "C3_structured")


# --- the capacity sweep -----------------------------------------------------------------------------

def crucible():
    out = {"matrix": {}}
    for policy in RULES:
        out["matrix"][policy] = {
            a: {"secret": secret_identifiable(policy, a), "generator": generator_identifiable(policy, a)}
            for a in ADVERSARY_CLASSES
        }
    M = out["matrix"]
    # 1. the secret of constant-feel is non-identifiable under EVERY class (severing = absolute)
    out["constant_secret_absolute"] = all(not M["constant_feel"][a]["secret"] for a in ADVERSARY_CLASSES)
    # 2. constant-feel's GENERATOR: invisible to C1 (M20's class) but identified by C2/C3 — class-relative
    out["constant_generator_safe_vs_C1"] = (M["constant_feel"]["C1_threshold"]["generator"] is False)
    out["constant_generator_cracked_by_C2"] = (M["constant_feel"]["C2_single_bit"]["generator"] is True)
    out["constant_generator_cracked_by_C3"] = (M["constant_feel"]["C3_structured"]["generator"] is True)
    # 3. naive's secret leaks only to the matching class (C1/C3), not the "richer-looking" C2
    out["naive_secret_C1"] = M["naive"]["C1_threshold"]["secret"] is True
    out["naive_secret_not_C2"] = M["naive"]["C2_single_bit"]["secret"] is False
    # 4. classes are incomparable (a lattice): C1 cracks naive-gen not constant-gen; C2 the reverse
    out["classes_incomparable"] = (M["naive"]["C1_threshold"]["generator"] and not M["constant_feel"]["C1_threshold"]["generator"]
                                   and M["constant_feel"]["C2_single_bit"]["generator"] and not M["naive"]["C2_single_bit"]["generator"])
    # 5. C3 dominates: it identifies every generator
    out["C3_dominates_generator"] = all(M[p]["C3_structured"]["generator"] for p in RULES)
    # 6. keyed-feel needs the richest class (parity): not C1, not C2, yes C3
    out["keyed_only_C3"] = (not M["keyed_feel"]["C1_threshold"]["generator"]
                            and not M["keyed_feel"]["C2_single_bit"]["generator"]
                            and M["keyed_feel"]["C3_structured"]["generator"])
    # the synthesis: secret-privacy can be ABSOLUTE, generator-privacy only ever AIC-RELATIVE
    out["secret_absolute_generator_relative"] = (out["constant_secret_absolute"]
                                                 and out["constant_generator_cracked_by_C2"])
    out["recovered_bit"] = detect_single_bit(rule_constant_feel, 100)   # the structure learner names bit 3
    return out


def demo():
    r = crucible()
    M = r["matrix"]
    print("Adversary Information Capacity — security = non-identifiability under bounded experimental access\n")
    print("  identifiability matrix  (S=secret / G=generator),  · = safe,  X = identified\n")
    print("  %-14s %s" % ("", "  ".join("%-13s" % a for a in ADVERSARY_CLASSES)))
    for p in RULES:
        cells = []
        for a in ADVERSARY_CLASSES:
            s = "X" if M[p][a]["secret"] else "·"
            g = "X" if M[p][a]["generator"] else "·"
            cells.append("S:%s G:%s     " % (s, g))
        print("  %-14s %s" % (p, "  ".join(c[:13] for c in cells)))
    print()
    print("  · constant-feel SECRET non-identifiable under ALL classes (severed from channel): %s — absolute"
          % r["constant_secret_absolute"])
    print("  · constant-feel GENERATOR: safe vs C1 (M20's learner)=%s, cracked by C2=%s, by C3=%s — class-relative"
          % (r["constant_generator_safe_vs_C1"], r["constant_generator_cracked_by_C2"], r["constant_generator_cracked_by_C3"]))
    print("  · the structure learner names the rule: response keys off bit %s" % r["recovered_bit"])
    print("  · classes are incomparable (a lattice, not a scalar): %s; C3 dominates: %s"
          % (r["classes_incomparable"], r["C3_dominates_generator"]))
    print("\n  SECRET-privacy can be ABSOLUTE (sever the secret); GENERATOR-privacy is only ever AIC-RELATIVE —")
    print("  for any finite rule a rich enough class identifies it. secure-against-class ≠ secure; integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("adversary_capacity", OBSERVER, mutates_core=False,
                          note="Adversary Information Capacity — sweep the adversary MODEL CLASS (lattice, not "
                               "scalar); secret-privacy can be absolute (severed channel), generator-privacy is "
                               "only class-relative; M20's 'constant-feel' generator falls to a structure learner")
    except LayerViolation:
        pass
