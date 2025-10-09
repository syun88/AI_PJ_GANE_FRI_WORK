Haunted Ruin Escape Prototype
=============================

This repository contains the Python baseline for Team 7's haunted ruin escape
paper prototype. The goal is to keep the structure simple, extendable, and free
from third-party dependencies so everyone can contribute quickly.

チーム7の「廃墟からの脱出」紙プロトタイプをPythonで実験できるようにした最小構成です。外部ライブラリを使わずに動作するため、各メンバーが気軽にコード検証やルール調整を行えます。

Project Layout
--------------

- `src/haikyo_escape/` – core modules (entities, rooms, game state, engine).
- `src/main.py` – minimal CLI wiring to experiment with the loop.
- `tests/` – standard-library `unittest` smoke tests.
- `game_rule_doc.md` – original design notes (paper prototype reference).

Getting Started
---------------

### English

1. **Environment**: Python 3.11+ (only standard library modules are used).
2. **Run the sample loop**:
   ```bash
   python -m src.main
   ```
3. **Execute tests**:
   ```bash
   python -m unittest discover
   ```

### 日本語

1. **環境準備**: Python 3.11 以上（標準ライブラリのみ使用）。
2. **サンプルループ実行**:
   ```bash
   python -m src.main
   ```
   - 実行後はターンごとに行動を入力します。詳しくは下記「CLIの遊び方」を参照。
3. **テスト実行**:
   ```bash
   python -m unittest discover -v
   ```

CLI プレイガイド / How to Play via CLI
---------------------------------------

### EN
1. Run `python -m src.main`.
2. Each turn the script prints:
   - Current room name, available doors, inventory, and turn number.
3. Type one of the following commands and press Enter:
   - `move:<direction>` – move through a door (`move:east`, `move:north`, etc.).
   - `search` – reveal hidden items in the current room and pick them up.
   - `wait` – skip your action (placeholder; same effect as doing nothing).
   - `help` – print the command list again (handled by the CLI wrapper).
   - `quit` – exit the prototype immediately.
   - Any other string is ignored with a log entry.
   - Pressing Enter with no input defaults to `search`.
4. After the player action, ghosts move automatically and the result is logged.
5. The loop continues until either:
   - Player reaches the exit room while holding a key → **Winner: player**
   - A ghost enters the player’s room → **Winner: ghosts**
6. Session log is printed at the end for review.

### 日本語

1. `python -m src.main` を実行します。
2. 毎ターン表示される情報:
   - 現在いる部屋の名称とドアの方向
   - 所持アイテム（鍵など）
   - ターン番号
3. 下記コマンドを入力して Enter:
   - `move:<方向>` … 例: `move:east`（東）、`move:north`（北）。存在しない方向を指定すると移動失敗。
   - `search` … 現在の部屋を探索し、隠れているアイテムを確認・取得（サンプルでは自動で拾う仕様）。
   - `wait` … 行動をスキップ（現在は何も起こりませんが、ログに残ります）。
   - `help` … コマンド一覧を再表示。
   - `quit` … プロトタイプを即終了。
   - その他の文字列 … 無視されますがログには記録されます。
   - 何も入力せず Enter を押すと `search` が実行されます。
4. プレイヤーの行動後、自動で幽霊が移動。ログに結果が残ります。
5. 以下のいずれかでゲーム終了:
   - プレイヤーが鍵を持ったまま出口の部屋に到達 → **勝利: プレイヤー**
   - 幽霊がプレイヤーと同じ部屋に移動 → **勝利: 幽霊**
6. 最後にログ一覧が表示されるので、紙プロトタイプの再現に利用してください。

Command Reference / コマンド一覧
--------------------------------

| Command / コマンド | Description / 説明 |
|--------------------|---------------------|
| `move:<dir>`       | Move to the room connected via direction `<dir>` (e.g., `move:east`).<br>指定した方向のドアから隣室へ移動。 |
| `search`           | Reveal hidden items in the current room and pick them up.<br>現在の部屋を探索し、隠されたアイテムを発見して取得。 |
| `wait`             | Skip the turn. Useful when observing ghost behaviour during tests.<br>行動をスキップ。幽霊の動きを観察したい時に。 |
| `help`             | Display the help text again.<br>ヘルプを再表示。 |
| `quit`             | Exit the prototype immediately.<br>即時終了。 |

Sample Session / サンプルプレイ
-------------------------------

```
$ python -m src.main
========================================
 Haunted Ruin Escape Prototype (CLI)
 Commands: move:<dir>, search, wait, help, quit
 Exit with 'quit' or Ctrl+C
========================================

--- Turn 1 ---
Entrance Hall (doors: east -> corridor)
Inventory: []
Doors: east
Action (move:<dir>/search/wait/help/quit): search
Found and picked up Rusty Key.

--- Turn 2 ---
Entrance Hall (doors: east -> corridor)
Inventory: ['Rusty Key']
Doors: east
Action (move:<dir>/search/wait/help/quit): move:east
Entered Long Corridor.
幽霊B moved to entrance

--- Turn 3 ---
Long Corridor (doors: west -> entrance, north -> storage (locked))
Inventory: ['Rusty Key']
Doors: west, north
Action (move:<dir>/search/wait/help/quit): move:north
Player moved to storage
Entered Dusty Storage.

=== Game Over ===
Winner: player
Log:
- Turn 1: player chose search
- Found and picked up Rusty Key.
- 幽霊A moved to corridor
- 幽霊B moved to entrance
- Turn 2: player chose move:east
- Player moved to corridor
- 幽霊A moved to storage
- 幽霊B moved to entrance
- Turn 3: player chose move:north
- Player moved to storage
- 幽霊A moved to corridor
- 幽霊B moved to entrance
```

How to Develop / 開発の始め方
-----------------------------

- `src/main.py` からスタートすると、CLIベースで挙動を確認しながらルールを調整できます。
- 詳細仕様・データ構造は `src/haikyo_escape/` 配下に整理されています。担当例:
  - `entities.py`: プレイヤー・幽霊・アイテムの振る舞い。
  - `room.py`: 5×5 部屋やドアの定義。
  - `state.py`: 勝敗判定やログ管理など共通状態。
  - `engine.py`: ターン進行ロジック。UI/AIを差し替えるフックを用意。
- 新しい処理を追加する際は、まず該当モジュールに TODO コメントがないか確認し、埋める形で開発するとチーム間での衝突が減ります。
- 開発後は `python -m unittest discover -v` で基本的な動作確認を行ってください。

Next Steps / 次のステップ
-------------------------

1. 10部屋のレイアウトとドア接続の詳細を決定し、`room.py` にデータとして反映する。
2. 幽霊の移動テーブル（サイコロ結果と部屋の対応）を `engine.py` もしくは専用ファイルで実装。
3. 鍵・ダミー鍵・隠し情報の公開ルールを `state.py` と `entities.py` に落とし込む。
4. アクションコマンドを文字列からクラス化し、エンジン側での分岐を分かりやすくする。
5. 紙プロトタイプとの同期用ログ形式を決め、`GameState.record` での出力仕様を固める。

Team Reference
--------------

- C0B23159 チンジュンミン（自分）
- C0B23145 山本真之介
- C0B23106 中島聖成
- C0B23085 新宮 尊

Open TODO Buckets
-----------------

- Define the full 10-room layout and door connections.
- Formalise ghost movement tables (dice mapping, no-repeat handling).
- Decide how hidden information is revealed (search limits, dummy keys).
- Replace string actions in `GameEngine` with structured commands.
- Finalise logging format and decide on paper prototype sync procedure.
*Ghost movement is random; your log may differ when you run the prototype.*  
*幽霊の移動はランダムなので、実際のログは多少異なる可能性があります。*
