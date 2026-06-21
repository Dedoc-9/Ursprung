// SPDX-License-Identifier: AGPL-3.0-only
//! Reality Kernel — Rust CORE port (CANDIDATE; unverified in-session, no toolchain was available).
//!
//! This is a *semantic preservation* exercise, not a rewrite for speed. The Python `reality_kernel`
//! is the reference model; this crate must reproduce its distinctions and survive what Python could
//! not exercise: real concurrency, memory pressure, corruption, and a frame budget. Two paths, by type:
//!
//!   CommitPath   never drops · mutates canonical state · provenance required
//!   ResolvePath  may defer/batch/drop · inspection only · cannot advance state
//!
//! Invariant: `dropped observation = allowed; dropped transition = forbidden`.
//! Ceiling: this is an accounting system for state and ignorance — it records what changed, why we
//! think it changed, and what cannot currently be recovered. It does not certify the model correct
//! (`declared ≠ verified`; the kernel is a notary, not Reality).
//!
//! std-only on purpose (offline build). Digests use std DefaultHasher — they need only be present and
//! resolvable; the differential against the Python oracle is over existence/diagnosis/resolution,
//! never digest values.

use std::collections::hash_map::DefaultHasher;
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

// ---------------- failure taxonomy (mirrors failure_taxonomy/failure.py) ----------------
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Failure {
    Severance,
    Indistinguishability,
    AssumptionLimit,
    ResourceLimit,
    Unclassified,
}

impl Failure {
    pub fn name(&self) -> &'static str {
        match self {
            Failure::Severance => "severance",
            Failure::Indistinguishability => "indistinguishability",
            Failure::AssumptionLimit => "assumption_limit",
            Failure::ResourceLimit => "resource_limit",
            Failure::Unclassified => "unclassified",
        }
    }
    pub fn is_absolute(&self) -> bool {
        matches!(self, Failure::Severance | Failure::Indistinguishability)
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Case {
    pub signal_present: bool,
    pub alternative_cause_matches: bool,
    pub resolves_under_richer_admissibility: bool,
    pub resolves_under_richer_observer: bool,
}

/// Order matters: absence first, then collision, then the relative axes.
pub fn diagnose(c: Case) -> Failure {
    if !c.signal_present {
        return Failure::Severance;
    }
    if c.alternative_cause_matches {
        return Failure::Indistinguishability;
    }
    if c.resolves_under_richer_admissibility {
        return Failure::AssumptionLimit;
    }
    if c.resolves_under_richer_observer {
        return Failure::ResourceLimit;
    }
    Failure::Unclassified
}

// ---------------- existence (the four-way Query result) ----------------
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Existence {
    Present,
    Absent,
    Unresolved,
    Unaccounted,
}

impl Existence {
    pub fn name(&self) -> &'static str {
        match self {
            Existence::Present => "present",
            Existence::Absent => "absent",
            Existence::Unresolved => "unresolved",
            Existence::Unaccounted => "unaccounted",
        }
    }
}

// ---------------- Artifact: a thing with declared provenance ----------------
#[derive(Debug, Clone)]
pub struct Artifact {
    pub kind: String,
    pub content: String,
    pub provenance: HashMap<String, String>,
}

impl Artifact {
    pub fn new(kind: &str, content: &str, provenance: HashMap<String, String>) -> Result<Self, &'static str> {
        if provenance.is_empty() {
            return Err("an Artifact must carry declared provenance (identity includes provenance)");
        }
        Ok(Artifact { kind: kind.into(), content: content.into(), provenance })
    }
}

// ---------------- Event: a transition with lineage ----------------
#[derive(Debug, Clone)]
pub struct Event {
    pub target: String,
    pub previous: String,
    pub new: String,
    pub source: String,
    pub dependencies: Vec<String>,
    pub survival: Vec<bool>,
    pub justification: String,
}

impl Event {
    pub fn new(target: &str, previous: &str, new: &str, source: &str) -> Result<Self, &'static str> {
        if source.is_empty() {
            return Err("an Event must name a source — no transition without lineage");
        }
        Ok(Event {
            target: target.into(),
            previous: previous.into(),
            new: new.into(),
            source: source.into(),
            dependencies: Vec::new(),
            survival: Vec::new(),
            justification: "-".into(),
        })
    }
}

// ---------------- internal Edit (the stored, digestible lineage node) ----------------
#[derive(Debug, Clone)]
struct Edit {
    target: String,
    previous: String,
    new: String,
    source: String,
    depends_on: Option<String>,
    // recorded lineage (did this edit survive its tests), mirroring Python's Edit.survives();
    // not yet surfaced by a query, so allowed dead until a survival-aware Query is added.
    #[allow(dead_code)]
    survives: Option<bool>,
}

impl Edit {
    fn digest(&self) -> String {
        let mut h = DefaultHasher::new();
        (&self.target, &self.previous, &self.new, &self.source, &self.depends_on).hash(&mut h);
        format!("{:012x}", h.finish())
    }
}

// ---------------- CommitReceipt: a record, never an authorization ----------------
#[derive(Debug, Clone)]
pub struct CommitReceipt {
    pub target: String,
    pub previous: String,
    pub new: String,
    pub source: String,
    pub dependencies: Vec<String>,
    pub provenance_digest: String,
    // NOTE: there is deliberately no `allowed`/`authorized`/`permitted` field.
}

impl CommitReceipt {
    pub fn new(
        target: String,
        previous: String,
        new: String,
        source: String,
        dependencies: Vec<String>,
        provenance_digest: String,
    ) -> Result<Self, &'static str> {
        if provenance_digest.is_empty() {
            return Err("a CommitReceipt must carry a resolvable provenance digest (receipt, not authorization)");
        }
        Ok(CommitReceipt { target, previous, new, source, dependencies, provenance_digest })
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum CommitError {
    Severed,
}

#[derive(Debug)]
pub enum Resolution {
    Resolved(Vec<(String, String, String)>), // (source, previous, new) lineage
    Severed,
}

// ---------------- World: state as the consequence of an inspectable edit history ----------------
#[derive(Default)]
pub struct World {
    history: HashMap<String, Vec<Edit>>,
}

impl World {
    fn apply(&mut self, e: Edit) {
        self.history.entry(e.target.clone()).or_default().push(e);
    }
    fn orphaned(&self, e: &Edit) -> bool {
        match &e.depends_on {
            None => false,
            Some(d) => !self.history.values().flatten().any(|x| &x.digest() == d),
        }
    }
    pub fn value(&self, target: &str) -> Option<String> {
        let h = self.history.get(target)?;
        h.iter().filter(|e| !self.orphaned(e)).last().map(|e| e.new.clone())
    }
    pub fn provenance_of(&self, target: &str) -> Vec<(String, String, String)> {
        self.history
            .get(target)
            .map(|h| h.iter().map(|e| (e.source.clone(), e.previous.clone(), e.new.clone())).collect())
            .unwrap_or_default()
    }
    fn resolves(&self, digest: &str) -> bool {
        self.history.values().flatten().any(|e| e.digest() == digest)
    }
}

// ---------------- Query result ----------------
#[derive(Debug)]
pub struct QueryResult {
    pub existence: Existence,
    pub diagnosis: Option<String>,
    pub resolution_path: String,
}

impl QueryResult {
    pub fn diag_str(&self) -> &str {
        self.diagnosis.as_deref().unwrap_or("-")
    }
}

// ---------------- ResolvePath: inspection only, may drop, cannot advance state ----------------
pub struct ResolveRing {
    buf: Vec<Option<String>>,
    cap: usize,
    w: usize,
    r: usize,
    pub dropped: usize,
}

impl ResolveRing {
    pub fn new(cap: usize) -> Self {
        ResolveRing { buf: vec![None; cap], cap, w: 0, r: 0, dropped: 0 }
    }
    pub fn offer(&mut self, digest: String) -> bool {
        let n = (self.w + 1) % self.cap;
        if n == self.r {
            self.dropped += 1;
            return false;
        }
        self.buf[self.w] = Some(digest);
        self.w = n;
        true
    }
    pub fn poll(&mut self) -> Option<String> {
        if self.r == self.w {
            return None;
        }
        let d = self.buf[self.r].take();
        self.r = (self.r + 1) % self.cap;
        d
    }
    // NOTE: no apply() — the resolve path physically cannot advance world state.
}

// ---------------- Core: the kernel surface (single-consumer; the CommitPath authority) ----------------
pub struct Core {
    pub world: World,
    nonrecovery: HashMap<String, (Failure, Option<String>)>,
    pub refused: usize,
}

impl Core {
    pub fn new() -> Self {
        Core { world: World::default(), nonrecovery: HashMap::new(), refused: 0 }
    }

    /// The only path that advances state. Never drops; refuses an unresolvable prerequisite.
    pub fn apply(&mut self, ev: &Event, requires: Option<&str>) -> Result<CommitReceipt, CommitError> {
        if let Some(d) = requires {
            if !self.world.resolves(d) {
                self.refused += 1;
                return Err(CommitError::Severed);
            }
        }
        let survives = if ev.survival.is_empty() { None } else { Some(ev.survival.iter().all(|b| *b)) };
        let edit = Edit {
            target: ev.target.clone(),
            previous: ev.previous.clone(),
            new: ev.new.clone(),
            source: ev.source.clone(),
            depends_on: requires.map(|s| s.to_string()),
            survives,
        };
        let digest = edit.digest();
        self.world.apply(edit);
        CommitReceipt::new(
            ev.target.clone(),
            ev.previous.clone(),
            ev.new.clone(),
            ev.source.clone(),
            ev.dependencies.clone(),
            digest,
        )
        .map_err(|_| CommitError::Severed)
    }

    pub fn record_nonrecovery(&mut self, target: &str, case: Case, missing: Option<&str>) {
        self.nonrecovery
            .insert(target.into(), (diagnose(case), missing.map(|s| s.to_string())));
    }

    pub fn query(&self, target: &str) -> QueryResult {
        if self.world.history.contains_key(target) && self.world.value(target).is_some() {
            return QueryResult {
                existence: Existence::Present,
                diagnosis: None,
                resolution_path: "none_needed".into(),
            };
        }
        if let Some((f, missing)) = self.nonrecovery.get(target) {
            let existence = if f.is_absolute() { Existence::Absent } else { Existence::Unresolved };
            let resolution = match f {
                Failure::Severance | Failure::Indistinguishability => "none".to_string(),
                Failure::AssumptionLimit => {
                    format!("declare:{}", missing.clone().unwrap_or_else(|| "admissibility".into()))
                }
                Failure::ResourceLimit => "allocate".to_string(),
                Failure::Unclassified => "investigate".to_string(),
            };
            return QueryResult { existence, diagnosis: Some(f.name().to_string()), resolution_path: resolution };
        }
        QueryResult { existence: Existence::Unaccounted, diagnosis: None, resolution_path: "investigate".into() }
    }

    /// Resolve a digest to its lineage. Lineage is canonical (lives in `world`), not a deletable cache —
    /// so eviction can delay a resolve request, never erase the lineage (`compress ≠ sever`).
    pub fn resolve_digest(&self, digest: &str) -> Resolution {
        for h in self.world.history.values() {
            for e in h {
                if e.digest() == digest {
                    return Resolution::Resolved(self.world.provenance_of(&e.target));
                }
            }
        }
        Resolution::Severed
    }
}

impl Default for Core {
    fn default() -> Self {
        Core::new()
    }
}
