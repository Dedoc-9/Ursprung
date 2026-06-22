// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6d / T3: the TEMPORAL CAUSAL GATE (calibration baseline, monotone scene).
//!
//! T1 built the temporal apparatus; T2 proved the temporal ruler fair. T3 finally compares POLICIES on it:
//! does spending NOW measurably reduce FUTURE error, and for which policies — judged on a ruler they cannot
//! see, at equal measured budget.
//!
//! THE SEALED OBSERVER, IN TIME. Each policy maps (present revealed-mask, its OWN accumulation so far,
//! per-frame budget) → this frame's per-tile allocation. It never sees the future, the future reference, or
//! the ruler. So "optimize the metric" stays structurally impossible — the M6 rule, lifted into time.
//!
//! THE ONLY LEGITIMATE TEMPORAL LEVER (under T2's declared coupling). Disocclusion RESETS history, so
//! pre-warming still-occluded content is wasted — an oracle could not exploit it either. What remains: among
//! ALREADY-REVEALED tiles, serve the UNDER-ACCUMULATED ones (high future-causal deficit) and don't burn budget
//! on occluded content that will be reset. That is the temporal form of "drop present-perception S, allocate by
//! future causal loss" — and it is expressible from present state + own history alone.
//!
//! Five SEALED policies (admissible, equal budget):
//!   uniform           budget-blind — spends on occluded tiles too (which reset → wasted)
//!   present_pfal      ∝ present difficulty — deprioritises occluded but serves all revealed alike (history-blind)
//!   causal_future_d1  ∝ future-causal deficit on revealed tiles (exponent 1)
//!   causal_future_d23 deficit^(2/3) on revealed tiles (the M6c variance-optimal exponent, in time)
//!   drifted           random (negative control)
//! plus ONE NON-ADMISSIBLE prophet (sees the future) as a CALIBRATION CEILING — not a contender.
//!
//! HONEST SCENE CAVEAT (recorded, not hidden). This monotone occlusion sweep only ever *reveals*, so "revealed
//! now" already implies "relevant at the future frame", and disocclusion-reset forbids pre-warming — therefore
//! the prophet has almost no legitimate edge here, and prophet ≈ causal_future is expected. That near-tie is a
//! PROPERTY OF THIS SCENE (no hidden-future information to exploit), NOT proof the policy reached a fundamental
//! ceiling. The discriminating test — a scene whose future relevance is NOT visible in present state — is T4.
//!
//! Verdict is a Pareto VECTOR (pixel + structural future error) under ε-dominance; no scalar winner.
//! `benchmark gain ≠ universal`.
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;

use pollster::FutureExt as _;
use reality_core::{Core, Event};

const RES: u32 = 256;
const BYTES_PER_ROW: u32 = RES * 4;
const TILES_X: u32 = 8;
const TILES: usize = (TILES_X * TILES_X) as usize;
const REF_SAMPLES: u32 = 256;
const TF: usize = 5;
const HARD: f32 = 0.95;
const EASY: f32 = 0.12;
const B_FRAME: u32 = 512;     // per-frame allocation budget (equal for every policy)
const TARGET: u32 = 64;       // the sealed causal policies' per-tile accumulation target (deficit basis)

const SCENE_WGSL: &str = r#"
struct U { seed: u32, res: u32, tiles_x: u32, _pad: u32 };
@group(0) @binding(0) var<uniform> u: U;
@group(0) @binding(1) var<storage, read> tile_amp: array<f32>;
@group(0) @binding(2) var<storage, read> tile_samples: array<u32>;

fn scene(p: vec2<f32>, amp: f32) -> f32 {
    let hf = sin(p.x * 120.0) * sin(p.y * 120.0);
    let edge = select(0.0, 1.0, (p.x + p.y) > 1.0);
    return clamp(0.5 + amp * hf * 0.5 + 0.1 * edge, 0.0, 1.0);
}
@vertex
fn vs(@builtin(vertex_index) vi: u32) -> @builtin(position) vec4<f32> {
    var q = array<vec2<f32>, 3>(vec2<f32>(-1.0,-1.0), vec2<f32>(3.0,-1.0), vec2<f32>(-1.0,3.0));
    return vec4<f32>(q[vi], 0.0, 1.0);
}
@fragment
fn fs(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
    let res = f32(u.res);
    let tpx = u.res / u.tiles_x;
    let tx = min(u32(pos.x) / tpx, u.tiles_x - 1u);
    let ty = min(u32(pos.y) / tpx, u.tiles_x - 1u);
    let tile = ty * u.tiles_x + tx;
    let amp = tile_amp[tile];
    let n = max(tile_samples[tile], 1u);
    var acc = 0.0;
    var st: u32 = u.seed + u32(pos.x) * 1973u + u32(pos.y) * 9277u + 1u;
    for (var i: u32 = 0u; i < n; i = i + 1u) {
        st = st * 747796405u + 2891336453u; let jx = f32((st >> 16u) & 0xffffu) / 65535.0;
        st = st * 747796405u + 2891336453u; let jy = f32((st >> 16u) & 0xffffu) / 65535.0;
        let p = (pos.xy + vec2<f32>(jx, jy) - vec2<f32>(0.5)) / res;
        acc = acc + scene(p, amp);
    }
    let v = acc / f32(n);
    return vec4<f32>(v, v, v, 1.0);
}
"#;

fn world_amp(frame: usize) -> Vec<f32> {
    (0..TILES).map(|ti| { let x = (ti as u32 % TILES_X) as usize; if x <= frame { HARD } else { EASY } }).collect()
}
fn revealed_at(frame: usize) -> Vec<bool> {
    (0..TILES).map(|ti| (ti as u32 % TILES_X) as usize <= frame).collect()
}
fn world_state_str(frame: usize) -> String { format!("edge_col={}", frame) }

fn evolve_through_kernel(frames: usize) -> Vec<String> {
    let mut core = Core::new();
    let mut chain = Vec::new();
    let mut prev_digest: Option<String> = None;
    let mut prev_state = "edge_col=-1".to_string();
    for t in 0..frames {
        let ns = world_state_str(t);
        let ev = Event::new("scene", &prev_state, &ns, &format!("occlusion_sweep@f{}", t)).unwrap();
        let rec = core.apply(&ev, prev_digest.as_deref()).expect("commit");
        chain.push(rec.provenance_digest.clone());
        prev_digest = Some(rec.provenance_digest); prev_state = ns;
    }
    chain
}

// ---- equal-budget integer allocation (largest-remainder; zero weight → zero; all-zero → uniform) ----
fn hamilton(weights: &[f64], total: u32) -> Vec<u32> {
    let sum: f64 = weights.iter().map(|w| w.max(0.0)).sum();
    if sum <= 0.0 {
        let base = total / TILES as u32;
        let mut a = vec![base; TILES];
        let mut rem = (total - base * TILES as u32) as usize; let mut i = 0;
        while rem > 0 { a[i % TILES] += 1; rem -= 1; i += 1; }
        return a;
    }
    let exact: Vec<f64> = weights.iter().map(|w| w.max(0.0) / sum * total as f64).collect();
    let mut alloc: Vec<u32> = exact.iter().map(|x| x.floor() as u32).collect();
    let mut spent: u32 = alloc.iter().sum();
    let mut order: Vec<usize> = (0..TILES).collect();
    order.sort_by(|&a, &b| (exact[b] - exact[b].floor()).partial_cmp(&(exact[a] - exact[a].floor())).unwrap());
    let mut k = 0;
    while spent < total { alloc[order[k % TILES]] += 1; spent += 1; k += 1; }
    alloc
}

// ---- SEALED policies: (revealed_now, own_acc, frame_budget) → this frame's per-tile allocation ----
type Policy = fn(&[bool], &[u32], u32) -> Vec<u32>;

fn p_uniform(_rev: &[bool], _acc: &[u32], b: u32) -> Vec<u32> { hamilton(&vec![1.0; TILES], b) }
fn p_present(rev: &[bool], _acc: &[u32], b: u32) -> Vec<u32> {
    hamilton(&rev.iter().map(|&r| if r { HARD as f64 } else { EASY as f64 }).collect::<Vec<_>>(), b)
}
fn deficit(acc: u32) -> u32 { TARGET.saturating_sub(acc.min(TARGET)) }
fn p_causal_d1(rev: &[bool], acc: &[u32], b: u32) -> Vec<u32> {
    hamilton(&(0..TILES).map(|t| if rev[t] { deficit(acc[t]) as f64 } else { 0.0 }).collect::<Vec<_>>(), b)
}
fn p_causal_d23(rev: &[bool], acc: &[u32], b: u32) -> Vec<u32> {
    hamilton(&(0..TILES).map(|t| if rev[t] { (deficit(acc[t]) as f64).powf(2.0 / 3.0) } else { 0.0 }).collect::<Vec<_>>(), b)
}
fn p_drifted(_rev: &[bool], _acc: &[u32], b: u32) -> Vec<u32> {
    hamilton(&(0..TILES).map(|t| ((t * 40503) % 997 + 1) as f64).collect::<Vec<_>>(), b)
}

/// Simulate a sealed policy over frames 0..=TF under the T2 coupling (accumulate; reset on disocclusion).
/// Returns (effective samples at TF, total ALLOCATED budget — the equal-budget quantity).
fn simulate(pol: Policy) -> (Vec<u32>, u32) {
    let mut acc = vec![0u32; TILES];
    let mut prev = vec![false; TILES];
    let mut allocated = 0u32;
    for f in 0..=TF {
        let rev = revealed_at(f);
        for t in 0..TILES { if rev[t] != prev[t] { acc[t] = 0; } } // disocclusion invalidates history
        let al = pol(&rev, &acc, B_FRAME);
        allocated += al.iter().sum::<u32>();
        for t in 0..TILES { acc[t] = (acc[t] + al[t]).min(REF_SAMPLES); }
        prev = rev;
    }
    (acc, allocated)
}

/// NON-ADMISSIBLE prophet: knows the future (which tiles are hard at TF) and serves ONLY those, using the SAME
/// deficit mechanism as the sealed causal_d23 — so any difference would be pure oracle advantage, not a tuning
/// difference. A CALIBRATION CEILING, not a contender. In this monotone scene `revealed_now ⟹ hard_at_TF`, so
/// the future gate is NON-BINDING and the prophet COLLAPSES onto causal_d23 (gap ≈ 0) — the cleanest possible
/// statement that this world holds no hidden-future information to exploit.
fn simulate_prophet() -> (Vec<u32>, u32) {
    let hard_tf = revealed_at(TF); // future knowledge: the set of tiles hard at the future frame
    let mut acc = vec![0u32; TILES];
    let mut prev = vec![false; TILES];
    let mut allocated = 0u32;
    for f in 0..=TF {
        let rev = revealed_at(f);
        for t in 0..TILES { if rev[t] != prev[t] { acc[t] = 0; } }
        let w: Vec<f64> = (0..TILES).map(|t| if rev[t] && hard_tf[t] {
            (deficit(acc[t]) as f64).powf(2.0 / 3.0)   // identical basis to causal_d23 — only the future gate differs
        } else { 0.0 }).collect();
        let al = hamilton(&w, B_FRAME);
        allocated += al.iter().sum::<u32>();
        for t in 0..TILES { acc[t] = (acc[t] + al[t]).min(REF_SAMPLES); }
        prev = rev;
    }
    (acc, allocated)
}

struct Gpu { device: wgpu::Device, queue: wgpu::Queue, pipeline: wgpu::RenderPipeline, bgl: wgpu::BindGroupLayout,
             tex: wgpu::Texture, view: wgpu::TextureView, device_name: String, backend: String }

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor { backends: wgpu::Backends::PRIMARY, ..Default::default() });
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions { power_preference: wgpu::PowerPreference::HighPerformance, force_fallback_adapter: false, compatible_surface: None }).block_on().expect("no adapter");
        let info = adapter.get_info();
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor { label: Some("T3"), required_features: wgpu::Features::empty(), required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default() }, None).block_on().expect("device");
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor { label: Some("scene"), source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(SCENE_WGSL)) });
        let stor = |b: u32| wgpu::BindGroupLayoutEntry { binding: b, visibility: wgpu::ShaderStages::FRAGMENT, ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Storage { read_only: true }, has_dynamic_offset: false, min_binding_size: None }, count: None };
        let bgl = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor { label: Some("bgl"), entries: &[
            wgpu::BindGroupLayoutEntry { binding: 0, visibility: wgpu::ShaderStages::FRAGMENT, ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false, min_binding_size: None }, count: None },
            stor(1), stor(2),
        ]});
        let pl = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor { label: Some("pl"), bind_group_layouts: &[&bgl], push_constant_ranges: &[] });
        let format = wgpu::TextureFormat::Rgba8Unorm;
        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("scene"), layout: Some(&pl),
            vertex: wgpu::VertexState { module: &shader, entry_point: "vs", buffers: &[], compilation_options: Default::default() },
            fragment: Some(wgpu::FragmentState { module: &shader, entry_point: "fs", targets: &[Some(wgpu::ColorTargetState { format, blend: None, write_mask: wgpu::ColorWrites::ALL })], compilation_options: Default::default() }),
            primitive: wgpu::PrimitiveState::default(), depth_stencil: None, multisample: wgpu::MultisampleState::default(), multiview: None, cache: None,
        });
        let tex = device.create_texture(&wgpu::TextureDescriptor { label: Some("t"), size: wgpu::Extent3d { width: RES, height: RES, depth_or_array_layers: 1 }, mip_level_count: 1, sample_count: 1, dimension: wgpu::TextureDimension::D2, format, usage: wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC, view_formats: &[] });
        let view = tex.create_view(&Default::default());
        Gpu { device_name: info.name.clone(), backend: format!("{:?}", info.backend), device, queue, pipeline, bgl, tex, view }
    }

    fn storage_u32(&self, data: &[u32]) -> wgpu::Buffer {
        let buf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("s32"), size: (data.len() * 4) as u64, usage: wgpu::BufferUsages::STORAGE, mapped_at_creation: true });
        { let mut v = buf.slice(..).get_mapped_range_mut(); for (i, &x) in data.iter().enumerate() { v[i*4..i*4+4].copy_from_slice(&x.to_le_bytes()); } }
        buf.unmap(); buf
    }
    fn storage_f32(&self, data: &[f32]) -> wgpu::Buffer {
        let buf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("sf32"), size: (data.len() * 4) as u64, usage: wgpu::BufferUsages::STORAGE, mapped_at_creation: true });
        { let mut v = buf.slice(..).get_mapped_range_mut(); for (i, &x) in data.iter().enumerate() { v[i*4..i*4+4].copy_from_slice(&x.to_le_bytes()); } }
        buf.unmap(); buf
    }

    fn render(&self, frame_amp: &[f32], tile_samples: &[u32], seed: u32) -> Vec<u8> {
        let amp = self.storage_f32(frame_amp);
        let samp = self.storage_u32(tile_samples);
        let ubuf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("u"), size: 16, usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let mut u = [0u8; 16];
        u[0..4].copy_from_slice(&seed.to_le_bytes()); u[4..8].copy_from_slice(&RES.to_le_bytes()); u[8..12].copy_from_slice(&TILES_X.to_le_bytes());
        self.queue.write_buffer(&ubuf, 0, &u);
        let bind = self.device.create_bind_group(&wgpu::BindGroupDescriptor { label: Some("bg"), layout: &self.bgl, entries: &[
            wgpu::BindGroupEntry { binding: 0, resource: ubuf.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 1, resource: amp.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 2, resource: samp.as_entire_binding() },
        ]});
        let pxbuf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("px"), size: (BYTES_PER_ROW * RES) as u64, usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let mut enc = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = enc.begin_render_pass(&wgpu::RenderPassDescriptor { label: Some("p"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment { view: &self.view, resolve_target: None, ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Store } })],
                depth_stencil_attachment: None, timestamp_writes: None, occlusion_query_set: None });
            pass.set_pipeline(&self.pipeline); pass.set_bind_group(0, &bind, &[]); pass.draw(0..3, 0..1);
        }
        enc.copy_texture_to_buffer(
            wgpu::ImageCopyTexture { texture: &self.tex, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
            wgpu::ImageCopyBuffer { buffer: &pxbuf, layout: wgpu::ImageDataLayout { offset: 0, bytes_per_row: Some(BYTES_PER_ROW), rows_per_image: Some(RES) } },
            wgpu::Extent3d { width: RES, height: RES, depth_or_array_layers: 1 });
        self.queue.submit(Some(enc.finish()));
        let s = pxbuf.slice(..); let (tx, rx) = std::sync::mpsc::channel(); s.map_async(wgpu::MapMode::Read, move |r| { let _ = tx.send(r); });
        self.device.poll(wgpu::Maintain::Wait); rx.recv().unwrap().unwrap();
        let pd = s.get_mapped_range(); let pixels = pd.to_vec(); drop(pd); pxbuf.unmap();
        pixels
    }
}

fn r_channel(px: &[u8]) -> Vec<f64> { px.iter().step_by(4).map(|&b| b as f64 / 255.0).collect() }
fn pixel_err(a: &[u8], b: &[u8]) -> f64 {
    let (x, y) = (r_channel(a), r_channel(b));
    x.iter().zip(&y).map(|(p, q)| (p - q).abs()).sum::<f64>() / x.len() as f64
}
fn grad(px: &[u8]) -> Vec<f64> {
    let r = r_channel(px); let n = RES as usize; let mut g = vec![0.0; r.len()];
    for yy in 0..n { for xx in 0..n {
        let i = yy * n + xx;
        let dx = if xx + 1 < n { r[i + 1] - r[i] } else { 0.0 };
        let dy = if yy + 1 < n { r[i + n] - r[i] } else { 0.0 };
        g[i] = (dx * dx + dy * dy).sqrt();
    }}
    g
}
fn struct_err(a: &[u8], b: &[u8]) -> f64 {
    let (ga, gb) = (grad(a), grad(b));
    ga.iter().zip(&gb).map(|(x, y)| (x - y).abs()).sum::<f64>() / ga.len() as f64
}
fn spread(v: &[f64]) -> f64 {
    v.iter().cloned().fold(f64::MIN, f64::max) - v.iter().cloned().fold(f64::MAX, f64::min)
}

fn main() {
    let gpu = Gpu::init();
    println!("M6d / T3 — the TEMPORAL CAUSAL GATE (calibration baseline, monotone scene) on {} ({})", gpu.device_name, gpu.backend);
    let chain = evolve_through_kernel(TF + 1);
    println!("world ran through the kernel ({} commits; head {}); coupling = TAA accumulation + disocclusion reset (declared)", chain.len(), chain.first().cloned().unwrap_or_default());
    println!("sealed policies allocate the per-frame budget from present state + own accumulation only; scored on the T2 ruler vs future references\n");

    let budget_each = B_FRAME * (TF as u32 + 1);
    let amp_tf = world_amp(TF);
    let reference = gpu.render(&amp_tf, &vec![REF_SAMPLES; TILES], 0);
    let score = |eff: &[u32], seed: u32| -> (f64, f64) {
        let px = gpu.render(&amp_tf, eff, seed);
        (pixel_err(&px, &reference), struct_err(&px, &reference))
    };

    // ε floor (per axis), cross-seed on the uniform policy's effective map
    let (eff_u, _) = simulate(p_uniform);
    let (mut pe, mut se) = (Vec::new(), Vec::new());
    for s in [11u32, 22, 33, 44] { let (p, st) = score(&eff_u, s); pe.push(p); se.push(st); }
    let eps = [spread(&pe), spread(&se)];

    // run the five sealed policies (equal budget) + the prophet ceiling
    let sealed: [(&str, Policy); 5] = [
        ("uniform", p_uniform), ("present_pfal", p_present),
        ("causal_future_d1", p_causal_d1), ("causal_future_d23", p_causal_d23), ("drifted(ctrl)", p_drifted),
    ];
    let mut rows: Vec<(String, f64, f64)> = Vec::new();
    for (name, pol) in sealed.iter() {
        let (eff, alloc) = simulate(*pol);
        assert_eq!(alloc, budget_each, "equal-budget violated by {}", name);
        let (p, st) = score(&eff, 7);
        rows.push((name.to_string(), p, st));
    }
    let (eff_p, alloc_p) = simulate_prophet();
    assert_eq!(alloc_p, budget_each, "prophet must spend the same budget");
    let (pp, ps) = score(&eff_p, 7);

    println!("  policy               future_pixel  future_struct   (equal budget {} samples; lower = better)", budget_each);
    for (n, p, s) in &rows {
        println!("    {:<18} {:.5}      {:.5}", n, p, s);
    }
    println!("    {:<18} {:.5}      {:.5}   ← PROPHET (non-admissible ceiling; sees the future)", "prophet", pp, ps);
    println!("  measured ε floor (pixel/struct) = {:.6} / {:.6}\n", eps[0], eps[1]);

    // ε-dominance frontier among the FIVE SEALED policies (prophet excluded — it is not a contender)
    let dominates = |a: (f64, f64), b: (f64, f64)| {
        (a.0 <= b.0 + eps[0] && a.1 <= b.1 + eps[1]) && (a.0 < b.0 - eps[0] || a.1 < b.1 - eps[1])
    };
    let on_frontier = |i: usize| !(0..rows.len()).any(|j| dominates((rows[j].1, rows[j].2), (rows[i].1, rows[i].2)));
    let frontier: Vec<&str> = (0..rows.len()).filter(|&i| on_frontier(i)).map(|i| rows[i].0.as_str()).collect();
    println!("  → ε-frontier (sealed only): {:?}", frontier);

    let get = |name: &str| rows.iter().find(|r| r.0 == name).map(|r| (r.1, r.2)).unwrap();
    let beats = |a: (f64, f64), b: (f64, f64)| dominates(a, b);   // a ε-dominates b
    let (u, pf, c1, c23) = (get("uniform"), get("present_pfal"), get("causal_future_d1"), get("causal_future_d23"));
    println!("  → causal_future_d23 ε-dominates uniform:      {}", beats(c23, u));
    println!("  → causal_future_d23 ε-dominates present_pfal:  {}", beats(c23, pf));
    println!("  → causal_future_d23 vs causal_future_d1:       {}",
             if beats(c23, c1) { "d23 dominates d1" } else if beats(c1, c23) { "d1 dominates d23" } else { "incomparable / tied within ε" });
    let prophet_gap_px = c23.0 - pp;
    println!("  → prophet calibration gap (causal_d23 pixel − prophet pixel) = {:.5} (≈ε ⇒ no hidden-future opportunity in THIS scene)", prophet_gap_px);

    println!("\nT3 (calibration baseline) COMPLETE — the verdict is a measured boundary, not a law. Reading: whether");
    println!("sealed causal allocation beats uniform/present_pfal on FUTURE error tells whether the temporal lever");
    println!("(serve under-accumulated revealed tiles, waste nothing on soon-reset occluded ones) pays off HERE.");
    println!("The prophet's near-tie with causal is a PROPERTY OF THIS MONOTONE SCENE (present predicts future),");
    println!("NOT a fundamental ceiling — the discriminating test is T4: a scene whose future relevance is HIDDEN");
    println!("from present state, where the prophet can genuinely outperform a sealed policy. benchmark gain ≠ universal.");
    // apparatus sanity (not a verdict): a frontier exists and the budget gate held for every policy.
    assert!(!frontier.is_empty(), "no frontier — apparatus error");
}
