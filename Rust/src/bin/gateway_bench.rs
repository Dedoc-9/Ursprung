// SPDX-License-Identifier: AGPL-3.0-only
//! `gateway-bench` — the §6 metrology harness: a zero-dependency, std-only **throughput + latency** benchmark
//! over the gateway's streaming pipeline. It generates a synthetic dump for one of the four schemas, streams it
//! through the SAME `stream_frames` / `run_*_streaming` paths the binary uses (sealed observer: the timer wraps
//! the real code, never instruments inside it), and prints an un-hyped performance ledger.
//!
//! HONEST BOUNDARIES (read before trusting a number):
//! * **Resident-set size is NOT measured.** `std` exposes no portable RSS API; a real RSS probe needs `/proc`
//!   (Linux) or `GetProcessMemoryInfo` (Windows) — i.e. a non-std crate or raw OS calls, which this zero-dep
//!   harness refuses. Bounded memory is proven BY CONSTRUCTION (the loop holds one record + running aggregates,
//!   never collects; witnessed by `tests/streaming.rs::stream_callback_is_bounded_memory`). A best-effort
//!   `/proc/self/statm` read is printed on Linux only. `bounded-by-construction ≠ measured-RSS`.
//! * **Fail-closed is a VERDICT property, not a mid-stream short-circuit.** `run_*_streaming` reads the whole
//!   dump, then blocks — it does NOT abort on the first bad record. So "time to drop on a malformed block"
//!   equals the full-pass latency; this harness reports it as such rather than as an "instant drop".
//! * **Timing is point-in-time, host-specific, single-process, synthetic-distribution.** `measured ≠
//!   guaranteed`; `simulation ≠ physics`. The boundary clause is printed with every run.

use std::fs::File;
use std::io::{BufWriter, Read, Write};
use std::process::ExitCode;
use std::time::{Duration, Instant};

use ursprung::{
    kappa_skew, run_cert_streaming, run_coupling_streaming, run_gateway_streaming, sigma_max, stream_frames,
    Schema, SCHEMA_ABI, SCHEMA_CMI, SCHEMA_KAPPA, SCHEMA_TELEM, U_MAX_DEFAULT,
};

// ---- a tiny deterministic PRNG (splitmix64) for reproducible synthetic data --------------------------------
struct Rng(u64);
impl Rng {
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn unit(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / ((1u64 << 53) as f64)
    }
}

fn put_u64(b: &mut Vec<u8>, v: u64) {
    b.extend_from_slice(&v.to_le_bytes());
}
fn put_f64(b: &mut Vec<u8>, v: f64) {
    b.extend_from_slice(&v.to_le_bytes());
}
fn put_f32(b: &mut Vec<u8>, v: f32) {
    b.extend_from_slice(&v.to_le_bytes());
}

/// Append one synthetic record of the schema. `corrupt` injects a single non-finite float (the boundary-violation
/// path). κ blocks are the *remediated* skew matrix at a σ inside the margin, so a clean record certifies.
fn gen_record(buf: &mut Vec<u8>, schema_name: &str, frame: u64, rng: &mut Rng, corrupt: bool) {
    match schema_name {
        "telem" => {
            put_u64(buf, frame);
            for k in 0..8 {
                let v = if corrupt && k == 0 { f32::NAN } else { (rng.unit() * 50.0) as f32 };
                put_f32(buf, v);
            }
            buf.extend_from_slice(&[0u8, 1u8, 1u8, 0u8]); // ghost, contained, emitted, _pad
        }
        "abi" => {
            put_u64(buf, frame);
            for i in 0..3 {
                let v = if corrupt && i == 0 { f64::INFINITY } else { rng.unit() * 50.0 };
                put_f64(buf, v);
            }
            buf.extend_from_slice(&[0u8, 1u8]); // ghost, contained
            put_u64(buf, rng.next_u64()); // hash
        }
        "cmi" => {
            for i in 0..4 {
                let v = if corrupt && i == 0 { f64::NAN } else { rng.unit() };
                put_f64(buf, v);
            }
        }
        "kappa" => {
            put_u64(buf, frame);
            let k = kappa_skew(4);
            for i in 0..4 {
                for j in 0..4 {
                    let v = if corrupt && i == 0 && j == 0 { f64::NAN } else { k[i][j] };
                    put_f64(buf, v);
                }
            }
            put_f64(buf, 0.5); // lam
            put_f64(buf, 0.1); // dt
            put_f64(buf, sigma_max(&kappa_skew(4), 0.5) * 0.9); // σ inside the margin ⇒ certifies
        }
        _ => unreachable!(),
    }
}

/// Write `records` synthetic records to `path`, injecting a non-finite record every `corrupt_every` (0 = none).
/// Returns the byte length written.
fn generate_file(path: &std::path::Path, schema_name: &str, records: usize, corrupt_every: usize) -> std::io::Result<u64> {
    let f = File::create(path)?;
    let mut w = BufWriter::new(f);
    let mut rng = Rng(0xDEADBEEF);
    let mut rec = Vec::with_capacity(256);
    for i in 0..records {
        rec.clear();
        let corrupt = corrupt_every > 0 && (i % corrupt_every == 0);
        gen_record(&mut rec, schema_name, i as u64, &mut rng, corrupt);
        w.write_all(&rec)?;
    }
    w.flush()?;
    Ok(std::fs::metadata(path)?.len())
}

fn schema_for(name: &str) -> &'static Schema {
    match name {
        "telem" => &SCHEMA_TELEM,
        "abi" => &SCHEMA_ABI,
        "cmi" => &SCHEMA_CMI,
        "kappa" => &SCHEMA_KAPPA,
        _ => unreachable!(),
    }
}

/// Stream a reader through the real `stream_frames` parse loop, timing per-chunk (chunk = `chunk` records) so the
/// per-record latency distribution is measured with negligible observer overhead (`Instant` is called once per
/// chunk, not per record — per-record `Instant` at ns scale is observer-dominated and would be dishonest).
fn parse_bench<R: Read>(reader: R, schema: &Schema, chunk: usize) -> (usize, Duration, Vec<f64>) {
    let mut count = 0usize;
    let mut per_record_ns: Vec<f64> = Vec::new();
    let t0 = Instant::now();
    let mut last = t0;
    let _ = stream_frames(reader, schema, 0, |_row| {
        count += 1;
        if chunk > 0 && count % chunk == 0 {
            let now = Instant::now();
            per_record_ns.push(now.duration_since(last).as_nanos() as f64 / chunk as f64);
            last = now;
        }
    })
    .expect("benchmark read failed");
    (count, t0.elapsed(), per_record_ns)
}

fn percentile(sorted: &[f64], p: f64) -> f64 {
    if sorted.is_empty() {
        return f64::NAN;
    }
    let idx = (p * (sorted.len() - 1) as f64).round() as usize;
    sorted[idx.min(sorted.len() - 1)]
}

fn mbps(bytes: u64, d: Duration) -> f64 {
    bytes as f64 / 1e6 / d.as_secs_f64().max(1e-12)
}

/// Best-effort resident-set size (KB) — Linux `/proc/self/statm` only; `None` on every other platform. Pure
/// `std::fs`, zero-dep. This is the ONLY RSS signal available without a non-std dependency, and it is absent on
/// the typical Windows host. `bounded-by-construction ≠ measured-RSS`.
fn rss_kb() -> Option<u64> {
    let s = std::fs::read_to_string("/proc/self/statm").ok()?;
    let resident_pages: u64 = s.split_whitespace().nth(1)?.parse().ok()?;
    Some(resident_pages * 4) // 4 KiB pages on the common case
}

fn arg(args: &[String], key: &str) -> Option<String> {
    args.iter().position(|a| a == key).and_then(|i| args.get(i + 1)).cloned()
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    let schema_name = arg(&args, "--schema").unwrap_or_else(|| "telem".to_string());
    if !["telem", "abi", "cmi", "kappa"].contains(&schema_name.as_str()) {
        eprintln!("usage: gateway-bench --schema telem|abi|cmi|kappa [--records N] [--chunk N] [--validate] \
                   [--corrupt] [--samples N] [--reps N] [--output <md>] [--keep]");
        return ExitCode::from(2);
    }
    let records: usize = arg(&args, "--records").and_then(|v| v.parse().ok()).unwrap_or(1_000_000);
    let chunk: usize = arg(&args, "--chunk").and_then(|v| v.parse().ok()).unwrap_or(50_000);
    let samples: usize = arg(&args, "--samples").and_then(|v| v.parse().ok()).unwrap_or(0);
    let reps: usize = arg(&args, "--reps").and_then(|v| v.parse().ok()).unwrap_or(20);
    let validate = args.iter().any(|a| a == "--validate");
    let corrupt = args.iter().any(|a| a == "--corrupt");
    let keep = args.iter().any(|a| a == "--keep");
    let corrupt_every = if corrupt { 1000 } else { 0 };

    let schema = schema_for(&schema_name);
    let rec_size = schema.rec_size();
    let path = std::env::temp_dir().join(format!("ursprung_bench_{schema_name}_{records}.bin"));

    let rss_before = rss_kb();
    eprintln!("gateway-bench: generating {records} × {rec_size}B {schema_name} records → {path:?} …");
    let total_bytes = match generate_file(&path, &schema_name, records, corrupt_every) {
        Ok(n) => n,
        Err(e) => {
            eprintln!("generation failed: {e}");
            return ExitCode::FAILURE;
        }
    };

    // ---- pass 1: parse throughput from FILE (BufReader inside stream_frames; includes disk read) ----
    let file = File::open(&path).expect("reopen");
    let (n_file, t_file, mut chunk_ns) = parse_bench(file, schema, chunk);
    chunk_ns.sort_by(|a, b| a.partial_cmp(b).unwrap());

    // ---- pass 2: parse throughput from MEMORY (isolates CPU from disk) ----
    let bytes = std::fs::read(&path).expect("read to mem");
    let (n_mem, t_mem, _) = parse_bench(&bytes[..], schema, chunk);

    // ---- optional: full-gate validate timing (the schema-appropriate L-layer), and fail-closed latency ----
    let mut validate_line = String::new();
    if validate {
        let f = File::open(&path).expect("reopen");
        let t = Instant::now();
        let (ok, label) = match schema_name.as_str() {
            "telem" | "abi" => {
                let r = run_gateway_streaming(f, schema, U_MAX_DEFAULT, 0, None).expect("gate");
                (r.ok, "L1 lift + L4 ledger")
            }
            "kappa" => {
                let r = run_cert_streaming(f, &SCHEMA_KAPPA, 0, samples, 0).expect("gate");
                (r.ok, "L2 contraction certifier")
            }
            "cmi" => {
                let r = run_coupling_streaming(f, &SCHEMA_CMI, 0, "bench", "synthetic", true, reps, 0).expect("gate");
                (r.ok, "L3 coupling firewall (O(n·reps), one-shot audit)")
            }
            _ => unreachable!(),
        };
        let d = t.elapsed();
        validate_line = format!(
            "- **full-gate** ({label}): {:.3} s · {:.1} MB/s · verdict {} {}\n",
            d.as_secs_f64(),
            mbps(total_bytes, d),
            if ok { "PASS" } else { "BLOCKED" },
            if corrupt { "(corrupt stream ⇒ fail-closed AT THE VERDICT — full pass, no mid-stream short-circuit)" } else { "" }
        );
    }

    let rss_after = rss_kb();
    let p50 = percentile(&chunk_ns, 0.50);
    let p95 = percentile(&chunk_ns, 0.95);
    let p99 = percentile(&chunk_ns, 0.99);

    let mut md = String::new();
    md.push_str("# ursprung-gateway — §6 throughput & bounded-memory ledger (MEASURED, point-in-time)\n\n");
    md.push_str(&format!(
        "schema `{}` ({}) | records {} | record_size {}B | total_bytes {}\n\n",
        schema.name, schema_name, n_file, rec_size, total_bytes
    ));
    md.push_str("## Metrics profile\n");
    md.push_str(&format!(
        "- **read+parse, from file** : {:.3} s · **{:.1} MB/s** · {:.1} ns/record\n",
        t_file.as_secs_f64(),
        mbps(total_bytes, t_file),
        t_file.as_nanos() as f64 / n_file.max(1) as f64
    ));
    md.push_str(&format!(
        "- **read+parse, from memory**: {:.3} s · **{:.1} MB/s** · {:.1} ns/record  (isolates CPU from disk)\n",
        t_mem.as_secs_f64(),
        mbps(total_bytes, t_mem),
        t_mem.as_nanos() as f64 / n_mem.max(1) as f64
    ));
    md.push_str(&format!(
        "- per-record latency (chunked, {chunk}/chunk): p50 {p50:.1} ns · p95 {p95:.1} ns · p99 {p99:.1} ns\n"
    ));
    if !validate_line.is_empty() {
        md.push_str(&validate_line);
    }
    md.push_str("\n## Bounded memory\n");
    match (rss_before, rss_after) {
        (Some(a), Some(b)) => md.push_str(&format!(
            "- RSS (Linux /proc, best-effort): {a} KB → {b} KB across a {}-record stream (flat ⇒ O(1) by observation)\n",
            n_file
        )),
        _ => md.push_str(
            "- RSS: **unavailable on this platform** (no portable std API). Bounded memory holds BY CONSTRUCTION \
             — the loop holds one record + running aggregates, never collects (see \
             `tests/streaming.rs::stream_callback_is_bounded_memory`). `bounded-by-construction ≠ measured-RSS`\n",
        ),
    }
    md.push_str(
        "\n## does_not_show (the boundary clause)\n\
         These metrics represent point-in-time execution throughput on THIS specific local hardware layer under a \
         synthetic distribution; they do not guarantee universal performance parity across divergent OS disk \
         schedulers or uncalibrated file systems. Fail-closed is a verdict property (full-pass), not a mid-stream \
         abort. `measured ≠ guaranteed`; `simulation ≠ physics`; `integrity ≠ truth`.\n",
    );

    // determinism self-check: every generated record parsed back
    let expected = records;
    md.push_str(&format!(
        "\n## Self-check\n- records generated {} == parsed {} : {}\n",
        expected,
        n_file,
        if expected == n_file { "OK" } else { "MISMATCH" }
    ));

    print!("{md}");
    if let Some(out) = arg(&args, "--output") {
        if let Err(e) = std::fs::write(&out, &md) {
            eprintln!("cannot write --output {out:?}: {e}");
        } else {
            eprintln!("gateway-bench: wrote {out}");
        }
    }
    if !keep {
        let _ = std::fs::remove_file(&path);
    } else {
        eprintln!("gateway-bench: kept {path:?}");
    }

    if expected != n_file {
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}

#[cfg(test)]
mod tests {
    use super::*;
    use ursprung::parse_frames;

    // Deterministic (no timing): the generator emits records of the exact schema footprint and they parse back.
    fn gen_buf(schema_name: &str, n: usize) -> Vec<u8> {
        let mut buf = Vec::new();
        let mut rng = Rng(1);
        for i in 0..n {
            gen_record(&mut buf, schema_name, i as u64, &mut rng, false);
        }
        buf
    }

    #[test]
    fn record_footprints_match_schema() {
        for (name, schema) in
            [("telem", &SCHEMA_TELEM), ("abi", &SCHEMA_ABI), ("cmi", &SCHEMA_CMI), ("kappa", &SCHEMA_KAPPA)]
        {
            let buf = gen_buf(name, 1);
            assert_eq!(buf.len(), schema.rec_size(), "{name} record is one rec_size");
        }
    }

    #[test]
    fn generated_stream_parses_clean() {
        for (name, schema) in
            [("telem", &SCHEMA_TELEM), ("abi", &SCHEMA_ABI), ("cmi", &SCHEMA_CMI), ("kappa", &SCHEMA_KAPPA)]
        {
            let buf = gen_buf(name, 37);
            let (rows, rep) = parse_frames(&buf, schema, 0);
            assert_eq!(rep.n_records, 37, "{name} count");
            assert!(!rep.layout_mismatch && rep.nonfinite == 0, "{name} clean");
            assert_eq!(rows.len(), 37);
        }
    }
}
