"""廃墟脱出プロトタイプで利用するエンティティ定義。

チームメンバーが役割を分担しやすいよう、拡張ポイントを明確に用意する。
    - プレイヤー行動
    - 幽霊のAI挙動
    - アイテム同士の相互作用
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from .types import Direction, Position


class ItemType(Enum):
    """部屋に配置できるインタラクティブなアイテムの種別。"""

    KEY = auto()
    DUMMY_KEY = auto()
    GHOST_FREEZE = auto()
    SPEED_BOOST = auto()
    WALL_BREAKER = auto()
    LORE = auto()  # 収集要素（ゲーム進行には影響しない）


@dataclass
class Item:
    """盤面上に存在するアイテム情報。"""

    item_id: str
    name: str
    item_type: ItemType
    room_id: str
    hidden: bool = True  # TODO: 隠し情報をプレイヤーへ公開するタイミングを詰める。
    position: Optional[Position] = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class Entity:
    """名前と現在いる部屋を持つ基本エンティティ。"""

    entity_id: str
    name: str
    room_id: str
    is_active: bool = True
    position: Position = (0, 0)

    def move_to(self, next_room_id: str) -> None:
        """エンティティの現在位置を更新する。"""
        # TODO: 移動先の部屋が存在し、接続されているかを検証する。
        self.room_id = next_room_id

    def set_position(self, position: Position) -> None:
        self.position = position


@dataclass
class Player(Entity):
    """プレイヤーが操作する高校生キャラクター。"""

    inventory: list[Item] = field(default_factory=list)
    speed_turns_remaining: int = 0
    ghost_freeze_turns_remaining: int = 0

    def has_item_type(self, item_type: ItemType) -> bool:
        return any(item.item_type == item_type for item in self.inventory)

    def has_item(self, item_type: ItemType) -> bool:
        return self.has_item_type(item_type)

    def take_item(self, item: Item) -> None:
        # TODO: 必要に応じてインベントリ制限や行動コストを検討する。
        self.inventory.append(item)

    def drop_item(self, item_id: str) -> Optional[Item]:
        for idx, item in enumerate(self.inventory):
            if item.item_id == item_id:
                return self.inventory.pop(idx)
        return None

    def find_item_of_type(self, item_type: ItemType) -> Optional[Item]:
        for item in self.inventory:
            if item.item_type == item_type:
                return item
        return None

    def apply_speed_boost(self, duration: int) -> None:
        self.speed_turns_remaining = max(self.speed_turns_remaining, duration)

    def tick_effects(self) -> None:
        if self.speed_turns_remaining > 0:
            self.speed_turns_remaining -= 1

    @property
    def current_speed(self) -> int:
        return 2 if self.speed_turns_remaining > 0 else 1


@dataclass
class Ghost(Entity):
    """プレイヤーの後に行動する幽霊キャラクター。"""

    aggression: float = 0.5  # 0〜1のスケール。難易度調整時に調整する。
    cannot_repeat_room: bool = True
    last_room_id: Optional[str] = None
    frozen_turns: int = 0
    is_spawned: bool = False

    def choose_next_room(self, available_rooms: list[str]) -> Optional[str]:
        """部屋単位で移動先を決める旧フック（後方互換のため残置）。"""
        for room_id in available_rooms:
            if not self.cannot_repeat_room or room_id != self.last_room_id:
                return room_id
        return None

    def commit_move(self, next_room_id: str) -> None:
        self.last_room_id = self.room_id
        self.move_to(next_room_id)

    def apply_freeze(self, duration: int) -> None:
        self.frozen_turns = max(self.frozen_turns, duration)

    def tick_effects(self) -> None:
        if self.frozen_turns > 0:
            self.frozen_turns -= 1
