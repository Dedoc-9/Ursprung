# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/adversarial_runtime/adversarial.py — the offensive runtime: attack your own declarations.

The first runtime (provenance_runtime) RECORDS provenance. This one ATTACKS it. It is the non-entrenchment
posture: you cannot wall off the vacuum (`declared cost ≠ verified cost`), so instead of defending the
declarations you weaponize the gap, inject contradiction, kill what does not survive, and ground what you can
against an external anchor — and you keep the corpses. Four mechanisms, operating on the same Phase-R
`Artifact`:

  1. weaponize(artifact)            — turn `declared ≠ verified` into a detector: flag artifacts that assert a
                                      higher epistemic status than their evidence backs (laundering).
  2. ParadoxEngine.contradictions   — structural contradiction: declarations that cannot all hold (verified
                                      without evidence; same claim at two statuses; a provenance cycle).
  3. NecroRegistry + survives()     — adversarial survival tests: perturb (swap encoder, remove an assumption);
                                      bury what dies WITH its cause of death. A falsified artifact is preserved
                                      information, not garbage (preserve failed branches).
  4. ExternalAnchor                 — an append-only, tamper-evident commitment chain. HONEST BOUND, stated
                                      loudly: software hashing gives tamper-evident ORDERING, not physical
                                      irreversibility — a fresh chain from the same inputs reproduces, so it is
                                      `integrity = reproducibility`. A real external anchor (a verifiable delay
                                      function, proof-of-sequential-work, or an external clock) is the un-faked
                                      frontier; this records the discipline the anchor must satisfy.

Separators in play: declared ≠ verified; laundering = declared > verifiable; tamper-evident ordering ≠ physical
irreversibility; internal declaration ≠ external anchor.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os

# reuse the Phase-R Artifact (the thing being attacked)
_ap = os.path.join(os.path.dirname(__file__), "..", "provenance_runtime", "artifact.py")
_spec = importlib.util.spec_from_file_location("provenance_runtime_artifact", _ap)
_am = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_am)
Artifact = _am.Artifact

_ORDER = {"verified": 3, "survived": 2, "assumed": 1, "unknown": 0}


def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


# --- 1. weaponize the declared ≠ verified gap ---------------------------------------------------

def verifiable_status(a):
    """The highest status the artifact's EVIDENCE can back, ignoring what it declares."""
    if a.evidence["interventions"]:
        return "verified"
    if a.evidence["observations"]:
        return "survived"
    if a.provenance["declared_assumptions"]:
        return "assumed"
    return "unknown"


def weaponize(a):
    """Turn the gap into a detector. laundering = the declared status exceeds what the evidence supports."""
    declared, verifiable = a.status, verifiable_status(a)
    gap = _ORDER[declared] - _ORDER[verifiable]
    return {"declared": declared, "verifiable": verifiable, "laundering": gap > 0, "severity": max(0, gap)}


# --- 2. the Paradox Engine: structural contradiction --------------------------------------------

class ParadoxEngine:
    @staticmethod
    def contradictions(artifacts):
        out = []
        for a in artifacts:
            if a.status == "verified" and not (a.evidence["interventions"] or a.evidence["observations"]):
                out.append(("verified_without_evidence", a.kind, a.content))
            if a.status == "assumed" and not a.provenance["declared_assumptions"]:
                out.append(("assumed_without_assumption", a.kind, a.content))
        by_claim = {}
        for a in artifacts:
            by_claim.setdefault((a.kind, json.dumps(a.content, default=str)), set()).add(a.status)
        for key, statuses in by_claim.items():
            if len(statuses) > 1:
                out.append(("same_claim_contradictory_status", key[0], sorted(statuses)))
        digests = {a.digest(): a for a in artifacts}
        for a in artifacts:
            for dep in a.provenance["dependencies"]:
                if dep in digests and a.digest() in digests[dep].provenance["dependencies"]:
                    out.append(("provenance_cycle", a.kind, a.content))
        return out

    @staticmethod
    def make_paradox():
        """Construct a deliberately self-contradictory artifact (verified, but no evidence) — to test the
        detector. The Artifact base allows it (status is a label); the engine is what flags it."""
        return Artifact("Paradox", "verified-but-empty", status="verified")


# --- 3. the Necro-Registry: adversarial survival tests ------------------------------------------

def survives(a, perturbation):
    """Does the artifact's claim survive a perturbation? An intervention-grounded claim survives a change of
    representation; an assumption-backed claim dies when its assumption is removed from 𝓐 (Phase-3 logic)."""
    kind = perturbation[0]
    if kind == "remove_assumption":
        return not (a.provenance["declared_assumptions"] and perturbation[1] in a.provenance["declared_assumptions"])
    if kind == "swap_encoder":
        return bool(a.evidence["interventions"]) or a.status == "verified"
    if kind == "change_environment":
        return bool(a.evidence["interventions"])     # only intervention-grounded survives an environment shift
    return True


class NecroRegistry:
    """The graveyard of falsified artifacts — preserved, with cause of death. A dead claim is information."""
    def __init__(self):
        self.dead = []

    def run_survival(self, artifact, perturbations):
        for p in perturbations:
            if not survives(artifact, p):
                self.bury(artifact, "killed by %s" % (":".join(map(str, p)),))
                return False
        return True

    def bury(self, artifact, cause_of_death):
        self.dead.append({"kind": artifact.kind, "content": artifact.content,
                          "digest": artifact.digest(), "cause_of_death": cause_of_death})

    def epitaphs(self):
        return list(self.dead)


# --- 4. the External Anchor: irreversible (honest: tamper-evident-ordering) physical hash --------

class ExternalAnchor:
    """An append-only commitment chain. Tamper with any past entry and every later anchor breaks. It grounds
    ORDERING (you cannot backdate a commitment without rebuilding the chain) — the one thing internal
    declaration cannot supply. HONEST: software hashing is reproducible, so this is integrity/ordering, NOT
    physical irreversibility; a real anchor needs an external irreversible cost (VDF / PoW / clock)."""
    def __init__(self):
        self.chain = []

    def commit(self, digest, external_token="t"):
        prev = self.chain[-1]["anchor"] if self.chain else "GENESIS"
        anchor = _h({"prev": prev, "digest": digest, "ext": external_token})
        self.chain.append({"digest": digest, "anchor": anchor, "prev": prev})
        return anchor

    def verify(self):
        prev = "GENESIS"
        for e in self.chain:
            if _h({"prev": prev, "digest": e["digest"], "ext": "t"}) != e["anchor"]:
                return False
            prev = e["anchor"]
        return True

    def precedes(self, digest_a, digest_b):
        idx = {e["digest"]: i for i, e in enumerate(self.chain)}
        return digest_a in idx and digest_b in idx and idx[digest_a] < idx[digest_b]
