# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/dependency_integrity.py — the Dependency Integrity Layer (who decides what dependency info to trust).

Milestone 9 made dependency access the scarce resource. The next pressure point: that access channel can be
**corrupted, stale, or adversarial.** Every prior law failed at an analogous seam (importance ≠ allocation,
time-scale mismatch, threshold-blind resistance, prediction-as-authority); the new one is **access ≠
relevance.** This layer is a guard around the information pipeline, not another allocator.

A dependency is not a bare `requires("destruction_shader")`. It is a CLAIM that must carry its own doubt:

    DependencyClaim(source, dependency, confidence, evidence, expiration, consequence)

Three integrity mechanisms (mirroring the sealed workbench's discipline — `chronicle` content-addressing +
`quorum` exact-integer k-of-n consensus; here re-implemented stdlib-only and self-contained):

  1. TAUTOLOGY (forgery check) — the claim is content-addressed; recomputing its hash must equal the stored
     hash. This holds iff the record is unforged — an *integrity tautology*, never a truth claim
     (`integrity ≠ truth`: a perfectly unforged claim can still be wrong).
  2. CONSENSUS STREAM VALIDATOR — k-of-n independent witnesses must agree on the *same* claim hash by EXACT
     INTEGER tally (no float epsilon). Dissent is kept as a ghost, not silently dropped. (consensus ≠ truth:
     a colluding ≥k majority agrees on a falsehood just as cleanly.)
  3. EVIDENCE + DECAY — Preparation Value gains two factors so access ≠ relevance is closed:
        Preparation Value = Causal Surface Area × Dependency Access × Evidence Confidence × Temporal Relevance
     (false dependency → evidence 0 → no wasted budget; stale dependency → relevance → 0 → cools off).

THE INVARIANT: the renderer may consume dependency information, but it must know how stale, uncertain, and
expensive that information is.

CLASSIFICATION: OBSERVER (mutates_core=False). It validates and weights dependency claims; it commits no state
and asserts no truth. integrity ≠ truth.
"""
from __future__ import annotations

import hashlib
import json

from . import causal_surface as cs
from . import causal_contract as cc          # temporal_relevance (the half-life)
from . import dependency_surface as dep


class DependencyClaim:
    __slots__ = ("source", "dependency", "confidence", "evidence", "issued_tick", "expiration", "consequence")

    def __init__(self, source, dependency, confidence=100, evidence=100, issued_tick=0, expiration=10 ** 9,
                 consequence=1):
        self.source = source
        self.dependency = dependency
        self.confidence = confidence            # the claimant's self-reported confidence (not trusted alone)
        self.evidence = evidence                # independent corroboration that the dependency is REALIZED (0..100)
        self.issued_tick = issued_tick
        self.expiration = expiration
        self.consequence = consequence

    def content_hash(self):
        """Content address of the claim's identity (integer-clean fields). Recompute-and-compare = the
        integrity tautology: equal iff unforged."""
        payload = json.dumps({"source": self.source, "dependency": self.dependency,
                              "consequence": int(self.consequence)}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def is_fresh(self, now_tick):
        return now_tick <= self.expiration


def tautology_holds(claim, stored_hash):
    """The forgery check: a claim is admissible iff its recomputed content hash matches the stored one."""
    return claim.content_hash() == stored_hash


# --- the exact-integer k-of-n consensus stream validator --------------------------------------------

def consensus_validate(witness_claims, k):
    """Validate a stream of claims about the SAME dependency from independent witnesses. Exact-integer tally
    of agreement on content hash; admit iff ≥ k witnesses agree. Dissent is returned as a ghost, never
    silently dropped. Returns {admitted, winning_hash, agree, dissent}. consensus ≠ truth."""
    tally = {}
    for c in witness_claims:
        tally[c.content_hash()] = tally.get(c.content_hash(), 0) + 1   # exact integer count, no float
    if not tally:
        return {"admitted": False, "winning_hash": None, "agree": 0, "dissent": 0}
    winning = max(sorted(tally), key=lambda h: tally[h])               # deterministic tie-break by hash
    agree = tally[winning]
    dissent = sum(v for h, v in tally.items() if h != winning)
    return {"admitted": agree >= k, "winning_hash": winning, "agree": agree, "dissent": dissent}


# --- evidence + decay → integrity-aware Preparation Value -------------------------------------------

def integrity_aware_preparation_value(obj, claim, now_tick, coherence=30):
    """Preparation Value = CSA × Dependency Access × Evidence Confidence × Temporal Relevance. Closes
    access ≠ relevance: an unrealized (evidence 0) or stale (relevance → 0) dependency earns ~no budget."""
    base = cs.causal_surface_area(obj) * dep.dependency_access(obj) // 100
    evid = max(0, min(100, int(claim.evidence)))
    relevance = cc.temporal_relevance(now_tick - claim.issued_tick, coherence)
    return base * evid // 100 * relevance // 100


# --- the Dependency Fog Crucible (incomplete / false / stale dependency visibility) -----------------

def _fog_scene(seed=1, n=30, now_tick=100):
    import random
    rng = random.Random(seed)
    objs = {}
    for i in range(n):
        kind = i % 5
        hidden = (kind == 0)      # truly relevant but invisible (visibility says ignore; DSA says prepare)
        false = (kind == 1)       # claims a dependency that is never realized (evidence 0) — a budget trap
        stale = (kind == 2)       # was relevant long ago; now expired (issued far in the past)
        relevant = hidden          # only 'hidden' objects should actually be prepared this frame
        objs["o%02d" % i] = {
            "obj": {"affected_agents": 4 if (hidden or false or stale) else 1,
                    "expected_divergence": 5 if (hidden or false or stale) else 1,
                    "lighting_sensitivity": 8 if (hidden or false or stale) else 2,
                    "reconstruction_sensitivity": 7 if (hidden or false or stale) else 2,
                    "dependencies": ["material", "lighting", "destruction", "sound", "occlusion"],
                    "dependency_access": 90,
                    "visibility": 3 if hidden else rng.randint(40, 100)},
            "claim": DependencyClaim("o%02d" % i, "destruction_shader",
                                     evidence=(0 if false else 100),
                                     issued_tick=(now_tick - 500 if stale else now_tick),
                                     expiration=(now_tick - 1 if stale else now_tick + 100),
                                     consequence=5),
            "relevant": relevant,
        }
    return objs, now_tick


def _hamilton(weights, budget):
    keys = sorted(weights); tot = sum(max(0, weights[k]) for k in keys)
    if budget <= 0 or not keys:
        return {k: 0 for k in keys}
    if tot == 0:
        base, rem = divmod(budget, len(keys)); return {k: base + (1 if i < rem else 0) for i, k in enumerate(keys)}
    raw = {k: max(0, weights[k]) * budget / tot for k in keys}; fl = {k: int(raw[k]) for k in keys}
    for k in sorted(keys, key=lambda k: (-(raw[k] - fl[k]), k))[:budget - sum(fl.values())]:
        fl[k] += 1
    return fl


def fog_crucible(seed=1, budget=300):
    objs, now = _fog_scene(seed=seed)
    def cost(alloc):
        wasted = missed = 0
        for oid, rec in objs.items():
            got = alloc.get(oid, 0)
            if rec["relevant"]:
                missed += max(0, 30 - got) * cs.causal_surface_area(rec["obj"]) // 100   # starved a real need
            else:
                wasted += got                                                            # spent on a non-need
        return wasted + missed
    pol = {
        "visibility": lambda r: r["obj"]["visibility"],
        "access_naive (CSA×access)": lambda r: dep.preparation_value(r["obj"]),
        "integrity_aware": lambda r: integrity_aware_preparation_value(r["obj"], r["claim"], now),
    }
    return {name: cost(_hamilton({oid: wf(rec) for oid, rec in objs.items()}, budget)) for name, wf in pol.items()}


def demo(seed=1, budget=300):
    res = fog_crucible(seed=seed, budget=budget)
    print("Dependency Fog Crucible — incomplete / false / stale dependency visibility")
    print("  metric = wasted budget (false/stale) + missed need (hidden-relevant); lower better\n")
    for name in ("visibility", "access_naive (CSA×access)", "integrity_aware"):
        tag = "  ← × evidence × temporal relevance (access ≠ relevance closed)" if name == "integrity_aware" else ""
        print("  %-26s %d%s" % (name, res[name], tag))
    # consensus + tautology demo
    good = DependencyClaim("door", "destruction_shader", consequence=5)
    forged = DependencyClaim("door", "destruction_shader", consequence=5)
    print("\n  tautology (forgery) check: genuine=%s, tampered=%s"
          % (tautology_holds(good, good.content_hash()), tautology_holds(forged, "deadbeefdeadbeef")))
    witnesses = [DependencyClaim("door", "destruction_shader", consequence=5) for _ in range(3)]
    witnesses.append(DependencyClaim("door", "destruction_shader", consequence=999))   # one adversarial witness
    v = consensus_validate(witnesses, k=3)
    print("  consensus k=3 of 4 (1 adversarial): admitted=%s agree=%d dissent=%d (consensus ≠ truth)"
          % (v["admitted"], v["agree"], v["dissent"]))
    print("  best under fog: %s. integrity ≠ truth." % min(res, key=lambda k: res[k]))
    return res


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("dependency_integrity", OBSERVER, mutates_core=False,
                          note="Dependency Integrity Layer — content-hash tautology + exact-integer k-of-n "
                               "consensus stream validator + evidence/decay; access ≠ relevance; consensus ≠ truth")
    except LayerViolation:
        pass
