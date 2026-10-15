"""Baseline v2: deterministic model-free state-graph explorer (ARC-AGI-3).

Frozen design per docs/BASELINE_PROTOCOL.md (baseline architecture):
  * fail-closed frame/action validation (shape <=64x64, values -1..15)
  * hashes every raw frame before any derived representation
  * legal-action generator: reads available_actions every step
  * ACTION6 coordinates only from explainable candidates (component
    centers/corners, change frontiers, rare-color pixels), expanded in
    deterministic tiers (all non-background pixels, then a strided grid
    scan) when the explainable set is exhausted
  * RESET only after GAME_OVER / NOT_PLAYED
  * ACTION7 used only when currently legal
  * state graph keyed by frame/metadata hashes; repeated no-op
    (state, action) pairs deprioritized; novel/reversible transitions
    preferred (bounded-depth DFS with ACTION7-undo heuristic)
  * consecutive-action diversity to avoid single-path degeneracy in
    games without undo
  * deterministic seed from game_id digest (never wall clock / hash())
  * no game-ID branch, no per-game hand rule, no network, no LB feedback
"""

from __future__ import annotations

import hashlib
from collections import deque
from typing import Any, Optional

import numpy as np

from arcengine import FrameDataRaw, GameAction, GameState

SALT_DEFAULT = "arc3-cleanroom-baseline-v2|2026-10-15"

MAX_H, MAX_W = 64, 64
MIN_VAL, MAX_VAL = -1, 15
BACKTRACK_CAP = 5000
SMALL_COMP = 20          # components <= this size get all pixels as targets
TIER1_CAP = 512          # extra all-non-background targets
TIER2_CAP = 1024         # strided grid-scan fallback targets


class BaselineAgentV2:
    """Deterministic state-graph explorer operating on FrameDataRaw objects."""

    def __init__(
        self,
        game_id: str,
        max_steps: int = 40000,
        seed_salt: str = SALT_DEFAULT,
        max_targets: int = 40,
        noop_streak_limit: int = 40,
        stuck_step_limit: int = 600,
        max_depth: int = 6,
        run_diversity_limit: int = 4,
    ) -> None:
        digest = hashlib.sha256((seed_salt + "|" + game_id).encode("utf-8")).digest()
        self.seed = int.from_bytes(digest[:8], "big")
        self.counter = 0
        self.game_id = game_id
        self.max_steps = max_steps
        self.max_targets = max_targets
        self.noop_streak_limit = noop_streak_limit
        self.stuck_step_limit = stuck_step_limit
        self.max_depth = max_depth
        self.run_diversity_limit = run_diversity_limit

        self.graph: dict[tuple[int, int], dict[str, Any]] = {}
        self.visited: dict[int, int] = {}
        self.backtrack: list[tuple[int, int]] = []
        self._tier0_cache: dict[int, list[tuple[int, int]]] = {}
        self._target_idx: dict[int, int] = {}
        self._last: Optional[dict[str, Any]] = None
        self._prev_frame: Optional[np.ndarray] = None
        self._step = 0
        self._resets = 0
        self._noop_streak = 0
        self._last_change_step = 0
        self._run_action: Optional[int] = None
        self._run_len = 0
        self.last_action_id: Optional[int] = None
        self.last_obs: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------ rng
    @staticmethod
    def _mix(x: int) -> int:
        mask = (1 << 64) - 1
        x = (x + 0x9E3779B97F4A7C15) & mask
        x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & mask
        x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & mask
        return x ^ (x >> 31)

    def _next_rand(self, bound: int) -> int:
        self.counter += 1
        return self._mix(self.seed + self.counter * 0x9E3779B97F4A7C15) % bound

    # ----------------------------------------------------------- observation
    @staticmethod
    def _validate_frame(arr: np.ndarray) -> bool:
        if arr is None or arr.ndim != 2:
            return False
        h, w = arr.shape
        if h < 1 or w < 1 or h > MAX_H or w > MAX_W:
            return False
        if arr.dtype.kind not in "iub":
            return False
        if arr.size == 0:
            return False
        if int(arr.min()) < MIN_VAL or int(arr.max()) > MAX_VAL:
            return False
        return True

    def _obs(self, latest: FrameDataRaw) -> dict[str, Any]:
        frames: list[np.ndarray] = []
        valid = True
        for f in latest.frame:
            if not self._validate_frame(f):
                valid = False
                frames = []
                break
            frames.append(np.ascontiguousarray(f, dtype=np.int8))
        h = hashlib.sha256()
        h.update(b"V2|obs")
        h.update(str(int(latest.levels_completed)).encode())
        h.update(b"|")
        h.update(str(int(latest.win_levels)).encode())
        h.update(b"|")
        h.update(str(int(bool(latest.full_reset))).encode())
        h.update(b"|")
        h.update(",".join(str(a) for a in latest.available_actions).encode())
        for f in frames:
            h.update(f.tobytes())
        hexkey = h.hexdigest()
        return {
            "key": int(hexkey[:16], 16),
            "key_hex": hexkey,
            "levels": int(latest.levels_completed),
            "win": int(latest.win_levels),
            "avail": tuple(int(a) for a in latest.available_actions),
            "frames": frames,
            "valid": valid,
            "state": latest.state,
        }

    # ------------------------------------------------------- transition book
    def record_transition(self, obs: dict[str, Any]) -> None:
        if self._last is None:
            self._last = obs
        else:
            prev = self._last
            aid = self.last_action_id
            if aid is not None and aid != 0:
                tkey = (prev["key"], aid)
                info = self.graph.get(tkey)
                if info is None:
                    info = {"next": None, "delta_levels": 0, "delta_win": 0,
                            "count": 0, "noop": 0}
                    self.graph[tkey] = info
                info["count"] += 1
                noop = obs["key"] == prev["key"]
                if noop:
                    info["noop"] += 1
                    self._noop_streak += 1
                    if self.backtrack and self.backtrack[-1] == tkey:
                        self.backtrack.pop()
                else:
                    self._noop_streak = 0
                    self._last_change_step = self._step
                info["next"] = obs["key"]
                info["delta_levels"] = max(
                    info["delta_levels"], obs["levels"] - prev["levels"]
                )
                info["delta_win"] = max(info["delta_win"], obs["win"] - prev["win"])
            self._last = obs
        self.visited[obs["key"]] = self.visited.get(obs["key"], 0) + 1

    # --------------------------------------------------- ACTION6 candidates
    def _background(self, arr: np.ndarray) -> int:
        vals, counts = np.unique(arr, return_counts=True)
        return int(vals[int(np.argmax(counts))])

    def _components(self, arr: np.ndarray, bg: int) -> list[list[tuple[int, int]]]:
        h, w = arr.shape
        mask = arr != bg
        comps: list[list[tuple[int, int]]] = []
        seen = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                if mask[y, x] and not seen[y, x]:
                    q: deque[tuple[int, int]] = deque([(y, x)])
                    seen[y, x] = True
                    comp: list[tuple[int, int]] = []
                    while q:
                        cy, cx = q.popleft()
                        comp.append((cy, cx))
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            ny, nx = cy + dy, cx + dx
                            if (0 <= ny < h and 0 <= nx < w and mask[ny, nx]
                                    and not seen[ny, nx]):
                                seen[ny, nx] = True
                                q.append((ny, nx))
                    comps.append(comp)
        # small components first (clickable UI elements are usually small),
        # deterministic tie-break by first pixel
        comps.sort(key=lambda c: (0 if len(c) <= SMALL_COMP else 1,
                                  len(c), c[0][0], c[0][1]))
        return comps

    def _component_candidates(self, arr: np.ndarray) -> list[tuple[int, int]]:
        h, w = arr.shape
        bg = self._background(arr)
        comps = self._components(arr, bg)
        out: list[tuple[int, int]] = []
        budget = self.max_targets
        for comp in comps:
            if budget <= 0:
                break
            if len(comp) <= SMALL_COMP:
                pts = comp
            else:
                miny = min(p[0] for p in comp)
                maxy = max(p[0] for p in comp)
                minx = min(p[1] for p in comp)
                maxx = max(p[1] for p in comp)
                cy = int(round(sum(p[0] for p in comp) / len(comp)))
                cx = int(round(sum(p[1] for p in comp) / len(comp)))
                pts = [(miny, minx), (miny, maxx), (maxy, minx), (maxy, maxx),
                       (cy, cx)]
            for p in pts:
                out.append((int(p[0]), int(p[1])))
                budget -= 1
                if budget <= 0:
                    break
        return out

    def _delta_candidates(self, arr: np.ndarray) -> list[tuple[int, int]]:
        if self._prev_frame is None or self._prev_frame.shape != arr.shape:
            return []
        d = self._prev_frame != arr
        if not d.any():
            return []
        ys, xs = np.where(d)
        return [(int(round(float(ys.mean()))), int(round(float(xs.mean()))))]

    def _rare_candidates(self, arr: np.ndarray) -> list[tuple[int, int]]:
        vals, counts = np.unique(arr, return_counts=True)
        bg = int(vals[int(np.argmax(counts))])
        nonbg = int((arr != bg).sum())
        if nonbg == 0:
            return []
        out: list[tuple[int, int]] = []
        for v, c in zip(vals, counts):
            if int(v) == bg:
                continue
            if c <= max(1, nonbg // 100):
                ys, xs = np.where(arr == v)
                for i in range(min(4, len(ys))):
                    out.append((int(ys[i]), int(xs[i])))
        return out

    def _dedupe(self, pts: list[tuple[int, int]],
                h: int, w: int) -> list[tuple[int, int]]:
        seen: set[tuple[int, int]] = set()
        out: list[tuple[int, int]] = []
        for p in pts:
            p = (int(p[0]), int(p[1]))
            if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen:
                seen.add(p)
                out.append(p)
        return out

    def _tier0(self, obs: dict[str, Any]) -> list[tuple[int, int]]:
        key = obs["key"]
        if key not in self._tier0_cache:
            arr = obs["frames"][-1] if obs["frames"] else None
            if arr is None:
                self._tier0_cache[key] = []
            else:
                pts = self._component_candidates(arr)
                pts += self._delta_candidates(arr)
                pts += self._rare_candidates(arr)
                self._tier0_cache[key] = self._dedupe(
                    pts, arr.shape[0], arr.shape[1]
                )[: self.max_targets]
        return self._tier0_cache[key]

    def _extended_targets(self, obs: dict[str, Any]) -> list[tuple[int, int]]:
        tier0 = self._tier0(obs)
        arr = obs["frames"][-1] if obs["frames"] else None
        if arr is None:
            return tier0
        h, w = arr.shape
        t0set = set(tier0)
        bg = self._background(arr)
        # tier1: every non-background pixel, row-major
        ys, xs = np.where(arr != bg)
        tier1: list[tuple[int, int]] = []
        for y, x in zip(ys.tolist(), xs.tolist()):
            p = (int(y), int(x))
            if p not in t0set:
                tier1.append(p)
            if len(tier1) >= TIER1_CAP:
                break
        t01 = t0set | set(tier1)
        # tier2: strided full-grid scan
        tier2: list[tuple[int, int]] = []
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                p = (y, x)
                if p not in t01:
                    tier2.append(p)
                if len(tier2) >= TIER2_CAP:
                    break
            if len(tier2) >= TIER2_CAP:
                break
        return tier0 + tier1 + tier2

    def _targets_for(self, obs: dict[str, Any]) -> list[tuple[int, int]]:
        tier0 = self._tier0(obs)
        idx = self._target_idx.get(obs["key"], 0)
        if idx < len(tier0):
            return tier0
        return self._extended_targets(obs)

    def _target_available(self, obs: dict[str, Any]) -> bool:
        t = self._targets_for(obs)
        idx = self._target_idx.get(obs["key"], 0)
        return idx < len(t)

    # -------------------------------------------------------------- choosing
    def _finish_choose(self, obs: dict[str, Any], action: GameAction) -> None:
        if action is GameAction.RESET:
            self.backtrack.clear()
            self._resets += 1
            self._run_action = None
            self._run_len = 0
        elif action.value == 7:
            if self.backtrack:
                self.backtrack.pop()
        else:
            if not self.backtrack or self.backtrack[-1] != (obs["key"], action.value):
                self.backtrack.append((obs["key"], action.value))
                if len(self.backtrack) > BACKTRACK_CAP:
                    del self.backtrack[: BACKTRACK_CAP // 4]
        if action.value == self._run_action:
            self._run_len += 1
        else:
            self._run_action = action.value
            self._run_len = 1
        self.last_action_id = action.value
        self.last_obs = obs

    def choose_action(self, latest: FrameDataRaw) -> GameAction:
        obs = self._obs(latest)
        self.record_transition(obs)
        if obs["frames"]:
            self._prev_frame = obs["frames"][-1]
        self._step += 1

        if latest.state in (GameState.GAME_OVER, GameState.NOT_PLAYED):
            action = GameAction.RESET
            self._finish_choose(obs, action)
            return action

        key = obs["key"]
        legal = [a for a in obs["avail"] if 1 <= a <= 7]
        if not legal:
            legal = [1, 2, 3, 4, 5, 7]

        def info(a: int) -> Optional[dict[str, Any]]:
            return self.graph.get((key, a))

        known_good = sorted(
            a for a in legal if info(a) and info(a)["delta_levels"] > 0
        )
        untried_simple = sorted(
            a for a in legal if a not in (6, 7) and info(a) is None
        )
        untried_6 = 6 in legal and info(6) is None
        changed = sorted(
            (a for a in legal if info(a) and info(a)["count"] > info(a)["noop"]),
            key=lambda a: info(a)["count"] - info(a)["noop"],
        )
        noops = sorted(
            a for a in legal if info(a) and info(a)["count"] == info(a)["noop"]
        )
        untried_7 = 7 in legal and info(7) is None
        undo_available = 7 in legal and bool(self.backtrack)
        visits = self.visited.get(key, 0)
        depth = len(self.backtrack)

        if known_good:
            aid = known_good[0]
        elif undo_available and depth >= self.max_depth:
            # bounded-depth DFS: unwind to parent so siblings get tried
            aid = 7
        elif untried_simple:
            if (self._run_len >= self.run_diversity_limit
                    and self._run_action in untried_simple
                    and len(untried_simple) > 1):
                others = [a for a in untried_simple if a != self._run_action]
                aid = others[0]
            else:
                aid = untried_simple[0]
        elif untried_6 and self._target_available(obs):
            aid = 6
        elif undo_available and (visits >= 2 or not (changed or noops or untried_7)):
            aid = 7
        elif changed:
            aid = changed[0]
        elif untried_7:
            aid = 7
        elif noops:
            aid = noops[0]
        elif undo_available:
            aid = 7
        else:
            aid = min(legal, key=lambda a: (info(a) or {"count": 0})["count"])

        if aid == 6:
            t = self._targets_for(obs)
            idx = self._target_idx.get(key, 0)
            self._target_idx[key] = idx + 1
            if t:
                # Cycle deterministically through candidates so ACTION6 stays
                # valid even when chosen via the known-good path (which skips
                # the _target_available guard) after _target_idx has advanced
                # past the end of the list.
                x, y = t[idx % len(t)]
            else:
                x, y = (min(31, 63), min(31, 63))
            action = GameAction.ACTION6
            action.set_data({"game_id": self.game_id, "x": x, "y": y})
            action.reasoning = {"why": "explainable ACTION6 candidate"}
        else:
            action = GameAction.from_id(aid)
            action.reasoning = f"state-graph choice: action {aid}"

        self._finish_choose(obs, action)
        return action

    def is_done(self, frames: Any, latest: Any) -> bool:
        return latest.state is GameState.WIN
