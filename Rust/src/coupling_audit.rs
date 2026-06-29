// SPDX-License-Identifier: AGPL-3.0-only
//! The forbidden-coupling taxonomy — a Rust port of the decision layer in `DVSM/coupling_audit.py`, built on
//! top of the validated [`crate::residual_channel`] core. It asks whether a diagnostic channel X leaks
//! information into a future dynamics channel Y beyond the legitimate drivers Z, and stresses any residual
//! with a candidate confounder W:
//!
//!   I(X;Y_next | Z)  ~ null            ⇒  AIR_GAP_HELD
//!   I(X;Y_next | Z)  > null, stable/(Z,W) ⇒  OBSERVER_CONTAMINATION  (a real forbidden coupling)
//!   I(X;Y_next | Z)  > null, fragile/(Z,W) ⇒  CONFOUNDED_ARTIFACT     (a missing-confounder artifact)
//!
//! IDENTIFIABILITY BOUNDARY: if the diagnostic X is itself a near-deterministic FUNCTION of the conditioned
//! legit state Z, a positive CMI cannot be told apart from binning-resolution confounding. The firewall then
//! DECLINES to rule (UNIDENTIFIABLE) rather than emit a false contamination. `undetected ≠ absent`;
//! `detected-on-unidentifiable ≠ contamination`; `borrow-checker-clean ≠ air-gap-sound`.
//!
//! Continuous channels are quantile-binned (the same scheme as the Python `_binner`). The verdicts are
//! validated on planted, deterministic regimes in `tests/coupling.rs`, cross-checked against the Python
//! reference.

use crate::artifacts::{AnalysisResult, Finding, Limitation};
use crate::residual_channel::{audit, ChannelDecision, Sample};

const K: usize = 3; // bins per channel

/// Quantile binner: each channel → ~K equal-mass symbols. Faithful port of `_quantile_edges`/`_binner`.
pub struct Binner {
    edges: Vec<f64>,
}

impl Binner {
    pub fn new(values: &[f64], k: usize) -> Self {
        let mut xs = values.to_vec();
        xs.sort_by(|a, b| a.partial_cmp(b).expect("no NaN in telemetry channel"));
        let n = xs.len();
        let mut edges = Vec::new();
        if n > 0 {
            for q in 1..k {
                let idx = ((n * q) / k).min(n - 1); // = int(len*q/k) for positive ints
                edges.push(xs[idx]);
            }
        }
        Binner { edges }
    }

    pub fn bin(&self, v: f64) -> i64 {
        let mut lo = 0i64;
        for &e in &self.edges {
            if v <= e {
                return lo;
            }
            lo += 1;
        }
        lo
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CouplingVerdict {
    AirGapHeld,
    ObserverContamination,
    ConfoundedArtifact,
    SuspectUnstressed,
    Unidentifiable,
}

impl CouplingVerdict {
    pub fn as_str(&self) -> &'static str {
        match self {
            CouplingVerdict::AirGapHeld => "AIR_GAP_HELD",
            CouplingVerdict::ObserverContamination => "OBSERVER_CONTAMINATION",
            CouplingVerdict::ConfoundedArtifact => "CONFOUNDED_ARTIFACT",
            CouplingVerdict::SuspectUnstressed => "SUSPECT_UNSTRESSED",
            CouplingVerdict::Unidentifiable => "UNIDENTIFIABLE",
        }
    }
}

/// One coupling to audit. X = diagnostic (source); Y = future dynamics (target); Z = legitimate determinants
/// of Y (each a continuous series); W = candidate confounder(s) for the mis-specification stress.
#[derive(Debug, Clone)]
pub struct CouplingInput {
    pub name: String,
    pub manifest_rule: String,
    pub note: String,
    pub x: Vec<f64>,
    pub y: Vec<f64>,
    pub z_dims: Vec<Vec<f64>>,
    pub w_dims: Vec<Vec<f64>>,
    pub identifiable: bool,
    pub reps: usize,
    pub seed: u64,
}

#[derive(Debug, Clone)]
pub struct CouplingResult {
    pub name: String,
    pub manifest_rule: String,
    pub verdict: CouplingVerdict,
    pub mi: f64,
    pub cmi: f64,
    pub null_mean: f64,
    pub z_score: f64,
    pub identifiable: bool,
    pub note: String,
}

impl CouplingResult {
    pub fn as_analysis(&self) -> AnalysisResult {
        let mut lims = vec![
            Limitation::new(
                "forbidden-coupling",
                "a verdict is about THIS trace + the MODELED legit set Z; residual-CMI != channel until \
                 mis-specification-stable",
            ),
            Limitation::new(
                "forbidden-coupling",
                "AIR_GAP_HELD is absence-of-evidence at this window/conditioning, not proof of no coupling. \
                 proves-the-procedure != proves-the-phenomenon",
            ),
        ];
        if !self.identifiable {
            lims.push(Limitation::new(
                "identifiability",
                format!("{} undetected != absent", self.note),
            ));
        }
        AnalysisResult::new(
            "forbidden-coupling",
            vec![
                Finding::new("MANIFEST_RULE", "forbidden-coupling", self.manifest_rule.clone()),
                Finding::new(
                    "RESIDUAL_CMI",
                    "forbidden-coupling",
                    format!("I(X;Y_next|Z)={:.4} vs null {:.4} (z={:.1})", self.cmi, self.null_mean, self.z_score),
                ),
                Finding::new("VERDICT", "forbidden-coupling", self.verdict.as_str()),
            ],
            lims,
        )
        .expect("coupling as_analysis always satisfies the honesty contract")
    }
}

fn join_bins(binners: &[Binner], dims: &[Vec<f64>], i: usize) -> String {
    let parts: Vec<String> = binners.iter().zip(dims).map(|(b, d)| b.bin(d[i]).to_string()).collect();
    parts.join(",")
}

/// Audit one coupling: bin the channels, build (X, Y, Z) samples, define the (Z, W) re-conditioning, run the
/// residual-channel audit, and map its decision to a coupling verdict (declining as UNIDENTIFIABLE when the
/// coupling is not identifiable from telemetry).
pub fn audit_coupling(inp: &CouplingInput) -> CouplingResult {
    let n = inp.x.len();
    let bx = Binner::new(&inp.x, K);
    let by = Binner::new(&inp.y, K);
    let zbs: Vec<Binner> = inp.z_dims.iter().map(|d| Binner::new(d, K)).collect();
    let wbs: Vec<Binner> = inp.w_dims.iter().map(|d| Binner::new(d, K)).collect();

    let mut samples: Vec<Sample> = Vec::with_capacity(n);
    let mut zw: Vec<String> = Vec::with_capacity(n);
    for i in 0..n {
        let xb = bx.bin(inp.x[i]);
        let yb = by.bin(inp.y[i]);
        let zstr = join_bins(&zbs, &inp.z_dims, i);
        let wstr = join_bins(&wbs, &inp.w_dims, i);
        samples.push((xb, yb, zstr.clone()));
        zw.push(format!("{};{}", zstr, wstr)); // re-conditioning key = (Z, W)
    }

    let misspec: Box<dyn Fn(&[Sample]) -> Vec<Sample>> = {
        let zw = zw.clone();
        Box::new(move |s: &[Sample]| {
            s.iter().enumerate().map(|(i, (x, y, _z))| (*x, *y, zw[i].clone())).collect()
        })
    };

    let r = audit(&samples, inp.reps, inp.seed, 4.0, 0.005, std::slice::from_ref(&misspec));

    let verdict = if !inp.identifiable {
        CouplingVerdict::Unidentifiable
    } else {
        match r.decision {
            ChannelDecision::ConsistentWithNull => CouplingVerdict::AirGapHeld,
            ChannelDecision::ResidualMisspecStable => CouplingVerdict::ObserverContamination,
            ChannelDecision::ResidualMisspecFragile => CouplingVerdict::ConfoundedArtifact,
            ChannelDecision::ResidualDependence => CouplingVerdict::SuspectUnstressed,
        }
    };

    CouplingResult {
        name: inp.name.clone(),
        manifest_rule: inp.manifest_rule.clone(),
        verdict,
        mi: r.mi,
        cmi: r.cmi,
        null_mean: r.null_mean,
        z_score: r.z_score,
        identifiable: inp.identifiable,
        note: inp.note.clone(),
    }
}
