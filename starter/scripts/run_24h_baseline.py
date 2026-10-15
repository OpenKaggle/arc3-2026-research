"""24h milestone runner: baseline-v2 paired vs two trivial anchors on
authoring + validation public games (frozen split, never sealed games).

Per docs/BASELINE_PROTOCOL.md 24h row:
  * 100% legal actions, 0 crashes, correct terminal handling
  * paired against both trivial anchors
  * >=1 completed level AND aggregate local result strictly above best
    trivial anchor
  * p99 policy latency <100 ms/step, peak RSS <512 MiB
  * <=24 aggregate CPU-hours, cumulative 2 GiB, $0

Resumable: per-(policy, game) lines in receipts/24h_baseline/progress.jsonl
are skipped on rerun. Baseline policy gets a chained per-step hash file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VENDOR = ROOT / "vendor" / "ARC-AGI-3-Agents"
sys.path.insert(0, str(VENDOR))
AGENT_DIR = ROOT / "agent"
sys.path.insert(0, str(AGENT_DIR))

import arc_agi
from arc_agi import OperationMode
from arcengine import GameAction, GameState

from anchors import FixedActionAnchor, UniformRandomAnchor
from baseline_v2 import BaselineAgentV2

SPLIT_SALT = "arc3-cleanroom-split-v1|2026-09-11"
RECEIPTS = ROOT.parent / "receipts" / "24h_baseline"
PROGRESS = RECEIPTS / "progress.jsonl"


def compute_split(full_ids: list[str]) -> tuple[list[str], list[str]]:
    keyed = sorted(
        full_ids,
        key=lambda gid: hashlib.sha256(
            (SPLIT_SALT + "|" + gid).encode("utf-8")
        ).hexdigest(),
    )
    # First 15 authoring, next 5 validation; the sealed 5 are never
    # materialized or recorded (split vault rule).
    return keyed[:15], keyed[15:20]


def manifest_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            b = p.read_bytes()
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            h.update(hashlib.sha256(b).digest())
    return h.hexdigest()


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head(p: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(p), text=True
        ).strip()
    except Exception:
        return "unknown"


def make_policy(name: str, game_id: str, max_steps: int):
    if name == "baseline":
        return BaselineAgentV2(game_id, max_steps=max_steps)
    if name == "anchor_a":
        return FixedActionAnchor(game_id, max_steps=max_steps)
    if name == "anchor_b":
        return UniformRandomAnchor(game_id, max_steps=max_steps)
    raise SystemExit(f"unknown policy {name}")


def load_ledger() -> dict[tuple[str, str], dict]:
    """Last recorded row per (policy, game) from the progress ledger."""
    ledger: dict[tuple[str, str], dict] = {}
    if PROGRESS.exists():
        for line in PROGRESS.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "policy" in row and "game" in row:
                ledger[(row["policy"], row["game"])] = row
    return ledger


def load_done() -> set[tuple[str, str]]:
    return {
        key for key, row in load_ledger().items()
        if row.get("status") in ("done", "capped")
    }


def fold_completed(rows: dict[str, dict[str, dict]], games: list[str],
                   ledger: dict[tuple[str, str], dict]) -> int:
    """Merge last-per-(policy, game) ledger rows into the result table.

    A resumed run must report the full ledger in its receipt, not only the
    rows executed by the current process (repair 2026-10-15: the resumed
    24h receipt covered only 10/20 baseline games).
    """
    folded = 0
    for (policy, game), row in ledger.items():
        if policy in rows and game in games:
            rows[policy][game] = row
            folded += 1
    return folded


def run_game(
    env, policy, game_id: str, max_steps: int, per_game_cap_s: float,
    chain_fp=None, latencies: list[float] | None = None,
) -> dict:
    chain = hashlib.sha256(("arc3-chain|v2|" + game_id).encode("utf-8"))
    violations = 0
    crashes = 0
    crash_reason = ""
    fr = env.reset()
    if fr is None:
        return {
            "state": "CRASH", "levels": -1, "win": -1, "steps": 0,
            "illegal": 0, "crashes": 1, "wall_s": 0.0,
            "chain_head": chain.hexdigest(), "crash_reason": "reset_failed",
        }
    steps = 0
    t0 = time.time()
    while steps < max_steps:
        if fr.state is GameState.WIN:
            break
        t_act0 = time.perf_counter()
        try:
            action = policy.choose_action(fr)
        except Exception as exc:  # noqa: BLE001
            # Policy crash must fail the gate honestly, not kill the whole
            # 24h wall-clock run (repair 2026-10-15).
            crashes += 1
            crash_reason = f"{type(exc).__name__}: {str(exc)[:200]}"
            break
        if latencies is not None:
            latencies.append((time.perf_counter() - t_act0) * 1000.0)
        if action is GameAction.RESET:
            if fr.state not in (GameState.NOT_PLAYED, GameState.GAME_OVER):
                violations += 1
        else:
            avail = list(getattr(fr, "available_actions", []))
            if avail and action.value not in avail:
                violations += 1
        data = action.action_data.model_dump()
        reasoning = getattr(action, "reasoning", None)
        if reasoning is not None and not isinstance(reasoning, dict):
            reasoning = {"text": str(reasoning)}
        try:
            nxt = env.step(action, data=data, reasoning=reasoning)
        except Exception as exc:  # noqa: BLE001
            crashes += 1
            crash_reason = f"{type(exc).__name__}: {str(exc)[:200]}"
            break
        if nxt is None:
            crashes += 1
            crash_reason = "step_returned_none"
            break
        obs = getattr(policy, "last_obs", None)
        key_hex = obs["key_hex"] if isinstance(obs, dict) else ""
        x = data.get("x", "")
        y = data.get("y", "")
        chain.update(
            f"{steps}|{action.value}|{x}|{y}|{key_hex}|".encode("utf-8")
        )
        if chain_fp is not None:
            chain_fp.write(chain.hexdigest() + "\n")
        steps += 1
        fr = nxt
        if steps % 500 == 0 and (time.time() - t0) > per_game_cap_s:
            break
    wall = round(time.time() - t0, 2)
    if crashes == 0 and fr.state is GameState.WIN:
        status = "done"
    elif crashes == 0 and steps >= max_steps:
        status = "capped"
    elif crashes == 0:
        # wall-clock per-game cap hit before the step limit: not a WIN, so
        # this is a capped run, not a done one.
        status = "capped"
    else:
        status = "crash"
    return {
        "status": status,
        "state": str(fr.state),
        "levels": int(fr.levels_completed),
        "win": int(fr.win_levels),
        "steps": steps,
        "illegal": violations,
        "crashes": crashes,
        "wall_s": wall,
        "chain_head": chain.hexdigest(),
        "crash_reason": crash_reason,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policies", default="baseline,anchor_a,anchor_b")
    ap.add_argument("--games", default=None,
                    help="comma-separated short ids; default authoring+validation split")
    ap.add_argument("--max-steps", type=int, default=40000)
    ap.add_argument("--wall-cap-hours", type=float, default=20.0)
    ap.add_argument("--per-game-cap-s", type=float, default=1800.0)
    ap.add_argument("--quick", action="store_true",
                    help="short determinism sanity: baseline only, 2 passes, fewer steps")
    ap.add_argument("--quick-steps", type=int, default=2500)
    ap.add_argument("--receipts-dir", default=None,
                    help="output dir for receipts (default: arc3_2026/receipts/24h_baseline)")
    args = ap.parse_args()

    global RECEIPTS, PROGRESS
    if args.receipts_dir:
        RECEIPTS = Path(args.receipts_dir).expanduser().resolve()
        PROGRESS = RECEIPTS / "progress.jsonl"

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    print(f"[run_24h] start {datetime.now(timezone.utc).isoformat()}", flush=True)
    arc = arc_agi.Arcade(operation_mode=OperationMode.NORMAL)
    envs = arc.get_environments()
    full_ids = [e.game_id for e in envs]
    short_by_full = {e.game_id: e.game_id.split("-")[0] for e in envs}
    authoring_full, validation_full = compute_split(full_ids)
    authoring = [short_by_full[g] for g in authoring_full]
    validation = [short_by_full[g] for g in validation_full]
    print(f"[run_24h] split: authoring={authoring}", flush=True)
    print(f"[run_24h] split: validation={validation}", flush=True)

    policies = [p.strip() for p in args.policies.split(",") if p.strip()]
    if args.quick:
        games = [authoring[0]] if not args.games else [
            g.strip() for g in args.games.split(",") if g.strip()
        ]
        max_steps = args.quick_steps
        passes = 2
        policies = ["baseline"]
        wall_cap = 3600.0
    else:
        games = (authoring + validation) if not args.games else [
            g.strip() for g in args.games.split(",") if g.strip()
        ]
        max_steps = args.max_steps
        passes = 1
        wall_cap = args.wall_cap_hours * 3600.0

    done = load_done()
    ledger = load_ledger()
    rows: dict[str, dict[str, dict]] = {p: {} for p in policies}
    folded_rows = fold_completed(rows, games, ledger)
    latencies: dict[str, list[float]] = {p: [] for p in policies}

    for policy_name in policies:
        for gi, game in enumerate(games, 1):
            if (policy_name, game) in done:
                print(f"[run_24h] skip done {policy_name} {game}", flush=True)
                continue
            pass_rows = []
            pass_heads = []
            for p_i in range(passes):
                # Fresh env per pass: game instances do not fully restore via
                # reset() (verified 2026-10-15), so reuse breaks determinism.
                env = arc.make(game)
                if env is None:
                    print(f"[run_24h] env failed {game}", flush=True)
                    continue
                chain_fp = None
                chain_path = None
                if policy_name == "baseline":
                    chain_path = RECEIPTS / f"chain_{policy_name}_{game}_p{p_i}.txt"
                    chain_fp = open(chain_path, "w")
                try:
                    row = run_game(
                        env,
                        make_policy(policy_name, game, max_steps),
                        game, max_steps, args.per_game_cap_s,
                        chain_fp=chain_fp,
                        latencies=latencies[policy_name],
                    )
                finally:
                    if chain_fp is not None:
                        chain_fp.close()
                row["policy"] = policy_name
                row["game"] = game
                row["pass"] = p_i
                row["at"] = datetime.now(timezone.utc).isoformat()
                row["rss_mb"] = round(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 1
                )
                pass_rows.append(row)
                pass_heads.append(row["chain_head"])
                rows[policy_name][game] = row
                with open(PROGRESS, "a") as fp:
                    fp.write(json.dumps(row) + "\n")
                print(
                    f"[run_24h] {policy_name} {game}: state={row['state']} "
                    f"levels={row['levels']}/{row['win']} steps={row['steps']} "
                    f"illegal={row['illegal']} crash={row['crashes']} "
                    f"wall={row['wall_s']}s rss={row['rss_mb']}MB",
                    flush=True,
                )
            if passes > 1:
                print(
                    f"[run_24h] determinism {policy_name} {game}: "
                    f"{pass_heads[0] == pass_heads[1]}",
                    flush=True,
                )
            if (time.time() - t_start) > wall_cap:
                print("[run_24h] wall cap reached, stopping early", flush=True)
                write_receipt(rows, latencies, args, authoring_full,
                              validation_full, full_ids, short_by_full,
                              time.time() - t_start, complete=False,
                              folded_rows=folded_rows)
                return
    write_receipt(rows, latencies, args, authoring_full, validation_full,
                  full_ids, short_by_full, time.time() - t_start, complete=True,
                  folded_rows=folded_rows)


def write_receipt(rows, latencies, args, authoring_full, validation_full,
                  full_ids, short_by_full, wall_s, complete: bool,
                  folded_rows: int = 0) -> None:
    out = {}
    out["schema_version"] = 1
    out["milestone"] = "24h_baseline"
    out["run_at_utc"] = datetime.now(timezone.utc).isoformat()
    out["complete"] = complete
    out["versions"] = {
        "arc_agi": getattr(arc_agi, "__version__", "0.9.9"),
        "python": sys.version.split()[0],
        "framework_head": git_head(VENDOR),
        "starter_head": git_head(ROOT),
        "env_manifest_sha256": manifest_hash(ROOT / "environment_files"),
        "baseline_v2_sha256": file_sha256(AGENT_DIR / "baseline_v2.py"),
        "anchors_sha256": file_sha256(AGENT_DIR / "anchors.py"),
        "runner_sha256": file_sha256(Path(__file__)),
    }
    out["split"] = {
        "salt": SPLIT_SALT,
        "algorithm": "sha256(salt|full_game_id) sort ascending; first 15 authoring, next 5 validation; sealed never materialized",
        "authoring": authoring_full,
        "validation": validation_full,
    }
    out["config"] = {
        "max_steps_per_game": args.max_steps if not args.quick else args.quick_steps,
        "policies": sorted(rows.keys()),
        "quick_mode": bool(args.quick),
    }
    out["per_game"] = {p: rows[p] for p in sorted(rows.keys())}

    def levels_total(policy: str) -> int:
        return sum(
            r["levels"] for r in rows.get(policy, {}).values() if r["levels"] > 0
        )

    b = rows.get("baseline", {})
    illegal_total = sum(r["illegal"] for r in b.values())
    crash_total = sum(r["crashes"] for r in b.values())
    lats = sorted(latencies.get("baseline", []))
    p99 = lats[int(len(lats) * 0.99)] if lats else -1.0
    rss_mb = max(
        [r.get("rss_mb", 0.0) for r in b.values()] + [0.0]
    )
    bl = levels_total("baseline")
    al = levels_total("anchor_a")
    bl_ = levels_total("anchor_b")
    best_anchor = max(al, bl_)
    gate = {
        "legality_100pct": illegal_total == 0,
        "zero_crashes": crash_total == 0,
        "baseline_levels_total": bl,
        "anchor_a_levels_total": al,
        "anchor_b_levels_total": bl_,
        "best_anchor_levels_total": best_anchor,
        "at_least_one_level": bl >= 1,
        "strictly_above_best_anchor": bl > best_anchor,
        "p99_ms_baseline": round(p99, 2),
        "p99_below_100ms": 0.0 < p99 < 100.0,
        "peak_rss_mb": rss_mb,
        "rss_below_512": rss_mb < 512.0,
    }
    gate["gate_pass"] = bool(
        gate["legality_100pct"] and gate["zero_crashes"]
        and gate["at_least_one_level"] and gate["strictly_above_best_anchor"]
        and gate["p99_below_100ms"] and gate["rss_below_512"]
    )
    out["gate"] = gate
    out["budget"] = {
        "wall_s": round(wall_s, 1),
        "total_baseline_steps": sum(r["steps"] for r in b.values()),
        "approx_cpu_hours": round(wall_s / 3600.0, 2),
    }
    out["notes"] = [
        "Sealed 5 game ids were never computed, printed or recorded.",
        "Trivial anchors are controls only, not submission candidates.",
        "Stop condition pre-registered: if baseline <= best anchor or 0 levels, 24h gate fails and line is sealed unless a protocol repair is justified.",
    ]
    if folded_rows:
        out["notes"].append(
            f"Receipt folded {folded_rows} completed row(s) from "
            "progress.jsonl (resumed run); latency stats cover only steps "
            "run in the final session."
        )
    path = RECEIPTS / "baseline_24h_result.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (RECEIPTS / f"baseline_24h_result_{stamp}.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n"
    )
    print(f"[run_24h] receipt written: {path}", flush=True)
    print(f"[run_24h] gate: {json.dumps(gate)}", flush=True)


if __name__ == "__main__":
    main()
