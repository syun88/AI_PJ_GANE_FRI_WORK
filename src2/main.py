import os
import sys
import time
from collections import deque
from typing import List, Optional, Set, Tuple
from gamestate import GameState

ROOM_HEIGHT = 10
ROOM_WIDTH = 20
PREVIOUS_ROOM_WIDTH = 30


def make_grid_doors(h=6, w=6, grid_r=3, grid_c=3):
    """
    grid_r×grid_c の部屋を 0..N-1 で並べ、左右・上下の隣接を双方向ドアで自動配線。
    ドア位置:
      左端   (row_mid, 0)     → 入室後 (row_mid, 1)
      右端   (row_mid, w-1)   → 入室後 (row_mid, w-2)
      上端   (0, col_mid)     → 入室後 (1, col_mid)
      下端   (h-1, col_mid)   → 入室後 (h-2, col_mid)
    """
    def idx(r, c): return r * grid_c + c
    row_mid = (h - 1) // 2  
    col_mid = w // 2         

    doors = []
    for r in range(grid_r):
        for c in range(grid_c):
            me = idx(r, c)
            if c + 1 < grid_c:
                right = idx(r, c + 1)
                doors.append({"room": me, "pos": (row_mid, w - 1), "to_room": right, "to_pos": (row_mid, 1)})
                doors.append({"room": right, "pos": (row_mid, 0), "to_room": me, "to_pos": (row_mid, w - 2)})
            if r + 1 < grid_r:
                down = idx(r + 1, c)
                doors.append({"room": me, "pos": (h - 1, col_mid), "to_room": down, "to_pos": (1, col_mid)})
                doors.append({"room": down, "pos": (0, col_mid), "to_room": me, "to_pos": (h - 2, col_mid)})
    return doors


def corner_room_indices(rows: int, cols: int) -> list[int]:
    """Return room indices for the four grid corners."""
    indices = [
        0,
        cols - 1,
        (rows - 1) * cols,
        rows * cols - 1,
    ]
    return indices


def generate_extra_obstacles(
    num_rooms: int,
    room_h: int,
    room_w: int,
    forbidden_coords: Optional[Set[Tuple[int, int, int]]] = None,
) -> list[dict]:
    """
    Add extra obstacles using multiple patterns (center pillars + ring + scatter)
    to densify each room while keeping some paths open.
    """
    extras: list[dict] = []
    center_pattern = [(-1, -2), (-1, 2), (0, -3), (0, 3), (1, -2), (1, 2), (0, 0)]
    ring_pattern = [(-3, -3), (-3, 3), (3, -3), (3, 3), (0, -5), (0, 5)]
    scatter_pattern = [(-4, -1), (-4, 1), (4, -1), (4, 1), (-2, -4), (-2, 4), (2, -4), (2, 4)]
    trimmed_scatter_pattern = scatter_pattern[::2]

    for room_idx in range(num_rooms):
        mid_r = max(2, min(room_h - 3, room_h // 2))
        mid_c = max(4, min(room_w - 5, room_w // 2))
        for pattern in (center_pattern, ring_pattern, trimmed_scatter_pattern):
            for dr, dc in pattern:
                rr = mid_r + dr
                cc = mid_c + dc
                if 0 <= rr < room_h and 0 <= cc < room_w:
                    if forbidden_coords and (room_idx, rr, cc) in forbidden_coords:
                        continue
                    extras.append({"room": room_idx, "pos": (rr, cc)})
    return extras


def scale_column(col: int, *, old_w: int = PREVIOUS_ROOM_WIDTH, new_w: int = ROOM_WIDTH) -> int:
    if not 0 <= col < old_w:
        raise ValueError(f"Column {col} is outside expected range 0-{old_w - 1}")
    if new_w == 1:
        return 0
    return round(col * (new_w - 1) / (old_w - 1))


def scale_pos(pos: Tuple[int, int]) -> Tuple[int, int]:
    r, c = pos
    return (r, scale_column(c))


def scale_entries(entries: List[dict]) -> List[dict]:
    scaled: List[dict] = []
    for entry in entries:
        room_idx = int(entry["room"])
        r, c = entry["pos"]
        scaled.append({"room": room_idx, "pos": (int(r), scale_column(int(c)))})
    return scaled


GRID_ROWS = 4
GRID_COLS = 4
START_ROOM = 0
BASE_START_POS = (9, 14)
BASE_GOAL_POS = (5, 15)

START_POS = scale_pos(BASE_START_POS)
GOAL_POS = scale_pos(BASE_GOAL_POS)

corner_rooms = corner_room_indices(GRID_ROWS, GRID_COLS)
goal_rooms = [idx for idx in corner_rooms if idx != START_ROOM]
NUM_ROOMS = GRID_ROWS * GRID_COLS

DOORS = make_grid_doors(h=ROOM_HEIGHT, w=ROOM_WIDTH, grid_r=GRID_ROWS, grid_c=GRID_COLS)
goal_forbidden = {(room_idx, GOAL_POS[0], GOAL_POS[1]) for room_idx in goal_rooms}
door_forbidden = {(int(d["room"]), d["pos"][0], d["pos"][1]) for d in DOORS}
door_forbidden |= {(int(d["to_room"]), d["to_pos"][0], d["to_pos"][1]) for d in DOORS}
start_forbidden = {(START_ROOM, START_POS[0], START_POS[1])}
EXTRA_FORBIDDEN = goal_forbidden | door_forbidden | start_forbidden
EXTRA_OBSTACLES = generate_extra_obstacles(
    NUM_ROOMS,
    ROOM_HEIGHT,
    ROOM_WIDTH,
    forbidden_coords=EXTRA_FORBIDDEN,
)


CONFIG = {
    "room_size": (ROOM_HEIGHT, ROOM_WIDTH),
    "rooms": NUM_ROOMS,
    "required_keys": 3,
    "start": {"room": START_ROOM, "pos": START_POS},
    "doors": DOORS,
    "key_spots": scale_entries([
        {"room": 2, "pos": (5, 22)},
        {"room": 5, "pos": (7, 12)},
        {"room": 7, "pos": (3, 18)},
        {"room": 9, "pos": (6, 8)},
        {"room": 11, "pos": (4, 18)},
        {"room": 14, "pos": (5, 6)},
        {"room": 15, "pos": (3, 14)},
        {"room": 1, "pos": (7, 6)},
        {"room": 3, "pos": (5, 21)},
        {"room": 4, "pos": (3, 20)},
        {"room": 6, "pos": (2, 24)},
        {"room": 8, "pos": (6, 10)},
        {"room": 10, "pos": (4, 18)},
        {"room": 12, "pos": (5, 6)},
        {"room": 13, "pos": (2, 24)},
    ]),
    "key_decoy_spots": scale_entries([
        {"room": 0, "pos": (1, 15)},
        {"room": 1, "pos": (6, 18)},
        {"room": 3, "pos": (7, 12)},
        {"room": 4, "pos": (2, 22)},
        {"room": 6, "pos": (5, 8)},
        {"room": 8, "pos": (2, 18)},
        {"room": 10, "pos": (6, 6)},
        {"room": 12, "pos": (7, 4)},
        {"room": 13, "pos": (3, 18)},
        {"room": 15, "pos": (5, 4)},
        {"room": 2, "pos": (4, 12)},
        {"room": 5, "pos": (6, 20)},
        {"room": 7, "pos": (2, 8)},
        {"room": 9, "pos": (3, 16)},
        {"room": 11, "pos": (5, 10)},
        {"room": 14, "pos": (2, 4)},
        {"room": 6, "pos": (8, 4)},
        {"room": 4, "pos": (6, 6)},
        {"room": 8, "pos": (5, 20)},
        {"room": 10, "pos": (3, 24)},
    ]),
    "obstacles": scale_entries([
        # room 0
        {"room": 0, "pos": (2, 5)},
        {"room": 0, "pos": (2, 6)},
        {"room": 0, "pos": (3, 6)},
        {"room": 0, "pos": (4, 10)},
        {"room": 0, "pos": (5, 10)},
        {"room": 0, "pos": (5, 11)},
        {"room": 0, "pos": (6, 18)},
        {"room": 0, "pos": (6, 19)},
        {"room": 0, "pos": (3, 20)},
        {"room": 0, "pos": (4, 20)},
        {"room": 0, "pos": (1, 12)},
        {"room": 0, "pos": (2, 12)},
        {"room": 0, "pos": (7, 8)},
        {"room": 0, "pos": (8, 8)},
        {"room": 0, "pos": (8, 9)},
        # room 1
        {"room": 1, "pos": (1, 8)},
        {"room": 1, "pos": (2, 8)},
        {"room": 1, "pos": (3, 9)},
        {"room": 1, "pos": (4, 14)},
        {"room": 1, "pos": (4, 15)},
        {"room": 1, "pos": (5, 13)},
        {"room": 1, "pos": (7, 21)},
        {"room": 1, "pos": (8, 21)},
        {"room": 1, "pos": (8, 22)},
        {"room": 1, "pos": (6, 4)},
        {"room": 1, "pos": (7, 4)},
        {"room": 1, "pos": (7, 5)},
        {"room": 1, "pos": (2, 18)},
        {"room": 1, "pos": (2, 19)},
        {"room": 1, "pos": (3, 19)},
        # room 2
        {"room": 2, "pos": (1, 7)},
        {"room": 2, "pos": (2, 7)},
        {"room": 2, "pos": (3, 7)},
        {"room": 2, "pos": (4, 18)},
        {"room": 2, "pos": (4, 19)},
        {"room": 2, "pos": (5, 19)},
        {"room": 2, "pos": (6, 24)},
        {"room": 2, "pos": (6, 25)},
        {"room": 2, "pos": (7, 24)},
        {"room": 2, "pos": (8, 12)},
        {"room": 2, "pos": (8, 13)},
        {"room": 2, "pos": (8, 14)},
        {"room": 2, "pos": (2, 22)},
        {"room": 2, "pos": (2, 23)},
        {"room": 2, "pos": (3, 23)},
        # room 3
        {"room": 3, "pos": (2, 10)},
        {"room": 3, "pos": (2, 11)},
        {"room": 3, "pos": (3, 11)},
        {"room": 3, "pos": (4, 5)},
        {"room": 3, "pos": (5, 5)},
        {"room": 3, "pos": (6, 5)},
        {"room": 3, "pos": (6, 16)},
        {"room": 3, "pos": (6, 17)},
        {"room": 3, "pos": (7, 17)},
        {"room": 3, "pos": (1, 14)},
        {"room": 3, "pos": (2, 14)},
        {"room": 3, "pos": (2, 15)},
        {"room": 3, "pos": (8, 6)},
        {"room": 3, "pos": (8, 7)},
        {"room": 3, "pos": (7, 7)},
        # room 4
        {"room": 4, "pos": (1, 3)},
        {"room": 4, "pos": (2, 3)},
        {"room": 4, "pos": (3, 3)},
        {"room": 4, "pos": (4, 14)},
        {"room": 4, "pos": (5, 14)},
        {"room": 4, "pos": (5, 15)},
        {"room": 4, "pos": (7, 20)},
        {"room": 4, "pos": (7, 21)},
        {"room": 4, "pos": (8, 20)},
        {"room": 4, "pos": (1, 9)},
        {"room": 4, "pos": (1, 10)},
        {"room": 4, "pos": (2, 10)},
        {"room": 4, "pos": (6, 18)},
        {"room": 4, "pos": (6, 19)},
        {"room": 4, "pos": (5, 19)},
        # room 5
        {"room": 5, "pos": (2, 9)},
        {"room": 5, "pos": (3, 9)},
        {"room": 5, "pos": (4, 9)},
        {"room": 5, "pos": (5, 18)},
        {"room": 5, "pos": (5, 19)},
        {"room": 5, "pos": (6, 19)},
        {"room": 5, "pos": (6, 24)},
        {"room": 5, "pos": (7, 24)},
        {"room": 5, "pos": (8, 24)},
        {"room": 5, "pos": (1, 5)},
        {"room": 5, "pos": (1, 6)},
        {"room": 5, "pos": (2, 6)},
        {"room": 5, "pos": (8, 15)},
        {"room": 5, "pos": (8, 16)},
        {"room": 5, "pos": (7, 16)},
        # room 6
        {"room": 6, "pos": (1, 6)},
        {"room": 6, "pos": (1, 7)},
        {"room": 6, "pos": (2, 7)},
        {"room": 6, "pos": (4, 12)},
        {"room": 6, "pos": (4, 13)},
        {"room": 6, "pos": (5, 13)},
        {"room": 6, "pos": (7, 18)},
        {"room": 6, "pos": (7, 19)},
        {"room": 6, "pos": (8, 19)},
        {"room": 6, "pos": (2, 16)},
        {"room": 6, "pos": (3, 16)},
        {"room": 6, "pos": (3, 17)},
        {"room": 6, "pos": (5, 22)},
        {"room": 6, "pos": (6, 22)},
        {"room": 6, "pos": (6, 23)},
        # room 7
        {"room": 7, "pos": (2, 4)},
        {"room": 7, "pos": (3, 4)},
        {"room": 7, "pos": (4, 4)},
        {"room": 7, "pos": (5, 22)},
        {"room": 7, "pos": (5, 23)},
        {"room": 7, "pos": (6, 23)},
        {"room": 7, "pos": (7, 10)},
        {"room": 7, "pos": (8, 10)},
        {"room": 7, "pos": (8, 11)},
        {"room": 7, "pos": (1, 12)},
        {"room": 7, "pos": (2, 12)},
        {"room": 7, "pos": (2, 13)},
        {"room": 7, "pos": (4, 6)},
        {"room": 7, "pos": (5, 6)},
        {"room": 7, "pos": (5, 7)},
        # room 8
        {"room": 8, "pos": (1, 5)},
        {"room": 8, "pos": (2, 5)},
        {"room": 8, "pos": (3, 5)},
        {"room": 8, "pos": (4, 16)},
        {"room": 8, "pos": (4, 17)},
        {"room": 8, "pos": (5, 17)},
        {"room": 8, "pos": (7, 22)},
        {"room": 8, "pos": (7, 23)},
        {"room": 8, "pos": (8, 23)},
        {"room": 8, "pos": (1, 12)},
        {"room": 8, "pos": (1, 13)},
        {"room": 8, "pos": (2, 13)},
        {"room": 8, "pos": (3, 21)},
        {"room": 8, "pos": (4, 21)},
        {"room": 8, "pos": (4, 22)},
        # room 9
        {"room": 9, "pos": (2, 9)},
        {"room": 9, "pos": (2, 10)},
        {"room": 9, "pos": (3, 10)},
        {"room": 9, "pos": (4, 4)},
        {"room": 9, "pos": (5, 4)},
        {"room": 9, "pos": (6, 4)},
        {"room": 9, "pos": (7, 18)},
        {"room": 9, "pos": (7, 19)},
        {"room": 9, "pos": (8, 18)},
        {"room": 9, "pos": (1, 15)},
        {"room": 9, "pos": (1, 16)},
        {"room": 9, "pos": (2, 16)},
        {"room": 9, "pos": (5, 11)},
        {"room": 9, "pos": (5, 12)},
        {"room": 9, "pos": (6, 12)},
        # room 10
        {"room": 10, "pos": (1, 8)},
        {"room": 10, "pos": (2, 8)},
        {"room": 10, "pos": (3, 8)},
        {"room": 10, "pos": (4, 20)},
        {"room": 10, "pos": (4, 21)},
        {"room": 10, "pos": (5, 21)},
        {"room": 10, "pos": (6, 12)},
        {"room": 10, "pos": (6, 13)},
        {"room": 10, "pos": (7, 13)},
        {"room": 10, "pos": (2, 3)},
        {"room": 10, "pos": (2, 4)},
        {"room": 10, "pos": (3, 4)},
        {"room": 10, "pos": (8, 9)},
        {"room": 10, "pos": (8, 10)},
        {"room": 10, "pos": (7, 10)},
        # room 11
        {"room": 11, "pos": (2, 6)},
        {"room": 11, "pos": (3, 6)},
        {"room": 11, "pos": (4, 6)},
        {"room": 11, "pos": (5, 15)},
        {"room": 11, "pos": (5, 16)},
        {"room": 11, "pos": (6, 16)},
        {"room": 11, "pos": (7, 24)},
        {"room": 11, "pos": (8, 24)},
        {"room": 11, "pos": (8, 25)},
        {"room": 11, "pos": (1, 8)},
        {"room": 11, "pos": (1, 9)},
        {"room": 11, "pos": (2, 9)},
        {"room": 11, "pos": (6, 3)},
        {"room": 11, "pos": (7, 3)},
        {"room": 11, "pos": (7, 4)},
        # room 12
        {"room": 12, "pos": (1, 7)},
        {"room": 12, "pos": (2, 7)},
        {"room": 12, "pos": (3, 7)},
        {"room": 12, "pos": (4, 11)},
        {"room": 12, "pos": (4, 12)},
        {"room": 12, "pos": (5, 12)},
        {"room": 12, "pos": (6, 20)},
        {"room": 12, "pos": (6, 21)},
        {"room": 12, "pos": (7, 20)},
        {"room": 12, "pos": (2, 2)},
        {"room": 12, "pos": (3, 2)},
        {"room": 12, "pos": (3, 3)},
        {"room": 12, "pos": (4, 24)},
        {"room": 12, "pos": (5, 24)},
        {"room": 12, "pos": (5, 25)},
        # room 13
        {"room": 13, "pos": (2, 5)},
        {"room": 13, "pos": (3, 5)},
        {"room": 13, "pos": (4, 5)},
        {"room": 13, "pos": (5, 18)},
        {"room": 13, "pos": (5, 19)},
        {"room": 13, "pos": (6, 19)},
        {"room": 13, "pos": (7, 9)},
        {"room": 13, "pos": (7, 10)},
        {"room": 13, "pos": (8, 10)},
        {"room": 13, "pos": (1, 14)},
        {"room": 13, "pos": (1, 15)},
        {"room": 13, "pos": (2, 15)},
        {"room": 13, "pos": (4, 7)},
        {"room": 13, "pos": (4, 8)},
        {"room": 13, "pos": (5, 8)},
        # room 14
        {"room": 14, "pos": (1, 9)},
        {"room": 14, "pos": (2, 9)},
        {"room": 14, "pos": (3, 9)},
        {"room": 14, "pos": (4, 23)},
        {"room": 14, "pos": (4, 24)},
        {"room": 14, "pos": (5, 24)},
        {"room": 14, "pos": (6, 14)},
        {"room": 14, "pos": (6, 15)},
        {"room": 14, "pos": (7, 15)},
        {"room": 14, "pos": (2, 4)},
        {"room": 14, "pos": (2, 5)},
        {"room": 14, "pos": (3, 5)},
        {"room": 14, "pos": (5, 11)},
        {"room": 14, "pos": (5, 12)},
        {"room": 14, "pos": (6, 12)},
        # room 15
        {"room": 15, "pos": (2, 6)},
        {"room": 15, "pos": (3, 6)},
        {"room": 15, "pos": (4, 6)},
        {"room": 15, "pos": (6, 22)},
        {"room": 15, "pos": (6, 23)},
        {"room": 15, "pos": (7, 23)},
        {"room": 15, "pos": (7, 10)},
        {"room": 15, "pos": (8, 10)},
        {"room": 15, "pos": (8, 11)},
        {"room": 15, "pos": (1, 7)},
        {"room": 15, "pos": (1, 8)},
        {"room": 15, "pos": (2, 8)},
        {"room": 15, "pos": (4, 18)},
        {"room": 15, "pos": (4, 19)},
        {"room": 15, "pos": (5, 19)},
    ]) + EXTRA_OBSTACLES,
    "goal_candidates": [
        {"room": room_idx, "pos": GOAL_POS}
        for room_idx in goal_rooms
    ],
}


class AutoExplorer:
    """
    盤面の障害物とドアを考慮しながら最短手で鍵とゴールを巡る簡易AI。
    BFSでルートを探索し、毎手盤面を描画して進捗を表示する。
    """

    _DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    _DIR_LABEL = {
        (-1, 0): "北へ移動",
        (1, 0): "南へ移動",
        (0, -1): "西へ移動",
        (0, 1): "東へ移動",
    }

    def __init__(self, game_state: GameState, *, delay: float = 0.15):
        self.gs = game_state
        self.delay = delay

    def play(self) -> None:
        clear_screen()
        self.gs.draw()
        self._print_pending_messages()
        print(f"AI が探索を開始します。残機 {self.gs.lives_remaining}/{self.gs.initial_lives}")

        if self.gs.goal_location is None:
            print("ゴール位置が未設定のためAIを実行できません。")
            return
        if self.gs.goal_reached:
            print("\n🎉 ゴール！ゲームクリア！")
            return

        while not self.gs.goal_reached and not self.gs.caught_by_oni:
            target = self._choose_target()
            if target is None:
                print("AI は有効な目的地を見つけられず探索を終了します。")
                break

            self._announce_target(target)
            path = self._find_path(self._current_state(), target)
            if path is None:
                print("目標へのルートが見つからなかったため探索を断念します。")
                break

            self._follow_path(path)

        self._print_outcome()

    def _current_state(self) -> Tuple[int, Tuple[int, int]]:
        return self.gs.map.current_room, self.gs.player.pos

    def _choose_target(self) -> Optional[Tuple[int, Tuple[int, int]]]:
        if self.gs.player.keys_collected < self.gs.required_keys:
            return self._next_key_target()
        return self.gs.goal_location

    def _next_key_target(self) -> Optional[Tuple[int, Tuple[int, int]]]:
        remaining = self.gs.remaining_key_positions()
        if not remaining:
            return None
        ordered: List[Tuple[int, Tuple[int, int]]] = []
        for room_idx in sorted(remaining.keys()):
            for pos in sorted(remaining[room_idx]):
                ordered.append((room_idx, pos))
        return ordered[0] if ordered else None

    def _announce_target(self, target: Tuple[int, Tuple[int, int]]) -> None:
        room_idx, (row, col) = target
        if self.gs.goal_location and target == self.gs.goal_location:
            label = "ゴール"
        else:
            label = f"鍵 {self.gs.player.keys_collected + 1}"
        print(f"\n[AI] 目的地: {label} (room={room_idx}, row={row}, col={col})")

    def _find_path(
        self,
        start: Tuple[int, Tuple[int, int]],
        goal: Tuple[int, Tuple[int, int]],
    ) -> Optional[List[Tuple[int, int]]]:
        if start == goal:
            return []

        queue = deque([start])
        visited = {start: None}
        move_taken: dict[Tuple[int, Tuple[int, int]], Tuple[int, int]] = {}

        while queue:
            room_idx, pos = queue.popleft()
            if (room_idx, pos) == goal:
                break
            for next_state, move in self._neighbors(room_idx, pos):
                if next_state in visited:
                    continue
                visited[next_state] = (room_idx, pos)
                move_taken[next_state] = move
                queue.append(next_state)
        else:
            return None

        path: List[Tuple[int, int]] = []
        cursor = goal
        while cursor != start:
            move = move_taken.get(cursor)
            prev = visited.get(cursor)
            if move is None or prev is None:
                return None
            path.append(move)
            cursor = prev
        path.reverse()
        return path

    def _neighbors(
        self,
        room_idx: int,
        pos: Tuple[int, int],
    ) -> List[Tuple[Tuple[int, Tuple[int, int]], Tuple[int, int]]]:
        results: List[Tuple[Tuple[int, Tuple[int, int]], Tuple[int, int]]] = []
        for dr, dc in self._DIRS:
            nr, nc = pos[0] + dr, pos[1] + dc
            if not self.gs.map.in_bounds(nr, nc):
                continue
            if self.gs.map.is_blocked(room_idx, (nr, nc)):
                continue
            next_room = room_idx
            next_pos = (nr, nc)
            door = self.gs.map.rooms[room_idx].get_door((nr, nc))
            if door:
                next_room = door.target_room
                next_pos = door.target_pos
                if self.gs.map.is_blocked(next_room, next_pos):
                    continue
            results.append(((next_room, next_pos), (dr, dc)))
        return results

    def _follow_path(self, moves: List[Tuple[int, int]]) -> None:
        if not moves:
            self.gs.process_current_tile()
            self._print_pending_messages()
            return

        total = len(moves)
        for idx, (dr, dc) in enumerate(moves, start=1):
            if self.gs.goal_reached or self.gs.caught_by_oni:
                break
            time.sleep(self.delay)
            clear_screen()
            self.gs.try_move(dr, dc)
            self.gs.draw()
            direction = self._DIR_LABEL.get((dr, dc), f"({dr},{dc})")
            print(f"[AI] {direction} （{idx}/{total}）")
            self._print_pending_messages()

    def _print_pending_messages(self) -> None:
        for msg in self.gs.consume_pending_messages():
            print(msg)

    def _print_outcome(self) -> None:
        if self.gs.goal_reached:
            print("\n🎉 AI がゴールに到達しました！ゲームクリア！")
        elif self.gs.caught_by_oni:
            print("\n💀 AI は鬼に捕まってしまった…ゲームオーバー")
        else:
            print("\n⚠️ AI は探索を完了できませんでした。")


def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="", flush=True)

def resolve_lives_setting(default: int = 3) -> int:
    """
    残機設定をCLI引数または環境変数から取得（どちらもなければ既定値）。
    優先順位: 第1引数 > 環境変数 AI_LIVES > default
    """
    raw: Optional[str] = None
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    elif "AI_LIVES" in os.environ:
        raw = os.environ["AI_LIVES"]

    if raw:
        try:
            value = int(raw)
            return max(1, min(3, value))
        except ValueError:
            pass
    return default


def main():
    config = dict(CONFIG)
    config["lives"] = resolve_lives_setting()

    gs = GameState(config)
    delay = 0.15
    env_delay = os.getenv("AI_PLAY_DELAY")
    if env_delay:
        try:
            delay = max(0.0, float(env_delay))
        except ValueError:
            pass

    ai = AutoExplorer(gs, delay=delay)
    ai.play()


if __name__ == "__main__":
    main()
