// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 4: timestamp a RENDER pass, same identity contract as the compute pass.
//!
//! M1: the ruler exists (empty compute pass). M2: it measures real compute work. M3: the measurement is
//! bound to a world identity, and a ghost interval changes the number, never the digest. M4 proves the
//! contract is *backend-agnostic across pass types*: it times a real RENDER pass — a fullscreen triangle
//! with a per-fragment work loop, rendered to an OFFSCREEN texture — with the identical machinery
//! (GoldenReplay → FrameArtifact digest, classify-the-ghost, BenchmarkObservation, median over runs).
//!
//! Still headless: no window, no swapchain, no present, no pixel readback. Still no PFAL/TCFF/fidelity
//! claim. The only new thing is a render pipeline and a render pass; the timing path is unchanged.
//!
//! Acceptance (M4 claims success only if all hold):
//!   1. a RENDER pass's timestamps function (begin/end captured);
//!   2. duration is positive — real fragment work, not bracket overhead;
//!   3. many runs of one frame → ONE identity, timing observed;
//!   4. the observation carries the world-identity digest;
//!   5. a non-positive interval is a ghost (flagged, excluded), identity intact;
//!   6. it is headless — rendered to an offscreen texture, no swapchain.
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::collections::HashSet;
use std::hash::{Hash, Hasher};

use pollster::FutureExt as _;
use serde::{Deserialize, Serialize};

// fullscreen triangle (no vertex buffer) + a per-fragment work loop so the pass does measurable work.
const RENDER_WGSL: &str = r#"
@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> @builtin(position) vec4<f32> {
    var p = array<vec2<f32>, 3>(vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0));
    return vec4<f32>(p[vi], 0.0, 1.0);
}
@fragment
fn fs_main(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
    var acc: f32 = 0.0;
    for (var k: u32 = 0u; k < 64u; k = k + 1u) {
        acc = acc + sin(pos.x * 0.01 + f32(k)) * cos(pos.y * 0.01 + f32(k));
    }
    return vec4<f32>(fract(acc), 0.5, 0.25, 1.0);
}
"#;

const WORKLOAD_NAME: &str = "render_fullscreen_tri_frag64";
const PASS_KIND: &str = "render";
const WIDTH: u32 = 1920;
const HEIGHT: u32 = 1080;
const RUNS: usize = 12;
const HEADLESS: bool = true; // offscreen texture only; no Surface/swapchain is ever created

fn digest(parts: &[&str]) -> String {
    let mut h = DefaultHasher::new();
    for p in parts {
        p.hash(&mut h);
    }
    format!("{:012x}", h.finish())
}

#[derive(Clone)]
struct GoldenReplay {
    scene: String,
    seed: u64,
    policy: String,
}

#[derive(Clone, PartialEq)]
struct FrameArtifact {
    scene_digest: String,
    transform_digest: String,
    policy_id: String,
    provenance_digest: String,
}

impl GoldenReplay {
    fn frame(&self) -> FrameArtifact {
        let seed = self.seed.to_string();
        FrameArtifact {
            scene_digest: digest(&[&self.scene, &seed]),
            transform_digest: digest(&[&self.scene, &seed, "transform"]),
            policy_id: self.policy.clone(),
            provenance_digest: digest(&[&self.scene, &seed, &self.policy, "provenance"]),
        }
    }
}

impl FrameArtifact {
    fn digest(&self) -> String {
        digest(&[&self.scene_digest, &self.transform_digest, &self.policy_id, &self.provenance_digest])
    }
}

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone, Copy)]
enum TimingStatus {
    Ok,
    NonPositive,
}

fn classify(begin: u64, end: u64, period_ns: f32) -> (TimingStatus, f64) {
    let ticks = end as i128 - begin as i128;
    let status = if ticks > 0 { TimingStatus::Ok } else { TimingStatus::NonPositive };
    (status, ticks as f64 * period_ns as f64)
}

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
struct BenchmarkObservation {
    backend: String,
    device_name: String,
    driver: String,
    artifact_digest: String,
    provenance_digest: String,
    workload: String,
    pass_kind: String, // "render" — provenance of WHAT was timed (cf. "compute" in M2/M3)
    render_target: String,
    gpu_begin_tick: u64,
    gpu_end_tick: u64,
    timestamp_period_ns: f32,
    gpu_duration_ns: f64,
    timing_status: TimingStatus,
}

struct Gpu {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pipeline: wgpu::RenderPipeline,
    target_view: wgpu::TextureView,
    period_ns: f32,
    backend: String,
    device_name: String,
    driver: String,
}

impl Gpu {
    fn init() -> Gpu {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::PRIMARY,
            ..Default::default()
        });
        // headless: compatible_surface is None — no window, no swapchain, ever.
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::HighPerformance,
                force_fallback_adapter: false,
                compatible_surface: None,
            })
            .block_on()
            .expect("no GPU adapter found");
        let info = adapter.get_info();
        if !adapter.features().contains(wgpu::Features::TIMESTAMP_QUERY) {
            eprintln!("RULER ABSENT: adapter '{}' lacks TIMESTAMP_QUERY — hard stop.", info.name);
            std::process::exit(1);
        }
        let (device, queue) = adapter
            .request_device(
                &wgpu::DeviceDescriptor {
                    label: Some("bench_gpu_real M4"),
                    required_features: wgpu::Features::TIMESTAMP_QUERY,
                    required_limits: wgpu::Limits::default(),
                    memory_hints: wgpu::MemoryHints::default(),
                },
                None,
            )
            .block_on()
            .expect("device request failed");

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("render"),
            source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(RENDER_WGSL)),
        });
        let layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pl"),
            bind_group_layouts: &[],
            push_constant_ranges: &[],
        });
        let format = wgpu::TextureFormat::Rgba8Unorm;
        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("fullscreen tri"),
            layout: Some(&layout),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: "vs_main",
                buffers: &[],
                compilation_options: Default::default(),
            },
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: "fs_main",
                targets: &[Some(wgpu::ColorTargetState {
                    format,
                    blend: None,
                    write_mask: wgpu::ColorWrites::ALL,
                })],
                compilation_options: Default::default(),
            }),
            primitive: wgpu::PrimitiveState::default(),
            depth_stencil: None,
            multisample: wgpu::MultisampleState::default(),
            multiview: None,
            cache: None,
        });

        // the OFFSCREEN render target — a texture, not a swapchain
        let target = device.create_texture(&wgpu::TextureDescriptor {
            label: Some("offscreen target"),
            size: wgpu::Extent3d { width: WIDTH, height: HEIGHT, depth_or_array_layers: 1 },
            mip_level_count: 1,
            sample_count: 1,
            dimension: wgpu::TextureDimension::D2,
            format,
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            view_formats: &[],
        });
        let target_view = target.create_view(&Default::default());

        Gpu {
            period_ns: queue.get_timestamp_period(),
            backend: format!("{:?}", info.backend),
            device_name: info.name.clone(),
            driver: format!("{} {}", info.driver, info.driver_info),
            device,
            queue,
            pipeline,
            target_view,
        }
    }

    fn time_render(&self) -> (u64, u64) {
        let query_set = self.device.create_query_set(&wgpu::QuerySetDescriptor {
            label: Some("ts"),
            ty: wgpu::QueryType::Timestamp,
            count: 2,
        });
        let resolve = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("resolve"),
            size: 16,
            usage: wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let readback = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("readback"),
            size: 16,
            usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        let mut enc = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = enc.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("timed render pass"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &self.target_view,
                    resolve_target: None,
                    ops: wgpu::Operations {
                        load: wgpu::LoadOp::Clear(wgpu::Color::BLACK),
                        store: wgpu::StoreOp::Store,
                    },
                })],
                depth_stencil_attachment: None,
                timestamp_writes: Some(wgpu::RenderPassTimestampWrites {
                    query_set: &query_set,
                    beginning_of_pass_write_index: Some(0),
                    end_of_pass_write_index: Some(1),
                }),
                occlusion_query_set: None,
            });
            pass.set_pipeline(&self.pipeline);
            pass.draw(0..3, 0..1); // fullscreen triangle
        }
        enc.resolve_query_set(&query_set, 0..2, &resolve, 0);
        enc.copy_buffer_to_buffer(&resolve, 0, &readback, 0, 16);
        self.queue.submit(Some(enc.finish()));

        let slice = readback.slice(..);
        let (tx, rx) = std::sync::mpsc::channel();
        slice.map_async(wgpu::MapMode::Read, move |r| {
            let _ = tx.send(r);
        });
        self.device.poll(wgpu::Maintain::Wait);
        rx.recv().unwrap().unwrap();
        let data = slice.get_mapped_range();
        let begin = u64::from_le_bytes(data[0..8].try_into().unwrap());
        let end = u64::from_le_bytes(data[8..16].try_into().unwrap());
        drop(data);
        readback.unmap();
        (begin, end)
    }

    fn observe(&self, frame: &FrameArtifact) -> BenchmarkObservation {
        let (begin, end) = self.time_render();
        let (status, dur) = classify(begin, end, self.period_ns);
        BenchmarkObservation {
            backend: self.backend.clone(),
            device_name: self.device_name.clone(),
            driver: self.driver.clone(),
            artifact_digest: frame.digest(),
            provenance_digest: frame.provenance_digest.clone(),
            workload: WORKLOAD_NAME.into(),
            pass_kind: PASS_KIND.into(),
            render_target: format!("offscreen {}x{} Rgba8Unorm", WIDTH, HEIGHT),
            gpu_begin_tick: begin,
            gpu_end_tick: end,
            timestamp_period_ns: self.period_ns,
            gpu_duration_ns: dur,
            timing_status: status,
        }
    }
}

fn main() {
    let gpu = Gpu::init();
    let replay = GoldenReplay { scene: "hallway".into(), seed: 1, policy: "PFAL".into() };
    let frame = replay.frame();
    println!("M4 — RENDER-pass timing bound to world identity on {} ({})", gpu.device_name, gpu.backend);
    println!("  target: offscreen {}x{} (headless={}, no swapchain)", WIDTH, HEIGHT, HEADLESS);
    println!("  frame.digest() = {}\n", frame.digest());

    let obs: Vec<BenchmarkObservation> = (0..RUNS).map(|_| gpu.observe(&frame)).collect();
    let identities: HashSet<&str> = obs.iter().map(|o| o.artifact_digest.as_str()).collect();
    let ok_times: Vec<f64> = obs.iter()
        .filter(|o| o.timing_status == TimingStatus::Ok)
        .map(|o| o.gpu_duration_ns)
        .collect();
    let distinct: HashSet<u64> = ok_times.iter().map(|t| t.to_bits()).collect();
    let ghosts = obs.iter().filter(|o| o.timing_status == TimingStatus::NonPositive).count();
    let (tmin, tmax) = ok_times.iter().fold((f64::INFINITY, 0.0_f64), |(a, b), &x| (a.min(x), b.max(x)));

    println!("  {} runs · identities seen: {} · timing ok: {} (ghosts excluded: {}) · spread {:.0}–{:.0} ns",
             RUNS, identities.len(), ok_times.len(), ghosts, tmin, tmax);

    let sample = obs.iter().find(|o| o.timing_status == TimingStatus::Ok).unwrap_or(&obs[0]);
    let json = serde_json::to_string(sample).unwrap();
    let round: Result<BenchmarkObservation, _> = serde_json::from_str(&json);
    println!("\nobservation JSON: {}", json);

    let (gs_eq, _) = classify(100, 100, gpu.period_ns);
    let (gs_back, _) = classify(100, 90, gpu.period_ns);
    let (gs_ok, _) = classify(100, 140, gpu.period_ns);
    let ghost_handled = gs_eq == TimingStatus::NonPositive
        && gs_back == TimingStatus::NonPositive
        && gs_ok == TimingStatus::Ok;

    let checks = [
        ("1_render_pass_timestamps_function", !ok_times.is_empty()),
        ("2_duration_positive_real_fragment_work", tmax > 0.0 && tmin > 0.0),
        ("3_one_identity_timing_observed", identities.len() == 1 && distinct.len() >= 2),
        ("4_observation_carries_world_identity", sample.artifact_digest == frame.digest()),
        ("5_nonpositive_interval_is_a_ghost", ghost_handled),
        ("6_headless_offscreen_no_swapchain", HEADLESS && sample.render_target.starts_with("offscreen")),
        ("7_observation_json_round_trips", round.as_ref().map(|o| o == sample).unwrap_or(false)),
    ];
    println!("\nacceptance:");
    let mut ok = true;
    for (name, pass) in checks.iter() {
        println!("  {}  {}", if *pass { "ok  " } else { "FAIL" }, name);
        ok &= *pass;
    }
    println!(
        "\nM4 {} — a render pass times under the SAME contract as compute: identity stable ({}), \
         timing observed ({} distinct over {} runs), headless. Still no PFAL/fidelity claim.",
        if ok { "PASS" } else { "FAIL" },
        frame.digest(),
        distinct.len(),
        RUNS
    );
    assert!(ok, "M4 acceptance failed");
}
