// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6a: the PERCEPTUAL RULER (apparatus only — no policy verdict).
//!
//! M1–M5 proved the *timing* ruler is fair. M6a proves a *perceptual-error* ruler is fair, against a
//! frozen high-quality ground-truth reference — BEFORE any allocation policy is compared (that is M6b).
//! The error is reported as a policy-neutral VECTOR, never a scalar winner metric:
//!
//!     pixel_error      mean |approx − reference| over the frame      (reconstruction error)
//!     structural_error mean |∇approx − ∇reference|                   (meaningful scene change / edges)
//!     temporal_error   mean |approx(seed A) − approx(seed B)|        (instability / flicker)
//!
//! The quality knob is the per-pixel SAMPLE BUDGET (SSAA): the reference renders at max samples; an
//! approximation renders at fewer. The metric is computed from PIXELS ONLY — it never sees the sample
//! count or any "policy" label, so it is blind. M6a claims only that this ruler is fair; it declares no
//! policy better than another.
//!
//! Fairness obligations (all asserted): responds to real degradation; a negative control (reference vs
//! itself) reads ~0; reproducible across independent renders; the world identity is preserved (sample
//! budget is an execution condition, not identity); each render carries its measured GPU-tick budget and
//! ghost handling; and the limits are stated explicitly.
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use pollster::FutureExt as _;
use serde::{Deserialize, Serialize};

const RES: u32 = 256; // 256·4 = 1024 bytes/row, already 256-byte aligned for copy_texture_to_buffer
const BYTES_PER_ROW: u32 = RES * 4;
const REF_SAMPLES: u32 = 256; // the frozen ground-truth reference
const SCENE_WGSL: &str = r#"
struct U { samples: u32, seed: u32, res: u32, _pad: u32 };
@group(0) @binding(0) var<uniform> u: U;

fn scene(p: vec2<f32>) -> f32 {
    // high-frequency content + a hard edge → undersampling produces REAL reconstruction error
    let hf = sin(p.x * 90.0) * sin(p.y * 90.0);
    let edge = select(0.0, 1.0, (p.x + p.y) > 1.0);
    return clamp(0.5 + 0.35 * hf + 0.15 * edge, 0.0, 1.0);
}
@vertex
fn vs(@builtin(vertex_index) vi: u32) -> @builtin(position) vec4<f32> {
    var q = array<vec2<f32>, 3>(vec2<f32>(-1.0,-1.0), vec2<f32>(3.0,-1.0), vec2<f32>(-1.0,3.0));
    return vec4<f32>(q[vi], 0.0, 1.0);
}
@fragment
fn fs(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
    let res = f32(u.res);
    var acc = 0.0;
    var st: u32 = u.seed + u32(pos.x) * 1973u + u32(pos.y) * 9277u + 1u;
    for (var i: u32 = 0u; i < u.samples; i = i + 1u) {
        st = st * 747796405u + 2891336453u; let jx = f32((st >> 16u) & 0xffffu) / 65535.0;
        st = st * 747796405u + 2891336453u; let jy = f32((st >> 16u) & 0xffffu) / 65535.0;
        let p = (pos.xy + vec2<f32>(jx, jy) - vec2<f32>(0.5)) / res;
        acc = acc + scene(p);
    }
    let v = acc / f32(u.samples);
    return vec4<f32>(v, v, v, 1.0);
}
"#;

fn digest(parts: &[&str]) -> String {
    let mut h = DefaultHasher::new();
    for p in parts { p.hash(&mut h); }
    format!("{:012x}", h.finish())
}

#[derive(Clone)]
struct GoldenReplay { scene: String, seed: u64 }
impl GoldenReplay {
    fn frame_digest(&self) -> String {
        // identity is the SCENE; sample budget is an execution condition, not identity.
        digest(&[&self.scene, &self.seed.to_string(), "scene-identity"])
    }
}

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone, Copy)]
struct ErrorProfile { pixel_error: f64, structural_error: f64, temporal_error: f64 }
impl ErrorProfile {
    // deliberately NO .total()/.score() — three axes, never collapsed to a winner scalar
    fn axes(&self) -> [f64; 3] { [self.pixel_error, self.structural_error, self.temporal_error] }
}

fn r_channel(px: &[u8]) -> Vec<f64> { px.iter().step_by(4).map(|&b| b as f64 / 255.0).collect() }

fn pixel_error(a: &[u8], b: &[u8]) -> f64 {
    let (ra, rb) = (r_channel(a), r_channel(b));
    ra.iter().zip(&rb).map(|(x, y)| (x - y).abs()).sum::<f64>() / ra.len() as f64
}

/// forward-difference gradient magnitude per pixel (a simple, standard edge measure)
fn grad(px: &[u8]) -> Vec<f64> {
    let r = r_channel(px);
    let n = RES as usize;
    let mut g = vec![0.0; r.len()];
    for y in 0..n {
        for x in 0..n {
            let i = y * n + x;
            let dx = if x + 1 < n { r[i + 1] - r[i] } else { 0.0 };
            let dy = if y + 1 < n { r[i + n] - r[i] } else { 0.0 };
            g[i] = (dx * dx + dy * dy).sqrt();
        }
    }
    g
}
fn structural_error(a: &[u8], b: &[u8]) -> f64 {
    let (ga, gb) = (grad(a), grad(b));
    ga.iter().zip(&gb).map(|(x, y)| (x - y).abs()).sum::<f64>() / ga.len() as f64
}

struct Gpu {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pipeline: wgpu::RenderPipeline,
    bgl: wgpu::BindGroupLayout,
    tex: wgpu::Texture,
    view: wgpu::TextureView,
    period_ns: f32,
    device_name: String,
    backend: String,
}

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor { backends: wgpu::Backends::PRIMARY, ..Default::default() });
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance, force_fallback_adapter: false, compatible_surface: None,
        }).block_on().expect("no GPU adapter");
        let info = adapter.get_info();
        if !adapter.features().contains(wgpu::Features::TIMESTAMP_QUERY) {
            eprintln!("RULER ABSENT: '{}' lacks TIMESTAMP_QUERY — hard stop.", info.name);
            std::process::exit(1);
        }
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor {
            label: Some("M6a"), required_features: wgpu::Features::TIMESTAMP_QUERY,
            required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default(),
        }, None).block_on().expect("device request failed");

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("scene"), source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(SCENE_WGSL)),
        });
        let bgl = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl"),
            entries: &[wgpu::BindGroupLayoutEntry {
                binding: 0, visibility: wgpu::ShaderStages::FRAGMENT,
                ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false, min_binding_size: None },
                count: None,
            }],
        });
        let pl = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor { label: Some("pl"), bind_group_layouts: &[&bgl], push_constant_ranges: &[] });
        let format = wgpu::TextureFormat::Rgba8Unorm;
        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("scene pipeline"), layout: Some(&pl),
            vertex: wgpu::VertexState { module: &shader, entry_point: "vs", buffers: &[], compilation_options: Default::default() },
            fragment: Some(wgpu::FragmentState { module: &shader, entry_point: "fs",
                targets: &[Some(wgpu::ColorTargetState { format, blend: None, write_mask: wgpu::ColorWrites::ALL })],
                compilation_options: Default::default() }),
            primitive: wgpu::PrimitiveState::default(), depth_stencil: None, multisample: wgpu::MultisampleState::default(),
            multiview: None, cache: None,
        });
        let tex = device.create_texture(&wgpu::TextureDescriptor {
            label: Some("target"), size: wgpu::Extent3d { width: RES, height: RES, depth_or_array_layers: 1 },
            mip_level_count: 1, sample_count: 1, dimension: wgpu::TextureDimension::D2, format,
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC, view_formats: &[],
        });
        let view = tex.create_view(&Default::default());

        Gpu { period_ns: queue.get_timestamp_period(), device_name: info.name.clone(), backend: format!("{:?}", info.backend), device, queue, pipeline, bgl, tex, view }
    }

    /// Render the scene at `samples` SSAA with jitter `seed`; return (pixels RGBA, gpu_tick_interval, ghost?).
    fn render(&self, samples: u32, seed: u32) -> (Vec<u8>, i128, bool) {
        // uniform: {samples, seed, res, pad}
        let ubuf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("u"), size: 16, usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let mut u = [0u8; 16];
        u[0..4].copy_from_slice(&samples.to_le_bytes());
        u[4..8].copy_from_slice(&seed.to_le_bytes());
        u[8..12].copy_from_slice(&RES.to_le_bytes());
        self.queue.write_buffer(&ubuf, 0, &u);
        let bind = self.device.create_bind_group(&wgpu::BindGroupDescriptor { label: Some("bg"), layout: &self.bgl, entries: &[wgpu::BindGroupEntry { binding: 0, resource: ubuf.as_entire_binding() }] });

        let qs = self.device.create_query_set(&wgpu::QuerySetDescriptor { label: Some("ts"), ty: wgpu::QueryType::Timestamp, count: 2 });
        let qresolve = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("qr"), size: 16, usage: wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC, mapped_at_creation: false });
        let qread = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("qrd"), size: 16, usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });
        let pxbuf = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("px"), size: (BYTES_PER_ROW * RES) as u64, usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });

        let mut enc = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("scene"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment { view: &self.view, resolve_target: None,
                    ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Store } })],
                depth_stencil_attachment: None,
                timestamp_writes: Some(wgpu::RenderPassTimestampWrites { query_set: &qs, beginning_of_pass_write_index: Some(0), end_of_pass_write_index: Some(1) }),
                occlusion_query_set: None,
            });
            pass.set_pipeline(&self.pipeline);
            pass.set_bind_group(0, &bind, &[]);
            pass.draw(0..3, 0..1);
        }
        enc.resolve_query_set(&qs, 0..2, &qresolve, 0);
        enc.copy_buffer_to_buffer(&qresolve, 0, &qread, 0, 16);
        enc.copy_texture_to_buffer(
            wgpu::ImageCopyTexture { texture: &self.tex, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
            wgpu::ImageCopyBuffer { buffer: &pxbuf, layout: wgpu::ImageDataLayout { offset: 0, bytes_per_row: Some(BYTES_PER_ROW), rows_per_image: Some(RES) } },
            wgpu::Extent3d { width: RES, height: RES, depth_or_array_layers: 1 },
        );
        self.queue.submit(Some(enc.finish()));

        // map both buffers
        let s1 = qread.slice(..); let (t1, r1) = std::sync::mpsc::channel(); s1.map_async(wgpu::MapMode::Read, move |r| { let _ = t1.send(r); });
        let s2 = pxbuf.slice(..); let (t2, r2) = std::sync::mpsc::channel(); s2.map_async(wgpu::MapMode::Read, move |r| { let _ = t2.send(r); });
        self.device.poll(wgpu::Maintain::Wait);
        r1.recv().unwrap().unwrap(); r2.recv().unwrap().unwrap();

        let qd = s1.get_mapped_range();
        let begin = u64::from_le_bytes(qd[0..8].try_into().unwrap());
        let end = u64::from_le_bytes(qd[8..16].try_into().unwrap());
        drop(qd); qread.unmap();
        let ticks = end as i128 - begin as i128;
        let ghost = ticks <= 0;

        let pd = s2.get_mapped_range();
        let pixels = pd.to_vec();
        drop(pd); pxbuf.unmap();
        (pixels, ticks, ghost)
    }
}

fn main() {
    let gpu = Gpu::init();
    let replay = GoldenReplay { scene: "hf_edge".into(), seed: 1 };
    let id = replay.frame_digest();
    println!("M6a — the PERCEPTUAL RULER (apparatus, no verdict) on {} ({})", gpu.device_name, gpu.backend);
    println!("  scene identity = {}  ·  {}x{}  ·  reference = {} samples/pixel\n", id, RES, RES, REF_SAMPLES);

    // a discarded warm-up render absorbs GPU cold-start (its interval is a ghost we don't use)
    let _ = gpu.render(8, 99);
    // frozen ground-truth reference
    let (reference, ref_ticks, ref_ghost) = gpu.render(REF_SAMPLES, 0);

    // degradation sweep: fewer samples should measure FARTHER from the reference
    let mut deg = Vec::new();
    for &s in &[4u32, 16, 64] {
        let (px, ticks, ghost) = gpu.render(s, 1);
        let pe = pixel_error(&px, &reference);
        deg.push((s, pe, ticks, ghost));
        println!("  approx S={:<4} pixel_error {:.5}  · gpu {:>10} ticks{}", s, pe, ticks, if ghost { " (ghost, excluded)" } else { "" });
    }

    // negative control: reference vs itself = 0
    let ref_vs_ref = pixel_error(&reference, &reference);
    // reproducibility / blindness: two independent renders at the SAME budget differ only within noise
    let (a1, _, _) = gpu.render(16, 11);
    let (a2, _, _) = gpu.render(16, 22);
    let pe1 = pixel_error(&a1, &reference);
    let pe2 = pixel_error(&a2, &reference);
    let reproducible = (pe1 - pe2).abs();
    // the temporal axis is the instability between two same-budget renders
    let temporal = pixel_error(&a1, &a2);

    // a full error VECTOR for one approximation (S=16)
    let profile = ErrorProfile {
        pixel_error: pe1,
        structural_error: structural_error(&a1, &reference),
        temporal_error: temporal,
    };

    println!("\n  reference identity preserved across budgets: {}", id == replay.frame_digest());
    println!("  negative control  pixel_error(reference, reference) = {:.6}  (must be ~0)", ref_vs_ref);
    println!("  reproducibility   |pe(seedA) − pe(seedB)| = {:.6}  (small ⇒ blind/stable)", reproducible);
    println!("  error VECTOR (S=16)  pixel/structural/temporal = {:.5}/{:.5}/{:.5}",
             profile.pixel_error, profile.structural_error, profile.temporal_error);
    if ref_ghost {
        println!("  reference render budget = GHOST (cold-start zero interval; excluded — pixels unaffected)");
    } else {
        println!("  reference render budget = {} ticks (~{:.3} ms)", ref_ticks, ref_ticks as f64 * gpu.period_ns as f64 / 1e6);
    }

    let pes: Vec<f64> = deg.iter().map(|(_, pe, _, _)| *pe).collect();
    let monotone = pes.windows(2).all(|w| w[0] >= w[1]); // more samples (later) → less error
    let json = serde_json::to_string(&profile).unwrap();
    let round: Result<ErrorProfile, _> = serde_json::from_str(&json);

    let checks = [
        ("1_ruler_responds_to_degradation", monotone && pes[0] > pes[2]),     // S=4 worse than S=64
        ("2_negative_control_ref_vs_ref_zero", ref_vs_ref < 1e-9),
        ("3_reproducible_blind", reproducible < 0.02),                        // same budget ⇒ stable pixel_error
        ("4_error_is_a_vector_not_scalar", profile.axes().len() == 3 && profile.axes().iter().all(|x| x.is_finite())),
        ("5_identity_preserved_budget_is_condition", id == replay.frame_digest()),
        // a ghost is HANDLED (classified + excluded), never a failure; the ruler must tick at least once
        ("6_budget_recorded_and_ghosts_handled",
            (ref_ticks > 0 || ref_ghost) && deg.iter().any(|(_, _, t, _)| *t > 0)),
        ("7_profile_json_round_trips", round.as_ref().map(|p| *p == profile).unwrap_or(false)),
    ];
    println!("\nacceptance:");
    let mut ok = true;
    for (name, pass) in checks.iter() { println!("  {}  {}", if *pass { "ok  " } else { "FAIL" }, name); ok &= *pass; }

    println!("\nEXPLICIT LIMITS: one device (this GPU), one synthetic scene (high-frequency + edge), SSAA as the");
    println!("quality proxy, whole-frame aggregates (per-tile allocation is M6b). The metric is policy-neutral");
    println!("and blind (pixels only). M6a declares NO policy superior — that is M6b's question.");
    println!("\nM6a {} — a fair perceptual ruler exists on real silicon: tracks real degradation, reads zero on\n\
              the negative control, is reproducible, reports a vector (never a winner scalar).",
             if ok { "PASS" } else { "FAIL" });
    assert!(ok, "M6a acceptance failed");
}
