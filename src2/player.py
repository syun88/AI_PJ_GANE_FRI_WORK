from typing import Tuple

Coord = Tuple[int, int]


class Player:
    def __init__(self, pos: Coord):
        self.pos: Coord = pos

    def set_position(self, pos: Coord) -> None:
        self.pos = pos

    def move_by(self, dr: int, dc: int) -> Coord:
        r, c = self.pos
        return (r + dr, c + dc)
