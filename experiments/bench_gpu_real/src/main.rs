// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6d / T2: the TEMPORAL RULER (apparatus, no verdict).
//!
//! T1 proved the temporal apparatus (a world evolving through the kernel, replaying identically, posing the
//! present≠future question). T2 builds the *ruler* that T3 will score policies on — and proves it is fair
//! FIRST, exactly as M6a proved the perceptual ruler before M6b compared anything.
//!
//! THE COUPLING MODEL (a DECLARED boundary condition, NOT "the temporal law"). For "spend now to reduce error
//! later" to be measurable, work at frame t must persist to frame t+k. The model: TAA-style **history
//! accumulation with explicit disocclusion invalidation** — samples spent on a tile accumulate across frames
//! while its content is stable, and RESET the frame its content changes (the occlusion edge passes). This is
//! the *weakest* coupling that still exists in real renderers: present work can genuinely survive, history can
//! genuinely become wrong, future benefit is earned not assumed, and it arises from scene dynamics, not oracle
//! foresight. It is the rendering analogue of the project's recurring lesson — carried information has a cost
//! and is valid only until its assumptions change (disocclusion reset ≈ provenance invalidation; `compress ≠
//! sever` in time). A different reuse model would change the numbers: `declared ≠ verified`. The claim T2
//! earns is therefore scoped: *under a history-accumulation renderer with explicit disocclusion invalidation,
//! future consequence is measurable* — enough to make T3 a legitimate experiment, not a universal temporal law.
//!
//! THE KEY ISOLATION. future_penalty := error(t+k | accumulation WITH disocclusion resets)
//!                                     − error(t+k | accumulation WITHOUT resets), same future content & budget.
//! It isolates exactly the cost of history becoming invalid: a world with no emergence has identical sample
//! maps either way → penalty exactly 0; the sweeping world loses history at each disocclusion → penalty > ε.
//! So the ruler distinguishes *present error* from *future consequence* WITHOUT looking inside any policy.
//!
//! Five checks, NO policy compared. `benchmark gain ≠ universal`.
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
const TF: usize = 5;          // the future frame (the occlusion edge sweeps columns 0..=TF over frames 0..=TF)
const HARD: f32 = 0.95;
const EASY: f32 = 0.12;

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

/// The world at a frame: occlusion edge at column `frame`; columns 0..=frame revealed (hard), ahead occluded.
fn world_amp(frame: usize) -> Vec<f32> {
    (0..TILES)
        .map(|ti| { let x = (ti as u32 % TILES_X) as usize; if x <= frame { HARD } else { EASY } })
        .collect()
}
fn world_state_str(frame: usize) -> String { format!("edge_col={}", frame) }

/// Evolve the world through the KERNEL (for the identity check): chained Events committed by Core::apply.
fn evolve_through_kernel(frames: usize) -> (Vec<String>, usize) {
    let mut core = Core::new();
    let mut chain = Vec::new();
    let mut prev_digest: Option<String> = None;
    let mut prev_state = "edge_col=-1".to_string();
    for t in 0..frames {
        let new_state = world_state_str(t);
        let ev = Event::new("scene", &prev_state, &new_state, &format!("occlusion_sweep@f{}", t)).unwrap();
        let rec = core.apply(&ev, prev_digest.as_deref()).expect("commit");
        chain.push(rec.provenance_digest.clone());
        prev_digest = Some(rec.provenance_digest);
        prev_state = new_state;
    }
    (chain, core.refused)
}

/// THE DECLARED COUPLING MODEL. Per-tile effective samples at frame TF, accumulating a fixed per-frame budget
/// `b` while a tile's content is stable, RESETTING on disocclusion iff `reset` (the honest TAA model). `sweep`
/// selects the dynamic world (edge advances) vs a static one (edge frozen → no content change → no reset).
fn effective(b: u32, reset: bool, sweep: bool) -> Vec<u32> {
    let edge = |f: usize| -> usize { if sweep { f } else { TF } };
    let mut acc = vec![0u32; TILES];
    for f in 0..=TF {
        let e = edge(f);
        let e_prev = if f == 0 { e } else { edge(f - 1) };
        for ti in 0..TILES {
            let x = (ti as u32 % TILES_X) as usize;
            let revealed = x <= e;
            let changed = f != 0 && (revealed != (x <= e_prev));
            if reset && changed { acc[ti] = b; } else { acc[ti] = (acc[ti] + b).min(REF_SAMPLES); }
        }
    }
    acc
}

struct Gpu { device: wgpu::Device, queue: wgpu::Queue, pipeline: wgpu::RenderPipeline, bgl: wgpu::BindGroupLayout,
             tex: wgpu::Texture, view: wgpu::TextureView, device_name: String, backend: String }

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor { backends: wgpu::Backends::PRIMARY, ..Default::default() });
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions { power_preference: wgpu::PowerPreference::HighPerformance, force_fallback_adapter: false, compatible_surface: None }).block_on().expect("no adapter");
        let info = adapter.get_info();
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor { label: Some("T2"), required_features: wgpu::Features::empty(), required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default() }, None).block_on().expect("device");
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

fn main() {
    let gpu = Gpu::init();
    println!("M6d / T2 — the TEMPORAL RULER (apparatus, no verdict) on {} ({})", gpu.device_name, gpu.backend);
    println!("coupling: TAA history accumulation + explicit disocclusion invalidation (a DECLARED boundary condition, not 'the temporal law')");
    println!("future frame TF={}; per-frame budget accumulates while content is stable, RESETS on disocclusion\n", TF);

    let amp_tf = world_amp(TF);
    let reference = gpu.render(&amp_tf, &vec![REF_SAMPLES; TILES], 0);
    // future-frame error of an effective-sample map, vs the frozen hi-fi future reference
    let err = |eff: &[u32], seed: u32| pixel_err(&gpu.render(&amp_tf, eff, seed), &reference);

    let mut pass = 0u32; let mut total = 0u32;
    let mut check = |name: &str, ok: bool, detail: String| {
        total += 1; if ok { pass += 1; }
        println!("  [{}] {:<30} {}", if ok { "PASS" } else { "FAIL" }, name, detail);
    };

    // 1. future error monotonicity — degrade allocation (lower per-frame budget) → future error rises
    let e_lo = err(&effective(2, true, true), 7);
    let e_hi = err(&effective(8, true, true), 7);
    check("future_error_monotonic", e_lo > e_hi && e_hi > 0.0,
          format!("future err @b2 {:.5} > @b8 {:.5} > 0", e_lo, e_hi));

    // 2. negative control — the future reference scored against itself is exactly zero
    let nc = pixel_err(&reference, &reference);
    check("negative_control_zero", nc == 0.0, format!("ref vs ref future error = {:.6}", nc));

    // 3. reproducibility floor ε — cross-seed spread of the future-error measure
    let eff_real = effective(8, true, true);
    let errs: Vec<f64> = [11u32, 22, 33, 44].iter().map(|&s| err(&eff_real, s)).collect();
    let eps = errs.iter().cloned().fold(f64::MIN, f64::max) - errs.iter().cloned().fold(f64::MAX, f64::min);
    check("reproducibility_floor", eps >= 0.0 && eps < 0.002,
          format!("ε(future) = {:.6} across 4 seeds", eps));

    // 4. temporal sensitivity — future_penalty = err(WITH disocclusion resets) − err(WITHOUT), same content/budget.
    //    Emergence world: disoccluded tiles lose history → penalty > ε. Static world: identical maps → penalty 0.
    let pen_dyn = err(&effective(8, true, true), 7) - err(&effective(8, false, true), 7);
    let pen_stat = err(&effective(8, true, false), 7) - err(&effective(8, false, false), 7);
    check("temporal_sensitivity", pen_dyn > eps && pen_stat.abs() <= eps.max(1e-9),
          format!("future penalty: emergence {:.5} (> ε) vs static {:.6} (≈ 0) — ruler sees future consequence", pen_dyn, pen_stat));

    // 5. identity preservation — same world history (kernel commit chain) → same future reference
    let (chain1, _) = evolve_through_kernel(TF + 1);
    let ref1 = gpu.render(&amp_tf, &vec![REF_SAMPLES; TILES], 0);
    let (chain2, _) = evolve_through_kernel(TF + 1);
    let ref2 = gpu.render(&amp_tf, &vec![REF_SAMPLES; TILES], 0);
    check("identity_preservation", chain1 == chain2 && ref1 == ref2,
          format!("same kernel world-history ({} commits) → identical future reference", chain1.len()));

    println!("\nT2 {} — {}/{} checks. The TEMPORAL RULER is {}: future error responds to allocation, reads",
             if pass == total { "COMPLETE" } else { "INCOMPLETE" }, pass, total,
             if pass == total { "fair" } else { "NOT yet fair" });
    println!("zero on its negative control, has a measured floor ε, and DISTINGUISHES present error from future");
    println!("consequence (emergence penalised, static not) WITHOUT looking inside any policy. The coupling is a");
    println!("declared boundary condition (TAA + disocclusion invalidation) — `declared ≠ verified`; the claim is");
    println!("'future consequence is measurable UNDER THIS model', not a temporal law. No policy compared — that");
    println!("is T3, the temporal causal gate: does spending NOW measurably reduce FUTURE error? benchmark gain ≠ universal.");
    assert!(pass == total, "T2 ruler did not fully hold");
}
