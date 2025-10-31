from typing import Dict, Tuple, Union, List
from player import Player
from game_map import Map

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


        for d in config.get("doors", []):
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


        start = config.get("start", {"room": 0, "pos": (0, 0)})
        self.map.current_room = int(start.get("room", 0))
        self.player = Player(pos=tuple(start.get("pos", (0, 0))))  # type: ignore


        self.goal_reached: bool = False
        self._update_goal_flag() 

        
    def try_move(self, dr: int, dc: int) -> None:
        nr, nc = self.player.move_by(dr, dc)
        if not self.map.in_bounds(nr, nc):
            return

        tentative = (nr, nc)


        if self.map.has_goal_at(tentative):
            self.player.set_position(tentative)
            self._update_goal_flag() 
            


        self.player.set_position(tentative)
        _, new_pos = self.map.apply_move(self.player.pos)
        self.player.set_position(new_pos)


        self._update_goal_flag()
    def _update_goal_flag(self) -> None:
        self.goal_reached = self.map.has_goal_at(self.player.pos)


    def draw(self) -> None:
        self.map.render(self.player.pos)
