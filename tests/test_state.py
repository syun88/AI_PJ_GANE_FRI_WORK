"""廃墟脱出ゲーム用 GameState のユニットテスト。"""

import unittest

from haikyo_escape.entities import Ghost, Item, ItemType, Player
from haikyo_escape.room import Door, Room
from haikyo_escape.state import ActionResult, GameState
from haikyo_escape.types import Direction


class GameStateTest(unittest.TestCase):
    def make_state(self) -> GameState:
        room_a = Room(room_id="room_a", name="Room A")
        room_b = Room(room_id="room_b", name="Room B")

        # 壁を追加して衝突判定が正しく働くか確認できるようにする。
        room_a.add_wall((4, 1))
        room_b.add_wall((2, 4))

        # アイテムを配置できるよう探索マスを用意する。
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

    def test_search_breaks_fragile_wall_with_breaker(self) -> None:
        state = self.make_state()
        room = state.rooms["room_a"]
        room.add_fragile_wall((4, 3))
        breaker = Item(
            item_id="breaker",
            name="Breaker",
            item_type=ItemType.WALL_BREAKER,
            room_id="room_a",
            hidden=False,
            position=(4, 2),
            metadata={},
        )
        state.add_item(breaker)
        self.assertTrue(state.pickup_item(breaker.item_id))
        self.assertIsNotNone(state.player.find_item_of_type(ItemType.WALL_BREAKER))

        state.reveal_items_at_player()

        self.assertIsNone(state.player.find_item_of_type(ItemType.WALL_BREAKER))
        self.assertTrue(room.is_walkable((4, 3)))
        self.assertFalse(room.is_fragile_wall((4, 3)))
        self.assertTrue(any("brittle wall" in entry for entry in state.log))


if __name__ == "__main__":
    unittest.main()
