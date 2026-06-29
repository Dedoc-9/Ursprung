// SPDX-License-Identifier: AGPL-3.0-only
//! `ursprung-gateway` — the single-binary integrity gate. Ingests a BinaryFrame telemetry dump, lifts graded
//! obligations (L1), runs the proof-gated commercial ledger (L4) — optionally bound to a fresh build receipt
//! (Obligation B) — emits a disclaimer-first gate report, and exits non-zero (fail-closed) on any anomaly.
//!
//!   ursprung-gateway --telemetry <file> [--schema telem|abi] [--receipt <path>] [--u-max <f>]
//!                    [--header-lines <n>] [--output <md>] [--strict]
//!
//! With `--schema cmi` it instead runs the **L3 forbidden-coupling firewall** over a Schema-D sample dump
//! (`x,y,z0,w0` f64 records): assemble → `audit_coupling` → verdict; OBSERVER_CONTAMINATION fails closed.
//!   ursprung-gateway --telemetry <file> --schema cmi [--reps <n>] [--seed <n>] [--unidentifiable]
//!                    [--coupling-name <s>] [--manifest-rule <s>] [--header-lines <n>] [--output <md>]
//!
//! `receipt ≠ proof`; `residual-CMI ≠ channel`; `parts ≠ whole`; the verdict is a commitment, not a certification.

use std::collections::BTreeMap;
use std::process::ExitCode;
use std::time::SystemTime;

use ursprung::gateway::{
    parse_receipt, render_coupling_report, render_report, run_coupling_streaming, run_gateway_streaming,
};
use ursprung::{Schema, SCHEMA_ABI, SCHEMA_CMI, SCHEMA_TELEM, U_MAX_DEFAULT};

const RECEIPT_MAX_AGE_SECS: u64 = 600;

fn arg_val(args: &[String], key: &str) -> Option<String> {
    args.iter().position(|a| a == key).and_then(|i| args.get(i + 1)).cloned()
}

/// Read a receipt only if it exists AND is fresh (mtime within the window). A missing/stale receipt returns
/// None — the live binding is then simply not enforced (and `--strict` turns that into a failure).
fn read_fresh_receipt(path: &str) -> Option<BTreeMap<String, String>> {
    let meta = std::fs::metadata(path).ok()?;
    let modified = meta.modified().ok()?;
    let age = SystemTime::now().duration_since(modified).ok()?.as_secs();
    if age > RECEIPT_MAX_AGE_SECS {
        return None; // stale ⇒ treat as no live evidence
    }
    let text = std::fs::read_to_string(path).ok()?;
    Some(parse_receipt(&text))
}

fn usage() {
    eprintln!(
        "usage: ursprung-gateway --telemetry <file> [--schema telem|abi|cmi] [--receipt <path>] \
         [--u-max <f>] [--header-lines <n>] [--output <md>] [--strict]\n\
         \x20      --schema cmi (L3 firewall): [--reps <n>] [--seed <n>] [--unidentifiable] \
         [--coupling-name <s>] [--manifest-rule <s>]"
    );
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();

    let tele = match arg_val(&args, "--telemetry") {
        Some(t) => t,
        None => {
            usage();
            return ExitCode::from(2);
        }
    };
    // L3 forbidden-coupling firewall over a Schema-D (CMI sample) dump — a distinct gate (verdict, not
    // obligations), so it returns before the obligation path below.
    if arg_val(&args, "--schema").as_deref() == Some("cmi") {
        let header_lines = arg_val(&args, "--header-lines").and_then(|v| v.parse().ok()).unwrap_or(0usize);
        let reps = arg_val(&args, "--reps").and_then(|v| v.parse().ok()).unwrap_or(60usize);
        let seed = arg_val(&args, "--seed").and_then(|v| v.parse().ok()).unwrap_or(0u64);
        let identifiable = !args.iter().any(|a| a == "--unidentifiable");
        let name = arg_val(&args, "--coupling-name").unwrap_or_else(|| "telemetry-coupling".to_string());
        let manifest_rule =
            arg_val(&args, "--manifest-rule").unwrap_or_else(|| "(declared by caller)".to_string());
        let file = match std::fs::File::open(&tele) {
            Ok(f) => f,
            Err(e) => {
                eprintln!("cannot open telemetry {tele:?}: {e}");
                return ExitCode::FAILURE;
            }
        };
        let report = match run_coupling_streaming(
            file,
            &SCHEMA_CMI,
            header_lines,
            &name,
            &manifest_rule,
            identifiable,
            reps,
            seed,
        ) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("ursprung-gateway: read error on {tele:?}: {e} — failing closed.");
                return ExitCode::FAILURE;
            }
        };
        let md = render_coupling_report(&report);
        match arg_val(&args, "--output") {
            Some(out) => {
                if let Err(e) = std::fs::write(&out, &md) {
                    eprintln!("cannot write --output {out:?}: {e}");
                    return ExitCode::FAILURE;
                }
                println!("ursprung-gateway: wrote {out} — verdict {}", if report.ok { "PASS" } else { "FAIL" });
            }
            None => print!("{md}"),
        }
        return if report.ok { ExitCode::SUCCESS } else { ExitCode::FAILURE };
    }

    let schema: &Schema = match arg_val(&args, "--schema").as_deref() {
        Some("abi") => &SCHEMA_ABI,
        Some("telem") | None => &SCHEMA_TELEM,
        Some(other) => {
            eprintln!("unknown --schema {other:?} (use telem|abi|cmi)");
            return ExitCode::from(2);
        }
    };
    let u_max = arg_val(&args, "--u-max").and_then(|v| v.parse().ok()).unwrap_or(U_MAX_DEFAULT);
    let header_lines = arg_val(&args, "--header-lines").and_then(|v| v.parse().ok()).unwrap_or(0usize);
    let strict = args.iter().any(|a| a == "--strict");

    let receipt_path = arg_val(&args, "--receipt");
    let receipts = receipt_path.as_deref().and_then(read_fresh_receipt);
    if strict && receipt_path.is_some() && receipts.is_none() {
        eprintln!("--strict: the requested receipt is missing or stale — failing closed. receipt ≠ proof.");
        return ExitCode::FAILURE;
    }

    // STREAM the file (bounded memory, O(record)) rather than slurping it whole — scales to large dumps.
    let file = match std::fs::File::open(&tele) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("cannot open telemetry {tele:?}: {e}");
            return ExitCode::FAILURE;
        }
    };
    let report = match run_gateway_streaming(file, schema, u_max, header_lines, receipts.as_ref()) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("ursprung-gateway: read error on {tele:?}: {e} — failing closed.");
            return ExitCode::FAILURE;
        }
    };
    let md = render_report(&report);

    match arg_val(&args, "--output") {
        Some(out) => {
            if let Err(e) = std::fs::write(&out, &md) {
                eprintln!("cannot write --output {out:?}: {e}");
                return ExitCode::FAILURE;
            }
            println!("ursprung-gateway: wrote {out} — verdict {}", if report.ok { "PASS" } else { "FAIL" });
        }
        None => print!("{md}"),
    }

    if report.ok {
        ExitCode::SUCCESS
    } else {
        eprintln!("ursprung-gateway: BLOCKED (non-zero exit). A red gate is decisive; tested ≠ safe.");
        ExitCode::FAILURE
    }
}
