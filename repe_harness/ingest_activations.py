#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""ingest_activations.py — turn REAL token activations into the real audit->Grounded path (Lever A).

Replaces synthetic distributions with activations extracted from a real open-weight model, on CPU or an AMD
iGPU (no CUDA required). It produces your FIRST real-model number: held-out **probe AUROC**. Then it discretises
`(label, probe-score, confounder = token-length)` and runs the REAL `weltwerk/verify/residual_channel.audit` ->
a real verdict on YOUR probe direction; a mis-specification-stable channel grounds a steer via ChannelEstablished.

TWO-STATUS RULE.
- Apparatus: `--selftest` (GPU-free; numpy + the real weltwerk audit on SYNTHETIC activations) verifies the
  ingestion+audit chain recovers a planted signal AND rejects a length-confounder *even when raw AUROC is fooled*.
- Real-model number: `--extract` on your weights (needs torch) — yours to run. This file asserts no model number.

DEVICE. `pick_device()` returns 'cuda' when torch sees a CUDA/ROCm-HIP device (AMD ROCm-on-Windows presents as
'cuda'), else 'cpu'. The Radeon 890M path is UNVERIFIED for the Z2 Extreme (AMD's Windows PyTorch lists Ryzen AI
300 / AI Max — same silicon, not named); CPU is the reliable fallback. Use a SMALL instruct model (1-3B), not 8B.

GRADE:         apparatus VERIFIED when --selftest passes.
DOES_NOT_SHOW: safety (SPECULATIVE). A real probe AUROC on the shipped NEUTRAL data shows extraction+probe work
               on a real model — NOT that the model is safer. Safety needs `phase4.grade()=="MEASURED"` on
               held-out attacks with a real harmful/benign set. `apparatus != safety`; `AUROC != channel`.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import numpy as np


def _find_root():
    here = os.path.dirname(os.path.abspath(__file__)); d = here
    while True:
        if any(os.path.exists(os.path.join(d, m)) for m in (".git", "method.md", "AGENTS.md")):
            return d
        p = os.path.dirname(d)
        if p == d:
            return os.path.dirname(here)
        d = p


ROOT = os.environ.get("URSPRUNG_ROOT") or _find_root()
sys.path.insert(0, os.path.join(ROOT, "repe_harness"))
sys.path.insert(0, os.path.join(ROOT, "weltwerk", "verify"))

from phase1_probe import fit_probe, probe_scores, steering_vector, auroc   # noqa: E402  (unique to repe_harness)
try:
    from residual_channel import audit                                     # noqa: E402
    from epistemic_types import Grounded, ChannelEstablished, UngroundedError  # noqa: E402
    _KERNEL_OK, _KERNEL_ERR = True, None
except Exception as e:
    _KERNEL_OK, _KERNEL_ERR = False, e


def pick_device(pref="auto"):
    """'cuda' if torch sees a CUDA/ROCm-HIP device (ROCm-on-Windows presents as 'cuda'), else 'cpu'."""
    if pref != "auto":
        return pref
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def extract_activations(model_name, texts, layers, device="auto", batch_size=8, max_tokens=64):
    """Batched last-token hidden-state extraction (fixes the no-batching OOM gap). Lazy torch/transformers.
    Returns {layer: np.ndarray(n, d)}. REAL path — needs torch; NOT exercised by --selftest."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    dev = pick_device(device)
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    # transformers 4.x/5.x-safe: no `torch_dtype`/`dtype` kwarg (renamed across versions); force float32 on CPU.
    model = AutoModelForCausalLM.from_pretrained(model_name).to(dev).eval()
    if dev == "cpu":
        model = model.float()
    out = {int(L): [] for L in layers}
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            enc = tok(texts[i:i + batch_size], return_tensors="pt", padding=True,
                      truncation=True, max_length=max_tokens).to(dev)
            hs = model(**enc, output_hidden_states=True).hidden_states   # (n_layers+1) x (B, T, d)
            last = enc["attention_mask"].sum(1) - 1               # last non-pad index per row
            for L in layers:
                h = hs[int(L)]
                rows = h[torch.arange(h.size(0)), last]           # (B, d) last-token states
                out[int(L)].append(rows.float().cpu().numpy())
    return {L: np.concatenate(v, 0) for L, v in out.items()}


def _discretize(vals, k):
    vals = np.asarray(vals, float)
    if k <= 1:
        return [0] * len(vals)
    qs = np.quantile(vals, np.linspace(0, 1, k + 1)[1:-1])
    return np.digitize(vals, qs).tolist()


def build_samples(labels, scores, confound, n_bins=4, n_z=3):
    """Discrete (x=label, y=binned probe-score, z=binned confounder) triples for residual_channel.audit."""
    yb = _discretize(scores, n_bins)
    zb = _discretize(confound, n_z)
    return [(int(a), int(b), int(c)) for a, b, c in zip(labels, yb, zb)]


def ingest(acts, labels, confound, *, layer=None, test_frac=0.3, seed=0, reps=200, n_bins=4, n_z=3):
    """Activations -> held-out probe AUROC + REAL audit verdict + (if channel) a Grounded steer. Panel out."""
    if not _KERNEL_OK:
        raise RuntimeError(f"weltwerk kernel fail-closed: {_KERNEL_ERR}")
    X = acts if layer is None else acts[layer]
    X = np.asarray(X, float); y = np.asarray(labels); c = np.asarray(confound, float)
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(y)); cut = int(len(y) * (1 - test_frac))
    tr, te = idx[:cut], idx[cut:]
    w, b, mu, sd = fit_probe(X[tr], y[tr])
    s_te = probe_scores(X[te], w, b, mu, sd)
    probe_auroc = float(auroc(s_te, y[te]))
    steer = steering_vector(X[tr], y[tr])
    coarsen = (lambda smp: [(a, b2, z // 2) for a, b2, z in smp],)
    r = audit(build_samples(y[te], s_te, c[te], n_bins=n_bins, n_z=n_z), reps=reps, seed=seed, misspec_fns=coarsen)
    panel = {"probe_auroc": round(probe_auroc, 4), "audit_decision": r.decision,
             "audit_cmi": round(r.cmi, 4), "audit_z": round(r.z_score, 1),
             "channel_grounded": r.decision == "RESIDUAL_MISSPEC_STABLE", "n_test": int(len(te))}
    if panel["channel_grounded"]:
        g = Grounded.ground(steer, ChannelEstablished(r))
        panel["grounded_steer_dim"] = int(len(g.value))
    return panel


def run_extract(model_name, data_path, layers, device="auto", batch_size=8, test_frac=0.3, seed=0):
    """REAL path (needs torch): extract activations from `model_name` over the JSONL, then ingest per layer."""
    rows = [json.loads(l) for l in open(data_path, encoding="utf-8") if l.strip()]
    texts = [r["text"] for r in rows]; labels = [int(r["label"]) for r in rows]
    confound = [len(t) for t in texts]                     # confounder Z = prompt length (chars)
    acts = extract_activations(model_name, texts, layers, device=device, batch_size=batch_size)
    print(f"[extract] model={model_name} device={pick_device(device)} n={len(texts)} layers={list(acts)}")
    print("[note] shipped data is NEUTRAL (cooking/math) -> AUROC here is a real number, NOT a safety claim.")
    for L in acts:
        p = ingest(acts, labels, confound, layer=L, test_frac=test_frac, seed=seed)
        print(f"[layer {L}] {p}")
    return 0


def _synth(kind, n=400, d=32, seed=0):
    rng = np.random.RandomState(seed); direction = rng.randn(d)
    if kind == "planted":                                  # label encoded; confounder (length) INDEPENDENT
        y = rng.randint(0, 2, n)
        length = rng.randint(5, 60, n)
        X = y[:, None] * direction * 3.0 + rng.randn(n, d)
        return X, y, length, 3
    # confounded: X encodes a continuous confounder Z; label ~ logistic(Z) (correlated, independent flips);
    # X carries NO label signal beyond Z -> a probe separates on Z, so the audit must REJECT it.
    nn, dd = 2000, 8
    rng = np.random.RandomState(seed); direction = rng.randn(dd)
    Z = rng.normal(0, 1, nn)
    y = (rng.rand(nn) < 1.0 / (1.0 + np.exp(-1.4 * Z))).astype(int)
    X = Z[:, None] * direction * 2.0 + rng.randn(nn, dd) * 0.8
    return X, y, Z, 4


def selftest() -> int:
    if not _KERNEL_OK:
        print(f"[selftest] FAIL — weltwerk/verify kernel not importable: {_KERNEL_ERR}")
        return 1
    checks = []
    Xp, yp, cp, _ = _synth("planted", seed=0)
    pl = ingest(Xp, yp, cp, seed=0, n_z=3)
    checks.append(("planted: probe separates (AUROC>0.85)", pl["probe_auroc"] > 0.85))
    checks.append(("planted: audit -> RESIDUAL_MISSPEC_STABLE", pl["audit_decision"] == "RESIDUAL_MISSPEC_STABLE"))
    checks.append(("planted: channel grounds a steer", pl["channel_grounded"] and "grounded_steer_dim" in pl))

    Xc, yc, cc, nz = _synth("confounded", seed=1)
    cf = ingest(Xc, yc, cc, seed=1, n_z=nz)
    checks.append(("confounded: raw AUROC is FOOLED high (>0.75)", cf["probe_auroc"] > 0.75))
    checks.append(("confounded: audit -> CONSISTENT_WITH_NULL", cf["audit_decision"] == "CONSISTENT_WITH_NULL"))
    checks.append(("confounded: NOT grounded (firewall bites)", cf["channel_grounded"] is False))

    s = build_samples([0, 1, 1], [0.1, 0.9, 0.5], [10, 20, 30], n_bins=2, n_z=2)
    checks.append(("build_samples -> discrete triples", len(s) == 3 and all(len(t) == 3 for t in s)))
    checks.append(("pick_device returns a device string", pick_device() in {"cpu", "cuda"}))

    ok = all(o for _, o in checks); npass = sum(1 for _, o in checks if o)
    for label, o in checks:
        print(f"[selftest] {label:46s}: {o}")
    print(f"[selftest] {'PASS %d/%d - ingestion+audit chain valid' % (npass, len(checks)) if ok else 'FAIL'}")
    print("[frame]    AUROC alone is fooled by a length-confounder; the REAL audit gates it. AUROC != channel.")
    print("[grade]    apparatus VERIFIED (synthetic activations). DOES_NOT_SHOW: safety — run --extract on your")
    print("[bound]    weights for the real AUROC; only phase4 on held-out attacks earns MEASURED. apparatus != safety.")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="ingest REAL activations -> probe AUROC -> real audit -> Grounded (Lever A)")
    ap.add_argument("--selftest", action="store_true", help="GPU-free apparatus test (synthetic activations)")
    ap.add_argument("--extract", action="store_true", help="REAL path: extract from --model over --data (needs torch)")
    ap.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "contrastive_example.jsonl"))
    ap.add_argument("--layers", default="6,9,12")
    ap.add_argument("--device", default="auto"); ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--test-frac", type=float, default=0.3)
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    if a.extract:
        layers = [int(x) for x in a.layers.split(",") if x.strip()]
        raise SystemExit(run_extract(a.model, a.data, layers, device=a.device, batch_size=a.batch_size, test_frac=a.test_frac))
    print("run --selftest (GPU-free) or --extract --model <small-instruct> --data <jsonl> --device auto")
    if not _KERNEL_OK:
        print(f"WARNING: weltwerk kernel not importable now: {_KERNEL_ERR}")


if __name__ == "__main__":
    main()
