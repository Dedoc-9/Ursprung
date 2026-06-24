# SPDX-License-Identifier: AGPL-3.0-only
"""
topology_view.py — the wireframe of a causal topology (structure before geometry).

Renders a parsed world spec as a node-link wireframe: entities on a ring, directed causal edges between
them. Click an entity to see its Potential influence (green = an edit on it can reach here); feedback
loops are outlined orange (amplification RISK, to be confirmed dynamically — not a measured λ>0). The
panel reports the entity's blast radius and the graph's regime (DAG = bounded vs HAS-CYCLES). No
geometry, no art — just the causal structure a world would later be projected onto.

Run:  PYTHONHASHSEED=0 python3 topology_view.py   → writes topology_view.html (open in a browser).
"""
from __future__ import annotations

import json
import os

from world_spec import FORTRESS, parse_spec


def build_data():
    g = parse_spec(FORTRESS)
    nodes = sorted(g.nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    edges = [[idx[s], idx[d], g.labels[(s, d)]] for s in nodes for d in sorted(g.edges[s])]
    influence = {n: sorted(idx[m] for m in g.influence(n)) for n in nodes}
    return {
        "nodes": nodes,
        "edges": edges,
        "influence": influence,
        "cyclic": sorted(idx[n] for n in g.cyclic_nodes()),
        "blast": {n: g.blast_radius(n) for n in nodes},
        "in_cycle": {n: g.in_cycle(n) for n in nodes},
        "regime": g.regime(),
    }


HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Weltwerk — causal topology</title>
<style>
 body{{background:#0d1117;color:#d0d6e0;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;margin:0;padding:24px}}
 h1{{font-size:18px;margin:0 0 2px}} .sub{{color:#8b95a6;margin:0 0 12px;max-width:900px}}
 .legend{{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0;font-size:12.5px}}
 .legend div{{display:flex;align-items:center;gap:6px}} .sw{{width:13px;height:13px;border-radius:50%}}
 .panel{{margin:10px 0;padding:12px 15px;background:#11161d;border:1px solid #21262d;border-radius:8px;min-height:20px}}
 .reg{{font-weight:bold}} .note{{color:#8b95a6;font-size:12.5px;max-width:900px;margin-top:12px}}
 text{{font:11px ui-monospace,monospace;fill:#c9d1d9;cursor:pointer}}
</style></head><body>
<h1>Weltwerk — causal topology (text → structure, before geometry)</h1>
<p class="sub">A world spec rendered as causal structure: entities + directed "can-affect" edges. Click an
entity to see its <b>Potential</b> influence (green). Feedback loops are outlined orange — an amplification
<i>risk</i>, not a measured one.</p>
<div class="legend">
 <div><span class="sw" style="background:#1f6feb"></span>entity</div>
 <div><span class="sw" style="background:#2ea043"></span>in selected entity's influence</div>
 <div><span class="sw" style="background:#0d1117;border:2px solid #e3742f"></span>feedback loop (amplification risk)</div>
</div>
<svg id="g" width="640" height="560" viewBox="0 0 640 560"></svg>
<div class="panel" id="panel">Click an entity.</div>
<p class="note">Topology is cheap to change; geometry is expensive — so the causal structure is the durable
artifact and meshes are a later projection of it. A cycle here flags an amplification <b>risk</b>
(`structural-cycle ≠ measured-amplification`); confirm with the amplifying-dynamics gate before trusting
it. The spec is a declared authoring input; its consequences are what the engine measures.</p>
<script>
const D = __DATA__;
const NS = D.nodes.length, CX=320, CY=270, R=200;
const svg=document.getElementById("g");
function pos(i){{ const a = -Math.PI/2 + 2*Math.PI*i/NS; return [CX+R*Math.cos(a), CY+R*Math.sin(a)]; }}
const cyc = new Set(D.cyclic);
let sel = null;
function render(){{
  const inf = sel===null ? new Set() : new Set(D.influence[D.nodes[sel]]);
  let s="";
  for(const [a,b] of D.edges){{
    const [x1,y1]=pos(a),[x2,y2]=pos(b);
    const hot = sel!==null && inf.has(a) && inf.has(b);
    s+=`<line x1="${{x1}}" y1="${{y1}}" x2="${{x2}}" y2="${{y2}}" stroke="${{hot?'#2ea043':'#30363d'}}" stroke-width="${{hot?1.8:1}}"/>`;
    s+=`<circle cx="${{x2}}" cy="${{y2}}" r="3" fill="${{hot?'#2ea043':'#484f58'}}"/>`;   // arrowhead-ish at dst
  }}
  for(let i=0;i<NS;i++){{
    const [x,y]=pos(i);
    const fill = (sel!==null && inf.has(i)) ? "#2ea043" : "#1f6feb";
    const stroke = (i===sel) ? "#fff" : (cyc.has(i) ? "#e3742f" : "none");
    s+=`<circle cx="${{x}}" cy="${{y}}" r="13" fill="${{fill}}" stroke="${{stroke}}" stroke-width="2.5" data-i="${{i}}" style="cursor:pointer"/>`;
    const lx = x + (x<CX? -18: 18); const anc = x<CX?"end":"start";
    s+=`<text x="${{lx}}" y="${{y+4}}" text-anchor="${{anc}}" data-i="${{i}}">${{D.nodes[i]}}</text>`;
  }}
  svg.innerHTML=s;
  for(const el of svg.querySelectorAll("[data-i]")) el.onclick=()=>{{ sel=+el.dataset.i; render(); panel(); }};
}}
function panel(){{
  if(sel===null) return;
  const n=D.nodes[sel];
  document.getElementById("panel").innerHTML =
    `edit <b>${{n}}</b> → Potential blast radius <b>${{D.blast[n]}}</b> of ${{NS}} entities`+
    (D.in_cycle[n]?` &nbsp;·&nbsp; <span style="color:#e3742f">in a feedback loop (amplification risk)</span>`:"")+
    `<br><span class="reg">graph regime: ${{D.regime}}</span>`;
}}
render();
</script></body></html>"""


def main():
    data = build_data()
    html = HTML.replace("__DATA__", json.dumps(data))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topology_view.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("topology_view.py — emitted the causal-topology wireframe\n")
    print(f"  entities={len(data['nodes'])}  regime: {data['regime']}")
    print(f"  cyclic (amplification-risk): {[data['nodes'][i] for i in data['cyclic']]}")
    print(f"\n  wrote {out}  — open it in a browser; click an entity to see its blast radius.")


if __name__ == "__main__":
    main()
