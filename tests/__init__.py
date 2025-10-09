"""
Test package initialisation.
テストパッケージの初期化処理。

Appends the local `src` directory to `sys.path` so the package can be imported
without installing it. Keeps the project dependency-free.
ローカルの `src` ディレクトリを `sys.path` に追加し、インストールなしでパッケージを読み込めるようにする。
"""

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
