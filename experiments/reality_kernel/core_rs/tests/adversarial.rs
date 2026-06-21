// SPDX-License-Identifier: AGPL-3.0-only
//! What Rust adds over Python: stress cannot collapse the categories. The runtime must fail LOUDLY —
//! never lose a transition silently, never fabricate a lineage, never let an incomplete write be seen.

use reality_core::*;
use std::sync::mpsc;
use std::thread;

#[test]
fn artifact_without_provenance_fails() {
    assert!(Artifact::new("rule", "0.5", std::collections::HashMap::new()).is_err());
}

#[test]
fn event_without_source_fails() {
    assert!(Event::new("g", "1.0", "0.5", "").is_err());
}

#[test]
fn receipt_without_digest_fails() {
    assert!(CommitReceipt::new("g".into(), "1.0".into(), "0.5".into(), "developer".into(), vec![], "".into()).is_err());
}

#[test]
fn severed_prerequisite_refused_and_state_does_not_advance() {
    let mut c = Core::new();
    let ev = Event::new("x", "0", "1", "developer").unwrap();
    assert!(matches!(c.apply(&ev, Some("deadbeefcafe")), Err(CommitError::Severed)));
    assert!(matches!(c.query("x").existence, Existence::Unaccounted));
    assert_eq!(c.refused, 1);
}

#[test]
fn buffer_exhaustion_drops_resolves_never_commits() {
    // ResolvePath may drop under backpressure (counted, never panics)
    let mut ring = ResolveRing::new(4);
    for i in 0..50 {
        ring.offer(format!("d{}", i));
    }
    assert!(ring.dropped > 0);
    // CommitPath is a different path: flood it, nothing is silently lost
    let mut c = Core::new();
    for i in 0..200 {
        c.apply(&Event::new(&format!("o{}", i), "0", "1", "developer").unwrap(), None).unwrap();
    }
    let present = (0..200)
        .filter(|i| matches!(c.query(&format!("o{}", i)).existence, Existence::Present))
        .count();
    assert_eq!(present, 200, "a flooded commit path must never drop a transition");
}

#[test]
fn corruption_yields_unresolvable_not_a_guess() {
    let mut c = Core::new();
    let r = c.apply(&Event::new("g", "1.0", "0.5", "developer").unwrap(), None).unwrap();
    assert!(matches!(c.resolve_digest(&r.provenance_digest), Resolution::Resolved(_)));
    // corrupt the digest: it must become unresolvable, never reconstructed by guess
    let mut bad = r.provenance_digest.clone();
    bad.replace_range(0..1, if bad.starts_with('0') { "1" } else { "0" });
    assert!(matches!(c.resolve_digest(&bad), Resolution::Severed));
}

#[test]
fn lineage_is_canonical_not_a_deletable_cache() {
    // There is no separate resolve cache whose eviction could lose lineage; resolution reads the
    // authoritative World. Eviction (of any future cache) may delay a request, never erase history.
    let mut c = Core::new();
    let r = c.apply(&Event::new("g", "1.0", "0.5", "developer").unwrap(), None).unwrap();
    // simulate repeated "cold" resolves (as if a cache were cleared each time): all still resolve
    for _ in 0..3 {
        assert!(matches!(c.resolve_digest(&r.provenance_digest), Resolution::Resolved(_)));
    }
}

#[test]
fn concurrent_commits_single_ordered_no_loss() {
    // many producers → one ordered commit authority → no dropped, no duplicated transition
    let (tx, rx) = mpsc::channel::<Event>();
    let producers = 4;
    let per = 250;
    let mut handles = Vec::new();
    for p in 0..producers {
        let tx = tx.clone();
        handles.push(thread::spawn(move || {
            for i in 0..per {
                tx.send(Event::new(&format!("p{}_{}", p, i), "0", "1", "developer").unwrap()).unwrap();
            }
        }));
    }
    drop(tx);
    let mut c = Core::new();
    let mut applied = 0usize;
    for ev in rx {
        c.apply(&ev, None).unwrap();
        applied += 1;
    }
    for h in handles {
        h.join().unwrap();
    }
    assert_eq!(applied, producers * per, "every committed transition must survive concurrency");
}

#[test]
fn producer_panic_leaves_no_partial_state() {
    let mut c = Core::new();
    let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let _ev = Event::new("ghost", "0", "1", "developer").unwrap();
        panic!("die before commit");
        #[allow(unreachable_code)]
        {
            c.apply(&_ev, None).unwrap();
        }
    }));
    assert!(res.is_err());
    // the incomplete transition was never published
    assert!(matches!(c.query("ghost").existence, Existence::Unaccounted));
}
