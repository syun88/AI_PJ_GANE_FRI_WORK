"""
Room layout abstractions.

Each room is represented as a 5x5 grid (default). Doors connect to other rooms.
This module intentionally leaves concrete layout details for the team to define.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional


@dataclass
class Door:
    """Represents a doorway between two rooms."""

    target_room_id: str
    is_locked: bool = False
    requires_key: bool = False
    # TODO: add properties for one-way doors or trap behaviour if needed.


@dataclass
class Room:
    """5x5 (configurable) room grid containing doors and items."""

    room_id: str
    name: str
    width: int = 5
    height: int = 5
    doors: Dict[str, Door] = field(default_factory=dict)  # direction -> Door
    obstacles: set[tuple[int, int]] = field(default_factory=set)

    def add_door(self, direction: str, door: Door) -> None:
        """Attach a door to the room in a given direction."""
        # TODO: enforce consistent direction naming convention (N/E/S/W etc.)
        self.doors[direction] = door

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def add_obstacle(self, position: tuple[int, int]) -> None:
        """Mark a grid position as blocked."""
        if not self.is_within_bounds(*position):
            raise ValueError(f"Obstacle {position} is outside room bounds.")
        self.obstacles.add(position)

    def available_directions(self) -> Iterable[str]:
        return self.doors.keys()

    def describe(self) -> str:
        """Return a human-readable summary of the room."""
        # TODO: incorporate hidden info rules when revealing to the player.
        door_info = ", ".join(
            f"{direction} -> {door.target_room_id}{' (locked)' if door.is_locked else ''}"
            for direction, door in self.doors.items()
        )
        return f"{self.name} (doors: {door_info or 'none'})"
