import random
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple, Set, Iterable, List

Coord = Tuple[int, int]


@dataclass
class Oni:
    room_idx: int
    pos: Coord


class OniManager:
    """
    ・2部屋目に入って以降、プレイヤーの移動をカウント
    ・5マスごとの判定で段階的に上がる確率（10→25→45→70→100%）で同室のドアからOni出現（1体まで, プレイヤーから最遠のドアを選ぶ）
    ・Oniは毎ターン1 or 2マスで追跡し、障害物を避けた最短経路（4方向）を進む。必要ならドアを通過して隣室へ移動
    ・プレイヤーが部屋を2回移動したら追跡終了（消滅）
    """
    TWO_STEP_PROBABILITY = 0.25  # 2歩行動の確率

    def __init__(self):
        self.enabled_after_second_room: bool = False
        self.player_steps_since_enabled: int = 0
        self.oni: Optional[Oni] = None
        # 5歩ごとの判定で10%から10%ずつ上昇し、10回目（50歩目）で100%
        self._spawn_chances = (
            10,
            20,
            30,
            40,
            50,
            60,
            70,
            80,
            90,
            100,
        )
        self._spawn_stage = 0
        self._player_rooms_since_spawn: Set[int] = set()
        self._player_room_at_spawn: Optional[int] = None

    # ---- トリガー管理 ----
    def notify_entered_another_room_first_time(self):
        if not self.enabled_after_second_room:
            self.enabled_after_second_room = True
            self.player_steps_since_enabled = 0
            self._spawn_stage = 0

    def notify_player_step(self):
        if self.enabled_after_second_room and self.oni is None:
            self.player_steps_since_enabled += 1

    def notify_player_room_changed(self, new_room_idx: int):
        if self.oni is not None:
            if self._player_room_at_spawn is None:
                self._player_room_at_spawn = self.oni.room_idx
            if new_room_idx != self._player_room_at_spawn:
                self._player_rooms_since_spawn.add(new_room_idx)
            if len(self._player_rooms_since_spawn) >= 2:
                self.despawn()

    # ---- 出現/消滅 ----
    def try_spawn_if_due(
        self,
        current_room_idx: int,
        door_positions: Iterable[Coord],
        player_pos: Coord,
    ) -> None:
        if not self.enabled_after_second_room:
            return
        if self.oni is not None:
            return
        if self.player_steps_since_enabled == 0 or self.player_steps_since_enabled % 5 != 0:
            return

        doors = list(door_positions)
        if not doors:
            return

        spawn_threshold = self._spawn_chances[self._spawn_stage]
        if random.randint(1, 100) <= spawn_threshold:
            spawn_pos = max(
                doors,
                key=lambda pos: abs(pos[0] - player_pos[0]) + abs(pos[1] - player_pos[1]),
            )
            self.oni = Oni(room_idx=current_room_idx, pos=spawn_pos)
            self._spawn_stage = 0
            self._player_rooms_since_spawn.clear()
            self._player_room_at_spawn = current_room_idx
        else:
            self._spawn_stage = min(self._spawn_stage + 1, len(self._spawn_chances) - 1)

    def despawn(self):
        self.oni = None
        self._spawn_stage = 0
        self._player_rooms_since_spawn.clear()
        self._player_room_at_spawn = None

    def reset_spawn_progress(self):
        """Reset spawn counters without disabling Oni feature."""
        self.player_steps_since_enabled = 0
        self._spawn_stage = 0

    # ---- 追跡（同室のときのみ）----
    def move_oni_toward(
        self,
        current_room_idx: int,
        player_pos: Coord,
        in_bounds_fn,  # (r,c)->bool
        door_transition_fn,  # (room_idx,pos)->(room_idx,pos)
        door_to_room_fn,  # (room_idx,target_room)->Iterable[Coord]
        is_blocked_fn,  # (room_idx,pos)->bool
    ) -> bool:
        """Oniが1or2歩進み、障害物を避けた経路でターゲットへ接近する。"""
        if self.oni is None:
            return False

        # 1歩:2歩 = 3:1（75% / 25%）
        steps = 2 if random.random() < self.TWO_STEP_PROBABILITY else 1

        for _ in range(steps):
            if self.oni is None:
                break

            targets = self._target_positions_for_room(
                oni_room=self.oni.room_idx,
                player_room=current_room_idx,
                player_pos=player_pos,
                door_to_room_fn=door_to_room_fn,
            )
            if not targets:
                break

            next_pos = self._next_step_toward(
                room_idx=self.oni.room_idx,
                start=self.oni.pos,
                targets=targets,
                in_bounds_fn=in_bounds_fn,
                is_blocked_fn=is_blocked_fn,
            )
            if next_pos is None or next_pos == self.oni.pos:
                break

            self.oni.pos = next_pos
            new_room, new_pos = door_transition_fn(self.oni.room_idx, self.oni.pos)
            self.oni.room_idx = new_room
            self.oni.pos = new_pos

            if self.oni.room_idx == current_room_idx and self.oni.pos == player_pos:
                return True

        return self.oni is not None and self.oni.room_idx == current_room_idx and self.oni.pos == player_pos

    # ---- レンダリング補助 ----
    def enemy_positions_in_room(self, room_idx: int) -> Set[Coord]:
        if self.oni is not None and self.oni.room_idx == room_idx:
            return {self.oni.pos}
        return set()

    # ---- 内部ヘルパ ----
    def _target_positions_for_room(
        self,
        oni_room: int,
        player_room: int,
        player_pos: Coord,
        door_to_room_fn,
    ) -> List[Coord]:
        if oni_room == player_room:
            return [player_pos]
        return list(door_to_room_fn(oni_room, player_room))

    def _next_step_toward(
        self,
        room_idx: int,
        start: Coord,
        targets: Iterable[Coord],
        in_bounds_fn,
        is_blocked_fn,
    ) -> Optional[Coord]:
        target_set = set(targets)
        if not target_set:
            return None
        if start in target_set:
            return start

        queue = deque([start])
        came_from = {start: None}
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                nxt = (nr, nc)
                if nxt in came_from:
                    continue
                if not in_bounds_fn(nr, nc):
                    continue
                if is_blocked_fn(room_idx, nxt):
                    continue
                came_from[nxt] = (r, c)
                if nxt in target_set:
                    return self._first_step_from_path(start, nxt, came_from)
                queue.append(nxt)
        return None

    @staticmethod
    def _first_step_from_path(
        start: Coord,
        target: Coord,
        came_from: dict,
    ) -> Coord:
        node = target
        while came_from.get(node) not in (None, start):
            node = came_from[node]
        return node
