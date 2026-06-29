// SPDX-License-Identifier: AGPL-3.0-only
//! Bounded metric deflation. A novelty multiplier `m_novel` with a confidence interval is classified vs a
//! critical floor: SUPERCRITICAL → EXPLOIT, SUBCRITICAL → PIVOT, NEAR_CRITICAL → HOLD. The pivot fires only
//! when the CI is entirely below the floor — depletion is established, not merely suspected.
//! `pivot ≠ guaranteed-escape`.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Regime {
    Supercritical,
    Subcritical,
    NearCritical,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Exploit,
    Pivot,
    Hold,
}

impl Action {
    pub fn as_str(&self) -> &'static str {
        match self {
            Action::Exploit => "EXPLOIT",
            Action::Pivot => "PIVOT",
            Action::Hold => "HOLD",
        }
    }
}

/// Regime from the CI of `m_novel` vs the critical floor.
pub fn classify_regime(ci_lo: f64, ci_hi: f64, floor: f64) -> Regime {
    if ci_lo > floor {
        Regime::Supercritical
    } else if ci_hi < floor {
        Regime::Subcritical
    } else {
        Regime::NearCritical // CI crosses the floor ⇒ underdetermined
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Decision {
    pub regime: Regime,
    pub action: Action,
    pub m_novel: f64,
    pub ci: (f64, f64),
}

/// Reads `(m_novel, CI)` and decides EXPLOIT / PIVOT / HOLD.
pub struct FrontierGate {
    pub floor: f64,
}

impl FrontierGate {
    pub fn new(floor: f64) -> Self {
        Self { floor }
    }

    pub fn decide(&self, m_novel: f64, ci: (f64, f64)) -> Decision {
        let regime = classify_regime(ci.0, ci.1, self.floor);
        let action = match regime {
            Regime::Supercritical => Action::Exploit,
            Regime::Subcritical => Action::Pivot,
            Regime::NearCritical => Action::Hold,
        };
        Decision { regime, action, m_novel, ci }
    }
}

impl Default for FrontierGate {
    fn default() -> Self {
        Self { floor: 1.0 }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn supercritical_exploits() {
        assert_eq!(FrontierGate::default().decide(1.5, (1.2, 1.8)).action, Action::Exploit);
    }

    #[test]
    fn subcritical_pivots() {
        assert_eq!(FrontierGate::default().decide(0.5, (0.3, 0.8)).action, Action::Pivot);
    }

    #[test]
    fn crossing_holds() {
        assert_eq!(FrontierGate::default().decide(1.0, (0.7, 1.3)).action, Action::Hold);
    }
}
