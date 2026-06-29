// SPDX-License-Identifier: AGPL-3.0-only
//! Q32.32 deterministic fixed-point. A value is an `i64` interpreted as `raw / 2^32`. Products use an `i128`
//! intermediate and shift back — exactly representable in std, no 256-bit integer required.
//!
//! WHY Q32.32 (not the upstream Q64.64): a Q64.64 product is a 128×128→256-bit multiply, which the upstream
//! kernel writes with a bare `i256` type that Rust does not have and its `Cargo.toml` does not provide — so it
//! does not compile. Q32.32 keeps every operation inside `i128`, so it is deterministic, portable, and
//! actually builds. `representable > aspirational`.

/// A Q32.32 fixed-point number (`raw = value * 2^32`).
pub type Fixed = i64;

pub const FRAC_BITS: u32 = 32;
pub const ONE: Fixed = 1 << FRAC_BITS; // 1.0

/// `a * b` in Q32.32 (round toward zero) via an i128 intermediate. Deterministic on every platform.
#[inline]
pub fn qmul(a: Fixed, b: Fixed) -> Fixed {
    (((a as i128) * (b as i128)) >> FRAC_BITS) as Fixed
}

/// Convert an `f64` to Q32.32, clamped to the representable range (a non-finite value maps to 0).
#[inline]
pub fn from_f64(x: f64) -> Fixed {
    if !x.is_finite() {
        return 0;
    }
    let scaled = x * (ONE as f64);
    if scaled >= i64::MAX as f64 {
        i64::MAX
    } else if scaled <= i64::MIN as f64 {
        i64::MIN
    } else {
        scaled as i64
    }
}

#[inline]
pub fn to_f64(a: Fixed) -> f64 {
    a as f64 / (ONE as f64)
}

/// Quantize a non-negative physical reading into `[0, 1)` of its range, as Q32.32 (telemetry convention:
/// readings are non-negative; out-of-range saturates just below 1.0). A non-finite input maps to 0.
#[inline]
pub fn quantize(value: f64, max_phys: f64) -> Fixed {
    if !value.is_finite() || max_phys <= 0.0 {
        return 0;
    }
    let n = (value / max_phys).clamp(0.0, 0.999_999_999);
    from_f64(n)
}

#[inline]
pub fn clamp(a: Fixed, lo: Fixed, hi: Fixed) -> Fixed {
    if a < lo {
        lo
    } else if a > hi {
        hi
    } else {
        a
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn one_times_x_is_x() {
        let x = from_f64(0.375);
        assert_eq!(qmul(ONE, x), x);
    }

    #[test]
    fn qmul_matches_float_within_tolerance() {
        for &(a, b) in &[(0.5, 0.5), (0.1, 0.2), (0.99, 0.99), (0.0, 0.7), (0.333, 3.0)] {
            let got = to_f64(qmul(from_f64(a), from_f64(b)));
            assert!((got - a * b).abs() < 1e-6, "{a}*{b}: got {got}");
        }
    }

    #[test]
    fn roundtrip() {
        for v in [0.0, 0.25, 0.5, 0.99, 1.5, -2.0] {
            assert!((to_f64(from_f64(v)) - v).abs() < 1e-6);
        }
    }

    #[test]
    fn quantize_is_bounded_and_nonneg() {
        assert_eq!(quantize(f64::NAN, 100.0), 0);
        assert!(quantize(150.0, 100.0) < ONE && quantize(150.0, 100.0) >= 0); // saturates below 1.0
        assert_eq!(quantize(-5.0, 100.0), 0); // non-negative convention
    }
}
