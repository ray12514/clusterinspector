# Architecture decisions

This file tracks high-impact decisions so implementation stays consistent as `clusterinspector` evolves.

## D-001: Single package, sibling commands

- Date: 2026-03-06
- Status: accepted

Decision:

- Keep one package (`clusterinspector`) with sibling commands: `fabric` and `profile`.

Rationale:

- Shared execution primitives and evidence models reduce duplicate behavior.
- Common packaging/CLI lowers operational overhead.
- Keeps profile and fabric outputs aligned for future integrations.

Consequences:

- Core APIs must remain stable and generic.
- Changes to common models require compatibility care for both commands.

## D-002: Read-only, non-root collection

- Date: 2026-03-06
- Status: accepted

Decision:

- All probes default to passive, read-only collection and must not require root.

Rationale:

- Safe to run across production fleets.
- Easier adoption on restricted HPC systems.

Consequences:

- Some validations are probabilistic rather than definitive.
- Health/impact logic must use cautious confidence labels.

## D-003: Evidence-first data flow

- Date: 2026-03-06
- Status: accepted

Decision:

- Probes emit normalized evidence; classifiers derive labels from evidence.

Rationale:

- Easier to explain outcomes.
- Supports machine and human outputs from same canonical model.

Consequences:

- Evidence codes/messages become API-like and should be versioned carefully.
- Classifier logic should avoid hidden implicit state.

## D-004: Graceful degradation by default

- Date: 2026-03-06
- Status: accepted

Decision:

- Missing tools, command failures, or single-node failures do not abort fleet scans.

Rationale:

- Real clusters are heterogeneous and partially constrained.
- Operator value comes from partial visibility, not all-or-nothing runs.

Consequences:

- Reports must encode partial/incomplete status cleanly.
- Exit codes should reflect failure categories without losing successful node data.

## D-005: Stable machine-readable output surface

- Date: 2026-03-06
- Status: accepted

Decision:

- Keep output fields stable once introduced; add new fields additively.

Rationale:

- Enables automation and long-lived downstream parsers.

Consequences:

- Deprecations should be explicit and staged.
- Schema/version docs are required as profile output matures.

## D-006: Build order favors usable increments

- Date: 2026-03-06
- Status: accepted

Decision:

- Deliver in phases: shared core, fabric MVP, fabric depth, profile MVP, profile depth.

Rationale:

- Provides immediate operator value.
- Limits integration risk while architecture is still evolving.

Consequences:

- Some modules remain scaffolded during early phases.
- Docs must clearly distinguish implemented vs planned behavior.
