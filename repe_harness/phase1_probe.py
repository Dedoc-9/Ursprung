# SPDX-License-Identifier: AGPL-3.0-only
"""phase1_probe.py — RepE Phase 1: contrastive activation extraction, multi-layer linear probe, steering vectors.

Adjacent arc (`adjacent != on-mission`): an inference-time representation-engineering harness for open-weight
models — NOT part of the renderer/verification core. Anchored in RepE (Zou et al. 2023, arXiv:2310.01405) and
bounded by *No Red Lines*: this REDUCES harmful outputs probabilistically; it does NOT prove unsafe states
unreachable. `measured != guaranteed`.

Honest split of what is verified WHERE:
  * The falsifiable core (AUROC, logistic probe, steering vector) is PURE NUMPY and is self-tested on synthetic
    ground truth via `--selftest` (runs anywhere, no GPU). If that fails, the apparatus is broken.
  * The real-model activation extraction needs torch + transformers + weights and runs on YOUR machine
    (`--extract`). The held-out AUROC there is MEASURED only when you run it; this file never asserts it.

Deps: numpy always; torch + transformers lazy-imported only inside --extract.
"""
from __future__ import annotations
import argparse, json, os
import numpy as np


def auroc(scores, labels) -> float:
    """Mann-Whitney AUROC (rank-based). scores: floats; labels: {0,1}."""
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    concat = np.concatenate([neg, pos])
    order = np.argsort(concat, kind="mergesort")
    ranks = np.empty(order.size, float); ranks[order] = np.arange(1, order.size + 1)
    r_pos = ranks[neg.size:].sum()
    return float((r_pos - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))


def fit_probe(X, y, epochs=400, lr=0.1, l2=1e-3):
    """Logistic-regression probe by numpy gradient descent. Standardizes X. Returns (w, b, mu, sd)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    mu = X.mean(0); sd = X.std(0) + 1e-8; Xs = (X - mu) / sd
    n, d = Xs.shape; w = np.zeros(d); b = 0.0
    for _ in range(epochs):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xs @ w + b, -30, 30)))
        w -= lr * (Xs.T @ (p - y) / n + l2 * w); b -= lr * float((p - y).mean())
    return w, b, mu, sd


def probe_scores(X, w, b, mu, sd):
    return ((np.asarray(X, float) - mu) / sd) @ w + b


def steering_vector(X, y):
    X = np.asarray(X, float); y = np.asarray(y, int)
    return X[y == 1].mean(0) - X[y == 0].mean(0)   # mean(harmful) - mean(benign), per RepE


def split(n, frac=0.3, seed=0):
    idx = np.random.default_rng(seed).permutation(n); k = int(n * frac)
    return idx[k:], idx[:k]                          # (train, test)


def load_dataset(path):
    texts, labels = [], []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line); texts.append(r["text"]); labels.append(int(r["label"]))
    return texts, np.array(labels)


def extract_activations(model_name, texts, layers, device):
    """Last-token hidden state per requested decoder layer. Needs torch + transformers (lazy import)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype="auto", output_hidden_states=True).to(device).eval()
    feats = {L: [] for L in layers}
    with torch.no_grad():
        for t in texts:
            hs = model(**tok(t, return_tensors="pt").to(device)).hidden_states  # (emb, L1..Ln)
            for L in layers:
                feats[L].append(hs[L][0, -1].float().cpu().numpy())
    return {L: np.stack(v) for L, v in feats.items()}


def run_extract(a):
    texts, y = load_dataset(a.data)
    layers = [int(x) for x in a.layers.split(",")]
    acts = extract_activations(a.model, texts, layers, a.device)
    tr, te = split(len(y), a.test_frac, a.seed)
    os.makedirs(a.out, exist_ok=True)
    print(f"{'layer':>6} {'held-out AUROC':>16} {'n_train':>8} {'n_test':>7}")
    report = {}
    for L in layers:
        X = acts[L]
        w, b, mu, sd = fit_probe(X[tr], y[tr])
        au = auroc(probe_scores(X[te], w, b, mu, sd), y[te])
        np.save(os.path.join(a.out, f"probe_L{L}.npy"), np.concatenate([w, [b]]))
        np.save(os.path.join(a.out, f"steer_L{L}.npy"), steering_vector(X[tr], y[tr]))
        report[L] = au
        print(f"{L:>6} {au:>16.4f} {tr.size:>8} {te.size:>7}")
    json.dump({str(k): v for k, v in report.items()}, open(os.path.join(a.out, "auroc.json"), "w"), indent=2)
    best = max(report, key=report.get)
    print(f"\nbest layer L{best}: held-out AUROC={report[best]:.4f}  "
          f"[MEASURED on YOUR data+model; does_not_show downstream safety or robustness to unseen attacks]")


def selftest() -> int:
    """Validity-not-outcome: the math must recover a KNOWN-separable synthetic signal, align the steering
    vector with the true direction, and return ~0.5 on random labels (held-out). Fails loudly if broken."""
    rng = np.random.default_rng(0); d, n = 64, 200
    dirn = rng.normal(size=d); dirn /= np.linalg.norm(dirn)
    y = np.array([0] * n + [1] * n)
    # 4-sigma shift -> Bayes-optimal AUROC ~= 0.998, so a CORRECT probe clears 0.95 and a broken one can't.
    # (An earlier 2-sigma shift had Bayes ceiling ~0.92 < 0.95 — a test asserting an impossible outcome.)
    X = rng.normal(size=(2 * n, d)); X[n:] += 4.0 * dirn      # class 1 shifted along a known direction
    tr, te = split(2 * n, 0.3, 0)
    w, b, mu, sd = fit_probe(X[tr], y[tr]); a_sep = auroc(probe_scores(X[te], w, b, mu, sd), y[te])
    v = steering_vector(X[tr], y[tr]); cos = float(v @ dirn / (np.linalg.norm(v) * np.linalg.norm(dirn)))
    yr = rng.integers(0, 2, 2 * n)                            # noise control: labels carry no signal
    wr, br, mur, sdr = fit_probe(X[tr], yr[tr]); a_noise = auroc(probe_scores(X[te], wr, br, mur, sdr), yr[te])
    ok_sep, ok_cos, ok_noise = a_sep > 0.95, cos > 0.9, 0.35 < a_noise < 0.65
    print(f"[selftest] separable held-out AUROC = {a_sep:.3f}   (want > 0.95: {ok_sep})")
    print(f"[selftest] steering cos vs true dir = {cos:.3f}   (want > 0.9: {ok_cos})")
    print(f"[selftest] noise-control AUROC      = {a_noise:.3f}   (want ~0.5: {ok_noise})")
    ok = ok_sep and ok_cos and ok_noise
    print(f"[selftest] {'PASS 3/3 — apparatus valid (probe/AUROC/steering correct)' if ok else 'FAIL — apparatus broken'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 1 probe/steering extractor")
    ap.add_argument("--selftest", action="store_true", help="validate the math on synthetic ground truth (no GPU)")
    ap.add_argument("--extract", action="store_true", help="run activation extraction on a real model + dataset")
    ap.add_argument("--model", default="meta-llama/Meta-Llama-3-8B-Instruct")
    ap.add_argument("--data", default="data/contrastive_example.jsonl")
    ap.add_argument("--layers", default="8,12,16,20")
    ap.add_argument("--out", default="artifacts")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--test-frac", type=float, default=0.3, dest="test_frac")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    if a.extract:
        run_extract(a); return
    print("nothing to do — pass --selftest (validate apparatus) or --extract (run on your model + data)")


if __name__ == "__main__":
    main()
