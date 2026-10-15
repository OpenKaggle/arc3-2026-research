#!/usr/bin/env python3
"""ACTION6 coordinate-convention probe (read-only, local).

Establishes, against the vendored engine source + live local environments:
  engine convention: ACTION6 data {"x": c, "y": r} clicks the frame pixel at
  frame[r][c] (array indexed [row=y][col=x], (0,0) top-left), i.e. x=column,
  y=row.  For every explainable click, agent/baseline_v2.py unpacks the
  (row, col)=(y, x) candidate as `x, y = t[...]`, sending {"x": row, "y": col}
  -> transposed landing pixel.

Also replays BaselineAgentV2 deterministically for a bounded number of steps
to count ACTION6 usage and to record (candidate, sent) pairs.

Writes JSON to stdout (caller redirects into receipts/).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]                 # arc3_2026
STARTER = ROOT / "starter"
sys.path.insert(0, str(STARTER))
sys.path.insert(0, str(STARTER / "vendor" / "ARC-AGI-3-Agents"))
sys.path.insert(0, str(STARTER / "agent"))

import numpy as np  # noqa: E402
import arc_agi  # noqa: E402
from arc_agi import OperationMode  # noqa: E402
from arcengine import GameAction  # noqa: E402
from baseline_v2 import BaselineAgentV2  # noqa: E402

GAMES_STATIC = ["sp80", "su15", "m0r0", "ar25", "re86", "tu93", "ls20", "cd82", "lp85", "ft09"]
GAMES_REPLAY = ["sp80", "cd82", "lp85"]   # games where baseline gained a level
REPLAY_STEPS = 1200


def as_list(f):
    return np.asarray(f).tolist()


def static_probe(gid, arc, out):
    rec = {"game": gid}
    env = arc.make(gid)
    fr = env.reset() if env is not None else None
    if fr is None:
        rec["error"] = "reset_failed"
        out.append(rec)
        return rec
    g = env._game
    lvl = g.current_level
    sprites = lvl.get_sprites_by_tag("sys_click") + lvl.get_sprites_by_tag("sys_place")
    rec["n_clickable_sprites"] = len(sprites)
    try:
        clicks = g._get_valid_clickable_actions()
    except Exception as exc:  # noqa: BLE001
        clicks = []
        rec["valid_actions_error"] = repr(exc)
    rec["n_valid_click_actions"] = len(clicks)
    rec["state"] = str(fr.state)
    rec["levels"] = fr.levels_completed
    if fr.frame:
        F_resp = as_list(fr.frame[-1])
        F_render = as_list(g.camera.render(lvl.get_sprites()))
        rec["frame_matches_render"] = F_resp == F_render
    else:
        F_resp = None
    if sprites and F_resp is not None:
        scale, xoff, yoff = g.camera._calculate_scale_and_offset()
        rec["scale_offsets"] = [scale, xoff, yoff]
        s = sprites[0]
        P = s.render()
        found = None
        for py in range(P.shape[0]):
            for px in range(P.shape[1]):
                if P[py, px] >= 0:
                    found = (py, px, int(P[py, px]))
                    break
            if found:
                break
        rec["sprite0_x_y_w_h"] = [s.x, s.y, s.width, s.height]
        if found:
            py, px, val = found
            sx = (s.x + px) * scale + xoff
            sy = (s.y + py) * scale + yoff
            rec["probe_pixel"] = {"sprite_py_px": [py, px],
                                  "display_sx_sy": [sx, sy], "value": val}
            rec["frame_at_row_sy_col_sx"] = int(np.asarray(F_resp)[sy, sx])
            rec["frame_at_row_sx_col_sy"] = int(np.asarray(F_resp)[sx, sy])
            gd = g.camera.display_to_grid(sx, sy)
            gt = g.camera.display_to_grid(sy, sx)
            rec["display_to_grid_correct"] = list(gd) if gd else None
            rec["display_to_grid_transposed"] = list(gt) if gt else None
            if gd:
                sp = lvl.get_sprite_at(gd[0], gd[1])
                rec["sprite_at_correct"] = None if sp is None else {
                    "x": sp.x, "y": sp.y, "clickable": ("sys_click" in sp.tags or "sys_place" in sp.tags)}
            if gt:
                spt = lvl.get_sprite_at(gt[0], gt[1])
                rec["sprite_at_transposed"] = None if spt is None else {
                    "x": spt.x, "y": spt.y, "clickable": ("sys_click" in spt.tags or "sys_place" in spt.tags)}
            rec["correct_xy_in_valid_clicks"] = any(
                c.data.get("x") == sx and c.data.get("y") == sy for c in clicks)
            rec["transposed_xy_in_valid_clicks"] = any(
                c.data.get("x") == sy and c.data.get("y") == sx for c in clicks)
    out.append(rec)
    return rec


def send_click(env, gid, x, y):
    act = GameAction.ACTION6
    act.set_data({"game_id": gid, "x": int(x), "y": int(y)})
    data = act.action_data.model_dump()
    return env.step(act, data=data, reasoning=None), data


def diff_count(f0, f1):
    if f0 is None or f1 is None:
        return None
    a = np.asarray(f0); b = np.asarray(f1)
    if a.shape != b.shape:
        return -1
    return int((a != b).sum())


def dynamic_probe(gid, arc, out):
    """On a fresh instance, click correct then transposed coords (fresh env
    each); report frame diffs and level counts."""
    rec = {"game": gid}
    env = arc.make(gid)
    fr = env.reset() if env is not None else None
    if fr is None:
        rec["error"] = "reset_failed"
        out.append(rec)
        return
    g = env._game
    lvl = g.current_level
    sprites = lvl.get_sprites_by_tag("sys_click") + lvl.get_sprites_by_tag("sys_place")
    if not sprites:
        rec["note"] = "no clickable sprites at initial state"
        out.append(rec)
        return
    scale, xoff, yoff = g.camera._calculate_scale_and_offset()
    s = sprites[0]
    P = s.render()
    found = None
    for py in range(P.shape[0]):
        for px in range(P.shape[1]):
            if P[py, px] >= 0:
                found = (py, px)
                break
        if found:
            break
    py, px = found
    sx = (s.x + px) * scale + xoff
    sy = (s.y + py) * scale + yoff
    rec["click_correct_xy"] = [sx, sy]
    rec["click_transposed_xy"] = [sy, sx]

    # No-click control (fresh instance, one simple no-op-ish action? use RESET baseline frame diff)
    # correct click on fresh env
    env_c = arc.make(gid); fr_c0 = env_c.reset()
    f0 = fr_c0.frame[-1] if fr_c0.frame else None
    nxt, _ = send_click(env_c, gid, sx, sy)
    f1 = nxt.frame[-1] if (nxt is not None and nxt.frame) else None
    rec["correct_click_frame_diff"] = diff_count(f0, f1)
    rec["correct_click_levels_after"] = None if nxt is None else nxt.levels_completed

    # transposed click on fresh env
    env_t = arc.make(gid); fr_t0 = env_t.reset()
    f0 = fr_t0.frame[-1] if fr_t0.frame else None
    nxt, _ = send_click(env_t, gid, sy, sx)
    f1 = nxt.frame[-1] if (nxt is not None and nxt.frame) else None
    rec["transposed_click_frame_diff"] = diff_count(f0, f1)
    rec["transposed_click_levels_after"] = None if nxt is None else nxt.levels_completed

    # repeat correct click 3x to look for a state change
    env_r = arc.make(gid); fr = env_r.reset()
    f_prev = fr.frame[-1] if fr.frame else None
    diffs = []
    lv = fr.levels_completed
    for _ in range(3):
        nxt, _ = send_click(env_r, gid, sx, sy)
        if nxt is None:
            diffs.append(None)
            break
        f_now = nxt.frame[-1] if nxt.frame else None
        diffs.append(diff_count(f_prev, f_now))
        f_prev = f_now
        lv = nxt.levels_completed
    rec["repeat_correct_click_diffs"] = diffs
    rec["repeat_correct_click_levels"] = lv
    out.append(rec)


def replay_probe(gid, arc, out):
    """Deterministic bounded replay of BaselineAgentV2; count ACTION6 usage
    and verify (candidate row,col) vs (sent x,y) pairs."""
    rec = {"game": gid, "steps_run": 0}
    env = arc.make(gid)
    fr = env.reset() if env is not None else None
    if fr is None:
        rec["error"] = "reset_failed"
        out.append(rec)
        return
    agent = BaselineAgentV2(gid, max_steps=REPLAY_STEPS)
    aid6 = 0
    pairs = []
    levels = 0
    for i in range(REPLAY_STEPS):
        act = agent.choose_action(fr)
        data = act.action_data.model_dump() if act.action_data is not None else {}
        if act == GameAction.ACTION6:
            aid6 += 1
            sent_x, sent_y = data.get("x"), data.get("y")
            # recover the candidate the agent intended: recompute via internals
            key = agent.last_obs["key"] if getattr(agent, "last_obs", None) else None
            cand = None
            if key is not None:
                t = agent._targets_for(agent.last_obs)
                idx = agent._target_idx.get(key, 0) - 1
                if t:
                    cand = t[idx % len(t)]
            if cand is not None and len(pairs) < 8:
                pairs.append({"candidate_row_col": [int(cand[0]), int(cand[1])],
                              "sent_x_y": [int(sent_x), int(sent_y)],
                              "sent_equals_candidate_xy_order": (int(sent_x) == int(cand[0]) and int(sent_y) == int(cand[1]))})
        nxt = env.step(act, data=data, reasoning=None)
        rec["steps_run"] = i + 1
        if nxt is None:
            rec["step_error_at"] = i
            break
        fr = nxt
        levels = fr.levels_completed
        if str(fr.state) in ("GameState.WIN", "GameState.GAME_OVER"):
            if str(fr.state) == "GameState.GAME_OVER":
                # baseline chooses RESET next; continue
                pass
            else:
                break
    rec["action6_count"] = aid6
    rec["action6_rate"] = round(aid6 / max(1, rec["steps_run"]), 4)
    rec["levels_after"] = levels
    rec["click_pairs"] = pairs
    out.append(rec)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    arc = arc_agi.Arcade(operation_mode=OperationMode.NORMAL)
    report = {"probe": "action6_convention", "date": "2026-10-15", "static": [], "dynamic": [], "replay": []}
    if which in ("all", "static"):
        for gid in GAMES_STATIC:
            try:
                static_probe(gid, arc, report["static"])
            except Exception as exc:  # noqa: BLE001
                report["static"].append({"game": gid, "error": repr(exc)})
    if which in ("all", "dynamic"):
        for gid in ["sp80", "su15", "m0r0", "ar25"]:
            try:
                dynamic_probe(gid, arc, report["dynamic"])
            except Exception as exc:  # noqa: BLE001
                report["dynamic"].append({"game": gid, "error": repr(exc)})
    if which in ("all", "replay"):
        for gid in GAMES_REPLAY:
            try:
                replay_probe(gid, arc, report["replay"])
            except Exception as exc:  # noqa: BLE001
                report["replay"].append({"game": gid, "error": repr(exc)})
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
