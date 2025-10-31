"""廃墟脱出プロトタイプ向けの主要エクスポートをまとめたモジュール。

エンティティや部屋定義のデータクラスと、チームで拡張する軽量エンジンを提供する。
"""

from .dungeon import DungeonSetup, build_default_dungeon
from .entities import Ghost, Item, ItemType, Player
from .room import Door, Room
from .state import GameState
from .engine import GameEngine
from .types import Direction

__all__ = [
    "Player",
    "Ghost",
    "Item",
    "Room",
    "Door",
    "GameState",
    "GameEngine",
    "DungeonSetup",
    "build_default_dungeon",
    "ItemType",
    "Direction",
]
