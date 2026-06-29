// SPDX-License-Identifier: AGPL-3.0-only
//! Runnable demo of the Ursprung fundamentals: `cargo run --example chokepoints`.

use ursprung::*;

fn main() {
    let o = default_orchestrator();
    println!("Ursprung fundamentals (Rust) — orchestrator tools: {:?}\n", o.tool_names());

    // ANSWER chokepoint — a panel of witnesses, side by side, no fused scalar
    let calls = vec![
        ("frontier_gate".to_string(), Request::Frontier { m_novel: 0.5, ci: (0.3, 0.8) }),
        ("claim_ledger".to_string(), Request::Ledger {
            claims: vec![Claim::new(
                "D1", "the engine reproduces", Grade::Established, "replay", "the magnitude", "a failed replay",
            )],
        }),
    ];
    for (name, res) in o.panel(&calls) {
        match res {
            Ok(a) => println!("  [{name}] scope={:?} findings={} limitations={}",
                              a.scope(), a.findings().len(), a.limitations().len()),
            Err(e) => println!("  [{name}] ERROR {e}"),
        }
    }

    // residual-channel diagnostic: a real channel vs a confounder-only null
    let chan = audit_default(&demo_gen_channel(4000, 3, 2));
    let null = audit_default(&demo_gen_null(4000, 3, 1));
    println!("\n  channel stream decision: {}", chan.decision.as_str());
    println!("  null    stream decision: {}", null.decision.as_str());

    // ACTION chokepoint — certify the clean stream; an ungrounded value is refused before any effect
    let proof = NoHiddenChannel { decision: null.decision };
    match enact("telemetry", &proof, |t| format!("certified controller-safe: {t}")) {
        Ok(s) => println!("  enact → {s}"),
        Err(e) => println!("  enact refused → {e}"),
    }
    println!("\n  router != verifier; grounded != true; integrity != truth.");
}
