from dataclasses import dataclass
from typing import Tuple, Dict, Optional

Coord = Tuple[int, int]  # (row, col)


@dataclass(frozen=True)
class Door:
    pos: Coord            # この部屋でのドア位置
    target_room: int      # 遷移先の部屋インデックス
    target_pos: Coord     # 遷移先でのプレイヤー座標


class Room:
    def __init__(self, h: int, w: int):
        self.h = h
        self.w = w
        # 座標→Door の辞書（1部屋に複数ドアOK）
        self._doors: Dict[Coord, Door] = {}
        # 単一ゴール（必要なら複数にも拡張可）
        self._goal: Optional[Coord] = None

    # --- 基本 ---
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.h and 0 <= c < self.w

    # --- ドア操作API ---
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

    # --- ゴール操作API ---
    def set_goal(self, pos: Coord) -> None:
        if not self.in_bounds(*pos):
            raise ValueError(f"ゴール位置 {pos} が範囲外です（room h={self.h}, w={self.w}）")
        self._goal = pos

    def get_goal(self) -> Optional[Coord]:
        return self._goal

    # --- 表示 ---
    def render_lines(self, player_pos: Coord) -> list:
        """表示用に行ごとの文字列を返す（printは呼び出し側で）。"""
        horizontal = "+" + "+".join(["---"] * self.w) + "+"
        lines = []
        door_set = self.door_positions()
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
                if (r, c) == player_pos:
                    ch = "P"  # プレイヤー最優先表示
                row_cells.append(f" {ch} ")
            lines.append("|" + "|".join(row_cells) + "|")
        lines.append(horizontal)
        return lines
