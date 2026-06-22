// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 3: bind the GPU measurement to the WORLD IDENTITY it measured.
//!
//! M1: the ruler exists. M2: the ruler measures real work. M3 adds no rendering and no new timing —
//! it adds *traceability*: a `GoldenReplay` derives a `FrameArtifact` whose digest is the stable
//! identity of what is measured, and every `BenchmarkObservation` carries that digest. The dispatch is
//! "derived from this frame, derived from this replay." Identity is stable; timing is observed.
//!
//! This is the GPU analogue of the provenance kernel's digest-resolution contract: the measurement can
//! always be traced back to the thing it measured. Still compute-only — no window, swapchain, pixels.
//!
//! Acceptance (M3 claims success only if all hold):
//!   1. same replay → same digest;
//!   2. same digest → same dispatch description;
//!   3. the observation carries the digest;
//!   4. the observation JSON round-trips (serialize → deserialize → equal);
//!   5. many runs of one digest → varying timing but ONE identity;
//!   6. a non-positive interval is a ghost (flagged, excluded from stats) — never an identity change.
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::collections::HashSet;
use std::hash::{Hash, Hasher};

use pollster::FutureExt as _;
use serde::{Deserialize, Serialize};

const WORKLOAD_WGSL: &str = r#"
@group(0) @binding(0) var<storage, read_write> data: array<u32>;
@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let i = gid.x;
    if (i < arrayLength(&data)) {
        var acc: u32 = i;
        for (var k: u32 = 0u; k < 256u; k = k + 1u) {
            acc = acc * 1664525u + 1013904223u;
        }
        data[i] = acc;
    }
}
"#;

const WORKLOAD_NAME: &str = "compute_lcg_iter256";
const WORKLOAD_SIZE: u64 = 262_144; // execution condition (not identity); fixed for M3 (M2 did scaling)
const RUNS: usize = 12;

fn digest(parts: &[&str]) -> String {
    let mut h = DefaultHasher::new();
    for p in parts {
        p.hash(&mut h);
    }
    format!("{:012x}", h.finish())
}

// --- the world description: a replay derives a frame whose digest is its stable identity ----------
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
    /// The dispatch description derived from this frame — deterministic, so same digest → same dispatch.
    fn dispatch_descriptor(&self) -> String {
        format!("{}|{}|n={}", WORKLOAD_NAME, self.policy_id, WORKLOAD_SIZE)
    }
}

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone, Copy)]
enum TimingStatus {
    Ok,
    NonPositive, // end <= begin: a measurement ghost (clock re-index / power-state), not an identity change
}

fn classify(begin: u64, end: u64, period_ns: f32) -> (TimingStatus, f64) {
    // signed on purpose — a backward interval is recorded honestly, never clamped-and-hidden
    let ticks = end as i128 - begin as i128;
    let status = if ticks > 0 { TimingStatus::Ok } else { TimingStatus::NonPositive };
    (status, ticks as f64 * period_ns as f64)
}

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
struct BenchmarkObservation {
    backend: String,
    device_name: String,
    driver: String,
    artifact_digest: String, // the FrameArtifact identity measured (stable across runs)
    provenance_digest: String,
    workload: String,
    workload_size: u64,
    gpu_begin_tick: u64,
    gpu_end_tick: u64,
    timestamp_period_ns: f32,
    gpu_duration_ns: f64,
    timing_status: TimingStatus,
}

struct Gpu {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pipeline: wgpu::ComputePipeline,
    bgl: wgpu::BindGroupLayout,
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
                    label: Some("bench_gpu_real M3"),
                    required_features: wgpu::Features::TIMESTAMP_QUERY,
                    required_limits: wgpu::Limits::default(),
                    memory_hints: wgpu::MemoryHints::default(),
                },
                None,
            )
            .block_on()
            .expect("device request failed");

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("lcg"),
            source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(WORKLOAD_WGSL)),
        });
        let bgl = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl"),
            entries: &[wgpu::BindGroupLayoutEntry {
                binding: 0,
                visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Storage { read_only: false },
                    has_dynamic_offset: false,
                    min_binding_size: None,
                },
                count: None,
            }],
        });
        let pl = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pl"),
            bind_group_layouts: &[&bgl],
            push_constant_ranges: &[],
        });
        let pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("lcg pipeline"),
            layout: Some(&pl),
            module: &shader,
            entry_point: "main",
            compilation_options: Default::default(),
            cache: None,
        });

        Gpu {
            period_ns: queue.get_timestamp_period(),
            backend: format!("{:?}", info.backend),
            device_name: info.name.clone(),
            driver: format!("{} {}", info.driver, info.driver_info),
            device,
            queue,
            pipeline,
            bgl,
        }
    }

    fn time_dispatch(&self, n: u64) -> (u64, u64) {
        let buffer = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("data"),
            size: n * 4,
            usage: wgpu::BufferUsages::STORAGE,
            mapped_at_creation: false,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("bg"),
            layout: &self.bgl,
            entries: &[wgpu::BindGroupEntry { binding: 0, resource: buffer.as_entire_binding() }],
        });
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
            let mut pass = enc.begin_compute_pass(&wgpu::ComputePassDescriptor {
                label: Some("timed dispatch"),
                timestamp_writes: Some(wgpu::ComputePassTimestampWrites {
                    query_set: &query_set,
                    beginning_of_pass_write_index: Some(0),
                    end_of_pass_write_index: Some(1),
                }),
            });
            pass.set_pipeline(&self.pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            let workgroups = ((n + 63) / 64) as u32;
            pass.dispatch_workgroups(workgroups, 1, 1);
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

    /// Measure a frame: the observation carries the frame's identity digest.
    fn observe(&self, frame: &FrameArtifact) -> BenchmarkObservation {
        let (begin, end) = self.time_dispatch(WORKLOAD_SIZE);
        let (status, dur) = classify(begin, end, self.period_ns);
        BenchmarkObservation {
            backend: self.backend.clone(),
            device_name: self.device_name.clone(),
            driver: self.driver.clone(),
            artifact_digest: frame.digest(),
            provenance_digest: frame.provenance_digest.clone(),
            workload: WORKLOAD_NAME.into(),
            workload_size: WORKLOAD_SIZE,
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
    println!("M3 — measurement bound to world identity on {} ({})", gpu.device_name, gpu.backend);
    println!("  replay: scene={} seed={} policy={}", replay.scene, replay.seed, replay.policy);
    println!("  frame.digest() = {}  (the stable identity of what is measured)\n", frame.digest());

    // run the SAME frame many times — identity must stay one, timing must be observed
    let obs: Vec<BenchmarkObservation> = (0..RUNS).map(|_| gpu.observe(&frame)).collect();

    let identities: HashSet<&str> = obs.iter().map(|o| o.artifact_digest.as_str()).collect();
    let ok_times: Vec<f64> = obs.iter()
        .filter(|o| o.timing_status == TimingStatus::Ok)
        .map(|o| o.gpu_duration_ns)
        .collect();
    let distinct_times: HashSet<u64> = ok_times.iter().map(|t| t.to_bits()).collect();
    let ghosts = obs.iter().filter(|o| o.timing_status == TimingStatus::NonPositive).count();
    let (tmin, tmax) = ok_times.iter().fold((f64::INFINITY, 0.0_f64), |(a, b), &x| (a.min(x), b.max(x)));

    println!("  {} runs · identities seen: {} · timing ok: {} (ghosts excluded: {}) · spread {:.0}–{:.0} ns",
             RUNS, identities.len(), ok_times.len(), ghosts, tmin, tmax);

    // --- deterministic checks (don't depend on the GPU cooperating) ---
    let r1 = GoldenReplay { scene: "hallway".into(), seed: 1, policy: "PFAL".into() };
    let r2 = GoldenReplay { scene: "hallway".into(), seed: 1, policy: "PFAL".into() };
    let same_replay_same_digest = r1.frame().digest() == r2.frame().digest();
    let same_digest_same_dispatch = r1.frame().dispatch_descriptor() == r2.frame().dispatch_descriptor();

    let sample = obs.first().unwrap();
    let json = serde_json::to_string(sample).unwrap();
    let round: Result<BenchmarkObservation, _> = serde_json::from_str(&json);
    let json_round_trips = round.as_ref().map(|o| o == sample).unwrap_or(false);

    // Q2: a non-positive interval is a ghost — flagged, excluded from stats, identity intact.
    let (gs_eq, _) = classify(100, 100, gpu.period_ns); // equal ticks
    let (gs_back, _) = classify(100, 90, gpu.period_ns); // backward
    let (gs_ok, _) = classify(100, 140, gpu.period_ns);
    let ghost_handled = gs_eq == TimingStatus::NonPositive
        && gs_back == TimingStatus::NonPositive
        && gs_ok == TimingStatus::Ok;

    println!("\nobservation JSON: {}", json);

    let checks = [
        ("1_same_replay_same_digest", same_replay_same_digest),
        ("2_same_digest_same_dispatch", same_digest_same_dispatch),
        ("3_observation_carries_digest", sample.artifact_digest == frame.digest()),
        ("4_observation_json_round_trips", json_round_trips),
        ("5_one_identity_timing_observed", identities.len() == 1 && distinct_times.len() >= 2),
        ("6_nonpositive_interval_is_a_ghost_not_identity", ghost_handled),
    ];
    println!("\nacceptance:");
    let mut ok = true;
    for (name, pass) in checks.iter() {
        println!("  {}  {}", if *pass { "ok  " } else { "FAIL" }, name);
        ok &= *pass;
    }
    println!(
        "\nM3 {} — identity is stable ({}), timing is observed ({} distinct over {} runs). \
         A ghost interval would change the number, never the digest.",
        if ok { "PASS" } else { "FAIL" },
        frame.digest(),
        distinct_times.len(),
        RUNS
    );
    assert!(ok, "M3 acceptance failed");
}
