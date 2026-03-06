# ADR directory

Use this directory for decision records that need long-term traceability.

## Naming

- File format: `NNNN-short-title.md`
- Example: `0001-output-schema-stability.md`

## Workflow

1. Copy `docs/adr-template.md`
2. Fill in context, decision, alternatives, and rollout notes
3. Commit ADR with the related implementation change when possible

## Relationship to `docs/decisions.md`

- `docs/decisions.md` is a compact decision log.
- `docs/adr/` stores detailed, standalone records for major decisions.
