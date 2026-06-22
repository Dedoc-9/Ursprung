// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 6d / T1: the TEMPORAL apparatus, on the RealityKernel (apparatus, no verdict).
//!
//! M6a–M6c lived in a single frame: render once, score against one reference. They answered "allocate by
//! *present* render difficulty?" — and could not answer the ORIGINAL Causal Continuity claim, which is about
//! *future* consequence (drop present-perception S; spend now to reduce error LATER). Testing that needs a
//! world that EVOLVES across frames, where the cost of an allocation now is paid (or not) in a future frame.
//!
//! T1 builds only the apparatus and proves it is trustworthy — exactly as M6a did before any policy compare:
//!
//!   1. the world EVOLVES                  (state changes frame to frame)
//!   2. TEMPORAL replay identity           (re-run the evolution → byte-identical commit-digest chain)
//!   3. commit-path SEVERANCE              (a transition on an uncommitted prerequisite is REFUSED)
//!   4. future reference is REPRODUCIBLE   (render frame t+k twice → identical pixels)
//!   5. temporal error is MEASURABLE       (low-sample t+k vs its hi-fi reference > 0, and responds to samples)
//!   6. present ≠ future DECOUPLING EXISTS (≥1 tile easy NOW, hard LATER — the question T3 will pose)
//!   7. identity ⟂ render budget + provenance RESOLVES (rendering is observation, not state; compress ≠ sever)
//!
//! THE WORLD RUNS THROUGH THE KERNEL. Each frame's state transition is an `Event` committed by
//! `reality_core::Core::apply`, chained by `requires` (frame t+1 requires frame t's digest). So this is also
//! the first **world-loop client**: the kernel stops being a verified substrate and starts carrying a world,
//! its replay identity and lineage now operating across *time*, not within a frame.
//!
//! THE DECOUPLING IS EMERGENT, NOT DECLARED (the load-bearing rule, lifted from M6's sealed observer). The
//! scene is an occlusion edge sweeping across the tile grid: a tile ahead of the edge is flat (cheap to render
//! NOW) and becomes high-frequency the frame the edge reaches it (expensive LATER). "Future consequence" is a
//! *consequence of the world's dynamics*, never a per-tile importance map authored by the benchmark. T3 may
//! later ask whether a policy can exploit it; T1 only proves the rig can pose the question honestly.
//!
//! NO POLICY IS COMPARED HERE. `benchmark gain ≠ universal`; this is the instrument, not a verdict.
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
const N_FRAMES: usize = 8;     // the occlusion edge sweeps columns 0..8
const T0: usize = 2;           // the "present" frame
const HORIZON: usize = 3;      // look-ahead k; future frame = T0 + HORIZON
const HARD: f32 = 0.95;        // revealed tile: high-frequency content (expensive)
const EASY: f32 = 0.12;        // still-occluded tile: nearly flat (cheap)

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

/// The world at a given frame: an occlusion edge at column `frame`. Columns 0..=frame are REVEALED (hard);
/// columns ahead are still occluded (easy). A column x therefore becomes hard exactly at frame x — so at any
/// present frame t, every column x in (t, ..] is cheap NOW and will be expensive LATER. Emergent, not declared.
fn world_amp(frame: usize) -> Vec<f32> {
    (0..TILES)
        .map(|ti| {
            let x = (ti as u32 % TILES_X) as usize;
            if x <= frame { HARD } else { EASY }
        })
        .collect()
}

/// A compact, replayable description of the world state (what the kernel commits as the transition's value).
fn world_state_str(frame: usize) -> String {
    format!("edge_col={}", frame)
}

/// Evolve the world through the KERNEL: each frame is an Event committed via Core::apply, chained by `requires`
/// (frame t requires frame t-1's digest). Returns the commit-digest chain (the temporal Weltlinie) + refusals.
fn evolve_through_kernel(frames: usize) -> (Vec<String>, usize) {
    let mut core = Core::new();
    let mut chain: Vec<String> = Vec::new();
    let mut prev_digest: Option<String> = None;
    let mut prev_state = "edge_col=-1".to_string();
    for t in 0..frames {
        let new_state = world_state_str(t);
        let ev = Event::new("scene", &prev_state, &new_state, &format!("occlusion_sweep@f{}", t))
            .expect("event must name a source");
        let receipt = core
            .apply(&ev, prev_digest.as_deref())
            .expect("a well-formed, prerequisite-satisfied transition must commit");
        chain.push(receipt.provenance_digest.clone());
        prev_digest = Some(receipt.provenance_digest);
        prev_state = new_state;
    }
    (chain, core.refused)
}

struct Gpu { device: wgpu::Device, queue: wgpu::Queue, pipeline: wgpu::RenderPipeline, bgl: wgpu::BindGroupLayout,
             tex: wgpu::Texture, view: wgpu::TextureView, device_name: String, backend: String }

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor { backends: wgpu::Backends::PRIMARY, ..Default::default() });
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions { power_preference: wgpu::PowerPreference::HighPerformance, force_fallback_adapter: false, compatible_surface: None }).block_on().expect("no adapter");
        let info = adapter.get_info();
        let (device, queue) = adapter.request_device(&wgpu::DeviceDescriptor { label: Some("T1"), required_features: wgpu::Features::empty(), required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default() }, None).block_on().expect("device");
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

    /// Render a world frame (amp from `world_amp`) with a per-tile sample budget. Pixels only — T1 does not time.
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
    println!("M6d / T1 — TEMPORAL apparatus on the RealityKernel (apparatus, no verdict) on {} ({})",
             gpu.device_name, gpu.backend);
    println!("world: occlusion edge sweeping {} tile-columns over {} frames; present frame T0={}, horizon k={} (future frame {})\n",
             TILES_X, N_FRAMES, T0, HORIZON, T0 + HORIZON);

    let tf = T0 + HORIZON;
    let mut pass = 0u32;
    let mut total = 0u32;
    let mut check = |name: &str, ok: bool, detail: String| {
        total += 1; if ok { pass += 1; }
        println!("  [{}] {:<34} {}", if ok { "PASS" } else { "FAIL" }, name, detail);
    };

    // 1. the world evolves
    let states: Vec<String> = (0..N_FRAMES).map(world_state_str).collect();
    let distinct = { let mut s = states.clone(); s.sort(); s.dedup(); s.len() };
    check("world_evolves", distinct == N_FRAMES,
          format!("{} distinct states over {} frames", distinct, N_FRAMES));

    // 2. temporal replay identity — the world runs through the kernel, twice, byte-identical commit chain
    let (chain_a, refused_a) = evolve_through_kernel(N_FRAMES);
    let (chain_b, _) = evolve_through_kernel(N_FRAMES);
    let replay_ok = chain_a == chain_b && chain_a.len() == N_FRAMES;
    check("temporal_replay_identity", replay_ok,
          format!("commit-digest chain identical across 2 runs ({} commits; head {})",
                  chain_a.len(), chain_a.first().cloned().unwrap_or_default()));

    // 3. commit-path severance — a transition requiring an uncommitted prerequisite is REFUSED
    let severance_ok = {
        let mut core = Core::new();
        let ev = Event::new("scene", "edge_col=-1", "edge_col=0", "orphan_frame").unwrap();
        let refused_before = core.refused;
        let res = core.apply(&ev, Some("deadbeefdeadbeef")); // a prerequisite digest that was never committed
        res.is_err() && core.refused == refused_before + 1
    };
    check("commit_path_severance", severance_ok && refused_a == 0,
          format!("orphan transition refused; legitimate chain refused {} (dropped transition forbidden)", refused_a));

    // 4. future reference is reproducible — render frame tf at full fidelity twice → identical pixels
    let amp_tf = world_amp(tf);
    let full = vec![REF_SAMPLES; TILES];
    let ref_a = gpu.render(&amp_tf, &full, 0);
    let ref_b = gpu.render(&amp_tf, &full, 0);
    check("future_reference_reproducible", ref_a == ref_b,
          format!("frame {} hi-fi render identical across 2 calls ({} bytes)", tf, ref_a.len()));

    // 5. temporal error is measurable and responds to samples (low-sample future render vs its hi-fi reference)
    let err_lo = pixel_err(&gpu.render(&amp_tf, &vec![4u32; TILES], 11), &ref_a);
    let err_hi = pixel_err(&gpu.render(&amp_tf, &vec![64u32; TILES], 11), &ref_a);
    check("temporal_error_measurable", err_lo > 0.0 && err_hi > 0.0 && err_lo > err_hi,
          format!("future-frame err @4spp {:.5} > @64spp {:.5} > 0", err_lo, err_hi));

    // 6. present ≠ future decoupling EXISTS — tiles cheap NOW (T0) that become expensive LATER (tf)
    let amp_now = world_amp(T0);
    let decoupled: usize = (0..TILES).filter(|&ti| amp_now[ti] < amp_tf[ti]).count();
    check("present_future_decoupling_exists", decoupled > 0,
          format!("{} tiles easy@T0 but hard@{} (emergent, not authored)", decoupled, tf));

    // 7. identity ⟂ render budget, and provenance resolves (compress ≠ sever)
    let chain_before = evolve_through_kernel(N_FRAMES).0;
    let _ = gpu.render(&amp_tf, &vec![4u32; TILES], 1);   // render at one budget
    let _ = gpu.render(&amp_tf, &vec![128u32; TILES], 1); // render at another
    let chain_after = evolve_through_kernel(N_FRAMES).0;
    let provenance_ok = {
        // re-walk the kernel and confirm a committed frame's digest still resolves to lineage
        let mut core = Core::new();
        let mut prev_d: Option<String> = None;
        let mut prev_s = "edge_col=-1".to_string();
        let mut t0_digest = String::new();
        for t in 0..=T0 {
            let ns = world_state_str(t);
            let ev = Event::new("scene", &prev_s, &ns, &format!("occlusion_sweep@f{}", t)).unwrap();
            let rec = core.apply(&ev, prev_d.as_deref()).unwrap();
            if t == T0 { t0_digest = rec.provenance_digest.clone(); }
            prev_d = Some(rec.provenance_digest); prev_s = ns;
        }
        matches!(core.resolve_digest(&t0_digest), reality_core::Resolution::Resolved(_))
    };
    check("identity_independent_of_render", chain_before == chain_after && provenance_ok,
          format!("commit chain unchanged by rendering at 2 budgets; T0 lineage resolves = {}", provenance_ok));

    println!("\nT1 {} — {}/{} checks. The TEMPORAL apparatus is {}: the world evolves through the kernel,",
             if pass == total { "COMPLETE" } else { "INCOMPLETE" }, pass, total,
             if pass == total { "trustworthy" } else { "NOT yet trustworthy" });
    println!("replays identically, refuses severed transitions, renders reproducible futures, measures future");
    println!("error, and CAN pose the present≠future question — with the decoupling emerging from world dynamics,");
    println!("not authored. No policy compared (that is T2's ruler, then T3's gate). benchmark gain ≠ universal.");
    assert!(pass == total, "T1 apparatus did not fully hold");
}
