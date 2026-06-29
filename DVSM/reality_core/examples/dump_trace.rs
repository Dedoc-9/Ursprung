// SPDX-License-Identifier: AGPL-3.0-only
//! Emit a telemetry trace CSV for the verification backend.
//!
//!   cargo run --example dump_trace -- trace.csv            # clean (air-gap held)
//!   cargo run --example dump_trace -- leak.csv --leak      # planted positive (diagnostic → input)
//!
//! Then audit it:  `cd ..; python reality_core_probe.py reality_core/trace.csv`
//! Replay parity:  emit twice and pass both:  `python reality_core_probe.py a.csv b.csv`

use dvsm_reality_core::{run_trace, write_csv};

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let leak = args.iter().any(|a| a == "--leak");
    let path = args.iter().find(|a| !a.starts_with("--")).cloned().unwrap_or_else(|| "trace.csv".into());

    let rows = run_trace(8, 3, 6000, 1, leak);
    match write_csv(&path, &rows) {
        Ok(()) => println!(
            "wrote {} frames to {}{}",
            rows.len(),
            path,
            if leak { "  (LEAK mode: diagnostic steers the input — broken air-gap fixture)" } else { "" }
        ),
        Err(e) => eprintln!("failed to write {path}: {e}"),
    }
}
