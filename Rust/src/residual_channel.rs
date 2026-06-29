// SPDX-License-Identifier: AGPL-3.0-only
//! The confounder-conditioned mutual-information diagnostic: is there dependence between X and Y that the
//! modeled conditioning set Z does NOT explain?
//!
//!   I(X;Y)     > 0  ← may be pure confounding by Z. NOT evidence of a channel.
//!   I(X;Y | Z) > 0  ← residual dependence beyond Z — a candidate channel.
//!
//! The estimator's finite-sample bias is positive, so a raw `I(X;Y|Z) > 0` proves nothing; it is compared to
//! a WITHIN-Z SHUFFLE NULL (permute Y inside each Z stratum). A signal exceeding the null is *residual
//! dependence*; whether it is a genuine channel or merely Z mis-specification is decided by re-conditioning
//! (each re-conditioning gets its OWN null — finer strata carry more bias). Everything is deterministic given
//! the seed (a per-stratum-seeded LCG), so results reproduce. `residual-CMI ≠ channel`;
//! `proves-the-procedure ≠ proves-the-phenomenon`.

use std::collections::{BTreeMap, HashMap};

use crate::artifacts::{AnalysisResult, Finding, Limitation};
use crate::epistemic_types::Grounding;

/// One observation: discretized `(x, y, z)` where `z` is the conditioning symbol (a `String`, so a composite
/// `(z, w)` re-conditioning is just a different string).
pub type Sample = (i64, i64, String);

// ---- deterministic RNG (LCG) ---------------------------------------------------------------------
struct Lcg {
    state: u64,
}

impl Lcg {
    fn new(seed: u64) -> Self {
        // scramble the seed so small/adjacent seeds diverge immediately
        Self { state: seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407) }
    }
    fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        self.state
    }
    fn below(&mut self, n: usize) -> usize {
        debug_assert!(n > 0);
        (self.next_u64() >> 33) as usize % n
    }
    fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / ((1u64 << 53) as f64)
    }
    fn shuffle<T>(&mut self, v: &mut [T]) {
        for i in (1..v.len()).rev() {
            let j = self.below(i + 1);
            v.swap(i, j);
        }
    }
}

fn fnv1a(s: &str) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in s.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

// ---- discrete estimators (exact from counts; bits) ----------------------------------------------
pub fn mutual_information(samples: &[(i64, i64)]) -> f64 {
    let n = samples.len() as f64;
    if n == 0.0 {
        return 0.0;
    }
    let mut cx: HashMap<i64, f64> = HashMap::new();
    let mut cy: HashMap<i64, f64> = HashMap::new();
    // BTreeMap (not HashMap) for the map we SUM over: HashMap's randomized iteration order makes float
    // addition non-associative across calls (a last-ULP nondeterminism ghost). Sorted iteration ⇒ bit-stable.
    let mut cxy: BTreeMap<(i64, i64), f64> = BTreeMap::new();
    for &(x, y) in samples {
        *cx.entry(x).or_insert(0.0) += 1.0;
        *cy.entry(y).or_insert(0.0) += 1.0;
        *cxy.entry((x, y)).or_insert(0.0) += 1.0;
    }
    let mut i = 0.0;
    for (&(x, y), &c) in &cxy {
        let pxy = c / n;
        let px = cx[&x] / n;
        let py = cy[&y] / n;
        i += pxy * (pxy / (px * py)).log2();
    }
    i
}

/// I(X;Y | Z) from a slice of `(x, y, z)`.
pub fn conditional_mutual_information(samples: &[Sample]) -> f64 {
    let n = samples.len() as f64;
    if n == 0.0 {
        return 0.0;
    }
    let mut cz: HashMap<&str, f64> = HashMap::new();
    let mut cxz: HashMap<(i64, &str), f64> = HashMap::new();
    let mut cyz: HashMap<(i64, &str), f64> = HashMap::new();
    // BTreeMap for the summed-over map ⇒ deterministic float accumulation order (see mutual_information).
    let mut cxyz: BTreeMap<(i64, i64, &str), f64> = BTreeMap::new();
    for (x, y, z) in samples {
        let z = z.as_str();
        *cz.entry(z).or_insert(0.0) += 1.0;
        *cxz.entry((*x, z)).or_insert(0.0) += 1.0;
        *cyz.entry((*y, z)).or_insert(0.0) += 1.0;
        *cxyz.entry((*x, *y, z)).or_insert(0.0) += 1.0;
    }
    let mut i = 0.0;
    for (&(x, y, z), &c) in &cxyz {
        let num = cz[z] * c;
        let den = cxz[&(x, z)] * cyz[&(y, z)];
        i += (c / n) * (num / den).log2();
    }
    i
}

/// Permute Y WITHIN each Z stratum (destroys conditional X–Y dependence, preserves the estimator bias), then
/// re-measure CMI. Each stratum is shuffled with its OWN seed (derived from the stratum key), so the result
/// is independent of hash-map iteration order — fully deterministic.
pub fn shuffle_null(samples: &[Sample], seed: u64) -> f64 {
    let mut by_z: HashMap<&str, Vec<usize>> = HashMap::new();
    for (idx, (_x, _y, z)) in samples.iter().enumerate() {
        by_z.entry(z.as_str()).or_default().push(idx);
    }
    let mut out: Vec<Sample> = samples.to_vec();
    for (z, idxs) in &by_z {
        let mut rng = Lcg::new(seed ^ fnv1a(z));
        let mut ys: Vec<i64> = idxs.iter().map(|&i| samples[i].1).collect();
        rng.shuffle(&mut ys);
        for (k, &i) in idxs.iter().enumerate() {
            out[i].1 = ys[k];
        }
    }
    conditional_mutual_information(&out)
}

pub fn shuffle_null_dist(samples: &[Sample], reps: usize, seed: u64) -> Vec<f64> {
    (0..reps.max(1)).map(|i| shuffle_null(samples, seed.wrapping_add(i as u64))).collect()
}

// ---- the audit -----------------------------------------------------------------------------------
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChannelDecision {
    ConsistentWithNull,
    ResidualDependence,
    ResidualMisspecStable,
    ResidualMisspecFragile,
}

impl ChannelDecision {
    pub fn as_str(&self) -> &'static str {
        match self {
            ChannelDecision::ConsistentWithNull => "CONSISTENT_WITH_NULL",
            ChannelDecision::ResidualDependence => "RESIDUAL_DEPENDENCE",
            ChannelDecision::ResidualMisspecStable => "RESIDUAL_MISSPEC_STABLE",
            ChannelDecision::ResidualMisspecFragile => "RESIDUAL_MISSPEC_FRAGILE",
        }
    }
}

#[derive(Debug, Clone)]
pub struct ResidualChannelResult {
    pub n: usize,
    pub mi: f64,
    pub cmi: f64,
    pub null_mean: f64,
    pub null_std: f64,
    pub null_max: f64,
    pub z_score: f64,
    pub decision: ChannelDecision,
    pub misspec_cmis: Vec<f64>,
}

impl ResidualChannelResult {
    pub fn as_analysis(&self) -> AnalysisResult {
        AnalysisResult::new(
            "conditional-dependence",
            vec![
                Finding::new(
                    "MARGINAL_DEPENDENCE",
                    "conditional-dependence",
                    format!("I(X;Y)={:.4} bits (may be confounded by Z)", self.mi),
                ),
                Finding::new(
                    "RESIDUAL_DEPENDENCE",
                    "conditional-dependence",
                    format!(
                        "I(X;Y|Z)={:.4} vs null {:.4}+/-{:.4} (z={:.1})",
                        self.cmi, self.null_mean, self.null_std, self.z_score
                    ),
                ),
                Finding::new("DECISION", "conditional-dependence", self.decision.as_str()),
            ],
            vec![
                Limitation::new(
                    "conditional-dependence",
                    "Z is the MODELED conditioning set; a positive I(X;Y|Z) is residual dependence, not proof \
                     of a channel. residual-CMI != channel",
                ),
                Limitation::new(
                    "method",
                    "absence is about the modeled system + sample size, not a general guarantee. \
                     proves-the-procedure != proves-the-phenomenon",
                ),
            ],
        )
        .expect("residual-channel as_analysis always satisfies the honesty contract")
    }
}

type MisspecFn = Box<dyn Fn(&[Sample]) -> Vec<Sample>>;

/// Decide whether X and Y carry dependence beyond Z. Each `misspec_fns` entry maps the samples to a
/// RE-CONDITIONED sample list (a different/coarser Z); a true channel stays above its own null under all.
pub fn audit(
    samples: &[Sample],
    reps: usize,
    seed: u64,
    k_sigma: f64,
    abs_floor: f64,
    misspec_fns: &[MisspecFn],
) -> ResidualChannelResult {
    let xy: Vec<(i64, i64)> = samples.iter().map(|s| (s.0, s.1)).collect();
    let mi = mutual_information(&xy);
    let cmi = conditional_mutual_information(samples);
    let nd = shuffle_null_dist(samples, reps, seed);
    let len = nd.len() as f64;
    let mean = nd.iter().sum::<f64>() / len;
    let var = nd.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / len;
    let std = var.sqrt();
    let nmax = nd.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let z = if std > 0.0 {
        (cmi - mean) / std
    } else if cmi > mean + abs_floor {
        f64::INFINITY
    } else {
        0.0
    };
    let threshold = (mean + k_sigma * std).max(mean + abs_floor).max(nmax);
    let detected = cmi > threshold;
    let mut decision =
        if detected { ChannelDecision::ResidualDependence } else { ChannelDecision::ConsistentWithNull };
    let mut misspec_cmis = Vec::new();
    if detected && !misspec_fns.is_empty() {
        let mut stable = true;
        for f in misspec_fns {
            let ms = f(samples);
            let c = conditional_mutual_information(&ms);
            // each re-conditioning has its OWN finite-sample bias floor ⇒ its OWN null. `bias != signal`.
            let mnull = shuffle_null_dist(&ms, (reps / 2).max(20), seed);
            let mlen = mnull.len() as f64;
            let mmean = mnull.iter().sum::<f64>() / mlen;
            let mstd = (mnull.iter().map(|v| (v - mmean).powi(2)).sum::<f64>() / mlen).sqrt();
            misspec_cmis.push(c);
            if !(c > (mmean + k_sigma * mstd).max(mmean + abs_floor)) {
                stable = false;
            }
        }
        decision = if stable {
            ChannelDecision::ResidualMisspecStable
        } else {
            ChannelDecision::ResidualMisspecFragile
        };
    }
    ResidualChannelResult {
        n: samples.len(),
        mi,
        cmi,
        null_mean: mean,
        null_std: std,
        null_max: nmax,
        z_score: z,
        decision,
        misspec_cmis,
    }
}

/// Convenience: the standard audit (reps=200, seed=0, k_sigma=4.0, abs_floor=0.005, no mis-spec stress).
pub fn audit_default(samples: &[Sample]) -> ResidualChannelResult {
    audit(samples, 200, 0, 4.0, 0.005, &[])
}

// ---- groundings (for the action chokepoint) ------------------------------------------------------
/// Grounded iff the audit found a mis-specification-stable channel.
pub struct ChannelEstablished {
    pub decision: ChannelDecision,
}
impl Grounding for ChannelEstablished {
    fn is_grounded(&self) -> bool {
        self.decision == ChannelDecision::ResidualMisspecStable
    }
    fn label(&self) -> String {
        format!("channel-decision={}", self.decision.as_str())
    }
}

/// Grounded iff the audit is CONSISTENT_WITH_NULL (no residual dependence beyond Z).
pub struct NoHiddenChannel {
    pub decision: ChannelDecision,
}
impl Grounding for NoHiddenChannel {
    fn is_grounded(&self) -> bool {
        self.decision == ChannelDecision::ConsistentWithNull
    }
    fn label(&self) -> String {
        format!("channel-decision={}", self.decision.as_str())
    }
}

// ---- self-contained demo generators (generic; not domain-specific) -------------------------------
fn noisy(v: i64, k: i64, rng: &mut Lcg) -> i64 {
    if rng.next_f64() < 0.35 {
        rng.below(k as usize) as i64
    } else {
        v
    }
}

/// X, Y both driven by a shared confounder Z; given Z they are INDEPENDENT (no channel).
pub fn demo_gen_null(n: usize, k: i64, seed: u64) -> Vec<Sample> {
    let mut rng = Lcg::new(seed);
    let mut out = Vec::with_capacity(n);
    for _ in 0..n {
        let z = rng.below(k as usize) as i64;
        out.push((noisy(z, k, &mut rng), noisy(z, k, &mut rng), z.to_string()));
    }
    out
}

/// A real channel: Y depends on X directly (beyond Z) ⇒ I(X;Y|Z) > 0.
pub fn demo_gen_channel(n: usize, k: i64, seed: u64) -> Vec<Sample> {
    let mut rng = Lcg::new(seed);
    let mut out = Vec::with_capacity(n);
    for _ in 0..n {
        let z = rng.below(k as usize) as i64;
        let x = noisy(z, k, &mut rng);
        out.push((x, noisy(x, k, &mut rng), z.to_string()));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mi_zero_for_independent_constanty() {
        // identical streams ⇒ MI > 0; constant Y ⇒ MI == 0
        let same: Vec<(i64, i64)> = (0..100).map(|i| (i % 3, i % 3)).collect();
        assert!(mutual_information(&same) > 0.5);
        let consty: Vec<(i64, i64)> = (0..100).map(|i| (i % 3, 0)).collect();
        assert!(mutual_information(&consty).abs() < 1e-9);
    }

    #[test]
    fn null_reads_consistent() {
        let r = audit(&demo_gen_null(5000, 3, 1), 80, 0, 4.0, 0.005, &[]);
        assert_eq!(r.decision, ChannelDecision::ConsistentWithNull, "cmi={} thr~null_max={}", r.cmi, r.null_max);
    }

    #[test]
    fn channel_is_detected() {
        let r = audit(&demo_gen_channel(5000, 3, 2), 80, 0, 4.0, 0.005, &[]);
        assert_ne!(r.decision, ChannelDecision::ConsistentWithNull, "cmi={}", r.cmi);
    }

    #[test]
    fn shuffle_null_is_deterministic() {
        let s = demo_gen_channel(2000, 3, 5);
        assert_eq!(shuffle_null(&s, 42), shuffle_null(&s, 42));
    }
}
