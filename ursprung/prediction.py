# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/prediction.py — a Dini-style prediction OBSERVER (surprise → attention, never authority).

Dini-style logic helps estimate WHERE the current representation is likely to lose information, WHERE the
model is surprised, and WHERE observation effort should increase. It is an observer/prediction layer that
feeds the ALLOCATOR — it is NOT an authority layer.

    prediction creates expectations
    determinism preserves the experiment
    ghosts reveal where the model and observation diverge
    — none of them alone define reality

The mechanism is the workbench ghost, applied to the render/observation stream:

    ghost  G⁺ = max(0, observed − predicted)        (rectified: surprise can only RAISE attention)

What this says, and what it must never say:
    SAYS:        "your model's coverage of this region is weak / this frame surprised the predictor."
    DOES NOT SAY: "this object is now important."   ← that decision belongs to the ALLOCATOR policy.

Applied to temporal rendering: predict frame(t+1) ≈ extrapolate(frame(t-1), frame(t)); where the error
grows, an ALLOCATOR may raise sampling, ray budget, LOD, temporal-history checks, or validation. The world
is NEVER rewritten because a prediction failed. Applied to physics the same shape holds — an unexpected
deviation from the expected trajectory is recorded as a ghost (category causal/numerical/model-boundary,
measured confidence, action = allocate investigation), never as a "truth violation."

This is the producer-agnostic novelty/surprise seam (the workbench treats `dini`'s hyperbolic novelty as
ONE producer of this signal; frame prediction error is another). It emits an attention hint; an ALLOCATOR
consumes it.

CLASSIFICATION: OBSERVER (mutates_core=False). It predicts, measures surprise, and reports; it changes
nothing committed and decides no importance.

HONEST BOUND: a low ghost is not proof the model is right — only that this predictor was not surprised.
Surprise correlates with weak coverage; it does not prove a cause (integrity ≠ truth).
"""
from __future__ import annotations

from . import ghost_report as gr


def _sprite_map(frame):
    """{id: (x, y, size)} for visible sprites; invisible/behind-camera sprites are omitted (no signal)."""
    out = {}
    for s in frame.sprites:
        if s.get("visible") and s["x"] is not None:
            out[s["id"]] = (s["x"], s["y"], s["size"])
    return out


def predict(prev_frame, cur_frame):
    """Constant-velocity extrapolation in screen space: predicted = cur + (cur - prev). The cheapest honest
    predictor; a smarter one only changes the residual, not the law. Returns {id: (x, y, size)}."""
    p, c = _sprite_map(prev_frame), _sprite_map(cur_frame)
    pred = {}
    for sid, (cx, cy, cs) in c.items():
        if sid in p:
            px, py, ps = p[sid]
            pred[sid] = (2 * cx - px, 2 * cy - py, 2 * cs - ps)
        else:
            pred[sid] = (cx, cy, cs)   # newly visible: no motion history → predict no change
    return pred


def surprise(predicted, observed_frame):
    """Per-id rectified surprise G⁺ = max(0, ‖observed − predicted‖). Screen-space distance plus size delta.
    Returns {id: G⁺} — only ids present in both predicted and observed contribute."""
    obs = _sprite_map(observed_frame)
    out = {}
    for sid, (ox, oy, osz) in obs.items():
        if sid not in predicted:
            continue
        px, py, psz = predicted[sid]
        err = ((ox - px) ** 2 + (oy - py) ** 2) ** 0.5 + abs(osz - psz)
        out[sid] = max(0.0, err)        # rectified: surprise only raises attention
    return out


class PredictionReport:
    """Surprise turned into an attention HINT for an ALLOCATOR. Importance is the ALLOCATOR's call, not this."""
    __slots__ = ("attention_hint", "ghosts", "note")

    def __init__(self, attention_hint, ghosts, note):
        self.attention_hint = attention_hint    # {id: G⁺} — where coverage looks weak / model is surprised
        self.ghosts = ghosts                     # list[Ghost] for the notably-surprising ids
        self.note = note

    def hottest(self, k=3):
        return sorted(self.attention_hint.items(), key=lambda kv: kv[1], reverse=True)[:k]

    def __repr__(self):
        return "<PredictionReport ids=%d ghosts=%d>" % (len(self.attention_hint), len(self.ghosts))


def observe(prev_frame, cur_frame, observed_next_frame, ghost_threshold=2.0):
    """The full predict → observe → ghost step over three consecutive VIEW frames.

    Returns a PredictionReport whose attention_hint an ALLOCATOR may use to raise sampling/ray budget/LOD/
    validation where the predictor was surprised. It NEVER rewrites the world and NEVER asserts importance.
    """
    pred = predict(prev_frame, cur_frame)
    hint = surprise(pred, observed_next_frame)
    ghosts = []
    for sid, g in hint.items():
        if g >= ghost_threshold:
            ghosts.append(gr.Ghost(
                gr.TEMPORAL, gr.MODEL_LIMIT,
                "predictor surprised at '%s' (G+=%.2f): model coverage weak here — allocate effort, "
                "not authority" % (sid, g), magnitude=round(g, 4)))
    note = ("attention hint for an ALLOCATOR: where coverage looks weak / the model was surprised. "
            "It says nothing about importance and never rewrites the world.")
    return PredictionReport(hint, ghosts, note)


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("prediction", OBSERVER, mutates_core=False,
                          note="Dini-style predict→observe→ghost; surprise feeds allocation, never authority")
    except LayerViolation:
        pass
