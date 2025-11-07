import sys
from gamestate import GameState

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



CONFIG = {
    "room_size": (6, 6),
    "rooms": 9,  # 0..8 の9部屋
    "start": {"room": 0, "pos": (5, 2)},
    "doors": make_grid_doors(h=6, w=6, grid_r=3, grid_c=3),
    "goal": {"room": 8, "pos": (2, 3)},
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


def main():
    gs = GameState(CONFIG)
    print("矢印キーで移動、Qで終了（WASDでも可）")
    gs.draw()
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
            gs.try_move(dr, dc)
            print("\033[2J\033[H", end="")
            gs.draw()

            if gs.goal_reached:
                print("\n🎉 ゴール！ゲームクリア！")
                break
            if gs.caught_by_oni:
                print("\n💀 鬼に捕まりました…ゲームオーバー")
                break


if __name__ == "__main__":
    main()
