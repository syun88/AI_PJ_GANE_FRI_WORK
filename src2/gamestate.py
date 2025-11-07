from typing import Dict, Tuple, Union, List
from player import Player
from game_map import Map
from enemy import OniManager

Coord = Tuple[int, int]


class GameState:
    """設定(CONFIG)を読み込み、Map/Playerを初期化。ゲーム進行のハブ。"""
    def __init__(self, config: Dict):
        # room size
        h, w = config.get("room_size", (6, 6))

        # 部屋数（doors から最大index+1）。固定したい場合は config["rooms"] に数を入れる
        if "rooms" in config:
            num_rooms = int(config["rooms"])
        else:
            max_idx = 0
            for d in config.get("doors", []):
                max_idx = max(max_idx, int(d["room"]), int(d["to_room"]))
            num_rooms = max_idx + 1

        # Map
        self.map = Map(h=h, w=w, num_rooms=num_rooms)

        # ドア設定反映（双方向は設定側で2本書く）
        for d in config.get("doors", []):
            self.map.set_door(
                room_idx=int(d["room"]),
                pos=tuple(d["pos"]),
                to_room=int(d["to_room"]),
                to_pos=tuple(d["to_pos"]),
            )

        # ゴール設定（単数 or 複数どちらでもOK）
        goal_cfg: Union[Dict, List[Dict], None] = config.get("goal")
        if isinstance(goal_cfg, dict):
            self.map.set_goal(int(goal_cfg["room"]), tuple(goal_cfg["pos"]))
        elif isinstance(goal_cfg, list):
            for g in goal_cfg:
                self.map.set_goal(int(g["room"]), tuple(g["pos"]))

        # Player
        start = config.get("start", {"room": 0, "pos": (0, 0)})
        self.map.current_room = int(start.get("room", 0))
        self.player = Player(pos=tuple(start.get("pos", (0, 0))))  # type: ignore

        # 勝敗フラグ
        self.goal_reached: bool = False
        self.caught_by_oni: bool = False

        # 「2部屋目」検出用：最初にいる部屋を記憶
        self._start_room_idx = self.map.current_room
        self._has_entered_second_room = False

        # 鬼の管理
        self.oni = OniManager()

        # 開始位置が即ゴールなら
        self._update_goal_flag()

    # --- 1ステップの移動適用 ---
    def try_move(self, dr: int, dc: int) -> None:
        if self.goal_reached or self.caught_by_oni:
            return

        # 次座標（範囲外は無視）
        nr, nc = self.player.move_by(dr, dc)
        if not self.map.in_bounds(nr, nc):
            return

        tentative = (nr, nc)

        # ゴール先行判定（同一マスにドアがあってもOK）
        if self.map.has_goal_at(tentative):
            self.player.set_position(tentative)
            self._update_goal_flag()
            return

        # 位置確定 → ドア遷移
        self.player.set_position(tentative)
        prev_room = self.map.current_room
        _, new_pos = self.map.apply_move(self.player.pos)
        self.player.set_position(new_pos)

        # 部屋が変わったら通知
        if self.map.current_room != prev_room:
            # 「2部屋目」に初めて入ったら有効化
            if (not self._has_entered_second_room) and (self.map.current_room != self._start_room_idx):
                self._has_entered_second_room = True
                self.oni.notify_entered_another_room_first_time()
            # 鬼の「2部屋移動で追跡解除」
            self.oni.notify_player_room_changed()

        # ゴール再チェック（ドア出現先がゴールの可能性）
        self._update_goal_flag()
        if self.goal_reached:
            return

        # ここから鬼の処理
        # 1) プレイヤー歩数カウント（5マス抽選のため）
        self.oni.notify_player_step()

        # 2) 抽選タイミングなら出現試行（同室のドアから）
        self.oni.try_spawn_if_due(
            current_room_idx=self.map.current_room,
            door_positions=self.map.door_positions_in_room(self.map.current_room),
        )

        # 3) 鬼の追跡移動（同室時のみ1～2歩）
        if self.oni.move_oni_toward(
            current_room_idx=self.map.current_room,
            player_pos=self.player.pos,
            in_bounds_fn=self.map.in_bounds,
        ):
            self.caught_by_oni = True

    def _update_goal_flag(self) -> None:
        self.goal_reached = self.map.has_goal_at(self.player.pos)

    # --- 描画 ---
    def draw(self) -> None:
        enemies = self.oni.enemy_positions_in_room(self.map.current_room)
        self.map.render(self.player.pos, enemies=enemies)
