"""
アイテム効果のヘルパー。

Ghost-freeze アイテムの仕様:
    - アイテムを使用した部屋のみで幽霊（鬼）の移動を停止させる。
    - 停止効果は指定ターン数だけ継続する（例: 3ターン）。
    - 重ね掛けした場合は、残りターンが長い方を優先する。

ゲーム本体への組み込みは今後の実装で行う想定。
"""

from __future__ import annotations

from typing import Iterable, MutableMapping


def apply_ghost_freeze(
    *,
    room_idx: int,
    freeze_registry: MutableMapping[int, int],
    duration: int = 3,
    affected_ghosts: Iterable[object] | None = None,
) -> int:
    """
    Register a “ghost freeze” aura for the given room.

    Parameters
    ----------
    room_idx:
        部屋番号。ここで指定した部屋に限り幽霊の移動を停止させる。
    freeze_registry:
        「部屋番号 -> 残りターン数」を保持する辞書。呼び出し側で保管する。
    duration:
        効果ターン数。0以下は無効として ValueError を投げる。
    affected_ghosts:
        同室にいる幽霊（または鬼）オブジェクトのイテラブル。
        `room_idx` が一致するものには `frozen_turns` 属性をセットし、
        その場で動きを止められるようにする（属性が無ければ自動追加）。

    Returns
    -------
    int:
        指定した部屋に残る凍結ターン数（更新後の値）。

    Notes
    -----
    - 呼び出し側はターン開始時などで freeze_registry のカウントを減らす想定。
    - 幽霊の移動ロジック側で `freeze_registry.get(current_room, 0)` や
      `getattr(ghost, "frozen_turns", 0)` を参照すれば凍結判定を実現できる。
    """
    if room_idx < 0:
        raise ValueError("room_idx must be non-negative.")
    if duration <= 0:
        raise ValueError("duration must be greater than zero.")

    remaining = max(duration, int(freeze_registry.get(room_idx, 0)))
    freeze_registry[room_idx] = remaining

    if affected_ghosts:
        for ghost in affected_ghosts:
            if getattr(ghost, "room_idx", None) != room_idx:
                continue
            current = int(getattr(ghost, "frozen_turns", 0))
            setattr(ghost, "frozen_turns", max(current, remaining))

    return remaining
