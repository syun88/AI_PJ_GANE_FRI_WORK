Haunted Ruin Escape (Digital Prototype)
=======================================

This repository hosts Team 7’s digital iteration of **「廃墟からの脱出」**, a turn-based escape game set inside a haunted school building. The codebase focuses on the programmable version of the rules (9 rooms, 6×6 grids, randomised items, dynamic ghost spawning) without relying on third-party libraries.

チーム7の脱出ゲーム「廃墟からの脱出」をデジタルで検証するためのリポジトリです。紙プロトタイプ向けの仕様をベースに、9部屋・6×6マスの迷路、ランダムなアイテム配置、幽霊の出現ルールなどをPythonで再現しています。

Project Layout / プロジェクト構成
----------------------------------

- `game_rule_doc.md` – 最新のデジタル版ルールメモ。
- `src/main.py` – CLI エントリポイント。
- `src/haikyo_escape/`
  - `dungeon.py` – 標準レイアウトとアイテム配置ジェネレータ。
  - `engine.py` – ターン制ループ／コマンド解釈／幽霊スポーン処理。
  - `entities.py` – プレイヤー・幽霊・アイテムのデータ構造。
  - `room.py` – 6×6 グリッド、ドア、一方通行タイルの定義。
  - `state.py` – ゲーム状態、移動・探索ロジック、勝敗判定。
  - `types.py` – 方向や座標の共通型。
- `tests/test_state.py` – コア状態の単体テスト。

Getting Started / はじめに
--------------------------

1. **Environment / 環境**  
   Python 3.11 以上（標準ライブラリのみ使用）

2. **Run the prototype / プロトタイプ実行**  
   ```bash
   python src/main.py            # 利用可能なら int のシードを渡せます
   python src/main.py 42         # 例: シード 42 で固定
   ```

3. **Run tests / テスト実行**  
   ```bash
   python -m unittest discover -v
   ```

CLI Controls / コマンド一覧
---------------------------

Command | 説明
------- | ----
`move <dir …>` | Move 1–2 tiles depending on current speed. Example: `move north`, `move east north`. 方向は `north`, `south`, `east`, `west` もしくは `n/s/e/w`。
`search` | Reveal hidden items on the current tile. アイテムは見つけるだけで拾わない。
`take [all\|id\|index]` | Take visible items (`take all`, `take key_master`, `take 0` など)。
`use <id\|index>` | Use an inventory item (speed boost, ghost freeze, etc.)。
`wait` | ターンを消費して様子を見る。
`look` | 現在の部屋情報を再表示。
`inventory` / `inv` | 所持アイテム一覧。
`items` | 足元のアイテム一覧。
`log` | 直近 10 行のログを表示。
`help` | コマンド一覧を表示。
`quit` | セッションを終了。

Gameplay Notes / ゲームメモ
--------------------------

- **布局**: 9 rooms × 6×6 tiles. One-way passages and walls force route planning.
- **Items**: Randomly assigned per room at start. Master key (`is_master: True`) is required to unlock the exit. Speed boosts last 4–5 turns; ghost freeze items halt ghosts and room activity for a limited duration.
- **Ghosts**: Up to two active.  
  - First ghost: 1/6 spawn chance every time player’s total steps reach multiples of 5 (outside safe rooms).  
  - Second ghost: 1/6 chance after every action once the first ghost is out (also respecting safe rooms).  
  - Movement: 1 tile with probability 2/3, 2 tiles with probability 1/3, chasing the player via shortest path but respecting safe zones and freezes.
- **Victory**: Reach the exit tile with the true key.  
  **Defeat**: Share a tile with any active ghost.

Example Session / サンプル
--------------------------

```
$ python src/main.py 7
==========================================
 Haunted Ruin Escape (Text Prototype)
 Commands: move <dirs>, search, take, use, wait, quit
 Utility: help, look, inventory, items, log
 Seed: 7
==========================================

[Location] 廃墟の玄関ホール (r0)
 Position: (2, 5)
 Doors: east, south
 Explore tiles: (1, 1), (4, 4)
 Movement speed: 1 step(s) this turn
 No visible items on this tile.

Command > search
Revealed items: 氷結スプレー

Command > take all
Picked up 氷結スプレー.

Command > move north
A wall blocks the way.

Command > move east
> You step into 曲がりくねった廊下.
Player moved to r1
···
```

Development Tips / 開発メモ
-------------------------

- Use `build_default_dungeon` (in `dungeon.py`) to tweak room connections, item tables, or starting positions.
- `GameState` exposes helper methods for movement, pathfinding, freezing effects, and logging—prefer using them inside new systems.
- Ghost logic (spawn thresholds, movement rolls) is centralised in `engine.py`; adjust probabilities or rules there.
- To reproduce runs, pass an integer seed to `python src/main.py <seed>`.

Open TODOs / 今後の課題
----------------------

1. Balance the default dungeon layout and ghost difficulty through playtests.
2. Implement richer ghost AI tables or behaviours (e.g., patrols, noise attraction).
3. Add automated simulations to verify escape probability and pacing.
4. Replace CLI strings with structured command objects for downstream GUI work.
5. Extend tests to cover item usage, freeze timers, and one-way tile edge cases.

Team Reference / メンバー
------------------------

- C0B23159 チンジュンミン
- C0B23145 山本真之介
- C0B23106 中島聖成
- C0B23085 新宮 尊

*Ghost movement uses randomness; expect different logs each run.*  
*幽霊の挙動は乱数に依存するため、出力ログは毎回変化します。*
