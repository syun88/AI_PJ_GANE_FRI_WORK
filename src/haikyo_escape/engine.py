"""
Core loop skeleton for the haunted ruin escape.

This engine does not perform real I/O; instead it exposes hooks so teammates
can plug in CLI, GUI, or scripted simulations.
"""

from __future__ import annotations

import random
from typing import Callable, Iterable, Optional

from .entities import Ghost, ItemType, Player
from .room import Door, Room
from .state import GameState, TurnPhase


ChoiceFunc = Callable[[GameState, Player], str]
GhostMoveFunc = Callable[[GameState, Ghost], Optional[str]]
RevealFunc = Callable[[Room], None]


class GameEngine:
    """
    Drives the turn-based flow.

    The engine is deliberately thin; logic is delegated to injected callables so
    the team can parallelise work (UI, AI, rule expansions).
    """

    def __init__(
        self,
        state: GameState,
        player_choice_fn: ChoiceFunc,
        ghost_move_fn: GhostMoveFunc,
        reveal_room_fn: Optional[RevealFunc] = None,
    ) -> None:
        self.state = state
        self.player_choice_fn = player_choice_fn
        self.ghost_move_fn = ghost_move_fn
        self.reveal_room_fn = reveal_room_fn

    def run_turn(self) -> None:
        """Execute a single player + ghost sequence."""
        if self.state.is_over:
            return

        self.state.turn_count += 1
        self.state.phase = TurnPhase.PLAYER_DECISION

        # Player decision (move or interact)
        action = self.player_choice_fn(self.state, self.state.player)
        # プレイヤー入力はコールバックで分離しているため、GUI/自動化にも対応しやすい。
        self.state.record(f"Turn {self.state.turn_count}: player chose {action}")
        self._resolve_player_action(action)

        if self.state.is_over:
            return

        if self.reveal_room_fn:
            current_room = self.state.rooms[self.state.player.room_id]
            self.reveal_room_fn(current_room)

        # Ghost movement
        self.state.phase = TurnPhase.GHOST_MOVEMENT
        for ghost in self.state.ghosts:
            next_room_id = self.ghost_move_fn(self.state, ghost)
            if next_room_id:
                ghost.commit_move(next_room_id)
                self.state.record(f"{ghost.name} moved to {ghost.room_id}")

        # Resolution
        self.state.phase = TurnPhase.RESOLUTION
        self.state.check_victory()

    def _resolve_player_action(self, action: str) -> None:
        """
        Handle abstract player actions.

        TODO: Replace string-based actions with structured commands once the
        action list is finalised (e.g., dataclass MoveCommand).
        """
        if action.startswith("move:"):
            _, direction = action.split(":", 1)
            self._move_player(direction.strip())
        elif action == "search":
            self._search_room()
        elif action == "wait":
            self.state.record("Player waits and observes.")
        elif action == "quit":
            self.state.is_over = True
            self.state.winner = self.state.winner or "quit"
            self.state.record("Player ended the session early.")
        else:
            self.state.record(f"Unknown action '{action}' ignored.")

    def _move_player(self, direction: str) -> None:
        player_room = self.state.rooms[self.state.player.room_id]
        door: Optional[Door] = player_room.doors.get(direction)
        if not door:
            self.state.record(f"No door to move {direction}.")
            return
        if door.is_locked and not self.state.player.has_item_type(ItemType.KEY):
            self.state.record("Door is locked. Need a key.")
            return

        self.state.player.move_to(door.target_room_id)
        self.state.record(f"Player moved to {door.target_room_id}")

    def _search_room(self) -> None:
        """
        Minimal search placeholder: reveal all items in the room.
        """
        # 検索処理の暫定実装。探索制限などはここを更新する。
        current_room_id = self.state.player.room_id
        found_items = [
            item
            for item in self.state.items.values()
            if item.room_id == current_room_id and item.hidden
        ]
        if not found_items:
            self.state.record("Search found nothing.")
            return

        random.shuffle(found_items)
        for item in found_items:
            item.hidden = False
            # TODO: prompt player whether to pick up or leave the item.
            self.state.player.take_item(item)
            self.state.record(f"Found and picked up {item.name}.")
