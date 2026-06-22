// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6d / T4: the HIDDEN-FUTURE scene + precursor sweep (the deep temporal test).
//!
//! T3 showed sealed causal allocation reaches the oracle ceiling — but on a MONOTONE scene where the prophet
//! collapses onto the sealed policy (present already predicts future). That cannot answer the deep question:
//! can a sealed policy recover future structure that is NOT visible in present state? T4 builds the scene
//! where it can fail, and the prophet finally becomes informative.
//!
//! THE HIDDEN CHANNEL (importance, not content — chosen so it is exploitable under the FIXED T2 coupling).
//! A content-difficulty spike would change content → trigger disocclusion reset → forbid preparation → the
//! prophet could not separate (T3's tautology again). So instead: every tile's CONTENT is STABLE across all
//! frames (no reset; accumulation survives), but a TF-time world event makes some tiles MATTER more — the
//! ruler weights per-tile error by `future_importance`, set by future dynamics invisible in present pixels.
//! Pre-accumulating a soon-to-be-important STABLE tile survives to TF and lowers weighted error — but only the
//! prophet knows which tiles those are. The coupling is UNCHANGED from T2 (one variable moved: scene only).
//!
//! THE PRECURSOR KNOB ρ ∈ [0,1] (the temporal analogue of M6c's alignment). Each tile carries a present-
//! observable `precursor = ρ·importance + (1−ρ)·noise`. At ρ=0 the future is genuinely hidden (precursor is
//! noise); at ρ=1 the present fully signals it. Swept → the curve `gap(ρ) = prophet − causal_future`, which
//! MEASURES how much latent future structure a sealed policy can recover without seeing the future: wide at
//! ρ=0 (inaccessible), collapsing toward 0 at ρ=1 (present suffices).
//!
//! Sealed policies (uniform, precursor_pfal ∝ precursor, causal_future ∝ precursor·deficit — present
//! precursor + own accumulation only) + one NON-ADMISSIBLE prophet (∝ true importance·deficit). Verdict is an
//! importance-weighted Pareto VECTOR (pixel + structural). `benchmark gain ≠ universal`; the prophet is a
//! ceiling, not a contender.
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
const AMP: f32 = 0.7;         // every tile's STABLE difficulty (so the lever is importance, not difficulty)
const B_FRAME: u32 = 256;     // per-frame budget — scarce: cannot accumulate all 64 tiles to convergence
const TARGET: u32 = 128;      // per-tile accumulation target (deficit basis)
const IMP_HIGH: f64 = 9.0;
const IMP_LOW: f64 = 1.0;

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

/// True future importance (set by a TF-time world event; invisible in present pixels). 8 of 64 tiles matter.
fn importance() -> Vec<f64> { (0..TILES).map(|t| if t % 8 == 3 { IMP_HIGH } else { IMP_LOW }).collect() }
/// Per-tile present noise, independent of importance.
fn noise(t: usize) -> f64 { (t.wrapping_mul(2654435761) % 997) as f64 / 997.0 }
/// Present-observable precursor: ρ·(importance signal) + (1−ρ)·noise. ρ=0 ⇒ hidden; ρ=1 ⇒ fully signalled.
fn precursor(rho: f64, imp_norm: &[f64]) -> Vec<f64> {
    (0..TILES).map(|t| rho * imp_norm[t] + (1.0 - rho) * noise(t)).collect()
}
fn deficit(acc: u32) -> u32 { TARGET.saturating_sub(acc.min(TARGET)) }

fn world_state_str(frame: usize) -> String { format!("stable@f{}", frame) }
fn evolve_through_kernel(frames: usize) -> Vec<String> {
    let mut core = Core::new();
    let mut chain = Vec::new();
    let mut prev_digest: Option<String> = None;
    let mut prev_state = "stable@f-1".to_string();
    for t in 0..frames {
        let ns = world_state_str(t);
        let ev = Event::new("scene", &prev_state, &ns, &format!("stable_world@f{}", t)).unwrap();
        let rec = core.apply(&ev, prev_digest.as_deref()).expect("commit");
        chain.push(rec.provenance_digest.clone());
        prev_digest = Some(rec.provenance_digest); prev_state = ns;
    }
    chain
}

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

/// Allocate this frame's budget by a signal (precursor for sealed, true importance for the prophet), optionally
/// scaled by the per-tile accumulation deficit (water-fill in time). Sealed callers pass the PRECURSOR only.
fn alloc_by_signal(signal: &[f64], acc: &[u32], b: u32, use_deficit: bool) -> Vec<u32> {
    let w: Vec<f64> = (0..TILES).map(|t| if use_deficit { signal[t] * deficit(acc[t]) as f64 } else { signal[t] }).collect();
    hamilton(&w, b)
}

/// Stable-content accumulation (NO reset — content never changes). Returns (effective@TF, total allocated).
fn simulate(mut f: impl FnMut(&[u32]) -> Vec<u32>) -> (Vec<u32>, u32) {
    let mut acc = vec![0u32; TILES];
    let mut allocated = 0u32;
    for _ in 0..=TF {
        let al = f(&acc);
        allocated += al.iter().sum::<u32>();
        for t in 0..TILES { acc[t] = (acc[t] + al[t]).min(REF_SAMPLES); }
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
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor { label: Some("T4"), required_features: wgpu::Features::empty(), required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default() }, None).block_on().expect("device");
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
fn pixel_diff_map(a: &[u8], b: &[u8]) -> Vec<f64> {
    r_channel(a).iter().zip(r_channel(b).iter()).map(|(x, y)| (x - y).abs()).collect()
}
fn grad_diff_map(a: &[u8], b: &[u8]) -> Vec<f64> {
    grad(a).iter().zip(grad(b).iter()).map(|(x, y)| (x - y).abs()).collect()
}
fn per_tile_mean(perpix: &[f64]) -> Vec<f64> {
    let n = RES as usize; let tp = (RES / TILES_X) as usize;
    let mut sum = vec![0.0; TILES]; let mut cnt = vec![0.0; TILES];
    for y in 0..n { for x in 0..n { let t = (y / tp) * (TILES_X as usize) + (x / tp); sum[t] += perpix[y * n + x]; cnt[t] += 1.0; } }
    (0..TILES).map(|t| sum[t] / cnt[t]).collect()
}
fn spread(v: &[f64]) -> f64 { v.iter().cloned().fold(f64::MIN, f64::max) - v.iter().cloned().fold(f64::MAX, f64::min) }

fn main() {
    let gpu = Gpu::init();
    println!("M6d / T4 — HIDDEN-FUTURE importance scene + precursor sweep on {} ({})", gpu.device_name, gpu.backend);
    let chain = evolve_through_kernel(TF + 1);
    println!("world ran through the kernel ({} commits; head {}); CONTENT stable (no reset) — the hidden channel is future IMPORTANCE, not difficulty",
             chain.len(), chain.first().cloned().unwrap_or_default());
    println!("ruler = importance-weighted future error; sealed policies see a precursor (ρ·importance+(1−ρ)·noise), never true importance\n");

    let imp = importance();
    let imp_norm: Vec<f64> = imp.iter().map(|&x| x / IMP_HIGH).collect();
    let amp_all = vec![AMP; TILES];
    let budget_each = B_FRAME * (TF as u32 + 1);
    let reference = gpu.render(&amp_all, &vec![REF_SAMPLES; TILES], 0);

    // importance-weighted future-error vector of an effective-sample map
    let score = |eff: &[u32], seed: u32| -> (f64, f64) {
        let px = gpu.render(&amp_all, eff, seed);
        let tp = per_tile_mean(&pixel_diff_map(&px, &reference));
        let ts = per_tile_mean(&grad_diff_map(&px, &reference));
        let wsum: f64 = imp.iter().sum();
        let wp = (0..TILES).map(|t| imp[t] * tp[t]).sum::<f64>() / wsum;
        let ws = (0..TILES).map(|t| imp[t] * ts[t]).sum::<f64>() / wsum;
        (wp, ws)
    };

    let mut pass = 0u32; let mut total = 0u32;
    let mut check = |name: &str, ok: bool, detail: String| {
        total += 1; if ok { pass += 1; }
        println!("  [{}] {:<28} {}", if ok { "PASS" } else { "FAIL" }, name, detail);
    };

    // ---- apparatus checks (the importance-weighted ruler must be trustworthy first) ----
    let e_lo = score(&vec![8u32; TILES], 7).0;
    let e_hi = score(&vec![64u32; TILES], 7).0;
    check("weighted_error_responds", e_lo > e_hi && e_hi > 0.0, format!("weighted err @8spp {:.5} > @64spp {:.5} > 0", e_lo, e_hi));

    let nc = score(&vec![REF_SAMPLES; TILES], 0).0;
    check("negative_control_zero", nc == 0.0, format!("reference-as-effective weighted error = {:.6}", nc));

    let (eff_u, au) = simulate(|_acc| hamilton(&vec![1.0; TILES], B_FRAME));
    assert_eq!(au, budget_each, "uniform must spend the equal budget");
    let (pe, se): (Vec<f64>, Vec<f64>) = [11u32, 22, 33, 44].iter().map(|&s| score(&eff_u, s)).unzip();
    let eps = [spread(&pe), spread(&se)];
    check("reproducibility_floor", eps[0] >= 0.0 && eps[0] < 0.002, format!("ε(weighted pixel/struct) = {:.6} / {:.6}", eps[0], eps[1]));

    // ---- the precursor sweep: gap(ρ) = causal_future − prophet on the importance-weighted ruler ----
    println!("\n  ρ      uniform   precursor_pfal  causal_future   prophet    gap(causal−prophet)   causal⪯uniform?");
    let dominates = |a: (f64, f64), b: (f64, f64)| (a.0 <= b.0 + eps[0] && a.1 <= b.1 + eps[1]) && (a.0 < b.0 - eps[0] || a.1 < b.1 - eps[1]);
    let prophet = { let (e, ab) = simulate(|acc| alloc_by_signal(&imp, acc, B_FRAME, true)); assert_eq!(ab, budget_each); score(&e, 7) };
    let rhos = [0.0f64, 0.25, 0.5, 0.75, 1.0];
    let mut gaps: Vec<(f64, f64)> = Vec::new();
    for &rho in rhos.iter() {
        let prec = precursor(rho, &imp_norm);
        let su = score(&simulate(|_acc| hamilton(&vec![1.0; TILES], B_FRAME)).0, 7);
        let spf = score(&simulate(|acc| alloc_by_signal(&prec, acc, B_FRAME, false)).0, 7);
        let scf = score(&simulate(|acc| alloc_by_signal(&prec, acc, B_FRAME, true)).0, 7);
        let gap = scf.0 - prophet.0;
        gaps.push((rho, gap));
        println!("  {:.2}   {:.5}   {:.5}         {:.5}        {:.5}    {:+.5}             {}",
                 rho, su.0, spf.0, scf.0, prophet.0, gap, dominates(scf, su));
    }
    println!("  measured ε floor (pixel/struct) = {:.6} / {:.6}   ·   prophet is a NON-ADMISSIBLE ceiling", eps[0], eps[1]);

    // ---- sweep-derived checks: the channel must be real (ρ=0 prophet separates) and closable (ρ=1 reached) ----
    let gap0 = gaps.first().unwrap().1;
    let gap1 = gaps.last().unwrap().1;
    check("channel_real_at_rho0", gap0 > eps[0], format!("ρ=0 gap {:.5} > ε {:.6} — future is genuinely hidden; oracle separates", gap0, eps[0]));
    check("ceiling_reached_at_rho1", gap1 <= eps[0].max(1e-6), format!("ρ=1 gap {:+.5} ≤ ε — present fully signals; sealed reaches the oracle", gap1));
    let monotone = gaps.windows(2).all(|w| w[1].1 <= w[0].1 + eps[0]);
    check("gap_closes_with_rho", monotone, "gap(ρ) is (weakly) decreasing — recoverability rises with precursor strength".into());

    println!("\nT4 {} — {}/{} apparatus/sweep checks. The deliverable is the CURVE gap(ρ): the value of future", if pass == total { "COMPLETE" } else { "INCOMPLETE" }, pass, total);
    println!("information a sealed policy CANNOT recover. Wide at ρ=0 (future hidden — prophet wins), closing to ≈0 at");
    println!("ρ=1 (present suffices). This is the temporal analogue of M6c's alignment sweep: not 'who wins', but a");
    println!("measured boundary of how much latent future structure is recoverable from present state — coupling FIXED,");
    println!("scene the only variable. benchmark gain ≠ universal; the prophet is a ceiling, never a contender.");
    assert!(pass == total, "T4 apparatus/sweep sanity did not fully hold");
}
