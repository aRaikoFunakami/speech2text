# speech2text

音声/動画ファイルを OpenAI Speech-to-Text API でテキストに変換する CLI ツール。

## 必要要件

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) — 音声/動画の変換に使用
- OpenAI API キー

## インストール

### GitHub からインストール

```bash
uv tool install git+https://github.com/aRaikoFunakami/speech2text.git@main
```

特定バージョンを指定：

```bash
uv tool install git+https://github.com/aRaikoFunakami/speech2text.git@v1.0.0
```

### ローカルからインストール（開発用）

```bash
git clone https://github.com/aRaikoFunakami/speech2text.git
cd speech2text
uv sync
```

## セットアップ

OpenAI API キーを環境変数に設定：

```bash
export OPENAI_API_KEY='your-api-key'
```

## 使い方

```bash
# 基本的な使い方（音声/動画ファイルをテキストに変換）
speech2text input.mp4

# モデルを指定
speech2text input.mp3 -m gpt-4o-transcribe

# 言語を指定（精度・速度向上）
speech2text input.wav -l ja

# 出力形式を指定
speech2text input.mp4 -f srt

# ファイルに出力
speech2text input.mp4 -o output.txt

# すべてのオプションを組み合わせ
speech2text input.mp4 -m whisper-1 -l ja -f text -o result.txt
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `input_file` | 入力の音声/動画ファイルパス | （必須） |
| `-m, --model` | 使用する OpenAI モデル | `whisper-1` |
| `-l, --language` | 入力音声の言語（ISO-639-1） | 自動検出 |
| `-f, --format` | 出力形式（text, json, srt, vtt, verbose_json） | `text` |
| `-o, --output` | 出力ファイルパス | stdout |

### 対応入力形式

ffmpeg が対応するすべての音声/動画形式を入力可能。以下の形式は変換なしで直接 API に送信：

`flac`, `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `ogg`, `wav`, `webm`

それ以外の形式は自動的に mp3 に変換されます。

### 制限事項

- 音声ファイルのサイズ上限: **25 MB**（OpenAI API の制限）
- ffmpeg がシステムにインストールされている必要があります

## 開発

```bash
# テスト実行
uv run pytest

# ローカルで直接実行
uv run speech2text --help
```

## ライセンス

MIT
