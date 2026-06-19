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


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("  ok  %s" % name)
    print("\n%d checks passed." % _n)


if __name__ == "__main__":
    main()