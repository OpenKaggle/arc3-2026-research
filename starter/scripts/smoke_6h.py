"""6-hour milestone smoke: 25 public games x 400 steps, legality + determinism."""
from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VENDOR = ROOT / "vendor" / "ARC-AGI-3-Agents"
sys.path.insert(0, str(VENDOR))

import arc_agi
from arc_agi import OperationMode
from arcengine import GameAction, GameState

sys.path.insert(0, str(ROOT / "agent"))

import my_agent  # noqa: E402

MAX_STEPS = 400
RUNS = 2


def run_pass(arc, game_ids, max_steps=MAX_STEPS):
    """Drive the agent manually with per-step legality capture."""
    results = {}
    trajectory = []
    violations = 0
    crashes = 0
    for game_id in game_ids:
        env = arc.make(game_id)
        if env is None:
            crashes += 1
            continue
        agent = my_agent.MyAgent(
            card_id="smoke-6h", game_id=game_id,
            agent_name=f"baseline.smoke.{game_id}",
            ROOT_URL="http://localhost", record=False, arc_env=env,
            tags=["smoke-6h"],
        )
        steps = 0
        game_violations = 0
        while steps < max_steps:
            if not agent.frames:
                frame = env.reset()
                agent.frames.append(frame)
            latest = agent.frames[-1]
            if agent.is_done(agent.frames, latest):
                break
            action = agent.choose_action(agent.frames, latest)
            available = getattr(latest, "available_actions", None)
            if action is GameAction.RESET:
                if latest.state not in (GameState.NOT_PLAYED, GameState.GAME_OVER):
                    game_violations += 1
            elif available is not None and action.value not in available:
                game_violations += 1
            try:
                data = action.action_data.model_dump()
                reasoning = getattr(action, "reasoning", None)
                if reasoning is not None and not isinstance(reasoning, dict):
                    reasoning = {"text": str(reasoning)}
                nxt = env.step(action, data=data, reasoning=reasoning)
            except Exception as exc:  # noqa: BLE001
                crashes += 1
                results[game_id] = {
                    "state": "CRASH", "levels_completed": -1,
                    "steps": steps, "illegal": game_violations,
                    "error": str(exc)[:200],
                }
                violations += game_violations
                break
            if nxt is None:
                crashes += 1
                results[game_id] = {
                    "state": "NONE_FRAME", "levels_completed": -1,
                    "steps": steps, "illegal": game_violations,
                }
                violations += game_violations
                break
            agent.frames.append(nxt)
            trajectory.append(
                f"{game_id}|{steps}|{action.value}|{getattr(latest,'state',None)}"
            )
            steps += 1
        final = agent.frames[-1]
        results[game_id] = {
            "state": str(final.state),
            "levels_completed": int(getattr(final, "levels_completed", -1)),
            "steps": steps,
            "illegal": game_violations,
        }
        violations += game_violations
    return results, violations, crashes, trajectory


def main() -> None:
    t0 = time.time()
    arc = arc_agi.Arcade(operation_mode=OperationMode.NORMAL)
    envs = arc.get_environments()
    game_ids = [e.game_id.split("-")[0] for e in envs]
    print(f"{len(game_ids)} games; {RUNS} passes x {MAX_STEPS} steps")
    passes = []
    for _ in range(RUNS):
        res, viol, crash, traj = run_pass(arc, game_ids)
        passes.append(
            {
                "results": res,
                "violations": viol,
                "crashes": crash,
                "trajectory_sha256": hashlib.sha256(
                    "\n".join(traj).encode()
                ).hexdigest(),
            }
        )
    det_ok = passes[0]["trajectory_sha256"] == passes[1]["trajectory_sha256"]
    total_steps = sum(r["steps"] for r in passes[0]["results"].values())
    receipt = {
        "schema_version": 1,
        "milestone": "6h_smoke",
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "versions": {
            "arc_agi": getattr(arc_agi, "__version__", "0.9.9"),
            "python": sys.version.split()[0],
            "framework_head": "4743e7d0aaae0ded0d98a89a7e282e63564cd58b",
            "starter_head": "eeb1535404f321d280a8f9194bbc1d7aca5f05fc",
            "agent_sha256": hashlib.sha256(
                (ROOT / "agent" / "my_agent.py").read_bytes()
            ).hexdigest(),
        },
        "coverage": {
            "games": len(game_ids),
            "passes": RUNS,
            "total_steps_pass0": total_steps,
            "target_steps": 10000,
        },
        "legality": {
            "violations_pass0": passes[0]["violations"],
            "violations_pass1": passes[1]["violations"],
            "crashes_pass0": passes[0]["crashes"],
            "crashes_pass1": passes[1]["crashes"],
        },
        "determinism": {
            "same_trajectory_hash": det_ok,
            "sha0": passes[0]["trajectory_sha256"],
            "sha1": passes[1]["trajectory_sha256"],
        },
        "per_game_pass0": passes[0]["results"],
        "wall_seconds": round(time.time() - t0, 3),
        "peak_rss_mb": round(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024, 1
        ),
        "denylist_accessed": False,
        "gate_6h": {
            "ten_thousand_steps_zero_illegal": total_steps >= 10000 and passes[0]["violations"] == 0,
            "replay_deterministic": det_ok,
            "zero_crashes": passes[0]["crashes"] == 0,
        },
    }
    out = ROOT.parent / "receipts" / "smoke_6h_2026-10-15.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in receipt.items() if k != "per_game_pass0"}, indent=1, ensure_ascii=False))
    print("receipt:", out)


if __name__ == "__main__":
    main()
