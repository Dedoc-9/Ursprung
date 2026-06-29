// SPDX-License-Identifier: AGPL-3.0-only
//! The epistemic type: a value that cannot exist without a valid proof.
//!
//! A [`Grounding`] is any proof object exposing `is_grounded()` + `label()`. [`Grounded<T>`] holds its value
//! in a PRIVATE field; the only constructor refuses (with [`UngroundedError`]) unless the proof is grounded.
//! Holding a `Grounded<T>` therefore *is* the witness that `T` was verified — the action chokepoint enforced
//! by the type system, not by a runtime re-check. `grounded ≠ true`: it is grounded relative to the proof's
//! scope.

use std::error::Error;
use std::fmt;

/// A verifier-issued proof. `is_grounded()` decides whether a value may be enacted; `label()` records what it
/// attests (never global correctness).
pub trait Grounding {
    fn is_grounded(&self) -> bool;
    fn label(&self) -> String;
}

/// Construction of a [`Grounded<T>`] (or a call through [`enact`]) was refused because the proof was not
/// grounded — raised BEFORE any action body runs (atomic refusal).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UngroundedError {
    pub label: String,
}

impl fmt::Display for UngroundedError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "refusing to ground value: proof not grounded ({})", self.label)
    }
}

impl Error for UngroundedError {}

/// A value tagged with the proof that grounds it. The raw value is reachable only AFTER grounding succeeded
/// (private field + checked constructor), so a `Grounded<T>` is unforgeable evidence that `T` was verified.
#[derive(Debug, Clone)]
pub struct Grounded<T> {
    value: T,
    proof_label: String,
}

impl<T> Grounded<T> {
    /// Ground `value` with `proof`; `Err(UngroundedError)` if the proof is not grounded.
    pub fn new<P: Grounding>(value: T, proof: &P) -> Result<Self, UngroundedError> {
        if proof.is_grounded() {
            Ok(Self { value, proof_label: proof.label() })
        } else {
            Err(UngroundedError { label: proof.label() })
        }
    }

    /// Borrow the grounded value.
    pub fn value(&self) -> &T {
        &self.value
    }

    /// Consume the wrapper, yielding the value (only reachable once grounding has succeeded).
    pub fn into_value(self) -> T {
        self.value
    }

    pub fn proof_label(&self) -> &str {
        &self.proof_label
    }
}

/// The ACTION chokepoint: run `action` on `value` ONLY if `proof` grounds it; otherwise return
/// `Err(UngroundedError)` without ever calling `action`. The grant of authority is the proof's, never the
/// orchestrator's.
pub fn enact<T, P, R, F>(value: T, proof: &P, action: F) -> Result<R, UngroundedError>
where
    P: Grounding,
    F: FnOnce(T) -> R,
{
    let g = Grounded::new(value, proof)?;
    Ok(action(g.into_value()))
}

/// A bare attestation (for tests / trusted boundaries). `ok` must be supplied explicitly — no default-true.
#[derive(Debug, Clone)]
pub struct Attested {
    pub ok: bool,
    pub why: String,
}

impl Attested {
    pub fn new(ok: bool, why: impl Into<String>) -> Self {
        Self { ok, why: why.into() }
    }
}

impl Grounding for Attested {
    fn is_grounded(&self) -> bool {
        self.ok
    }
    fn label(&self) -> String {
        self.why.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    #[test]
    fn grounded_runs_action() {
        let ran = Cell::new(false);
        let out = enact(7i32, &Attested::new(true, "verifier-grounded"), |v| {
            ran.set(true);
            v * 2
        });
        assert_eq!(out.unwrap(), 14);
        assert!(ran.get());
    }

    #[test]
    fn ungrounded_refuses_atomically() {
        let ran = Cell::new(false);
        let out = enact(7i32, &Attested::new(false, "ungrounded"), |v| {
            ran.set(true);
            v * 2
        });
        assert!(out.is_err());
        assert!(!ran.get(), "action must NOT run on an ungrounded value");
    }

    #[test]
    fn grounded_value_unconstructable_without_proof() {
        assert!(Grounded::new("x", &Attested::new(false, "no")).is_err());
        assert_eq!(*Grounded::new("x", &Attested::new(true, "yes")).unwrap().value(), "x");
    }
}
