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
//! ## Faithful to the reference — what this DOES NOT do
//! - **No `lift()`.** The obligation-lifting half of the Python adapter depends on `invariant_ledger`
//!   (`ObligationResult`), which is not yet in Rust. That is Sub-Slice 1B. This slice is parse + report only.
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
        let mut off = i * rec;
        let mut row: Row = Vec::with_capacity(schema.fields.len());
        let mut row_nonfinite = false;
        for &(name, ft) in schema.fields {
            match ft {
                FieldType::U64 => {
                    let v = u64::from_le_bytes(body[off..off + 8].try_into().unwrap());
                    off += 8;
                    row.push((name, Field::U64(v)));
                }
                FieldType::F32 => {
                    let v = f32::from_le_bytes(body[off..off + 4].try_into().unwrap());
                    off += 4;
                    if !v.is_finite() {
                        row_nonfinite = true;
                    }
                    row.push((name, Field::F32(v)));
                }
                FieldType::F64 => {
                    let v = f64::from_le_bytes(body[off..off + 8].try_into().unwrap());
                    off += 8;
                    if !v.is_finite() {
                        row_nonfinite = true;
                    }
                    row.push((name, Field::F64(v)));
                }
                FieldType::U8 => {
                    row.push((name, Field::U8(body[off])));
                    off += 1;
                }
                FieldType::Pad => {
                    off += 1; // consumed, dropped
                }
            }
        }
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
