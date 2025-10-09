"""
High-level package exports for the haunted ruin escape prototype.
廃墟脱出プロトタイプ向けの主要エクスポートをまとめたモジュール。

The package provides dataclasses for entities, room definitions,
and a light-weight engine loop intended to be extended by the team.
エンティティや部屋定義のデータクラス、チームで拡張する軽量エンジンを提供する。
"""

from .entities import Player, Ghost, Item, ItemType
from .room import Room, Door
from .state import GameState
from .engine import GameEngine

__all__ = [
    "Player",
    "Ghost",
    "Item",
    "Room",
    "Door",
    "GameState",
    "GameEngine",
    "ItemType",
]
