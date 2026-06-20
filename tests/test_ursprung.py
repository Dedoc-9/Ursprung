# SPDX-License-Identifier: AGPL-3.0-only
"""
tests/test_ursprung.py — milestone-1 unit tests (stdlib asserts, no pytest needed).

Run:  PYTHONHASHSEED=0 python3 tests/test_ursprung.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ursprung import world_core as core
from ursprung import view_layer as view
from ursprung import ghost_report as gr
from ursprung import verify
from ursprung import render_record as rr
from ursprung import conventions as conv
from ursprung import divergence as dv
from ursprung import prediction as pred
from ursprung import temporal_membrane as tm
from ursprung import pfal_bench as pf
from ursprung import tcff
from ursprung import polygon_reconciliation as poly
from ursprung import fidelity_conservation as fc
from ursprung import reality_debt as rd
from ursprung import causal_continuity as cc
from ursprung import raster
from ursprung import raster_bench as rb
from ursprung import representation as rep
from ursprung import allocation as al
from ursprung import perceptual as pc
from ursprung import policy_arena as arena
from ursprung import stress
from ursprung import transition_debt as td
from ursprung import adversarial_scenes as adv
from ursprung import resistance_tensor as rt
from ursprung import shader_cache as sc
from ursprung import causal_surface as cs
from ursprung import readiness as rdy
from ursprung import causal_contract as ccon
from ursprung import representation_futures as rf
from ursprung import causal_mutation as cm
from ursprung import provider_contract as pcon
from ursprung import dependency_surface as dep
from ursprung import dependency_integrity as di
from ursprung import representation_compiler as rc
from ursprung import capability as cap
from ursprung import causal_access as cac
from ursprung import reconstruction as rec
from ursprung import side_channel as sch
from ursprung import accumulation as acc
from ursprung import adversarial_dynamics as ad
from ursprung import representation_privacy as rp
from ursprung import execution_surface as es
from ursprung import convergence as cv
from ursprung import reality_harness as rh
from ursprung import behavioral_harness as bh
from ursprung import adversary_harness as ah
from ursprung import adversary_capacity as ac
from ursprung import channel_discovery as cd
from ursprung import disclosure as disc
from ursprung import perception as perc
from ursprung.registry import Registry, LayerViolation, CORE, VIEW, ALLOCATOR, OBSERVER

_n = 0


def check(cond, msg):
    global _n
    assert cond, "FAIL: " + msg
    _n += 1


# --- CORE -------------------------------------------------------------------------------------------

def test_core_determinism():
    h1 = core.trajectory(core.demo_world(), 50)
    h2 = core.trajectory(core.demo_world(), 50)
    check(core.trajectories_identical(h1, h2), "identical worlds must replay byte-identical")
    check(core.first_divergence(h1, h2) is None, "no divergence expected")


def test_core_tick_is_pure():
    w = core.demo_world()
    h_before = core.state_hash(w)
    _ = core.tick(w)                      # tick returns a NEW world
    check(core.state_hash(w) == h_before, "tick() must not mutate its input world")


def test_core_divergence_locator():
    a = core.trajectory(core.demo_world(), 30)
    b = a[:]
    b[10] = "deadbeef"
    check(core.first_divergence(a, b) == 10, "divergence locator must find the first differing tick")


# --- VIEW -------------------------------------------------------------------------------------------

def test_view_is_read_only():
    w = core.demo_world()
    w = core.tick(w)
    h = core.state_hash(w)
    snap = view.snapshot(w)
    frame = view.interpret(snap)
    # mutate the snapshot AND the frame as hard as we can
    snap["bodies"][0]["pos"][0] = 999999999
    view.perturb(frame)
    check(core.state_hash(w) == h, "mutating snapshot/frame must not change committed world state")


def test_view_observable_drift_is_benign():
    w = core.tick(core.demo_world())
    snap = view.snapshot(w)
    fa = view.interpret(snap, client_seed=1)
    fb = view.interpret(snap, client_seed=999)
    check(view.frames_agree_on_truth(fa, fb), "different clients must agree on the committed l1_hash")


def test_view_carries_truth_binding():
    w = core.tick(core.demo_world())
    snap = view.snapshot(w)
    frame = view.interpret(snap)
    check(frame.l1_hash == snap["l1_hash"] == core.state_hash(w),
          "a frame must bind to the committed state it was derived from")


# --- registry (the layer law) -----------------------------------------------------------------------

def test_registry_enforces_layer_law():
    r = Registry()
    r.register("w", CORE, mutates_core=True)
    r.register("v", VIEW, mutates_core=False)
    for layer in (VIEW, ALLOCATOR, OBSERVER):
        try:
            r.register("bad_" + layer, layer, mutates_core=True)
            check(False, "non-CORE claiming mutates_core must be rejected")
        except LayerViolation:
            check(True, "layer law rejected non-CORE mutation claim")
    check(len(r.authoritative_systems()) == 1, "only the CORE system may be authoritative")


# --- OBSERVER / ghosts ------------------------------------------------------------------------------

def test_no_float_leak_or_order_dependence():
    w = core.demo_world()
    check(gr.detect_float_leak(w) is None, "committed state must be integer-only (no float leak)")
    check(gr.detect_hidden_nondeterminism(lambda: core.demo_world()) is None,
          "repeated identical runs must not diverge")


def test_ghost_reconstruction_is_perceptual_approximation():
    # a camera placed so something falls off-screen should yield a PERCEPTUAL/approximation ghost, not error
    w = core.tick(core.demo_world())
    frame = view.interpret(view.snapshot(w), view.Camera(eye=(0.0, 0.0, 2.0), focal=5.0, screen=(16, 16)))
    g = gr.detect_view_reconstruction_loss(frame)
    if g is not None:
        check(g.category == gr.PERCEPTUAL and g.origin == gr.APPROXIMATION,
              "reconstruction loss is perceptual approximation, not error")
    else:
        check(True, "no reconstruction loss in this framing (acceptable)")


# --- the cardinal invariant -------------------------------------------------------------------------

def test_milestone_renderer_is_observer_only():
    res = verify.run_milestone_1(verbose=False)
    check(res.checks["replay_identity"], "replay identity must hold")
    check(res.checks["view_perturbation_invariance"],
          "CORE trajectory must be byte-identical with VIEW active+corrupted")
    check(res.checks["ordering_invariance"], "input ordering must not change the trajectory")
    check(res.passed(), "milestone 1 must pass overall")


# --- render verification record (experiments, not invasions) ----------------------------------------

def test_render_record_admits_observer_only_feature():
    def feat(snap, cfg):
        return view.interpret(snap, view.Camera(), client_seed=cfg.get("seed", 0))
    rec = rr.evaluate_feature("view_interpret", VIEW, feat, config={"seed": 3}, ticks=20,
                              measured={"hardware": "test", "resolution": "320x200", "scene": "demo"})
    check(rec.core_trajectory_changed is False, "an observer-only VIEW feature must not change CORE")
    check(rec.admissible(), "observer-only VIEW feature must be admissible")
    check(len(rec.output_artifact_hash) == 64, "record carries a SHA-256 of the output artifact")
    check("frame_budget_ms" in rec.measured, "record measures a frame budget (observable)")


def test_render_record_rejects_authority_leak():
    rec = rr.RenderVerificationRecord("bad_feature", VIEW, "a" * 64, "b" * 64, "c" * 64,
                                      core_trajectory_changed=True, view_divergence="unexpected",
                                      measured={}, known_ghosts=[])
    check(not rec.admissible(), "a non-CORE feature that changed the CORE trajectory must be REJECTED")


def test_render_record_hash_is_deterministic():
    def feat(snap, cfg):
        return view.interpret(snap, view.Camera(), client_seed=cfg.get("seed", 0))
    a = rr.evaluate_feature("f", VIEW, feat, config={"seed": 1}, ticks=15)
    b = rr.evaluate_feature("f", VIEW, feat, config={"seed": 1}, ticks=15)
    check(a.output_artifact_hash == b.output_artifact_hash, "identical experiment must hash identically")
    check(a.renderer_config_hash == b.renderer_config_hash, "config hash must be stable")


# --- the Arbitrary-Boundary Law (conventions as data) -----------------------------------------------

def test_conventions_are_deterministic_and_not_truth():
    L = conv.default_ledger()
    check(L.digest() == conv.default_ledger().digest(), "the convention set must have a stable content id")
    for c in L.all():
        check(c.not_a_truth_claim is True, "a convention must never be a truth claim")
        check(c.hash() == L.get(c.name).hash(), "a convention's identity is its content hash")
    check(len(L.by_domain(conv.RASTERIZATION)) >= 1, "rasterization boundary choice is declared")


def test_convention_rule_change_changes_identity():
    L = conv.ConventionLedger()
    a = L.declare("x", conv.LOD, rule="bands at 10/50/200")
    h1 = a.hash()
    b = conv.ConventionLedger().declare("x", conv.LOD, rule="bands at 10/40/200")  # different rule
    check(h1 != b.hash(), "changing the chosen rule must change the convention's identity (a version bump)")


def test_boundary_ghost_is_not_an_error():
    c = conv.default_ledger().get("pixel_coverage")
    g = conv.boundary_ghost(c, "edge seam between two triangles", magnitude=3)
    check(g.origin == conv.BOUNDARY_CHOICE, "a boundary footprint has origin boundary_choice, not error")
    check(g.category == gr.SPATIAL, "rasterization boundary maps to a spatial ghost category")


# --- conventions enrichment (Boundary Ledger) -------------------------------------------------------

def test_convention_explains_by_convention_not_reality():
    pc = conv.default_ledger().get("pixel_coverage")
    check(pc.truth_claim is False, "a convention is never a truth claim")
    check(bool(pc.purpose and pc.selected_reason and pc.deterministic_rule), "Boundary Ledger fields present")
    exp = pc.explain("this pixel", "this triangle")
    check("convention" in exp and "not a claim about reality" in exp,
          "explain() answers by convention, never by reality")


# --- divergence classes -----------------------------------------------------------------------------

def test_divergence_three_classes():
    check(dv.classify(True, layer="VIEW").kind == dv.WORLD and not dv.classify(True, layer="VIEW").valid,
          "CORE change from a VIEW system is an invalid WORLD divergence")
    check(dv.classify(False, representation_changed=True).kind == dv.REPRESENTATION, "same CORE, diff lens")
    check(dv.classify(False, False, observation_changed=True).kind == dv.OBSERVATION, "diff measured behavior")
    check(dv.classify_artifact_source("boundary_convention")["is_bug"] is False, "convention artifact not a bug")
    check(dv.classify_artifact_source("implementation_error")["is_bug"] is True, "impl error is a bug")


# --- Dini-style prediction observer -----------------------------------------------------------------

def test_prediction_surprise_feeds_attention_not_importance():
    w = core.demo_world()
    frames = []
    for _ in range(30):
        frames.append(view.interpret(view.snapshot(w)))
        w = core.tick(w)
    peak = 0.0
    for i in range(2, len(frames)):
        rep = pred.observe(frames[i - 2], frames[i - 1], frames[i])
        peak = max([peak] + list(rep.attention_hint.values()))
    check(peak > 0.0, "a non-linear motion (collision) must surprise the predictor somewhere")
    rep = pred.observe(frames[3], frames[4], frames[5])
    check("nothing about importance" in rep.note, "prediction is an attention hint, never importance")


# --- temporal membrane + PFAL bench -----------------------------------------------------------------

def test_membrane_budget_is_exact_and_lawful():
    for kind in (tm.TEMPORAL, tm.SPATIAL, tm.NUMERICAL, tm.CAUSAL):
        info = tm.classify_render_ghost(kind)
        check(bool(info["response"] and info["never"]), "ghost class %s maps to response + forbidden" % kind)
    budget = tm.TemporalRealityBudget().allocate(
        {"a": {"uncertainty": 3.0, "consequence": 5}, "b": {"uncertainty": 0.1, "consequence": 1}}, 100)
    check(sum(budget.values()) == 100, "Temporal Reality Budget is exact (sums to budget)")
    check(budget["a"] > budget["b"], "higher uncertainty×consequence earns more budget")


def test_pfal_beats_distance_and_control_falsifies():
    res = pf.run(seed=1, budget=600)
    check(res["pfal (U×C×P×S)"] > res["distance_visibility"],
          "PFAL covers more failure-cost than distance/visibility at equal budget")
    check(res["drifted_pfal (control)"] < res["uniform"],
          "negative control must lose to the uniform floor (the bench can falsify)")


# --- TCFF (temporal proximity τ) + PCJ ---------------------------------------------------------------

def test_tau_is_proactive():
    check(tcff.temporal_proximity(1) > tcff.temporal_proximity(8), "an imminent event has higher τ")
    check(tcff.temporal_proximity(None) == 1, "no predicted event ⇒ τ = 1")
    soon = {"uncertainty": 2.0, "consequence": 5, "persistence": 3, "sensitivity": 4, "frames_to_event": 1}
    late = dict(soon); late["frames_to_event"] = 10
    check(tcff.tcff_score(soon) > tcff.tcff_score(late), "τ makes the imminent region score higher")


def test_pcj_tcff_beats_reactive_and_control_does_not_win():
    res = tcff.run(seed=1, budget=600)
    check(res["tcff (U×C×P×S×τ)"]["pcj"] > res["reactive (visibility)"]["pcj"],
          "TCFF achieves higher Perceptual Continuity per Joule than a reactive visibility budget")
    check(res["tcff (U×C×P×S×τ)"]["pcj"] >= res["pfal (U×C×P×S)"]["pcj"],
          "τ (proactive) does at least as well as τ-blind PFAL on PCJ")
    check(res["drifted (control)"]["pcj"] <= res["tcff (U×C×P×S×τ)"]["pcj"],
          "the negative control must not beat TCFF")


# --- Polygon Reconciliation Law ---------------------------------------------------------------------

def test_polygon_reconciliation_is_cost_based_not_truth():
    check(poly.reconcile(100, 10)["keep_polygons"] is True,
          "keep polygons when abandoning them costs more than their approximation error")
    check(poly.reconcile(5, 50)["keep_polygons"] is False,
          "a replacement may be justified only when approximation error exceeds abandonment cost")
    check(poly.reconcile(10, 10)["keep_polygons"] is True, "a tie keeps polygons (>=)")
    check(poly.reconcile(1, 1)["truth_claim"] is False, "reconciliation is a cost choice, never a truth claim")
    check(abs(poly.FRAME_BUDGET_MS - 4.13) < 1e-9, "the 4.13 ms reconciliation budget is recorded")
    L = poly.RECONCILED_LEDGER
    ps = L.get("polygon_substrate")
    check(ps.truth_claim is False and len(ps.alternatives_rejected) >= 5,
          "polygon_substrate records rejected replacements and is not a truth claim")


# --- Temporal Fidelity Conservation Law -------------------------------------------------------------

def test_fidelity_is_conserved_and_transfer_is_zero_sum():
    a = {"x": 300, "y": 300}
    check(fc.is_conserved(a, 600) and not fc.is_conserved(a, 500), "conservation means Σ allocation == budget")
    b = fc.transfer(a, "x", "y", 100)
    check(fc.total(b) == 600 and b["x"] == 200 and b["y"] == 400, "a transfer is zero-sum")
    try:
        fc.transfer(a, "x", "y", 9999)
        check(False, "an over-draw transfer must fail closed")
    except fc.ConservationError:
        check(True, "cannot transfer fidelity you do not have")


def test_objective_swap_min_discontinuity_beats_max_detail():
    regions, a_local, a_mind = fc.demo(budget=600)
    check(fc.is_conserved(a_local, 600) and fc.is_conserved(a_mind, 600), "both objectives conserve the budget")
    check(fc.consequential_discontinuity(regions, a_mind) < fc.consequential_discontinuity(regions, a_local),
          "minimizing consequential discontinuity beats maximizing local detail at equal budget")


# --- Reality Debt Law -------------------------------------------------------------------------------

def test_debt_is_product_and_borrow_vs_genuine():
    check(rd.debt(8, 3, 10) == 240, "Debt = Approximation × Persistence × Consequence")
    check(rd.debt(0, 5, 9) == 0, "a zero-approximation (genuine) optimization incurs no debt")
    check(rd.DebtRecord("x", 5, 4, 10, borrowed=False).debt == 0, "a genuine cost reduction incurs no debt")
    check(rd.DebtRecord("y", 5, 4, 10, borrowed=True).debt == 200, "a borrowing optimization incurs debt")


def test_debt_placement_and_repayment_follow_consequence():
    order = rd.recommend_debt_placement({"sky": 1, "enemy": 10, "crosshair": 9, "far": 2})
    check(order[0] == "sky" and order[-1] == "enemy", "debt accumulates where future consequence is lowest")
    lawful, naive = rd.demo()
    check(lawful.total_debt() < naive.total_debt(),
          "placing the same approximation on low-consequence regions accrues less consequential debt")
    L = rd.DebtLedger(); L.incur("a", 5, 2, 3); L.incur("b", 5, 2, 9)
    check(L.repayment_priority()[0].consequence == 9, "repay highest-consequence debt first")


# --- VIEW vertical slice: rasterizer + Causal Continuity Hypothesis ---------------------------------

def _frame_at(w, W=64, H=40):
    return view.interpret(view.snapshot(w), view.Camera(eye=(0.0, 20.0, 80.0), focal=60.0, screen=(W, H)))


def test_rasterizer_is_deterministic_and_covers():
    w = core.demo_world()
    for _ in range(5):
        w = core.tick(w)
    fb1 = raster.rasterize(_frame_at(w), 64, 40)
    fb2 = raster.rasterize(_frame_at(w), 64, 40)
    check(fb1.content_hash() == fb2.content_hash(), "same frame must rasterize to the same image hash")
    check(sum(fb1.coverage_counts().values()) > 0, "the rasterizer must actually cover pixels")
    check(set(raster.CONVENTIONS) == {"projection", "coverage", "sampling", "rasterization"},
          "each pipeline stage declares its convention")
    check(raster.aliasing_error(10, 1) > raster.aliasing_error(10, 8), "more samples reduces aliasing error")


def test_rasterizer_is_observer_only():
    baseline = core.trajectory(core.demo_world(), 40)
    w = core.demo_world()
    obs = [core.state_hash(w)]
    for _ in range(40):
        _ = raster.rasterize(_frame_at(w), 48, 30)     # full VIEW raster work each tick
        w = core.tick(w)
        obs.append(core.state_hash(w))
    check(core.trajectories_identical(baseline, obs),
          "CORE trajectory must be byte-identical with the rasterizer running (cardinal invariant)")


def test_causal_continuity_is_provisional_and_gate_is_honest():
    check(cc.STATUS == "hypothesis", "Causal Continuity must stay provisional in source (never a hard-coded law)")
    # the gate promotes only on a strict win over all controls + control loses
    win = {"causal (U×C×P)": 1, "uniform": 2, "distance": 2, "visibility": 2, "pfal (U×C×P×S)": 2,
           "drifted (control)": 3}
    lose = dict(win); lose["uniform"] = 0
    check(cc.earns_promotion(win)[0] is True, "a strict win over all controls earns promotion")
    check(cc.earns_promotion(lose)[0] is False, "losing to any control blocks promotion")


def test_view_slice_records_honest_failure():
    res, promote, reason = rb.evaluate(seed=1, budget=400)
    check(promote is False, "the STATED (proportional) causal hypothesis does not earn promotion (recorded)")
    check(res["causal (U×C×P)"] > res["uniform"], "proportional causal over-concentrates and loses to uniform")
    check(res["optimal_waterfill (√C×perim)"] < res["uniform"],
          "the diagnosis holds: size-aware water-filling beats uniform")


# --- ranking/allocation split + Representation Resistance (Milestone 3.1) ---------------------------

def test_representation_resistance_and_debt_pressure():
    check(rep.representation_resistance({"size": 10}) > rep.representation_resistance({"size": 2}),
          "a bigger region has more representation resistance (more edge)")
    check(rep.debt_pressure(200, 80) == 16000, "DebtPressure = RealityDebt × RepresentationResistance")


def test_two_stage_allocation_is_exact_and_deterministic():
    regions = {"a": {"uncertainty": 3.0, "consequence": 9, "persistence": 4, "size": 10},
               "b": {"uncertainty": 0.5, "consequence": 1, "persistence": 1, "size": 2}}
    a1 = al.two_stage_allocate(regions, 100, al._causal_priority)
    a2 = al.two_stage_allocate(regions, 100, al._causal_priority)
    check(sum(a1.values()) == 100, "two-stage allocation is exact (sums to budget)")
    check(a1 == a2, "two-stage allocation is deterministic")
    check(a1["a"] > a1["b"], "the high-priority, high-resistance region receives more budget")


def test_ranking_is_not_allocation():
    res = al.run(seed=1, budget=400)
    rw = res["ranked_waterfill (√(prio·RR))"]
    check(all(rw < res[k] for k in res if not k.startswith("ranked")),
          "two-stage ranked_waterfill strictly beats every other policy on the future-causal residual")
    check(res["proportional_causal (∝U·C·P)"] > rw,
          "proportional allocation (conflated) is worse than two-stage — ranking ≠ allocation")


# --- Milestone 4: dual-axis arena + stressors -------------------------------------------------------

def test_perceptual_continuity_loss():
    check(pc.perceptual_continuity_loss({"a": 5}, {"a": 5}, {"a": 3}) == 0,
          "no reallocation between frames means zero perceptual continuity loss")
    check(pc.perceptual_continuity_loss({"a": 5}, {"a": 9}, {"a": 3}) == 12,
          "PCL = sensitivity × |Δ samples| (3 × 4)")


def test_arena_exposes_causal_vs_perceptual_mismatch():
    res = arena.run(seed=1, budget=400, frames=24)
    check(res["uniform"][1] == 0, "uniform is perfectly steady (zero perceptual loss)")
    check(res["ranked_waterfill"][0] < res["uniform"][0], "ranked_waterfill wins the causal residual axis")
    check(res["ranked_waterfill"][1] > res["uniform"][1], "ranked_waterfill loses the perceptual axis (churn)")
    bc = min(res, key=lambda k: res[k][0]); bp = min(res, key=lambda k: res[k][1])
    check(bc != bp, "MISMATCH: minimizing causal residual ≠ maximizing perceptual continuity")
    check(len(arena.pareto_front(res)) >= 2, "a genuine trade-off: multiple non-dominated policies")


def test_hardening_damped_waterfill_cuts_perceptual_loss():
    res = arena.run(seed=1, budget=400, frames=24)
    check(res["damped_waterfill (hardened)"][1] < res["ranked_waterfill"][1],
          "the hardened damped allocator cuts perceptual loss vs the churny optimum")


def test_stressors_extract_weaknesses():
    check(any(d for _, d, _ in stress.mutation_guard(seed=1)),
          "the Goodhart mutation guard notices at least one degraded allocator (metric is not decoration)")
    check(stress.adversary_wrong()["broke"], "raw-consequence allocator breaks on improbable futures")
    check(stress.adversary_gameable()["broke"], "self-report allocator is gameable (a region inflates its budget)")


# --- Milestone 5: transition debt + adversarial scenes ----------------------------------------------

def test_transition_debt_frontier_is_lambda_parameterized():
    check(td.transition_debt({"a": 5}, {"a": 9}, {"a": 3}) == 12, "transition debt = sensitivity × |Δ|")
    check(td.total_cost(100, 10, exchange_rate=5) == 150, "Total Cost = Representation + λ·Transition")
    res = arena.run(seed=1, budget=400, frames=24)
    check(td.best_policy(res, 0) == "ranked_waterfill", "λ=0 → chase the causal residual")
    check(td.best_policy(res, 10_000_000) == "uniform", "huge λ → never move (uniform)")
    check(len(td.crossovers(res)) >= 3, "the frontier has ≥3 regimes (ranked → damped → uniform)")


def test_adversarial_scenes_expose_adaptation_tension():
    check(adv.probe_thrash(adv.flicker_trap(seed=1), adv.greedy) >
          adv.probe_thrash(adv.flicker_trap(seed=1), adv.Damped()),
          "FLICKER: greedy thrashes more than damped")
    gg, _ = adv.probe_lag(adv.delayed_consequence(delay=12, seed=1), adv.greedy, 12)
    dg, _ = adv.probe_lag(adv.delayed_consequence(delay=12, seed=1), adv.Damped(), 12)
    check(dg < gg, "DELAYED CONSEQUENCE: damped lags (less budget at the critical frame) — no free damping")
    h = adv.probe_hoard(adv.false_future())
    check(h["priority_hoard_%"] > h["realized_hoard_%"], "FALSE FUTURE: a priority allocator hoards fidelity")
    c = adv.probe_cliff(adv.representation_cliff())
    check(c["perimeter_resistance_error"] > c["cliff_aware_error"], "CLIFF: scalar resistance misses the threshold")


# --- Milestone 6: resistance tensor + shader cache (the industrial bridge) ---------------------------

def test_resistance_tensor_and_fidelity_derivative():
    t = rt.resistance_tensor({"lighting_sensitivity": 9})
    check(set(t) == set(rt.DIMENSIONS), "the resistance tensor carries all 7 dimensions")
    check(rt.miss_cost({"lighting_sensitivity": 9, "reconstruction_sensitivity": 8}) >
          rt.miss_cost({"lighting_sensitivity": 2}), "miss_cost is higher for a high-sensitivity region")
    check(rt.fidelity_derivative(lambda b: min(100, b * 10), 0) >
          rt.fidelity_derivative(lambda b: min(100, b * 10), 50),
          "marginal utility (∂Fidelity/∂Budget) falls as quality saturates")


def test_shader_cache_turns_hitches_into_allocation():
    c = {"material_family": "m", "geometry_class": "g", "lighting_regime": "l",
         "hardware_path": "rdna", "temporal_stability": "s"}
    check(sc.condition_key(c) == sc.condition_key(dict(c)), "condition key is deterministic / replayable")
    res = sc.run(seed=1, frames=48)
    check(res["predictive"] < res["reactive"], "predictive prewarm beats reactive compile-on-miss")
    check(res["predictive+fallback"] <= res["predictive"] + 1, "fallback tiers bound the worst-case hitch")
    check(res["random (control)"] >= res["predictive"], "random prewarm control does not beat predictive")


# --- Milestone 7: Causal Surface Area + Representation Readiness -------------------------------------

def test_causal_surface_area_and_prophecy_guard():
    shared = {"agents_can_affect": 4, "expected_divergence": 8, "lighting_sensitivity": 9,
              "reconstruction_sensitivity": 8}
    solo = {"agents_can_affect": 1, "expected_divergence": 1, "lighting_sensitivity": 2}
    check(cs.causal_surface_area(shared) > cs.causal_surface_area(solo) * 5,
          "a shared/contested object has far higher Causal Surface Area")
    check(cs.representation_forecast("wall", "destruction_assets").admissible(),
          "preparing a representation is an admissible forecast")
    check(not cs.reality_forecast("wall", "destroyed").admissible(), "asserting an outcome is not admissible")
    try:
        cs.assert_prepared(cs.reality_forecast("wall", "destroyed"))
        check(False, "a reality forecast must raise ProphecyViolation")
    except cs.ProphecyViolation:
        check(True, "the renderer may prepare representations, never decide outcomes (prepare ≠ decide)")
    check(cs.classify_multiplayer_artifact("incorrect_hit")[0] == "core_network",
          "a bad hit result is a CORE/network issue, not a renderer concern")


def test_causal_surface_beats_proximity_for_shared_objects():
    res = cs.run(seed=1, budget=400)
    check(res["causal_surface_area"] < res["proximity"] and res["causal_surface_area"] < res["visibility"],
          "CSA-driven readiness leaves less unprepared debt where futures converged than proximity/visibility")


def test_readiness_layer_prepares_shared_resources():
    prepared, shared_ids = rdy.demo(seed=1, budget=400)
    check(len(prepared & shared_ids) >= 1, "the readiness layer prepares shared high-CSA resources")


# --- Milestone 8: Causal Contract + Representation Futures Graph -------------------------------------

def test_causal_contract_maps_causality_not_outcomes():
    con = ccon.make_contract("door", ["collision", "explosion", "net_authority"], ["intact", "cracked", "debris"])
    check(con.admissible(), "a relationship-map contract (affected_by + possible representations) is admissible")
    try:
        ccon.reject_outcome("door", "destroyed", at_tick=400)
        check(False, "a contract asserting an outcome must be rejected")
    except ccon.CausalAuthorityLeak:
        check(True, "an outcome assertion raises CausalAuthorityLeak (a contract maps causality, never predicts)")


def test_csa_temporal_decay_fixes_the_leak():
    obj = {"agents_can_affect": 4, "expected_divergence": 6, "lighting_sensitivity": 8}
    check(ccon.decayed_csa(obj, dt=0) > ccon.decayed_csa(obj, dt=120) * 3,
          "Causal Surface Area decays with temporal distance — no readiness memory leak")
    check(ccon.temporal_relevance(0) == 100 and ccon.temporal_relevance(10 ** 6) <= 1,
          "temporal relevance is 100 now and decays toward 0 far out")


def test_futures_graph_prepares_breadth_never_selects():
    g = (rf.FuturesGraph()
         .add_transition("intact", "damaged", 60, "shaderA+debris", cost=20)
         .add_transition("intact", "destroyed", 30, "fracture+dust", cost=20))
    from ursprung import causal_surface as _cs
    csa = _cs.causal_surface_area({"agents_can_affect": 4, "expected_divergence": 6, "lighting_sensitivity": 8})
    prepared = rf.prepare_branches(g, "intact", csa, budget=100)
    check(len(prepared) >= 2, "the futures graph prepares MULTIPLE branches (breadth preserved)")
    check(rf.survive_truth_correction(prepared, "damaged")[0] == "ready",
          "a prepared branch survives a CORE truth correction with no hitch")
    check(rf.survive_truth_correction(prepared, "gone")[0] == "fallback",
          "an unprepared outcome degrades to a graceful fallback, never a lie")
    try:
        rf.select_future("intact", "destroyed")
        check(False, "select_future must be forbidden")
    except ccon.CausalAuthorityLeak:
        check(True, "select_future is forbidden — the renderer prepares futures, only CORE selects one")


# --- Milestone 9: causal mutation surface + provider contracts + dependency access ------------------

def test_causal_mutation_surface_wins_the_crucible():
    shared = {"authority_distance": 8, "affected_agents": 6, "rollback_cost": 9,
              "lighting_sensitivity": 8, "reconstruction_sensitivity": 7}
    solo = {"authority_distance": 1, "affected_agents": 1, "rollback_cost": 1, "lighting_sensitivity": 2}
    check(cm.mutation_cost(shared) > cm.mutation_cost(solo) * 20, "a shared contested object has far higher mutation cost")
    check(cm.object_facets(shared)["physical"] == "CORE", "only the physical facet is CORE-authoritative")
    res = cm.crucible(seed=1, budget=240)
    best = min(res, key=lambda k: res[k])
    check(best == "causal_mutation_surface", "mutation surface loses least when reality disagrees (rollback-aware)")
    check(res["causal_mutation_surface"] <= res["causal_surface_area"], "mutation surface ≤ CSA under contention")


def test_provider_contracts_select_by_capability():
    P = pcon.default_providers()
    check(pcon.select_provider(P, {"material", "lighting", "geometry", "history", "motion"}, 40)[0] == "ray_tracer",
          "ample budget + full conditions → highest-quality admissible provider")
    check(pcon.select_provider(P, {"material", "lighting"}, 1)[0] in ("impostor", "particle_fallback"),
          "a very tight latency budget degrades to a cheap provider / fallback")
    check(pcon.select_provider(P, {"geometry"}, 6)[0] in ("meshlet", "impostor", "particle_fallback"),
          "missing inputs excludes providers that require them")


def test_dependency_access_is_the_hidden_resource():
    check(dep.dependency_surface_area({"dependencies": ["material", "lighting", "animation", "destruction",
                                                        "sound", "occlusion"]}) >= 6, "DSA counts coupled dependencies")
    hi = dep.preparation_value({"affected_agents": 4, "expected_divergence": 5, "lighting_sensitivity": 8, "dependency_access": 100})
    lo = dep.preparation_value({"affected_agents": 4, "expected_divergence": 5, "lighting_sensitivity": 8, "dependency_access": 10})
    check(hi > lo, "Preparation Value = Causal Surface Area × Dependency Access (rises with access)")
    objs = dep._scene(seed=1)
    check(dep.access_debt(objs, 10) > dep.access_debt(objs, 100),
          "fidelity is downstream of dependency visibility (more access → less unprepared debt)")
    vr = dep.value_ranked_debt(objs, exposure_budget=60)
    check(vr["value_ranked"] <= vr["uniform"] and vr["value_ranked"] <= vr["random"],
          "spending dependency access by Preparation Value beats uniform/random")


# --- Milestone 10: dependency integrity + representation compiler -----------------------------------

def test_dependency_claim_tautology_and_consensus():
    g = di.DependencyClaim("door", "destruction_shader", consequence=5)
    check(di.tautology_holds(g, g.content_hash()), "a genuine claim passes the integrity tautology")
    check(not di.tautology_holds(g, "deadbeefdeadbeef"), "a tampered hash fails the tautology")
    ws = [di.DependencyClaim("door", "destruction_shader", consequence=5) for _ in range(3)]
    ws.append(di.DependencyClaim("door", "destruction_shader", consequence=999))   # one adversarial witness
    v = di.consensus_validate(ws, k=3)
    check(v["admitted"] and v["agree"] == 3 and v["dissent"] == 1,
          "k-of-n consensus admits the agreeing majority; the adversary is kept as a dissent ghost")
    check(not di.consensus_validate(ws, k=4)["admitted"], "raising k beyond agreement refuses (no false consensus)")


def test_evidence_and_decay_close_access_not_relevance():
    obj = {"affected_agents": 4, "expected_divergence": 5, "lighting_sensitivity": 8, "dependency_access": 100}
    false = di.DependencyClaim("o", "d", evidence=0, issued_tick=100, expiration=10 ** 9)
    fresh = di.DependencyClaim("o", "d", evidence=100, issued_tick=100, expiration=10 ** 9)
    stale = di.DependencyClaim("o", "d", evidence=100, issued_tick=0, expiration=10 ** 9)
    check(di.integrity_aware_preparation_value(obj, false, 100) == 0, "a false dependency earns ~no preparation budget")
    check(di.integrity_aware_preparation_value(obj, stale, 600) < di.integrity_aware_preparation_value(obj, fresh, 100),
          "a stale dependency decays (temporal half-life)")
    res = di.fog_crucible(seed=1, budget=300)
    check(min(res, key=lambda k: res[k]) == "integrity_aware", "integrity-aware loses least under dependency fog")


def test_representation_compiler_preserves_continuity():
    ample = rc.compile_pipeline({"geometry", "lighting", "motion", "history"}, 60)
    tight = rc.compile_pipeline({"geometry", "lighting", "motion", "history"}, 8)
    check(ample["continuity_preserved"] and tight["continuity_preserved"], "continuity is preserved in both")
    check(not ample["degraded"] and ample["total_quality"] > tight["total_quality"], "ample budget → full quality")
    check(tight["total_latency"] <= 8 and tight["degraded"], "tight budget degrades but fits the deadline")


# --- Milestone 11: capability tokens + causal access control (information firewall) -----------------

def test_capability_token_is_bounded_and_never_grants_authority():
    t = cap.issue("prepare_representation", subject="door", scope="visual_only", horizon=200)
    check(t.permits("prepare_representation", "visual_only", 100), "token permits a bounded prepare within horizon")
    check(not t.permits("prepare_representation", "gameplay", 100), "token denies a different purpose")
    check(not t.permits("prepare_representation", "visual_only", 500), "token denies use beyond its horizon")
    check("mutate" in t.cannot and "select_outcome" in t.cannot and "reveal_hidden" in t.cannot,
          "mutate / select_outcome / reveal_hidden are forbidden on every token")
    try:
        cap.issue("mutate", subject="door")
        check(False, "issuing a token that grants mutate must raise")
    except cap.CapabilityViolation:
        check(True, "a capability token may never grant mutate/select (prepare ≠ decide)")


def test_information_firewall_blocks_wallhack_despite_integrity_and_consensus():
    obs = cac.Observer("A", authorized_scope={"door", "wall"})
    legit = di.DependencyClaim("door", "destruction_shader", consequence=5)
    check(cac.admissible_for_representation(legit, obs, legit.content_hash())[0],
          "an in-scope, unforged claim is admitted (legitimate readiness)")
    cheat = di.DependencyClaim("enemy_hidden", "position_reveal", consequence=9)
    check(di.tautology_holds(cheat, cheat.content_hash()), "the cheat claim passes the integrity tautology")
    check(di.consensus_validate([cheat] * 5, k=3)["admitted"], "the cheat claim passes a colluding consensus")
    ok, reason = cac.admissible_for_representation(cheat, obs, cheat.content_hash())
    check(not ok and reason.startswith("forbidden_advantage"),
          "an out-of-scope claim is rejected even though unforged + agreed (wallhack/ESP blocked)")
    r = cac.fog_attack()
    check(r["advantage_leaked"] == 0, "Dependency Fog Attack: advantage leaked = 0 (authorization is the floor)")


# --- Milestone 12: composition firewall + side-channel defenses -------------------------------------

def test_composition_firewall_caps_reconstruction():
    r = rec.crucible(fact_bits=64, threshold=0.5)
    check(r["each_individually_allowed"], "each fragment is individually allowed (below threshold)")
    check(r["naive_reconstruction"] > 0.5, "without the firewall the SET reconstructs > threshold (a leak)")
    check(r["debt_without_firewall"] > 0, "Information Reconstruction Debt > 0 (per-fragment firewall would leak)")
    check(r["composition_firewall_reconstruction"] <= 0.5, "the composition firewall caps reconstruction at/below threshold")
    check(len(r["blocked"]) >= 1, "the marginal fragment(s) crossing the threshold are blocked")


def test_side_channels_are_closed():
    ft = [8, 12, 15, 8]
    check(sch.timing_leak(ft) > sch.timing_leak(sch.normalize_timing(ft, 16)), "timing normalization reduces the leak")
    check(sch.timing_leak(sch.normalize_timing(ft, 16)) == 0, "quantized timing has no resource-dependent spread")
    check(sch.inversion_leak(["debris"]) > sch.inversion_leak(["a", "b", "c", "d"]),
          "preparing breadth dilutes the prediction-inversion leak (prepare ≠ announce probability)")
    cheat = [{"hash": "CHEAT", "evidence": 30, "authority": 10, "reliability": 10, "validity": 80} for _ in range(8)]
    honest = [{"hash": "TRUE", "evidence": 90, "authority": 95, "reliability": 90, "validity": 90},
              {"hash": "TRUE", "evidence": 80, "authority": 60, "reliability": 80, "validity": 90},
              {"hash": "TRUE", "evidence": 80, "authority": 60, "reliability": 80, "validity": 90}]
    v = sch.weighted_consensus(cheat + honest)
    check(v["by_count_would_pick"] == "CHEAT", "by witness count the colluding majority would win")
    check(v["admitted"] and v["winning_hash"] == "TRUE",
          "by weighted trust the honest+server claim wins — collusion defeated (consensus ≠ truth)")


def test_accumulation_safety_caps_the_sequence():
    r = acc.crucible()
    # 1. history compression: per-frame harmless, accumulated reconstructs (M12's firewall would miss this)
    check(r["per_frame_harmless"], "each frame's leak is below the single-frame threshold")
    check(r["accumulated_debt"] > 0, "accumulated over the window the history reconstructs > threshold (debt > 0)")
    # 2. privacy budget: hidden object = 0 blocks any spend; the COMBINATION trips, not the piece
    check(r["hidden_spend_blocked"], "a hidden-object (budget 0) representation spend is blocked")
    check(r["visible_spend_ok"], "a visible-object (unlimited) spend is allowed")
    pb = acc.PrivacyBudget(); pb.set_budget("A", "wall", 1.0)
    check(pb.spend("A", "wall", 0.6) and not pb.spend("A", "wall", 0.6),
          "each spend is individually fine; the COMBINATION exceeds the privacy budget")
    # 3. causal query rate limiting: allowed query, disallowed sequence
    check(r["early_queries_allowed"], "each individual query about the subject is legal")
    check(r["accumulation_throttled"], "the accumulation of legal queries is throttled (sequence ≠ query)")
    # 4. importance ≠ exposure: internal importance does not leak as observable behavior
    check(r["importance_hidden"], "differing internal importances collapse to one external exposure level")
    check(acc.exposed_level(10) == acc.exposed_level(90) == 0, "at 1 public level, exposure is constant")


def test_adversarial_dynamics_defense_is_the_leak():
    r = ad.crucible()
    # 1. reaction debt: a defense that reacts only near the secret leaks; a constant reaction leaks nothing
    check(r["reaction_naive_leak"] > 0, "a reaction correlated with the hidden trigger leaks (the discontinuity is the signal)")
    check(r["reaction_safe_leak"] == 0, "a reaction uncorrelated with the secret carries no information")
    # 2. absence firewall: missing ≠ informative unless entitled
    check(r["absence_naive"] > 0, "a conspicuously missing representation is a negative-space signal")
    check(r["absence_masked"] == 0, "for an unentitled observer the suppression must mask its own gap (missing ≠ informative)")
    check(r["absence_entitled_honest"] == r["absence_naive"], "for an entitled observer the absence is honest, not masked")
    # 3. distributed reconstruction: each observer safe, the union reconstructs, the firewall caps the group
    check(r["per_observer_each_safe"], "each observer alone stays below the reconstruction threshold")
    check(r["distributed_union"] > 0.5, "the colluding GROUP (union of fragments) reconstructs > threshold")
    check(r["distributed_firewalled"] <= 0.5, "the distributed firewall caps the cross-observer reconstruction")
    # 4. adaptive ≠ random: the boundary moves on probing instead of rolling dice
    check(r["adaptive_total"] < r["random_total"], "an adaptive boundary yields less under sustained probing than a fixed-distribution one")
    # 5. the ultimate invariant: reveal consequences, never the mechanism
    check(r["consequence_after_ok"], "a consequence may be revealed at/after the committed event")
    check(r["consequence_before_blocked"], "a consequence shown BEFORE the event leaks the predictive mechanism")
    check(r["mechanism_always_blocked"], "the mechanism (prepared branch / hidden cause) is never disclosable")
    check(ad.reveals_mechanism("hidden_branch_choice", 99), "naming a hidden branch is mechanism even long after the event")


def test_representation_privacy_image_not_generator():
    r = rp.crucible()
    # 1. ambiguity debt: an invertible uncertainty field collapses; a coarse one preserves the ambiguity
    check(r["ambiguity_naive"] > r["ambiguity_shaped"], "an invertible uncertainty radius is a measurement instrument (high ambiguity debt)")
    check(r["ambiguity_shaped"] == 0.0, "a coarse/constant exposure leaves the design's full ambiguity intact")
    check(r["naive_recoverable"] > r["shaped_recoverable"], "the naive field lets the attacker distinguish more secret levels")
    # 2. representation hysteresis: a single threshold oscillates (probe-able); a band does not
    check(r["single_threshold_flips"] > r["hysteresis_flips"], "a single threshold oscillates under hovering — the attacker reads it")
    check(r["hysteresis_flips"] <= 1, "enter ≠ exit band stays stable (the boundary resists being used as a probe)")
    # 3. decoy without reality mutation: fake reality forbidden, fake observability pattern allowed
    check(r["fake_reality_blocked"], "a decoy that asserts a false world fact is forbidden (CORE cannot lie)")
    check(r["fake_observability_ok"], "a non-informative continuity pattern that asserts no fact is admissible")
    check(r["core_mutation_blocked"], "a decoy that mutates committed state is forbidden")
    # 4. observer fingerprint debt: uncaused per-observer variance leaks the rules
    check(r["fingerprint_leak"] == 40, "uncaused per-observer policy variance is a fingerprint leak")
    check(r["fingerprint_hardened"] == 0, "policy driven only by world state has no fingerprint debt")
    # 5. image ≠ generator
    check(r["world_fact_ok"], "a world consequence (explosion) may be exposed")
    check(r["generator_tell_blocked"], "a known implementation tell (streaming stall ⇒ proximity) is blocked")
    check(r["correlated_impl_blocked"], "even a world fact leaks the generator if its rendering correlates with hidden state")


def test_execution_surface_cost_is_not_hidden_state():
    r = es.crucible()
    # 1. transition signature debt: on-demand streaming spikes for the secret; pre-preparation does not
    check(r["signature_on_demand"] > 0, "streaming a representation on demand makes a cost signature unique to the secret")
    check(r["signature_prepared"] == 0, "a pre-prepared representation emits the same signature whether or not the secret is present")
    # 2. cache side-channel budget: prepare by policy, not by hidden-state visibility
    check(r["cache_exposure_naive"] > 0, "preparing assets only when the secret is near makes the cache a message")
    check(r["cache_exposure_policy"] == 0, "a fixed readiness policy reveals nothing through what got prepared")
    # 3. semantic constant-time: world A vs B must not be separable from behavior
    check(r["separable_on_demand"], "on-demand behavior lets a classifier separate enemy-present from enemy-absent")
    check(not r["separable_prepared"], "prepared behavior is indistinguishable across the two worlds")
    check(r["accuracy_on_demand"] == 1.0 and r["accuracy_prepared"] == 0.5, "separability collapses to chance when prepared")
    # 4. three-currency objective: counting leakage flips the winner over the SAME plans
    check(r["old_objective_winner"] == "min_gpu", "the old GPU-only objective picks the cheap, leaky plan")
    check(r["new_objective_winner"] == "over_prepared", "counting information leakage makes over-preparation the cheapest plan")
    check(r["over_prepared_total_new"] < r["min_gpu_total_new"], "under fidelity+transition+leakage, over-preparation wins")
    # 5. renderer ≠ oracle
    check(r["world_observation_ok"], "a client may observe a world fact")
    check(r["machinery_blocked"], "a client may not observe the machinery (a timing/cache tell) that maps hidden state to representation")


def test_convergence_correction_not_cause():
    r = cv.crucible()
    # 1. reconciliation signature debt: an exact rollback distance is invertible; a bounded family is not
    check(r["recon_exact_levels"] > r["recon_bucketed_levels"], "an exact correction distance leaks more states than a bounded family")
    check(r["recon_bucketed_levels"] <= 4, "the bounded correction family {none,small,medium,large} reveals only the coarse class")
    # 2. divergence firewall: an unentitled client learns 'world changed', not the repair detail
    check(r["disclosure_unentitled_bits"] == 1, "an unentitled client is told only that the world changed")
    check(r["disclosure_entitled_bits"] > r["disclosure_unentitled_bits"], "an entitled client gets the full in-scope correction")
    # 3. convergence readiness: a prepared correction is unobservable; an unprepared one spikes
    check(r["readiness_unprepared"] > 0, "an unprepared correction's cost reveals that a hidden event was near")
    check(r["readiness_prepared"] == 0, "a prepared representation absorbs the correction with no observable reconciliation event")
    # 4. distributed correction reconstruction: a fleet of honest clients is a distributed microscope
    check(r["per_client_each_safe"], "each client's own correction stays below the reconstruction threshold")
    check(r["fleet_union"] > 0.5, "the fleet's compared corrections (the union) reconstructs the hidden event")
    check(r["fleet_firewalled"] <= 0.5, "the distributed correction firewall caps the cross-client union")
    # 5. correction ≠ cause
    check(r["change_fact_ok"], "a correction may reveal THAT reality changed")
    check(r["repair_detail_blocked"], "a correction may not reveal WHY/WHERE/WHO it was repaired (the rollback distance)")
    check(r["entitled_sees_detail"], "a causally entitled observer may see the repair detail")


def test_reality_harness_traffic_produces_hypothesis():
    r = rh.crucible()
    # the substrate is reproducible (deterministic simulated traffic)
    check(r["channel_deterministic"], "the simulated channel is deterministic — reproducible traffic")
    check(rh.run_experiment("bucketed") == rh.run_experiment("bucketed"), "an experiment run is reproducible")
    # measured (not asserted) findings about the reconciliation policies
    check(r["bucketing_reduces_entropy"], "bucketing (M17) measurably reduces correction entropy")
    check(r["bucketing_reduces_info"], "bucketing measurably reduces extractable info bits")
    check(r["bucketing_keeps_existence_leak"], "bucketing still leaks the EXISTENCE of disagreement (distinguishability 1.0)")
    check(r["floor_reduces_distinguishability"], "a cover-correction floor measurably lowers distinguishability")
    check(r["floor_costs_fidelity"], "the floor buys existence-privacy with measurably more fidelity cost")
    check(r["no_free_lunch"], "no reconciliation policy achieves full privacy at no fidelity cost")
    check(r["large_events_still_leak"], "large corrections still leak — convergence-privacy ⟂ convergence-fidelity is a frontier")
    # the seam: changing the (simulated) channel changes the measurement, as a real socket would
    slow = rh.run_experiment("exact", channel=rh.NetworkChannel(base_latency=12, jitter=0, seed=1))
    fast = rh.run_experiment("exact", channel=rh.NetworkChannel(base_latency=2, jitter=0, seed=1))
    check(slow["fidelity_cost"] > fast["fidelity_cost"], "latency drives reconciliation cost (the channel is the swappable seam)")


def test_behavioral_harness_player_is_final_observer():
    r = bh.crucible()
    # 1. Convergence Leakage Vector: privacy is a vector, not a scalar
    check(r["bucketing_closes_magnitude"], "bucketing closes the magnitude axis")
    check(r["bucketing_keeps_existence"], "bucketing leaves the existence axis fully open")
    check(r["floor_scalar_lower"] and r["timing_axis_untouched"], "a lower scalar hides that the timing axis was never touched — privacy ≠ scalar")
    check(r["only_timing_norm_closes_timing"], "only a timing-normalized policy closes the timing axis (a produced insight, not assumed)")
    # 2. counterfactual amplification: a probing adversary localizes the hidden boundary; a passive one cannot
    check(r["passive_uncertainty"] == 100.0, "a passive client cannot localize the server's hidden decision boundary")
    check(r["probing_uncertainty"] < 0.01, "an adversary that chooses its inputs binary-searches the boundary to near-zero uncertainty")
    check(r["debt_probing"] > r["debt_passive"], "Counterfactual Debt amplifies with probe control (the attacker chooses the question)")
    # 3. experiment-layer seam: same API over simulated (regression) and real (validity) channels
    check(r["sim_replayable"], "the simulated channel is deterministic and replayable (the regression environment)")
    check(r["real_unavailable_same_api"], "the real channel uses the identical API and is intentionally unbuilt here (the validity environment)")
    # 4. the player as the final observer
    check(r["naive_feel_learnable"], "a naive policy lets the player learn the rules by feel (image ≠ generator at the gameplay layer)")
    check(r["constant_feel_opaque"], "a constant-feel policy is behaviorally indistinguishable")
    check(r["feel_ok"], "a player may experience the world (recoil, hits, audio)")
    check(r["policy_tell_blocked"], "a player may not learn a policy threshold (the rollback threshold) through interaction")


def test_adversary_harness_learning_observer():
    r = ah.crucible()
    # the closed-loop learner cracks a naive policy in O(log N) but cannot localize constant-feel
    check(r["naive_is_cracked"], "a naive policy's hidden boundary is localized below the extraction bound")
    check(r["constant_feel_resists_learning"], "constant-feel keeps the learner's regret at/above the extraction bound")
    check(r["naive_learns"], "the agent's true regret descends with interactions against a naive policy (it learns)")
    check(r["constant_feel_curve_flat"], "the agent's regret does NOT improve against constant-feel (the curve stays flat)")
    check(r["leakage_naive_gt_constant"], "Behavioral Leakage (info/experiment) is higher for naive than constant-feel")
    # incentive / decision-channel leakage: hidden state can leak through the action economy
    check(r["decision_leak_naive"] == 1.0, "under a naive policy every decision channel (hit-reg, audio, matchmaking…) leaks")
    check(r["decision_leak_constant"] == 0.0, "under constant-feel no decision channel leaks")
    # active learning + reproducibility (the substrate is a deterministic regression environment)
    check(ah.AdaptiveObserver(1024).select_experiment() == 512, "the agent selects the max-information-gain experiment (bisection midpoint)")
    check(ah.run_agent("naive", 300, 1024, 12)[-1] <= 1, "active bisection localizes a naive boundary to within 1 over 12 chosen experiments")
    check(ah.run_agent("constant_feel", 300, 1024, 12)[-1] >= 1, "the same agent cannot localize a constant-feel boundary")
    check(ah.crucible() == r, "the adversary experiment is reproducible (deterministic regression environment)")


def test_adversary_capacity_identifiability_is_class_relative():
    r = ac.crucible()
    # the absolute result: severing the secret from the channel beats EVERY adversary class
    check(r["constant_secret_absolute"], "constant-feel's secret is non-identifiable under all classes (info-theoretic severing)")
    # the relative result: M20's 'resists learning' was only true against the 1-D learner (C1)
    check(r["constant_generator_safe_vs_C1"], "constant-feel's generator is invisible to the C1 threshold learner (M20's class)")
    check(r["constant_generator_cracked_by_C2"], "a single-bit structure learner (C2) identifies the generator M20 could not")
    check(r["constant_generator_cracked_by_C3"], "the structured class (C3) also identifies it")
    check(r["recovered_bit"] == 3, "the structure learner names the actual rule (response keys off bit 3)")
    # the secret leaks only to the class that can express its dependence
    check(r["naive_secret_C1"], "naive's threshold secret is recovered by the matching (threshold) class")
    check(r["naive_secret_not_C2"], "the 'richer-looking' single-bit class cannot recover a threshold secret — capacity is not a scalar")
    # AIC is a lattice, not a total order; only C3 dominates
    check(r["classes_incomparable"], "C1 cracks the threshold rule but not the bit rule; C2 the reverse — the classes are incomparable")
    check(r["C3_dominates_generator"], "the richest tested class identifies every generator")
    check(r["keyed_only_C3"], "a parity-keyed generator needs the structured class (neither threshold nor single-bit suffices)")
    # the synthesis
    check(r["secret_absolute_generator_relative"], "secret-privacy can be absolute (sever the channel); generator-privacy is only ever class-relative")
    # the little learners are real, not asserted
    check(ac.detect_threshold(ac.rule_naive, 100) is True, "the threshold detector identifies the naive rule")
    check(ac.detect_threshold(ac.rule_constant_feel, 100) is False, "the threshold detector correctly fails on the non-monotone bit rule")
    check(ac.detect_single_bit(ac.rule_naive, 100) is None, "the single-bit detector correctly fails on the threshold rule")


def test_channel_discovery_finds_the_unmodeled_channel():
    r = cd.crucible()
    # clean channels read as severed (I = 0): the M21 class-independent absolute guarantee
    check(r["clean_channels_severed"], "channels independent of the secret carry zero mutual information (severed)")
    check(r["severed_is_absolute"], "a severed channel leaks the secret to no observer of any capacity")
    # a fully-revealing channel is found
    check(r["correction_fully_reveals"], "a channel that mirrors the secret reads as near-maximal mutual information")
    # THE HEADLINE: discovery surfaces a leaking channel that the modeled audit set omits
    check(r["unmodeled_leak_found"], "discovery finds a leaking channel (animation_events) outside the modeled audit set")
    check(r["animation_not_in_audit"], "that channel was never in the enumerated audit set")
    check(r["audit_alone_would_pass"], "an audit of only the enumerated channels would have passed while the system leaks")
    check(r["leak_is_real"], "the unmodeled channel's leak is real (I > 0), to be handed to the adversary class")
    # discovery inverts the question: it ranks ALL observed channels, not just the audited ones
    check(r["discovers_more_than_audit"], "discovery scans more channels than the audit enumerated")
    check(cd.secret_severed_in("audio_events"), "secret_severed_in confirms an absolute (severed) channel")
    check(not cd.secret_severed_in("correction_events"), "secret_severed_in reports a leaking channel as not severed")
    # the recursive mirror: the detector is itself a hypothesis class (estimator coverage)
    check(r["per_sample_reads_severed"], "a marginal estimator reads the accumulation channel as severed (I = 0)")
    check(r["windowed_finds_leak"], "a sequence estimator finds the same channel leaking (temporal structure)")
    check(r["same_channel_flips_verdict"], "the SAME channel + trace flips verdict across estimator classes — 'no leak' is always 'under estimator E'")
    check(r["result_carries_its_boundary"], "every MeasurementResult names its estimator class and coverage boundary, never a bare 'safe'")
    ps = cd.measure("accumulation_events", cd.accumulation_channel, cd.slow_secret, "per_sample")
    check(ps.estimator_class == "C_marginal" and ps.coverage_boundary, "a MeasurementResult carries its estimator class and blind spot")


def test_disclosure_policy_compiles_and_audits():
    r = disc.crucible()
    # the committed compiler emits exactly the purpose-need ∩ allowed: compliant AND sufficient
    check(r["compiled_channels"] == ["threat_direction", "timing_window"], "the compiler emits the purpose's needed channels within the allowed set")
    check(r["compiled_compliant"], "the compiled emission discloses nothing forbidden or unauthorized")
    check(r["compiled_sufficient"], "the compiled emission meets the purpose's participation floor")
    # negative controls — the M10–M21 firewall, pointed at the emission, catches violations
    check(r["over_disclosure_caught"], "an emission leaking a forbidden channel (exact_position) is caught (not compliant)")
    check(r["outside_allowed_caught"], "an emission outside the allowed set (server_state) is caught (not compliant)")
    check(r["under_provision_flagged"], "an emission missing a needed channel is compliant but NOT sufficient (participation floor)")
    # the policy is a committed, content-addressed convention, never a truth claim
    check(r["policy_hash_deterministic"], "the disclosure policy is content-addressed (deterministic hash)")
    check(r["policy_not_a_truth_claim"], "a disclosure policy chooses what to reveal; it is not a truth claim")
    # the audit reports its own boundary — 'compliant' is w.r.t. the audited channels, never 'safe'
    check(r["audit_carries_boundary"], "the audit names its coverage boundary (declared channels only)")
    p = disc.DisclosurePolicy("player", "survival", ["threat_direction"], ["exact_position"])
    check(p.permits("threat_direction") and not p.permits("exact_position"), "permits() respects allowed and forbidden")


def test_perception_loop_is_the_first_privacy_funnel_benchmark():
    r = perc.crucible()
    # the full loop runs: world → policy → compiled observation → agent → task → leakage
    # raw: full task success but the secret is fully recoverable (over-discloses)
    check(r["raw_utility"] == 1.0, "the raw policy lets the agent act optimally (utility 1.0)")
    check(r["raw_leakage"] == 6.0, "the raw policy leaks the whole secret (I = H(secret) = 6 bits)")
    check(r["raw_over_discloses"], "raw clears the utility floor but exceeds the leakage budget — over-discloses")
    # compiled: SAME task success at a fraction of the leakage → clears both → the funnel point
    check(r["compiled_utility"] == 1.0, "the compiled observation preserves full task success")
    check(r["compiled_cuts_leakage"], "the compiled observation leaks strictly less than raw")
    check(r["compiled_passes"], "compiled clears BOTH the utility floor and the leakage budget")
    # blind: private but useless
    check(r["blind_leakage"] == 0.0, "the blind policy leaks nothing")
    check(r["blind_under_serves"], "blind is within the leakage budget but fails the utility floor — under-serves")
    # the produced result: only the compiled policy is on the right side of the frontier
    check(r["only_compiled_passes"], "of the three policies, only the compiled one preserves utility under the leakage budget")
    # the measurement carries its boundary, never a bare 'safe'
    res = perc.evaluate("compiled")
    check(res.passes and res.coverage_boundary, "the MeasurementResult reports pass/fail with a coverage boundary, not 'safe'")


def test_perception_adversary_leakage_is_not_exploitability():
    r = perc.adversary.crucible()
    # per-frame MI is a small, valid per-observation estimate; one frame cannot localize the secret (DPI)
    check(r["per_frame_leakage"] < 1.5, "the per-frame leakage estimate is a sliver (< 1.5 bits)")
    check(r["single_frame_candidates"] > 1, "a single compliant observation leaves many candidate cells")
    check(r["single_frame_within_bound"], "a single frame does not beat the per-frame MI bound (data-processing inequality holds)")
    # an accumulating (richer-class) learner recovers the EXACT secret across the session
    check(r["exact_recovered"], "the accumulating multilateration learner recovers the exact secret cell")
    check(r["accumulated_recovered_bits"] == 6.0, "accumulation recovers the full 6 bits of the secret")
    check(r["accumulation_beats_single_frame"], "the accumulating learner recovers strictly more than a single frame")
    # the headline: leakage (per-frame) ≠ exploitability (session) — the static estimate is falsified as a session claim
    check(r["exploitability_exceeds_estimate"], "session exploitability far exceeds the per-frame leakage estimate — leakage ≠ exploitability")


def test_session_accounting_is_purpose_preserving_under_accumulation():
    r = perc.session_accounting.crucible()
    # the accumulation-aware compiler drops the triangulating channel and keeps the stable task band
    check(r["aware_drops_triangulating_channel"], "the compiler drops the moving-threat channel that triangulates over a session")
    check(r["aware_keeps_task_channel"], "the compiler keeps the coarse band channel the task needs")
    # naive (the policy adversary.py broke) recovers the exact secret and busts the session budget
    check(r["naive_exact_recovered"], "the naive session policy still lets the accumulating learner recover the exact secret")
    check(r["naive_fails_budget"], "naive exceeds the session leakage budget (6 bits > 2)")
    # accumulation-aware: utility preserved AND exploitability collapsed, exact never recovered
    check(r["aware_preserves_utility"], "accumulation-aware keeps task utility at the floor (1.0)")
    check(r["aware_within_budget"], "accumulation-aware keeps session exploitability under the budget")
    check(r["aware_collapses_exploitability"], "accumulation-aware collapses exploitability vs naive (6 → ~1 bit)")
    check(r["aware_does_not_recover_exact"], "the accumulating learner can no longer recover the exact secret under the aware policy")
    check(r["aware_holds_for_all_secrets"], "the aware policy stays within budget and hides the exact cell for every secret")
    # blind is private but useless; only the aware policy clears both axes
    check(r["blind_under_serves"], "the blind policy is within budget but fails the utility floor")
    check(r["only_aware_passes"], "of the three session policies, only the accumulation-aware one passes both axes")
    # the first general result
    check(r["purpose_preserving_under_accumulation"], "purpose-preserving disclosure under an accumulating observer: utility 1.0, exploitability collapsed, exact hidden")


def test_perception_frontier_is_the_measurable_cost_of_knowledge():
    r = perc.frontier.crucible()
    # it is a genuine frontier: both axes strictly increase together — a tradeoff curve, no dominating point
    check(r["leakage_monotone"] and r["utility_monotone"], "leakage and utility rise together — a real tradeoff curve")
    check(r["leakage_equals_bits"], "leakage equals the bits disclosed (measured by the QIF estimator)")
    # NON-separable: full utility strictly requires full leakage (the opposite of the separable session win)
    check(r["full_utility_requires_full_leakage"], "exact-interception utility of 1.0 requires the full 6 bits of leakage — no free lunch")
    check(r["no_high_utility_at_low_leakage"], "no policy achieves high utility at low leakage — the channels are inseparable")
    check(r["each_bit_buys_utility"], "every disclosed bit buys utility — the measurable value of knowledge")
    check(r["utility_floor"] < 0.05, "with near-zero leakage, exact interception is near-hopeless")
    check(r["min_leakage_for_half_utility"] == 5.0, "even half the interception rate costs 5 of 6 bits")
    # the benchmark's point: the separable session result was a special case, not the general rule
    check(r["separable_was_a_special_case"], "the separable session win does not generalize — when the task needs the secret, the tradeoff is irreducible")


def test_perception_fidelity_condition_distinguishes_feasible_from_irreducible():
    r = perc.fidelity.crucible()
    # the separable session task satisfies BOTH clauses — a feasible Perception Fidelity Condition
    check(r["separable_faithful"] and r["separable_bounded"], "the separable task is both task-faithful and inference-bounded")
    check(r["separable_holds"], "the Perception Fidelity Condition HOLDS for the separable task")
    check(r["separable_preserves_uncertainty"], "the separable case preserves residual uncertainty (inverse leakage > 4 bits)")
    # the non-separable task: no disclosure level satisfies both — the condition is infeasible
    check(not r["nonseparable_feasible"], "no disclosure level makes the non-separable task both faithful and bounded — infeasible")
    check(r["nonseparable_umin_only_at_full_leakage"], "the only level meeting the utility floor busts the reconstruction bound (faithful XOR bounded)")
    check(r["nonseparable_full_utility_zero_residual"], "full interception utility leaves zero residual uncertainty (the secret fully recovered)")
    # the condition does its job: feasible for one task, provably irreducible for the other
    check(r["condition_distinguishes"], "the Perception Fidelity Condition holds for the separable task and is infeasible for the non-separable one")


def test_perception_leakage_is_a_function_of_observer_capacity():
    r = perc.observer_capacity.crucible()
    # against ONE fixed representation, recovery rises monotonically with observer capacity (memory horizon)
    check(r["monotone_in_capacity"], "recovery is monotone non-decreasing in observer capacity")
    check(r["rises_overall"], "recovery strictly rises from the lowest to the highest capacity")
    check(r["memoryless_recovers_little"], "a memoryless observer (W=1) recovers almost nothing")
    check(r["full_capacity_recovers_secret"], "a full-capacity (accumulating) observer recovers the exact secret")
    # the point: the same disclosure leaks differently to different observers → Leakage(C), never a scalar
    check(r["leakage_undefined_without_observer_class"], "the same fixed representation has capacity-dependent leakage — 'leakage' is undefined without naming the observer class")


def test_perception_response_action_is_a_channel():
    r = perc.response.crucible()
    # reaction is itself a leakage channel: the action alone leaks the secret even if disclosure was sealed
    check(r["reaction_is_a_channel"], "the actor's action carries information about the secret (I(S;A) > 0)")
    check(r["reactive_leaks_full_secret"], "an always-react policy leaks the whole secret through the action (2 bits)")
    check(r["reactive_utility"] == 1.0, "the reactive policy achieves full task utility (but at full action leakage)")
    # the response gate collapses action-leakage while preserving the high-value action
    check(r["gate_reduces_leakage"], "the response gate reduces action-leakage versus reacting to everything")
    check(r["gate_preserves_high_value"], "the gate still defends the high-value zone (utility on the action that matters)")
    # non-action is a coherent, first-class output
    check(r["silent_zero_leak"] and r["silent_zero_utility"], "never reacting is a coherent policy: zero action-leak, zero utility")
    # the response frontier is a coupled tradeoff (reducing the leak costs utility — not a free lunch)
    check(r["frontier_monotone"], "utility and action-leakage both fall as the response gate rises — a tradeoff curve")
    check(r["coupled_tradeoff"], "you cannot keep full utility at lower action-leakage — the action channel couples them")
    # a no-op is attributable: optimal abstention vs ignorance are distinguishable
    check(r["non_action_not_ignorance"], "a gated no-op is an attributable optimal abstention, distinguishable from ignorance")


def test_perception_intent_leakage_the_secret_is_the_policy():
    r = perc.intent.crucible()
    # the agent's goal/policy is recoverable from behaviour (inverse planning), even without the world secret
    check(r["intent_is_a_secret"], "the agent's goal is recoverable from behaviour — intent leakage I(G;A) > 0")
    check(r["full_policy_recovered"], "accumulated behaviour recovers the WHOLE policy (I(G;behaviour) = H(G))")
    check(r["intent_accumulates"], "intent leakage accumulates with observations (the cascade structure, on the optimizer)")
    check(r["single_observation_ambiguous"], "a single action is goal-ambiguous — inverse planning needs accumulation")
    # a behavioral-ambiguity defense caps intent leakage at a coupled cost
    check(r["ambiguity_caps_intent_leak"], "making goals behave alike caps intent leakage below H(G)")
    check(r["ambiguity_costs_distinctness"], "the ambiguity defense costs goal distinctness (two goals become identical) — a coupled tradeoff")


def test_perception_consistency_behavior_underdetermines_cause():
    r = perc.consistency.crucible()
    # distinct mechanisms emit identical behaviour — purposeful adaptation vs unintended drift collide
    check(r["adaptation_drift_collide"], "adaptation and drift emit the identical trajectory (distinct causes, same behaviour)")
    check(r["distinct_causes_identical_behavior"], "at least one pair of distinct causes is behaviorally indistinguishable")
    check(r["cause_underdetermined"], "I(cause; behaviour) < H(cause) — behaviour does not determine its own cause")
    check(r["change_is_ambiguous"], "a single 'behaviour changed' signal is shared by most causes — it attributes nothing")
    check(r["needs_attestation_not_observation"], "separating the causes needs attestation of the transformation, not more behaviour")


def test_perception_identifiability_is_there_a_stable_generator():
    r = perc.identifiability.crucible()
    # the three regimes are exhibited
    check(r["identifiable_exists"], "a coherent agent is identifiable (exactly one stable generator fits)")
    check(r["ambiguous_exists"], "behaviour observed only where two generators agree is ambiguous")
    check(r["non_identifiable_exists"], "a rule outside the observer's class is non-identifiable (none fit)")
    # the identity trap and its honest limit
    check(r["coherent_adaptive_indistinguishable_from_generatorless"], "a coherent adaptive agent and a generatorless sequence get the same verdict — opacity ≠ privacy")
    check(r["non_identifiability_is_class_relative"], "'non-identifiable' is relative to the observer's generator class — enriching it identifies the agent (M21)")
    check(r["antipolicy_useful"] and r["antipolicy_unpredictable"], "the anti-policy stays useful while confirming zero generators — usefulness − predictability")
    # the noise floor: 'become noise' relocates the secret to the stochastic character, it does not remove it
    check(r["noise_character_recoverable"], "even when the only invariant is noise, the observer recovers the generator's character (I(N;behaviour) > 0)")
    check(r["secret_relocated_not_eliminated"], "becoming noise relocates the secret from goal to stochastic character — noise ≠ ignorance")


def test_perception_substrate_generator_leaks_through_residue():
    r = perc.substrate.crucible()
    # signal privacy != generator privacy: the encrypted output hides content, the residue exposes the machine
    check(r["signal_hidden"], "the encrypted output channel leaks nothing about the generator (I(G;content)=0)")
    check(r["generator_leaks_via_residue"], "a physical residue channel (power) leaks the generator (I(G;power)>0)")
    check(r["signal_privacy_neq_generator_privacy"], "hiding the content is not hiding the machine — signal privacy != generator privacy")
    # a sensor-fusion adversary recovers more than any single channel
    check(r["fusion_exceeds_single"], "fusing power+timing recovers more than either channel alone")
    check(r["fusion_recovers_full_generator"], "sensor fusion recovers the whole generator")
    # leakage is a physical capacity curve, monotone in sensor access
    check(r["capacity_monotone"], "L(C_sensors) is monotone in which channels the observer physically has")
    # unobserved != unknown: recovery 0 with no channel is a missing channel, not a missing/absent generator
    check(r["unobserved_not_unknown"], "with no residue channel recovery is 0 though the generator is determined — unobserved != unknown")


def test_perception_adaptation_provenance_interface_not_truth():
    r = perc.adaptation.crucible()
    # adaptation is detectable: the observer can infer it caused a different interface trajectory
    check(r["adaptation_changes_view"], "the view differs per observer (the system adapts its projection)")
    check(r["adaptation_detectable"], "the adaptation is detectable — I(observer; view) > 0")
    # but interface adaptation leaves CORE byte-identical — 'I adapted your interface, not my truth'
    check(r["core_hash_independent_of_observer"], "the CORE hash is identical across observers (the cardinal invariant holds under adaptation)")
    check(r["self_change_breaks_core"], "a self-change (generator mutation) breaks core invariance")
    # the distinguishability point: view alone is ambiguous; only the attestation separates the two
    check(r["view_alone_ambiguous"], "from the view alone, interface-adaptation and self-change both look like 'behaviour changed'")
    check(r["attestation_distinguishes"], "only a CORE-invariance attestation distinguishes 'changed itself' from 'changed what it showed'")
    # observer-relative != observer-controlled, and every transition has an attributable boundary
    check(r["observer_relative_not_controlled"], "the observer selects the projection but does not author the core — observer-relative ≠ observer-controlled")
    check(r["provenance_attributable"], "every transition carries provenance: what changed / why / what did NOT change (core, attested)")


def test_perception_operators_separation_is_the_artifact():
    r = perc.operators.crucible()
    # holding the observer fixed, the projection moves leakage; holding the projection fixed, the observer does
    check(r["projection_matters"], "with F and A_C fixed, the projection Π moves leakage (raw vs coarse)")
    check(r["observer_matters"], "with F and Π fixed, the observer class A_C moves leakage (marginal vs full)")
    check(r["leakage_is_joint"], "leakage is L(Π, A_C) jointly — never a property of one operator alone")
    # the dynamics is independent of the projection — changing Π does not change the generator (CORE ⟂ VIEW)
    check(r["F_independent_of_projection"], "the world trajectory is identical regardless of Π — F is independent of the projection")
    check(r["memory_accumulates"], "the memory operator M accumulates the trajectory")
    # the separation localizes the source of every result
    check(r["raw_full"] == 3.0 and r["coarse_marginal"] == 2.0, "the operators reproduce the expected per-configuration leakage")


def test_perception_confounder_generator_is_the_invariant():
    r = perc.confounder.crucible()
    # within one context the generator and a confounder are indistinguishable
    check(r["single_context_ambiguous"], "in one context the generator and a confounder both fit perfectly — indistinguishable")
    # across contexts only the generator survives — it is the cross-context invariant
    check(r["context_variation_identifies_generator"], "across contexts only the causal rule (the generator) stays consistent")
    check(r["generator_is_the_invariant"], "the generator is the invariant across context — everything else dissolves")
    # the confounder fits in-context and fails across; higher capacity overfits it
    check(r["confounder_fits_in_context"], "the confounder predicts perfectly in its own context")
    check(r["confounder_fails_across"], "the confounder's accuracy collapses across contexts")
    check(r["capacity_overfits_confounder"], "a higher-capacity observer overfits the confounder — better in-context, worse cross-context (high capacity, low causal identifiability)")
    # separation requires context variation
    check(r["separation_requires_context_variation"], "separating generator from confounder requires >=2 contexts — one cannot do it")


def test_perception_ghost_invariance_ghost_is_not_truth():
    r = perc.ghost_invariance.crucible()
    # the ghost contains more than the generator
    check(r["ghost_has_nongenerator"], "the ghost contains a non-generator component")
    # the invariant ghost component (survives the projection change) is the generator candidate
    check(r["invariant_ghost_is_generator"], "the ghost component present under every projection is the generator candidate")
    check(r["variant_is_projection_artifact"], "the ghost component whose presence depends on the projection is an artifact — the observer's shadow")
    # necessity: g is necessary, a is contingent
    check(r["g_necessary"], "removing the generator component changes the F trajectory (necessary)")
    check(r["a_contingent"], "removing the artifact component changes nothing (contingent)")
    # Generator = invariant necessity; confounder = invariant-looking contingency
    check(r["generator_invariant_and_necessary"], "the generator is both invariant-in-ghost and necessary")
    check(r["artifact_neither_necessary_nor_invariant"], "the artifact is neither — a ghost is not automatically a hidden truth")


def test_perception_attribution_ghost_is_a_candidate_set():
    r = perc.attribution.crucible()
    # the ghost decomposes into G_F (generator) and G_C (confounder/artifact) — a partition, not a truth
    check(r["ghost_is_candidate_set"], "the ghost is a candidate set of multiple components, not a single hidden truth")
    check(r["decomposition_partitions"], "the ghost decomposes into G_F and G_C — a clean partition")
    check(r["G_F_is_generator_only"], "G_F (invariant ∧ necessary) is the generator component alone")
    # the decisive case: invariance alone over-attributes; a stable artifact is invariant yet lands in G_C
    check(r["stable_artifact_is_invariant"], "a stable artifact is invariant across every projection")
    check(r["stable_artifact_attributed_to_GC"], "yet the stable artifact is attributed to G_C (it is not necessary)")
    check(r["invariance_alone_overattributes"], "invariance alone over-attributes — it would keep the stable artifact")
    check(r["ever_hidden_is_not_causal"], "two distinct questions: the stable artifact was ever-hidden (Q1 yes) but is not causal (Q2 no)")
    check(r["both_tests_required"], "G_F = invariant ∧ necessary; both tests are required, neither alone — stable ≠ causal")
    # projection-relative artifact, and the hash limitation
    check(r["projection_artifact_is_variant"], "a projection-relative component is the variant artifact in G_C")
    check(r["integrity_is_reproducibility_not_validity"], "the hash binds reproducibility, not causal validity — it cannot tell G_F from G_C")


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("  ok  %s" % name)
    print("\n%d checks passed." % _n)


if __name__ == "__main__":
    main()
