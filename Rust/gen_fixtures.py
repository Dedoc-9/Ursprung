# SPDX-License-Identifier: AGPL-3.0-only
"""
gen_fixtures.py — regenerate the cross-language differential-test fixtures from the PYTHON reference.

The fixtures in tests/fixtures/ are the ground truth the Rust `residual_channel` port is checked against:
they carry Python's MI, CMI and DECISION on the planted null/channel generators. The Rust test
(tests/differential_residual.rs) recomputes MI/CMI on the same samples (RNG-free ⇒ must match to 1e-9) and
asserts the audit decision matches Python.

    python gen_fixtures.py            # rewrites tests/fixtures/{null,channel}.tsv

`decisions match, floats need not`: MI/CMI are RNG-free and compared for value-parity; the shuffle-null
moments depend on CPython's RNG and are NOT expected to match the Rust LCG — only the decision is.
"""
from __future__ import annotations

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# residual_channel lives in the repo's weltwerk/verify (one level up from Rust/)
sys.path.insert(0, os.path.join(HERE, "..", "weltwerk", "verify"))
from residual_channel import audit, demo_gen_null, demo_gen_channel  # noqa: E402

N, K, REPS, SEED = 800, 3, 200, 0


def fixture_text(kind: str, samples, r) -> str:
    body = "".join(f"{x}{y}{z}" for x, y, z in samples)  # each symbol in 0..k-1 -> one digit
    sha = hashlib.sha256(body.encode()).hexdigest()
    header = (f"# kind={kind} decision={r.decision} n={r.n} k={K} reps={REPS} seed={SEED} "
              f"mi={r.mi:.12f} cmi={r.cmi:.12f} null_mean={r.null_mean:.12f} "
              f"null_std={r.null_std:.12f} null_max={r.null_max:.12f} sha256={sha}")
    return header + "\n" + body + "\n"


def main():
    out_dir = os.path.join(HERE, "tests", "fixtures")
    os.makedirs(out_dir, exist_ok=True)
    for kind, samples in (("null", demo_gen_null(N, K, seed=1)),
                          ("channel", demo_gen_channel(N, K, seed=2))):
        r = audit(samples, reps=REPS, seed=SEED)
        with open(os.path.join(out_dir, f"{kind}.tsv"), "w") as f:
            f.write(fixture_text(kind, samples, r))
        print(f"  wrote {kind}.tsv  decision={r.decision} mi={r.mi:.6f} cmi={r.cmi:.6f}")
    print("  fixtures regenerated; Rust differential test asserts MI/CMI value-parity + decision-parity.")


if __name__ == "__main__":
    main()
