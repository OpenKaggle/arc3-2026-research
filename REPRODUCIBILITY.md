# Reproducibility guide

## Snapshot purpose

This is an identity-blocked clean-room planning snapshot. It supports review of
the policy boundary, source inventory, identity gate, migration rules, and
baseline protocol. It does not contain competition/private/evaluation data and
does not authorize joining, downloading data, running private evaluation, or
submitting.

## Review sequence

1. Read `docs/IDENTITY_GATE.md`; an unresolved gate remains unresolved.
2. Read `docs/RULES_AUDIT.md` for the historical rule interpretation.
3. Read `docs/MIGRATION_MATRIX.md` before moving any prior ARC material.
4. Read `docs/BASELINE_PROTOCOL.md` for the clean CPU-only milestones.
5. Inspect `AUDIT_STATE.json`, `manifests/denylist.txt`, and
   `manifests/official_source_heads.json` as fail-closed evidence records.

No root README documents a supported executable baseline command, so this
release does not invent one. Reproduction stops at document and evidence review
until the identity gate is satisfied and the authorized public inputs are
acquired under their own terms.

## Historical manifest note

`MANIFEST.sha256` binds the source snapshot recorded before these public-release
metadata files and README status banner were added. It is retained as historical
evidence, not regenerated as a current whole-repository manifest; its README
entry will therefore not match the release copy. Validate it only against the
historical snapshot it describes.

Hashes prove byte identity, not provenance, licensing, or clean-room
eligibility. See `NOTICE.md` for the third-party boundary.
