#!/usr/bin/env python3
"""Build baseline_24h_result_rev2.json by folding the full progress ledger.

Corrections vs rev1 (sha256 387bd8ed...):
 1. per_game now folds ALL 60 ledger rows (rev1 carried only the 10 rows
    re-run by the final process; the 10 skipped-on-resume baseline rows were
    missing).
 2. budget.total_baseline_steps corrected 393000 -> 793000 (all 20 games).
 3. lf52/baseline status label corrected "done" -> "capped" (row produced by
    pre-edit runner bytes; terminal state NOT_FINISHED with cap hit; wall
    13938.54s / 33000 steps). Content fields unchanged.
 4. Gate fields recomputed from the folded table; verdict unchanged
    (baseline 3 vs best anchor 8 -> gate_pass=false).
p99 latency and wall_s carried over from rev1 (not recomputable post hoc).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT.parent / "receipts" / "24h_baseline"
rev1 = json.loads((R / "baseline_24h_result.json").read_text())
rows = [json.loads(l) for l in (R / "progress.jsonl").read_text().splitlines() if l.strip()]
led: dict[tuple[str, str], dict] = {}
for r in rows:
    led[(r["policy"], r["game"])] = dict(r)  # last wins

lf = led.get(("baseline", "lf52"))
if lf and lf.get("status") == "done":
    lf["status"] = "capped"
    lf["label_note"] = ("rev2 label correction: row written by pre-edit runner bytes; "
                        "on-disk label logic emits 'capped' (state NOT_FINISHED with cap hit; "
                        "wall 13938.54s / 33000 steps). Content fields unchanged.")

per_game: dict[str, dict[str, dict]] = {}
for (pol, g), r in led.items():
    per_game.setdefault(pol, {})[g] = r


def levels_total(policy: str) -> int:
    return sum(r["levels"] for r in per_game.get(policy, {}).values() if r["levels"] > 0)


b = per_game["baseline"]
illegal_total = sum(r["illegal"] for r in b.values())
crash_total = sum(r["crashes"] for r in b.values())
rss_mb = max([r.get("rss_mb", 0.0) for r in b.values()] + [0.0])
bl, al, bl_ = levels_total("baseline"), levels_total("anchor_a"), levels_total("anchor_b")
best = max(al, bl_)
gate = dict(rev1["gate"])
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
    and gate["strictly_above_best_anchor"] and gate["p99_below_100ms"] and gate["rss_below_512"]
)

out = dict(rev1)
out["per_game"] = per_game
out["gate"] = gate
out["budget"] = dict(rev1["budget"])
out["budget"]["total_baseline_steps"] = sum(r["steps"] for r in b.values())
out["budget"]["total_steps_all_policies"] = sum(r["steps"] for r in led.values())
out["revision"] = {
    "rev": 2,
    "rev_of": "baseline_24h_result.json",
    "rev_of_sha256": "387bd8ede7e42f71a584ea380ef0e22a9f83abf1890d14380d1bc60ee4271286",
    "revised_at_utc": datetime.now(timezone.utc).isoformat(),
    "fold_source": "progress.jsonl",
    "fold_source_sha256": hashlib.sha256((R / "progress.jsonl").read_bytes()).hexdigest(),
    "folded_rows": len(led),
    "fold_rule": "last row per (policy, game)",
    "corrections": [
        "per_game folded from all 60 ledger rows (rev1 carried only the 10 rows re-run by the final process)",
        f"budget.total_baseline_steps corrected 393000 -> {sum(r['steps'] for r in b.values())}",
        "lf52/baseline status label corrected 'done' -> 'capped' (pre-edit bytes); content fields unchanged",
        f"gate fields recomputed from folded table; verdict unchanged (baseline {bl} vs best anchor {best})",
        "p99_ms and wall_s carried over from rev1 (not recomputable post hoc)",
    ],
}
out["notes"] = list(rev1.get("notes", [])) + [
    "REV2 2026-10-15: receipt corrected per fold rules; no change to gate verdict; rev1 retained as the as-written record.",
]
(R / "baseline_24h_result_rev2.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(R / f"baseline_24h_result_rev2_{stamp}.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
print("rev2 written")
print("gate:", json.dumps({k: out["gate"][k] for k in (
    "baseline_levels_total", "anchor_a_levels_total", "anchor_b_levels_total",
    "strictly_above_best_anchor", "gate_pass", "peak_rss_mb", "p99_ms_baseline")}))
print("budget:", json.dumps(out["budget"]))
print("per_game rows:", {k: len(v) for k, v in per_game.items()})
