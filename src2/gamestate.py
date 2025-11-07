from typing import Dict, Tuple, Union, List, Optional
from collections import defaultdict
from player import Player
from game_map import Map
from enemy import OniManager

Coord = Tuple[int, int]


class GameState:
    def __init__(self, config: Dict):

        h, w = config.get("room_size", (6, 6))


        if "rooms" in config:
            num_rooms = int(config["rooms"])
        else:
            max_idx = 0
            for d in config.get("doors", []):
                max_idx = max(max_idx, int(d["room"]), int(d["to_room"]))
            num_rooms = max_idx + 1


        self.map = Map(h=h, w=w, num_rooms=num_rooms)


        doors_cfg = config.get("doors", [])
        for d in doors_cfg:
            self.map.set_door(
                room_idx=int(d["room"]),
                pos=tuple(d["pos"]),
                to_room=int(d["to_room"]),
                to_pos=tuple(d["to_pos"]),
            )


        goal_cfg: Union[Dict, List[Dict], None] = config.get("goal")
        if isinstance(goal_cfg, dict):
            self.map.set_goal(int(goal_cfg["room"]), tuple(goal_cfg["pos"]))
        elif isinstance(goal_cfg, list):
            for g in goal_cfg:
                self.map.set_goal(int(g["room"]), tuple(g["pos"]))

        forbidden_positions = self._build_forbidden_positions(doors_cfg)
        for o in config.get("obstacles", []):
            room_idx = int(o["room"])
            resolved_pos = self._resolve_obstacle_position(
                room_idx=room_idx,
                desired_pos=tuple(o["pos"]),
                forbidden_positions=forbidden_positions,
            )
            if resolved_pos is None:
                continue
            self.map.add_obstacle(
                room_idx=room_idx,
                pos=resolved_pos,
            )

        start = config.get("start", {"room": 0, "pos": (0, 0)})
        self.map.current_room = int(start.get("room", 0))
        self.player = Player(pos=tuple(start.get("pos", (0, 0))))  # type: ignore

        self.oni = OniManager()
        self.caught_by_oni: bool = False

        self.goal_reached: bool = False
        self._update_goal_flag() 

         
    def try_move(self, dr: int, dc: int) -> None:
        if self.goal_reached or self.caught_by_oni:
            return

        # 次座標（範囲外は無視）
        nr, nc = self.player.move_by(dr, dc)
        if not self.map.in_bounds(nr, nc):
            return

        tentative = (nr, nc)
        if self.map.is_blocked(self.map.current_room, tentative):
            return


        if self.map.has_goal_at(tentative):
            self.player.set_position(tentative)
            self._update_goal_flag() 
            


        self.player.set_position(tentative)
        prev_room = self.map.current_room
        _, new_pos = self.map.apply_move(self.player.pos)
        if self.map.current_room != prev_room:
            self.oni.notify_entered_another_room_first_time()
            self.oni.notify_player_room_changed()
        self.player.set_position(new_pos)


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
            player_pos=self.player.pos,
        )

        # 3) 鬼の追跡移動（同室時のみ1～2歩）
        if self.oni.move_oni_toward(
            current_room_idx=self.map.current_room,
            player_pos=self.player.pos,
            in_bounds_fn=self.map.in_bounds,
            door_transition_fn=self.map.resolve_door_transition,
            door_to_room_fn=self.map.door_positions_to_room,
            is_blocked_fn=self.map.is_blocked,
        ):
            self.caught_by_oni = True

    def _update_goal_flag(self) -> None:
        self.goal_reached = self.map.has_goal_at(self.player.pos)


    def draw(self) -> None:
        enemies = self.oni.enemy_positions_in_room(self.map.current_room)
        self.map.render(self.player.pos, enemies=enemies)

    # ---- 障害物関連 ----
    def _build_forbidden_positions(self, doors_cfg: List[Dict]) -> Dict[int, set]:
        forbidden = defaultdict(set)
        for d in doors_cfg:
            room = int(d["room"])
            forbidden[room].add(tuple(d["pos"]))
            to_room = int(d["to_room"])
            forbidden[to_room].add(tuple(d["to_pos"]))
        return forbidden

    def _resolve_obstacle_position(
        self,
        room_idx: int,
        desired_pos: Coord,
        forbidden_positions: Dict[int, set],
    ) -> Optional[Coord]:
        room = self.map.rooms[room_idx]
        forbidden = forbidden_positions.get(room_idx, set())
        if desired_pos not in forbidden and not room.has_obstacle(desired_pos):
            return desired_pos
        return self._find_alternative_obstacle_pos(room_idx, forbidden_positions)

    def _find_alternative_obstacle_pos(
        self,
        room_idx: int,
        forbidden_positions: Dict[int, set],
    ) -> Optional[Coord]:
        room = self.map.rooms[room_idx]
        forbidden = forbidden_positions.get(room_idx, set())
        for r in range(self.map.h):
            for c in range(self.map.w):
                candidate = (r, c)
                if candidate in forbidden:
                    continue
                if room.has_obstacle(candidate):
                    continue
                return candidate
        return None
