from typing import Tuple

Coord = Tuple[int, int]


class Player:
    def __init__(self, pos: Coord):
        self.pos: Coord = pos

    def set_position(self, pos: Coord) -> None:
        self.pos = pos

    def move_by(self, dr: int, dc: int) -> Coord:
        """移動後の仮座標を返す（適用は呼び出し側）"""
        r, c = self.pos
        return (r + dr, c + dc)
