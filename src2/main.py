import os
import sys
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

def read_key() -> str:

    try:
        import msvcrt
        while True:
            ch = msvcrt.getch()
            if ch in (b"q", b"Q"):
                return "q"
            if ch in (b"w", b"W", b"a", b"A", b"s", b"S", b"d", b"D"):
                return ch.decode().lower()
            if ch in (b"\x00", b"\xe0"):
                code = msvcrt.getch()[0]
                if code == 72:
                    return "up"
                if code == 80:
                    return "down"
                if code == 75:
                    return "left"
                if code == 77:
                    return "right"
    except ImportError:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch1 = sys.stdin.read(1)
                if ch1 in ("q", "Q"):
                    return "q"
                if ch1.lower() in ("w", "a", "s", "d"):
                    return ch1.lower()
                if ch1 == "\x1b":
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return "up"
                        if ch3 == "B":
                            return "down"
                        if ch3 == "D":
                            return "left"
                        if ch3 == "C":
                            return "right"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="", flush=True)


def main():
    gs = GameState(CONFIG)
    clear_screen()
    gs.draw()
    for msg in gs.consume_pending_messages():
        print(msg)

    print("矢印キーで移動、Qで終了（WASDでも可）")
    if gs.goal_reached:
        print("\n🎉 ゴール！ゲームクリア！")
        return

    key_to_move = {
        "up": (-1, 0), "down": (1, 0),
        "left": (0, -1), "right": (0, 1),
        "w": (-1, 0), "s": (1, 0),
        "a": (0, -1), "d": (0, 1),
    }

    while True:
        k = read_key()
        if k == "q":
            print("\n終了します。")
            break
        if k in key_to_move:
            dr, dc = key_to_move[k]
            clear_screen()
            gs.try_move(dr, dc)
            gs.draw()
            for msg in gs.consume_pending_messages():
                print(msg)

            if gs.goal_reached:
                print("\n🎉 ゴール！ゲームクリア！")
                break
            if gs.caught_by_oni:
                print("\n💀 鬼に捕まりました…ゲームオーバー")
                break


if __name__ == "__main__":
    main()
