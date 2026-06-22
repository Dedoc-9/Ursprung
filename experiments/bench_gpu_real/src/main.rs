// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6b: the Causal Continuity gate on the perceptual ruler (real falsification).
//!
//! M6a built a fair, blind perceptual ruler. M6b finally compares allocation POLICIES on it — the gate that
//! can move Causal Continuity from `supported_constructed` to *supported-on-silicon within this domain*, OR
//! falsify it. Every policy allocates the **per-tile sample budget** under an **equal total budget**; the
//! evaluator (the M6a ruler) measures the resulting error vector against a frozen reference.
//!
//! THE SEALED OBSERVER (the load-bearing rule). A policy receives ONLY declared per-tile priors
//! (`TilePriors`) and the budget. It does NOT receive the rendered pixels, the reference, or the scene's
//! ground-truth per-tile difficulty (`tile_amp`). Those are not in its function's scope — so "optimize the
//! metric" is structurally unrepresentable. The ruler is a sealed evaluator; the benchmark is not a
//! metric-optimization loop. (That loop is exactly the Goodhart failure the project exists to detect.)
//!
//! THE BOUNDARY-CONDITION DESIGN. Two scenes are run: `aligned` (the declared causal priors correlate with
//! real per-tile difficulty) and `adversarial` (priors anti-correlate). The valuable result is not "causal
//! wins" — it is *where* causal allocation helps and *where* it hurts, turning a slogan into a boundary.
//!
//! HONEST CEILING. Even a clean win is "supported on THIS device, THESE scenes, THIS metric" —
//! `benchmark gain ≠ universal`. M6b reports which policies occupy the Pareto frontier, never a crowned king.
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;

use pollster::FutureExt as _;
use serde::{Deserialize, Serialize};

const RES: u32 = 256;
const BYTES_PER_ROW: u32 = RES * 4;
const TILES_X: u32 = 8; // 8×8 = 64 tiles, each 32×32 px
const TILES: usize = (TILES_X * TILES_X) as usize;
const REF_SAMPLES: u32 = 256;
const TOTAL_BUDGET: u32 = TILES as u32 * 16; // all policies distribute the SAME total sample budget
const TOLERANCE: f64 = 0.20; // M5 fairness gate on MEASURED ticks

const SCENE_WGSL: &str = r#"
struct U { seed: u32, res: u32, tiles_x: u32, _pad: u32 };
@group(0) @binding(0) var<uniform> u: U;
@group(0) @binding(1) var<storage, read> tile_amp: array<f32>;     // WORLD difficulty per tile (ground truth)
@group(0) @binding(2) var<storage, read> tile_samples: array<u32>; // the ALLOCATION per tile (policy output)

fn scene(p: vec2<f32>, amp: f32) -> f32 {
    let hf = sin(p.x * 120.0) * sin(p.y * 120.0);   // high-frequency: amp controls how hard the tile is
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

// --- declared per-tile priors (the ONLY thing a policy sees) --------------------------------------
#[derive(Clone)]
struct TilePriors {
    consequence: Vec<f64>, // declared "how much this tile matters"
    uncertainty: Vec<f64>,
    persistence: Vec<f64>,
    sensitivity: Vec<f64>, // present perceptual loudness (PFAL's S)
    distance: Vec<f64>,
    visibility: Vec<f64>,
    resistance: Vec<f64>,  // declared representation difficulty (perimeter-like)
}

// --- the world (NOT visible to any policy) --------------------------------------------------------
struct Scene { name: &'static str, tile_amp: Vec<f32>, priors: TilePriors }

fn build_scene(name: &'static str, aligned: bool) -> Scene {
    // ground-truth difficulty: a fixed pattern over tiles (some hard, some flat)
    let amp: Vec<f64> = (0..TILES).map(|t| {
        let x = (t as u32 % TILES_X) as f64; let y = (t as u32 / TILES_X) as f64;
        0.15 + 0.85 * (0.5 + 0.5 * ((x * 0.9).sin() * (y * 1.3).cos()))
    }).collect();
    // declared causal priors: ALIGNED ⇒ track difficulty; ADVERSARIAL ⇒ anti-track it.
    let consequence: Vec<f64> = amp.iter().map(|&a| if aligned { a } else { 1.0 - a }).collect();
    let mk = |f: &dyn Fn(usize) -> f64| (0..TILES).map(f).collect::<Vec<f64>>();
    Scene {
        name,
        tile_amp: amp.iter().map(|&a| a as f32).collect(),
        priors: TilePriors {
            consequence: consequence.clone(),
            uncertainty: consequence.iter().map(|&c| 0.5 + 0.5 * c).collect(),
            persistence: mk(&|t| 1.0 + (t % 4) as f64),
            sensitivity: mk(&|t| 0.3 + 0.7 * (((t * 7) % 11) as f64 / 10.0)), // independent of difficulty
            distance: mk(&|t| 1.0 + (t % 9) as f64),                          // geometry, independent
            visibility: mk(&|t| 0.2 + 0.8 * (((t * 5) % 13) as f64 / 12.0)),  // geometry, independent
            resistance: consequence.iter().map(|&c| 1.0 + 3.0 * c).collect(), // declared difficulty proxy
        },
    }
}

// --- SEALED policies: signature exposes ONLY priors + budget (no pixels, reference, or tile_amp) ---
fn hamilton(weights: &[f64], total: u32) -> Vec<u32> {
    let n = weights.len();
    let w: Vec<f64> = weights.iter().map(|x| x.max(1e-9)).collect();
    let sum: f64 = w.iter().sum();
    // reserve 1 sample/tile (a tile must render), distribute the rest by weight
    let rest = total.saturating_sub(n as u32);
    let mut alloc: Vec<u32> = w.iter().map(|&x| 1 + (x / sum * rest as f64) as u32).collect();
    // fix rounding so the total is exact
    let mut spent: u32 = alloc.iter().sum();
    let mut order: Vec<usize> = (0..n).collect();
    order.sort_by(|&a, &b| w[b].partial_cmp(&w[a]).unwrap());
    let mut i = 0;
    while spent < total { let k = order[i % n]; alloc[k] += 1; spent += 1; i += 1; }
    while spent > total { let k = order[n - 1 - (i % n)]; if alloc[k] > 1 { alloc[k] -= 1; spent -= 1; } i += 1; }
    alloc
}

type Policy = fn(&TilePriors, u32) -> Vec<u32>;

fn p_uniform(pr: &TilePriors, total: u32) -> Vec<u32> { hamilton(&vec![1.0; pr.consequence.len()], total) }
fn p_distance(pr: &TilePriors, total: u32) -> Vec<u32> { hamilton(&pr.distance.iter().map(|&d| 1.0 / (d + 1.0)).collect::<Vec<_>>(), total) }
fn p_visibility(pr: &TilePriors, total: u32) -> Vec<u32> { hamilton(&pr.visibility, total) }
fn p_pfal(pr: &TilePriors, total: u32) -> Vec<u32> {
    // PFAL priority U·C·P·S, water-filled under resistance: ∝ √(priority · resistance)
    let w: Vec<f64> = (0..pr.consequence.len()).map(|t| {
        let prio = pr.uncertainty[t] * pr.consequence[t] * pr.persistence[t] * pr.sensitivity[t];
        (prio * pr.resistance[t]).sqrt()
    }).collect();
    hamilton(&w, total)
}
fn p_causal(pr: &TilePriors, total: u32) -> Vec<u32> {
    // the candidate: future-causal U·C·P (drop present-perception S), water-filled under resistance
    let w: Vec<f64> = (0..pr.consequence.len()).map(|t| {
        let prio = pr.uncertainty[t] * pr.consequence[t] * pr.persistence[t];
        (prio * pr.resistance[t]).sqrt()
    }).collect();
    hamilton(&w, total)
}
fn p_drifted(pr: &TilePriors, total: u32) -> Vec<u32> {
    // negative control: structure-blind pseudo-random allocation at the SAME budget
    let w: Vec<f64> = (0..pr.consequence.len()).map(|t| ((t * 2654435761usize) % 997) as f64 + 1.0).collect();
    hamilton(&w, total)
}

// --- the M6a perceptual ruler (sealed evaluator) --------------------------------------------------
#[derive(Serialize, Deserialize, PartialEq, Debug, Clone, Copy)]
struct ErrorProfile { pixel: f64, structural: f64, temporal: f64 }
impl ErrorProfile { fn axes(&self) -> [f64; 3] { [self.pixel, self.structural, self.temporal] } }

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

// --- pre-registered outcome (fixed before running) -----------------------------------------------
#[derive(Serialize, Debug, Clone)]
struct PolicyOutcome {
    policy: String,
    budget_ms: f64,
    total_samples: u32,
    perceptual_error: ErrorProfile,
    transition_cost: Option<f64>, // n/a this bench (single frame) — recorded as None, not faked
    admitted: bool,               // equal-budget (M5 gate)
    notes: String,
}

struct Gpu { device: wgpu::Device, queue: wgpu::Queue, pipeline: wgpu::RenderPipeline, bgl: wgpu::BindGroupLayout,
             tex: wgpu::Texture, view: wgpu::TextureView, period_ns: f32, device_name: String, backend: String }

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor { backends: wgpu::Backends::PRIMARY, ..Default::default() });
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions { power_preference: wgpu::PowerPreference::HighPerformance, force_fallback_adapter: false, compatible_surface: None }).block_on().expect("no adapter");
        let info = adapter.get_info();
        if !adapter.features().contains(wgpu::Features::TIMESTAMP_QUERY) { eprintln!("RULER ABSENT: TIMESTAMP_QUERY"); std::process::exit(1); }
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor { label: Some("M6b"), required_features: wgpu::Features::TIMESTAMP_QUERY, required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default() }, None).block_on().expect("device");
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
        Gpu { period_ns: queue.get_timestamp_period(), device_name: info.name.clone(), backend: format!("{:?}", info.backend), device, queue, pipeline, bgl, tex, view }
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

    /// render scene (tile_amp) with allocation (tile_samples) at jitter seed → (pixels, ticks)
    fn render(&self, tile_amp: &wgpu::Buffer, tile_samples: &[u32], seed: u32) -> (Vec<u8>, i128) {
        let samp = self.storage_u32(tile_samples);
        let ubuf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("u"), size: 16, usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let mut u = [0u8; 16];
        u[0..4].copy_from_slice(&seed.to_le_bytes()); u[4..8].copy_from_slice(&RES.to_le_bytes()); u[8..12].copy_from_slice(&TILES_X.to_le_bytes());
        self.queue.write_buffer(&ubuf, 0, &u);
        let bind = self.device.create_bind_group(&wgpu::BindGroupDescriptor { label: Some("bg"), layout: &self.bgl, entries: &[
            wgpu::BindGroupEntry { binding: 0, resource: ubuf.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 1, resource: tile_amp.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 2, resource: samp.as_entire_binding() },
        ]});
        let qs = self.device.create_query_set(&wgpu::QuerySetDescriptor { label: Some("ts"), ty: wgpu::QueryType::Timestamp, count: 2 });
        let qres = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("qr"), size: 16, usage: wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC, mapped_at_creation: false });
        let qread = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("qrd"), size: 16, usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let pxbuf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("px"), size: (BYTES_PER_ROW * RES) as u64, usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let mut enc = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = enc.begin_render_pass(&wgpu::RenderPassDescriptor { label: Some("p"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment { view: &self.view, resolve_target: None, ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Store } })],
                depth_stencil_attachment: None,
                timestamp_writes: Some(wgpu::RenderPassTimestampWrites { query_set: &qs, beginning_of_pass_write_index: Some(0), end_of_pass_write_index: Some(1) }),
                occlusion_query_set: None });
            pass.set_pipeline(&self.pipeline); pass.set_bind_group(0, &bind, &[]); pass.draw(0..3, 0..1);
        }
        enc.resolve_query_set(&qs, 0..2, &qres, 0);
        enc.copy_buffer_to_buffer(&qres, 0, &qread, 0, 16);
        enc.copy_texture_to_buffer(
            wgpu::ImageCopyTexture { texture: &self.tex, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
            wgpu::ImageCopyBuffer { buffer: &pxbuf, layout: wgpu::ImageDataLayout { offset: 0, bytes_per_row: Some(BYTES_PER_ROW), rows_per_image: Some(RES) } },
            wgpu::Extent3d { width: RES, height: RES, depth_or_array_layers: 1 });
        self.queue.submit(Some(enc.finish()));
        let s1 = qread.slice(..); let (t1, r1) = std::sync::mpsc::channel(); s1.map_async(wgpu::MapMode::Read, move |r| { let _ = t1.send(r); });
        let s2 = pxbuf.slice(..); let (t2, r2) = std::sync::mpsc::channel(); s2.map_async(wgpu::MapMode::Read, move |r| { let _ = t2.send(r); });
        self.device.poll(wgpu::Maintain::Wait); r1.recv().unwrap().unwrap(); r2.recv().unwrap().unwrap();
        let qd = s1.get_mapped_range(); let begin = u64::from_le_bytes(qd[0..8].try_into().unwrap()); let end = u64::from_le_bytes(qd[8..16].try_into().unwrap()); drop(qd); qread.unmap();
        let pd = s2.get_mapped_range(); let pixels = pd.to_vec(); drop(pd); pxbuf.unmap();
        (pixels, end as i128 - begin as i128)
    }
}

fn median_i(mut v: Vec<i128>) -> i128 { v.sort(); v[v.len() / 2] }

fn main() {
    let gpu = Gpu::init();
    println!("M6b — Causal Continuity gate on the perceptual ruler (SEALED evaluator) on {} ({})\n", gpu.device_name, gpu.backend);
    let policies: [(&str, Policy); 6] = [
        ("uniform", p_uniform), ("distance", p_distance), ("visibility", p_visibility),
        ("pfal", p_pfal), ("causal_waterfill", p_causal), ("drifted(control)", p_drifted),
    ];

    let mut all_ok = true;
    for &(aligned, sname) in &[(true, "aligned"), (false, "adversarial")] {
        let scene = build_scene(sname, aligned);
        let amp_buf = gpu.storage_f32(&scene.tile_amp);
        // warm-up (discarded) absorbs cold-start; reference at full samples
        let _ = gpu.render(&amp_buf, &vec![8u32; TILES], 99);
        let (reference, _) = gpu.render(&amp_buf, &vec![REF_SAMPLES; TILES], 0);

        println!("=== scene: {} (declared causal priors {} real difficulty) ===",
                 scene.name, if aligned { "ALIGN with" } else { "ANTI-CORRELATE with" });
        let target_ticks = {
            let alloc = p_uniform(&scene.priors, TOTAL_BUDGET);
            median_i((0..5).map(|_| gpu.render(&amp_buf, &alloc, 1).1).collect())
        } as f64;

        let mut outcomes = Vec::new();
        for (name, pol) in policies.iter() {
            let alloc = pol(&scene.priors, TOTAL_BUDGET);       // SEALED: priors + budget only
            let total: u32 = alloc.iter().sum();
            let ticks = median_i((0..5).map(|_| gpu.render(&amp_buf, &alloc, 1).1).collect());
            let (px_a, _) = gpu.render(&amp_buf, &alloc, 11);
            let (px_b, _) = gpu.render(&amp_buf, &alloc, 22);
            let prof = ErrorProfile { pixel: pixel_err(&px_a, &reference), structural: struct_err(&px_a, &reference), temporal: pixel_err(&px_a, &px_b) };
            let admitted = (ticks as f64 - target_ticks).abs() <= TOLERANCE * target_ticks.max(1.0);
            outcomes.push(PolicyOutcome {
                policy: name.to_string(), budget_ms: ticks as f64 * gpu.period_ns as f64 / 1e6,
                total_samples: total, perceptual_error: prof, transition_cost: None, admitted,
                notes: if admitted { "".into() } else { "budget_violation — excluded from frontier".into() },
            });
        }

        // report: pre-registered outcomes, then dominance + Pareto frontier (admitted only)
        for o in &outcomes {
            println!("  {:<18} budget {:.4} ms · samples {} · err pixel/struct/temporal {:.5}/{:.5}/{:.5} · admitted {}{}",
                     o.policy, o.budget_ms, o.total_samples, o.perceptual_error.pixel, o.perceptual_error.structural,
                     o.perceptual_error.temporal, o.admitted, if o.notes.is_empty() { "".into() } else { format!(" [{}]", o.notes) });
        }
        let adm: Vec<&PolicyOutcome> = outcomes.iter().filter(|o| o.admitted).collect();

        // measure the per-axis reproducibility FLOOR (ε) from the uniform allocation across seed pairs.
        // dominance below this floor is noise, not a result — so the frontier uses ε-dominance, not <.
        let ucal = p_uniform(&scene.priors, TOTAL_BUDGET);
        let cal: Vec<[f64; 3]> = [(11u32, 22u32), (33, 44), (55, 66), (77, 88)].iter().map(|&(sa, sb)| {
            let (a, _) = gpu.render(&amp_buf, &ucal, sa);
            let (b, _) = gpu.render(&amp_buf, &ucal, sb);
            [pixel_err(&a, &reference), struct_err(&a, &reference), pixel_err(&a, &b)]
        }).collect();
        let eps: [f64; 3] = [0, 1, 2].map(|i| {
            let v: Vec<f64> = cal.iter().map(|p| p[i]).collect();
            v.iter().cloned().fold(f64::NEG_INFINITY, f64::max) - v.iter().cloned().fold(f64::INFINITY, f64::min)
        });
        println!("  measured noise floor ε (pixel/struct/temporal) = {:.6}/{:.6}/{:.6}", eps[0], eps[1], eps[2]);

        // ε-dominance: A dominates B only if better by MORE than ε on ≥1 axis and not worse by > ε on any axis.
        let dominates = |a: &ErrorProfile, b: &ErrorProfile| {
            let (x, y) = (a.axes(), b.axes());
            (0..3).all(|i| x[i] <= y[i] + eps[i]) && (0..3).any(|i| x[i] < y[i] - eps[i])
        };
        let frontier: Vec<&str> = adm.iter().filter(|o| !adm.iter().any(|p| dominates(&p.perceptual_error, &o.perceptual_error)))
            .map(|o| o.policy.as_str()).collect();
        let causal = adm.iter().find(|o| o.policy == "causal_waterfill");
        let king = adm.iter().find(|o| adm.iter().all(|p| std::ptr::eq(*p, **o) || dominates(&o.perceptual_error, &p.perceptual_error)));
        println!("  → Pareto frontier (equal budget): {:?}", frontier);
        println!("  → dominant policy (beats all on every axis): {}",
                 king.map(|k| k.policy.clone()).unwrap_or_else(|| "none — tradeoffs only".into()));
        println!("  → causal_waterfill on the frontier: {}\n",
                 causal.map(|c| frontier.contains(&c.policy.as_str())).unwrap_or(false));

        // M6b is honest as long as the apparatus held: budgets equal (admitted set non-empty) and a
        // frontier was computed. The VERDICT (who wins / whether causal holds) is reported, never asserted.
        all_ok &= !adm.is_empty() && !frontier.is_empty();
    }

    println!("BOUNDARY-CONDITION READING (ε-aware): on the ε-frontier means NOT MEASURABLY WORSE than the best —");
    println!("it is parity, never proof of improvement. If causal_waterfill is on the ε-frontier under 'aligned'");
    println!("but off it under 'adversarial', the honest claim is: aligned causal priors cost nothing measurable,");
    println!("misaligned ones measurably hurt — an ASYMMETRIC, downside-only profile at this budget. That is a");
    println!("PARTIAL FALSIFICATION of the constructed gate's blessing: a neutral ruler shows no measured upside");
    println!("for causal allocation, only downside risk. HONEST CEILING: this device/scene/budget/metric, not a law.");
    println!("\nM6b {} — the SEALED gate ran: policies allocated from priors only, were compared at equal measured",
             if all_ok { "COMPLETE" } else { "INCONCLUSIVE" });
    println!("budget on a blind perceptual ruler, and the frontier was reported. No policy was crowned by fiat.");
    assert!(all_ok, "M6b apparatus did not hold (empty admitted set or frontier)");
}
