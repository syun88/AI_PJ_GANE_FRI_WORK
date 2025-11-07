from dataclasses import dataclass
from typing import Tuple, Dict, Optional

Coord = Tuple[int, int]


@dataclass(frozen=True)
class Door:
    pos: Coord
    target_room: int
    target_pos: Coord


class Room:
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

    # ドアまわり以下は変更しない
    def set_door(self, pos: Coord, to_room: int, to_pos: Coord) -> None:
        if not self.in_bounds(*pos):
            raise ValueError(f"ドア位置 {pos} が範囲外です（room h={self.h}, w={self.w}）")
        self._doors[pos] = Door(pos=pos, target_room=to_room, target_pos=to_pos)

    def remove_door(self, pos: Coord) -> None:
        self._doors.pop(pos, None)

    def get_door(self, pos: Coord) -> Optional[Door]:
        return self._doors.get(pos)

    def door_positions(self):
        return set(self._doors.keys())

    def set_goal(self, pos: Coord) -> None:
        if not self.in_bounds(*pos):
            raise ValueError(f"ゴール位置 {pos} が範囲外です（room h={self.h}, w={self.w}）")
        self._goal = pos

    def get_goal(self) -> Optional[Coord]:
        return self._goal

    def render_lines(self, player_pos: Coord) -> list:
        horizontal = "+" + "+".join(["---"] * self.w) + "+"
        lines = []
        door_set = self.door_positions()
        goal = self._goal
        obst = self._obstacles  # ← 障害物参照

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
                if (r, c) == player_pos:
                    ch = "P"
                row_cells.append(f" {ch} ")
            lines.append("|" + "|".join(row_cells) + "|")
        lines.append(horizontal)
        return lines
