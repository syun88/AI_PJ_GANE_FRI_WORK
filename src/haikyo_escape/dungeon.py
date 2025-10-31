"""廃墟脱出ゲーム向けの標準ダンジョンレイアウトとアイテム配置を定義する。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from .entities import Item, ItemType
from .room import Door, Room
from .types import Direction, Position


@dataclass
class DungeonSetup:
    rooms: Dict[str, Room]
    items: Dict[str, Item]
    start_room_id: str
    start_position: Position
    exit_room_id: str
    exit_position: Position
    safe_rooms: set[str]


def build_default_dungeon(rng: Optional[random.Random] = None) -> DungeonSetup:
    rng = rng or random.Random()

    rooms = _build_rooms()
    _connect_rooms(rooms)

    start_room_id = "r0"
    start_position = (2, 5)
    exit_room_id = "r8"
    exit_position = (3, 0)
    safe_rooms = {start_room_id, "r1"}

    items = _generate_items(rooms, rng)

    return DungeonSetup(
        rooms=rooms,
        items=items,
        start_room_id=start_room_id,
        start_position=start_position,
        exit_room_id=exit_room_id,
        exit_position=exit_position,
        safe_rooms=safe_rooms,
    )


# ---------------------------------------------------------------------------
# 部屋レイアウト生成ヘルパー
# ---------------------------------------------------------------------------


def _build_rooms() -> Dict[str, Room]:
    rooms: Dict[str, Room] = {}

    def make_room(room_id: str, name: str) -> Room:
        room = Room(room_id=room_id, name=name)
        rooms[room_id] = room
        return room

    make_room("r0", "廃墟の玄関ホール")
    make_room("r1", "曲がりくねった廊下")
    make_room("r2", "旧理科室")
    make_room("r3", "崩れた踊り場")
    make_room("r4", "管理人室")
    make_room("r5", "音楽室跡")
    make_room("r6", "地下階段口")
    make_room("r7", "貯蔵庫")
    make_room("r8", "裏口の部屋")

    # シンプルな迷路になるよう壁を配置。
    rooms["r0"].add_wall((1, 3))
    rooms["r0"].add_wall((4, 2))
    rooms["r1"].add_wall((2, 2))
    rooms["r1"].add_wall((3, 2))
    rooms["r2"].add_wall((1, 1))
    rooms["r2"].add_fragile_wall((4, 4))
    rooms["r3"].add_wall((0, 2))
    rooms["r3"].add_fragile_wall((1, 2))
    rooms["r4"].add_wall((2, 3))
    rooms["r4"].add_wall((2, 4))
    rooms["r5"].add_wall((5, 1))
    rooms["r5"].add_wall((5, 2))
    rooms["r6"].add_fragile_wall((3, 3))
    rooms["r6"].add_wall((3, 4))
    rooms["r7"].add_wall((2, 1))
    rooms["r7"].add_fragile_wall((3, 1))
    rooms["r8"].add_wall((1, 4))
    rooms["r8"].add_wall((4, 2))

    # 探索マス（ピンクタイルに相当）を配置。
    rooms["r0"].add_explore_position((1, 1))
    rooms["r0"].add_explore_position((4, 4))
    rooms["r1"].add_explore_position((4, 1))
    rooms["r1"].add_explore_position((1, 4))
    rooms["r2"].add_explore_position((2, 3))
    rooms["r3"].add_explore_position((4, 0))
    rooms["r4"].add_explore_position((1, 1))
    rooms["r4"].add_explore_position((4, 4))
    rooms["r5"].add_explore_position((3, 3))
    rooms["r6"].add_explore_position((2, 2))
    rooms["r6"].add_explore_position((4, 5))
    rooms["r7"].add_explore_position((4, 2))
    rooms["r8"].add_explore_position((2, 1))
    rooms["r8"].add_explore_position((3, 4))

    # 一方通行マス（トラップ床や滑り床を想定）
    rooms["r3"].add_one_way_exit((5, 3), {Direction.SOUTH})
    rooms["r4"].add_one_way_exit((0, 5), {Direction.EAST})
    rooms["r6"].add_one_way_exit((1, 5), {Direction.NORTH})

    return rooms


def _connect_rooms(rooms: Dict[str, Room]) -> None:
    # 双方向ドアを素早く追加するユーティリティ。
    def connect_east_west(left: Room, right: Room, *, bidirectional: bool = True) -> None:
        left.add_door(
            Direction.EAST,
            Door(
                target_room_id=right.room_id,
                position=(5, 2),
                target_position=(0, 2),
                direction=Direction.EAST,
            ),
        )
        if bidirectional:
            right.add_door(
                Direction.WEST,
                Door(
                    target_room_id=left.room_id,
                    position=(0, 2),
                    target_position=(5, 2),
                    direction=Direction.WEST,
                ),
            )

    def connect_north_south(top: Room, bottom: Room, *, bidirectional: bool = True) -> None:
        top.add_door(
            Direction.SOUTH,
            Door(
                target_room_id=bottom.room_id,
                position=(3, 5),
                target_position=(3, 0),
                direction=Direction.SOUTH,
            ),
        )
        if bidirectional:
            bottom.add_door(
                Direction.NORTH,
                Door(
                    target_room_id=top.room_id,
                    position=(3, 0),
                    target_position=(3, 5),
                    direction=Direction.NORTH,
                ),
            )

    connect_east_west(rooms["r0"], rooms["r1"])
    connect_east_west(rooms["r1"], rooms["r2"])
    connect_east_west(rooms["r3"], rooms["r4"])
    connect_east_west(rooms["r4"], rooms["r5"])
    connect_east_west(rooms["r6"], rooms["r7"], bidirectional=False)
    rooms["r7"].add_door(
        Direction.EAST,
        Door(
            target_room_id=rooms["r8"].room_id,
            position=(5, 3),
            target_position=(0, 3),
            direction=Direction.EAST,
            one_way=True,
        ),
    )
    rooms["r8"].add_door(
        Direction.WEST,
        Door(
            target_room_id=rooms["r7"].room_id,
            position=(0, 3),
            target_position=(5, 3),
            direction=Direction.WEST,
            one_way=True,
        ),
    )

    connect_north_south(rooms["r0"], rooms["r3"])
    connect_north_south(rooms["r1"], rooms["r4"])
    connect_north_south(rooms["r2"], rooms["r5"])
    connect_north_south(rooms["r3"], rooms["r6"], bidirectional=False)
    connect_north_south(rooms["r4"], rooms["r7"])
    connect_north_south(rooms["r5"], rooms["r8"])


# ---------------------------------------------------------------------------
# アイテム配置
# ---------------------------------------------------------------------------


def _generate_items(rooms: Dict[str, Room], rng: random.Random) -> Dict[str, Item]:
    item_templates: List[tuple[str, str, ItemType, dict]] = [
        ("key_master", "裏口の鍵", ItemType.KEY, {"is_master": True}),
        ("key_dummy_a", "錆びた鍵", ItemType.DUMMY_KEY, {"is_master": False}),
        ("key_dummy_b", "折れた鍵", ItemType.DUMMY_KEY, {"is_master": False}),
        ("freeze_a", "御札", ItemType.GHOST_FREEZE, {"duration": 3}),
        ("freeze_b", "氷結スプレー", ItemType.GHOST_FREEZE, {"duration": 2}),
        ("speed_a", "アドレナリン注射", ItemType.SPEED_BOOST, {"duration": 5}),
        ("speed_b", "滑走シューズ", ItemType.SPEED_BOOST, {"duration": 4}),
        ("breaker_a", "錆びたバール", ItemType.WALL_BREAKER, {"consumed_on_use": True}),
        ("lore_a", "旧校長の日誌", ItemType.LORE, {}),
    ]

    room_ids = list(rooms.keys())
    rng.shuffle(room_ids)
    if len(room_ids) < len(item_templates):
        raise ValueError("Not enough rooms to place all items.")

    rng.shuffle(item_templates)

    items: Dict[str, Item] = {}
    for room_id, template in zip(room_ids, item_templates):
        room = rooms[room_id]
        positions = list(room.explore_positions)
        if not positions:
            raise ValueError(f"Room {room_id} lacks exploration tiles for item placement.")
        position = rng.choice(positions)
        item_id, name, item_type, metadata = template
        items[item_id] = Item(
            item_id=item_id,
            name=name,
            item_type=item_type,
            room_id=room_id,
            hidden=True,
            position=position,
            metadata=metadata,
        )
    return items
