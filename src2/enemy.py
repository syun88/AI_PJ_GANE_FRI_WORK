import random
from dataclasses import dataclass
from typing import Optional, Tuple, Set, Iterable

Coord = Tuple[int, int]


@dataclass
class Oni:
    room_idx: int
    pos: Coord


class OniManager:
    """
    ・2部屋目に入って以降、プレイヤーの移動をカウント
    ・5マスごとに 1/6 抽選で同室のドアからOni出現（1体まで）
    ・Oniは毎ターン1～2マスで追跡。
        - 1マス移動: 最短になる方向に1歩
        - 2マス移動: 「同じ方向に直線で2歩まで」(方向転換しない)
    ・プレイヤーが部屋を2回移動したら追跡終了（消滅）
    """
    def __init__(self):
        self.enabled_after_second_room: bool = False
        self.player_steps_since_enabled: int = 0
        self.oni: Optional[Oni] = None
        self.player_room_changes_since_spawn: int = 0

    # ---- トリガー管理 ----
    def notify_entered_another_room_first_time(self):
        if not self.enabled_after_second_room:
            self.enabled_after_second_room = True
            self.player_steps_since_enabled = 0

    def notify_player_step(self):
        if self.enabled_after_second_room and self.oni is None:
            self.player_steps_since_enabled += 1

    def notify_player_room_changed(self):
        if self.oni is not None:
            self.player_room_changes_since_spawn += 1
            if self.player_room_changes_since_spawn >= 2:
                self.despawn()

    # ---- 出現/消滅 ----
    def try_spawn_if_due(
        self,
        current_room_idx: int,
        door_positions: Iterable[Coord],
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

        if random.randint(1, 6) == 1:
            spawn_pos = random.choice(doors)
            self.oni = Oni(room_idx=current_room_idx, pos=spawn_pos)
            self.player_room_changes_since_spawn = 0

    def despawn(self):
        self.oni = None
        self.player_room_changes_since_spawn = 0

    # ---- 追跡（同室のときのみ）----
    def move_oni_toward(
        self,
        current_room_idx: int,
        player_pos: Coord,
        in_bounds_fn,  # (r,c)->bool
    ) -> bool:
        """
        Oniが同室なら1～2歩で最短接近。
        ・1歩: その時点で最短になる方向へ1歩
        ・2歩: 最初に選んだ軸（縦 or 横）を固定し、同じ方向に最大2歩の直線移動
        捕まえたら True。
        """
        if self.oni is None or self.oni.room_idx != current_room_idx:
            return False

        pr, pc = player_pos
        or_, oc_ = self.oni.pos
        steps = random.randint(1, 2)

        def step_toward_axis(axis: str) -> bool:
            """axis='r' で上下、'c' で左右に1歩だけ動く。動けたらTrue。"""
            nonlocal or_, oc_
            nr, nc = or_, oc_
            if axis == 'r':
                if pr > or_:
                    nr = or_ + 1
                elif pr < or_:
                    nr = or_ - 1
                else:
                    return False  # 縦方向の差が無い
            else:  # axis == 'c'
                if pc > oc_:
                    nc = oc_ + 1
                elif pc < oc_:
                    nc = oc_ - 1
                else:
                    return False  # 横方向の差が無い

            if in_bounds_fn(nr, nc):
                or_, oc_ = nr, nc
                self.oni.pos = (or_, oc_)
                return True
            return False

        # まず軸を決定（マンハッタン距離をより縮める方を優先）
        dr_abs = abs(pr - or_)
        dc_abs = abs(pc - oc_)
        primary_axis = 'r' if dr_abs >= dc_abs else 'c'
        secondary_axis = 'c' if primary_axis == 'r' else 'r'

        if steps == 1:
            # 1歩は従来通り：主軸で動けなければ副軸で1歩
            moved = step_toward_axis(primary_axis)
            if not moved:
                step_toward_axis(secondary_axis)
        else:
            # 2歩は「直線のみ」。まず主軸を固定。
            axis = primary_axis
            # 主軸に差が無ければ副軸に切り替えて、その軸で直線移動。
            if (axis == 'r' and dr_abs == 0) or (axis == 'c' and dc_abs == 0):
                axis = secondary_axis

            for _ in range(2):
                if self.oni.pos == player_pos:
                    break
                moved = step_toward_axis(axis)
                if not moved:
                    # 直線でこれ以上進めない場合は止まる（方向転換はしない）
                    break

        return self.oni.pos == player_pos

    # ---- レンダリング補助 ----
    def enemy_positions_in_room(self, room_idx: int) -> Set[Coord]:
        if self.oni is not None and self.oni.room_idx == room_idx:
            return {self.oni.pos}
        return set()
