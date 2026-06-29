// SPDX-License-Identifier: AGPL-3.0-only
//! LAYER 2 — the mutable runtime. It ingests a stream, schedules discrete steps, and applies backpressure —
//! but it CANNOT alter Layer-1 geometry except by submitting an input through [`GeometricCore::step`]. The
//! core is held privately; there is no accessor that mutates `s`/`w`. `observation != authority`;
//! `mode != geometry`.
//!
//! HARDENING vs the upstream runtime: the original keyed its cadence on `Instant::now()` (wall-clock), which
//! makes execution non-deterministic and untestable. Here the runtime runs on a LOGICAL clock the caller
//! advances ([`Runtime::advance`]), so a given (input stream, clock schedule) replays bit-identically.
//! `replay-determinism > wall-clock convenience`.

use std::collections::VecDeque;

use crate::core::{GeometricCore, Observation};

/// Execution profile. Affects ONLY the scheduling cadence (in logical frames), never the geometry.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mode {
    Gaming, // ~60 Hz: step every 16 logical frames
    Rf,     // fast: step every 2 logical frames
    Hybrid, // step as soon as a frame elapses AND input is queued
}

impl Mode {
    pub fn cadence(&self) -> u64 {
        match self {
            Mode::Gaming => 16,
            Mode::Rf => 2,
            Mode::Hybrid => 1,
        }
    }
}

/// LAYER 2. Owns a [`GeometricCore`] privately; drives it only via `step`, observes it read-only.
pub struct Runtime {
    core: GeometricCore,
    mode: Mode,
    buffer: VecDeque<Vec<f64>>,
    max_buffer: usize,
    dropped: u64,
    clock: u64,     // logical time (frames), advanced by the caller
    last_step: u64, // logical time of the last executed step
}

impl Runtime {
    pub fn new(core: GeometricCore, mode: Mode) -> Self {
        Self { core, mode, buffer: VecDeque::new(), max_buffer: 64, dropped: 0, clock: 0, last_step: 0 }
    }

    pub fn with_max_buffer(mut self, cap: usize) -> Self {
        self.max_buffer = cap.max(1);
        self
    }

    /// FIFO ingestion with bounded backpressure: when full, the OLDEST input is dropped (and counted).
    pub fn ingest(&mut self, z: Vec<f64>) {
        if self.buffer.len() >= self.max_buffer {
            self.buffer.pop_front();
            self.dropped += 1;
        }
        self.buffer.push_back(z);
    }

    /// Advance the logical clock by `frames` (this is the deterministic substitute for wall-clock time).
    pub fn advance(&mut self, frames: u64) {
        self.clock = self.clock.wrapping_add(frames);
    }

    /// Execute one step iff the cadence has elapsed (logically) and an input is queued.
    pub fn tick(&mut self) -> Option<Observation> {
        if self.clock.wrapping_sub(self.last_step) < self.mode.cadence() {
            return None;
        }
        let z = self.buffer.pop_front()?;
        self.last_step = self.clock;
        Some(self.core.step(&z))
    }

    /// Convenience: advance the clock and try to step (a single logical tick of `frames`).
    pub fn advance_and_tick(&mut self, frames: u64) -> Option<Observation> {
        self.advance(frames);
        self.tick()
    }

    /// Mode switch is a safe reset boundary: the pending buffer is cleared (its cadence was for the old mode).
    pub fn set_mode(&mut self, mode: Mode) {
        self.mode = mode;
        self.buffer.clear();
        self.last_step = self.clock;
    }

    // ---- read-only observation (no authority over the geometry) ----
    pub fn mode(&self) -> Mode {
        self.mode
    }
    pub fn buffered(&self) -> usize {
        self.buffer.len()
    }
    pub fn dropped(&self) -> u64 {
        self.dropped
    }
    pub fn clock(&self) -> u64 {
        self.clock
    }
    /// Read-only view of the core's state — Layer 2 can see, never set.
    pub fn observe_state(&self) -> &[f64] {
        self.core.state()
    }
    /// A non-invasive probe of the core's current invariant residuals.
    pub fn probe(&self) -> Observation {
        self.core.probe()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::Config;

    fn rt() -> Runtime {
        Runtime::new(GeometricCore::new(4, 2, Config::default()), Mode::Rf)
    }

    #[test]
    fn backpressure_drops_oldest_and_counts() {
        let mut r = rt().with_max_buffer(8);
        for i in 0..20 {
            r.ingest(vec![i as f64, 0.0, 0.0, 0.0]);
        }
        assert_eq!(r.buffered(), 8);
        assert_eq!(r.dropped(), 12);
    }

    #[test]
    fn cadence_gates_steps() {
        let mut r = rt(); // Rf cadence = 2
        r.ingest(vec![1.0, 0.0, 0.0, 0.0]);
        r.advance(1);
        assert!(r.tick().is_none(), "should not step before cadence elapses");
        r.advance(1); // now 2 elapsed
        assert!(r.tick().is_some(), "should step once cadence elapses");
    }

    #[test]
    fn mode_switch_clears_buffer() {
        let mut r = rt();
        r.ingest(vec![1.0, 0.0, 0.0, 0.0]);
        r.ingest(vec![2.0, 0.0, 0.0, 0.0]);
        assert_eq!(r.buffered(), 2);
        r.set_mode(Mode::Gaming);
        assert_eq!(r.buffered(), 0);
    }

    #[test]
    fn replay_is_deterministic() {
        let drive = |seed: u64| {
            let mut r = rt();
            let mut st = seed;
            let mut trace = Vec::new();
            for _ in 0..50 {
                st = st.wrapping_mul(6364136223846793005).wrapping_add(1);
                let v = ((st >> 11) as f64 / (1u64 << 53) as f64) - 0.5;
                r.ingest(vec![v, v * 2.0, v - 1.0, v + 1.0]);
                if let Some(o) = r.advance_and_tick(2) {
                    trace.push(o.stress);
                }
            }
            trace
        };
        assert_eq!(drive(42), drive(42));
        assert!(!drive(42).is_empty());
    }
}
