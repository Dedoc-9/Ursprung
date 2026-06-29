// SPDX-License-Identifier: AGPL-3.0-only
//! Differential test for the BinaryFrame parser (Sub-Slice 1A) vs the Python reference
//! (`DVSM/commercial/binframe_adapter.py`). The two hex fixtures below were packed by Python's `struct` with
//! the exact reference formats (`<QffffffffBBBB` / `<QdddBBQ`); this test parses the identical bytes in Rust
//! and asserts the same record count, anomaly flags, and decoded values. `parsed ≠ correct`.

use ursprung::binframe_adapter::{field, parse_frames, SCHEMA_ABI, SCHEMA_TELEM};

// packed by /tmp/packbf.py (Python struct), little-endian:
//   TELEM rows: (1, 2.5,0.5,1.25,3.0,0.0,4.0,-1.5,0.75, ghost=2,contained=1,emitted=0,_pad=0)
//               (2, 2.0,0.25,1.0,3.5,0.1,4.5,-1.0,0.5,  ghost=0,contained=1,emitted=1,_pad=0)
const TELEM_HEX: &str = "0100000000000000000020400000003f0000a03f0000404000000000000080400000c0bf0000403f020100000200000000000000000000400000803e0000803f00006040cdcccc3d00009040000080bf0000003f00010100";
//   ABI rows:   (10, 5.0,1.0,2.0, ghost=1,contained=1, hash=123456789)
//               (11, 6.0,1.5,2.5, ghost=0,contained=0, hash=987654321)
const ABI_HEX: &str = "0a000000000000000000000000001440000000000000f03f0000000000000040010115cd5b07000000000b000000000000000000000000001840000000000000f83f00000000000004400000b168de3a00000000";

fn hx(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

#[test]
fn telem_fixture_matches_python() {
    let bytes = hx(TELEM_HEX);
    let (rows, rep) = parse_frames(&bytes, &SCHEMA_TELEM, 0);
    assert_eq!(rep.rec_size, 44, "TELEM record is 44 bytes");
    assert_eq!(rep.n_records, 2);
    assert_eq!(rep.leftover_bytes, 0);
    assert!(!rep.layout_mismatch);
    assert_eq!(rep.nonfinite, 0);
    assert!(rep.ok());
    // decoded values match the Python pack
    assert_eq!(field(&rows[0], "energy").unwrap().as_f64(), Some(2.5));
    assert_eq!(field(&rows[0], "ghost").unwrap().as_u8(), Some(2));
    assert_eq!(field(&rows[1], "emitted").unwrap().as_u8(), Some(1));
    // the `_pad` byte is consumed but dropped from the row (mirrors the Python `_`-prefix skip)
    assert!(field(&rows[0], "_pad").is_none());
}

#[test]
fn abi_fixture_matches_python() {
    let bytes = hx(ABI_HEX);
    let (rows, rep) = parse_frames(&bytes, &SCHEMA_ABI, 0);
    assert_eq!(rep.rec_size, 42, "ABI record is 42 bytes");
    assert_eq!(rep.n_records, 2);
    assert!(rep.ok());
    assert_eq!(field(&rows[0], "hash").unwrap().as_u64(), Some(123456789));
    assert_eq!(field(&rows[1], "entropy").unwrap().as_f64(), Some(2.5));
}

#[test]
fn trailing_byte_flags_layout_mismatch() {
    let mut bytes = hx(TELEM_HEX);
    bytes.push(0xAB); // one stray byte ⇒ stream no longer divides the record size
    let (_rows, rep) = parse_frames(&bytes, &SCHEMA_TELEM, 0);
    assert!(rep.layout_mismatch, "a non-dividing stream is flagged, not silently truncated");
    assert_eq!(rep.leftover_bytes, 1);
    assert_eq!(rep.n_records, 2, "the whole records still parse; only the remainder is flagged");
    assert!(!rep.ok());
}

#[test]
fn nonfinite_float_is_flagged() {
    let mut bytes = hx(TELEM_HEX);
    // overwrite row 0's `energy` (offset 8..12, the first f32 after the u64 frame) with NaN
    bytes[8..12].copy_from_slice(&f32::NAN.to_le_bytes());
    let (_rows, rep) = parse_frames(&bytes, &SCHEMA_TELEM, 0);
    assert_eq!(rep.nonfinite, 1, "a NaN in a float field is surfaced before it pollutes downstream loops");
    assert!(!rep.ok());
}

#[test]
fn header_lines_are_skipped() {
    // the run_profile dump carries a leading text header; the parser skips N newline-terminated lines first
    let mut bytes = b"DVSM-V20 demo R=4\n".to_vec();
    bytes.extend_from_slice(&hx(ABI_HEX));
    let (rows, rep) = parse_frames(&bytes, &SCHEMA_ABI, 1);
    assert_eq!(rep.n_records, 2, "header line skipped, both records parsed");
    assert_eq!(field(&rows[0], "hash").unwrap().as_u64(), Some(123456789));
}
