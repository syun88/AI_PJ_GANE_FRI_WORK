from typing import Tuple

Coord = Tuple[int, int]


class Player:
    def __init__(self, pos: Coord):
        self.pos: Coord = pos
        self.has_key: bool = False

    def set_position(self, pos: Coord) -> None:
        self.pos = pos

    def move_by(self, dr: int, dc: int) -> Coord:
        r, c = self.pos
        return (r + dr, c + dc)

    def obtain_key(self) -> None:
        self.has_key = True
