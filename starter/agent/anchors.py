"""Trivial control policies for the 24h milestone (controls only, never
submission candidates), per docs/BASELINE_PROTOCOL.md:
  (A) one fixed legal action
  (B) uniformly random legal actions with a stable seed
Both reset only after GAME_OVER / NOT_PLAYED and only return currently
legal actions.
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

from arcengine import FrameDataRaw, GameAction, GameState


def _digest(game_id: str, salt: str) -> int:
    return int.from_bytes(
        hashlib.sha256((salt + "|" + game_id).encode("utf-8")).digest()[:8],
        "big",
    )


class FixedActionAnchor:
    """Control A: one fixed legal action repeated forever."""

    def __init__(self, game_id: str, max_steps: int = 40000) -> None:
        self.game_id = game_id
        self.max_steps = max_steps
        self.fixed_id: Optional[int] = None
        self.last_action_id: Optional[int] = None
        self.last_obs: Optional[dict[str, Any]] = None

    def choose_action(self, latest: FrameDataRaw) -> GameAction:
        if latest.state in (GameState.GAME_OVER, GameState.NOT_PLAYED):
            self.last_action_id = 0
            self.last_obs = None
            return GameAction.RESET
        avail = list(latest.available_actions) or [1, 2, 3, 4, 5, 7]
        if self.fixed_id is None or self.fixed_id not in avail:
            simple = [a for a in avail if 1 <= a <= 7 and a != 6]
            self.fixed_id = simple[0] if simple else avail[0]
        self.last_action_id = self.fixed_id
        self.last_obs = None
        return GameAction.from_id(self.fixed_id)


class UniformRandomAnchor:
    """Control B: uniformly random legal actions, stable per-game seed."""

    def __init__(
        self,
        game_id: str,
        max_steps: int = 40000,
        salt: str = "arc3-anchor-b-uniform|2026-10-15",
    ) -> None:
        self.game_id = game_id
        self.max_steps = max_steps
        self.seed = _digest(game_id, salt)
        self.counter = 0
        self.last_action_id: Optional[int] = None
        self.last_obs: Optional[dict[str, Any]] = None

    @staticmethod
    def _mix(x: int) -> int:
        mask = (1 << 64) - 1
        x = (x + 0x9E3779B97F4A7C15) & mask
        x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & mask
        x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & mask
        return x ^ (x >> 31)

    def _next(self, bound: int) -> int:
        self.counter += 1
        return self._mix(self.seed + self.counter * 0x9E3779B97F4A7C15) % bound

    def choose_action(self, latest: FrameDataRaw) -> GameAction:
        if latest.state in (GameState.GAME_OVER, GameState.NOT_PLAYED):
            self.last_action_id = 0
            self.last_obs = None
            return GameAction.RESET
        avail = list(latest.available_actions) or [1, 2, 3, 4, 5, 7]
        aid = avail[self._next(len(avail))]
        action = GameAction.from_id(aid)
        if aid == 6:
            x, y = self._next(64), self._next(64)
            action.set_data({"game_id": self.game_id, "x": x, "y": y})
        self.last_action_id = aid
        self.last_obs = None
        return action
