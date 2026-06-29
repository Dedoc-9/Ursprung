// SPDX-License-Identifier: AGPL-3.0-only
//! The forbidden-coupling taxonomy separates the four regimes and declines on the unidentifiable one.
//! The deterministic generators below were validated against the Python reference (`DVSM/coupling_audit.py`
//! + `weltwerk/verify/residual_channel.py`) before being mirrored here: the Python `audit` produced exactly
//! AIR_GAP_HELD / OBSERVER_CONTAMINATION / CONFOUNDED_ARTIFACT / UNIDENTIFIABLE for these same constructions.
//! Because the estimators are differentially value-validated and these regimes sit far from threshold, the
//! Rust decisions carry over. `decisions match, floats need not`; `borrow-checker-clean != air-gap-sound`.

use ursprung::{audit_coupling, default_orchestrator, CouplingInput, CouplingVerdict, Request};

const N: usize = 3645; // 5 * 729 → the //1.. //243 mod-3 digits stay balanced & independent
const REPS: usize = 60;
const SEED: u64 = 0;

fn jit(i: usize) -> f64 {
    // distinct, monotonic, tiny (<<1): spreads values for quantile binning WITHOUT synchronized edge ties.
    // A repeating jitter (e.g. (i%7)/10) puts many samples at the exact bin edge and misbins them together,
    // leaving a spurious residual that survives conditioning — that flipped the artifact verdict. With a
    // distinct jitter at most ~1 sample sits on an edge, so the confounded artifact dissolves cleanly
    // (misspec CMI ~0.0006 << abs_floor 0.005 ⇒ FRAGILE, RNG-independently). Validated in Python first.
    i as f64 * 1e-7
}

/// Build (x, y, z_dims, w_dims) for a regime; cats in {0,1,2}, +jitter to spread for quantile binning.
fn gens(kind: &str) -> (Vec<f64>, Vec<f64>, Vec<Vec<f64>>, Vec<Vec<f64>>) {
    let (mut x, mut y, mut z, mut w) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for i in 0..N {
        let g0 = (i % 3) as i64;
        let g1 = ((i / 3) % 3) as i64;
        let g2 = ((i / 9) % 3) as i64;
        let g3 = ((i / 27) % 3) as i64;
        let (xc, yc, zc, wc) = match kind {
            "airgap" => ((g0 + g1) % 3, (g0 + g2) % 3, g0, g3), // x,y independent given z
            "contam" => {
                let xc = (g0 + g1) % 3;
                (xc, xc, g0, g3) // y = x beyond z, irrelevant w ⇒ stable
            }
            "artifact" => {
                let ax = ((i / 81) % 3) as i64;
                let ay = ((i / 243) % 3) as i64;
                // x,y = noisy copies of the confounder w=g3 with INDEPENDENT noise ⇒ dissolves under (z,w)
                let xc = if ax != 0 { g3 } else { (g3 + 1) % 3 };
                let yc = if ay != 0 { g3 } else { (g3 + 2) % 3 };
                (xc, yc, g0, g3)
            }
            _ => unreachable!(),
        };
        x.push(xc as f64 + jit(i));
        y.push(yc as f64 + jit(i));
        z.push(zc as f64 + jit(i));
        w.push(wc as f64 + jit(i));
    }
    (x, y, vec![z], vec![w])
}

fn input(kind: &str, identifiable: bool) -> CouplingInput {
    let (x, y, z_dims, w_dims) = gens(kind);
    CouplingInput {
        name: kind.to_string(),
        manifest_rule: "test coupling".to_string(),
        note: if identifiable { String::new() } else { "diagnostic is a near-function of Z.".to_string() },
        x,
        y,
        z_dims,
        w_dims,
        identifiable,
        reps: REPS,
        seed: SEED,
    }
}

#[test]
fn airgap_reads_air_gap_held() {
    let r = audit_coupling(&input("airgap", true));
    assert_eq!(r.verdict, CouplingVerdict::AirGapHeld, "cmi={}", r.cmi);
}

#[test]
fn contamination_is_detected_and_stable() {
    let r = audit_coupling(&input("contam", true));
    assert_eq!(r.verdict, CouplingVerdict::ObserverContamination, "cmi={}", r.cmi);
}

#[test]
fn confounded_artifact_dissolves_under_w() {
    let r = audit_coupling(&input("artifact", true));
    assert_eq!(r.verdict, CouplingVerdict::ConfoundedArtifact, "cmi={}", r.cmi);
}

#[test]
fn unidentifiable_declines_even_when_planted() {
    // same data as contamination, but flagged unidentifiable ⇒ the firewall declines to rule (no false positive)
    let r = audit_coupling(&input("contam", false));
    assert_eq!(r.verdict, CouplingVerdict::Unidentifiable);
    // and the analysis carries the identifiability limitation
    let a = r.as_analysis();
    assert!(a.limitations().iter().any(|l| l.scope == "identifiability"));
}

#[test]
fn coupling_routes_through_orchestrator_honestly() {
    let o = default_orchestrator();
    assert!(o.tool_names().iter().any(|n| n == "coupling_audit"), "tool registered");
    let req = Request::Coupling(Box::new(input("contam", true)));
    let a = o.analyze("coupling_audit", &req).expect("registered tool");
    // honest by construction (scope + >=1 limitation), and the verdict propagates as a finding
    assert_eq!(a.scope(), "forbidden-coupling");
    assert!(!a.limitations().is_empty());
    assert!(a
        .findings()
        .iter()
        .any(|f| f.kind == "VERDICT" && f.detail == "OBSERVER_CONTAMINATION"));
}
