"""
High-level package exports for the haunted ruin escape prototype.

The package provides dataclasses for entities, room definitions,
and a light-weight engine loop intended to be extended by the team.
"""

from .entities import Player, Ghost, Item, ItemType
from .room import Room, Door
from .state import GameState
from .engine import GameEngine

__all__ = [
    "Player",
    "Ghost",
    "Item",
    "Room",
    "Door",
    "GameState",
    "GameEngine",
    "ItemType",
]
