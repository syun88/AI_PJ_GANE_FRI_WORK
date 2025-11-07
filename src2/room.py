from dataclasses import dataclass
from typing import Tuple, Dict, Optional, Iterable, Set

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


    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.h and 0 <= c < self.w


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
        enemy_set = set(enemies or [])
        goal = self._goal

        for r in range(self.h):
            lines.append(horizontal)
            row_cells = []
            for c in range(self.w):
                ch = " "
                if (r, c) in door_set:
                    ch = "D"
                if goal is not None and (r, c) == goal:
                    ch = "G"
                if (r, c) in enemy_set:
                    ch = "E"
                if (r, c) == player_pos:
                    ch = "P"
                row_cells.append(f" {ch} ")
            lines.append("|" + "|".join(row_cells) + "|")
        lines.append(horizontal)
        return lines
