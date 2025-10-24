"""
Game state container and rule helpers for the haunted ruin escape.
ゲーム全体の状態を保持し、ルール判定を行うモジュール。

The intent is to keep core logic independent of presentation so that CLI, GUI,
and automated simulations can share the same engine.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from .entities import Ghost, Item, ItemType, Player
from .room import Door, Room
from .types import Direction, Position


class TurnPhase(Enum):
    """High-level turn phases to keep the loop explicit."""

    PLAYER_DECISION = auto()
    GHOST_MOVEMENT = auto()
    RESOLUTION = auto()


class ActionResult(Enum):
    """Outcome for player actions."""

    SUCCESS = auto()
    BLOCKED = auto()
    INVALID = auto()


@dataclass
class GameState:
    """
    Tracks all mutable simulation data required by the engine.
    エンジンが必要とする可変データをすべて保持する。
    """

    rooms: Dict[str, Room]
    player: Player
    ghosts: List[Ghost]
    items: Dict[str, Item] = field(default_factory=dict)
    exit_room_id: Optional[str] = None
    exit_position: Optional[Position] = None
    start_room_id: Optional[str] = None
    start_position: Position = (0, 0)
    safe_rooms: set[str] = field(default_factory=set)
    turn_count: int = 0
    phase: TurnPhase = TurnPhase.PLAYER_DECISION
    is_over: bool = False
    winner: Optional[str] = None
    log: List[str] = field(default_factory=list)
    rng_seed: Optional[int] = None

    # Gameplay counters
    total_steps: int = 0
    action_count: int = 0
    first_ghost_spawned: bool = False
    second_ghost_spawned: bool = False
    room_freeze_turns: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start_room_id:
            self.player.move_to(self.start_room_id)
        self.player.set_position(self.start_position)
        self.player.tick_effects()  # ensure counters non-negative

    # ------------------------------------------------------------------
    # Logging utilities
    # ------------------------------------------------------------------
    def record(self, message: str) -> None:
        """Append an event to the session log."""
        self.log.append(message)

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------
    def add_item(self, item: Item) -> None:
        if not item.position:
            raise ValueError("Item must have a position within its room.")
        if item.room_id not in self.rooms:
            raise ValueError(f"Item room {item.room_id} is not registered.")
        self.items[item.item_id] = item

    def items_in_room(self, room_id: str, include_hidden: bool = False) -> Iterable[Item]:
        for item in self.items.values():
            if item.room_id == room_id and (include_hidden or not item.hidden):
                yield item

    def items_at_position(self, room_id: str, position: Position, include_hidden: bool = False) -> list[Item]:
        return [
            item
            for item in self.items.values()
            if item.room_id == room_id
            and item.position == position
            and (include_hidden or not item.hidden)
        ]

    def reveal_items_at_player(self) -> list[Item]:
        """Reveal all hidden items at the player's current tile."""
        visible = []
        for item in self.items_at_position(self.player.room_id, self.player.position, include_hidden=True):
            if item.hidden:
                item.hidden = False
                visible.append(item)
        if visible:
            self.record(
                "Revealed items: " + ", ".join(item.name for item in visible)
            )
        else:
            self.record("Search found nothing.")
        return visible

    def pickup_item(self, item_id: str) -> bool:
        item = self.items.get(item_id)
        if not item or item.hidden:
            return False
        if item.room_id != self.player.room_id or item.position != self.player.position:
            return False
        self.player.take_item(item)
        item.room_id = "inventory"
        item.position = None
        item.hidden = False
        self.record(f"Picked up {item.name}.")
        return True

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def move_player_step(self, direction: Direction) -> ActionResult:
        """Attempt to move the player by one tile or through a door."""
        room = self.rooms[self.player.room_id]
        current_pos = self.player.position

        door_here = room.door_at(current_pos)
        if door_here and direction == door_here.direction:
            return self._move_player_through_door(door_here)

        if not room.allows_exit_from(current_pos, direction):
            self.record("One-way path blocks movement.")
            return ActionResult.BLOCKED

        dx, dy = direction.delta
        candidate = (current_pos[0] + dx, current_pos[1] + dy)
        door_ahead = room.door_at(candidate)
        if door_ahead and direction == door_ahead.direction:
            return self._move_player_through_door(door_ahead)

        if not room.is_walkable(candidate):
            self.record("A wall blocks the way.")
            return ActionResult.BLOCKED

        self.player.set_position(candidate)
        self.total_steps += 1
        self.record(f"Player moved to {self.player.position} in {room.room_id}.")
        return ActionResult.SUCCESS

    def _move_player_through_door(self, door: Door) -> ActionResult:
        """Handle door traversal, including locked doors."""
        if door.is_locked and not self._player_has_valid_key():
            self.record("Door is locked. Need the correct key.")
            return ActionResult.BLOCKED

        self.player.move_to(door.target_room_id)
        self.player.set_position(door.target_position)
        self.total_steps += 1
        self.record(
            f"Player moved through door to {door.target_room_id} @ {door.target_position}."
        )
        return ActionResult.SUCCESS

    def _player_has_valid_key(self) -> bool:
        for item in self.player.inventory:
            if item.item_type == ItemType.KEY and item.metadata.get("is_master", False):
                return True
        return False

    # ------------------------------------------------------------------
    # Turn bookkeeping
    # ------------------------------------------------------------------
    def tick_start_of_turn(self) -> None:
        """Apply start-of-turn decay for effects."""
        self.player.tick_effects()
        expired_rooms = []
        for room_id, remaining in self.room_freeze_turns.items():
            if remaining <= 1:
                expired_rooms.append(room_id)
            else:
                self.room_freeze_turns[room_id] = remaining - 1
        for room_id in expired_rooms:
            del self.room_freeze_turns[room_id]
            self.record(f"The ghost-freeze effect in {room_id} wears off.")

        for ghost in self.ghosts:
            ghost.tick_effects()

    def increment_action_count(self) -> None:
        self.action_count += 1

    # ------------------------------------------------------------------
    # Ghost helpers
    # ------------------------------------------------------------------
    def active_ghosts(self) -> Iterable[Ghost]:
        return (ghost for ghost in self.ghosts if ghost.is_spawned and ghost.is_active)

    def spawn_ghost(self, ghost: Ghost) -> bool:
        if ghost.is_spawned:
            return False
        if self.player.room_id in self.safe_rooms:
            self.record("Ghost cannot spawn while the player is in a safe room.")
            return False

        spawn_room_id = self.player.room_id
        room = self.rooms[spawn_room_id]
        spawn_position = self._farthest_door_position(room, self.player.position)
        if spawn_position is None:
            spawn_position = self.player.position  # fallback

        ghost.is_spawned = True
        ghost.move_to(spawn_room_id)
        ghost.set_position(spawn_position)
        ghost.last_room_id = spawn_room_id
        self.record(f"{ghost.name} materialises at {spawn_position} in {spawn_room_id}.")
        return True

    def _farthest_door_position(self, room: Room, origin: Position) -> Optional[Position]:
        if not room.doors:
            return None

        distance_map = self._distance_map(room.room_id, origin, for_player=True)
        farthest: Tuple[int, Position] | None = None
        for door in room.doors.values():
            distance = distance_map.get((room.room_id, door.position))
            if distance is None:
                continue
            if farthest is None or distance > farthest[0]:
                farthest = (distance, door.position)
        if farthest:
            return farthest[1]
        return None

    def move_ghost_towards_player(self, ghost: Ghost, steps: int) -> None:
        if ghost.frozen_turns > 0:
            self.record(f"{ghost.name} is frozen and cannot move.")
            return
        if self.is_room_frozen(ghost.room_id):
            self.record(f"{ghost.name} is bound by the freezing aura in {ghost.room_id}.")
            return
        if ghost.room_id in self.safe_rooms:
            self.record(f"{ghost.name} hesitates at the edge of a safe room.")
            return
        for _ in range(steps):
            path = self._shortest_path(
                (ghost.room_id, ghost.position),
                (self.player.room_id, self.player.position),
                for_player=False,
            )
            if len(path) <= 1:
                return
            next_room_id, next_pos = path[1]
            self.record(
                f"{ghost.name} moves from {(ghost.room_id, ghost.position)} to {(next_room_id, next_pos)}."
            )
            ghost.move_to(next_room_id)
            ghost.set_position(next_pos)

    def freeze_room(self, room_id: str, duration: int) -> None:
        self.room_freeze_turns[room_id] = max(self.room_freeze_turns.get(room_id, 0), duration)
        self.record(f"Room {room_id} is engulfed in a chilling aura for {duration} turns.")

    def is_room_frozen(self, room_id: str) -> bool:
        return self.room_freeze_turns.get(room_id, 0) > 0

    # ------------------------------------------------------------------
    # Pathfinding utilities
    # ------------------------------------------------------------------
    def _neighbors(
        self,
        room_id: str,
        position: Position,
        *,
        for_player: bool,
    ) -> list[tuple[str, Position]]:
        room = self.rooms[room_id]
        results: list[tuple[str, Position]] = []
        door_here = room.door_at(position)
        if door_here:
            if not for_player or (not door_here.is_locked or self._player_has_valid_key()):
                if for_player or door_here.target_room_id not in self.safe_rooms:
                    # Players respect door locks, ghosts ignore them.
                    results.append((door_here.target_room_id, door_here.target_position))

        for direction in Direction:
            if not room.allows_exit_from(position, direction):
                continue
            dx, dy = direction.delta
            next_pos = (position[0] + dx, position[1] + dy)
            if room.is_walkable(next_pos):
                neighbor_room = room_id
                if not for_player and neighbor_room in self.safe_rooms:
                    continue
                results.append((neighbor_room, next_pos))
        return results

    def _distance_map(
        self,
        origin_room_id: str,
        origin_position: Position,
        *,
        for_player: bool,
    ) -> Dict[tuple[str, Position], int]:
        visited: Dict[tuple[str, Position], int] = {}
        queue: Deque[tuple[str, Position]] = deque()
        queue.append((origin_room_id, origin_position))
        visited[(origin_room_id, origin_position)] = 0

        while queue:
            room_id, position = queue.popleft()
            distance = visited[(room_id, position)]
            for neighbor in self._neighbors(room_id, position, for_player=for_player):
                if neighbor in visited:
                    continue
                visited[neighbor] = distance + 1
                queue.append(neighbor)
        return visited

    def _shortest_path(
        self,
        origin: tuple[str, Position],
        destination: tuple[str, Position],
        *,
        for_player: bool,
    ) -> List[tuple[str, Position]]:
        queue: Deque[tuple[str, Position]] = deque()
        queue.append(origin)
        came_from: Dict[tuple[str, Position], Optional[tuple[str, Position]]] = {origin: None}

        while queue:
            current = queue.popleft()
            if current == destination:
                break
            for neighbor in self._neighbors(current[0], current[1], for_player=for_player):
                if neighbor in came_from:
                    continue
                came_from[neighbor] = current
                queue.append(neighbor)

        if destination not in came_from:
            return [origin]

        path: List[tuple[str, Position]] = []
        current = destination
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Victory / defeat checks
    # ------------------------------------------------------------------
    def check_victory(self) -> None:
        if self.is_over:
            return

        if self.player.room_id == self.exit_room_id and self.player.position == self.exit_position:
            if self._player_has_valid_key():
                self.is_over = True
                self.winner = "player"
                self.record("Player escapes through the back door!")
            else:
                self.record("The exit is locked tight. Need the correct key.")

        for ghost in self.active_ghosts():
            if ghost.room_id == self.player.room_id and ghost.position == self.player.position:
                self.is_over = True
                self.winner = "ghosts"
                self.record(f"{ghost.name} catches the player!")

    def reset(self) -> None:
        self.turn_count = 0
        self.phase = TurnPhase.PLAYER_DECISION
        self.is_over = False
        self.winner = None
        self.log.clear()
        self.total_steps = 0
        self.action_count = 0
        self.first_ghost_spawned = False
        self.second_ghost_spawned = False
        self.room_freeze_turns.clear()
