<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SHA-256 — stress audit of a "3-in-1" cryptanalysis proposal (Ursprung framework)

> **Security research on a public standard.** The question is not "let's break SHA-256" — it is *"does the
> proposed 3-in-1 method threaten full SHA-256, and where does each component's claim exceed its evidence?"* The
> deliverable is an audit, not an attack: it produces no working preimage/collision tool, and its honest
> conclusion is that full SHA-256 is **unbroken** and the proposal, as stated, is largely **undercommitted**.
> `declared ≠ verified`; strength is never upgraded; absence of evidence ≠ evidence of absence.

The proposal: **(1)** a SAT solver generates the foundation, **(2)** differential cryptanalysis corrects the SAT
path, **(3)** Hamming distances + genetic seeding close the loop, **(4)** a "reverse-Collatz-like counter."
Audited component by component below.

## 1. Observation layer — the MEASURED state of SHA-256 cryptanalysis

SHA-256 has **64 steps (rounds)**. Distinguish a *theoretical attack* (a published complexity below generic, but
never executed) from a *practical attack* (actually computed) — they are different provenance.

| Fact | Value | Provenance |
|---|---|---|
| Generic security (no structure) | collision 2¹²⁸ · preimage 2²⁵⁶ | `MEASURED` (definitional) |
| Best **collision** (reduced) | ~**31 of 64** steps (semi-free-start / reduced); practical differential collisions ~28–31 steps | `MEASURED` (published; mix of theoretical + practical) |
| Best **preimage** (reduced) | ~**45 of 64** steps, complexity **near 2²⁵⁶** (marginal advantage) | `MEASURED` (published, **theoretical** — not executed) |
| **SAT-based practical** preimage | ~**16–20 rounds** within a 24 h solve | `MEASURED` (executed) |
| **SAT/programmatic-SAT** collisions | reduced-step compression-function collisions (≈19 steps SAT; higher with programmatic SAT, still ≪ 64) | `MEASURED` (executed) |
| **Full 64-step** SHA-256 | **no attack better than generic** (collision or preimage) | `MEASURED` (the standing result) |

**Security margin:** roughly *half the function* is untouched — best collision reaches ~31/64, best preimage
~45/64 but only at ~brute-force cost. The published advances **do not threaten** applications using SHA-256.

## 2. The 3-in-1 method, graded component by component

### (1) SAT solver "generates the foundation" — `MEASURED` (reduced rounds) / `DECLARED` (for full)
- **What it really does:** encode the SHA-256 step function as CNF and ask a solver (MiniSat/CryptoMiniSat) for
  a satisfying assignment = a preimage. Real, published, and the *practical* state of the art for small
  round-counts.
- **Ceiling:** practical preimage stalls at **~16–20 rounds**; the CNF blows up and the search space is 2²⁵⁶ —
  a CDCL solver has no traction once diffusion is complete. **It does not "found" an attack on full SHA-256.**
- **Falsifier of the strong claim:** a SAT-found preimage/collision at 64 steps in feasible time. None exists.
- **Honest status:** the *committed* prediction of SAT cryptanalysis is "reduced rounds only" — which is exactly
  what is observed. As a foundation for full SHA-256 it is `DECLARED`-unsupported.

### (2) Differential cryptanalysis "corrects the SAT path" — `MEASURED` (reduced rounds); the most grounded part
- **What it really does:** find a differential characteristic (an input-difference → output-difference path of
  high probability) and use it to *constrain* the search — and **SAT + differential is already an established
  combination** (differential paths encoded into the SAT instance reduce the collision search; this is how
  reduced-round collisions are found).
- **Ceiling:** differential collision tops out ~**31 steps**; the characteristic probability collapses past that.
- **Falsifier:** a 64-step differential characteristic with usable probability. None published.
- **Honest status:** real, committed, and genuinely the strongest leg — but its committed prediction is *also*
  "reduced rounds." Combining (1)+(2) is not new and does not reach full SHA-256.

### (3) Hamming distances + genetic seeding "close the loop" — `DECLARED` → **refuted by diffusion**
- **What it claims:** treat preimage search as optimization — seed candidate messages, score them by Hamming
  distance to the target digest, evolve toward it (a genetic algorithm / hill-climb on the distance fitness).
- **Why it fails by design — and this is measurable (§4):** SHA-256's **avalanche/strict-diffusion** property
  means a one-bit input change flips ~half the output bits. So the fitness landscape (input-Hamming vs
  output-Hamming-to-target) is **flat and uncorrelated** — there is *no gradient* for a GA or hill-climb to
  exploit; "closer in input" tells you nothing about "closer in output." The hash is *built* to destroy exactly
  the local structure a Hamming-guided search needs.
- **Falsifier:** demonstrate input→output Hamming correlation in full SHA-256 (a gradient). The avalanche test
  (§4) measures the opposite.
- **Honest status:** not merely weak — **effectively refuted as a path to full preimage** by a property you can
  measure in seconds. No competitive GA/Hamming preimage results exist for SHA-2.

### (4) "Reverse-Collatz-like counter" — `UNDERCOMMITTED` → set aside (not refuted)
- **What it is:** not a recognized cryptanalytic technique; a coinage. The Collatz analogy is "reverse-iterate a
  map and enumerate predecessors."
- **Why it does not map:** SHA-256's compression is **not a reversible iterated map** you can cheaply
  enumerate backward — the message schedule injects 64 distinct 32-bit words and the Davies–Meyer feed-forward
  (`H = E(M, H_prev) ⊞ H_prev`) is one-way by construction; there is no "reverse counter" that inverts a step
  without solving the same hard problem. As stated it commits to **no falsifiable prediction**.
- **Honest status:** `UNDERCOMMITTED` — it specifies no `pred(do(x))`, so nothing can discriminate it. Per the
  discipline it is **set aside as non-discriminable, not declared impossible** (`absence of evidence ≠ evidence
  of absence`). To re-enter it must commit: *what, concretely, does the counter enumerate, at what cost, and
  what would prove it wrong?*
- **UPDATE — `UNDERCOMMITTED` → `FORMULATED & EXPOSED` → `TESTED`.** The coinage was subsequently committed: the
  round is modelled as a piecewise **2-adic affine map** branching on the modular-addition carry vector; the
  "counter" enumerates carry-propagation paths backward, taking the unique affine inverse per fixed carry and
  pruning carry-inconsistent branches. Falsifier committed: `Pr(carry-vector consistent | wrong branch) = ½ᵇ`
  ⇒ no structural gradient ⇒ refuted. This is now a real, discriminable hypothesis — tested by
  [`sha256_2adic_branch.py`](sha256_2adic_branch.py). Two corrections the audit imposes: **(A)** carries are not
  the only nonlinearity — **Ch/Maj are AND-based and nonlinear regardless of carries**, so fixing carries does
  *not* make the round affine and the true branching is *larger* than carry-only; **(B)** atomic carry survival
  ≠ ½ is the *expected, already-known* result (addition is structured — it is why SAT reaches ~16–20 rounds),
  so the decisive question is whether that local structure **compounds**, and `sha256_avalanche.py` already
  measured that it does not (cross-round decorrelation). **Verdict regime:** *local 2-adic gradient real,
  global compounding absent → `BOUNDED_TO_REDUCED_ROUNDS`* — never a break. The coinage is now an honest
  reduced-round structural probe, not a path to full SHA-256.

## 3. Commitment gate (the framework lens)

| Component | Commits a falsifiable prediction? | State | Action |
|---|---|---|---|
| (1) SAT foundation | yes — "reduced-round preimages, stalls ~16–20" | `COMMITTED` (and confirmed reduced-only) | known result; no path to 64 |
| (2) Differential correction | yes — "reduced-round collisions ~31" | `COMMITTED` (and confirmed reduced-only) | known result; SAT+diff already standard |
| (3) GA + Hamming | yes — "distance gradient guides search" | `COMMITTED` → **refuted** (avalanche kills the gradient) | drop as a full-preimage path |
| (4) reverse-Collatz counter | no | `UNDERCOMMITTED` | demand a concrete prediction or set aside |

**The bottleneck is the same one the framework keeps finding: prediction scarcity at the load-bearing joint.**
The components that commit (1, 2) commit only to *reduced-round* results; the component that would have to do the
*new* work to reach 64 (4) commits to nothing, and (3) commits to something the hash is designed to defeat. The
"break" lives entirely in the undercommitted/refuted parts.

## 4. The one genuinely measurable stress test — diffusion / avalanche

The honest empirical "stress test" of SHA-256 you can actually run is its **diffusion**, and it is also the thing
that refutes component (3). Flip one input bit; measure the output Hamming distance to the original digest. For a
strong hash the distribution is **Binomial(256, ½)** — mean **128**, std ≈ 8 — i.e. a single-bit change is
indistinguishable from a random re-hash.

A standalone, dependency-free harness is provided: [`sha256_avalanche.py`](sha256_avalanche.py) (run it; it uses
`hashlib`, executes no attack, and is a textbook diffusion measurement). Expected, honest outcome: mean ≈ 128,
no input-bit position privileged, **no input→output Hamming correlation** — which is `MEASURED` evidence that the
fitness landscape a GA/Hamming search would climb does not exist. (Confirming strong diffusion is *not* a
vulnerability finding; it is the positive control that a good hash must pass.)

## 5. Failure-mode mapping (where the "break" claim actually sits)

- **The break is `OCCLUDED`/undercommitted at its core.** The work that would reach full rounds is assigned to
  the parts that don't specify a mechanism (the Collatz counter) or that diffusion defeats (GA/Hamming) — the
  cryptographic analog of attributing the result to an unobservable interior variable.
- **`INTERVENTION_ONLY` for the strong claim.** No observation short of *actually executing a 64-step attack*
  discriminates "this will scale to 64" from "it won't" — and that execution is infeasible (2¹²⁸/2²⁵⁶). So the
  scaling claim is not testable by argument; the burden is a demonstrated full-round result.
- **Not `FLOODED`, not `NON_ORIENTABLE`** — those axes don't apply here; assigning them would be over-reach.

## 6. What would falsify "the 3-in-1 breaks SHA-256"

A single, concrete result: **a preimage or collision on full 64-step SHA-256 at complexity below the generic
bound (2²⁵⁶ / 2¹²⁸), produced by the method.** That is the only thing that converts the claim from `DECLARED` to
`MEASURED_BY_INTERVENTION`. Everything short of it — reduced-round successes, heuristic seeding, a clever
counter — is consistent with SHA-256 remaining secure, and the published record shows the component techniques
saturate near half the rounds.

## 7. Honest verdict and the highest-value next step

**Verdict:** full SHA-256 is unbroken; the 3-in-1, as stated, does not change that. Its two grounded legs
(SAT, differential) are real but reduced-round-bounded; its loop-closer (GA/Hamming) is refuted by the hash's
own diffusion; its novel element (reverse-Collatz counter) is undercommitted and, where interpretable, does not
map to SHA-256's one-way structure.

**Highest-value next step — and it is *not* "run the 3-in-1 on full SHA-256":**
1. **Run the avalanche harness** (§4) — cheap, confirms diffusion, and demonstrates *why* the GA/Hamming leg
   cannot work. (`MEASURED`.)
2. **Force component (4) to commit** a concrete, falsifiable prediction (`pred(do(x))`) — what the counter
   enumerates and at what cost — or set it aside. This is the cheap commitment-gate move; until it commits,
   there is nothing to test.
3. **Test (1)+(2) at the round-count where they are tractable** (~16–31 steps) to *reproduce* the published
   ceiling — honest, runnable, and it quantifies the margin rather than pretending to cross it.

The defensible one-line: *the proposal is a real reduced-round pipeline wearing a full-break claim; the break
lives in the parts that commit to nothing, and the one thing you can measure (avalanche) is the reason the
heuristic leg fails.* `declared ≠ verified`; reduced-round ≠ full; heuristic-seeded ≠ gradient-bearing;
undercommitted ≠ impossible.

## Sources

- *Attacking Reduced Round SHA-256* — [ResearchGate](https://www.researchgate.net/publication/220335111_Attacking_Reduced_Round_SHA-256)
- Khovratovich/Aoki et al., preimage attacks on reduced SHA-2 — *Preimage Attacks on 41-Step SHA-256 and 46-Step SHA-512* — [ResearchGate](https://www.researchgate.net/publication/220332897_Preimage_Attacks_on_41-Step_SHA-256_and_46-Step_SHA-512)
- Mendel, Nad, Schläffer, *Improving Local Collisions: New Attacks on Reduced SHA-256* — [IACR eprint 2015/350](https://eprint.iacr.org/2015/350.pdf)
- *SHA-256 Collision Attack with Programmatic SAT* — [arXiv 2406.20072](https://arxiv.org/html/2406.20072v1)
- SAT-based preimage attacks on SHA-256 (CryptoMiniSat encodings) — [cryptosym / preimage-attacks (GitHub)](https://github.com/trevphil/preimage-attacks) · *CDCL(Crypto) SAT Solvers for Cryptanalysis* — [arXiv 2005.13415](https://ar5iv.labs.arxiv.org/html/2005.13415)
- F. Mendel, *Analysis of Cryptographic Hash Functions* (PhD thesis, SHA-2 differential cryptanalysis) — [TU Graz](https://diglib.tugraz.at/download.php?id=576a7a85b2dc5&location=browse)
