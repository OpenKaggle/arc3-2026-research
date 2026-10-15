"""Deterministic clean-room baseline for ARC-AGI-3 (frozen protocol 2026-09-11).

Model-free state machine slice, per docs/BASELINE_PROTOCOL.md:
  - deterministic seed derived from game_id digest (never wall-clock / hash())
  - reads available_actions every step; only returns currently legal actions
  - blocks repeated no-op (state_hash, action) pairs
  - RESET on GAME_OVER, keep playing until WIN or step budget
  - ACTION6 coordinates from frame-derived candidate set (non-background
    center-of-mass and its jitter ring); never pure random coordinates
  - no game-ID special-case rule, no ARC-2 imports, no network, no LB feedback
"""
from __future__ import annotations

import hashlib
from typing import Any

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent


class MyAgent(Agent):
    MAX_ACTIONS = 200

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        digest = hashlib.sha256(
            ("arc3-cleanroom-baseline-v1|" + str(self.game_id)).encode("utf-8")
        ).digest()
        self._seed = int.from_bytes(digest[:8], "big")
        self._counter = 0
        self._seen_state_action: set[tuple[int, int]] = set()
        self._candidate_points: list[tuple[int, int]] = []
        self._grid_h = self._grid_w = 64

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    def _next_rand(self, bound: int) -> int:
        self._counter += 1
        material = (self._seed + self._counter * 2654435761) & 0xFFFFFFFFFFFFFFFF
        return material % bound

    def _frame_hash(self, latest_frame: FrameData) -> int:
        try:
            arr = getattr(latest_frame, "image", None)
            if arr is None:
                arr = getattr(latest_frame, "grid", None)
            if arr is not None:
                return int(hashlib.sha256(arr.tobytes()).hexdigest()[:16], 16)
        except Exception:  # noqa: BLE001
            pass
        return len(str(latest_frame))

    def _refresh_candidates(self, latest_frame: FrameData) -> None:
        """Explainable ACTION6 candidates: center-of-mass of non-background pixels."""
        pts: list[tuple[int, int]] = []
        try:
            arr = getattr(latest_frame, "image", None)
            if arr is None:
                arr = getattr(latest_frame, "grid", None)
            if arr is not None:
                h, w = arr.shape[:2]
                self._grid_h, self._grid_w = h, w
                # background = most common value (mode of the frame)
                flat = arr.reshape(-1)
                vals, counts = __import__("numpy").unique(flat, return_counts=True)
                background = int(vals[int(counts.argmax())])
                ys, xs = __import__("numpy").where(arr != background)
                if len(xs) and len(ys):
                    cx, cy = int(xs.mean()), int(ys.mean())
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            x = max(0, min(w - 1, cx + dx))
                            y = max(0, min(h - 1, cy + dy))
                            pts.append((x, y))
        except Exception:  # noqa: BLE001
            pts = []
        self._candidate_points = pts or [(31, 31)]

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        self._refresh_candidates(latest_frame)
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            action = GameAction.RESET
        else:
            avail = getattr(latest_frame, "available_actions", None)
            legal = [
                a for a in GameAction
                if a is not GameAction.RESET
                and (avail is None or a.value in avail)
            ]
            if not legal:
                # when legality metadata is unavailable, allow simple actions only
                legal = [a for a in GameAction if a.is_simple()]
            state_hash = self._frame_hash(latest_frame)
            # block repeated (state, action) no-ops
            fresh = [
                a for a in legal if (state_hash, a.value) not in self._seen_state_action
            ] or legal
            action = fresh[self._next_rand(len(fresh))]
            self._seen_state_action.add((state_hash, action.value))
            if action.is_complex():
                x, y = self._candidate_points[
                    self._next_rand(len(self._candidate_points))
                ]
                action.set_data({"game_id": str(self.game_id), "x": x, "y": y})
                action.reasoning = {"why": "non-background center-of-mass candidate"}
            else:
                action.reasoning = f"deterministic simple action: {action.value}"
        return action
