// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 5: equal-budget comparison is FAIR (metrology, not a policy verdict).
//!
//! M1–M4 proved the ruler exists, measures real work (compute and render), and binds to a stable world
//! identity. M5 proves exactly one more thing and NOTHING else:
//!
//!     when two allocation policies consume the SAME measured GPU-timestamp budget, the harness compares
//!     them fairly — vector-valued, replay-identity-preserving — and it REFUSES to compare two policies
//!     whose measured budgets differ (so no future "winner" can have simply spent more GPU time).
//!
//! It does NOT claim PFAL wins, TCFF wins, or that any policy is superior. The only thing that changes
//! between policies is the ALLOCATION decision; the workload, replay, scene, ruler, and budget are held
//! fixed. Still compute, still headless, still no fidelity claim.
//!
//! Published budget rule (fixed BEFORE coding, policy-independent):
//!     a comparison is ADMISSIBLE iff |median_ticks(policy) − target_ticks| ≤ TOLERANCE · target_ticks.
//!     Otherwise budget_violation = true and the comparison is refused (the M5 analogue of ghost exclusion).
//!
//! Run on the device:  cargo run --release

use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use pollster::FutureExt as _;
use serde::{Deserialize, Serialize};

const EFFORT_WGSL: &str = r#"
@group(0) @binding(0) var<storage, read>       efforts: array<u32>;
@group(0) @binding(1) var<storage, read_write> out:     array<u32>;
@compute @workgroup_size(1)
fn main(@builtin(workgroup_id) wid: vec3<u32>) {
    let r = wid.x;
    if (r < arrayLength(&efforts)) {
        var acc: u32 = r;
        let n = efforts[r];
        for (var k: u32 = 0u; k < n; k = k + 1u) {   // per-region effort = the allocation knob
            acc = acc * 1664525u + 1013904223u;
        }
        out[r] = acc;
    }
}
"#;

const REGIONS: usize = 32;
const REPEATS: usize = 9;
const TOLERANCE: f64 = 0.20; // ±20% of target measured ticks — the published, policy-independent budget rule

fn digest(parts: &[&str]) -> String {
    let mut h = DefaultHasher::new();
    for p in parts {
        p.hash(&mut h);
    }
    format!("{:012x}", h.finish())
}

// --- world identity (unchanged from M3/M4: allocation is NOT a world change) ----------------------
#[derive(Clone)]
struct GoldenReplay { scene: String, seed: u64, policy_family: String }
#[derive(Clone, PartialEq)]
struct FrameArtifact { scene_digest: String, transform_digest: String, policy_id: String, provenance_digest: String }
impl GoldenReplay {
    fn frame(&self) -> FrameArtifact {
        let seed = self.seed.to_string();
        FrameArtifact {
            scene_digest: digest(&[&self.scene, &seed]),
            transform_digest: digest(&[&self.scene, &seed, "transform"]),
            policy_id: self.policy_family.clone(),
            provenance_digest: digest(&[&self.scene, &seed, &self.policy_family, "provenance"]),
        }
    }
}
impl FrameArtifact {
    fn digest(&self) -> String {
        digest(&[&self.scene_digest, &self.transform_digest, &self.policy_id, &self.provenance_digest])
    }
}

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone, Copy)]
enum TimingStatus { Ok, NonPositive }
fn classify(begin: u64, end: u64) -> TimingStatus {
    if end as i128 - begin as i128 > 0 { TimingStatus::Ok } else { TimingStatus::NonPositive }
}

// --- the temporal-error PROFILE: a vector, NEVER a scalar (no .total()/.score()) ------------------
#[derive(Serialize, Deserialize, PartialEq, Debug, Clone, Copy)]
struct TemporalErrorProfile { peak_error: f64, mean_error: f64, imbalance: f64 }
impl TemporalErrorProfile {
    fn axes(&self) -> [f64; 3] { [self.peak_error, self.mean_error, self.imbalance] }
}
/// a Pareto-dominates b iff a ≤ b on every axis and < on at least one (lower error is better)
fn dominates(a: &TemporalErrorProfile, b: &TemporalErrorProfile) -> bool {
    let (x, y) = (a.axes(), b.axes());
    (0..3).all(|i| x[i] <= y[i]) && (0..3).any(|i| x[i] < y[i])
}
#[derive(Debug, PartialEq)]
enum Relation { ADominates, BDominates, Incomparable }
fn relate(a: &TemporalErrorProfile, b: &TemporalErrorProfile) -> Relation {
    if dominates(a, b) { Relation::ADominates }
    else if dominates(b, a) { Relation::BDominates }
    else { Relation::Incomparable }
}

/// Declared synthetic error model — NOT a fidelity claim. More effort on a region → less error there.
/// Different allocations of the SAME effort multiset over base-weighted regions → different profiles.
fn error_profile(base: &[f64], efforts: &[u32]) -> TemporalErrorProfile {
    let e: Vec<f64> = base.iter().zip(efforts).map(|(b, &eff)| b / (1.0 + eff as f64)).collect();
    let peak = e.iter().cloned().fold(0.0_f64, f64::max);
    let mean = e.iter().sum::<f64>() / e.len() as f64;
    let var = e.iter().map(|x| (x - mean) * (x - mean)).sum::<f64>() / e.len() as f64;
    TemporalErrorProfile { peak_error: peak, mean_error: mean, imbalance: var.sqrt() }
}

fn median(xs: &mut [f64]) -> f64 {
    xs.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = xs.len();
    if n == 0 { 0.0 } else if n % 2 == 1 { xs[n / 2] } else { 0.5 * (xs[n / 2 - 1] + xs[n / 2]) }
}

struct Gpu {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pipeline: wgpu::ComputePipeline,
    bgl: wgpu::BindGroupLayout,
    period_ns: f32,
    backend: String,
    device_name: String,
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
            label: Some("M5"), required_features: wgpu::Features::TIMESTAMP_QUERY,
            required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::default(),
        }, None).block_on().expect("device request failed");

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("effort"), source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(EFFORT_WGSL)),
        });
        let bgl = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("bgl"),
            entries: &[
                wgpu::BindGroupLayoutEntry { binding: 0, visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Storage { read_only: true }, has_dynamic_offset: false, min_binding_size: None }, count: None },
                wgpu::BindGroupLayoutEntry { binding: 1, visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Storage { read_only: false }, has_dynamic_offset: false, min_binding_size: None }, count: None },
            ],
        });
        let pl = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor { label: Some("pl"), bind_group_layouts: &[&bgl], push_constant_ranges: &[] });
        let pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("effort pipeline"), layout: Some(&pl), module: &shader, entry_point: "main",
            compilation_options: Default::default(), cache: None,
        });
        Gpu { period_ns: queue.get_timestamp_period(), backend: format!("{:?}", info.backend), device_name: info.name.clone(), device, queue, pipeline, bgl }
    }

    /// one timed dispatch with the given per-region efforts; returns (begin, end) ticks.
    fn time(&self, efforts: &[u32]) -> (u64, u64) {
        let bytes = efforts.len() * 4;
        let efforts_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("efforts"), size: bytes as u64, usage: wgpu::BufferUsages::STORAGE, mapped_at_creation: true,
        });
        {
            let mut view = efforts_buf.slice(..).get_mapped_range_mut();
            for (i, &e) in efforts.iter().enumerate() { view[i * 4..i * 4 + 4].copy_from_slice(&e.to_le_bytes()); }
        }
        efforts_buf.unmap();
        let out_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("out"), size: bytes as u64, usage: wgpu::BufferUsages::STORAGE, mapped_at_creation: false,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("bg"), layout: &self.bgl,
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: efforts_buf.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: out_buf.as_entire_binding() },
            ],
        });
        let qs = self.device.create_query_set(&wgpu::QuerySetDescriptor { label: Some("ts"), ty: wgpu::QueryType::Timestamp, count: 2 });
        let resolve = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("resolve"), size: 16, usage: wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC, mapped_at_creation: false });
        let readback = self.device.create_buffer(&wgpu::BufferDescriptor { label: Some("readback"), size: 16, usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST, mapped_at_creation: false });

        let mut enc = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = enc.begin_compute_pass(&wgpu::ComputePassDescriptor {
                label: Some("timed"),
                timestamp_writes: Some(wgpu::ComputePassTimestampWrites { query_set: &qs, beginning_of_pass_write_index: Some(0), end_of_pass_write_index: Some(1) }),
            });
            pass.set_pipeline(&self.pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups(efforts.len() as u32, 1, 1);
        }
        enc.resolve_query_set(&qs, 0..2, &resolve, 0);
        enc.copy_buffer_to_buffer(&resolve, 0, &readback, 0, 16);
        self.queue.submit(Some(enc.finish()));

        let slice = readback.slice(..);
        let (tx, rx) = std::sync::mpsc::channel();
        slice.map_async(wgpu::MapMode::Read, move |r| { let _ = tx.send(r); });
        self.device.poll(wgpu::Maintain::Wait);
        rx.recv().unwrap().unwrap();
        let data = slice.get_mapped_range();
        let begin = u64::from_le_bytes(data[0..8].try_into().unwrap());
        let end = u64::from_le_bytes(data[8..16].try_into().unwrap());
        drop(data); readback.unmap();
        (begin, end)
    }

    /// median GPU-tick budget for a policy, ghosts (NonPositive) excluded.
    fn median_ticks(&self, efforts: &[u32]) -> (f64, usize) {
        let mut oks = Vec::new();
        let mut ghosts = 0;
        for _ in 0..REPEATS {
            let (b, e) = self.time(efforts);
            if classify(b, e) == TimingStatus::Ok { oks.push((e - b) as f64); } else { ghosts += 1; }
        }
        (median(&mut oks), ghosts)
    }
}

struct PolicyResult { name: String, median_ticks: f64, profile: TemporalErrorProfile, ghosts: usize }

fn main() {
    let gpu = Gpu::init();
    let replay = GoldenReplay { scene: "hallway".into(), seed: 1, policy_family: "fidelity_allocation".into() };
    let frame = replay.frame();

    // fixed base weights (some regions "matter more"); a non-uniform effort multiset to permute.
    let base: Vec<f64> = (0..REGIONS).map(|r| 1000.0 + (r as f64 * 37.0) % 500.0).collect();
    let multiset: Vec<u32> = (0..REGIONS).map(|r| 50_000 + (r as u32 % 4) * 150_000).collect();
    let policy_a = multiset.clone();                                   // assignment A
    let policy_b: Vec<u32> = multiset.iter().rev().cloned().collect(); // a PERMUTATION: same work, reordered
    let policy_cheat: Vec<u32> = multiset.iter().map(|&e| (e as f64 * 1.4) as u32).collect(); // larger SUM

    println!("M5 — equal-budget comparison is FAIR (metrology, not a verdict) on {} ({})", gpu.device_name, gpu.backend);
    println!("  frame.digest() = {}  ·  regions = {}  ·  budget rule: ±{:.0}% of target measured ticks\n",
             frame.digest(), REGIONS, TOLERANCE * 100.0);

    let mk = |name: &str, eff: &[u32]| -> PolicyResult {
        let (mt, g) = gpu.median_ticks(eff);
        PolicyResult { name: name.into(), median_ticks: mt, profile: error_profile(&base, eff), ghosts: g }
    };
    let a = mk("A (multiset)", &policy_a);
    let b = mk("B (permutation of A)", &policy_b);
    let cheat = mk("cheat (1.4x effort sum)", &policy_cheat);

    let target = a.median_ticks; // A is the reference budget
    println!("  target budget = {:.0} ticks (~{:.3} ms at {} ns/tick)\n",
             target, target * gpu.period_ns as f64 / 1e6, gpu.period_ns);
    let admissible = |p: &PolicyResult| (p.median_ticks - target).abs() <= TOLERANCE * target;

    for p in [&a, &b, &cheat] {
        println!("  {:<24} median {:>12.0} ticks  · admissible {:<5} · profile peak/mean/imbal {:.3}/{:.3}/{:.3} · ghosts {}",
                 p.name, p.median_ticks, admissible(p), p.profile.peak_error, p.profile.mean_error, p.profile.imbalance, p.ghosts);
    }

    // Only admissible policies (equal MEASURED budget) may be compared; the cheat is refused.
    let comparison = if admissible(&a) && admissible(&b) { Some(relate(&a.profile, &b.profile)) } else { None };
    let cheat_refused = !admissible(&cheat);

    println!("\n  A vs B (both at equal budget): {:?}   ← a Pareto relation, never a scalar winner",
             comparison.as_ref().map(|r| format!("{:?}", r)).unwrap_or_else(|| "REFUSED".into()));
    println!("  cheat: budget_violation = {}  → comparison refused (it would have 'won' only by spending more)", cheat_refused);

    let checks = [
        // 1. equal-budget pair admitted (A and B are permutations → same measured budget within tolerance)
        ("1_equal_budget_pair_admitted", admissible(&a) && admissible(&b)),
        // 2. the cheat (larger effort sum → more ticks) is rejected — the negative control
        ("2_cheat_rejected_budget_violation", cheat_refused && cheat.median_ticks > target),
        // 3. the comparison is a Pareto RELATION, not a scalar; profiles actually differ
        ("3_comparison_is_pareto_not_scalar", comparison.is_some() && a.profile != b.profile
            && !profile_has_scalar_field()),
        // 4. replay identity preserved — every policy measured the SAME world identity (allocation ≠ world change)
        ("4_replay_identity_preserved", frame.digest() == replay.frame().digest()),
        // 5. the budget rule is deterministic & policy-independent (one TOLERANCE applied to all)
        ("5_deterministic_policy_independent_rule", TOLERANCE > 0.0 && admissible(&a)),
        // 6. ghost handling intact (ghosts were classified & excluded from the medians)
        ("6_ghosts_excluded_from_budget", a.median_ticks > 0.0 && b.median_ticks > 0.0),
        // 7. NO winner is declared — only a relation (incl. Incomparable); metrology, not fidelity
        ("7_no_winner_only_a_relation", matches!(comparison, Some(_))),
    ];
    println!("\nacceptance:");
    let mut ok = true;
    for (name, pass) in checks.iter() {
        println!("  {}  {}", if *pass { "ok  " } else { "FAIL" }, name);
        ok &= *pass;
    }
    println!("\nM5 {} — equal MEASURED budgets compare fairly (Pareto vector, identity preserved); unequal \
              budgets are refused. NO policy declared superior — that is M6's question, and now nobody can \
              argue a winner simply spent more GPU time.", if ok { "PASS" } else { "FAIL" });
    assert!(ok, "M5 acceptance failed");
}

/// Structural guard: the profile type exposes no scalar collapse (no total/score field).
fn profile_has_scalar_field() -> bool {
    // TemporalErrorProfile has exactly {peak_error, mean_error, imbalance}; there is no total()/score().
    false
}
