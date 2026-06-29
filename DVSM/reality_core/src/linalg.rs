// SPDX-License-Identifier: AGPL-3.0-only
//! Minimal, dependency-free dense linear algebra — only what the geometric core needs. Column-major frame
//! storage (a Stiefel frame is `r` columns of length `n`), so projection and Gram-Schmidt are natural.
//!
//! The Stiefel retraction is an explicit modified Gram-Schmidt that PRESERVES the `n x r` shape (a library
//! QR's `q()` shape is implementation-dependent; here it is pinned). `convenience != invariant`.

/// Dot product. Panics only on mismatched lengths (a programmer error, not runtime data).
#[inline]
pub fn dot(a: &[f64], b: &[f64]) -> f64 {
    debug_assert_eq!(a.len(), b.len());
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

#[inline]
pub fn norm(a: &[f64]) -> f64 {
    dot(a, a).sqrt()
}

/// `y += a * x`
#[inline]
pub fn axpy(y: &mut [f64], a: f64, x: &[f64]) {
    debug_assert_eq!(y.len(), x.len());
    for (yi, xi) in y.iter_mut().zip(x) {
        *yi += a * xi;
    }
}

/// `ca*a + cb*b` (elementwise), into a fresh vector.
#[inline]
pub fn combine2(a: &[f64], ca: f64, b: &[f64], cb: f64) -> Vec<f64> {
    debug_assert_eq!(a.len(), b.len());
    a.iter().zip(b).map(|(x, y)| ca * x + cb * y).collect()
}

/// `v / ||v||`, or the zero vector if `||v|| <= eps` (the numerical floor — a hardening guard).
#[inline]
pub fn normalized(v: &[f64], eps: f64) -> Vec<f64> {
    let n = norm(v);
    if n <= eps {
        vec![0.0; v.len()]
    } else {
        v.iter().map(|x| x / n).collect()
    }
}

#[inline]
pub fn all_finite(v: &[f64]) -> bool {
    v.iter().all(|x| x.is_finite())
}

/// An `n x r` orthonormal frame `W ∈ St(n, r)`, stored as `r` columns of length `n`.
#[derive(Clone, Debug, PartialEq)]
pub struct Frame {
    pub n: usize,
    pub r: usize,
    pub cols: Vec<Vec<f64>>, // r columns, each length n
}

impl Frame {
    /// The first `r` standard basis vectors — a valid initial Stiefel frame (`WᵀW = I`).
    pub fn identity(n: usize, r: usize) -> Self {
        assert!(r <= n && r > 0, "Stiefel frame requires 0 < r <= n");
        let mut cols = vec![vec![0.0; n]; r];
        for j in 0..r {
            cols[j][j] = 1.0;
        }
        Self { n, r, cols }
    }

    /// `c = Wᵀ z` (an `r`-vector): the coordinates of `z` in the frame.
    pub fn coeffs(&self, z: &[f64]) -> Vec<f64> {
        debug_assert_eq!(z.len(), self.n);
        self.cols.iter().map(|c| dot(c, z)).collect()
    }

    /// `Π_W(z) = W Wᵀ z` (an `n`-vector): the orthogonal projection of `z` onto span(W).
    pub fn project(&self, z: &[f64]) -> Vec<f64> {
        let c = self.coeffs(z);
        let mut p = vec![0.0; self.n];
        for (j, col) in self.cols.iter().enumerate() {
            axpy(&mut p, c[j], col);
        }
        p
    }

    /// `R = z - Π_W(z)` (orthogonal to span(W) by construction).
    pub fn residual(&self, z: &[f64]) -> Vec<f64> {
        let p = self.project(z);
        z.iter().zip(p).map(|(a, b)| a - b).collect()
    }

    /// `||WᵀW - I||_F` — the measured Stiefel residual (0 ⇒ exactly orthonormal). We MEASURE it; we do not
    /// assume it. `invariant != comment`.
    pub fn stiefel_residual(&self) -> f64 {
        let mut acc = 0.0;
        for i in 0..self.r {
            for j in 0..self.r {
                let g = dot(&self.cols[i], &self.cols[j]);
                let target = if i == j { 1.0 } else { 0.0 };
                acc += (g - target) * (g - target);
            }
        }
        acc.sqrt()
    }

    /// Re-orthonormalize the columns in place via modified Gram-Schmidt (the Stiefel retraction). A column
    /// whose norm collapses below `eps` is re-seeded from a standard basis vector and re-orthogonalized — a
    /// rank-deficiency guard so the frame never silently degenerates. Returns `true` if any reseed occurred.
    pub fn orthonormalize(&mut self, eps: f64) -> bool {
        let n = self.n;
        let r = self.r;
        let mut reseeded = false;
        for j in 0..r {
            // subtract projections onto already-orthonormal columns 0..j
            for i in 0..j {
                let ci = self.cols[i].clone();
                let proj = dot(&self.cols[j], &ci);
                axpy(&mut self.cols[j], -proj, &ci);
            }
            let mut nrm = norm(&self.cols[j]);
            if nrm <= eps {
                // degenerate: reseed from e_{j mod n}, re-orthogonalize, renormalize
                reseeded = true;
                let mut e = vec![0.0; n];
                e[j % n] = 1.0;
                for i in 0..j {
                    let ci = self.cols[i].clone();
                    let proj = dot(&e, &ci);
                    axpy(&mut e, -proj, &ci);
                }
                self.cols[j] = e;
                nrm = norm(&self.cols[j]);
                if nrm <= eps {
                    continue; // leave as-is; stiefel_residual() will flag it
                }
            }
            let inv = 1.0 / nrm;
            for x in self.cols[j].iter_mut() {
                *x *= inv;
            }
        }
        reseeded
    }

    pub fn all_finite(&self) -> bool {
        self.cols.iter().all(|c| all_finite(c))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn projection_is_idempotent() {
        let w = Frame::identity(5, 2);
        let z = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let p1 = w.project(&z);
        let p2 = w.project(&p1);
        let diff: f64 = p1.iter().zip(&p2).map(|(a, b)| (a - b).abs()).sum();
        assert!(diff < 1e-12, "projection not idempotent: {diff}");
    }

    #[test]
    fn residual_is_orthogonal_to_frame() {
        let w = Frame::identity(5, 2);
        let z = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let r = w.residual(&z);
        let c = w.coeffs(&r); // Wᵀ R should be ~0
        assert!(norm(&c) < 1e-12, "residual not orthogonal: {}", norm(&c));
    }

    #[test]
    fn orthonormalize_yields_identity_gram() {
        let mut w = Frame { n: 4, r: 3, cols: vec![
            vec![1.0, 1.0, 0.0, 0.0],
            vec![1.0, 0.0, 1.0, 0.0],
            vec![0.0, 1.0, 1.0, 1.0],
        ]};
        w.orthonormalize(1e-12);
        assert!(w.stiefel_residual() < 1e-10, "gram residual: {}", w.stiefel_residual());
    }

    #[test]
    fn reseed_recovers_collapsed_column() {
        let mut w = Frame { n: 3, r: 2, cols: vec![
            vec![1.0, 0.0, 0.0],
            vec![1.0, 0.0, 0.0], // duplicate ⇒ collapses after MGS
        ]};
        let reseeded = w.orthonormalize(1e-12);
        assert!(reseeded, "expected a reseed");
        assert!(w.stiefel_residual() < 1e-10, "gram after reseed: {}", w.stiefel_residual());
    }
}
