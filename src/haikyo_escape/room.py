"""
Room layout abstractions for the digital haunted ruin escape.
デジタル版廃墟脱出ゲーム向けの部屋レイアウト抽象化。

Each room is a grid (default 6x6) with walls, exploration points, and doors that
link to other rooms. One-way exits and locked doors are supported so designers
can shape maze-like experiences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Set

from .types import Direction, Position


@dataclass
class Door:
    """Represents a doorway on a specific tile within a room."""

    target_room_id: str
    position: Position
    target_position: Position
    direction: Direction
    is_locked: bool = False
    requires_key: bool = False
    one_way: bool = False


@dataclass
class Room:
    """6x6 room grid containing walls, exploration tiles, and door definitions."""

    room_id: str
    name: str
    width: int = 6
    height: int = 6
    doors: Dict[Direction, Door] = field(default_factory=dict)
    walls: Set[Position] = field(default_factory=set)
    fragile_walls: Set[Position] = field(default_factory=set)
    explore_positions: Set[Position] = field(default_factory=set)
    one_way_exits: Dict[Position, Set[Direction]] = field(default_factory=dict)
    door_positions: Dict[Position, Door] = field(default_factory=dict)

    def is_within_bounds(self, position: Position) -> bool:
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, position: Position) -> bool:
        return self.is_within_bounds(position) and position not in self.walls

    def add_wall(self, position: Position) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Wall {position} is outside room bounds.")
        self.walls.add(position)

    def add_explore_position(self, position: Position) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Explore tile {position} is outside room bounds.")
        self.explore_positions.add(position)

    def add_fragile_wall(self, position: Position) -> None:
        """Register a wall that can later be broken to create a tunnel."""
        self.add_wall(position)
        self.fragile_walls.add(position)

    def remove_wall(self, position: Position) -> None:
        self.walls.discard(position)
        self.fragile_walls.discard(position)

    def add_one_way_exit(self, position: Position, allowed_directions: Iterable[Direction]) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"One-way tile {position} is outside room bounds.")
        self.one_way_exits[position] = set(allowed_directions)

    def add_door(self, direction: Direction, door: Door) -> None:
        if direction in self.doors:
            raise ValueError(f"Door already registered for {direction} in {self.room_id}.")
        if not self.is_within_bounds(door.position):
            raise ValueError(f"Door position {door.position} is outside room bounds.")
        self.doors[direction] = door
        self.door_positions[door.position] = door

    def door_at(self, position: Position) -> Optional[Door]:
        return self.door_positions.get(position)

    def allows_exit_from(self, position: Position, direction: Direction) -> bool:
        allowed = self.one_way_exits.get(position)
        return allowed is None or direction in allowed

    def is_fragile_wall(self, position: Position) -> bool:
        return position in self.fragile_walls

    def available_directions(self) -> Iterable[str]:
        return (direction.name.lower() for direction in self.doors.keys())

    def describe(self) -> str:
        """Return a human-readable summary of the room, including door states."""
        door_info = ", ".join(
            f"{direction.name.lower()} -> {door.target_room_id}"
            f"{' (locked)' if door.is_locked else ''}"
            f"{' (one-way)' if door.one_way else ''}"
            for direction, door in self.doors.items()
        )
        explore_info = ", ".join(f"{pos}" for pos in sorted(self.explore_positions)) or "none"
        return f"{self.name} (doors: {door_info or 'none'}, explore tiles: {explore_info})"
