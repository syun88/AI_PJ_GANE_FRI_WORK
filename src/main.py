"""
Entry point for quick experiments with the haunted ruin escape prototype.

This script wires the engine with very simple CLI callbacks so teammates can
incrementally test mechanics without external dependencies.
"""

from __future__ import annotations

import random
from typing import Optional

from haikyo_escape.engine import GameEngine
from haikyo_escape.entities import Ghost, Item, ItemType, Player
from haikyo_escape.room import Door, Room
from haikyo_escape.state import GameState


def build_sample_state() -> GameState:
    """Creates a tiny playable network of rooms for demonstration."""
    # サンプル用に3部屋のみ定義。10部屋版はこの辞書を拡張してください。
    rooms = {
        "entrance": Room(room_id="entrance", name="Entrance Hall"),
        "corridor": Room(room_id="corridor", name="Long Corridor"),
        "storage": Room(room_id="storage", name="Dusty Storage"),
    }

    rooms["entrance"].add_door("east", Door(target_room_id="corridor"))
    rooms["corridor"].add_door("west", Door(target_room_id="entrance"))
    rooms["corridor"].add_door("north", Door(target_room_id="storage", is_locked=True, requires_key=True))
    rooms["storage"].add_door("south", Door(target_room_id="corridor"))

    player = Player(entity_id="player", name="高校生ヒーロー", room_id="entrance")

    ghosts = [
        Ghost(entity_id="ghost_a", name="幽霊A", room_id="storage"),
        Ghost(entity_id="ghost_b", name="幽霊B", room_id="corridor"),
    ]

    key_item = Item(
        item_id="key_01",
        name="Rusty Key",
        item_type=ItemType.KEY,
        room_id="entrance",
        hidden=False,
    )

    game_state = GameState(
        rooms=rooms,
        player=player,
        ghosts=ghosts,
        exit_room_id="storage",
    )

    game_state.add_item(key_item)
    # TODO: ダミー鍵や障害物などもここで追加する。
    return game_state


def cli_player_choice(state: GameState, player: Player) -> str:
    """Prompt-driven player input."""
    room = state.rooms[player.room_id]
    print(f"\n--- Turn {state.turn_count + 1} ---")
    print(room.describe())
    print(f"Inventory: {[item.name for item in player.inventory]}")
    print("Doors:", ", ".join(room.available_directions()) or "none")
    action = input("Action (move:<dir>/search/end): ").strip().lower()
    return action or "search"


def random_ghost_move(state: GameState, ghost: Ghost) -> Optional[str]:
    """Randomly pick an available door, respecting the no-repeat rule."""
    # TODO: サイコロ対応表を導入したらここを差し替える。
    room = state.rooms[ghost.room_id]
    options = []
    for direction, door in room.doors.items():
        if door.target_room_id == ghost.last_room_id and ghost.cannot_repeat_room:
            continue
        options.append(door.target_room_id)
    if not options:
        return None
    return random.choice(options)


def reveal_room(room: Room) -> None:
    print(f"Entered {room.name}.")


def main() -> None:
    state = build_sample_state()
    engine = GameEngine(
        state=state,
        player_choice_fn=cli_player_choice,
        ghost_move_fn=random_ghost_move,
        reveal_room_fn=reveal_room,
    )

    while not state.is_over:
        engine.run_turn()

    print("\n=== Game Over ===")
    print("Winner:", state.winner)
    print("Log:")
    for entry in state.log:
        print("-", entry)


if __name__ == "__main__":
    main()
