"""
Room layout abstractions.
部屋レイアウトを扱う抽象化モジュール。

Each room is represented as a 5x5 grid (default). Doors connect to other rooms.
各部屋はデフォルトで 5x5 マスのグリッドとして表現され、ドアで別室と接続します。
This module intentionally leaves concrete layout details for the team to define.
具体的なレイアウト定義はチームで自由に決められるよう余白を残しています。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional


@dataclass
class Door:
    """Represents a doorway between two rooms.
    2 つの部屋を接続するドア情報を表す。
    """

    target_room_id: str
    is_locked: bool = False
    requires_key: bool = False
    # TODO: add properties for one-way doors or trap behaviour if needed. / 片方向ドアや罠ギミックが必要ならプロパティを追加する。


@dataclass
class Room:
    """5x5 (configurable) room grid containing doors and items.
    ドアやアイテムを含む 5x5（設定で変更可能）の部屋グリッド。
    """

    room_id: str
    name: str
    width: int = 5
    height: int = 5
    doors: Dict[str, Door] = field(default_factory=dict)  # direction -> Door / 方向名 -> Door
    obstacles: set[tuple[int, int]] = field(default_factory=set)

    def add_door(self, direction: str, door: Door) -> None:
        """Attach a door to the room in a given direction.
        指定した方向にドア情報を登録する。
        """
        # TODO: enforce consistent direction naming convention (N/E/S/W etc.) / 方向名を統一（N/E/S/W など）するルールを決める。
        self.doors[direction] = door

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def add_obstacle(self, position: tuple[int, int]) -> None:
        """Mark a grid position as blocked.
        指定座標を障害物として扱う。
        """
        if not self.is_within_bounds(*position):
            raise ValueError(f"Obstacle {position} is outside room bounds.")
        self.obstacles.add(position)

    def available_directions(self) -> Iterable[str]:
        return self.doors.keys()

    def describe(self) -> str:
        """Return a human-readable summary of the room.
        部屋の概要を読みやすい文字列で返す。
        """
        # TODO: incorporate hidden info rules when revealing to the player. / 情報公開ルール（隠し要素の扱い）をここに組み込む。
        door_info = ", ".join(
            f"{direction} -> {door.target_room_id}{' (locked)' if door.is_locked else ''}"
            for direction, door in self.doors.items()
        )
        return f"{self.name} (doors: {door_info or 'none'})"
