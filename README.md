# [2026-11] ARC Prize 2026 — ARC-AGI-3 clean-room campaign

> **Public clean-room snapshot — identity-blocked.** This repository preserves
> the policy, audit, and baseline-planning state recorded below. It contains no
> authorization to join, inspect private evaluation material, or make a
> competition submission.

Status at `2026-09-11T01:12:43Z`: **conditional GO, identity-blocked**.

The rules, local assets, contamination boundary, and a CPU-only baseline plan
have been audited. The logged-in Kaggle account has **not** joined this
competition. No competition data was downloaded, no evaluation answer was
opened, no submission was made, and no GPU was started.

The only authorized next step is completion of
[`docs/IDENTITY_GATE.md`](docs/IDENTITY_GATE.md). Joining remains blocked until
the required personal facts are supplied by the account holder and pass that
gate.

## Current decision

- **Legally/operationally feasible:** yes, subject to the identity and IP gate.
- **Prize feasibility:** unproven. The live public leaderboard snapshot had a
  first-place score of `11.04` and third-place score of `7.63`; a fresh system
  has no evidence yet that it can approach those scores.
- **Milestone 2 feasibility:** time remains until `2026-09-30 23:59 UTC`, but
  no prize claim is justified until a public, reproducible, license-clean
  notebook and a non-trivial sealed local result exist.
- **Compute posture:** CPU only. GPU, Kaggle submission, and private-evaluation
  reruns are separately gated.

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
