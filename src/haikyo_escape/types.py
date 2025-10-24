"""
Shared typing helpers for the haunted ruin escape engine.
共通型定義をまとめてエンジン全体で再利用できるようにする。
"""

from __future__ import annotations

from enum import Enum
from typing import Tuple

# Position on a room grid (x, y). Origin is top-left and x increases to the right.
# 部屋グリッド上の座標 (x, y)。原点は左上、x は右方向に増加する。
Position = Tuple[int, int]


class Direction(Enum):
    """Cardinal movement directions within a room grid."""

    NORTH = (0, -1)
    EAST = (1, 0)
    SOUTH = (0, 1)
    WEST = (-1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        return self.value

    @property
    def opposite(self) -> "Direction":
        mapping = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return mapping[self]

    @classmethod
    def from_token(cls, token: str) -> "Direction":
        token = token.lower()
        aliases = {
            "n": cls.NORTH,
            "north": cls.NORTH,
            "s": cls.SOUTH,
            "south": cls.SOUTH,
            "e": cls.EAST,
            "east": cls.EAST,
            "w": cls.WEST,
            "west": cls.WEST,
        }
        if token not in aliases:
            raise ValueError(f"Unsupported direction token: {token}")
        return aliases[token]

    @classmethod
    def tokens(cls) -> tuple[str, ...]:
        return ("north", "east", "south", "west")
