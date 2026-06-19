# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/conventions.py — the Arbitrary-Boundary Law + the Boundary Ledger, encoded as data.

THE LAW (the renderer's `integrity ≠ truth`):

    Arbitrary boundaries require deterministic handling, not claims of truth.

The discretization hierarchy that produces these boundaries:

    Reality / intended domain
        → Model assumptions
            → Discrete representation
                → Implementation
                    → Rendered / measured output

Each downward step introduces necessary choices — grid size, tick rate, float format, sampling pattern,
culling threshold, compression scheme, cache strategy, interpolation method. The choices are necessary; the
mistake is treating them as discoveries. The engineering rule:

    When symmetry is impossible, choose a deterministic asymmetry and record it.

    determinism → integrity of PROCESS      (the same convention yields the same result)
    determinism ↛ correctness of OUTCOME     (the convention is a choice, not a law of nature)

A `Convention` (a Boundary-Ledger entry) makes one such choice explicit and content-addressed, carrying its
purpose, the chosen convention, the rejected alternatives (a failed branch carries architectural
information), the reason it was selected, and the deterministic rule (the mechanical tie-break). Every entry
asserts `truth_claim = False` by construction. The engine can then answer "why does this pixel belong to
this triangle?" with *"because this renderer's coverage convention assigns it that way"* — never *"because
that is reality."*

CLASSIFICATION: OBSERVER (mutates_core=False). It declares and reports choices; it changes no committed state.

HONEST BOUND: declaring a convention makes the choice reproducible and auditable — it does not make the
choice *right*. integrity ≠ truth.
"""
from __future__ import annotations

from .render_record import canon_hash
from . import ghost_report as gr

# Origin vocabulary extension: a ghost whose cause is a declared boundary choice (NOT an error).
BOUNDARY_CHOICE = "boundary_choice"

# Domains where arbitrary boundaries arise in a renderer.
RASTERIZATION = "rasterization"
FLOATING_POINT = "floating_point"
LOD = "lod"
TICK = "tick"
CULLING = "culling"
COLOR = "color"
DOMAINS = (RASTERIZATION, FLOATING_POINT, LOD, TICK, CULLING, COLOR)


class Convention:
    """A Boundary-Ledger entry: an explicit, deterministic, content-addressed arbitrary choice.

    Fields (the Boundary Ledger schema):
        name               : identifier
        purpose            : what discretization problem this choice resolves
        domain             : one of DOMAINS
        convention (rule)  : the chosen convention, stated plainly
        alternatives       : rejected alternatives (preserved — failed branches carry information)
        selected_reason    : why THIS choice (never why it is "true")
        deterministic_rule : the mechanical rule / tie-break that makes it reproducible
        truth_claim        : always False (invariant)
    """
    __slots__ = ("name", "domain", "rule", "purpose", "selected_reason", "deterministic_rule",
                 "alternatives_rejected", "truth_claim")

    def __init__(self, name, domain, rule, purpose="", selected_reason="", deterministic_rule="",
                 alternatives_rejected=()):
        self.name = name
        self.domain = domain
        self.rule = rule                                   # the chosen convention (a.k.a. "convention")
        self.purpose = purpose
        self.selected_reason = selected_reason
        self.deterministic_rule = deterministic_rule or rule
        self.alternatives_rejected = list(alternatives_rejected)
        self.truth_claim = False                           # invariant: a convention is never a truth claim

    # backward-compatible alias
    @property
    def rationale(self):
        return self.selected_reason

    @property
    def not_a_truth_claim(self):
        return not self.truth_claim

    def hash(self):
        """Stable identity of the CHOICE. Changing the chosen convention or its deterministic rule changes
        the identity — like a deliberate ruleset version bump on the workbench."""
        return canon_hash({"name": self.name, "domain": self.domain, "rule": self.rule,
                           "deterministic_rule": self.deterministic_rule})

    def explain(self, subject="this sample", obj="this primitive"):
        """Answer 'why does <subject> belong to <obj>?' the honest way: by convention, not by reality."""
        return ("%s is assigned to %s because the '%s' convention (%s) maps it that way under the rule: %s. "
                "This is a deterministic choice, not a claim about reality (truth_claim=false)."
                % (subject, obj, self.name, self.hash()[:8], self.deterministic_rule))

    def as_dict(self):
        return {"name": self.name, "domain": self.domain, "convention": self.rule, "purpose": self.purpose,
                "selected_reason": self.selected_reason, "deterministic_rule": self.deterministic_rule,
                "alternatives": self.alternatives_rejected, "truth_claim": False, "hash": self.hash()}

    def __repr__(self):
        return "<Convention %s [%s] %s>" % (self.name, self.domain, self.hash()[:8])


class ConventionLedger:
    """The Boundary Ledger: the set of arbitrary choices a renderer build commits to. Its digest is a single
    content address for 'which conventions this build used' — pin it into a render Verification Record."""

    def __init__(self):
        self._by_name = {}

    def declare(self, name, domain, rule, purpose="", selected_reason="", deterministic_rule="",
                alternatives_rejected=()):
        if domain not in DOMAINS:
            raise ValueError("unknown convention domain %r (expected %r)" % (domain, DOMAINS))
        c = Convention(name, domain, rule, purpose, selected_reason, deterministic_rule, alternatives_rejected)
        self._by_name[name] = c
        return c

    def get(self, name):
        return self._by_name[name]

    def all(self):
        return [self._by_name[k] for k in sorted(self._by_name)]

    def by_domain(self, domain):
        return [c for c in self.all() if c.domain == domain]

    def digest(self):
        """Content address of the whole Boundary Ledger — the 'convention id' of a build."""
        return canon_hash([c.as_dict() for c in self.all()])


def boundary_ghost(convention, detail, category=None, magnitude=None):
    """Tag an observed artifact as the footprint of a declared boundary choice — an attention signal that
    says 'this is expected structure from convention X', not an error. The right question follows: 'is this
    acceptable for the intended purpose?'"""
    cat = category or _domain_category(convention.domain)
    return gr.Ghost(cat, BOUNDARY_CHOICE,
                    "%s — footprint of convention '%s' (%s); not an error, evaluate for purpose"
                    % (detail, convention.name, convention.hash()[:8]), magnitude=magnitude)


def _domain_category(domain):
    return {
        RASTERIZATION: gr.SPATIAL, FLOATING_POINT: gr.NUMERICAL, LOD: gr.PERCEPTUAL,
        TICK: gr.TEMPORAL, CULLING: gr.PERCEPTUAL, COLOR: gr.PERCEPTUAL,
    }.get(domain, gr.PERCEPTUAL)


# --- the canonical Ursprung conventions (the four examples, made explicit) --------------------------

def default_ledger():
    """Seed the Boundary Ledger with Ursprung's foundational choices. Each is a CONVENTION, not a law of
    nature; each is deterministic; each preserves the alternatives it rejected."""
    L = ConventionLedger()
    L.declare(
        "pixel_coverage", RASTERIZATION,
        rule="a triangle covers a pixel iff the pixel center is inside it, with a top-left fill rule on edges",
        purpose="assign continuous geometry to discrete pixels when an edge falls between samples",
        selected_reason="reproducible, watertight edge assignment (no double-/un-covered pixels on shared edges)",
        deterministic_rule="sample at pixel center; on an exactly-on-edge tie, cover iff the edge is a top or "
                           "left edge of the triangle",
        alternatives_rejected=["any-coverage (touch ⇒ shade)", "centroid sampling", "MSAA-only coverage"])
    L.declare(
        "float_representation", FLOATING_POINT,
        rule="committed CORE state is integer/fixed-point (never float); VIEW math is float64; VIEW artifacts "
             "are compared cross-machine after canonicalizing floats to 12 significant figures",
        purpose="GPU/parallel reductions can associate differently across hardware",
        selected_reason="define the representation and accept its bounded behavior rather than chase 'the one "
                        "true float ordering'",
        deterministic_rule="format(x, '.12g') before any cross-machine compare or record hash",
        alternatives_rejected=["assume IEEE associativity across hardware", "pin a single reduction order"])
    L.declare(
        "lod_threshold", LOD,
        rule="LOD swap distances are explicit authored config bands, hashed into the renderer_config_hash",
        purpose="choose where a mesh changes detail level",
        selected_reason="the swap distance is a human/model choice, not a law of nature; making it explicit "
                        "lets us test its artifacts (the pop) deterministically",
        deterministic_rule="band index = first i where distance < bands[i]; ties resolve to the higher detail",
        alternatives_rejected=["per-frame adaptive float threshold", "screen-coverage-only auto LOD"])
    L.declare(
        "tick_rate", TICK,
        rule="an integer truth-tick (e.g. 120 Hz) is authoritative; render frames interpolate between ticks",
        purpose="sample a continuous system at a discrete cadence",
        selected_reason="the tick is a reproducible approximation layer, not reality; decoupling it from the "
                        "frame rate keeps determinism while presentation varies (see lockstep)",
        deterministic_rule="truth advances in integer tick indices; frame f maps to n + rem/den, lerp is "
                           "integer-exact",
        alternatives_rejected=["variable wall-clock dt integration", "frame-rate-coupled simulation"])
    return L


# A module-level Boundary Ledger callers can pin / extend.
LEDGER = default_ledger()


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("conventions", OBSERVER, mutates_core=False,
                          note="the Boundary Ledger — declares arbitrary boundary choices explicitly + "
                               "deterministically (the Arbitrary-Boundary Law); never a truth claim")
    except LayerViolation:
        pass
