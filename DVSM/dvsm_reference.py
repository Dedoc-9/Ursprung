# SPDX-License-Identifier: AGPL-3.0-only
"""
dvsm_reference.py — a REDUCED, deterministic Python reference of the DVSM-π+++ recurrence, built to give
the weltwerk auditors planted traces to validate the audit PROCEDURE on. It is NOT the authoritative kernel.

  reference-model ≠ authoritative-kernel : the shipped DVSM core is Rust, no_std, fixed-point (Q16/Q31/Q64)
  with a Stiefel basis W and an FNV-1a replay hash. This reference is f64, scalar-summarised, and models only
  the channels the forbidden-coupling audit needs. It reproduces the kernel's *structure* (Lie bracket + EMA
  memory + Z→Ω drift + read-only diagnostics + containment), not its bit-exact trajectory. Anything graded
  here is a property of THIS reference (or of the procedure run on it), never of the executed Rust kernel.
  `proves-the-procedure ≠ proves-the-phenomenon`.

Faithful core (from dvsm_one_file.rs / NO_LIE_DEGEN_ULTRA_TELEM.rs):
    Ż_k = Σ_j (Z_k S_j − Z_j S_k) κ_{kj} − λ Z_k          (Lie evolution, λ = const dissipation)
    S   = α S + (1−α) Z                                     (EMA memory; makes [Z,S] ≠ 0)
    Ω   = (Ω + Z α dt) · decay                              (drift witness: Z → Ω only, NO backfeed)
    V   = V γ + drive η                                     (velocity → output; driven by residual, NOT Ω)
    κ_{kj} = sin(k·1.37 − j·1.73)                           (THE ACTUAL init — see the skew-symmetry GHOST)

GHOST (recorded, not hidden): the kernel comment asserts κ is "guaranteed κ[i,j] = −κ[j,i]", but
sin(i·1.37 − j·1.73) is NOT skew-symmetric (it would require 1.37 = 1.73). The energy law d‖Z‖²/dt = −2λ‖Z‖²
leans on that skew-symmetry. `invariant_ledger.py` measures the residual ‖κ+κᵀ‖ and grades it. We keep the
real formula here so the auditor catches the real discrepancy — `claimed-skew ≠ actual-skew`.

The forbidden feedback couplings the manifest names (NO Ω→V, NO ν→λ, NO Stiffness→Dynamics, NO Trace→W) are
enforced here by construction in the CLEAN trace and can be PLANTED back in via `contaminate=` so the
firewall has a known-positive to separate from the known-negative.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

R = 4                    # active modes (reduced; kernel uses up to RMAX=16)
DT = 1.0 / 240.0
LAMBDA0 = 0.05
ALPHA = 0.98
ETA = 0.5
V_DAMP = 0.95
OMEGA_DECAY = 0.999
U_MAX = 100.0           # containment bound on ‖Z‖
KILL_K = 3              # hysteresis: consecutive over-bound frames before a GhostSnap kill


def kappa_matrix(r: int = R) -> List[List[float]]:
    """κ_{kj} = sin(k·1.37 − j·1.73) — the kernel's ACTUAL init (deliberately NOT antisymmetrised)."""
    return [[math.sin(k * 1.37 - j * 1.73) for j in range(r)] for k in range(r)]


def fnv1a(values: Tuple[int, ...]) -> int:
    """Deterministic FNV-1a over quantised state — a portable replay hash (integrity, NOT correctness)."""
    h = 0xCBF29CE484222325
    for v in values:
        h ^= (v & 0xFFFFFFFFFFFFFFFF)
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


@dataclass(frozen=True)
class StepRecord:
    """Scalar per-step channels. `drive`/`z`/`s` are LEGITIMATE; `omega`/`novelty`/`stiffness` are
    DIAGNOSTIC (read-only by contract); `v`/`z_next`/`lambda_eff` are DYNAMICS the diagnostics must not feed."""
    t: int
    drive: float                  # legitimate exogenous driver (stands for residual/input)
    z0: float                     # fast field, mode 0
    z_energy: float               # ‖Z‖
    s0: float                     # EMA memory, mode 0
    omega0: float                 # Ω drift, mode 0  (DIAGNOSTIC witness)
    omega_norm: float             # ‖Ω‖             (DIAGNOSTIC witness)
    novelty: float                # |drive| proxy    (DIAGNOSTIC)
    stiffness: float              # shadow-probe response (DIAGNOSTIC, read-only)
    lambda_eff: float             # dissipation actually used this step (should be constant)
    v0: float                     # velocity mode 0 → output (DYNAMICS)
    z0_next: float                # next-step z0 (DYNAMICS target)
    v0_next: float                # next-step v0 (DYNAMICS target)
    energy: float
    stress: float
    entropy: float
    ghost: str
    contained: int
    hash: int


_GHOSTS = ("Nominal", "Collapse", "Diffuse", "Echo", "Burst", "Trap", "Vacuum")


class DvsmReference:
    """A reduced reference recurrence. Deterministic given `seed`. `contaminate` plants forbidden couplings:
      'omega_to_v'        : V += c·Ω           (violates NO Ω→V)
      'novelty_to_lambda' : λ = λ0 + c·ν        (violates NO ν→λ)
      'stiffness_to_z'    : Z += c·stiffness    (violates NO Stiffness→Dynamics)
    Multiple may be set at once. Strength via `strength`."""

    def __init__(self, seed: int = 0, r: int = R, contaminate: Optional[Dict[str, bool]] = None,
                 strength: float = 0.8):
        self.r = r
        self.rng = random.Random(seed)
        self.kappa = kappa_matrix(r)
        self.contaminate = contaminate or {}
        self.c = strength
        self.z = [0.01 * (k + 1) for k in range(r)]
        self.s = [0.0] * r
        self.omega = [0.0] * r
        self.v = [0.0] * r
        self.contain_fails = 0

    # ---- helpers ------------------------------------------------------------------------------
    def _norm(self, a: List[float]) -> float:
        return math.sqrt(sum(x * x for x in a))

    def _entropy(self) -> float:
        tot = sum(x * x for x in self.z) + 1e-15
        h = 0.0
        for x in self.z:
            p = (x * x) / tot
            if p > 1e-15:
                h -= p * math.log2(p)
        return h

    def _stiffness(self) -> float:
        """Read-only shadow probe: perturb a COPY of z, measure ‖Z‖² sensitivity. Never mutates state."""
        eps = 1e-3
        shadow = list(self.z)
        shadow[0] += eps
        e0 = sum(x * x for x in self.z)
        e1 = sum(x * x for x in shadow)
        return abs(e1 - e0) / eps

    # ---- one step -----------------------------------------------------------------------------
    def step(self, t: int) -> StepRecord:
        r = self.r
        drive = self.rng.gauss(0.0, 1.0)
        novelty = abs(drive)
        stiffness = self._stiffness()

        # λ — constant by contract; ν→λ contamination breaks ∂λ/∂ν = 0
        lam = LAMBDA0
        if self.contaminate.get("novelty_to_lambda"):
            lam = LAMBDA0 + self.c * 0.05 * novelty

        # 1. containment (hysteresis) — a GhostSnap kill if ‖Z‖ exceeds the bound KILL_K frames running
        e2 = sum(x * x for x in self.z)
        if e2 > U_MAX * U_MAX or e2 != e2:
            self.contain_fails += 1
        else:
            self.contain_fails = 0
        killed = self.contain_fails >= KILL_K
        if killed:
            self.z = [1e-6] * r
            self.s = [0.0] * r
            self.omega = [0.0] * r
            self.contain_fails = 0

        # 2. Lie evolution Z_k += dt·(Σ_j (Z_k S_j − Z_j S_k) κ_kj − λ Z_k)
        z_next = [0.0] * r
        for k in range(r):
            torque = 0.0
            for j in range(r):
                if j != k:
                    torque += (self.z[k] * self.s[j] - self.z[j] * self.s[k]) * self.kappa[k][j]
            zk = self.z[k] + DT * (torque - lam * self.z[k])
            # legitimate drive injection into the field (mode 0 only)
            if k == 0:
                zk += DT * ETA * drive
            # CONTAMINATION: Stiffness → Dynamics (forbidden)
            if self.contaminate.get("stiffness_to_z") and k == 0:
                zk += DT * self.c * 0.1 * stiffness
            z_next[k] = zk

        # 3. velocity (output) — legit driver is `drive`; Ω→V contamination is forbidden
        v_next = [0.0] * r
        for k in range(r):
            nv = self.v[k] * V_DAMP + (drive if k == 0 else 0.0) * ETA
            if self.contaminate.get("omega_to_v") and k == 0:
                nv += self.c * self.omega[k]          # forbidden Ω → V
            v_next[k] = max(-U_MAX, min(U_MAX, nv))

        # snapshot pre-commit diagnostics
        z0, s0, omega0 = self.z[0], self.s[0], self.omega[0]
        v0 = self.v[0]
        omega_norm = self._norm(self.omega)
        energy = self._norm(self.z)
        s_n = self._norm(self.s)
        stress = s_n / max(energy, 1e-15)
        entropy = self._entropy()
        if killed:
            ghost = "Vacuum"
        elif stress > 1.5:
            ghost = "Burst"
        elif energy < 1e-9 and entropy < 0.1:
            ghost = "Collapse"
        elif entropy > 1.5:
            ghost = "Diffuse"
        elif entropy < 0.3 and stress < 0.1:
            ghost = "Echo"
        elif omega_norm / max(energy, 1e-15) > 1.0:
            ghost = "Trap"
        else:
            ghost = "Nominal"
        qhash = fnv1a(tuple(int(x * 65536) & 0xFFFFFFFF for x in self.z + self.s))

        # 4. commit: EMA memory, Ω drift (Z→Ω only), state advance
        self.z = z_next
        if self.contain_fails == 0 and not killed:
            self.s = [ALPHA * self.s[k] + (1 - ALPHA) * self.z[k] for k in range(r)]
        self.omega = [(self.omega[k] + self.z[k] * ALPHA * DT) * OMEGA_DECAY for k in range(r)]
        self.v = v_next

        return StepRecord(
            t=t, drive=drive, z0=z0, z_energy=energy, s0=s0, omega0=omega0, omega_norm=omega_norm,
            novelty=novelty, stiffness=stiffness, lambda_eff=lam, v0=v0, z0_next=self.z[0],
            v0_next=self.v[0], energy=energy, stress=stress, entropy=entropy, ghost=ghost,
            contained=int(killed), hash=qhash,
        )

    def run(self, n: int) -> List[StepRecord]:
        return [self.step(t) for t in range(n)]


# ---- planted trace generators (the audit's known-negative / known-positive) ----------------------
def gen_clean(n: int = 6000, seed: int = 1) -> List[StepRecord]:
    """Air-gap held: every diagnostic is read-only; no forbidden coupling. The audit should find NONE."""
    return DvsmReference(seed=seed).run(n)


def gen_contaminated(channel: str, n: int = 6000, seed: int = 2, strength: float = 0.8) -> List[StepRecord]:
    """One forbidden coupling planted (e.g. 'omega_to_v'). The audit should find exactly that contamination."""
    return DvsmReference(seed=seed, contaminate={channel: True}, strength=strength).run(n)


def main():
    print("dvsm_reference.py — reduced Python reference (reference-model ≠ authoritative-kernel)\n")
    k = kappa_matrix()
    skew = max(abs(k[i][j] + k[j][i]) for i in range(R) for j in range(R))
    print(f"  κ skew-symmetry residual max|κ+κᵀ| = {skew:.4f}  (0 ⇒ skew-symmetric; >0 ⇒ the GHOST)")
    clean = gen_clean(2000)
    en = [r.energy for r in clean]
    print(f"  clean run: {len(clean)} frames, ‖Z‖ in [{min(en):.3f}, {max(en):.3f}] (bounded < U_MAX={U_MAX})")
    print(f"  ghosts seen: {sorted(set(r.ghost for r in clean))}")
    print("  use: coupling_audit.audit_coupling(trace, ...) — a CHANNEL verdict = observer contamination.")


if __name__ == "__main__":
    main()
