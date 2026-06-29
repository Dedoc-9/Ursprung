// SPDX-License-Identifier: AGPL-3.0-only
//! binframe_adapter (Sub-Slice 1A) — the BinaryFrame PARSER, ported from `DVSM/commercial/binframe_adapter.py`.
//! Gateway layer 1, ingestion. This slice is the parser ONLY: read a fixed-record byte stream, validate the
//! layout, flag anomalies into a [`ParseReport`], and return typed rows.
//!
//! Two on-disk schemas (packed little-endian, `repr(C)`):
//!   * [`SCHEMA_TELEM`] (`dvsm_one_file.BinaryFrame`, 44 B) — rich diagnostics: frame + 8 f32 channels
//!     (energy, novelty, stress, stiffness, omega_norm, entropy, drift, resonance_peak) + 4 u8
//!     (ghost, contained, emitted, _pad). NO replay hash.
//!   * [`SCHEMA_ABI`] (`dvsm_v20.run_profile`, 42 B) — frame + 3 f64 (energy, stress, entropy) + 2 u8
//!     (ghost, contained) + u64 hash (the FNV-1a replay hash).
//!
//! ## Faithful to the reference — what this DOES / DOES NOT do
//! - **`lift()` (Sub-Slice 1B, now wired).** Grades the obligations a dump CAN support (containment,
//!   replay-parity) over the ported [`crate::invariant_ledger`], and HONESTLY declares the non-liftable
//!   air-gap checks (Ω→V, ν→λ) because the public frame carries neither `v` nor `lambda_eff`.
//!   `emitted-telemetry ≠ full-state`; `undetected ≠ absent`.
//! - **No "ForbiddenSetViolation."** The Python `ParseReport` has exactly two anomalies — `layout_mismatch`
//!   (a non-zero record remainder) and `nonfinite` (NaN/Inf in a float field). There is no forbidden-flag check
//!   in the reference, so none is invented here. `claim ≠ code`.
//! - **Not zero-copy.** Fields are decoded into typed values (a cheap copy), exactly like the Python rows.
//!
//! ## `does_not_show`
//! `parsed ≠ correct`: the formats assume packed little-endian. A build whose `repr(C)` inserts padding has a
//! different `rec_size`; the report's `layout_mismatch` catches a non-dividing stream, but a coincidentally
//! dividing-but-misaligned stream would parse to garbage. Verify the schema against your build's
//! `sizeof(BinaryFrame)` before trusting values. `emitted-telemetry ≠ full-state` (V and λ are not emitted, so
//! the Ω→V / ν→λ air-gap obligations cannot be lifted from a public frame — surfaced in 1B, not here).

use crate::invariant_ledger::{ObligationResult, ObligationStatus};
use std::io::{BufReader, Read};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FieldType {
    U64,
    F32,
    F64,
    U8,
    Pad, // a byte consumed but dropped from output (mirrors the Python `_`-prefixed field)
}

/// A decoded field value. `PartialEq` only (floats are not `Eq`).
#[derive(Debug, Clone, PartialEq)]
pub enum Field {
    U64(u64),
    F32(f32),
    F64(f64),
    U8(u8),
}

impl Field {
    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Field::F32(x) => Some(*x as f64),
            Field::F64(x) => Some(*x),
            _ => None,
        }
    }
    pub fn as_u64(&self) -> Option<u64> {
        match self {
            Field::U64(x) => Some(*x),
            _ => None,
        }
    }
    pub fn as_u8(&self) -> Option<u8> {
        match self {
            Field::U8(x) => Some(*x),
            _ => None,
        }
    }
    pub fn is_nonfinite(&self) -> bool {
        match self {
            Field::F32(x) => !x.is_finite(),
            Field::F64(x) => !x.is_finite(),
            _ => false,
        }
    }
}

/// A `struct`-format schema: an ordered list of `(field name, type)`.
pub struct Schema {
    pub name: &'static str,
    pub fields: &'static [(&'static str, FieldType)],
}

impl Schema {
    pub fn rec_size(&self) -> usize {
        self.fields
            .iter()
            .map(|(_, ft)| match ft {
                FieldType::U64 | FieldType::F64 => 8,
                FieldType::F32 => 4,
                FieldType::U8 | FieldType::Pad => 1,
            })
            .sum()
    }
}

pub const SCHEMA_TELEM: Schema = Schema {
    name: "dvsm_one_file.BinaryFrame",
    fields: &[
        ("frame", FieldType::U64),
        ("energy", FieldType::F32),
        ("novelty", FieldType::F32),
        ("stress", FieldType::F32),
        ("stiffness", FieldType::F32),
        ("omega_norm", FieldType::F32),
        ("entropy", FieldType::F32),
        ("drift", FieldType::F32),
        ("resonance_peak", FieldType::F32),
        ("ghost", FieldType::U8),
        ("contained", FieldType::U8),
        ("emitted", FieldType::U8),
        ("_pad", FieldType::Pad),
    ],
};

pub const SCHEMA_ABI: Schema = Schema {
    name: "dvsm_v20.run_profile",
    fields: &[
        ("frame", FieldType::U64),
        ("energy", FieldType::F64),
        ("stress", FieldType::F64),
        ("entropy", FieldType::F64),
        ("ghost", FieldType::U8),
        ("contained", FieldType::U8),
        ("hash", FieldType::U64),
    ],
};

/// One parsed row: `(field name, value)`, with `Pad` fields dropped (mirrors the Python `_`-prefix skip).
pub type Row = Vec<(&'static str, Field)>;

/// Look up a field in a row by name.
pub fn field<'a>(row: &'a Row, name: &str) -> Option<&'a Field> {
    row.iter().find(|(n, _)| *n == name).map(|(_, v)| v)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseReport {
    pub schema: &'static str,
    pub n_records: usize,
    pub rec_size: usize,
    pub leftover_bytes: usize,
    pub layout_mismatch: bool,
    pub nonfinite: usize,
}

impl ParseReport {
    pub fn ok(&self) -> bool {
        !self.layout_mismatch && self.nonfinite == 0 && self.n_records > 0
    }
}

/// Parse a fixed-record byte stream into typed rows + a [`ParseReport`]. `header_lines` skips that many leading
/// newline-terminated text lines (e.g. the `run_profile` header) before the binary body. A non-zero remainder
/// (`layout_mismatch`) or any non-finite float (`nonfinite`) is surfaced, never hidden. `parsed ≠ correct`.
pub fn parse_frames(data: &[u8], schema: &Schema, header_lines: usize) -> (Vec<Row>, ParseReport) {
    // skip header text lines
    let mut start = 0usize;
    for _ in 0..header_lines {
        match data[start..].iter().position(|&b| b == b'\n') {
            Some(p) => start += p + 1,
            None => break,
        }
    }
    let body = &data[start..];

    let rec = schema.rec_size();
    let (n, rem) = if rec == 0 { (0, body.len()) } else { (body.len() / rec, body.len() % rec) };

    let mut rows: Vec<Row> = Vec::with_capacity(n);
    let mut nonfinite = 0usize;
    for i in 0..n {
        let (row, row_nonfinite) = decode_record(&body[i * rec..i * rec + rec], schema);
        if row_nonfinite {
            nonfinite += 1;
        }
        rows.push(row);
    }

    let report = ParseReport {
        schema: schema.name,
        n_records: n,
        rec_size: rec,
        leftover_bytes: rem,
        layout_mismatch: rem != 0,
        nonfinite,
    };
    (rows, report)
}

/// Decode ONE fixed-size record into a `Row` + whether it carried a non-finite float. Shared by the whole-file
/// [`parse_frames`] and the streaming readers so they decode IDENTICALLY — `streaming-decode ≡ whole-file-decode`
/// by construction (the equivalence is asserted in `tests/streaming.rs`).
fn decode_record(rec_bytes: &[u8], schema: &Schema) -> (Row, bool) {
    let mut off = 0usize;
    let mut row: Row = Vec::with_capacity(schema.fields.len());
    let mut nonfinite = false;
    for &(name, ft) in schema.fields {
        match ft {
            FieldType::U64 => {
                let v = u64::from_le_bytes(rec_bytes[off..off + 8].try_into().unwrap());
                off += 8;
                row.push((name, Field::U64(v)));
            }
            FieldType::F32 => {
                let v = f32::from_le_bytes(rec_bytes[off..off + 4].try_into().unwrap());
                off += 4;
                if !v.is_finite() {
                    nonfinite = true;
                }
                row.push((name, Field::F32(v)));
            }
            FieldType::F64 => {
                let v = f64::from_le_bytes(rec_bytes[off..off + 8].try_into().unwrap());
                off += 8;
                if !v.is_finite() {
                    nonfinite = true;
                }
                row.push((name, Field::F64(v)));
            }
            FieldType::U8 => {
                row.push((name, Field::U8(rec_bytes[off])));
                off += 1;
            }
            FieldType::Pad => {
                off += 1; // consumed, dropped
            }
        }
    }
    (row, nonfinite)
}

/// Stream-parse fixed records from any `Read`, invoking `on_record(&Row)` per record — **bounded input memory**
/// (one record buffer; the whole dump is never loaded). Returns the same [`ParseReport`] the whole-file
/// [`parse_frames`] would, including `layout_mismatch` on a trailing partial record. Synchronous and
/// deterministic — NO async runtime, NO extra dependency (`std::io::BufReader` only). `streaming ≡ whole-file`
/// on the decisions; the input may arrive in arbitrary fragments (a record is filled across reads).
pub fn stream_frames<R: Read, F: FnMut(&Row)>(
    reader: R,
    schema: &Schema,
    header_lines: usize,
    mut on_record: F,
) -> std::io::Result<ParseReport> {
    let mut r = BufReader::new(reader);
    // skip `header_lines` newline-terminated text lines
    let mut skipped = 0usize;
    let mut one = [0u8; 1];
    while skipped < header_lines {
        match r.read(&mut one)? {
            0 => break,
            _ => {
                if one[0] == b'\n' {
                    skipped += 1;
                }
            }
        }
    }

    let rec = schema.rec_size();
    let mut buf = vec![0u8; rec.max(1)];
    let mut n_records = 0usize;
    let mut nonfinite = 0usize;
    let mut leftover_bytes = 0usize;
    if rec > 0 {
        loop {
            let mut filled = 0usize;
            while filled < rec {
                match r.read(&mut buf[filled..rec])? {
                    0 => break,
                    k => filled += k,
                }
            }
            if filled == 0 {
                break; // clean EOF on a record boundary
            }
            if filled < rec {
                leftover_bytes = filled; // trailing partial record
                break;
            }
            let (row, rn) = decode_record(&buf[..rec], schema);
            if rn {
                nonfinite += 1;
            }
            n_records += 1;
            on_record(&row);
        }
    }

    Ok(ParseReport {
        schema: schema.name,
        n_records,
        rec_size: rec,
        leftover_bytes,
        layout_mismatch: leftover_bytes != 0,
        nonfinite,
    })
}

/// Convenience: stream into a `Vec<Row>` — still bounded *input* buffering (reads incrementally rather than
/// loading the whole file as bytes). Mirrors [`parse_frames`]'s return so it is a drop-in for large dumps.
pub fn read_frames_streaming<R: Read>(
    reader: R,
    schema: &Schema,
    header_lines: usize,
) -> std::io::Result<(Vec<Row>, ParseReport)> {
    let mut rows = Vec::new();
    let report = stream_frames(reader, schema, header_lines, |row| rows.push(row.clone()))?;
    Ok((rows, report))
}

// ---- lift: obligations the emitted telemetry CAN support, kernel-relative (Sub-Slice 1B) ----------

/// Default containment bound (`U_MAX_DEFAULT` in the Python adapter).
pub const U_MAX_DEFAULT: f64 = 100.0;

fn has_field(rows: &[Row], name: &str) -> bool {
    rows.first().map_or(false, |r| field(r, name).is_some())
}

/// §7 containment from the pre-reduced max energy + frame count — the obligation builder shared by the
/// whole-file `containment` and the streaming fold, so both produce a BYTE-IDENTICAL `ObligationResult`.
/// `max_energy = None` (no energy field seen) ⇒ NaN ⇒ VIOLATED, matching the whole-file path.
pub fn containment_from(max_energy: Option<f64>, n_frames: usize, u_max: f64) -> ObligationResult {
    let mx = max_energy.unwrap_or(f64::NAN);
    let status = if mx.is_finite() && mx < u_max {
        ObligationStatus::Bounded
    } else {
        ObligationStatus::Violated
    };
    ObligationResult::new(
        "DVSM-3-kernel",
        "‖Z‖ stays under U_MAX on the REAL emitted telemetry",
        status,
        format!("max(energy)={:.3} over {} real frames (bound={})", mx, n_frames, u_max),
        "boundedness for all inputs — only this dumped run; empirical-boundedness ≠ certified",
        "a real dump whose energy reaches U_MAX without GhostSnap recovery",
    )
}

/// §7 containment: ‖Z‖ (the `energy` channel) stays under `u_max` on the emitted run.
pub fn containment(rows: &[Row], u_max: f64) -> ObligationResult {
    let mut max_energy: Option<f64> = None;
    for r in rows {
        if let Some(v) = field(r, "energy").and_then(|f| f.as_f64()) {
            max_energy = Some(match max_energy {
                Some(m) => m.max(v),
                None => v,
            });
        }
    }
    containment_from(max_energy, rows.len(), u_max)
}

/// The UNDERDETERMINED "no replay hash in this schema" obligation — shared by `lift` and `lift_streaming`.
fn no_hash_obligation(schema: &Schema) -> ObligationResult {
    ObligationResult::new(
        "DVSM-6-kernel",
        "replay-hash parity on the real dump",
        ObligationStatus::Underdetermined,
        format!("the {} frame carries no hash field — cannot check replay parity from this schema", schema.name),
        "anything about reproducibility from a hashless dump",
        "switch to the ABI/run_profile dump (carries the FNV-1a hash)",
    )
}

/// §6 replay parity: two real dumps from the same seed share an identical replay-hash sequence.
pub fn replay_parity(rows_a: &[Row], rows_b: &[Row]) -> ObligationResult {
    let a: Vec<Option<u64>> = rows_a.iter().map(|r| field(r, "hash").and_then(|f| f.as_u64())).collect();
    let b: Vec<Option<u64>> = rows_b.iter().map(|r| field(r, "hash").and_then(|f| f.as_u64())).collect();
    let status = if !a.is_empty() && a == b { ObligationStatus::Closed } else { ObligationStatus::Violated };
    ObligationResult::new(
        "DVSM-6-kernel",
        "two real dumps from the same seed share an identical replay-hash sequence",
        status,
        format!("{} vs {} frames; hash sequences identical = {}", a.len(), b.len(), a == b),
        "CORRECTNESS or cross-precision parity — integrity ≠ truth; hash ≠ reality",
        "identical seed yielding divergent emitted hashes",
    )
}

/// Forbidden-coupling obligations a PUBLIC frame dump cannot support: `(id, needed-field, why)`. Neither `v`
/// nor `lambda_eff` is emitted, so both are always non-liftable from the public schemas. `undetected ≠ absent`.
pub const NON_LIFTABLE_NEEDS: &[(&str, &str, &str)] = &[
    ("DVSM-7 (Ω→V air-gap)", "v", "velocity V is not emitted in the public frame; the Ω→V air-gap needs it"),
    ("DVSM-4 (ν→λ air-gap)", "lambda_eff", "dissipation λ is not emitted in the public frame; the ν→λ air-gap needs it"),
];

/// The forbidden-coupling obligations the emitted fields cannot support, with the reason — `(id, why)`.
pub fn non_liftable(rows: &[Row]) -> Vec<(&'static str, &'static str)> {
    NON_LIFTABLE_NEEDS
        .iter()
        .filter(|(_id, need, _why)| !has_field(rows, need))
        .map(|(id, _need, why)| (*id, *why))
        .collect()
}

/// Lift every obligation the dump supports to a graded [`ObligationResult`], and return the non-liftable ones
/// with why. Mirrors the Python `lift()`: containment if `energy` present; replay-parity if `hash` present and
/// a second dump is supplied, else an UNDERDETERMINED no-hash obligation for a hashless schema.
pub fn lift(
    rows: &[Row],
    schema: &Schema,
    u_max: f64,
    rows_b: Option<&[Row]>,
) -> (Vec<ObligationResult>, Vec<(&'static str, &'static str)>) {
    let mut obs = Vec::new();
    if has_field(rows, "energy") {
        obs.push(containment(rows, u_max));
    }
    if has_field(rows, "hash") {
        if let Some(rb) = rows_b {
            obs.push(replay_parity(rows, rb));
        }
    } else if !rows.is_empty() {
        obs.push(no_hash_obligation(schema));
    }
    (obs, non_liftable(rows))
}

/// Streaming `lift` for a SINGLE dump — bounded memory (one row + a running max energy, independent of file
/// size). Produces the SAME obligations + non-liftable set as `lift(rows, schema, u_max, None)` would on the
/// fully-buffered rows (the obligation builders are shared, so the equivalence is by construction; it is also
/// asserted in `tests/gateway.rs`). `streaming ≡ whole-file`. (A two-dump `replay_parity` is intentionally not
/// offered here — it would need both hash sequences held in lockstep, breaking the O(record) bound.)
pub fn lift_streaming<R: Read>(
    reader: R,
    schema: &Schema,
    u_max: f64,
    header_lines: usize,
) -> std::io::Result<(Vec<ObligationResult>, Vec<(&'static str, &'static str)>, ParseReport)> {
    let mut max_energy: Option<f64> = None;
    let mut first_row: Option<Row> = None;
    let report = stream_frames(reader, schema, header_lines, |row| {
        if first_row.is_none() {
            first_row = Some(row.clone()); // hold exactly ONE row (O(record))
        }
        if let Some(v) = field(row, "energy").and_then(|f| f.as_f64()) {
            max_energy = Some(match max_energy {
                Some(m) => m.max(v),
                None => v,
            });
        }
    })?;

    let mut obs = Vec::new();
    let non_lift;
    match &first_row {
        Some(fr) => {
            let probe = std::slice::from_ref(fr); // 1-row slice ⇒ `has_field` / `non_liftable` see the schema
            if has_field(probe, "energy") {
                obs.push(containment_from(max_energy, report.n_records, u_max));
            }
            if !has_field(probe, "hash") {
                obs.push(no_hash_obligation(schema));
            }
            non_lift = non_liftable(probe);
        }
        None => {
            non_lift = non_liftable(&[]); // empty stream
        }
    }
    Ok((obs, non_lift, report))
}

