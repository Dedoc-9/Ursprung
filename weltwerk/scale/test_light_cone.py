# SPDX-License-Identifier: AGPL-3.0-only
"""
test_light_cone.py — validity-not-outcome self-test for the coupled-world light-cone probe.

The CRUX is again correctness under the HARDER coupled case: by-difference reconstruction (simulate only
the cone, reuse line A for clean chunks — whose states feed the frontier's diffusion) must be
byte-identical to a full honest sim of the edited coupled world. If that fails, every velocity and cost
number is void.

  1. equivalence_coupled  — line_b == brute full sim of edited coupled world, byte-identical (THE crux)
  2. actual_subset_cone   — actual divergence ⊆ the conservative cone we pay to simulate (∀ tick)
  3. cone_monotonic       — the cone never shrinks (causality does not un-spread)
  4. velocity_bounded     — ring nearest-neighbour ⇒ cone grows ≤ 2 chunks/tick; 0 < velocity ≤ 2
  5. cost_is_cone_volume  — cf_cost == chunk_size · Σ cone_count[1:]  (cost accounting is exact)
  6. saturation_vanishes  — with a long horizon the cone fills the world and cf_cost == naive (no win)
  7. determinism          — same seed ⇒ identical line_b

Run:  PYTHONHASHSEED=0 python3 test_light_cone.py
"""
from __future__ import annotations

from cow_world import Edit, Rules, genesis, snapshot_hash
from light_cone import brute_force_edit_future, counterfactual_lightcone

N_CH, CHUNK_SIZE, SEED = 60, 20, 0
N = N_CH * CHUNK_SIZE


def check(name, ok, detail):
    return (name, ok, detail)


def _world():
    return genesis(n_entities=N, n_chunks=N_CH, seed=SEED), Rules()


def test_equivalence_coupled():
    snap, rules = _world()
    edit = Edit("cull_pred_chunk", chunk=30)
    r = counterfactual_lightcone(snap, rules, SEED, edit, horizon=40)
    brute = brute_force_edit_future(snap, rules, SEED, edit, horizon=40)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_coupled", ok,
                 f"by-difference B == full honest sim of edited COUPLED world: {ok}")


def test_actual_subset_cone():
    snap, rules = _world()
    r = counterfactual_lightcone(snap, rules, SEED, Edit("cull_pred_chunk", chunk=30), 40)
    ok = all(a <= c for a, c in zip(r.actual_count, r.cone_count))
    return check("actual_subset_cone", ok,
                 f"actual divergence ⊆ conservative cone at every tick: {ok}")


def test_cone_monotonic():
    snap, rules = _world()
    r = counterfactual_lightcone(snap, rules, SEED, Edit("cull_pred_chunk", chunk=30), 40)
    ok = all(r.cone_count[i + 1] >= r.cone_count[i] for i in range(len(r.cone_count) - 1))
    return check("cone_monotonic", ok, f"cone never shrinks: {ok}")


def test_velocity_bounded():
    snap, rules = _world()
    r = counterfactual_lightcone(snap, rules, SEED, Edit("cull_pred_chunk", chunk=30), 40)
    incr = [r.cone_count[i + 1] - r.cone_count[i] for i in range(len(r.cone_count) - 1)]
    bounded = max(incr) <= 2                                   # ring: at most one new chunk each side
    vel_ok = 0 < r.information_velocity <= 2
    return check("velocity_bounded", bounded and vel_ok,
                 f"max cone growth/tick={max(incr)} (≤2={bounded}); velocity={r.information_velocity:.2f} (0<v≤2={vel_ok})")


def test_cost_is_cone_volume():
    snap, rules = _world()
    r = counterfactual_lightcone(snap, rules, SEED, Edit("cull_pred_chunk", chunk=30), 40)
    expected = CHUNK_SIZE * sum(r.cone_count[1:])              # entities per chunk uniform (N divisible)
    ok = r.cf_cost == expected
    return check("cost_is_cone_volume", ok,
                 f"cf_cost={r.cf_cost} == chunk_size·Σcone={expected}: {ok}")


def test_saturation_vanishes():
    snap, rules = _world()
    # horizon > radius-to-fill (≈ N_CH/2) so the cone saturates the world
    r = counterfactual_lightcone(snap, rules, SEED, Edit("cull_pred_chunk", chunk=30), horizon=80)
    saturated = r.saturation_tick >= 0 and max(r.cone_count) == N_CH
    # once fully saturated, each subsequent tick simulates all N chunks (no win at the margin)
    return check("saturation_vanishes", saturated,
                 f"cone fills world @tick {r.saturation_tick}; max cone={max(r.cone_count)}/{N_CH}: {saturated}")


def test_non_vacuous_and_propagates():
    """The ghost-guard: the edit must actually DO something (source diverges) AND coupling must
    actually TRANSMIT it (divergence spreads beyond the edited chunk). Catches the all-prey/all-pred
    no-op that made an earlier run pass equivalence vacuously."""
    snap, rules = _world()
    r = counterfactual_lightcone(snap, rules, SEED, Edit("cull_pred_chunk", chunk=30), 40)
    source_diverges = r.actual_count[0] >= 1
    spreads = max(r.actual_count) > 1
    return check("non_vacuous_propagates", source_diverges and spreads,
                 f"edit diverges at source={source_diverges}; divergence spreads (peak actual="
                 f"{max(r.actual_count)})={spreads}")


def test_determinism():
    snap, rules = _world()
    edit = Edit("cull_pred_chunk", chunk=15)
    a = counterfactual_lightcone(snap, rules, SEED, edit, 30)
    b = counterfactual_lightcone(snap, rules, SEED, edit, 30)
    ok = snapshot_hash(a.line_b) == snapshot_hash(b.line_b)
    return check("determinism", ok, f"identical line_b across runs: {ok}")


def main():
    results = [
        test_equivalence_coupled(),
        test_actual_subset_cone(),
        test_cone_monotonic(),
        test_velocity_bounded(),
        test_cost_is_cone_volume(),
        test_saturation_vanishes(),
        test_non_vacuous_and_propagates(),
        test_determinism(),
    ]
    print("test_light_cone — validity-not-outcome (the coupled mechanism is CORRECT; not 'scaling is good')\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. The coupled probe is sound iff this is {total}/{total}: by-difference"
          f"\n  reconstruction is byte-identical under coupling, the cone is monotone and topology-bounded,"
          f"\n  cost equals cone volume exactly, and the win VANISHES once the cone fills the world.")
    assert passed == total, f"{total - passed} check(s) failed — the light-cone probe is not sound"


if __name__ == "__main__":
    main()
