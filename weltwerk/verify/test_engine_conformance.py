# SPDX-License-Identifier: AGPL-3.0-only
"""
test_engine_conformance.py — Phase A.2: the engine-conformance gate as a test.

Runs `conformance.check_conformance` over every available engine (the explicit reference always; the
symbolic engine too, iff z3 is installed) and asserts each satisfies the universal contract. This is the
gate every future backend (abstract interpreter, SAT backend, repair engine) must clear before it is a
supported engine. The explicit engine is pure-stdlib, so this suite never fully skips.

Run:  python3 test_engine_conformance.py
"""
from __future__ import annotations

from conformance import check_conformance, engines, build_model, VerificationOptions, SMALL


def main():
    print("test_engine_conformance — universal engine contract gate (validity-not-outcome)\n")
    engs = engines()
    total_ok = 0
    total = 0
    failures = []
    for engine in engs:
        label = engine.verify(build_model(SMALL), VerificationOptions(depth_bound=1)).engine
        results = check_conformance(engine)
        print(f"  engine: {label}")
        for name, ok, detail in results:
            print(f"    [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
            total += 1
            total_ok += int(ok)
            if not ok:
                failures.append(f"{label}:{name}")
        print()
    note = "" if len(engs) > 1 else "  (symbolic engine not gated — z3 not installed; explicit gated)\n"
    if note:
        print(note)
    print(f"  {total_ok}/{total} conformance checks across {len(engs)} engine(s). "
          f"Sound iff all pass: every engine returns the contract, emits a replayable Trace on violation, "
          f"uses\n  only the three statuses, is deterministic, is labelled, and is frontier-consistent. "
          f"A new engine must pass this gate. engine ≠ semantics.")
    assert not failures, f"conformance failures: {failures}"


if __name__ == "__main__":
    main()
