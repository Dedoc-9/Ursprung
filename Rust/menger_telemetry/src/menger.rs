// SPDX-License-Identifier: AGPL-3.0-only
//! The Menger / Sierpinski-carpet sparsity mask over a `side × side` index grid (the 2D fractal that gates a
//! coupling matrix). Unlike the upstream — whose depth loop never used the level variable, so depth 1 and 2
//! produced the SAME single-scale mask while the test expected `(20/27)²` — here **depth is real and the
//! retained fraction is exact**: on a `side = 3^L` grid, level `k` removes the center of every `3×3` sub-block
//! at scale `side/3^(k+1)`, so after `depth` levels the retained count is exactly `8^depth · 9^(L−depth)`,
//! i.e. a fraction `(8/9)^depth`. `claimed-fractal = code-fractal`, and it is tested.
//!
//! (The classic Menger *sponge* is the 3D object with keep-ratio 20/27; the natural analog for a 2D index
//! grid — a coupling matrix — is the Sierpinski *carpet*, keep-ratio 8/9 per level. We use and name the 2D
//! object honestly rather than applying the 3D ratio to a 2D mask.)

#[derive(Clone, Debug)]
pub struct MengerMask {
    pub side: usize,
    pub depth: u32,
    kept: Vec<bool>, // row-major side*side
}

fn pow3(k: u32) -> usize {
    (0..k).fold(1usize, |a, _| a * 3)
}

/// Largest depth a side supports (number of times `side` divides by 3).
pub fn max_depth(side: usize) -> u32 {
    let mut d = 0;
    let mut s = side;
    while s > 1 && s % 3 == 0 {
        s /= 3;
        d += 1;
    }
    d
}

fn removed(i: usize, j: usize, side: usize, depth: u32) -> bool {
    for k in 0..depth {
        let block = side / pow3(k + 1);
        if block == 0 {
            break;
        }
        let di = (i / block) % 3;
        let dj = (j / block) % 3;
        if di == 1 && dj == 1 {
            return true; // center of this sub-block ⇒ carved out
        }
    }
    false
}

impl MengerMask {
    /// Build the carpet mask. `depth` is clamped to `max_depth(side)` so the fractal is well-defined.
    pub fn new(side: usize, depth: u32) -> Self {
        assert!(side >= 1, "side must be >= 1");
        let depth = depth.min(max_depth(side));
        let mut kept = vec![true; side * side];
        for i in 0..side {
            for j in 0..side {
                if removed(i, j, side, depth) {
                    kept[i * side + j] = false;
                }
            }
        }
        Self { side, depth, kept }
    }

    #[inline]
    pub fn kept(&self, i: usize, j: usize) -> bool {
        self.kept[i * self.side + j]
    }

    pub fn total(&self) -> usize {
        self.side * self.side
    }

    pub fn retained(&self) -> usize {
        self.kept.iter().filter(|&&b| b).count()
    }

    pub fn fraction(&self) -> f64 {
        self.retained() as f64 / self.total() as f64
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn depth_zero_keeps_everything() {
        assert_eq!(MengerMask::new(9, 0).retained(), 81);
    }

    #[test]
    fn side9_exact_counts() {
        // 9 = 3^2; retained = 8^depth * 9^(2-depth)
        assert_eq!(MengerMask::new(9, 1).retained(), 72); // 8 * 9
        assert_eq!(MengerMask::new(9, 2).retained(), 64); // 8^2
    }

    #[test]
    fn side27_exact_counts() {
        // 27 = 3^3
        assert_eq!(MengerMask::new(27, 1).retained(), 648); // 8 * 81
        assert_eq!(MengerMask::new(27, 2).retained(), 576); // 64 * 9
        assert_eq!(MengerMask::new(27, 3).retained(), 512); // 8^3
    }

    #[test]
    fn depth_is_not_idempotent() {
        // the upstream bug: depth 1 and 2 gave the same mask. Here they must differ.
        assert_ne!(MengerMask::new(9, 1).retained(), MengerMask::new(9, 2).retained());
    }

    #[test]
    fn fraction_is_eight_ninths_per_level() {
        let f1 = MengerMask::new(27, 1).fraction();
        let f2 = MengerMask::new(27, 2).fraction();
        assert!((f1 - 8.0 / 9.0).abs() < 1e-12);
        assert!((f2 - (8.0 / 9.0_f64).powi(2)).abs() < 1e-12);
    }

    #[test]
    fn depth_clamped_to_max() {
        assert_eq!(MengerMask::new(9, 5).depth, 2);
    }
}
