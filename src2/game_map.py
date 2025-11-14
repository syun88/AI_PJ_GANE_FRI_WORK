import os
import sys
from typing import List, Tuple, Optional, Iterable, Set, Dict
from room import Room, Door

Coord = Tuple[int, int]


class Map:
    def __init__(self, h: int, w: int, num_rooms: int):
        self.h = h
        self.w = w
        self.rooms: List[Room] = [Room(h, w) for _ in range(num_rooms)]
        self.current_room: int = 0
        self._use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None


    def set_door(self, room_idx: int, pos: Coord, to_room: int, to_pos: Coord) -> None:
        self.rooms[room_idx].set_door(pos, to_room, to_pos)


    def remove_door(self, room_idx: int, pos: Coord) -> None:
        self.rooms[room_idx].remove_door(pos)


    def set_goal(self, room_idx: int, pos: Coord) -> None:
        self.rooms[room_idx].set_goal(pos)


    def has_goal_at(self, pos: Coord) -> bool:
        goal = self.rooms[self.current_room].get_goal()
        return goal is not None and goal == pos
    
    def add_obstacle(self, room_idx: int, pos: Coord) -> None:
        self.rooms[room_idx].add_obstacle(pos)



    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.h and 0 <= c < self.w

    def is_blocked(self, room_idx: int, pos: Coord) -> bool:
        return self.rooms[room_idx].has_obstacle(pos)


    def render(
        self,
        player_pos: Coord,
        enemies: Optional[Iterable[Coord]] = None,
        items: Optional[Dict[Coord, str]] = None,
    ) -> None:
        print(f"\n[Room] {self.current_room}   [Player] row={player_pos[0]}, col={player_pos[1]}")
        for line in self.rooms[self.current_room].render_lines(
            player_pos,
            enemies=enemies,
            items=items,
            use_color=self._use_color,
        ):
            print(line)



    def apply_move(self, player_pos: Coord) -> Tuple[int, Coord]:
        room = self.rooms[self.current_room]
        door: Optional[Door] = room.get_door(player_pos)
        if door:
            self.current_room = door.target_room
            return self.current_room, door.target_pos
        return self.current_room, player_pos

    def resolve_door_transition(self, room_idx: int, pos: Coord) -> Tuple[int, Coord]:
        door = self.rooms[room_idx].get_door(pos)
        if door:
            return door.target_room, door.target_pos
        return room_idx, pos

    # ---- 現在/任意の部屋のドア座標取得 ----
    def door_positions_in_room(self, room_idx: int) -> Set[Coord]:
        return self.rooms[room_idx].door_positions()

    def door_positions_to_room(self, room_idx: int, target_room: int) -> Set[Coord]:
        return self.rooms[room_idx].door_positions_to(target_room)
