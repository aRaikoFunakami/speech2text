# 依存ライブラリ管理ルール

## 原則

このプロジェクトでは **`uv`** を使って依存関係を管理する。
`pyproject.toml` を Single Source of Truth とし、ロックファイル (`uv.lock`) で再現性を担保する。

---

## 許可されるコマンド

| 操作 | コマンド |
|------|---------|
| ライブラリ追加 | `uv add <package>` |
| ライブラリ削除 | `uv remove <package>` |
| 開発用ライブラリ追加 | `uv add --dev <package>` |
| ロックファイル更新 | `uv lock` |
| 依存の同期（インストール） | `uv sync` |

---

## 禁止されるコマンド

以下のコマンドは **絶対に使用禁止**：

- `pip install`
- `pip uninstall`
- `pip freeze > requirements.txt`
- `poetry add` / `poetry remove`（このプロジェクトでは poetry を使わない）

### 理由

- `pip install` は `pyproject.toml` を更新しないため、依存が暗黙的になる
- 環境ごとに差異が生まれ、再現性が失われる
- ロックファイルとの整合性が壊れる

---

## 注意事項

- パッケージ追加後は `uv.lock` の差分もコミットに含めること
- バージョン制約が必要な場合は `uv add "package>=1.0,<2.0"` のように指定する
- グローバル環境への直接インストールは行わない
