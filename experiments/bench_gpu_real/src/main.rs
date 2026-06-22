// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6c: the alignment × budget × exponent sweep (chasing M6b's ghost).
//!
//! M6b found a *narrow* falsification: at 16 samples/tile, on this scene/metric/device, causal-waterfill
//! allocation showed no measured upside over uniform and a temporal downside. M6b left three separable
//! questions open, and M6c turns each into a swept axis instead of a slogan:
//!
//!   (a) BUDGET.    At ~16 samples/tile every tile is already near-converged — redistribution had no room
//!                  to win. Does a LOWER budget (tiles genuinely unconverged) ever let causal reach the
//!                  ε-frontier? Budget is swept over {2,4,8,16,64} avg samples/tile.
//!   (b) ALIGNMENT. The declared causal priors may be informative or wrong. `prior_alignment α ∈ [-1,1]`
//!                  (1 = perfect prior, 0 = random, -1 = inverted) is swept to produce a CURVE, not 2 points.
//!   (c) EXPONENT.  The variance-optimal allocation for SSAA error scales as ∝ difficulty^(2/3); causal-
//!                  waterfill allocates ∝ difficulty^1 (it likely OVER-concentrates). So two causal policies
//!                  run side by side: `causal_d1` (√(U·C·P·resistance) ≈ difficulty^1) and `causal_d23`
//!                  ((U·C·P·resistance)^(1/3) ≈ difficulty^(2/3), the variance-optimal exponent).
//!
//! SEALED OBSERVER preserved exactly (M6b's load-bearing rule): every policy is `fn(&TilePriors,u32) ->
//! Vec<u32>` — it never sees pixels, the reference, or the ground-truth difficulty. The ε-frontier is
//! computed with ε MEASURED PER CELL from the data (noise grows as budget shrinks; you cannot claim
//! dominance below your own noise). Policy set is reduced to {uniform, causal_d1, causal_d23, drifted} to
//! ISOLATE the causal-vs-neutral question — distance/visibility were dominated in M6b and are not the
//! question here. Output reports ε-frontier membership + dominated_by per cell, never a "winner".
//!
//! HONEST CEILING unchanged: one device, one synthetic scene family, SSAA proxy. A cell where causal reaches
//! the frontier is "supported at THAT budget/alignment here", not a law. `benchmark gain ≠ universal`.
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;

use pollster::FutureExt as _;
use serde::{Deserialize, Serialize};

const RES: u32 = 256;
const BYTES_PER_ROW: u32 = RES * 4;
const TILES_X: u32 = 8;
const TILES: usize = (TILES_X * TILES_X) as usize;
const REF_SAMPLES: u32 = 256;
const TOLERANCE: f64 = 0.20;

// swept axes
const BUDGETS_AVG: [u32; 5] = [2, 4, 8, 16, 64];          // avg samples/tile → total = avg * TILES
const ALPHAS: [f64; 5] = [1.0, 0.5, 0.0, -0.5, -1.0];     // prior alignment with real difficulty

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

// --- declared per-tile priors (the ONLY thing a policy sees) --------------------------------------
#[derive(Clone)]
struct TilePriors {
    uncertainty: Vec<f64>,
    consequence: Vec<f64>,
    persistence: Vec<f64>,
    resistance: Vec<f64>,
}

struct Scene { tile_amp: Vec<f32>, priors: TilePriors }

/// alignment-parameterized scene. amp is the fixed WORLD difficulty; the declared prior tracks it (α>0),
/// is random (α=0), or is inverted (α<0). corr(prior, amp) ≈ α. The policy sees only the prior.
fn build_scene(alpha: f64) -> Scene {
    let amp: Vec<f64> = (0..TILES).map(|t| {
        let x = (t as u32 % TILES_X) as f64; let y = (t as u32 / TILES_X) as f64;
        0.15 + 0.85 * (0.5 + 0.5 * ((x * 0.9).sin() * (y * 1.3).cos()))
    }).collect();
    // deterministic per-tile noise, independent of amp
    let rnd: Vec<f64> = (0..TILES).map(|t| ((t * 2654435761usize) % 1009) as f64 / 1008.0).collect();
    // blend toward the (correct or inverted) signal by |α|, else random
    let prior: Vec<f64> = (0..TILES).map(|t| {
        let signal = if alpha >= 0.0 { amp[t] } else { 1.0 - amp[t] };
        let a = alpha.abs();
        ((1.0 - a) * rnd[t] + a * signal).clamp(0.0, 1.0)
    }).collect();
    Scene {
        tile_amp: amp.iter().map(|&a| a as f32).collect(),
        priors: TilePriors {
            uncertainty: prior.iter().map(|&c| 0.5 + 0.5 * c).collect(),
            consequence: prior.clone(),
            persistence: (0..TILES).map(|t| 1.0 + (t % 4) as f64).collect(),
            resistance: prior.iter().map(|&c| 1.0 + 3.0 * c).collect(),
        },
    }
}

// --- SEALED policies: priors + budget only --------------------------------------------------------
fn hamilton(weights: &[f64], total: u32) -> Vec<u32> {
    let n = weights.len();
    let w: Vec<f64> = weights.iter().map(|x| x.max(1e-9)).collect();
    let sum: f64 = w.iter().sum();
    let rest = total.saturating_sub(n as u32);
    let mut alloc: Vec<u32> = w.iter().map(|&x| 1 + (x / sum * rest as f64) as u32).collect();
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
fn p_causal_d1(pr: &TilePriors, total: u32) -> Vec<u32> {
    // ∝ √(U·C·P·resistance) ≈ difficulty^1 (the M6b causal-waterfill — likely over-concentrates)
    let w: Vec<f64> = (0..pr.consequence.len()).map(|t| {
        (pr.uncertainty[t] * pr.consequence[t] * pr.persistence[t] * pr.resistance[t]).sqrt()
    }).collect();
    hamilton(&w, total)
}
fn p_causal_d23(pr: &TilePriors, total: u32) -> Vec<u32> {
    // ∝ (U·C·P·resistance)^(1/3) ≈ difficulty^(2/3) — the VARIANCE-OPTIMAL exponent for SSAA error
    let w: Vec<f64> = (0..pr.consequence.len()).map(|t| {
        (pr.uncertainty[t] * pr.consequence[t] * pr.persistence[t] * pr.resistance[t]).powf(1.0 / 3.0)
    }).collect();
    hamilton(&w, total)
}
fn p_drifted(pr: &TilePriors, total: u32) -> Vec<u32> {
    let w: Vec<f64> = (0..pr.consequence.len()).map(|t| ((t * 40503usize) % 997) as f64 + 1.0).collect();
    hamilton(&w, total)
}

// --- the M6a perceptual ruler (sealed evaluator) --------------------------------------------------
#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
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

struct Gpu { device: wgpu::Device, queue: wgpu::Queue, pipeline: wgpu::RenderPipeline, bgl: wgpu::BindGroupLayout,
             tex: wgpu::Texture, view: wgpu::TextureView, device_name: String, backend: String }

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor { backends: wgpu::Backends::PRIMARY, ..Default::default() });
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions { power_preference: wgpu::PowerPreference::HighPerformance, force_fallback_adapter: false, compatible_surface: None }).block_on().expect("no adapter");
        let info = adapter.get_info();
        if !adapter.features().contains(wgpu::Features::TIMESTAMP_QUERY) { eprintln!("RULER ABSENT: TIMESTAMP_QUERY"); std::process::exit(1); }
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor { label: Some("M6c"), required_features: wgpu::Features::TIMESTAMP_QUERY, required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default() }, None).block_on().expect("device");
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

struct Cell { profile: ErrorProfile, ticks: i128, admitted: bool }

fn main() {
    let gpu = Gpu::init();
    println!("M6c — alignment × budget × exponent sweep (SEALED evaluator) on {} ({})", gpu.device_name, gpu.backend);
    println!("policies: uniform · causal_d1 (∝difficulty^1) · causal_d23 (∝difficulty^2/3, variance-optimal) · drifted(control)");
    println!("question: does causal allocation EVER reach the ε-frontier — at some budget / alignment / exponent?\n");

    let policies: [(&str, Policy); 4] = [
        ("uniform", p_uniform), ("causal_d1", p_causal_d1), ("causal_d23", p_causal_d23), ("drifted", p_drifted),
    ];
    // record where each causal policy reaches the ε-frontier
    let mut d1_hits: Vec<String> = Vec::new();
    let mut d23_hits: Vec<String> = Vec::new();
    let mut apparatus_ok = true;

    for &avg in BUDGETS_AVG.iter() {
        let total = avg * TILES as u32;
        println!("======== budget: {} avg samples/tile ({} total) ========", avg, total);
        for &alpha in ALPHAS.iter() {
            let scene = build_scene(alpha);
            let amp_buf = gpu.storage_f32(&scene.tile_amp);
            let _ = gpu.render(&amp_buf, &vec![avg; TILES], 99); // warm-up (discarded)
            let (reference, _) = gpu.render(&amp_buf, &vec![REF_SAMPLES; TILES], 0);

            // ε measured per cell from the uniform allocation across seed pairs (noise grows at low budget)
            let ucal = p_uniform(&scene.priors, total);
            let cal: Vec<[f64; 3]> = [(11u32, 22u32), (33, 44), (55, 66), (77, 88)].iter().map(|&(sa, sb)| {
                let (a, _) = gpu.render(&amp_buf, &ucal, sa);
                let (b, _) = gpu.render(&amp_buf, &ucal, sb);
                [pixel_err(&a, &reference), struct_err(&a, &reference), pixel_err(&a, &b)]
            }).collect();
            let eps: [f64; 3] = [0, 1, 2].map(|i| {
                let v: Vec<f64> = cal.iter().map(|p| p[i]).collect();
                v.iter().cloned().fold(f64::NEG_INFINITY, f64::max) - v.iter().cloned().fold(f64::INFINITY, f64::min)
            });

            // render every policy
            let mut cells: Vec<(String, Cell)> = Vec::new();
            let mut target_ticks = 1.0f64;
            for (name, pol) in policies.iter() {
                let alloc = pol(&scene.priors, total);
                let ticks = median_i((0..3).map(|_| gpu.render(&amp_buf, &alloc, 1).1).collect());
                if *name == "uniform" { target_ticks = ticks as f64; }
                let (px_a, _) = gpu.render(&amp_buf, &alloc, 11);
                let (px_b, _) = gpu.render(&amp_buf, &alloc, 22);
                let profile = ErrorProfile { pixel: pixel_err(&px_a, &reference), structural: struct_err(&px_a, &reference), temporal: pixel_err(&px_a, &px_b) };
                cells.push((name.to_string(), Cell { profile, ticks, admitted: true }));
            }
            // equal-budget gate (M5): all share the same total samples, so ticks should match uniform's
            for (_, c) in cells.iter_mut() {
                c.admitted = (c.ticks as f64 - target_ticks).abs() <= TOLERANCE * target_ticks.max(1.0);
            }

            // ε-dominance frontier among admitted policies (index-based: 0=uniform 1=d1 2=d23 3=drifted)
            let dominates = |a: &ErrorProfile, b: &ErrorProfile| {
                let (x, y) = (a.axes(), b.axes());
                (0..3).all(|i| x[i] <= y[i] + eps[i]) && (0..3).any(|i| x[i] < y[i] - eps[i])
            };
            let adm: Vec<usize> = (0..cells.len()).filter(|&i| cells[i].1.admitted).collect();
            let frontier_of = |i: usize| !adm.iter().any(|&j| dominates(&cells[j].1.profile, &cells[i].1.profile));
            let dominated_by_of = |i: usize| -> Vec<String> {
                adm.iter().filter(|&&j| dominates(&cells[j].1.profile, &cells[i].1.profile))
                    .map(|&j| cells[j].0.clone()).collect()
            };
            let frontier: Vec<String> = adm.iter().filter(|&&i| frontier_of(i)).map(|&i| cells[i].0.clone()).collect();

            let (d1f, d23f) = (frontier_of(1), frontier_of(2));
            let label = format!("b{}/α{:+.1}", avg, alpha);
            if d1f { d1_hits.push(label.clone()); }
            if d23f { d23_hits.push(label.clone()); }

            let (u, d1, d23) = (&cells[0].1.profile, &cells[1].1.profile, &cells[2].1.profile);
            println!("  α{:+.1}  ε {:.5}/{:.5}/{:.5}  uniform {:.5}/{:.5}/{:.5}  d1 {:.5}/{:.5}/{:.5}  d23 {:.5}/{:.5}/{:.5}",
                     alpha, eps[0], eps[1], eps[2], u.pixel, u.structural, u.temporal,
                     d1.pixel, d1.structural, d1.temporal, d23.pixel, d23.structural, d23.temporal);
            println!("        frontier {:?}   causal_d1 frontier={} {}   causal_d23 frontier={} {}",
                     frontier, d1f, if d1f { String::new() } else { format!("(dominated_by {:?})", dominated_by_of(1)) },
                     d23f, if d23f { String::new() } else { format!("(dominated_by {:?})", dominated_by_of(2)) });
            apparatus_ok &= !frontier.is_empty() && eps[0] > 0.0;
        }
        println!();
    }

    println!("======== SWEEP SUMMARY (the answer to M6b's open question) ========");
    println!("causal_d1  (∝difficulty^1)   reached the ε-frontier in: {}", if d1_hits.is_empty() { "NEVER (no cell)".into() } else { format!("{:?}", d1_hits) });
    println!("causal_d23 (∝difficulty^2/3) reached the ε-frontier in: {}", if d23_hits.is_empty() { "NEVER (no cell)".into() } else { format!("{:?}", d23_hits) });
    println!();
    println!("READING: 'on the ε-frontier' = not measurably worse than the best — parity, not proof of gain.");
    println!("If d1 NEVER reaches the frontier but d23 reaches it at LOW budget, the M6b loss is (in part) a");
    println!("WRONG-EXPONENT result: causal allocation over-concentrates (∝difficulty^1 vs variance-optimal");
    println!("∝difficulty^2/3), and a corrected exponent earns parity where there is room to reallocate. If");
    println!("NEITHER ever reaches it, causal importance weighting is simply not competitive with uniform on");
    println!("this scene/metric/device — the stronger, narrower falsification stands. HONEST CEILING: this is");
    println!("one synthetic scene family on one device; benchmark gain ≠ universal, and neither does a loss.");
    println!("\nM6c {} — the sweep ran sealed (priors only), per-cell ε-calibrated, equal-budget, no winner crowned.",
             if apparatus_ok { "COMPLETE" } else { "INCONCLUSIVE (a cell had empty frontier or zero ε)" });
    assert!(apparatus_ok, "M6c apparatus did not hold in some cell");
}
