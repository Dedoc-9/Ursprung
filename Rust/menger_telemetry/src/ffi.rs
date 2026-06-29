// SPDX-License-Identifier: AGPL-3.0-only
//! C ABI — embeddable telemetry. Mirrors the upstream `telemetry_*` surface, but with a verify that actually
//! verifies. All entry points are null/length-guarded; bad calls return negative codes, never unwind.
//!
//! Return codes: 0 success · -1 invalid parameter · -2 processing error (rate limit) · -3 null pointer.

use std::slice;

use crate::kernel::{FrameSnapshot, Kernel, ProcessError, HASH_SIZE, N};

/// Initialize a kernel with the given Menger depth. Never null on success.
#[no_mangle]
pub extern "C" fn telemetry_init(menger_depth: u8) -> *mut Kernel {
    Box::into_raw(Box::new(Kernel::new(menger_depth)))
}

/// Destroy a kernel created by [`telemetry_init`].
#[no_mangle]
pub unsafe extern "C" fn telemetry_destroy(handle: *mut Kernel) {
    if !handle.is_null() {
        drop(Box::from_raw(handle));
    }
}

/// Process one frame: `sensor_count` must equal `N`. Writes the snapshot to `out`.
///
/// # Safety
/// `handle` from [`telemetry_init`]; `sensors` points to `sensor_count` `f64`s; `out` is writable.
#[no_mangle]
pub unsafe extern "C" fn telemetry_process(
    handle: *mut Kernel,
    sensors: *const f64,
    sensor_count: u32,
    timestamp_ns: u64,
    out: *mut FrameSnapshot,
) -> i32 {
    if handle.is_null() || sensors.is_null() || out.is_null() {
        return -3;
    }
    if sensor_count as usize != N {
        return -1;
    }
    let k = &mut *handle;
    let src = slice::from_raw_parts(sensors, N);
    let mut arr = [0.0f64; N];
    arr.copy_from_slice(src);
    match k.process_frame(&arr, timestamp_ns) {
        Ok(snap) => {
            *out = snap;
            0
        }
        Err(ProcessError::RateLimited) => -2,
    }
}

/// Copy the 32-byte SHA-256 commitment out of a snapshot.
///
/// # Safety
/// `snap` valid; `out` points to `HASH_SIZE` writable bytes.
#[no_mangle]
pub unsafe extern "C" fn telemetry_get_hash(snap: *const FrameSnapshot, out: *mut u8) -> i32 {
    if snap.is_null() || out.is_null() {
        return -3;
    }
    let dst = slice::from_raw_parts_mut(out, HASH_SIZE);
    dst.copy_from_slice(&(*snap).hash);
    0
}

/// REAL integrity check: recompute the commitment and compare. Returns 1 (valid), 0 (tampered), -3 (null).
///
/// # Safety
/// `snap` must be a valid pointer or null.
#[no_mangle]
pub unsafe extern "C" fn telemetry_verify(snap: *const FrameSnapshot) -> i32 {
    match snap.as_ref() {
        Some(s) => {
            if Kernel::verify(s) {
                1
            } else {
                0
            }
        }
        None => -3,
    }
}

/// The kernel's current Menger depth (0 on null).
///
/// # Safety
/// `handle` valid or null.
#[no_mangle]
pub unsafe extern "C" fn telemetry_menger_depth(handle: *const Kernel) -> u8 {
    match handle.as_ref() {
        Some(k) => k.menger_depth(),
        None => 0,
    }
}

/// The processed-frame count (0 on null).
///
/// # Safety
/// `handle` valid or null.
#[no_mangle]
pub unsafe extern "C" fn telemetry_frame_count(handle: *const Kernel) -> u64 {
    match handle.as_ref() {
        Some(k) => k.frame_count(),
        None => 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ffi_process_and_verify() {
        let h = telemetry_init(2);
        assert!(!h.is_null());
        let sensors = [50.0f64; N];
        let mut snap = FrameSnapshot::default();
        unsafe {
            assert_eq!(telemetry_process(h, sensors.as_ptr(), N as u32, 1_000, &mut snap), 0);
            assert_eq!(telemetry_frame_count(h), 1);
            assert_eq!(telemetry_menger_depth(h), 2);

            let mut hash = [0u8; HASH_SIZE];
            assert_eq!(telemetry_get_hash(&snap, hash.as_mut_ptr()), 0);
            assert_eq!(hash, snap.hash);

            assert_eq!(telemetry_verify(&snap), 1); // genuine
            let mut bad = snap;
            bad.z[0] = bad.z[0].wrapping_add(1);
            assert_eq!(telemetry_verify(&bad), 0); // tampered

            // guards
            assert_eq!(telemetry_process(h, sensors.as_ptr(), 3, 5_000_000, &mut snap), -1);
            assert_eq!(telemetry_process(std::ptr::null_mut(), sensors.as_ptr(), N as u32, 0, &mut snap), -3);
            assert_eq!(telemetry_verify(std::ptr::null()), -3);

            telemetry_destroy(h);
        }
    }
}
