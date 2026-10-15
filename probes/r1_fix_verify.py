#!/usr/bin/env python3
"""R1 fix verification (local, read-only).

Runs the R1-fixed BaselineAgentV2 deterministically and, for every ACTION6
payload, checks that the agent now addresses the intended candidate pixel:
  * candidates are (row, col)=(y, x) from the frame array;
  * engine ACTION6 payload must be {"x": col, "y": row};
  * hence sent == (candidate_col, candidate_row).
Also contrasts the pixel the payload will actually address (frame[row=sent_y,
col=sent_x] == intended), versus the pixel the pre-R1 transposed payload would
have addressed (frame[candidate_col, candidate_row]).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
STARTER = ROOT / "starter"
sys.path.insert(0, str(STARTER))
sys.path.insert(0, str(STARTER / "vendor" / "ARC-AGI-3-Agents"))
sys.path.insert(0, str(STARTER / "agent"))

import numpy as np  # noqa: E402
import arc_agi  # noqa: E402
from arc_agi import OperationMode  # noqa: E402
from arcengine import GameAction  # noqa: E402
from baseline_v2 import BaselineAgentV2  # noqa: E402

GAMES = ["sp80", "lp85"]
STEPS = 1500


def run(game_id: str, arc) -> dict:
    rec = {"game": game_id}
    env = arc.make(game_id)
    fr = env.reset() if env is not None else None
    if fr is None:
        rec["error"] = "reset_failed"
        return rec
    agent = BaselineAgentV2(game_id, max_steps=STEPS)
    checks = []
    steps_run = 0
    for i in range(STEPS):
        act = agent.choose_action(fr)
        data = act.action_data.model_dump() if act.action_data is not None else {}
        if act == GameAction.ACTION6:
            obs = agent.last_obs
            F = obs["frames"][-1]
            vals, counts = np.unique(F, return_counts=True)
            bg = int(vals[int(np.argmax(counts))])
            key = obs["key"]
            t = agent._targets_for(obs)
            idx = agent._target_idx.get(key, 0) - 1
            if t:
                cand = t[idx % len(t)]
                cr, cc = int(cand[0]), int(cand[1])
                sx, sy = int(data.get("x")), int(data.get("y"))
                checks.append({
                    "step": i,
                    "candidate_row_col": [cr, cc],
                    "sent_x_y": [sx, sy],
                    "sent_is_cand_col_row": (sx == cc and sy == cr),
                    "intended_pixel_value": int(F[cr, cc]),
                    "intended_pixel_is_non_bg": bool(int(F[cr, cc]) != bg),
                    "pre_fix_payload_target_value": int(F[cc, cr]),
                    "pre_fix_payload_target_is_non_bg": bool(int(F[cc, cr]) != bg),
                })
        nxt = env.step(act, data=data, reasoning=None)
        steps_run = i + 1
        if nxt is None:
            rec["step_error_at"] = i
            break
        fr = nxt
    rec["steps_run"] = steps_run
    rec["n_clicks_checked"] = len(checks)
    rec["all_sent_are_cand_col_row"] = all(c["sent_is_cand_col_row"] for c in checks) if checks else None
    rec["intended_non_bg_rate"] = (
        sum(c["intended_pixel_is_non_bg"] for c in checks) / len(checks) if checks else None
    )
    rec["pre_fix_target_non_bg_rate"] = (
        sum(c["pre_fix_payload_target_is_non_bg"] for c in checks) / len(checks) if checks else None
    )
    rec["pre_fix_target_same_as_intended_rate"] = (
        sum(c["pre_fix_payload_target_value"] == c["intended_pixel_value"] for c in checks) / len(checks)
        if checks else None
    )
    rec["sample_checks"] = checks[:6]
    return rec


def main() -> None:
    arc = arc_agi.Arcade(operation_mode=OperationMode.NORMAL)
    out = {"probe": "r1_fix_verify", "date": "2026-10-15",
           "baseline_v2_sha256_note": "f6a2bbb233556da8debea0a8012f2e12573a26ec6524798989a19f9f402e7dfe",
           "games": []}
    for gid in GAMES:
        out["games"].append(run(gid, arc))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
