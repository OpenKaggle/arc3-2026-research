# [2026-11] ARC Prize 2026 — ARC-AGI-3 clean-room campaign

> **Public clean-room snapshot — identity-blocked.** This repository preserves
> the policy, audit, and baseline-planning state recorded below. It contains no
> authorization to join, inspect private evaluation material, or make a
> competition submission.

Status at `2026-09-11T01:12:43Z`: identity-blocked planning snapshot —
**superseded on 2026-10-15: the line was SEALED after the preregistered local
baseline gate failed; the competition entry window closed on 2026-10-26 and no
Join ever occurred.**

The rules, local assets, contamination boundary, and a CPU-only baseline plan
have been audited. The logged-in Kaggle account has **not** joined this
competition. No competition data was downloaded, no evaluation answer was
opened, no submission was made, and no GPU was started.

The identity gate ([`docs/IDENTITY_GATE.md`](docs/IDENTITY_GATE.md)) is retained
below as an audit record of the planning state. With the entry window closed it
has no remaining operational effect.

## Current decision

**Terminal state: SEALED — gate failed as preregistered (2026-10-15); entry
window closed 2026-10-26, no Join occurred.**

- The local clean-room 24-hour baseline was executed against the preregistered
  gate. The R1 rerun **FAILED that gate**: the baseline completed **4 levels**
  in total versus **8 levels** for the uniform-random control anchor
  (`anchor_b`), so the preregistered requirement of scoring strictly above the
  best anchor was not met.
- Per the preregistered stop rule ("if baseline <= best anchor or 0 levels,
  the 24h gate fails and the line is sealed unless a protocol repair is
  justified"), the line was **sealed on 2026-10-15**. The single permitted
  repair (the ACTION6 coordinate-convention fix, baseline 3→4 levels) was
  applied and retested; no further repairs or 24-hour attempts were made.
- Gate integrity facts at seal were green (100% action legality, zero crashes,
  baseline p99 latency 12.81 ms, peak RSS 159.1 MiB); the gate failed only on
  the level-count comparison against the control anchor.
- The competition entry window closed on 2026-10-26. The account never joined:
  no competition data was downloaded, no submission was made, and no GPU was
  used on the competition.

Seal receipts (paths relative to this repository):

- [`receipts/24h_baseline/seal_24h_baseline_2026-10-15.json`](receipts/24h_baseline/seal_24h_baseline_2026-10-15.json)
  — R0 pre-fix run: baseline 3 levels vs anchor 8; sealed gate-failed.
- [`receipts/24h_baseline_r1/seal_r1_2026-10-15.json`](receipts/24h_baseline_r1/seal_r1_2026-10-15.json)
  — R1 rerun after the single-factor repair: baseline 4 levels, still at or
  below the 8-level anchor; verdict `SEALED_GATE_FAILED_AS_PREREGISTERED`.
- [`receipts/24h_baseline_r1/gate_fold_20261015T123234Z.json`](receipts/24h_baseline_r1/gate_fold_20261015T123234Z.json)
  — folded gate facts (`gate_result: FAILED_AS_PREREGISTERED`).
- [`receipts/24h_baseline_diagnosis_2026-10-15/R1_DECISION_2026-10-15.json`](receipts/24h_baseline_diagnosis_2026-10-15/R1_DECISION_2026-10-15.json)
  and [`docs/GATE_DIAGNOSIS_ACTION6_2026-10-15.md`](docs/GATE_DIAGNOSIS_ACTION6_2026-10-15.md)
  — diagnosis and decision record for the single repair factor.

## Documents

- [`docs/RULES_AUDIT.md`](docs/RULES_AUDIT.md) — binding terms, deadlines,
  conflicts, and conservative operating interpretation.
- [`docs/IDENTITY_GATE.md`](docs/IDENTITY_GATE.md) — facts that cannot be
  inferred and must be attested by the user.
- [`docs/MIGRATION_MATRIX.md`](docs/MIGRATION_MATRIX.md) — what may and may not
  move from `arc2_paper`.
- [`docs/BASELINE_PROTOCOL.md`](docs/BASELINE_PROTOCOL.md) — clean baseline,
  6/24/72-hour falsifiable milestones, budgets, stop rules, and first-submit
  gate.
- [`receipts/2026-09-11-source-snapshot.md`](receipts/2026-09-11-source-snapshot.md)
  — source and local-environment receipt.
- [`AUDIT_STATE.json`](AUDIT_STATE.json) — machine-readable fail-closed state.

## Non-negotiable boundaries

1. The runner's only future project root is this repository.
2. Nothing under the legacy denylist may be copied, mounted, symlinked,
   imported, or added to `PYTHONPATH`.
3. Only public ARC-AGI-3 material may enter development. Hidden evaluation
   inputs, frames, source, labels, replays, or inferred answers must never be
   inspected or exported.
4. Leaderboard feedback is reporting evidence, not a training label.
5. Every stage requires a frozen input/code/environment hash and authorization
   for one named action only.
6. A hash proves byte identity, not provenance or license; each external asset
   also needs source URL, version, access time, license, and public-access
   evidence.
