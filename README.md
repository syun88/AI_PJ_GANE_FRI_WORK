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
   - コマンド入力例: `move:east` で東側の部屋に移動、`search` で探索。
3. **テスト実行**:
   ```bash
   python -m unittest discover -v
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
