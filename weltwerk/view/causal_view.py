# SPDX-License-Identifier: AGPL-3.0-only
"""
causal_view.py — the VIEW: a causal debugger, not a game renderer.

It turns the four measured sets into something impossible to accidentally merge. It does NOT recompute
causality in the browser — it runs the verified engine (teleport.reconstruct + causal_budget) and emits
a self-contained HTML that *renders committed measurements*. VIEW reveals; it does not define.

THE FOUR SETS (a proven nesting: changed ⊆ pruned.touched ⊆ conservative.touched ⊆ all):
  BLUE   committed / unaffected  — outside the potential cone
  GREEN  potential               — the conservative path would touch it; the pruned path did not
  YELLOW allocated               — simulated by the pruned allocator but did NOT change (frontier overhead)
  RED    actual divergence       — genuinely changed (= the lossless transmit set)

Each colour is a different measured object. The panel shows |potential| ⊇ |allocated| ⊇ |actual| and the
savings, so `potential ≠ allocated ≠ actual ≠ transmitted` is visible, not asserted.

Run:  PYTHONHASHSEED=0 python3 causal_view.py   → writes causal_view.html (open it in a browser).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scale"))

from cow_world import Edit, Rules, genesis                         # noqa: E402
from teleport import Topology, full_sim_traced, reconstruct        # noqa: E402

N, CHUNK_SIZE, SEED, H = 60, 10, 0, 20


def classify(snap, topo, rules, seed, edit, horizon):
    """Return per-chunk colour class + the four counts, all from the verified engine."""
    line_a = full_sim_traced(snap, topo, rules, seed, horizon)[0][horizon]
    cons = reconstruct(snap, topo, rules, seed, edit, horizon, prune=False)
    pru = reconstruct(snap, topo, rules, seed, edit, horizon, prune=True)
    potential = cons.touched                       # conservative reachability
    allocated = pru.touched                        # what the pruned allocator simulated
    changed = frozenset(c for c in line_a if line_a[c] != pru.line_b[c])   # actual = transmit
    # proven nesting (guarded in test_causal_view): changed ⊆ allocated ⊆ potential
    classes = []
    for c in range(topo.n):
        if c in changed:
            classes.append("actual")
        elif c in allocated:
            classes.append("alloc")
        elif c in potential:
            classes.append("potential")
        else:
            classes.append("committed")
    return {
        "classes": classes,
        "teleport": [list(e) for e in topo.teleport_edges],
        "counts": {"potential": len(potential), "allocated": len(allocated),
                   "actual": len(changed), "transmit": len(changed), "broadcast": topo.n},
    }


def build_data():
    snap = genesis(N * CHUNK_SIZE, N, SEED)
    rules = Rules()
    scenarios = [
        ("cull predators @5 — ring (geography)", Topology(N), Edit("cull_pred_chunk", chunk=5)),
        ("cull predators @5 — +teleport 5↔40", Topology(N, ((5, 40),)), Edit("cull_pred_chunk", chunk=5)),
        ("cull predators @30 — ring", Topology(N), Edit("cull_pred_chunk", chunk=30)),
        ("GLOBAL: predation off — ring", Topology(N), Edit("set_rule", rule_field="predation_enabled", rule_value=False)),
    ]
    return {name: classify(snap, topo, rules, SEED, edit, H) for name, topo, edit in scenarios}


HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Weltwerk — causal debugger</title>
<style>
 body{{background:#0d1117;color:#d0d6e0;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:0;padding:24px}}
 h1{{font-size:18px;margin:0 0 2px}} .sub{{color:#8b95a6;margin:0 0 18px}}
 .btns{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}}
 button{{background:#161b22;color:#d0d6e0;border:1px solid #30363d;border-radius:6px;padding:7px 11px;cursor:pointer;font:inherit}}
 button.on{{border-color:#58a6ff;background:#1b2533;color:#fff}}
 .legend{{display:flex;gap:18px;flex-wrap:wrap;margin:14px 0}}
 .legend div{{display:flex;align-items:center;gap:7px}}
 .sw{{width:14px;height:14px;border-radius:3px;display:inline-block}}
 .panel{{display:flex;gap:26px;flex-wrap:wrap;margin:16px 0;padding:14px 16px;background:#11161d;border:1px solid #21262d;border-radius:8px}}
 .stat b{{font-size:22px;display:block}} .stat span{{color:#8b95a6;font-size:12px}}
 .note{{color:#8b95a6;font-size:12.5px;max-width:920px;margin-top:14px}}
 svg{{display:block;margin-top:6px}}
</style></head><body>
<h1>Weltwerk — causal debugger</h1>
<p class="sub">A wireframe of the chunk ring, coloured by four <i>measured</i> sets. VIEW reveals committed data; it does not define it.</p>
<div class="btns" id="btns"></div>
<div class="legend">
 <div><span class="sw" style="background:#1f6feb"></span> BLUE committed / unaffected</div>
 <div><span class="sw" style="background:#2ea043"></span> GREEN potential (could differ)</div>
 <div><span class="sw" style="background:#d29922"></span> YELLOW allocated (simulated, didn't change)</div>
 <div><span class="sw" style="background:#da3633"></span> RED actual divergence (= transmit set)</div>
</div>
<svg id="strip" width="980" height="160" viewBox="0 0 980 160"></svg>
<div class="panel" id="panel"></div>
<p class="note">Proven nesting: <b>changed ⊆ allocated ⊆ potential ⊆ all</b>. The four counts are different
measured objects — never merged. <b>potential</b> = conservative reachability (dependency analysis);
<b>allocated</b> = what the pruned allocator actually simulated (incl. frontier overhead);
<b>actual</b> = chunks that genuinely changed (the lossless transmit set). A local edit lights a small
region; a GLOBAL edit lights the whole ring — that contrast is the point. Arcs above the strip are
teleport edges (long-range coupling).</p>
<script>
const DATA = __DATA__;
const COL = {{committed:"#1f6feb", potential:"#2ea043", alloc:"#d29922", actual:"#da3633"}};
const names = Object.keys(DATA);
const N = DATA[names[0]].classes.length;
const W = 980, cw = W / N, y0 = 70, ch = 30;
function cx(i){{ return i*cw + cw/2; }}
function render(name){{
  const d = DATA[name], svg = document.getElementById("strip");
  let s = "";
  for(let i=0;i<N;i++){{
    s += `<rect x="${{i*cw+0.5}}" y="${{y0}}" width="${{cw-1}}" height="${{ch}}" fill="${{COL[d.classes[i]]}}" />`;
  }}
  for(const [a,b] of d.teleport){{
    const x1=cx(a), x2=cx(b), mx=(x1+x2)/2, h=y0-46;
    s += `<path d="M${{x1}} ${{y0}} Q ${{mx}} ${{h}} ${{x2}} ${{y0}}" fill="none" stroke="#bc8cff" stroke-width="1.6"/>`;
    s += `<circle cx="${{x1}}" cy="${{y0}}" r="2.5" fill="#bc8cff"/><circle cx="${{x2}}" cy="${{y0}}" r="2.5" fill="#bc8cff"/>`;
  }}
  s += `<text x="0" y="${{y0+ch+18}}" fill="#6b7280" font-size="11">chunk 0</text>`;
  s += `<text x="${{W-46}}" y="${{y0+ch+18}}" fill="#6b7280" font-size="11">chunk ${{N-1}} (ring wraps)</text>`;
  svg.innerHTML = s;
  const c = d.counts;
  document.getElementById("panel").innerHTML =
    `<div class="stat"><b style="color:#2ea043">${{c.potential}}</b><span>potential (could differ)</span></div>`+
    `<div class="stat"><b style="color:#d29922">${{c.allocated}}</b><span>allocated (simulated)</span></div>`+
    `<div class="stat"><b style="color:#da3633">${{c.actual}}</b><span>actual (did differ)</span></div>`+
    `<div class="stat"><b style="color:#da3633">${{c.transmit}}</b><span>transmit (lossless)</span></div>`+
    `<div class="stat"><b>${{c.broadcast}}</b><span>broadcast (distance)</span></div>`+
    `<div class="stat"><b>${{(100*c.transmit/c.broadcast).toFixed(1)}}%</b><span>transmit / broadcast</span></div>`;
  for(const b of document.querySelectorAll("#btns button")) b.classList.toggle("on", b.dataset.n===name);
}}
const btns = document.getElementById("btns");
for(const name of names){{
  const b=document.createElement("button"); b.textContent=name; b.dataset.n=name;
  b.onclick=()=>render(name); btns.appendChild(b);
}}
render(names[0]);
</script></body></html>"""


def main():
    data = build_data()
    html = HTML.replace("__DATA__", json.dumps(data))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "causal_view.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("causal_view.py — emitted the causal debugger\n")
    for name, d in data.items():
        c = d["counts"]
        print(f"  {name}\n    potential={c['potential']}  allocated={c['allocated']}  "
              f"actual={c['actual']}  transmit/broadcast={c['transmit']}/{c['broadcast']}")
    print(f"\n  wrote {out}  — open it in a browser.")


if __name__ == "__main__":
    main()
