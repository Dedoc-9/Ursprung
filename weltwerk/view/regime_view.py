# SPDX-License-Identifier: AGPL-3.0-only
"""
regime_view.py — the regime-aware causal renderer: WHERE is reality sparse enough for the allocator?

The amplification gate resolved the theory: the cheap-counterfactual / causal-allocation win is a
property of the dynamical regime (sub-critical/dissipative → sparse → works; chaotic/amplifying → dense
→ fails). The open question is now visual, per real world design: *which regions are which?*

This renders a world with HETEROGENEOUS dynamics — a coupled map lattice ring that is mostly dissipative
with an embedded chaotic band — and shows two things a developer needs to see:

  REGIME MAP (measured, not read off the parameter): perturb each region, watch how far divergence
  spreads, classify.  GREEN  sparse (allocator belongs) · PURPLE marginal/saturated · ORANGE chaotic
  (allocator does not help — divergence fills the reachable cone).

  EDIT FOOTPRINT: for a chosen edit, BLUE unaffected · GREEN potential cone · RED actual divergence.
  A local edit in a dissipative region stays a small red pocket; an edit in the chaotic band floods.

VIEW reveals committed measurements; it does not recompute the dynamics in the browser. The regime is
MEASURED (perturb-and-watch), never inferred from the gain — that keeps it honest for real worlds whose
local regime is unknown.

Run:  PYTHONHASHSEED=0 python3 regime_view.py   → writes regime_view.html (open in a browser).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scale"))

from amplify import _f, cone, diverged, initial, perturb     # noqa: E402

N, EPS, DELTA, TAU, H = 60, 0.25, 1e-3, 1e-6, 45
# heterogeneous gains: dissipative everywhere except a chaotic band [26,38]
R_LOW, R_HIGH = 2.8, 3.95
BAND = range(26, 39)
SPARSE_T, DENSE_T = 0.15, 0.40   # regime thresholds on measured local spread (fraction of world)


def gains() -> list:
    return [R_HIGH if i in BAND else R_LOW for i in range(N)]


def het_step(state: list, rs: list, eps: float) -> list:
    n = len(state)
    fx = [_f(state[i], rs[i]) for i in range(n)]
    return [(1.0 - eps) * fx[i] + 0.5 * eps * (fx[(i - 1) % n] + fx[(i + 1) % n]) for i in range(n)]


def het_run(state: list, rs: list, eps: float, horizon: int) -> list:
    traj = [list(state)]
    s = list(state)
    for _ in range(horizon):
        s = het_step(s, rs, eps)
        traj.append(s)
    return traj


def regime_map(rs: list) -> list:
    """Measured local spread for each chunk: perturb it, watch divergence, return peak fraction of world."""
    s0 = initial(N)
    base = het_run(s0, rs, EPS, H)
    out = []
    for c in range(N):
        b = het_run(perturb(s0, c, DELTA), rs, EPS, H)
        peak = max(len(diverged(base[t], b[t], TAU)) for t in range(H + 1))
        out.append(peak / N)
    return out


def regime_class(frac: float) -> str:
    return "sparse" if frac < SPARSE_T else ("marginal" if frac < DENSE_T else "chaotic")


def edit_footprint(rs: list, c: int) -> dict:
    """For an edit at chunk c: per-chunk class (committed/potential/actual) + its measured spread."""
    s0 = initial(N)
    base = het_run(s0, rs, EPS, H)
    b = het_run(perturb(s0, c, DELTA), rs, EPS, H)
    ever = set()
    for t in range(H + 1):
        ever |= diverged(base[t], b[t], TAU)
    pot = cone(c, N, H)
    classes = ["actual" if i in ever else ("potential" if i in pot else "committed") for i in range(N)]
    frac = len(ever) / N
    return {"edit": c, "classes": classes, "spread": frac, "regime": regime_class(frac)}


def build_data():
    rs = gains()
    rmap = regime_map(rs)
    # edits: one deep dissipative, one inside the chaotic band, one on the band boundary
    edits = [("dissipative region @8", 8), ("chaotic band @32", 32), ("band boundary @25", 25)]
    return {
        "regime": [regime_class(f) for f in rmap],
        "regime_frac": [round(f, 3) for f in rmap],
        "footprints": {name: edit_footprint(rs, c) for name, c in edits},
    }


HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Weltwerk — regime-aware causal view</title>
<style>
 body{{background:#0d1117;color:#d0d6e0;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:0;padding:24px}}
 h1{{font-size:18px;margin:0 0 2px}} .sub{{color:#8b95a6;margin:0 0 16px;max-width:920px}}
 .btns{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}
 button{{background:#161b22;color:#d0d6e0;border:1px solid #30363d;border-radius:6px;padding:7px 11px;cursor:pointer;font:inherit}}
 button.on{{border-color:#58a6ff;background:#1b2533;color:#fff}}
 .legend{{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0;font-size:12.5px}}
 .legend div{{display:flex;align-items:center;gap:6px}} .sw{{width:13px;height:13px;border-radius:3px}}
 .lab{{color:#8b95a6;font-size:12px;margin:14px 0 3px}}
 .panel{{margin:16px 0;padding:13px 16px;background:#11161d;border:1px solid #21262d;border-radius:8px}}
 .verdict{{font-size:16px;font-weight:bold}} .note{{color:#8b95a6;font-size:12.5px;max-width:920px;margin-top:14px}}
</style></head><body>
<h1>Weltwerk — regime-aware causal view</h1>
<p class="sub">A heterogeneous world (mostly dissipative, with an embedded chaotic band). The regime is
<b>measured</b> by perturb-and-watch, not read off the dynamics. The allocator belongs to the GREEN
regions; in ORANGE regions divergence fills the reachable cone and there is no win.</p>
<div class="legend">
 <div><span class="sw" style="background:#2ea043"></span>sparse — allocator works</div>
 <div><span class="sw" style="background:#8957e5"></span>marginal / saturated</div>
 <div><span class="sw" style="background:#e3742f"></span>chaotic — allocator fails</div>
 <div><span class="sw" style="background:#1f6feb"></span>committed</div>
 <div><span class="sw" style="background:#da3633"></span>actual divergence</div>
</div>
<p class="lab">REGIME MAP (measured local spread per region)</p>
<svg id="regime" width="980" height="44" viewBox="0 0 980 44"></svg>
<div class="btns" id="btns"></div>
<p class="lab">EDIT FOOTPRINT (blue committed · green potential cone · red actual divergence)</p>
<svg id="foot" width="980" height="44" viewBox="0 0 980 44"></svg>
<div class="panel"><span class="verdict" id="verdict"></span><div id="detail" style="color:#8b95a6;font-size:12.5px;margin-top:5px"></div></div>
<p class="note">The regime map answers the question the amplification result raised: <b>where is reality
sparse enough for the causal allocator to matter?</b> Edit inside a green region and the footprint stays
a small red pocket (cheap counterfactual / replication). Edit inside the orange band and red floods the
reachable cone — the allocator degenerates to full simulation there. Same engine, same correctness; only
the economics differ, and the difference is the local dynamical regime.</p>
<script>
const DATA = __DATA__;
const N = DATA.regime.length, W = 980, cw = W/N;
const RC = {{sparse:"#2ea043", marginal:"#8957e5", chaotic:"#e3742f"}};
const FC = {{committed:"#1f6feb", potential:"#2ea043", actual:"#da3633"}};
function strip(id, colors){{
  let s=""; for(let i=0;i<N;i++) s+=`<rect x="${{i*cw+0.5}}" y="6" width="${{cw-1}}" height="30" fill="${{colors[i]}}"/>`;
  document.getElementById(id).innerHTML=s;
}}
strip("regime", DATA.regime.map(r=>RC[r]));
const names=Object.keys(DATA.footprints);
function showEdit(name){{
  const f=DATA.footprints[name];
  strip("foot", f.classes.map(c=>FC[c]));
  // mark the edit chunk
  const svg=document.getElementById("foot");
  svg.innerHTML += `<rect x="${{f.edit*cw}}" y="2" width="${{cw}}" height="40" fill="none" stroke="#fff" stroke-width="1.5"/>`;
  const help = f.regime==="sparse";
  document.getElementById("verdict").innerHTML =
    `edit @${{f.edit}} — region regime: <span style="color:${{RC[f.regime]}}">${{f.regime.toUpperCase()}}</span> — allocator helps here: `+
    `<span style="color:${{help?'#2ea043':'#e3742f'}}">${{help?'YES':'NO'}}</span>`;
  document.getElementById("detail").textContent =
    `divergence spread = ${{(100*f.spread).toFixed(0)}}% of world (sparse<15% · marginal<40% · chaotic≥40%)`;
  for(const b of document.querySelectorAll("#btns button")) b.classList.toggle("on", b.dataset.n===name);
}}
const btns=document.getElementById("btns");
for(const name of names){{const b=document.createElement("button");b.textContent=name;b.dataset.n=name;b.onclick=()=>showEdit(name);btns.appendChild(b);}}
showEdit(names[0]);
</script></body></html>"""


def main():
    data = build_data()
    html = HTML.replace("__DATA__", json.dumps(data))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regime_view.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    counts = {k: data["regime"].count(k) for k in ("sparse", "marginal", "chaotic")}
    print("regime_view.py — emitted the regime-aware causal view\n")
    print(f"  regime map ({N} chunks): {counts}")
    for name, fp in data["footprints"].items():
        help = "YES" if fp["regime"] == "sparse" else "NO"
        print(f"  {name:<24} regime={fp['regime']:<9} spread={fp['spread']:.0%}  allocator helps={help}")
    print(f"\n  wrote {out}  — open it in a browser.")


if __name__ == "__main__":
    main()
