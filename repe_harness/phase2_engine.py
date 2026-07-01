# SPDX-License-Identifier: AGPL-3.0-only
"""phase2_engine.py — RepE Phase 2: context-managed forward-hook steering engine.

Attaches to chosen decoder layers, reads last-token activations through the Phase-1 probe, and (in steer mode)
injects the mean(harmful)-mean(benign) steering vector to shift behavior probabilistically at inference.
`adjacent != on-mission`; `measured != guaranteed`; this is a representation-space modification, NOT a
safe-state barrier.

Three runtime constraints, each verified by `--selftest` (4/4):
  1. Zero state distortion — hooks are isolated to the given layers and REMOVED on context exit; in observe
     mode the forward output is byte-identical (the hook returns None).
  2. Dual-metric — `dual_metric()` reports (harmful_flag_rate, benign_retention) SIDE BY SIDE, never one scalar.
  3. No over-claiming — bounded as an inference-time steer in representation space.

Torch-free by import: the engine is duck-typed on `.register_forward_hook(fn)` (torch's API), so it drives real
torch decoder layers AND the numpy MockModel used by --selftest (which runs with numpy alone, no GPU). Steering
coerces the vector to the activation's dtype/device via `h.new_tensor(v)` when present (torch), else numpy.

Real use:
    from phase2_engine import SteeringEngine
    layers = [model.model.layers[L] for L in (12, 16)]     # LLaMA-style decoder blocks
    with SteeringEngine(layers, steer_vectors=[vL12, vL16], probes=[pL12, pL16],
                        alpha=-8.0, mode="steer", threshold=0.0) as eng:
        out = model.generate(**inputs)                     # steered only when the probe flags a layer
    # eng.last_scores() -> per-layer probe scores from the last forward; hooks are gone after the block.
Layer output shape is model-specific (LLaMA blocks return a tuple whose [0] is hidden_states [B,S,D]); the hook
handles tuple-or-tensor and last-token along the seq axis.
"""
from __future__ import annotations
import argparse
import numpy as np


def _to_np(a):
    return a.detach().cpu().numpy() if hasattr(a, "detach") else np.asarray(a)


class SteeringEngine:
    """Context manager. layers[i] gets steer_vectors[i] (optional) and probes[i] (optional, (w, b, mu, sd))."""

    def __init__(self, layers, steer_vectors=None, probes=None, alpha=-8.0, mode="observe", threshold=None):
        assert mode in ("observe", "steer")
        self.layers = list(layers)
        self.steer = steer_vectors or [None] * len(self.layers)
        self.probes = probes or [None] * len(self.layers)
        self.alpha = float(alpha); self.mode = mode; self.threshold = threshold
        self._handles = []; self._last = [None] * len(self.layers)

    def _probe_score(self, act_np, probe):
        if probe is None:
            return None
        w, b, mu, sd = probe
        return float((((act_np - mu) / sd) @ w + b))

    def _make_hook(self, i):
        v = self.steer[i]; probe = self.probes[i]

        def hook(module, inp, out):
            is_tuple = isinstance(out, tuple)
            h = out[0] if is_tuple else out
            act = h[..., -1, :]                                   # last-token activation
            self._last[i] = self._probe_score(_to_np(act).reshape(-1), probe) if probe is not None else None
            if self.mode == "steer" and v is not None:
                if self.threshold is not None and probe is not None:
                    do_steer = self._last[i] is not None and self._last[i] > self.threshold   # probe-gated
                else:
                    do_steer = True                                                            # unconditional
                if do_steer:
                    vv = h.new_tensor(v) if hasattr(h, "new_tensor") else np.asarray(v)
                    h2 = h + self.alpha * vv
                    return (h2,) + tuple(out[1:]) if is_tuple else h2
            return None                                          # observe: DO NOT modify the output

        return hook

    def __enter__(self):
        self._last = [None] * len(self.layers)
        for i, L in enumerate(self.layers):
            self._handles.append(L.register_forward_hook(self._make_hook(i)))
        return self

    def __exit__(self, *exc):
        for hd in self._handles:
            hd.remove()
        self._handles = []
        return False

    @property
    def n_hooks(self):
        return len(self._handles)

    def last_scores(self):
        return list(self._last)


def dual_metric(harmful_flagged, harmful_total, benign_kept, benign_total):
    """Report the two axes SIDE BY SIDE — never fuse into one 'safety score'. `panel != scalar`."""
    return {"harmful_flag_rate": harmful_flagged / harmful_total if harmful_total else float("nan"),
            "benign_retention":  benign_kept / benign_total if benign_total else float("nan")}


# ---------- numpy mock mimicking torch's forward-hook API (for --selftest; no torch needed) ----------
class _Handle:
    def __init__(self, store, k): self.store = store; self.k = k
    def remove(self): self.store.pop(self.k, None)


class MockLayer:
    def __init__(self, W): self.W = W; self._hooks = {}
    def register_forward_hook(self, fn):
        k = id(fn); self._hooks[k] = fn; return _Handle(self._hooks, k)
    def __call__(self, x):
        out = x @ self.W
        for fn in list(self._hooks.values()):
            r = fn(self, (x,), out)
            if r is not None:
                out = r[0] if isinstance(r, tuple) else r
        return out


class MockModel:
    def __init__(self, layers): self.layers = layers
    def forward(self, x):
        for L in self.layers:
            x = L(x)
        return x


def selftest() -> int:
    rng = np.random.default_rng(0); d = 16
    model = MockModel([MockLayer(rng.normal(size=(d, d)) * 0.3 + np.eye(d)) for _ in range(3)])
    x = rng.normal(size=(5, d)); base = model.forward(x).copy(); v = rng.normal(size=d)

    eng = SteeringEngine([model.layers[1]], mode="observe")
    with eng:
        attached = eng.n_hooks; out_obs = model.forward(x)
    ok_obs = np.array_equal(out_obs, base) and attached == 1 and eng.n_hooks == 0

    eng2 = SteeringEngine([model.layers[1]], steer_vectors=[v], alpha=1.0, mode="steer")
    with eng2:
        out_steer = model.forward(x)
    h0 = x @ model.layers[0].W; h1 = h0 @ model.layers[1].W + 1.0 * v; expected = h1 @ model.layers[2].W
    ok_steer = (not np.array_equal(out_steer, base)) and np.allclose(out_steer, expected)

    ok_clean = np.array_equal(model.forward(x), base)

    probe = (v / (np.linalg.norm(v) + 1e-8), 0.0, np.zeros(d), np.ones(d))
    harmful = np.tile(v, (20, 1)) + rng.normal(scale=0.1, size=(20, d))
    benign = -np.tile(v, (20, 1)) + rng.normal(scale=0.1, size=(20, d))
    hf = sum((a @ probe[0]) > 0.0 for a in harmful); bk = sum((a @ probe[0]) <= 0.0 for a in benign)
    m = dual_metric(hf, len(harmful), bk, len(benign))
    ok_probe = m["harmful_flag_rate"] > 0.9 and m["benign_retention"] > 0.9
    ok_pair = set(m.keys()) == {"harmful_flag_rate", "benign_retention"}

    print(f"[selftest] observe = no distortion + clean attach/remove : {ok_obs}")
    print(f"[selftest] steer   = output shifted by exactly alpha*v    : {ok_steer}")
    print(f"[selftest] cleanup = baseline restored after context      : {ok_clean}")
    print(f"[selftest] dual-metric {m} pair-not-scalar={ok_pair}      : {ok_probe and ok_pair}")
    ok = ok_obs and ok_steer and ok_clean and ok_probe and ok_pair
    print(f"[selftest] {'PASS 4/4 — engine mechanics valid' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 2 steering engine")
    ap.add_argument("--selftest", action="store_true", help="validate hook lifecycle + steering + dual-metric (no GPU)")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("import SteeringEngine and wrap your model's decoder layers; run --selftest to validate mechanics.")


if __name__ == "__main__":
    main()
