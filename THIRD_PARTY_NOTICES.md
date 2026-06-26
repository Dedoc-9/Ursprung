<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# THIRD-PARTY NOTICES

This file lists third-party components **distributed inside this repository** and their licenses, as
required by those licenses. The project as a whole is licensed **AGPL-3.0-only** (see `LICENSE` and
`NOTICE`); the components below retain their own licenses and copyright notices.

> Decisions about *whether* to vendor, interoperate with, or reimplement a given project are recorded
> in [docs/LICENSE_DECISIONS.md](docs/LICENSE_DECISIONS.md). Subsystem authorship and clean-room notes
> are in [docs/PROVENANCE.md](docs/PROVENANCE.md).

## Currently vendored components

**None.** As of this writing, no third-party source is vendored into the tree. All code is original
(see `docs/PROVENANCE.md`). Runtime dependencies (e.g. `three.js` in the HTML views) are loaded from
their own CDNs/package sources and are not copied into this repository.

The Reality_Engine workbench is **imported read-only** and is **not** vendored (see `NOTICE`, "Sibling
Law"); it is therefore not a third-party component distributed here.

## Template — add an entry here before vendoring any component

When (and only when) permissive source is copied into the tree, add a block like the following in the
same commit, keep the component's `LICENSE`/`NOTICE` files alongside its source, and state any changes:

```
### <Component name> — <version / commit>
Upstream:   <repository URL>
License:    Apache-2.0   (SPDX: Apache-2.0)
Copyright:  <upstream copyright line(s)>
Location:   <path/in/this/repo>
Modified:   <yes/no — if yes, summarize changes, as Apache-2.0 §4(b) requires>
NOTICE:     <reproduce upstream NOTICE text, or path to the preserved NOTICE file>
```

### Eligibility reminder (see docs/LICENSE_DECISIONS.md for the full rules)

- **Permissive only (Apache-2.0 / BSD / MIT):** may be vendored. Preserve notices; state changes.
- **NOSA (NASA Open Source Agreement):** GPL/AGPL-incompatible — **must not be vendored**; reimplement
  the published idea clean-room instead.
- Vendoring copyleft/GPL-incompatible code would also forfeit the repository's ability to offer a
  future commercial/dual license, so it is disallowed by policy here, not only by law.

## Pre-cleared upstreams (Apache-2.0 — verified, not yet vendored)

These are confirmed Apache-2.0 and therefore eligible to vendor if a concrete need arises. Listing them
here is informational; an actual entry must be added above at the moment source is copied.

- **Open MCT** — https://github.com/nasa/openmct — Apache-2.0
- **NASA Ames Stereo Pipeline** — https://github.com/NeoGeographyToolkit/StereoPipeline — Apache-2.0
- **GMAT** (current releases) — https://github.com/nasa/GMAT — Apache-2.0
- **Java Pathfinder** — https://github.com/javapathfinder/jpf-core — Apache-2.0
- **Core Flight System** components (`cFE`, `osal`, `psp`, `SBN`, app repos) — https://github.com/nasa —
  Apache-2.0 **per repository; verify the specific repo + commit** (the 2015 bundle and some older
  branches were NOSA).
