"""
Turn-based engine that applies the haunted ruin escape ruleset.
廃墟からの脱出ゲームのルールを実行するターン制エンジン。

The engine is presentation-agnostic: input/output is provided via callbacks so
CLI や GUI、シミュレーションを自由に差し替えられる。
"""

from __future__ import annotations

import random
from typing import Callable, Optional

from .entities import Ghost, ItemType, Player
from .state import ActionResult, GameState, TurnPhase
from .types import Direction


ChoiceFunc = Callable[[GameState, Player], str]
RoomRevealFunc = Callable[[GameState], None]


class GameEngine:
    """Coordinates player turns, ghost resolution, and win/lose checks."""

    def __init__(
        self,
        state: GameState,
        player_choice_fn: ChoiceFunc,
        reveal_callback: Optional[RoomRevealFunc] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.state = state
        self.player_choice_fn = player_choice_fn
        self.reveal_callback = reveal_callback
        self.rng = rng or random.Random(state.rng_seed)
        self.next_first_spawn_threshold = 5

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_turn(self) -> None:
        """Execute a full player + ghost cycle."""
        if self.state.is_over:
            return

        self.state.turn_count += 1
        self.state.phase = TurnPhase.PLAYER_DECISION
        self.state.tick_start_of_turn()

        raw_action = self.player_choice_fn(self.state, self.state.player)
        action_consumed = self._resolve_player_action(raw_action)

        if self.state.is_over:
            return

        if action_consumed:
            self.state.increment_action_count()
            self._maybe_spawn_ghosts()

        self.state.check_victory()
        if self.state.is_over:
            return

        self.state.phase = TurnPhase.GHOST_MOVEMENT
        self._move_ghosts()

        self.state.phase = TurnPhase.RESOLUTION
        self.state.check_victory()

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------
    def _resolve_player_action(self, raw_action: str) -> bool:
        action = (raw_action or "").strip()
        if not action:
            self.state.record("No action specified.")
            return False

        tokens = action.split()
        verb = tokens[0].lower()
        args = tokens[1:]

        if verb == "move":
            return self._handle_move(args)
        if verb == "search":
            self.state.reveal_items_at_player()
            return True
        if verb == "take":
            return self._handle_take(args)
        if verb == "use":
            return self._handle_use(args)
        if verb == "wait":
            self.state.record("Player waits and listens to the silence...")
            return True
        if verb == "quit":
            self.state.is_over = True
            self.state.winner = "quit"
            self.state.record("Player chose to quit the expedition.")
            return False

        self.state.record(f"Unknown action '{raw_action}'.")
        return False

    def _handle_move(self, args: list[str]) -> bool:
        if not args:
            self.state.record("Specify at least one direction (north/east/south/west).")
            return False

        max_steps = self.state.player.current_speed
        if len(args) > max_steps:
            self.state.record(
                f"Speed limit allows {max_steps} step(s); extra directions are ignored."
            )
            args = args[:max_steps]

        attempted = False
        for token in args:
            try:
                direction = Direction.from_token(token)
            except ValueError:
                self.state.record(f"Unsupported direction '{token}'.")
                continue

            attempted = True
            before_room = self.state.player.room_id
            result = self.state.move_player_step(direction)
            if result == ActionResult.SUCCESS:
                if self.reveal_callback and before_room != self.state.player.room_id:
                    self.reveal_callback(self.state)
            elif result == ActionResult.BLOCKED:
                break
            else:
                break

        return attempted

    def _handle_take(self, args: list[str]) -> bool:
        current_items = self.state.items_at_position(
            self.state.player.room_id, self.state.player.position, include_hidden=False
        )
        if not current_items:
            self.state.record("There is nothing here to pick up.")
            return False

        if not args or args[0].lower() == "all":
            success = False
            for item in current_items:
                success |= self.state.pickup_item(item.item_id)
            return success

        target = args[0].lower()
        for item in current_items:
            if item.item_id.lower() == target or item.name.lower() == target:
                return self.state.pickup_item(item.item_id)

        if target.isdigit():
            idx = int(target)
            if 0 <= idx < len(current_items):
                return self.state.pickup_item(current_items[idx].item_id)

        self.state.record("Cannot find the specified item to pick up.")
        return False

    def _handle_use(self, args: list[str]) -> bool:
        if not args:
            self.state.record("Specify which item to use (id or name).")
            return False

        query = args[0].lower()
        inventory = self.state.player.inventory

        target_item = None
        for item in inventory:
            if item.item_id.lower() == query or item.name.lower() == query:
                target_item = item
                break

        if target_item is None and query.isdigit():
            index = int(query)
            if 0 <= index < len(inventory):
                target_item = inventory[index]

        if target_item is None:
            self.state.record("No matching item in inventory.")
            return False

        if target_item.item_type == ItemType.SPEED_BOOST:
            duration = int(target_item.metadata.get("duration", 5))
            self.state.player.apply_speed_boost(duration)
            self.state.record(f"Speed boost activated for {duration} turn(s).")
            self.state.consume_item(target_item.item_id)
            return True

        if target_item.item_type == ItemType.GHOST_FREEZE:
            duration = int(target_item.metadata.get("duration", 3))
            self.state.freeze_room(self.state.player.room_id, duration)
            for ghost in self.state.active_ghosts():
                if ghost.room_id == self.state.player.room_id:
                    ghost.apply_freeze(duration)
            self.state.consume_item(target_item.item_id)
            return True

        if target_item.item_type == ItemType.KEY:
            self.state.record("You hang onto the precious key for later.")
            return False

        if target_item.item_type == ItemType.DUMMY_KEY:
            self.state.record("The fake key rattles uselessly in your hand.")
            return False

        if target_item.item_type == ItemType.LORE:
            self.state.record("You skim the lore item. It might contain clues.")
            return False

        if target_item.item_type == ItemType.WALL_BREAKER:
            self.state.record("Search near brittle walls to put this breaker to use.")
            return False

        self.state.record("That item cannot be used right now.")
        return False

    # ------------------------------------------------------------------
    # Ghost logic
    # ------------------------------------------------------------------
    def _maybe_spawn_ghosts(self) -> None:
        # First ghost: triggered by movement thresholds.
        if (
            not self.state.first_ghost_spawned
            and self.state.total_steps >= self.next_first_spawn_threshold
            and self.state.player.room_id not in self.state.safe_rooms
        ):
            if self._roll_one_in_six():
                ghost = self._next_unspawned_ghost()
                if ghost and self.state.spawn_ghost(ghost):
                    self.state.first_ghost_spawned = True
            self.next_first_spawn_threshold += 5

        # Second ghost: action-based 1/6 chance per turn after first ghost appears.
        if (
            self.state.first_ghost_spawned
            and not self.state.second_ghost_spawned
            and self.state.player.room_id not in self.state.safe_rooms
        ):
            if self._roll_one_in_six():
                ghost = self._next_unspawned_ghost()
                if ghost and self.state.spawn_ghost(ghost):
                    self.state.second_ghost_spawned = True

    def _next_unspawned_ghost(self) -> Optional[Ghost]:
        for ghost in self.state.ghosts:
            if not ghost.is_spawned:
                return ghost
        return None

    def _move_ghosts(self) -> None:
        for ghost in self.state.ghosts:
            if not ghost.is_spawned or not ghost.is_active:
                continue

            steps = self._roll_ghost_steps()
            self.state.move_ghost_towards_player(ghost, steps)

    def _roll_ghost_steps(self) -> int:
        # 1 step with probability 2/3, 2 steps with probability 1/3.
        return 1 if self.rng.random() < (2 / 3) else 2

    def _roll_one_in_six(self) -> bool:
        return self.rng.randint(1, 6) == 1
