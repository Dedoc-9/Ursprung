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

use crate::binframe_adapter::{
    field, lift, lift_streaming, parse_frames, read_frames_streaming, stream_frames, ParseReport, Row, Schema,
};
use crate::commercial_obligations::{shipped_ledger, CommercialAudit};
use crate::contraction_cert::{certify, CertDecision};
use crate::coupling_audit::{audit_coupling, CouplingInput, CouplingResult, CouplingVerdict};
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
         not run from a public frame dump — hence the non-liftable air-gaps above. The L3 firewall CAN be run \
         from a Schema-D sample dump (`--schema cmi`); see `run_coupling_streaming`. `parts ≠ whole`.\n",
    );
    s
}

// ---- L3: forbidden-coupling firewall over a Schema-D (CMI sample) dump --------------------------------------

/// Error assembling a [`CouplingInput`] from parsed Schema-D rows.
#[derive(Debug, PartialEq, Eq)]
pub enum CmiAssembleError {
    NoSamples,
    MissingColumn(&'static str),
}

impl std::fmt::Display for CmiAssembleError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CmiAssembleError::NoSamples => write!(f, "no samples"),
            CmiAssembleError::MissingColumn(c) => write!(f, "column `{c}` missing or non-numeric"),
        }
    }
}

/// Re-shape parsed Schema-D rows into a [`CouplingInput`] by the field-name convention: `x` and `y` are the
/// channels; every `z*` column (in schema order) is a conditioning dim; every `w*` column is a candidate
/// confounder. The columns ARE the parsed records — this is a pure transpose, so `ingested ≡ constructed`
/// (asserted in `tests/cmi_ingest.rs`). The coupling's identity, identifiability flag, and audit reps/seed are
/// the caller's to declare; the dump supplies only the samples.
pub fn coupling_input_from_rows(
    rows: &[Row],
    schema: &Schema,
    name: &str,
    manifest_rule: &str,
    identifiable: bool,
    reps: usize,
    seed: u64,
) -> Result<CouplingInput, CmiAssembleError> {
    if rows.is_empty() {
        return Err(CmiAssembleError::NoSamples);
    }
    let column = |nm: &'static str| -> Option<Vec<f64>> {
        rows.iter().map(|r| field(r, nm).and_then(|f| f.as_f64())).collect()
    };
    let x = column("x").ok_or(CmiAssembleError::MissingColumn("x"))?;
    let y = column("y").ok_or(CmiAssembleError::MissingColumn("y"))?;
    let mut z_dims = Vec::new();
    let mut w_dims = Vec::new();
    for &(fname, _ft) in schema.fields {
        if fname == "x" || fname == "y" {
            continue;
        }
        let col = column(fname).ok_or(CmiAssembleError::MissingColumn(fname))?;
        if fname.starts_with('z') {
            z_dims.push(col);
        } else if fname.starts_with('w') {
            w_dims.push(col);
        }
    }
    let note = if identifiable {
        String::new()
    } else {
        "flagged unidentifiable: diagnostic is a near-function of Z".to_string()
    };
    Ok(CouplingInput {
        name: name.to_string(),
        manifest_rule: manifest_rule.to_string(),
        note,
        x,
        y,
        z_dims,
        w_dims,
        identifiable,
        reps,
        seed,
    })
}

/// The L3 coupling-gate verdict over a sample dump.
#[derive(Debug)]
pub struct CouplingGateReport {
    pub schema: &'static str,
    pub parse: ParseReport,
    pub result: Option<CouplingResult>,
    pub ok: bool,
    pub reasons: Vec<String>,
}

/// Run the forbidden-coupling firewall over a STREAMED Schema-D dump. Input buffering is bounded (the chunked
/// reader), but the audit holds all samples — CMI binning is inherently O(samples); `bounded-input ≠ O(1)-total`.
/// Fail-closed: a parse anomaly, zero samples, or an un-assemblable input blocks. The verdict mapping is honest:
/// **OBSERVER_CONTAMINATION** (a forbidden coupling affirmatively detected, mis-spec-stable) **blocks**;
/// **AIR_GAP_HELD** passes; a dissolved **CONFOUNDED_ARTIFACT** and a declined **UNIDENTIFIABLE** pass but are
/// reported — the verdict is about THIS window conditioned on the MODELED `Z` (`residual-CMI ≠ channel`;
/// `proves-the-procedure ≠ proves-the-phenomenon`).
pub fn run_coupling_streaming<R: Read>(
    reader: R,
    schema: &Schema,
    header_lines: usize,
    name: &str,
    manifest_rule: &str,
    identifiable: bool,
    reps: usize,
    seed: u64,
) -> std::io::Result<CouplingGateReport> {
    let (rows, parse) = read_frames_streaming(reader, schema, header_lines)?;
    let mut reasons = Vec::new();
    if parse.layout_mismatch {
        reasons.push(format!(
            "ingestion: layout_mismatch ({} leftover bytes — verify the schema against the producer's record)",
            parse.leftover_bytes
        ));
    }
    if parse.nonfinite > 0 {
        reasons.push(format!("ingestion: {} non-finite sample(s)", parse.nonfinite));
    }
    if parse.n_records == 0 {
        reasons.push("ingestion: no samples parsed".to_string());
    }
    if !reasons.is_empty() {
        return Ok(CouplingGateReport { schema: schema.name, parse, result: None, ok: false, reasons });
    }

    let result = match coupling_input_from_rows(&rows, schema, name, manifest_rule, identifiable, reps, seed) {
        Ok(inp) => audit_coupling(&inp),
        Err(e) => {
            reasons.push(format!("ingestion: cannot assemble coupling input — {e}"));
            return Ok(CouplingGateReport { schema: schema.name, parse, result: None, ok: false, reasons });
        }
    };

    if result.verdict == CouplingVerdict::ObserverContamination {
        reasons.push(format!(
            "forbidden coupling DETECTED: {} (I(X;Y|Z)={:.4} vs null {:.4}, z={:.1})",
            result.verdict.as_str(),
            result.cmi,
            result.null_mean,
            result.z_score
        ));
    }
    let ok = reasons.is_empty();
    Ok(CouplingGateReport { schema: schema.name, parse, result: Some(result), ok, reasons })
}

/// Disclaimer-first render of the L3 coupling-gate report.
pub fn render_coupling_report(r: &CouplingGateReport) -> String {
    let mut s = String::new();
    s.push_str("# ursprung-gateway — L3 forbidden-coupling firewall (NOT a certification)\n\n");
    s.push_str(
        "This is a checkable COMMITMENT about THIS window, conditioned on the MODELED legitimate set `Z` — not \
         proof of (no) coupling, not a model-safety certification. `residual-CMI ≠ channel`; \
         `proves-the-procedure ≠ proves-the-phenomenon`; `integrity ≠ truth`.\n\n",
    );
    s.push_str(&format!("- **gate: {}**\n", if r.ok { "PASS (no detected coupling)" } else { "BLOCKED" }));
    s.push_str(&format!(
        "- schema `{}` | samples {} | rec_size {}B | leftover {} | non-finite {}\n\n",
        r.schema, r.parse.n_records, r.parse.rec_size, r.parse.leftover_bytes, r.parse.nonfinite
    ));
    match &r.result {
        Some(res) => {
            s.push_str(&format!("## Coupling: {} ({})\n", res.name, res.manifest_rule));
            s.push_str(&format!("- **verdict: {}**\n", res.verdict.as_str()));
            s.push_str(&format!(
                "- I(X;Y) = {:.4} | I(X;Y|Z) = {:.4} | within-Z null = {:.4} | z = {:.1}\n",
                res.mi, res.cmi, res.null_mean, res.z_score
            ));
            if !res.identifiable {
                s.push_str("- identifiability: **DECLINED** (diagnostic ~ a function of Z; `undetected ≠ absent`)\n");
            }
        }
        None => s.push_str("## No verdict — failed closed at ingestion.\n"),
    }
    if !r.reasons.is_empty() {
        s.push_str("\n## Why blocked\n");
        for reason in &r.reasons {
            s.push_str(&format!("- {}\n", reason));
        }
    }
    s.push_str(
        "\n---\nScope: AIR_GAP_HELD is absence-of-evidence at this window/conditioning, not proof of no \
         coupling; a surviving residual is a CANDIDATE until mis-specification-stable. `parts ≠ whole`.\n",
    );
    s
}

// ---- L2: contraction certifier over a Schema-C (dense κ-block) dump -----------------------------------------

/// Error assembling a κ block + scalars from a parsed Schema-C row.
#[derive(Debug, PartialEq, Eq)]
pub enum CertAssembleError {
    NoMatrix,
    NonSquare(usize),
    MissingColumn(&'static str),
}

impl std::fmt::Display for CertAssembleError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CertAssembleError::NoMatrix => write!(f, "no κ entries (k*) in the schema"),
            CertAssembleError::NonSquare(n) => write!(f, "{n} κ entries is not a square matrix"),
            CertAssembleError::MissingColumn(c) => write!(f, "field `{c}` missing or non-numeric"),
        }
    }
}

/// Re-shape a Schema-C row into `(κ, λ, dt, σ)` by convention: every `k*` field (in schema order) is a κ entry,
/// reshaped **row-major** into an `n×n` matrix (`n = √count`); `lam`/`dt`/`sigma` are the scalars. A pure
/// transpose of the parsed record — no mutation of the ingested κ. `ingested ≡ constructed`.
pub fn kappa_input_from_row(row: &Row, schema: &Schema) -> Result<(Vec<Vec<f64>>, f64, f64, f64), CertAssembleError> {
    let mut flat = Vec::new();
    for &(fname, _ft) in schema.fields {
        if fname.starts_with('k') {
            let v = field(row, fname).and_then(|f| f.as_f64()).ok_or(CertAssembleError::MissingColumn(fname))?;
            flat.push(v);
        }
    }
    let total = flat.len();
    if total == 0 {
        return Err(CertAssembleError::NoMatrix);
    }
    let n = (total as f64).sqrt() as usize;
    if n * n != total {
        return Err(CertAssembleError::NonSquare(total));
    }
    let kappa: Vec<Vec<f64>> = (0..n).map(|i| flat[i * n..(i + 1) * n].to_vec()).collect();
    let lam = field(row, "lam").and_then(|f| f.as_f64()).ok_or(CertAssembleError::MissingColumn("lam"))?;
    let dt = field(row, "dt").and_then(|f| f.as_f64()).ok_or(CertAssembleError::MissingColumn("dt"))?;
    let sigma = field(row, "sigma").and_then(|f| f.as_f64()).ok_or(CertAssembleError::MissingColumn("sigma"))?;
    Ok((kappa, lam, dt, sigma))
}

/// The L2 contraction-gate verdict over a κ-block dump.
#[derive(Debug)]
pub struct CertGateReport {
    pub schema: &'static str,
    pub parse: ParseReport,
    pub n_certified: usize,
    pub ok: bool,
    pub reasons: Vec<String>,
}

/// Run the contraction certifier over a STREAMED Schema-C dump — **O(1) memory** (each κ block certifies
/// independently; one matrix is held at a time, nothing is collected). Fail-closed: a parse anomaly, a
/// non-finite κ/scalar, an un-assemblable record, or ANY record that fails the sufficient condition
/// (`2‖κ‖_F·σ < λ ∧ dtλ ≤ 1`) blocks. The κ is certified **as ingested** — never silently antisymmetrized
/// (`observation ≠ authority`). `ported ≠ ingested` is now closed for L2; `parsed ≠ validated` is enforced.
pub fn run_cert_streaming<R: Read>(
    reader: R,
    schema: &Schema,
    header_lines: usize,
    samples: usize,
    seed: u64,
) -> std::io::Result<CertGateReport> {
    let mut n_certified = 0usize;
    let mut reasons: Vec<String> = Vec::new();
    let mut idx = 0usize;
    let report = stream_frames(reader, schema, header_lines, |row| {
        let i = idx;
        idx += 1;
        match kappa_input_from_row(row, schema) {
            Ok((kappa, lam, dt, sigma)) => {
                let r = certify(&kappa, lam, dt, sigma, samples, seed);
                if r.decision == CertDecision::ContractiveCert {
                    n_certified += 1;
                } else if reasons.len() < 8 {
                    reasons.push(format!(
                        "record {i}: NOT_CERTIFIED (2‖κ‖_F·σ={:.4} vs λ={:.4}; ρ={:.4}; σ_max={:.4})",
                        2.0 * r.frob * sigma,
                        lam,
                        r.rho,
                        r.sigma_max
                    ));
                }
            }
            Err(e) => {
                if reasons.len() < 8 {
                    reasons.push(format!("record {i}: cannot assemble κ — {e}"));
                }
            }
        }
    })?;

    if report.layout_mismatch {
        reasons.push(format!("ingestion: layout_mismatch ({} leftover bytes)", report.leftover_bytes));
    }
    if report.nonfinite > 0 {
        reasons.push(format!("ingestion: {} record(s) carried a non-finite float", report.nonfinite));
    }
    if report.n_records == 0 {
        reasons.push("ingestion: no κ blocks parsed".to_string());
    }

    let clean_parse = !report.layout_mismatch && report.nonfinite == 0 && report.n_records > 0;
    let ok = clean_parse && n_certified == report.n_records;
    Ok(CertGateReport { schema: schema.name, parse: report, n_certified, ok, reasons })
}

/// Disclaimer-first render of the L2 contraction-gate report.
pub fn render_cert_report(r: &CertGateReport) -> String {
    let mut s = String::new();
    s.push_str("# ursprung-gateway — L2 contraction certifier (NOT a certification of model safety)\n\n");
    s.push_str(
        "Each κ block is checked against the SUFFICIENT discrete-contraction condition `2‖κ‖_F·σ < λ ∧ dtλ ≤ 1 \
         ⇒ ρ < 1`. CONTRACTIVE_CERT is a checkable COMMITMENT for ‖S‖ ≤ σ under explicit-Euler — NOT stability \
         for ‖S‖ > σ, the fixed-point clamps, or the full coupled system. κ is certified AS INGESTED (never \
         silently antisymmetrized). `certificate ≠ proof-of-everything`; `integrity ≠ truth`.\n\n",
    );
    s.push_str(&format!("- **gate: {}**\n", if r.ok { "PASS (all κ blocks certified)" } else { "BLOCKED" }));
    s.push_str(&format!(
        "- schema `{}` | κ blocks {} | certified {} | rec_size {}B | leftover {} | non-finite {}\n",
        r.schema, r.parse.n_records, r.n_certified, r.parse.rec_size, r.parse.leftover_bytes, r.parse.nonfinite
    ));
    if !r.reasons.is_empty() {
        s.push_str("\n## Why blocked\n");
        for reason in &r.reasons {
            s.push_str(&format!("- {}\n", reason));
        }
    }
    s.push_str(
        "\n---\nScope: a SUFFICIENT condition with an explicit boundary (`bounded-here ≠ safe-everywhere`); the \
         κ-fix `κ←(κ−κᵀ)/2` widens σ_max but is an advisory, not applied to the committed input. `parts ≠ whole`.\n",
    );
    s
}
