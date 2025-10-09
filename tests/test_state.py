"""Minimal smoke tests for the haunted ruin escape prototype."""

import unittest

from haikyo_escape.entities import Ghost, Item, ItemType, Player
from haikyo_escape.room import Door, Room
from haikyo_escape.state import GameState


class GameStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rooms = {
            "r1": Room(room_id="r1", name="Room 1"),
            "r2": Room(room_id="r2", name="Room 2"),
        }
        self.rooms["r1"].add_door("east", Door(target_room_id="r2"))
        self.rooms["r2"].add_door("west", Door(target_room_id="r1"))

        self.player = Player(entity_id="player", name="Hero", room_id="r1")
        self.ghost = Ghost(entity_id="ghost", name="Ghost", room_id="r2")
        self.state = GameState(
            rooms=self.rooms,
            player=self.player,
            ghosts=[self.ghost],
            exit_room_id="r2",
        )

    def test_player_has_key_triggers_victory(self) -> None:
        key = Item(
            item_id="key1",
            name="Key",
            item_type=ItemType.KEY,
            room_id="r1",
            hidden=False,
        )
        self.state.add_item(key)
        self.player.take_item(key)
        self.player.move_to("r2")
        self.ghost.move_to("r1")  # keep ghost away from exit to simulate success

        self.state.check_victory()

        self.assertTrue(self.state.is_over)
        self.assertEqual(self.state.winner, "player")

    def test_ghost_collides_with_player(self) -> None:
        self.ghost.move_to("r1")
        self.state.check_victory()
        self.assertTrue(self.state.is_over)
        self.assertEqual(self.state.winner, "ghosts")


if __name__ == "__main__":
    unittest.main()
