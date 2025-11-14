from dataclasses import dataclass
from typing import Tuple, Dict, Optional, Iterable, Set
import unicodedata

Coord = Tuple[int, int]


@dataclass(frozen=True)
class Door:
    pos: Coord
    target_room: int
    target_pos: Coord


class Room:
    CELL_WIDTH = 4
    def __init__(self, h: int, w: int):
        self.h = h
        self.w = w
        self._doors: Dict[Coord, Door] = {}
        self._goal: Optional[Coord] = None
        self._obstacles: set[Coord] = set()  # ← 障害物追加

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.h and 0 <= c < self.w

    # 障害物管理の最小 API
    def add_obstacle(self, pos: Coord):
        if not self.in_bounds(*pos):
            raise ValueError(f"障害物位置 {pos} が範囲外です")
        self._obstacles.add(pos)

    def remove_obstacle(self, pos: Coord):
        self._obstacles.discard(pos)

    def obstacle_positions(self):
        return set(self._obstacles)

    def has_obstacle(self, pos: Coord) -> bool:
        return pos in self._obstacles

    # ドアまわり以下は変更しない
    def set_door(self, pos: Coord, to_room: int, to_pos: Coord) -> None:
        if not self.in_bounds(*pos):
            raise ValueError(f"ドア位置 {pos} が範囲外です（room h={self.h}, w={self.w}）")
        self._doors[pos] = Door(pos=pos, target_room=to_room, target_pos=to_pos)

    def remove_door(self, pos: Coord) -> None:
        self._doors.pop(pos, None)

    def get_door(self, pos: Coord) -> Optional[Door]:
        return self._doors.get(pos)

    def door_positions(self) -> Set[Coord]:
        return set(self._doors.keys())

    def door_positions_to(self, target_room: int) -> Set[Coord]:
        return {pos for pos, door in self._doors.items() if door.target_room == target_room}

    def set_goal(self, pos: Coord) -> None:
        if not self.in_bounds(*pos):
            raise ValueError(f"ゴール位置 {pos} が範囲外です（room h={self.h}, w={self.w}）")
        self._goal = pos

    def get_goal(self) -> Optional[Coord]:
        return self._goal

    def render_lines(
        self,
        player_pos: Coord,
        enemies: Optional[Iterable[Coord]] = None,
        items: Optional[Dict[Coord, str]] = None,
        use_color: bool = False,
    ) -> list:
        horizontal = "+" + "+".join(["-" * self.CELL_WIDTH] * self.w) + "+"
        lines = []
        door_set = self.door_positions()
        enemy_set = set(enemies or [])
        goal = self._goal
        obst = self._obstacles  # ← 障害物参照
        item_map = items or {}

        for r in range(self.h):
            lines.append(horizontal)
            row_cells = []
            for c in range(self.w):
                ch = " "
                if (r, c) in obst:
                    ch = "#"          # ← 障害物
                if (r, c) in door_set:
                    ch = "D"
                if goal is not None and (r, c) == goal:
                    ch = "G"
                if (r, c) in item_map:
                    ch = "？"
                if (r, c) in enemy_set:
                    ch = "鬼"
                if (r, c) == player_pos:
                    ch = "人"
                row_cells.append(self._format_cell(ch, use_color))
            lines.append("|" + "|".join(row_cells) + "|")
        lines.append(horizontal)
        return lines

    def _format_cell(self, ch: str, use_color: bool) -> str:
        colored = self._colorize_cell(ch, use_color)
        width = self._char_width(ch)
        padding = max(self.CELL_WIDTH - width, 0)
        left = padding // 2
        right = padding - left
        return f"{' ' * left}{colored}{' ' * right}"

    @staticmethod
    def _colorize_cell(ch: str, use_color: bool) -> str:
        if not use_color:
            return ch
        color_map = {
            "人": "\033[1;36m",
            "鬼": "\033[1;31m",
            "？": "\033[1;33m",
            "#": "\033[90m",
            "D": "\033[32m",
            "G": "\033[1;33m",
        }
        reset = "\033[0m"
        prefix = color_map.get(ch)
        if not prefix:
            return ch
        return f"{prefix}{ch}{reset}"

    @staticmethod
    def _char_width(ch: str) -> int:
        if not ch:
            return 0
        if unicodedata.east_asian_width(ch[0]) in {"F", "W"}:
            return 2
        return 1
