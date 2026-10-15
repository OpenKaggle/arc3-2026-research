# 24h Gate Failure — Diagnosis & R1 Decision (2026-10-15)

Status: **R1 single-factor protocol repair APPROVED; gate re-run in progress**
(local-only; no join; no submission; anonymous public envs only).

## 1. Outcome recap (F)
The pre-registered 24h baseline gate **FAILED as preregistered**: baseline 3 levels
(sp80, cd82, lp85 ×1) vs best trivial anchor (uniform random) 8 levels;
`strictly_above_best_anchor=false`. Integrity was green (100% legal, 0 crashes,
p99=4.42 ms, RSS=134.2 MB). Receipts: `receipts/24h_baseline/baseline_24h_result.json`
(sha `387bd8ed…`), `gate_fold_2026-10-15.json`.

## 2. Defect found (F) — ACTION6 payload transposed
`starter/agent/baseline_v2.py` built click candidates as **(row, col) = (y, x)** tuples
from the frame array, but the ACTION6 block unpacked them as `x, y = t[…]` and sent
`{"x": row, "y": col}`. The engine convention is **`{"x": col, "y": row}`**
(x = column, y = row, (0,0) top-left), so **every explainable click landed on the
transposed pixel**.

Engine-source chain (verified in the vendored packages):
- `arcengine/camera.py::_raw_render` places sprite pixels at `output[sprite.y+py, sprite.x+px]`;
  `display_to_grid(display_x, display_y) -> (grid_x, grid_y)` with x=column.
- `arcengine/level.py::get_sprite_at` uses `x>=sprite.x, y>=sprite.y` and indexes
  `pixels[y-sprite.y][x-sprite.x]`.
- `arcengine/base_game.py` generates its own valid ACTION6 clicks as
  `{"x": (sprite.x+px)*scale+x_offset, "y": (sprite.y+py)*scale+y_offset}`;
  the agent-visible frame is `camera.render()` → `frame[row=y][col=x]`.

Live evidence (`receipts/24h_baseline_diagnosis_2026-10-15/`, all local, read-only):
- `action6_probe_static…json` (sha `2e536dc4…`): 4/4 click-capable games (sp80, m0r0,
  ar25, lp85) — the correct payload resolves to the clickable sprite and is in the
  engine's valid-click set; the transposed payload resolves to `None`.
- `action6_probe_replay…json` (sha `ac66d079…`): pre-fix deterministic replay —
  **100 % of sampled ACTION6 sends were transposed**; ACTION6 usage: lp85 **1.000/step**
  (click-dominant game), sp80 0.0125, cd82 0.0017.
- `r1_fix_verify…json` (sha `4eb70b71…`): post-fix, `sent==(col,row)` 22/22 (sp80) and
  1500/1500 (lp85); intended pixel is non-background 95.5 % / 86.1 % of the time;
  **pre-fix, the payload landed on the intended pixel only 45.5 % / 33.5 %** of the time.

## 3. Interpretation (I)
The transposition is a mechanical convention bug, not a policy-design weakness. It is
sufficient to explain why click-driven progress underperformed for a policy whose
explainable-click machinery was its differentiator. It does **not** by itself prove the
fixed policy beats the uniform-random anchor — the re-run decides.

## 4. Decision (F) — R1 (single factor), per preregistration
Preregistration: “line is sealed **unless a protocol repair is justified**.” A mechanical
one-line convention defect justifies exactly ONE repair:
- **Changed**: `baseline_v2.py` `967812a6… → f6a2bbb2…` (one-line fix + comment; diff sha
  `0723cdfe…`). This is the single factor.
- **Unchanged**: anchors (A never clicks; B is uniform-random, transpose-invariant),
  all other policy logic, split, protocol parameters, all receipts retained.
- **Receipt hygiene (not part of the factor)**: rev2 folded receipt
  (`baseline_24h_result_rev2.json`, sha `cade093c…`: fold 60 rows; budget 393000→793000;
  lf52 `done→capped`; verdict unchanged) and runner `--receipts-dir` plumbing
  (`45680aad… → f4c574ed…`).
- **Re-run**: same protocol, outputs isolated in `receipts/24h_baseline_r1/`
  (pid 4562 started 10:49:36Z).
- **Stop conditions**: pass → next milestone planning; fail (baseline ≤ best anchor or
  0 levels) → **line sealed, no further repairs**.
- Decision receipt: `receipts/24h_baseline_diagnosis_2026-10-15/R1_DECISION_2026-10-15.json`
  (sha `58af1eab…`). The earlier seal draft (`seal_24h_baseline_2026-10-15.json`,
  sha `5b2d2179…`, written 10:28:09Z before diagnosis concluded) is retained as a
  historical draft and superseded for current state.

## 5. Deferred / unknown (U) — explicitly NOT included in R1
- Whether click *coverage policy* (which candidates, when, how many) needs improvement
  beyond the convention fix.
- ACTION5-modifier semantics for combo actions.
- lp85-style click-dominated games: post-fix behavior under the full 40k-step protocol.
These are held for a post-R1 review only if the line survives the re-run.
