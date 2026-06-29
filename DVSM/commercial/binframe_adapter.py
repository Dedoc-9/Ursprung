# SPDX-License-Identifier: AGPL-3.0-only
# Commercial use beyond AGPL-3.0 requires a separate license — see LICENSE-COMMERCIAL.md.
"""
binframe_adapter.py — ingest REAL DVSM kernel telemetry dumps (the B3 "lift"): turn reference-relative
results into KERNEL-relative ones by reading the bytes the shipped Rust kernel actually emits.

The DVSM kernel emits ABI-stable `repr(C)` frames over its C ABI (`dvsm_step` fills a frame struct):
  • SCHEMA_TELEM  (dvsm_one_file.rs `BinaryFrame`): rich diagnostics — energy, novelty, stress, stiffness,
                  omega_norm, entropy, drift, resonance_peak, ghost, contained, emitted. NO replay hash.
  • SCHEMA_ABI    (dvsm_v20 `run_profile` record): id, energy, stress, entropy, ghost, contained, hash.
                  Carries the FNV-1a replay hash; fewer diagnostic channels.

This adapter (1) parses either layout with a record-size VALIDATION that flags a layout/endianness mismatch
instead of emitting silent garbage (`parsed ≠ correct`), (2) LIFTS the obligations the emitted telemetry can
actually support to kernel-relative graded `ObligationResult`s, and (3) **explicitly declares which obligations
cannot be lifted from frame dumps alone** — the forbidden-coupling air-gap checks (Ω→V, ν→λ) need the velocity
`V` and dissipation `λ`, which the public frame does NOT emit. `emitted-telemetry ≠ full-state`.

LAYOUT CAVEAT (honest): the default formats assume packed little-endian. `repr(C)` may insert trailing padding
on your target (e.g. sizeof rounded up to the u64 alignment). The adapter validates `len(body) % rec_size == 0`
and surfaces a `layout_mismatch` — verify the format against your build's `sizeof(BinaryFrame)` before trusting
parsed values. Customers can pass their own `BinFrameSchema(fmt=…, fields=…)`.
"""
from __future__ import annotations

import math
import os
import struct
import sys
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))
from invariant_ledger import ObligationResult, CLOSED, BOUNDED, VIOLATED, UNDERDETERMINED  # noqa: E402

GHOST_NAMES = ("Nominal", "Collapse", "Diffuse", "Echo", "Burst", "Trap", "Vacuum", "Denatured")
U_MAX_DEFAULT = 100.0


@dataclass(frozen=True)
class BinFrameSchema:
    """A `struct` format + field names for one on-disk frame record. `fmt` uses struct syntax; the leading
    '<' selects packed little-endian (verify against your build's actual sizeof — see LAYOUT CAVEAT)."""
    name: str
    fmt: str
    fields: Tuple[str, ...]

    @property
    def rec_size(self) -> int:
        return struct.calcsize(self.fmt)


# dvsm_one_file.rs BinaryFrame — rich diagnostics, packed little-endian assumption.
SCHEMA_TELEM = BinFrameSchema(
    "dvsm_one_file.BinaryFrame",
    "<QffffffffBBBB",
    ("frame", "energy", "novelty", "stress", "stiffness", "omega_norm", "entropy", "drift",
     "resonance_peak", "ghost", "contained", "emitted", "_pad"))

# dvsm_v20 run_profile record — carries the replay hash.
SCHEMA_ABI = BinFrameSchema(
    "dvsm_v20.run_profile",
    "<QdddBBQ",
    ("frame", "energy", "stress", "entropy", "ghost", "contained", "hash"))


@dataclass(frozen=True)
class ParseReport:
    schema: str
    n_records: int
    rec_size: int
    leftover_bytes: int
    layout_mismatch: bool
    nonfinite: int           # rows with a non-finite float (a parse/endianness ghost)

    def ok(self) -> bool:
        return not self.layout_mismatch and self.nonfinite == 0 and self.n_records > 0


def read_binframes(path: str, schema: BinFrameSchema = SCHEMA_TELEM,
                   header_lines: int = 0) -> Tuple[List[dict], ParseReport]:
    """Parse a binary dump into dict rows + a ParseReport. `header_lines` skips that many leading text lines
    (e.g. the run_profile header). A non-zero leftover or a non-finite float is surfaced, not hidden."""
    with open(path, "rb") as f:
        data = f.read()
    return parse_binframes(data, schema, header_lines)


def parse_binframes(data: bytes, schema: BinFrameSchema = SCHEMA_TELEM,
                    header_lines: int = 0) -> Tuple[List[dict], ParseReport]:
    off = 0
    for _ in range(header_lines):
        nl = data.find(b"\n", off)
        if nl < 0:
            break
        off = nl + 1
    body = data[off:]
    rec = schema.rec_size
    n, rem = divmod(len(body), rec)
    rows: List[dict] = []
    nonfinite = 0
    for i in range(n):
        vals = struct.unpack_from(schema.fmt, body, i * rec)
        row = {f: v for f, v in zip(schema.fields, vals) if not f.startswith("_")}
        if any(isinstance(v, float) and not math.isfinite(v) for v in row.values()):
            nonfinite += 1
        rows.append(row)
    report = ParseReport(schema.name, n, rec, rem, rem != 0, nonfinite)
    return rows, report


def write_binframes(path: str, rows: List[dict], schema: BinFrameSchema = SCHEMA_TELEM,
                    header: bytes = b"") -> None:
    """Pack rows back to the on-disk layout (for round-trip tests and fixtures)."""
    with open(path, "wb") as f:
        if header:
            f.write(header)
        for r in rows:
            f.write(struct.pack(schema.fmt, *[r.get(fld, 0) for fld in schema.fields]))


def with_next(rows: List[dict], fields: Tuple[str, ...]) -> List[dict]:
    """Add `<field>_next` columns (the next frame's value) so a per-frame dump can feed a diagnostic→dynamics
    probe. Drops the final row (no successor). The kernel emits per-frame; the audit needs t vs t+1."""
    out = []
    for a, b in zip(rows, rows[1:]):
        r = dict(a)
        for fld in fields:
            r[fld + "_next"] = b[fld]
        out.append(r)
    return out


def ghost_census(rows: List[dict]) -> Dict[str, int]:
    out = {g: 0 for g in GHOST_NAMES}
    for r in rows:
        g = int(r.get("ghost", 0))
        out[GHOST_NAMES[g] if 0 <= g < len(GHOST_NAMES) else "Nominal"] += 1
    return out


# ---- lift: obligations the emitted telemetry CAN support, kernel-relative -------------------------
def containment(rows: List[dict], u_max: float = U_MAX_DEFAULT, field: str = "energy") -> ObligationResult:
    mx = max((float(r[field]) for r in rows if field in r), default=float("nan"))
    status = BOUNDED if math.isfinite(mx) and mx < u_max else VIOLATED
    return ObligationResult(
        "DVSM-3-kernel", "‖Z‖ stays under U_MAX on the REAL emitted telemetry", status,
        f"max(energy)={mx:.3f} over {len(rows)} real frames (bound={u_max})",
        "boundedness for all inputs — only this dumped run; empirical-boundedness ≠ certified",
        "a real dump whose energy reaches U_MAX without GhostSnap recovery")


def replay_parity(rows_a: List[dict], rows_b: List[dict], field: str = "hash") -> ObligationResult:
    a = [r.get(field) for r in rows_a]
    b = [r.get(field) for r in rows_b]
    status = CLOSED if a and a == b else VIOLATED
    return ObligationResult(
        "DVSM-6-kernel", "two real dumps from the same seed share an identical replay-hash sequence", status,
        f"{len(a)} vs {len(b)} frames; hash sequences identical = {a == b}",
        "CORRECTNESS or cross-precision parity — integrity ≠ truth; hash ≠ reality",
        "identical seed yielding divergent emitted hashes")


# obligations that CANNOT be lifted from a public frame dump (and why) — the honest B3 boundary
_NEEDS = {
    "DVSM-7 (Ω→V air-gap)": ("v", "velocity V is not emitted in the public frame; the Ω→V air-gap needs it"),
    "DVSM-4 (ν→λ air-gap)": ("lambda_eff", "dissipation λ is not emitted in the public frame; the ν→λ air-gap needs it"),
}


def non_liftable(rows: List[dict]) -> List[Tuple[str, str]]:
    """List forbidden-coupling obligations that the emitted fields cannot support, with the reason. These
    require richer instrumentation (a custom telemetry build), not a verdict from the public frame."""
    have = set(rows[0].keys()) if rows else set()
    return [(oid, reason) for oid, (need, reason) in _NEEDS.items() if need not in have]


def lift(rows: List[dict], schema: BinFrameSchema, *, u_max: float = U_MAX_DEFAULT,
         rows_b: Optional[List[dict]] = None) -> Tuple[List[ObligationResult], List[Tuple[str, str]]]:
    """Lift every obligation the dump supports to kernel-relative, and return the non-liftable ones with why."""
    obs: List[ObligationResult] = []
    if rows and "energy" in rows[0]:
        obs.append(containment(rows, u_max))
    if rows and "hash" in rows[0] and rows_b is not None:
        obs.append(replay_parity(rows, rows_b))
    elif rows and "hash" not in rows[0]:
        obs.append(ObligationResult(
            "DVSM-6-kernel", "replay-hash parity on the real dump", UNDERDETERMINED,
            f"the {schema.name} frame carries no hash field — cannot check replay parity from this schema",
            "anything about reproducibility from a hashless dump",
            "switch to the ABI/run_profile dump (carries the FNV-1a hash)"))
    return obs, non_liftable(rows)


def _safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def main():
    print("binframe_adapter.py — real DVSM BinaryFrame ingest (the B3 lift)\n")
    # synthesize a real-format dump from the reference (we cannot run the Rust kernel here)
    from dvsm_reference import gen_clean
    trace = gen_clean(3000, seed=1)
    abi_rows = [{"frame": r.t, "energy": r.energy, "stress": r.stress, "entropy": r.entropy,
                 "ghost": GHOST_NAMES.index(r.ghost) if r.ghost in GHOST_NAMES else 0,
                 "contained": r.contained, "hash": r.hash} for r in trace]
    path = os.path.join(tempfile.gettempdir(), "_dvsm_demo_abi.bin")
    write_binframes(path, abi_rows, SCHEMA_ABI, header=b"DVSM-V20 demo R=4\n")
    rows, report = read_binframes(path, SCHEMA_ABI, header_lines=1)
    print(f"  parsed {report.n_records} ABI frames (rec={report.rec_size}B) layout_ok={report.ok()}")
    obs, notliftable = lift(rows, SCHEMA_ABI, rows_b=rows)   # rows_b=rows ⇒ trivially-identical replay
    for o in obs:
        print(f"    [{o.status:9s}] {o.id}: {o.witness}")
    print("  NOT liftable from this dump:")
    for oid, why in notliftable:
        print(f"    - {oid}: {why}")
    print(f"  ghost census: {ghost_census(rows)}")
    _safe_remove(path)
    print("\n  emitted-telemetry ≠ full-state; parsed ≠ correct; integrity ≠ truth.")


if __name__ == "__main__":
    main()
