// SPDX-License-Identifier: AGPL-3.0-only
//! gateway — the single-binary integrity gate (`ursprung-gateway`). It wires the layers a BinaryFrame dump can
//! actually drive: **L1 ingestion + obligation-lift** (`binframe_adapter`) and the **L4 proof-gated ledger**
//! (`commercial_obligations`), with the **Rust-side live receipt read** (Obligation B). It produces a
//! fail-closed verdict + a gate report.
//!
//! HONEST SCOPE (`parts ≠ whole`): this is NOT the full monolith from the spec diagram. The L2 contraction
//! certifier and the L3 CMI firewall need their own typed inputs (κ matrices; `(X,Y,Z)` samples) that a public
//! frame dump does not carry — which is exactly why the Ω→V / ν→λ air-gaps come back **non-liftable** here.
//! Those layers stay library APIs, not steps in this frame-driven CLI. The verdict is a checkable COMMITMENT,
//! not a signature, and never a certification of model safety. `integrity ≠ truth`; `receipt ≠ proof`.

use std::collections::BTreeMap;

use std::io::Read;

use crate::binframe_adapter::{lift, lift_streaming, parse_frames, ParseReport, Schema};
use crate::commercial_obligations::{shipped_ledger, CommercialAudit};
use crate::invariant_ledger::{ObligationResult, ObligationStatus};

#[derive(Debug)]
pub struct GatewayReport {
    pub schema: &'static str,
    pub parse: ParseReport,
    pub obligations: Vec<ObligationResult>,
    pub non_liftable: Vec<(&'static str, &'static str)>,
    pub commercial: CommercialAudit,
    pub live_enforced: bool,
    pub ok: bool,
    pub reasons: Vec<String>,
}

/// Parse a receipt body (`suite \t status \t run-id`) into `suite → status`.
pub fn parse_receipt(text: &str) -> BTreeMap<String, String> {
    let mut m = BTreeMap::new();
    for line in text.lines() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let mut it = line.split('\t');
        if let (Some(suite), Some(status)) = (it.next(), it.next()) {
            m.insert(suite.to_string(), status.to_string());
        }
    }
    m
}

/// Assemble the fail-closed verdict from already-lifted obligations — shared by the whole-file and streaming
/// entry points so they produce an identical `GatewayReport`. Blocks on any parse anomaly, any VIOLATED
/// obligation, or a non-honest commercial ledger.
fn assemble_report(
    schema_name: &'static str,
    parse: ParseReport,
    obligations: Vec<ObligationResult>,
    non_liftable: Vec<(&'static str, &'static str)>,
    receipts: Option<&BTreeMap<String, String>>,
) -> GatewayReport {
    let led = shipped_ledger();
    let commercial = match receipts {
        Some(r) => led.audit_live(r),
        None => led.audit(),
    };

    let mut reasons = Vec::new();
    if parse.layout_mismatch {
        reasons.push(format!(
            "ingestion: layout_mismatch ({} leftover bytes — verify the schema against the build's sizeof)",
            parse.leftover_bytes
        ));
    }
    if parse.nonfinite > 0 {
        reasons.push(format!("ingestion: {} non-finite telemetry row(s)", parse.nonfinite));
    }
    if parse.n_records == 0 {
        reasons.push("ingestion: no records parsed".to_string());
    }
    for o in &obligations {
        if o.status == ObligationStatus::Violated {
            reasons.push(format!("obligation {} VIOLATED: {}", o.id, o.witness));
        }
    }
    if !commercial.honest {
        reasons.push(format!(
            "commercial gate not honest (exceeds={:?} hype={:?} unknown={:?} missing={:?} unverified_live={:?})",
            commercial.exceeds_proof,
            commercial.hype,
            commercial.unknown_obligation,
            commercial.missing_boundary,
            commercial.unverified_live
        ));
    }

    let ok = reasons.is_empty();
    GatewayReport {
        schema: schema_name,
        parse,
        obligations,
        non_liftable,
        commercial,
        live_enforced: receipts.is_some(),
        ok,
        reasons,
    }
}

/// Run the gate over a whole telemetry buffer. Pure (no IO) for testability.
pub fn run_gateway(
    data: &[u8],
    schema: &Schema,
    u_max: f64,
    header_lines: usize,
    receipts: Option<&BTreeMap<String, String>>,
) -> GatewayReport {
    let (rows, parse) = parse_frames(data, schema, header_lines);
    let (obligations, non_liftable) = lift(&rows, schema, u_max, None);
    assemble_report(schema.name, parse, obligations, non_liftable, receipts)
}

/// Run the gate by STREAMING from any reader — bounded memory (O(record), independent of file size). Produces
/// the same `GatewayReport` as `run_gateway` on the same bytes (the obligation builders are shared; equivalence
/// is asserted in `tests/gateway.rs`). This is the binary's path so it scales to large dumps. An IO error is
/// surfaced as `Err`; a truncated/partial trailing record is a `layout_mismatch` ⇒ `ok=false` (fail-closed).
pub fn run_gateway_streaming<R: Read>(
    reader: R,
    schema: &Schema,
    u_max: f64,
    header_lines: usize,
    receipts: Option<&BTreeMap<String, String>>,
) -> std::io::Result<GatewayReport> {
    let (obligations, non_liftable, parse) = lift_streaming(reader, schema, u_max, header_lines)?;
    Ok(assemble_report(schema.name, parse, obligations, non_liftable, receipts))
}

/// Render a disclaimer-first gate report (the gate-approved artifact, or the block reason).
pub fn render_report(r: &GatewayReport) -> String {
    let mut s = String::new();
    s.push_str("# ursprung-gateway — integrity gate report\n\n");
    s.push_str(
        "**NOT a certification of model safety, ethics, or real-world behavior.** This attests that the named \
         checks RAN and their stated bounds held on THIS telemetry window — a checkable COMMITMENT, not a \
         cryptographic signature, and not a proof. `integrity ≠ truth`; `certificate ≠ proof-of-everything`; \
         `receipt ≠ proof`.\n\n",
    );
    s.push_str(&format!("- **verdict: {}**\n", if r.ok { "PASS (gate-approved)" } else { "FAIL (blocked)" }));
    s.push_str(&format!(
        "- schema `{}` | records {} | rec_size {}B | leftover {} | non-finite {}\n",
        r.schema, r.parse.n_records, r.parse.rec_size, r.parse.leftover_bytes, r.parse.nonfinite
    ));
    s.push_str(&format!(
        "- live execution binding: {}\n\n",
        if r.live_enforced {
            "ENFORCED (a fresh receipt was supplied; supported claims' suites checked PASS)"
        } else {
            "NOT enforced (no receipt) — static audit only"
        }
    ));

    s.push_str("## Graded obligations (lifted from the dump)\n");
    if r.obligations.is_empty() {
        s.push_str("- (none liftable from this schema)\n");
    }
    for o in &r.obligations {
        s.push_str(&format!(
            "- **[{}]** {} — {}\n  - does not show: {}\n",
            o.status.as_str(),
            o.id,
            o.witness,
            o.does_not_show
        ));
    }

    s.push_str("\n## Non-liftable (honestly declared blind spots)\n");
    for (id, why) in &r.non_liftable {
        s.push_str(&format!("- **{}** — {}  (`undetected ≠ absent`)\n", id, why));
    }

    s.push_str("\n## Proof-gated commercial ledger\n");
    s.push_str(&format!("- honest: **{}**\n", r.commercial.honest));
    if !r.commercial.unverified_live.is_empty() {
        s.push_str(&format!(
            "- unverified-live (backing suite did not PASS this build): {:?}\n",
            r.commercial.unverified_live
        ));
    }

    if !r.ok {
        s.push_str("\n## Why blocked\n");
        for reason in &r.reasons {
            s.push_str(&format!("- {}\n", reason));
        }
    }

    s.push_str(
        "\n---\nScope: this gate covers L1 ingestion+lift and the L4 proof-gated ledger. The L2 contraction \
         certifier and the L3 CMI firewall need their own typed inputs (κ matrices; (X,Y,Z) samples) and are \
         not run from a public frame dump — hence the non-liftable air-gaps above. `parts ≠ whole`.\n",
    );
    s
}
