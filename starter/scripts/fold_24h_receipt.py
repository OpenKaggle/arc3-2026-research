#!/usr/bin/env python3
"""Fold a completed (or interrupted) 24h milestone run into audit receipts.

Usage:
  fold_24h_receipt.py --dir receipts/24h_baseline_r1 [--dry-run] [--label r1]

Reads:  <dir>/progress.jsonl (per-(policy,game) rows), <dir>/baseline_24h_result.json
Writes: <dir>/baseline_24h_result_folded.json  (full ledger fold, gate recomputed)
        <dir>/gate_fold_<stamp>.json           (compact gate facts + verdict + suggestion)

Does NOT touch AUDIT_STATE.json (operator applies the printed suggestion), does not
delete anything, and is idempotent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # starter/
CAMP = "arc-prize-2026-arc-agi-3"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fold(dir_path: Path, label: str, dry_run: bool) -> dict:
    prog = dir_path / "progress.jsonl"
    res = dir_path / "baseline_24h_result.json"
    rows = [json.loads(l) for l in prog.read_text().splitlines() if l.strip()]
    led: dict[tuple[str, str], dict] = {}
    for r in rows:
        led[(r["policy"], r["game"])] = dict(r)  # last wins

    per_game: dict[str, dict[str, dict]] = {}
    for (pol, g), r in led.items():
        per_game.setdefault(pol, {})[g] = r

    def levels_total(policy: str) -> int:
        return sum(r["levels"] for r in per_game.get(policy, {}).values() if r["levels"] > 0)

    b = per_game.get("baseline", {})
    illegal_total = sum(r["illegal"] for r in b.values())
    crash_total = sum(r["crashes"] for r in b.values())
    rss_mb = max([r.get("rss_mb", 0.0) for r in b.values()] + [0.0])
    bl, al, bl_ = levels_total("baseline"), levels_total("anchor_a"), levels_total("anchor_b")
    best = max(al, bl_)

    src = json.loads(res.read_text()) if res.exists() else {}
    gate = dict(src.get("gate", {}))
    lat = gate.get("p99_ms_baseline", -1.0)
    gate.update({
        "legality_100pct": illegal_total == 0,
        "zero_crashes": crash_total == 0,
        "baseline_levels_total": bl,
        "anchor_a_levels_total": al,
        "anchor_b_levels_total": bl_,
        "best_anchor_levels_total": best,
        "at_least_one_level": bl >= 1,
        "strictly_above_best_anchor": bl > best,
        "peak_rss_mb": rss_mb,
        "rss_below_512": rss_mb < 512.0,
    })
    gate["gate_pass"] = bool(
        gate["legality_100pct"] and gate["zero_crashes"] and gate["at_least_one_level"]
        and gate["strictly_above_best_anchor"] and gate.get("p99_below_100ms", False)
        and gate["rss_below_512"]
    )

    n_rows_expected = 60
    complete = src.get("complete", False)
    fold = {
        "schema_version": 1,
        "milestone": "24h_baseline",
        "label": label,
        "source_dir": str(dir_path),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "progress_rows": len(rows),
        "games_folded": {k: len(v) for k, v in per_game.items()},
        "complete_flag_in_source": complete,
        "fold_expected_60_rows": len(rows) == n_rows_expected,
        "per_game": per_game,
        "gate": gate,
        "budget": {
            "total_baseline_steps": sum(r["steps"] for r in b.values()),
            "total_steps_all_policies": sum(r["steps"] for r in led.values()),
        },
        "evidence": {
            "progress_jsonl_sha256": sha256(prog) if prog.exists() else None,
            "result_json_sha256": sha256(res) if res.exists() else None,
        },
    }
    verdict = "PASS" if gate["gate_pass"] else "FAILED_AS_PREREGISTERED"
    suggestion = (
        "R1 gate PASS: plan next milestone (still local-only; no join)."
        if gate["gate_pass"] else
        "R1 gate FAILED: per stop text the line is SEALED (no further protocol repairs)."
    )
    gfold = {
        "schema_version": "arc3-24h-gate-fold/1.0",
        "campaign": CAMP,
        "label": label,
        "created_utc": fold["created_utc"],
        "gate_result": verdict,
        "gate_facts": {
            "baseline_levels_total": bl,
            "anchor_a_levels_total": al,
            "anchor_b_levels_total": bl_,
            "best_anchor_levels_total": best,
            "strictly_above_best_anchor": gate["strictly_above_best_anchor"],
            "legality_100pct": gate["legality_100pct"],
            "zero_crashes": gate["zero_crashes"],
            "p99_ms_baseline": lat,
            "rss_below_512": gate["rss_below_512"],
            "level_games": {
                pol: sorted(g for g, r in per_game.get(pol, {}).items() if r["levels"] > 0)
                for pol in ("baseline", "anchor_a", "anchor_b")
            },
        },
        "operator_next_step_suggestion": suggestion,
        "progress_rows": len(rows),
        "no_user_action_required": True,
    }

    if not dry_run:
        (dir_path / "baseline_24h_result_folded.json").write_text(
            json.dumps(fold, indent=1, sort_keys=True) + "\n")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (dir_path / f"gate_fold_{stamp}.json").write_text(
            json.dumps(gfold, indent=1, sort_keys=True) + "\n")
    return gfold


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True, help="receipts dir to fold")
    ap.add_argument("--label", default="run")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    d = Path(args.dir).expanduser().resolve()
    if not (d / "progress.jsonl").exists():
        raise SystemExit(f"no progress.jsonl in {d}")
    g = fold(d, args.label, args.dry_run)
    print(json.dumps({"gate_result": g["gate_result"], "gate_facts": g["gate_facts"],
                      "rows": g["progress_rows"], "suggestion": g["operator_next_step_suggestion"]},
                     indent=1))


if __name__ == "__main__":
    main()
