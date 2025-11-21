from typing import Tuple

Coord = Tuple[int, int]


class Player:
    def __init__(self, pos: Coord):
        self.pos: Coord = pos
        self.keys_collected: int = 0

    def set_position(self, pos: Coord) -> None:
        self.pos = pos

    def move_by(self, dr: int, dc: int) -> Coord:
        r, c = self.pos
        return (r + dr, c + dc)

    def obtain_key(self) -> None:
        self.keys_collected += 1

    @property
    def has_key(self) -> bool:
        return self.keys_collected > 0
