# SPDX-License-Identifier: AGPL-3.0-only
"""
causal_field.py — the capstone VIEW: a space-time diagram where the theory draws its own picture.

The strongest thing the probes found is not the fork, the observer, or the allocator — it is the GAP
between Potential and Actual. `Potential ≫ Actual` ⇒ cheap; `Potential ≈ Actual` ⇒ expensive. No
mainstream engine shows that gap. This renders it.

A SPACE-TIME diagram: chunks on x, time flowing downward on y, every cell coloured by its causal class
at that tick — BLUE committed · GREEN potential cone · YELLOW allocated frontier · RED actual divergence.
The reachability cone becomes a literal green triangle; each dynamical regime writes its signature inside
it, fed by the REAL engines (no recomputation in the browser):

  diffusion (dissipative, λ<0) → a thin red diagonal trace inside a green triangle (actual ≪ potential)
  teleport  (ring + long edge)  → the green cone FORKS to a far region (potential explodes), red stays thin
  chaos     (CML, r=4.0, λ>0)   → red FLOODS the green triangle (actual → potential, the allocator dies)

Same engine, same correctness in all three; only the gap differs — and the difference is the regime.
VIEW reveals committed measurements; it does not define them.

Run:  PYTHONHASHSEED=0 python3 causal_field.py   → writes causal_field.html (open in a browser).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scale"))

from amplify import initial, perturb, run as cml_run, diverged           # noqa: E402
from cow_world import Edit, Rules, genesis                                # noqa: E402
from reachability_algebra import reflexive_ball                          # noqa: E402
from teleport import Topology, apply_edit, full_sim_traced               # noqa: E402

N, CS, H, SEED = 80, 8, 64, 0
EDIT_C = 20
EPS, R_CHAOS, DELTA, TAU = 0.25, 4.0, 1e-3, 1e-6
TELE_EDGE = (EDIT_C, EDIT_C + N // 2)

COLORS = "bgry"   # blue committed, green potential, yellow allocated, red actual


def _ring_adj() -> dict:
    return {c: ((c - 1) % N, (c + 1) % N) for c in range(N)}


def _frame(actual: set, potential: set, adj: dict) -> str:
    out = []
    for c in range(N):
        if c in actual:
            out.append("r")
        elif any(nb in actual for nb in adj[c]):
            out.append("y")          # allocated frontier (the pruned allocator must simulate these)
        elif c in potential:
            out.append("g")
        else:
            out.append("b")
    return "".join(out)


def _ecology_frames(topo: Topology) -> list:
    snap = genesis(N * CS, N, SEED)
    rules = Rules()
    a = full_sim_traced(snap, topo, rules, SEED, H)[0]
    snap_b, rules_b, _ = apply_edit(snap, rules, Edit("cull_pred_chunk", chunk=EDIT_C))
    b = full_sim_traced(snap_b, topo, rules_b, SEED, H)[0]
    frames = []
    for t in range(H + 1):
        actual = {c for c in range(N) if a[t][c] != b[t][c]}
        pot = reflexive_ball(topo.adj, {EDIT_C}, t)
        frames.append(_frame(actual, pot, topo.adj))
    return frames


def _chaos_frames() -> list:
    adj = _ring_adj()
    s0 = initial(N)
    a = cml_run(s0, R_CHAOS, EPS, H)
    b = cml_run(perturb(s0, EDIT_C, DELTA), R_CHAOS, EPS, H)
    frames = []
    for t in range(H + 1):
        actual = set(diverged(a[t], b[t], TAU))
        pot = reflexive_ball(adj, {EDIT_C}, t)
        frames.append(_frame(actual, pot, adj))
    return frames


def build_data():
    return {
        "diffusion (dissipative)": {
            "frames": _ecology_frames(Topology(N)),
            "caption": "λ<0 — thin red trace inside the green cone: actual ≪ potential, the allocator wins.",
        },
        "teleport (long-range edge)": {
            "frames": _ecology_frames(Topology(N, (TELE_EDGE,))),
            "caption": f"green cone FORKS to chunk {TELE_EDGE[1]} (potential explodes); red stays thin — pruned recovers.",
        },
        "chaos (CML r=4.0)": {
            "frames": _chaos_frames(),
            "caption": "λ>0 — red FLOODS the green cone: actual → potential, the allocator's advantage dies.",
        },
    }


HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Weltwerk — causal field (space-time)</title>
<style>
 body{{background:#0d1117;color:#d0d6e0;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:0;padding:24px}}
 h1{{font-size:18px;margin:0 0 2px}} .sub{{color:#8b95a6;margin:0 0 14px;max-width:940px}}
 .btns{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
 button{{background:#161b22;color:#d0d6e0;border:1px solid #30363d;border-radius:6px;padding:7px 11px;cursor:pointer;font:inherit}}
 button.on{{border-color:#58a6ff;background:#1b2533;color:#fff}}
 .legend{{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0;font-size:12.5px}}
 .legend div{{display:flex;align-items:center;gap:6px}} .sw{{width:13px;height:13px;border-radius:3px}}
 canvas{{border:1px solid #21262d;image-rendering:pixelated;margin-top:8px}}
 .cap{{color:#cdd3df;font-size:13px;margin:10px 0;min-height:20px}}
 .axes{{color:#6b7280;font-size:11.5px}} .note{{color:#8b95a6;font-size:12.5px;max-width:940px;margin-top:14px}}
</style></head><body>
<h1>Weltwerk — causal field (space-time)</h1>
<p class="sub">x = chunk, y = time (downward). Every cell is its causal class at that tick. The reachability
cone is the green triangle; each regime writes its signature inside it. Fed by the real engines.</p>
<div class="btns" id="btns"></div>
<div class="legend">
 <div><span class="sw" style="background:#1f6feb"></span>committed</div>
 <div><span class="sw" style="background:#2ea043"></span>potential cone</div>
 <div><span class="sw" style="background:#d29922"></span>allocated frontier</div>
 <div><span class="sw" style="background:#da3633"></span>actual divergence</div>
</div>
<canvas id="cv"></canvas>
<p class="axes">↳ x: chunk 0…{N0} (ring) &nbsp;·&nbsp; ↓ y: tick 0…{H0} &nbsp;·&nbsp; edit at chunk {EC}</p>
<p class="cap" id="cap"></p>
<p class="note">The gap between the green triangle and the red inside it IS the economic win. Diffusion and
teleport keep red ≪ green (cheap counterfactual / replication). Chaos fills green with red — `Actual →
Potential`, no win. Correctness is identical in all three; only the gap differs, and the gap is set by the
dynamical regime (sign of the largest Lyapunov exponent).</p>
<script>
const DATA = __DATA__;
const N = {N0}+1, COL = {{b:"#1f6feb", g:"#2ea043", y:"#d29922", r:"#da3633"}};
const CELL = 8, EC = {EC};
const names = Object.keys(DATA);
const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
function draw(name){{
  const fr = DATA[name].frames, rows = fr.length;
  cv.width = N*CELL; cv.height = rows*CELL;
  for(let t=0;t<rows;t++){{
    const row = fr[t];
    for(let c=0;c<N;c++){{ ctx.fillStyle = COL[row[c]]; ctx.fillRect(c*CELL, t*CELL, CELL, CELL); }}
  }}
  ctx.strokeStyle="rgba(255,255,255,0.35)"; ctx.lineWidth=1;
  ctx.strokeRect(EC*CELL+0.5, 0, CELL-1, rows*CELL);   // mark the edit column
  document.getElementById("cap").textContent = DATA[name].caption;
  for(const b of document.querySelectorAll("#btns button")) b.classList.toggle("on", b.dataset.n===name);
}}
const btns=document.getElementById("btns");
for(const name of names){{const b=document.createElement("button");b.textContent=name;b.dataset.n=name;b.onclick=()=>draw(name);btns.appendChild(b);}}
draw(names[0]);
</script></body></html>"""


def main():
    data = build_data()
    html = (HTML.replace("__DATA__", json.dumps(data))
                .replace("{N0}", str(N - 1)).replace("{H0}", str(H)).replace("{EC}", str(EDIT_C)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "causal_field.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("causal_field.py — emitted the space-time causal field\n")
    for name, d in data.items():
        final = d["frames"][-1]
        red = final.count("r")
        green = final.count("g") + final.count("y") + red
        print(f"  {name:<28} final tick: red(actual)={red:>3}  within cone(potential+)={green:>3}  "
              f"gap={green - red:>3}")
    print(f"\n  wrote {out}  — open it in a browser; switch systems to compare signatures.")


if __name__ == "__main__":
    main()
