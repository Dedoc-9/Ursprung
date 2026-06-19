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


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("  ok  %s" % name)
    print("\n%d checks passed." % _n)


if __name__ == "__main__":
    main()
