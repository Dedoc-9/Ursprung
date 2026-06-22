// SPDX-License-Identifier: AGPL-3.0-only
//! bench_gpu_real — Milestone 1: does the contract's GPU-interval ruler exist on real silicon?
//!
//! The smallest non-faked claim in the whole project: time an EMPTY GPU compute pass with timestamp
//! queries on this device, and print `(end - begin) * timestamp_period` nanoseconds — with provenance.
//! No window, no swapchain, no pixels, no fidelity claim. Just the ruler.
//!
//! Guardrails (deliberate):
//!   * TIMESTAMP_QUERY is a REQUIRED feature — if the adapter can't do it, we fail hard, never silently.
//!   * the raw primitive is used (QuerySet -> resolve -> map/read), no wgpu-profiler layer on top yet.
//!   * the output carries provenance (backend / adapter / driver / period) — a bare number would already
//!     violate the benchmark contract.
//!
//! Run on the device:  cargo run        (a release build times more realistically: cargo run --release)

use pollster::FutureExt as _;

/// Mirrors the Python contract's measurement object: a number never travels without its conditions.
#[derive(Debug)]
struct GpuMeasurement {
    backend: String,
    adapter: String,
    driver: String,
    timestamp_period_ns: f32, // nanoseconds per timestamp tick (from the queue)
    begin: u64,               // raw GPU timestamp at pass begin
    end: u64,                 // raw GPU timestamp at pass end
}

impl GpuMeasurement {
    fn gpu_interval_ns(&self) -> f64 {
        (self.end - self.begin) as f64 * self.timestamp_period_ns as f64
    }
}

fn main() {
    // 1. Instance — ask for the "primary" backends (DX12 / Vulkan / Metal), not the GL fallback.
    let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
        backends: wgpu::Backends::PRIMARY,
        ..Default::default()
    });

    // 2. Adapter — a handle to a real GPU. HighPerformance picks the discrete/iGPU over a software one.
    let adapter = instance
        .request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            force_fallback_adapter: false,
            compatible_surface: None, // headless — we are not drawing to a window
        })
        .block_on()
        .expect("no GPU adapter found — is a graphics driver present?");

    let info = adapter.get_info();

    // 3. The ruler must be REAL: require TIMESTAMP_QUERY, fail hard if the adapter can't provide it.
    if !adapter.features().contains(wgpu::Features::TIMESTAMP_QUERY) {
        eprintln!(
            "RULER ABSENT: adapter '{}' ({:?}) does not expose TIMESTAMP_QUERY.\n\
             The benchmark question is specifically about the GPU ruler, so this is a hard stop, \
             not a silent fallback.",
            info.name, info.backend
        );
        std::process::exit(1);
    }

    // 4. Device + queue, with the timestamp feature REQUIRED (not optional).
    let (device, queue) = adapter
        .request_device(
            &wgpu::DeviceDescriptor {
                label: Some("bench_gpu_real device"),
                required_features: wgpu::Features::TIMESTAMP_QUERY,
                required_limits: wgpu::Limits::default(),
                memory_hints: wgpu::MemoryHints::default(),
            },
            None,
        )
        .block_on()
        .expect("device request failed despite TIMESTAMP_QUERY being reported — driver/feature mismatch");

    // 5. A query set holding two timestamps: [begin, end].
    let query_set = device.create_query_set(&wgpu::QuerySetDescriptor {
        label: Some("timestamps"),
        ty: wgpu::QueryType::Timestamp,
        count: 2,
    });

    // 6. Two GPU buffers: one the GPU resolves the raw timestamps into, one the CPU can map and read.
    let resolve_buffer = device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("query resolve"),
        size: 16, // 2 timestamps * 8 bytes
        usage: wgpu::BufferUsages::QUERY_RESOLVE | wgpu::BufferUsages::COPY_SRC,
        mapped_at_creation: false,
    });
    let readback_buffer = device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("readback"),
        size: 16,
        usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });

    // 7. Record an EMPTY compute pass, bracketed by the two timestamps. No pipeline, no dispatch —
    //    the pass itself is the thing being timed; Milestone 1 only needs the ruler, not work.
    let mut encoder = device.create_command_encoder(&wgpu::CommandEncoderDescriptor {
        label: Some("timed empty pass"),
    });
    {
        let _pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
            label: Some("empty"),
            timestamp_writes: Some(wgpu::ComputePassTimestampWrites {
                query_set: &query_set,
                beginning_of_pass_write_index: Some(0),
                end_of_pass_write_index: Some(1),
            }),
        });
        // (intentionally empty)
    }
    // Resolve the raw timestamps into a GPU buffer, then copy to a CPU-readable buffer.
    encoder.resolve_query_set(&query_set, 0..2, &resolve_buffer, 0);
    encoder.copy_buffer_to_buffer(&resolve_buffer, 0, &readback_buffer, 0, 16);
    queue.submit(Some(encoder.finish()));

    // 8. Map the readback buffer, wait for the GPU, and read the two u64 timestamps.
    let slice = readback_buffer.slice(..);
    let (tx, rx) = std::sync::mpsc::channel();
    slice.map_async(wgpu::MapMode::Read, move |res| {
        let _ = tx.send(res);
    });
    device.poll(wgpu::Maintain::Wait); // block until the GPU is done and the mapping is ready
    rx.recv().expect("map channel dropped").expect("buffer map failed");

    let (begin, end) = {
        let data = slice.get_mapped_range();
        let begin = u64::from_le_bytes(data[0..8].try_into().unwrap());
        let end = u64::from_le_bytes(data[8..16].try_into().unwrap());
        (begin, end)
    };
    readback_buffer.unmap();

    let m = GpuMeasurement {
        backend: format!("{:?}", info.backend),
        adapter: info.name.clone(),
        driver: format!("{} {}", info.driver, info.driver_info),
        timestamp_period_ns: queue.get_timestamp_period(),
        begin,
        end,
    };

    // 9. The physical invariant: time cannot go backward. This is the ruler sanity check.
    if m.end < m.begin {
        panic!("RULER VIOLATION: end < begin ({} < {}) — GPU timestamp went backward", m.end, m.begin);
    }

    // human-readable
    println!("{:#?}", m);
    println!("gpu_interval_ns = {:.1}", m.gpu_interval_ns());
    if m.end == m.begin {
        println!(
            "NOTE: end == begin — the empty pass was below one timestamp tick. The ruler RESOLVED \
             (mechanism works); Milestone 2+ adds trivial GPU work so the interval is non-zero."
        );
    }

    // one-line JSON, ready to paste into the Python contract (BenchmarkObservation) later
    println!(
        "{{\"backend\":\"{}\",\"adapter\":\"{}\",\"driver\":\"{}\",\"timestamp_period_ns\":{},\
         \"begin\":{},\"end\":{},\"gpu_interval_ns\":{:.1}}}",
        m.backend, m.adapter, m.driver, m.timestamp_period_ns, m.begin, m.end, m.gpu_interval_ns()
    );
}
