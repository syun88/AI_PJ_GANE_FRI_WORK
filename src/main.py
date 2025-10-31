"""デジタル版「廃墟からの脱出」を手軽に試せるコマンドラインエントリ。"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Optional

# `python src/main.py` で実行した際にも `src/` ディレクトリをインポート可能にする。
PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from haikyo_escape.dungeon import build_default_dungeon
from haikyo_escape.engine import GameEngine
from haikyo_escape.entities import Ghost, Player
from haikyo_escape.state import GameState


def build_game_state(seed: Optional[int] = None) -> GameState:
    rng = random.Random(seed)
    setup = build_default_dungeon(rng)

    player = Player(
        entity_id="player",
        name="高校生プレイヤー",
        room_id=setup.start_room_id,
        position=setup.start_position,
    )

    ghosts = [
        Ghost(entity_id="ghost_a", name="白い影", room_id=setup.start_room_id, position=setup.start_position),
        Ghost(entity_id="ghost_b", name="黒い影", room_id=setup.start_room_id, position=setup.start_position),
    ]

    state = GameState(
        rooms=setup.rooms,
        player=player,
        ghosts=ghosts,
        exit_room_id=setup.exit_room_id,
        exit_position=setup.exit_position,
        start_room_id=setup.start_room_id,
        start_position=setup.start_position,
        safe_rooms=setup.safe_rooms,
        rng_seed=seed,
    )
    for item in setup.items.values():
        state.add_item(item)
    return state


def print_welcome(seed: Optional[int]) -> None:
    divider = "=" * 42
    print(divider)
    print(" Haunted Ruin Escape (Text Prototype)")
    print(" Commands: move <dirs>, search, take [all], use <id>, wait, quit")
    print(" Utility: help, look, inventory, items, log")
    if seed is not None:
        print(f" Seed: {seed}")
    print(divider)


def print_help() -> None:
    print("\n[Help / ヘルプ]")
    print("  move <dir ...>  : 例) move north east  (加速中は最大2方向)")
    print("  search          : 現在マスを探索し、アイテムを発見する")
    print("  take [all|id]   : 発見済みアイテムを拾う（IDまたは一覧番号）")
    print("  use <id|index>  : 所持アイテムを使用する（速度UPや幽霊停止など）")
    print("  wait            : 何もせず様子を見る")
    print("  quit            : ゲームを終了する")
    print("  look            : 現在の部屋情報を再表示")
    print("  inventory       : 所持アイテムを表示")
    print("  items           : 足元にある発見済みアイテムを表示")
    print("  log             : 直近のログを確認")


def describe_room(state: GameState) -> None:
    room = state.rooms[state.player.room_id]
    print(f"\n[Location] {room.name} ({state.player.room_id})")
    print(f" Position: {state.player.position}")
    doors = ", ".join(f"{direction.name.lower()}" for direction in room.doors.keys()) or "none"
    print(f" Doors: {doors}")
    if room.explore_positions:
        explore = ", ".join(str(pos) for pos in sorted(room.explore_positions))
        print(f" Explore tiles: {explore}")
    print(f" Movement speed: {state.player.current_speed} step(s) this turn")


def list_inventory(state: GameState) -> None:
    if not state.player.inventory:
        print(" Inventory is empty.")
        return
    print(" Inventory:")
    for idx, item in enumerate(state.player.inventory):
        extra = item.metadata.get("duration")
        meta = f" (duration={extra})" if extra is not None else ""
        print(f"  [{idx}] {item.item_id} - {item.name}{meta}")


def list_floor_items(state: GameState) -> None:
    items = state.items_at_position(state.player.room_id, state.player.position, include_hidden=False)
    if not items:
        print(" No visible items on this tile.")
        return
    print(" Items on the ground:")
    for idx, item in enumerate(items):
        print(f"  [{idx}] {item.item_id} - {item.name}")


def reveal_room(state: GameState) -> None:
    room = state.rooms[state.player.room_id]
    print(f"\n> You step into {room.name}.")


def cli_player_choice(state: GameState, player: Player) -> str:
    describe_room(state)
    list_floor_items(state)

    while True:
        raw = input("\nCommand > ").strip()
        if not raw:
            continue

        lowered = raw.lower()
        if lowered in {"help", "h", "?"}:
            print_help()
            continue
        if lowered in {"look", "l"}:
            describe_room(state)
            continue
        if lowered in {"inventory", "inv", "i"}:
            list_inventory(state)
            continue
        if lowered in {"items", "floor"}:
            list_floor_items(state)
            continue
        if lowered == "log":
            print("[Log]")
            for entry in state.log[-10:]:
                print(" ", entry)
            continue

        # 行動コマンドの処理はゲームエンジンに委譲する。
        return lowered


def main(seed: Optional[int] = None) -> None:
    state = build_game_state(seed)
    print_welcome(seed)
    engine = GameEngine(
        state=state,
        player_choice_fn=cli_player_choice,
        reveal_callback=reveal_room,
    )

    while not state.is_over:
        engine.run_turn()

    print("\n=== Game Over ===")
    print(f"Winner: {state.winner}")
    print("Final log:")
    for entry in state.log:
        print("-", entry)


if __name__ == "__main__":
    cli_seed: Optional[int] = None
    if len(sys.argv) > 1:
        try:
            cli_seed = int(sys.argv[1])
        except ValueError:
            print("Seed must be an integer.", file=sys.stderr)
            sys.exit(1)
    main(cli_seed)
