# Clean CPU baseline and falsifiable campaign plan

## Baseline architecture

The first baseline is a deterministic, model-free state machine:

```text
official adapter
  -> fail-closed frame/action validation
  -> multi-frame delta and generic object candidates
  -> legal-action generator
  -> short-horizon novelty/state-graph planner
  -> global budget guard
  -> chained trajectory receipt
```

It must:

- read `available_actions` on every step and never assume fixed semantics for
  `ACTION1..ACTION7`;
- accept one or multiple frames, shapes up to `64x64`, values `0..15`, and
  hash every raw frame before any derived representation;
- generate `ACTION6` coordinates only from explainable candidates such as
  component centers, endpoints, rare-color objects, and change frontiers;
- allow only `RESET` after `GAME_OVER` and use `ACTION7` only when currently
  legal;
- store a state graph keyed by frame/metadata hashes, block repeated no-op
  `(state, action)` pairs, and prefer novel/reversible transitions;
- be seeded by a stable digest, never wall-clock time or Python's randomized
  `hash()`;
- contain no game-ID branch, per-game hand rule, ARC-2 import, remote model API,
  or leaderboard-conditioned threshold;
- use a configurable `8h15m` hard stop inside Kaggle, reserving 45 minutes for
  orderly shutdown and generated output under the official 9-hour limit.

The trivial controls are (A) one fixed legal action and (B) uniformly random
legal actions with a stable seed. They are controls only, not submission
candidates.

## Public-development and sealed split

After identity approval and a separately authorized acquisition step, freeze
the exact Kaggle public-file manifest before opening environment source or
running a game. Group strictly by game ID; levels, variants, and seeds from one
game can never cross partitions.

The split algorithm is frozen now:

```text
salt = "arc3-cleanroom-split-v1|2026-09-11"
key(game_id) = SHA256(salt + "|" + game_id)
sort ascending by key
first 15  -> authoring
next 5    -> validation
last 5    -> sealed one-shot audit
```

Do not calculate or reveal sealed assignments until the files are placed in a
runner-inaccessible evaluator vault. The policy author must not view sealed
frames, environment code, replays, or per-game results. The evaluator returns
only aggregate score/progress, legality/crash counts, wall time, memory, and
artifact hashes. Any observed sealed content permanently contaminates that
split; re-shuffling does not repair it.

## 6 / 24 / 72-hour milestones

| Timebox | Falsifiable deliverable and pass condition | Maximum cost | Stop condition |
|---|---|---|---|
| 6 hours | Freeze official source/version/license/hash receipts; clean Git repo and lockfile; synthetic mock engine; tests for multi-frame input, shape/value bounds, dynamic actions, ACTION6 boundaries, GAME_OVER, no-op, deadline; 10,000 synthetic steps with 0 illegal actions; two same-seed runs have identical trajectory hashes; 0 denylist accesses | 2 aggregate CPU-hours, 1 GiB, GPU 0, cloud/API `$0` | Cannot establish license/version; holdout not frozen before content access; any legacy/hidden read; nondeterministic replay |
| 24 hours | CPU baseline on authoring/validation public games; 100% legal actions, 0 crashes, correct terminal handling; paired against both trivial anchors; at least one completed level and aggregate official local result strictly above the best trivial anchor; p99 policy latency target `<100 ms/step`, peak RSS `<512 MiB` | 24 aggregate CPU-hours, cumulative 2 GiB, GPU 0, `$0` | One protocol repair still leaves illegal/crashing behavior; two preregistered single-factor policies yield zero progress; improvement requires viewing sealed content |
| 72 hours | Freeze policy, then exactly one sealed audit; nonzero progress on at least one never-authored game and, if all 5 run, at least two; aggregate beats best trivial anchor; `legality-only -> delta/object -> planner` single-factor ablation; offline/no-network Phase-A dry run; 8h15 stress guard exits cleanly; release/dependency/secret/IP audits green | 120 aggregate CPU-hours, cumulative 5 GiB, GPU 0 by default | Sealed zero progress or loses to trivial anchor; predicted runtime exceeds 8h15; license/IP cannot be published; hash drift, game override, hidden/leaderboard feedback used for tuning |

Disk currently has roughly `58 GiB` free at `94%` utilization. The campaign
must stay below `5 GiB` net new storage and preserve at least `20 GiB` free.
The old `~8.9 GiB` ARC-2 tree is not duplicated.

Only after the 72-hour gate passes and the user issues a separate, one-action
authorization may a single accelerator smoke of at most one accelerator-hour
or 10% of available quota be considered. No purchase is implied or authorized.

## Minimum first-submission gate

All ten conditions must be true:

1. Identity, residence, sanctions, employer/entity, competition-entity,
   account/team, IP, publication, award, and tax facts are attested.
2. Current Rules, starter, competition engine, public data, dependencies,
   licenses, URLs, versions, byte sizes, and hashes are frozen from first-party
   sources.
3. Repository is clean; dependency lock and package hashes are complete; the
   runtime records zero access to legacy denied paths.
4. Public validation and sealed audit both show 100% legal actions, 0 crashes,
   correct terminal behavior, and deterministic replays.
5. Sealed aggregate shows nonzero progress and beats the best trivial anchor.
6. The 8h15 global guard and failure/interrupt/output finalization paths pass a
   stress test.
7. Notebook has internet off, no secrets/absolute user paths/cell outputs, and
   its generated `submission.parquet` passes the official starter checks.
8. Every releasable code/model/data artifact passes public-access, license,
   training-provenance, and winner-disclosure review.
9. Policy, inputs, code, environment, and notebook are frozen and hash-bound;
   the user authorizes one specific Phase-B rerun/submission only.
10. Leaderboard feedback is recorded after the run but never selects or tunes
    the next policy.

Passing this gate permits one cheap submission. It does not permit a GPU run,
second submission, team merge, public release, or prize claim.

## Receipt contract

Canonical JSON receipts will use UTF-8 with sorted keys and compact separators
until an RFC 8785 implementation is pinned. Every receipt binds:

- `schema_version`, UTC timestamp, and previous-receipt SHA-256;
- Git commit and dirty-patch hash;
- input, dependency-lock, engine, starter, policy, and notebook hashes;
- stable seed, single changed variable, compute/action/time/memory limits;
- stage, one authorized action, terminal status, and claim boundary;
- source URL/version/license/access time for each external asset.

Each trajectory step binds an episode pseudonym, step number, hashes for every
returned frame and metadata, available-action hash, chosen action/coordinates,
response hash, terminal state, cumulative wall time, and prior-step hash.
Hidden evaluation stores only permitted aggregate observations and artifact
hashes, never raw frames or inferred answers.
