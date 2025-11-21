import random
from pathlib import Path
from typing import Dict, Tuple, Union, List, Optional, Set, Literal
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
        self._explanation_path = Path(__file__).resolve().parent.parent / "src" / "説明.txt"
        self._pending_messages: List[str] = []
        self.goal_location: Optional[Tuple[int, Coord]] = None
        self.required_keys: int = int(config.get("required_keys", 3))
        self._key_positions: Dict[int, Set[Coord]] = defaultdict(set)


        doors_cfg = config.get("doors", [])
        for d in doors_cfg:
            self.map.set_door(
                room_idx=int(d["room"]),
                pos=tuple(d["pos"]),
                to_room=int(d["to_room"]),
                to_pos=tuple(d["to_pos"]),
            )


        goal_candidates = config.get("goal_candidates")
        if goal_candidates:
            chosen_goal = random.choice(goal_candidates)
            room_idx = int(chosen_goal["room"])
            pos = tuple(chosen_goal["pos"])
            self.map.set_goal(room_idx, pos)
            self.goal_location = (room_idx, pos)
        else:
            goal_cfg: Union[Dict, List[Dict], None] = config.get("goal")
            if isinstance(goal_cfg, dict):
                room_idx = int(goal_cfg["room"])
                pos = tuple(goal_cfg["pos"])
                self.map.set_goal(room_idx, pos)
                self.goal_location = (room_idx, pos)
            elif isinstance(goal_cfg, list):
                for g in goal_cfg:
                    room_idx = int(g["room"])
                    pos = tuple(g["pos"])
                    self.map.set_goal(room_idx, pos)
                    self.goal_location = (room_idx, pos)

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

        key_spots = config.get("key_spots", [])
        if key_spots:
            filtered_spots = [
                spot
                for spot in key_spots
                if (
                    (not self.goal_location or int(spot["room"]) != self.goal_location[0])
                    and not self.map.rooms[int(spot["room"])].has_obstacle(tuple(spot["pos"]))
                )
            ]
            if len(filtered_spots) < self.required_keys:
                raise ValueError("Not enough key spots to place required keys.")
            chosen_spots = random.sample(filtered_spots, self.required_keys)
            for entry in chosen_spots:
                room_idx = int(entry["room"])
                pos = tuple(entry["pos"])
                self._key_positions[room_idx].add(pos)

        decoy_spots = config.get("key_decoy_spots", [])
        self._decoy_positions: Dict[int, Set[Coord]] = defaultdict(set)
        for entry in decoy_spots:
            room_idx = int(entry["room"])
            pos = tuple(entry["pos"])
            if self.map.rooms[room_idx].has_obstacle(pos):
                continue
            if pos in self._key_positions.get(room_idx, set()):
                continue
            self._decoy_positions[room_idx].add(pos)

        start = config.get("start", {"room": 0, "pos": (0, 0)})
        self.map.current_room = int(start.get("room", 0))
        self.player = Player(pos=tuple(start.get("pos", (0, 0))))  # type: ignore

        self.oni = OniManager()
        self.caught_by_oni: bool = False

        self.goal_reached: bool = False
        self._key_prompt_displayed: bool = False
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
            self.oni.notify_player_room_changed(self.map.current_room)
        self.player.set_position(new_pos)

        self._notify_question_tile_if_needed()

        self._check_key_pickup()
        self._check_decoy_tile()

        self._update_goal_flag()
        self._notify_key_requirement_if_needed()
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
        self.goal_reached = self.map.has_goal_at(self.player.pos) and self.player.keys_collected >= self.required_keys

    def draw(self) -> None:
        enemies = self.oni.enemy_positions_in_room(self.map.current_room)
        items = self._items_in_current_room()
        self.map.render(self.player.pos, enemies=enemies, items=items)
        self._print_explanation_text()
        self._print_key_status()

    def consume_pending_messages(self) -> List[str]:
        messages = self._pending_messages[:]
        self._pending_messages.clear()
        return messages

    def _print_explanation_text(self) -> None:
        try:
            text = self._explanation_path.read_text(encoding="utf-8")
        except OSError:
            return
        stripped = text.rstrip("\n")
        if not stripped:
            return
        print()
        print(stripped)

    def _print_key_status(self) -> None:
        if self.player.keys_collected == 0:
            return
        print(f"\n[Status] 🔑 鍵 {self.player.keys_collected}/{self.required_keys}")

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

    # ---- 鍵関連 ----
    def _check_key_pickup(self) -> None:
        key_positions = self._key_positions.get(self.map.current_room)
        if not key_positions:
            return
        if self.player.pos in key_positions:
            key_positions.remove(self.player.pos)
            self.player.obtain_key()
            self._queue_message(f"🔑 鍵を手に入れた！（{self.player.keys_collected}/{self.required_keys}）")

    def _notify_key_requirement_if_needed(self) -> None:
        if self.player.keys_collected >= self.required_keys:
            return
        if self.map.has_goal_at(self.player.pos) and not self._key_prompt_displayed:
            print(f"ゴールのドアには鍵が{self.required_keys}本必要だ…（現在 {self.player.keys_collected}）")
            self._key_prompt_displayed = True

    def _items_in_current_room(self) -> Dict[Coord, str]:
        items: Dict[Coord, str] = {}
        key_positions = self._key_positions.get(self.map.current_room, set())
        for pos in key_positions:
            items[pos] = "？"

        decoys = self._decoy_positions.get(self.map.current_room, set())
        for pos in decoys:
            if pos not in items:
                items[pos] = "？"
        return items

    def _check_decoy_tile(self) -> None:
        decoys = self._decoy_positions.get(self.map.current_room)
        if not decoys:
            return
        if self.player.pos in decoys:
            decoys.remove(self.player.pos)
            self._queue_message("ここには鍵が落ちていなかった…")

    def _notify_question_tile_if_needed(self) -> None:
        tile_type = self._question_tile_type(self.map.current_room, self.player.pos)
        if tile_type == "key":
            self._queue_message("？マスから本物の鍵の気配がする…！")
        elif tile_type == "decoy":
            self._queue_message("？マスだが、鍵は見当たらなかった…。")

    def _question_tile_type(self, room_idx: int, pos: Coord) -> Optional[Literal["key", "decoy"]]:
        key_positions = self._key_positions.get(room_idx)
        if key_positions and pos in key_positions:
            return "key"
        decoys = self._decoy_positions.get(room_idx)
        if decoys and pos in decoys:
            return "decoy"
        return None

    def _queue_message(self, message: str) -> None:
        self._pending_messages.append(message)
