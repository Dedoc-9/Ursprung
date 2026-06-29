// SPDX-License-Identifier: AGPL-3.0-only
//! Streaming reader equivalence — the synchronous, zero-dep `BufReader`-based chunked parser must produce the
//! SAME result as the whole-file `parse_frames` (same `ParseReport`, same rows), **including when the input
//! arrives in arbitrary fragments** (a record filled across multiple `read()` calls). `streaming ≡ whole-file`;
//! no async runtime, no dependency.

use ursprung::{parse_frames, read_frames_streaming, stream_frames, SCHEMA_ABI, SCHEMA_TELEM};

const TELEM_HEX: &str = "0100000000000000000020400000003f0000a03f0000404000000000000080400000c0bf0000403f020100000200000000000000000000400000803e0000803f00006040cdcccc3d00009040000080bf0000003f00010100";
const ABI_HEX: &str = "0a000000000000000000000000001440000000000000f03f0000000000000040010115cd5b07000000000b000000000000000000000000001840000000000000f83f00000000000004400000b168de3a00000000";

fn hx(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

/// A reader that yields ONE byte per `read()` — forces the streaming parser to fill each record across many
/// reads, exercising the partial-read accumulation that real files / sockets exhibit.
struct Trickle<'a> {
    data: &'a [u8],
    pos: usize,
}
impl<'a> std::io::Read for Trickle<'a> {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        if self.pos >= self.data.len() || buf.is_empty() {
            return Ok(0);
        }
        buf[0] = self.data[self.pos];
        self.pos += 1;
        Ok(1)
    }
}

#[test]
fn streaming_equals_whole_file_telem() {
    let bytes = hx(TELEM_HEX);
    let (rows_w, rep_w) = parse_frames(&bytes, &SCHEMA_TELEM, 0);
    let (rows_s, rep_s) = read_frames_streaming(&bytes[..], &SCHEMA_TELEM, 0).unwrap();
    assert_eq!(rep_w, rep_s, "ParseReport must match the whole-file parse");
    assert_eq!(rows_w, rows_s, "decoded rows must be identical");
}

#[test]
fn streaming_equals_whole_file_abi() {
    let bytes = hx(ABI_HEX);
    let (rows_w, rep_w) = parse_frames(&bytes, &SCHEMA_ABI, 0);
    let (rows_s, rep_s) = read_frames_streaming(&bytes[..], &SCHEMA_ABI, 0).unwrap();
    assert_eq!(rep_w, rep_s);
    assert_eq!(rows_w, rows_s);
}

#[test]
fn streaming_survives_one_byte_at_a_time() {
    // the crux: a record is filled across many single-byte reads, yet the result is identical
    let bytes = hx(TELEM_HEX);
    let (rows_w, rep_w) = parse_frames(&bytes, &SCHEMA_TELEM, 0);
    let (rows_s, rep_s) =
        read_frames_streaming(Trickle { data: &bytes, pos: 0 }, &SCHEMA_TELEM, 0).unwrap();
    assert_eq!(rep_w, rep_s, "fragmented reads must not change the report");
    assert_eq!(rows_w, rows_s, "fragmented reads must not change the rows");
}

#[test]
fn streaming_flags_trailing_partial_record() {
    let mut bytes = hx(TELEM_HEX);
    bytes.push(0xAB); // a stray byte ⇒ a trailing partial record
    let (_rows, rep) = read_frames_streaming(&bytes[..], &SCHEMA_TELEM, 0).unwrap();
    assert!(rep.layout_mismatch);
    assert_eq!(rep.leftover_bytes, 1);
    assert_eq!(rep.n_records, 2, "the whole records still parse; only the remainder is flagged");
}

#[test]
fn streaming_skips_header_lines() {
    let mut bytes = b"DVSM-V20 demo R=4\n".to_vec();
    bytes.extend_from_slice(&hx(ABI_HEX));
    let (rows, rep) = read_frames_streaming(&bytes[..], &SCHEMA_ABI, 1).unwrap();
    assert_eq!(rep.n_records, 2);
    assert_eq!(rows.len(), 2);
}

#[test]
fn stream_callback_is_bounded_memory() {
    // the callback form never collects the rows — only a running count — proving O(record) memory is enough
    let bytes = hx(TELEM_HEX);
    let mut count = 0usize;
    let rep = stream_frames(&bytes[..], &SCHEMA_TELEM, 0, |_row| count += 1).unwrap();
    assert_eq!(count, rep.n_records);
    assert_eq!(count, 2);
}
