// SPDX-License-Identifier: AGPL-3.0-only
//! Integration test: both orchestrator chokepoints, end to end, through the public API only.
//! Validity-not-outcome — we assert the apparatus, not a hoped result.

use ursprung::*;

#[test]
fn answer_chokepoint_is_honest() {
    let o = default_orchestrator();
    let samples = demo_gen_channel(4000, 3, 2);
    let a = o
        .analyze("residual_channel", &Request::Residual { samples, reps: 60, seed: 0 })
        .expect("registered tool");
    assert_eq!(a.scope(), "conditional-dependence");
    assert!(!a.limitations().is_empty(), "honesty travels with the result");
}

#[test]
fn action_chokepoint_refuses_unstressed_residual() {
    // a bare audit (no mis-spec stress) of a real channel is RESIDUAL_DEPENDENCE, NOT mis-spec-stable —
    // so ChannelEstablished must refuse to promote it. residual-CMI != channel.
    let samples = demo_gen_channel(4000, 3, 2);
    let r = audit(&samples, 60, 0, 4.0, 0.005, &[]);
    assert_eq!(r.decision, ChannelDecision::ResidualDependence);
    let proof = ChannelEstablished { decision: r.decision };
    let gated = enact((), &proof, |_| "promoted");
    assert!(gated.is_err(), "an unstressed residual must not be promotable");
}

#[test]
fn action_chokepoint_certifies_clean() {
    // a confounder-explained (null) stream is CONSISTENT_WITH_NULL ⇒ NoHiddenChannel grounds a clean-cert.
    let samples = demo_gen_null(4000, 3, 1);
    let r = audit(&samples, 60, 0, 4.0, 0.005, &[]);
    assert_eq!(r.decision, ChannelDecision::ConsistentWithNull);
    let proof = NoHiddenChannel { decision: r.decision };
    let out = enact("telemetry", &proof, |t| format!("certified:{t}"));
    assert_eq!(out.unwrap(), "certified:telemetry");
}

#[test]
fn panel_stays_plural() {
    let o = default_orchestrator();
    let calls = vec![
        ("frontier_gate".to_string(), Request::Frontier { m_novel: 0.5, ci: (0.3, 0.8) }),
        ("residual_channel".to_string(), Request::Residual { samples: demo_gen_null(2000, 3, 7), reps: 40, seed: 0 }),
    ];
    let panel = o.panel(&calls);
    assert_eq!(panel.len(), 2, "one witness per call, reported side by side");
}
