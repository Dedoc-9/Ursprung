<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Adversarial Runtime — attack the declarations, keep the corpses

The first runtime (`provenance_runtime`) **records** provenance. This one **attacks** it. It is the
non-entrenchment posture: you cannot wall off the vacuum (`declared cost ≠ verified cost`), so instead of
defending the declarations you turn the gap into a weapon, inject contradiction, kill what does not survive, and
ground what you can against an external anchor — and you preserve the dead. It operates on the same Phase-R
`Artifact`.

## Run

```bash
python3 experiments/adversarial_runtime/run.py     # stdlib only; deterministic
```

## The four mechanisms

1. **Weaponize `declared ≠ verified`.** `weaponize(artifact)` computes the highest status the *evidence* can
   back (`verifiable_status`) and flags **laundering** when the declared status exceeds it. A `CausalEdge`
   declared `verified` with no interventions is caught — it asserts more than it can show.
2. **The Paradox Engine — structural contradiction.** `contradictions()` finds declarations that cannot all
   hold: *verified without evidence*, *assumed without an assumption*, *the same claim asserted at two
   contradictory statuses*, a *provenance cycle*. `make_paradox()` builds one on purpose to test the detector.
3. **The Necro-Registry — adversarial survival tests.** `survives(artifact, perturbation)` perturbs the world
   (swap encoder, remove an assumption from `𝓐`, change environment). An intervention-grounded claim survives a
   change of representation/environment; an assumption-backed claim **dies** when its assumption is removed. The
   dead are *buried with a cause of death* and preserved — a falsified artifact is information, not garbage.
4. **The External Anchor.** An append-only, tamper-evident commitment chain: tamper with any past entry and
   every later anchor breaks, so a commitment cannot be backdated without rebuilding the chain. It grounds
   **ordering** — the one thing internal declaration cannot supply.

## Verified (10 checks)

```
weaponize catches laundering; verifiable_status ignores the declaration
paradox: verified-without-evidence; same-claim-contradictory-status
necro: intervention edge survives perturbation; assumption edge dies when its 𝓐 is removed; the dead are kept with cause
anchor: proves ordering; is tamper-evident; AND is reproducible — therefore NOT physically irreversible
```

## Honest bounds (loud, because this is where software overclaims)

The External Anchor is **tamper-evident ordering, not physical irreversibility.** A fresh chain built from the
same inputs reproduces the same anchors — so it is `integrity = reproducibility`, exactly the separator the
project has held since M1. A *real* external anchor needs an irreversible external cost — a verifiable delay
function, proof-of-sequential-work, or an external clock — and that is the un-faked frontier; this records the
discipline such an anchor must satisfy, it does not manufacture the irreversibility in software.

The runtime as a whole only ever does what the discipline allows: it **detects** laundering and contradiction,
it **records** what died and why, and it **anchors ordering** — none of which closes the vacuum. It refuses to
entrench against the hole; it marks every declaration's relation to it. `declared ≠ verified`;
`tamper-evident ordering ≠ physical irreversibility`; `internal declaration ≠ external anchor`.
