"""
Entry point for quick experiments with the haunted ruin escape prototype.
廃墟脱出プロトタイプを手軽に試すためのエントリーポイント。

This script wires the engine with very simple CLI callbacks so teammates can
incrementally test mechanics without external dependencies.
シンプルなCLIコールバックでエンジンを動かし、外部依存なしで検証できる。
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Optional

# Ensure the `src/` directory is on sys.path regardless of invocation style.
# 実行方法に関わらず `src/` ディレクトリをモジュール検索パスに含める。
PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from haikyo_escape.engine import GameEngine
from haikyo_escape.entities import Ghost, Item, ItemType, Player
from haikyo_escape.room import Door, Room
from haikyo_escape.state import GameState


def build_sample_state() -> GameState:
    """Creates a tiny playable network of rooms for demonstration.
    サンプル用に小規模な部屋ネットワークを構築する。
    """
    # Define just three rooms for the sample; expand to ten for the full design.
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
    # TODO: Add dummy keys and obstacles as the layout evolves. / ダミー鍵や障害物などもここで追加する。
    return game_state


def print_welcome() -> None:
    """Display basic instructions for CLI users.
    CLI 利用者向けの簡単な説明を表示する。
    """
    divider = "=" * 40
    print(divider)
    print(" Haunted Ruin Escape Prototype (CLI)")
    print(" Commands: move:<dir>, search, wait, help, quit")
    print(" Exit with 'quit' or Ctrl+C / 終了: quit または Ctrl+C")
    print(divider)


def print_help(room: Room, player: Player) -> None:
    """Print the command list without consuming a turn.
    ターンを消費せずにコマンド一覧を表示する。
    """
    print("\n[Help] コマンド一覧 / Command reference")
    print("  move:<dir>  - 例: move:east。指定方向のドアがあれば移動します。")
    print("  search      - 現在の部屋を探索し、隠されたアイテムを見つけます。")
    print("  wait        - そのターンは何もしません。（幽霊の動きのみ観察）")
    print("  help        - この一覧を再表示します。")
    print("  quit        - すぐにゲームを終了します。")
    print(" 現在の部屋:", room.describe())
    inventory_names = [item.name for item in player.inventory] or ["なし / none"]
    print(" 所持アイテム:", ", ".join(inventory_names))


def cli_player_choice(state: GameState, player: Player) -> str:
    """Prompt-driven player input.
    プロンプトに基づきプレイヤーの入力を受け付ける。
    """
    room = state.rooms[player.room_id]
    print(f"\n--- Turn {state.turn_count} ---")
    print(room.describe())
    print(f"Inventory: {[item.name for item in player.inventory]}")
    print("Doors:", ", ".join(room.available_directions()) or "none")

    while True:
        action = input("Action (move:<dir>/search/wait/help/quit): ").strip().lower()

        if not action:
            return "search"

        if action == "help":
            print_help(room, player)
            continue

        if action == "quit":
            state.is_over = True
            state.winner = state.winner or "quit"
            return "quit"

        if action in {"search", "wait"} or action.startswith("move:"):
            return action

        print("[Invalid] 未知のコマンドです。help で一覧を確認してください。")


def random_ghost_move(state: GameState, ghost: Ghost) -> Optional[str]:
    """Randomly pick an available door, respecting the no-repeat rule.
    連続同部屋禁止ルールを守りつつ、利用可能なドアからランダムに選ぶ。
    """
    # TODO: Replace with dice-based table when the official rule is ready. / サイコロ対応表を導入したらここを差し替える。
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
    print_welcome()
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
