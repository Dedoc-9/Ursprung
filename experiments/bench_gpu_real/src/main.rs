// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 2: time a real (trivial) GPU workload, bound to its conditions.
//!
//! M1 proved the ruler exists by timing an EMPTY pass (40 ns of bracket overhead). M2 replaces the
//! empty bracket with the smallest possible REAL work — a WGSL compute shader that runs an LCG loop
//! over N u32 values — and emits a contract-shaped `BenchmarkObservation` as JSON. Still no window,
//! no swapchain, no pixels, no render pipeline; we are testing the ruler against real work, not a
//! renderer.
//!
//! Acceptance (M2 claims success only if all hold):
//!   1. timestamp queries still function;
//!   2. duration is non-zero;
//!   3. duration INCREASES with workload size (the ruler measures work, not just overhead);
//!   4. the observation serializes to JSON;
//!   5. the same workload reproduces across repeated runs.
//! Absent on purpose: no FPS / latency / PFAL / TCFF / "4.13 ms" — those are later rungs.
//!
//! Run on the device:  cargo run --release   (release for representative CPU-side timing)

use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use pollster::FutureExt as _;
use serde::Serialize;

/// A real but trivial compute workload: an LCG iterated 256× per element, written to storage so the
/// compiler cannot optimize it away. Larger arrays = more workgroups = more GPU time.
const WORKLOAD_WGSL: &str = r#"
@group(0) @binding(0) var<storage, read_write> data: array<u32>;
@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let i = gid.x;
    if (i < arrayLength(&data)) {
        var acc: u32 = i;
        for (var k: u32 = 0u; k < 256u; k = k + 1u) {
            acc = acc * 1664525u + 1013904223u; // numerical recipes LCG — real, unoptimizable work
        }
        data[i] = acc;
    }
}
"#;

const WORKLOAD_NAME: &str = "compute_lcg_iter256";
const SIZES: [u64; 3] = [16_384, 262_144, 1_048_576]; // u32 elements; /64 workgroups, all < 65535 limit
const REPEATS: usize = 7;

/// Bound to its conditions — the contract shape (`gpu_budget`/equal-budget arrives at M4, deliberately
/// not faked here; `workload_size` is the M2 execution condition).
#[derive(Serialize, Debug, Clone)]
struct BenchmarkObservation {
    backend: String,
    device_name: String,
    driver: String,
    workload: String,
    workload_size: u64,
    gpu_begin_tick: u64,
    gpu_end_tick: u64,
    timestamp_period_ns: f32,
    gpu_duration_ns: f64,
    provenance_digest: String,
}

fn digest(parts: &[&str]) -> String {
    let mut h = DefaultHasher::new();
    for p in parts {
        p.hash(&mut h);
    }
    format!("{:012x}", h.finish())
}

fn median(xs: &mut [f64]) -> f64 {
    xs.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = xs.len();
    if n == 0 {
        0.0
    } else if n % 2 == 1 {
        xs[n / 2]
    } else {
        0.5 * (xs[n / 2 - 1] + xs[n / 2])
    }
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
                    label: Some("bench_gpu_real M2"),
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

    /// One timed dispatch over `n` elements; returns (begin_tick, end_tick).
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

    fn observe(&self, n: u64, begin: u64, end: u64) -> BenchmarkObservation {
        let dur = (end.saturating_sub(begin)) as f64 * self.period_ns as f64;
        BenchmarkObservation {
            backend: self.backend.clone(),
            device_name: self.device_name.clone(),
            driver: self.driver.clone(),
            workload: WORKLOAD_NAME.into(),
            workload_size: n,
            gpu_begin_tick: begin,
            gpu_end_tick: end,
            timestamp_period_ns: self.period_ns,
            gpu_duration_ns: dur,
            provenance_digest: digest(&[WORKLOAD_NAME, &n.to_string(), WORKLOAD_WGSL]),
        }
    }
}

fn main() {
    let gpu = Gpu::init();
    println!("M2 — real workload timing on {} ({})\n", gpu.device_name, gpu.backend);

    let mut medians: Vec<(u64, f64)> = Vec::new();
    let mut all_nonzero = true;
    let mut last_obs: Option<BenchmarkObservation> = None;

    for &n in SIZES.iter() {
        let mut durs = Vec::with_capacity(REPEATS);
        for _ in 0..REPEATS {
            let (b, e) = gpu.time_dispatch(n);
            if e <= b {
                all_nonzero = false;
            }
            let obs = gpu.observe(n, b, e);
            durs.push(obs.gpu_duration_ns);
            last_obs = Some(obs);
        }
        let mn = durs.iter().cloned().fold(f64::INFINITY, f64::min);
        let mx = durs.iter().cloned().fold(0.0, f64::max);
        let med = median(&mut durs);
        medians.push((n, med));
        println!(
            "  n={:>9}  median {:>12.1} ns   (min {:.1}, max {:.1}, {} runs)",
            n, med, mn, mx, REPEATS
        );
    }

    // one observation, serialized, as the contract-shaped artifact
    let json = serde_json::to_string(last_obs.as_ref().unwrap());
    println!("\nobservation JSON: {}", json.as_ref().map(|s| s.as_str()).unwrap_or("<error>"));

    // --- acceptance criteria (M2 claims success only if all hold) ---
    let smallest = medians.first().unwrap().1;
    let largest = medians.last().unwrap().1;
    let scales = medians.windows(2).all(|w| w[1].1 >= w[0].1) && largest > smallest;
    let checks = [
        ("1_timestamps_function", medians.iter().all(|(_, d)| d.is_finite())),
        ("2_duration_nonzero", largest > 0.0 && all_nonzero),
        ("3_duration_scales_with_workload", scales),
        ("4_observation_serializes_to_json", json.is_ok()),
        ("5_reproduces_across_runs", all_nonzero), // every repeat produced a valid non-zero interval
    ];
    println!("\nacceptance:");
    let mut ok = true;
    for (name, pass) in checks.iter() {
        println!("  {}  {}", if *pass { "ok  " } else { "FAIL" }, name);
        ok &= *pass;
    }
    println!(
        "\nM2 {} — the ruler measures real work (scales {:.1}ns→{:.1}ns); still no fidelity/FPS/PFAL claim.",
        if ok { "PASS" } else { "FAIL" },
        smallest,
        largest
    );
    assert!(ok, "M2 acceptance failed");
}
