"""
Game state container and helper functions.
ゲーム状態を保持し操作するためのヘルパー群。

This module centralises mutable game data so the team can
swap in different UIs (CLI, GUI, paper play-by-play logger).
可変データを一箇所に集約することで、CLI/GUI/紙ログなど異なるUIを差し替えやすくする。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional

from .entities import Ghost, Item, ItemType, Player
from .room import Room


class TurnPhase(Enum):
    """High-level turn phases to keep the loop explicit.
    ループの状態をわかりやすくするための大まかなフェーズ区分。
    """

    PLAYER_DECISION = auto()
    GHOST_MOVEMENT = auto()
    RESOLUTION = auto()


@dataclass
class GameState:
    """Tracks all mutable simulation data.
    シミュレーション中に変化するデータを一括で管理する。
    """

    rooms: Dict[str, Room]
    player: Player
    ghosts: List[Ghost]
    items: Dict[str, Item] = field(default_factory=dict)
    turn_count: int = 0
    phase: TurnPhase = TurnPhase.PLAYER_DECISION
    exit_room_id: Optional[str] = None
    is_over: bool = False
    winner: Optional[str] = None
    log: List[str] = field(default_factory=list)

    def add_room(self, room: Room) -> None:
        self.rooms[room.room_id] = room

    def add_item(self, item: Item) -> None:
        # TODO: validate there is a matching room for the item.room_id. / アイテムの部屋IDが実在し接続されているか検証する。
        self.items[item.item_id] = item

    def record(self, message: str) -> None:
        """Append an event to the session log.
        セッションログへイベントを追記する。
        """
        self.log.append(message)

    def check_victory(self) -> None:
        """Evaluate win/lose conditions.
        勝利・敗北条件を評価する。
        """
        # TODO: connect to real rules (key possession + exit reach). / 実際のルール（鍵保持＋出口到達など）に合わせて処理を整える。
        if (
            self.player.room_id == self.exit_room_id
            and self.player.has_item_type(ItemType.KEY)
        ):
            # Player wins when reaching exit with the key.
            # プレイヤーが鍵を保持した状態で出口に到達すると勝利。
            self.is_over = True
            self.winner = "player"

        for ghost in self.ghosts:
            if ghost.room_id == self.player.room_id:
                # Player loses if a ghost enters the same room.
                # 幽霊と同じ部屋に入ったらプレイヤーの敗北。
                self.is_over = True
                self.winner = "ghosts"

    def reset(self) -> None:
        """Bring the state back to initial conditions.
        状態を初期化して再プレイできるようにする。
        """
        # TODO: define what reset means once setup flow is finalised. / セットアップ手順が決まったら初期化内容を確定させる。
        self.turn_count = 0
        self.phase = TurnPhase.PLAYER_DECISION
        self.is_over = False
        self.winner = None
        self.log.clear()
