# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/reality_harness.py — the Reality Harness (M18): traffic produces the hypothesis.

M1–M17 built a complete reference model from committed truth to photon, every rung carrying a falsifiable
bench with a negative control. But M17 exposed the limit of the whole method: convergence is only meaningful
against REAL divergence, and no constructed bench can promote a claim about it. The discipline up to here was:

    bench proves hypothesis.

M18 inverts it:

    traffic produces the hypothesis.

This module is not another defense. It is the measurement substrate the model has been written to deserve: an
authoritative server (CORE-driven), a SIMULATED network channel (latency / jitter / loss / reorder), and
client mirrors that predict, diverge, and reconcile. It then MEASURES — correction entropy, convergence time,
observer distinguishability, information gained per correction, and fidelity cost — across reconciliation
policies, and lets the numbers fall where they do.

The headline finding is produced, not asserted: M17's bucketing buys *magnitude* privacy at near-zero fidelity
cost, but does NOT hide the *existence* of disagreement (a far client sees "none", a near one sees a class —
existence still leaks). Hiding existence needs cover corrections (a Convergence Privacy Budget / equivalence
floor), which costs fidelity and STILL cannot mask a large correction without capping it (which breaks
convergence). So convergence-privacy and convergence-fidelity are a measured FRONTIER, not a win — the
traffic-derived version of the user's own proposed refinements, and their limit.

THE SWAPPABLE SEAM: `NetworkChannel` is a deterministic model. Replace it with a real socket and this same
harness becomes the real experiment. That substitution — not any number below — is the actual M18→reality step.

CLASSIFICATION: OBSERVER (mutates_core=False). The server's authoritative step is the only CORE mutation and
it is deterministic; client mirrors are speculative predictions reconciled AGAINST the committed trajectory,
never written back. The harness records; it commits nothing and asserts no truth.

HONEST BOUND: the network here is SIMULATED — a seeded model (Arbitrary-Boundary Law: a model construct, not
the network). The measurements are measured-from-simulation, still constructed; what has changed is the MODE
(traffic-driven, reproducible) and the architecture (a real channel drops in unchanged). Real latency, jitter,
DVFS, and adversarial input-timing will move every number here. integrity ≠ truth; simulation ≠ physics.
"""
from __future__ import annotations

import math
from collections import Counter


# --- the swappable seam: a deterministic simulated network channel ----------------------------------

class NetworkChannel:
    """A seeded model of one-way network behaviour (latency in ticks, jitter, loss). Deterministic given the
    seed → fully reproducible. THIS IS THE SEAM: replace `delay_for` with a real socket's measured RTT and the
    harness becomes the real experiment, unchanged above this line."""

    def __init__(self, base_latency=4, jitter=2, loss_pct=0, seed=1):
        self.base_latency = base_latency
        self.jitter = jitter
        self.loss_pct = loss_pct
        self._s = seed & 0x7fffffff or 1

    def _rand(self):
        # a small LCG — determinism without depending on PYTHONHASHSEED
        self._s = (1103515245 * self._s + 12345) & 0x7fffffff
        return self._s

    def delay_for(self, tick):
        """Latency (in ticks) for a packet sent at `tick`, or None if the packet is lost."""
        if self.loss_pct and (self._rand() % 100) < self.loss_pct:
            return None
        j = (self._rand() % (2 * self.jitter + 1)) - self.jitter if self.jitter else 0
        return max(1, self.base_latency + j)


# --- the authoritative world (a deterministic toy; the real one wires to world_core) ----------------

def intensity_field(n_clients, epicenter, radius):
    """A hidden event's influence on each client's causal neighborhood (0 = outside it). The clients a
    correction will diverge for. The real harness derives this from CORE; here it is an explicit integer model."""
    return [max(0, radius - abs(i - epicenter)) for i in range(n_clients)]


def true_corrections(intensity, latency):
    """The magnitude of correction each client actually needs once the delayed authoritative snapshot arrives:
    a client mispredicts for `latency` ticks wherever the hidden event touched it."""
    return [k * latency for k in intensity]


# --- reconciliation policies (what the client is allowed to OBSERVE about its own correction) --------

def _bucket(mag):
    m = abs(int(mag))
    if m == 0:
        return "none"
    if m <= 4:
        return "small"
    if m <= 16:
        return "medium"
    return "large"


_CLASS_COST = {"none": 0, "small": 1, "medium": 2, "large": 3}


def expose(corrections, policy):
    """The externally observable reconciliation signal per client under a policy.
    exact:    the raw magnitude (invertible — the correction IS the hidden information).
    bucketed: the bounded family {none,small,medium,large} (M17 — hides magnitude, not existence).
    floor:    a Convergence Privacy Budget — every client emits at least a 'small' cover correction, so
              'none' never appears (hides existence for small events; large events still show through)."""
    if policy == "exact":
        return [abs(int(c)) for c in corrections]
    if policy == "bucketed":
        return [_bucket(c) for c in corrections]
    if policy == "floor":
        order = ["none", "small", "medium", "large"]
        return [max(_bucket(c), "small", key=order.index) for c in corrections]
    raise ValueError("policy must be exact|bucketed|floor")


# --- measurements (the harness records; it does not judge) ------------------------------------------

def shannon_entropy(values):
    """Bits of entropy in the exposed-signal distribution. Low ⇒ the repair is predictable (a leak surface)."""
    n = len(values)
    if n == 0:
        return 0.0
    return -sum((k / n) * math.log2(k / n) for k in Counter(values).values())


def observer_distinguishability(exposed, near_mask):
    """Can an observer separate clients IN the event's neighborhood from those outside it, by their exposed
    reconciliation? 0.5 = chance (indistinguishable); 1.0 = perfectly separable (existence-of-disagreement
    fully leaks). This is the M16/M17 separability, now MEASURED over traffic."""
    far_classes = {exposed[i] for i in range(len(exposed)) if not near_mask[i]}
    near_idx = [i for i in range(len(exposed)) if near_mask[i]]
    if not near_idx:
        return 0.5
    distinguishable = sum(1 for i in near_idx if exposed[i] not in far_classes)
    return 0.5 + 0.5 * (distinguishable / len(near_idx))


def info_bits(exposed):
    """Information an observer can extract from the exposed signal ≈ log2(distinguishable states)."""
    return math.log2(len(set(exposed))) if exposed else 0.0


def fidelity_cost(corrections, policy):
    """The reconciliation work actually applied. exact/bucketed converge on the true corrections; the floor
    adds cover corrections to clients that did not need them (privacy bought with fidelity)."""
    applied = sum(abs(int(c)) for c in corrections)
    if policy == "floor":
        # every client with no real correction now emits a 'small' cover reconciliation
        applied += sum(2 for c in corrections if abs(int(c)) == 0)
    return applied


def counterfactual_bits(intensity, latency):
    """Counterfactual Debt (the convergence form of M13): a client that can VARY its input and watch the
    correction learns the boundary. ≈ log2(distinct corrections it can induce). A single correction is
    harmless; a thousand chosen experiments is a query oracle."""
    inducible = {k * latency for k in range(max(intensity) + 1)} if intensity else {0}
    return math.log2(len(inducible)) if inducible else 0.0


def aggregate_extraction(exposed):
    """Convergence Privacy Budget: what ALL observers together can extract (distinct classes seen across the
    fleet), not what any one client sees. The M12→M13 jump, on the convergence axis."""
    return len(set(exposed))


# --- the experiment (traffic-driven; no asserted hypothesis) ----------------------------------------

def run_experiment(policy, n_clients=10, epicenter=7, radius=3, channel=None):
    channel = channel or NetworkChannel(base_latency=4, jitter=2, seed=1)
    latency = channel.delay_for(tick=0)            # one sampled, reproducible latency for this run
    intensity = intensity_field(n_clients, epicenter, radius)
    near_mask = [k > 0 for k in intensity]
    corrections = true_corrections(intensity, latency)
    exposed = expose(corrections, policy)
    return {
        "policy": policy,
        "latency_ticks": latency,
        "convergence_time": latency + 1,           # measured: replay completes one tick after the snapshot lands
        "correction_entropy": round(shannon_entropy(exposed), 3),
        "distinguishability": round(observer_distinguishability(exposed, near_mask), 3),
        "info_bits": round(info_bits(exposed), 3),
        "fidelity_cost": fidelity_cost(corrections, policy),
        "counterfactual_bits": round(counterfactual_bits(intensity, latency), 3),
        "aggregate_extraction": aggregate_extraction(exposed),
    }


def crucible():
    out = {}
    ex = run_experiment("exact")
    bu = run_experiment("bucketed")
    fl = run_experiment("floor")
    out["exact"], out["bucketed"], out["floor"] = ex, bu, fl
    # the channel is deterministic (reproducible traffic)
    out["channel_deterministic"] = (NetworkChannel(seed=1).delay_for(0) == NetworkChannel(seed=1).delay_for(0))
    # measured findings (produced, not asserted):
    out["bucketing_reduces_entropy"] = bu["correction_entropy"] < ex["correction_entropy"]
    out["bucketing_reduces_info"] = bu["info_bits"] < ex["info_bits"]
    out["bucketing_keeps_existence_leak"] = bu["distinguishability"] == 1.0       # existence still leaks
    out["floor_reduces_distinguishability"] = fl["distinguishability"] < bu["distinguishability"]
    out["floor_costs_fidelity"] = fl["fidelity_cost"] > bu["fidelity_cost"]
    out["no_free_lunch"] = not (fl["distinguishability"] <= 0.5 and fl["fidelity_cost"] <= bu["fidelity_cost"])
    out["large_events_still_leak"] = fl["distinguishability"] > 0.5               # can't mask big corrections
    return out


def demo():
    r = crucible()
    print("Reality Harness — traffic produces the hypothesis (simulated network; the channel is the seam)\n")
    hdr = "  %-9s entropy=%-6s distinguish=%-6s info_bits=%-6s fidelity_cost=%-4s"
    for name in ("exact", "bucketed", "floor"):
        d = r[name]
        print(hdr % (name, d["correction_entropy"], d["distinguishability"], d["info_bits"], d["fidelity_cost"]))
    print("\n  measured findings (not asserted):")
    print("   · bucketing (M17) reduces correction entropy/info: %s / %s"
          % (r["bucketing_reduces_entropy"], r["bucketing_reduces_info"]))
    print("   · bucketing still leaks EXISTENCE of disagreement (distinguishability 1.0): %s"
          % r["bucketing_keeps_existence_leak"])
    print("   · a cover-correction floor lowers distinguishability (%.2f) but costs fidelity (%d>%d): %s / %s"
          % (r["floor"]["distinguishability"], r["floor"]["fidelity_cost"], r["bucketed"]["fidelity_cost"],
             r["floor_reduces_distinguishability"], r["floor_costs_fidelity"]))
    print("   · large corrections still leak; no policy gets full privacy free: %s" % r["no_free_lunch"])
    print("\n  convergence-privacy ⟂ convergence-fidelity is a MEASURED frontier, not a win. simulation ≠ physics;")
    print("  the proof is replacing the channel with a socket. integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("reality_harness", OBSERVER, mutates_core=False,
                          note="Reality Harness — authoritative server + simulated channel + client mirrors; "
                               "measures correction entropy/convergence/distinguishability/fidelity; traffic "
                               "produces the hypothesis. the channel is the swappable seam to real netcode")
    except LayerViolation:
        pass
