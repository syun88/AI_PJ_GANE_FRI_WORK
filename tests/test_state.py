"""Unit tests for the haunted ruin escape state helpers."""

import unittest

from haikyo_escape.entities import Ghost, Item, ItemType, Player
from haikyo_escape.room import Door, Room
from haikyo_escape.state import ActionResult, GameState
from haikyo_escape.types import Direction


class GameStateTest(unittest.TestCase):
    def make_state(self) -> GameState:
        room_a = Room(room_id="room_a", name="Room A")
        room_b = Room(room_id="room_b", name="Room B")

        # Add a couple of walls to ensure collision checks behave.
        room_a.add_wall((4, 1))
        room_b.add_wall((2, 4))

        # Exploration tiles so items can be placed.
        room_a.add_explore_position((4, 2))
        room_b.add_explore_position((0, 2))

        room_a.add_door(
            Direction.EAST,
            Door(
                target_room_id="room_b",
                position=(5, 2),
                target_position=(0, 2),
                direction=Direction.EAST,
            ),
        )
        room_b.add_door(
            Direction.WEST,
            Door(
                target_room_id="room_a",
                position=(0, 2),
                target_position=(5, 2),
                direction=Direction.WEST,
            ),
        )

        player = Player(entity_id="player", name="Hero", room_id="room_a", position=(4, 2))

        ghost = Ghost(entity_id="ghost", name="Test Ghost", room_id="room_b", position=(1, 1))
        ghost.is_spawned = True

        state = GameState(
            rooms={"room_a": room_a, "room_b": room_b},
            player=player,
            ghosts=[ghost],
            exit_room_id="room_b",
            exit_position=(0, 2),
            start_room_id="room_a",
            start_position=(4, 2),
            safe_rooms={"room_a"},
        )
        return state

    def test_exit_requires_master_key(self) -> None:
        state = self.make_state()
        result = state.move_player_step(Direction.EAST)
        self.assertEqual(result, ActionResult.SUCCESS)
        self.assertEqual(state.player.room_id, "room_b")
        state.check_victory()
        self.assertFalse(state.is_over)
        self.assertIsNone(state.winner)

    def test_exit_with_master_key_wins(self) -> None:
        state = self.make_state()
        key = Item(
            item_id="master_key",
            name="Master Key",
            item_type=ItemType.KEY,
            room_id="room_a",
            hidden=False,
            position=(4, 2),
            metadata={"is_master": True},
        )
        state.add_item(key)
        self.assertTrue(state.pickup_item(key.item_id))

        result = state.move_player_step(Direction.EAST)
        self.assertEqual(result, ActionResult.SUCCESS)
        state.check_victory()
        self.assertTrue(state.is_over)
        self.assertEqual(state.winner, "player")

    def test_ghost_captures_player(self) -> None:
        state = self.make_state()
        state.player.move_to("room_b")
        state.player.set_position((1, 1))
        state.check_victory()
        self.assertTrue(state.is_over)
        self.assertEqual(state.winner, "ghosts")

    def test_wall_blocks_movement(self) -> None:
        state = self.make_state()
        state.player.set_position((4, 2))
        result = state.move_player_step(Direction.NORTH)
        self.assertEqual(result, ActionResult.BLOCKED)
        self.assertEqual(state.player.position, (4, 2))


if __name__ == "__main__":
    unittest.main()
