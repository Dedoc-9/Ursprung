// SPDX-License-Identifier: AGPL-3.0-only
//! C ABI — the embeddable backend. A host engine (C/C++/Unreal/Unity-native/etc.) can drive the core through
//! five `extern "C"` functions, mirroring the DVSM kernel's own `dvsm_*` ABI shape. The opaque handle is a
//! boxed [`GeometricCore`]; the host never sees the geometry, only the measured [`ObservationC`].
//! `observation != authority` holds across the ABI too — there is no exported setter for `s`/`w`.
//!
//! Build `cdylib`/`staticlib` via the `[lib] crate-type` in Cargo.toml. All entry points are null-checked and
//! length-checked; a bad call returns a negative code instead of unwinding across the FFI boundary.
//!
//! NOTE: this crate has a module named `core`, so we qualify std paths as `std::ptr`/`std::slice` (a bare
//! `core::` path would resolve to the crate module, not the `core` crate).

use std::ptr;
use std::slice;

use crate::core::{Config, GeometricCore, Health};

/// repr(C) mirror of [`crate::core::Observation`] (health as a small int: 0=Nominal, 1=Degenerate, 2=NonFinite).
#[repr(C)]
#[derive(Clone, Copy)]
pub struct ObservationC {
    pub frame: u64,
    pub stress: f64,
    pub sphere_residual: f64,
    pub stiefel_residual: f64,
    pub residual_ortho: f64,
    pub reseeded: u8,
    pub health: u8,
}

fn health_code(h: Health) -> u8 {
    match h {
        Health::Nominal => 0,
        Health::Degenerate => 1,
        Health::NonFinite => 2,
    }
}

/// Create a core of dimensions `n x r` with default config. Returns null on invalid dims.
#[no_mangle]
pub extern "C" fn rc_new(n: usize, r: usize) -> *mut GeometricCore {
    if n == 0 || r == 0 || r > n {
        return ptr::null_mut();
    }
    Box::into_raw(Box::new(GeometricCore::new(n, r, Config::default())))
}

/// Step the core with an input of length `len` (must equal `n`), writing telemetry to `out`.
/// Returns 0 on success; negative on a bad handle / null / length mismatch (never unwinds).
///
/// # Safety
/// `core` must be a pointer from [`rc_new`] not yet freed; `z` must point to `len` readable `f64`s; `out`
/// must point to a writable `ObservationC`.
#[no_mangle]
pub unsafe extern "C" fn rc_step(
    core: *mut GeometricCore,
    z: *const f64,
    len: usize,
    out: *mut ObservationC,
) -> i32 {
    let c = match core.as_mut() {
        Some(c) => c,
        None => return -1,
    };
    if z.is_null() {
        return -2;
    }
    let (n, _r) = c.dims();
    if len != n {
        return -3;
    }
    let zs = slice::from_raw_parts(z, len);
    let o = c.step(zs);
    if let Some(dst) = out.as_mut() {
        *dst = ObservationC {
            frame: o.frame,
            stress: o.stress,
            sphere_residual: o.sphere_residual,
            stiefel_residual: o.stiefel_residual,
            residual_ortho: o.residual_ortho,
            reseeded: o.reseeded as u8,
            health: health_code(o.health),
        };
    }
    0
}

/// Copy the (read-only) spherical state into `out` (length must equal `n`). Returns 0 on success.
///
/// # Safety
/// `core` must be valid; `out` must point to `len` writable `f64`s.
#[no_mangle]
pub unsafe extern "C" fn rc_observe_state(core: *const GeometricCore, out: *mut f64, len: usize) -> i32 {
    let c = match core.as_ref() {
        Some(c) => c,
        None => return -1,
    };
    let s = c.state();
    if out.is_null() || len != s.len() {
        return -2;
    }
    let dst = slice::from_raw_parts_mut(out, len);
    dst.copy_from_slice(s);
    0
}

/// The current frame index, or 0 on a null handle.
///
/// # Safety
/// `core` must be a valid pointer from [`rc_new`] or null.
#[no_mangle]
pub unsafe extern "C" fn rc_frame(core: *const GeometricCore) -> u64 {
    match core.as_ref() {
        Some(c) => c.frame_index(),
        None => 0,
    }
}

/// Free a core created by [`rc_new`].
///
/// # Safety
/// `core` must be a pointer from [`rc_new`] not yet freed (or null).
#[no_mangle]
pub unsafe extern "C" fn rc_free(core: *mut GeometricCore) {
    if !core.is_null() {
        drop(Box::from_raw(core));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ffi_roundtrip() {
        let c = rc_new(4, 2);
        assert!(!c.is_null());
        let z = [0.3f64, -0.2, 0.1, 0.5];
        let mut o = ObservationC {
            frame: 0, stress: 0.0, sphere_residual: 0.0, stiefel_residual: 0.0,
            residual_ortho: 0.0, reseeded: 0, health: 9,
        };
        unsafe {
            assert_eq!(rc_step(c, z.as_ptr(), z.len(), &mut o), 0);
            assert_eq!(o.frame, 1);
            assert!(o.health <= 2);
            let mut st = [0.0f64; 4];
            assert_eq!(rc_observe_state(c, st.as_mut_ptr(), 4), 0);
            assert_eq!(rc_frame(c), 1);
            // length mismatch is rejected, not unwound
            assert_eq!(rc_step(c, z.as_ptr(), 3, &mut o), -3);
            rc_free(c);
        }
    }

    #[test]
    fn null_handles_are_safe() {
        unsafe {
            let mut o = ObservationC {
                frame: 0, stress: 0.0, sphere_residual: 0.0, stiefel_residual: 0.0,
                residual_ortho: 0.0, reseeded: 0, health: 0,
            };
            assert_eq!(rc_step(ptr::null_mut(), ptr::null(), 0, &mut o), -1);
            assert_eq!(rc_frame(ptr::null()), 0);
            rc_free(ptr::null_mut()); // no-op, must not crash
        }
    }
}
