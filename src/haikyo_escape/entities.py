"""
Entity definitions for the haunted ruin escape prototype.

The intent is to give each teammate clear extension points:
    - Player actions
    - Ghost AI behaviour
    - Item interactions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ItemType(Enum):
    """Types of interactable items that can be placed in rooms."""

    KEY = auto()
    DUMMY_KEY = auto()
    OBSTACLE = auto()
    TOOL = auto()  # TODO: define tool uses (e.g., door unlock, distraction)


@dataclass
class Item:
    """Static representation of an item on the board."""

    item_id: str
    name: str
    item_type: ItemType
    room_id: str
    hidden: bool = True  # TODO: decide how hidden info is revealed to the player
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class Entity:
    """Base entity with a name and current room reference."""

    entity_id: str
    name: str
    room_id: str
    is_active: bool = True

    def move_to(self, next_room_id: str) -> None:
        """Update the entity location."""
        # TODO: validate that the destination room exists and is connected.
        self.room_id = next_room_id


@dataclass
class Player(Entity):
    """Player-controlled high school student."""

    inventory: list[Item] = field(default_factory=list)

    def has_item_type(self, item_type: ItemType) -> bool:
        return any(item.item_type == item_type for item in self.inventory)

    # TODO: evaluate whether aliasing helps or confuses future code.
    def has_item(self, item_type: ItemType) -> bool:
        return self.has_item_type(item_type)

    def take_item(self, item: Item) -> None:
        # TODO: enforce inventory limits or action cost if required.
        self.inventory.append(item)

    def drop_item(self, item_id: str) -> Optional[Item]:
        for idx, item in enumerate(self.inventory):
            if item.item_id == item_id:
                return self.inventory.pop(idx)
        return None


@dataclass
class Ghost(Entity):
    """Ghost opponent that moves after the player."""

    aggression: float = 0.5  # 0-1 scale; TODO: tune for difficulty settings
    cannot_repeat_room: bool = True
    last_room_id: Optional[str] = None

    def choose_next_room(self, available_rooms: list[str]) -> Optional[str]:
        """Placeholder logic for ghost movement decision."""
        # TODO: replace with dice table or AI script.
        for room_id in available_rooms:
            if not self.cannot_repeat_room or room_id != self.last_room_id:
                return room_id
        return None

    def commit_move(self, next_room_id: str) -> None:
        self.last_room_id = self.room_id
        self.move_to(next_room_id)
