# 引継ぎくん

業務引継ぎを支援するAIアプリケーション。動画や資料から詳細な引継ぎドキュメントを自動生成します。

## 📚 プロジェクトドキュメント

開発状況やタスク管理については、以下のドキュメントを参照してください：

- 📊 **[実装状況整理](file:///.gemini/antigravity/brain/770cb451-012a-4e41-8701-1ffca33a88f7/implementation_status.md)** - Streamlit→HTMX移行後の実装状況
- 📋 **[タスクリスト](file:///.gemini/antigravity/brain/770cb451-012a-4e41-8701-1ffca33a88f7/task.md)** - 開発タスクと進捗管理
- 📖 **[タスク管理ガイド](file:///.gemini/antigravity/brain/770cb451-012a-4e41-8701-1ffca33a88f7/task_management_guide.md)** - GitHub Issueとの連携方法
- 📝 **[Phase 1 実装計画](file:///.gemini/antigravity/brain/770cb451-012a-4e41-8701-1ffca33a88f7/phase1_implementation_plan.md)** - SSE接続の詳細実装手順

## ✨ 機能

- **Human-in-the-Loop分析**: 冒頭5分の初期分析 → 質問 → 詳細解析の3段階フロー
- 動画（MP4/MOV/AVI/WebM）からの業務手順抽出
- タイムスタンプ付き操作手順の生成
- 6カテゴリの詳細チェックリスト
- Notion貼り付け用Markdownドキュメント生成

## セットアップ

### 1. 基本セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/hikitsugi-kun.git
cd hikitsugi-kun

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集してGOOGLE_API_KEYを設定
```

### 2. FFmpegセットアップ（動画フレーム抽出機能）

動画からフレームを抽出するにはFFmpegが必要です。

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update && sudo apt install ffmpeg
```

#### Windows
1. [FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロード
2. 解凍してパスを通す、または`C:\ffmpeg\bin`に配置

#### インストール確認
```bash
ffmpeg -version
```

### 3. 起動

```bash
# FastAPIアプリを起動
python main.py
```

ブラウザで `http://localhost:8000` が開きます（自動でポート検索）。

## 使い方

1. **資料/動画をアップロード**: PDF、Excel、Word、または動画ファイル（2GBまで）
2. **業務を説明**: チャットで業務内容を説明
3. **チェックリスト確認**: AIが6カテゴリのチェックリストを自動評価
4. **ドキュメント生成**: 「ドキュメント生成」ボタンでMarkdown出力

## 設定

### サイドバー
- **フレーム抽出間隔**: 動画からフレームを抽出する間隔（1-30秒）
- **フレームクリア**: 抽出済みフレームを削除

### Streamlit設定（.streamlit/config.toml）
```toml
[server]
maxUploadSize = 2000  # 2GBまでアップロード可能
```

## 環境変数

`.env`ファイルに以下を設定:

```
GOOGLE_API_KEY=your_google_api_key_here
```

Google AI Studioで[APIキーを取得](https://aistudio.google.com/app/apikey)できます。

## 技術スタック

- **バックエンド**: FastAPI
- **フロントエンド**: HTMX + Vanilla JavaScript
- **UI**: カスタムCSS（v0デザイン）
- **AI**: Google Gemini API (gemini-2.5-flash-lite)
- **動画処理**: FFmpeg + ffmpeg-python
- **画像処理**: Pillow
- **言語**: Python 3.14

## アーキテクチャ

```
hikitsugi-kun/
├── main.py                 # FastAPIアプリケーションエントリーポイント
├── routes/                 # APIルート定義
│   ├── upload.py          # ファイルアップロード + バックグラウンド処理
│   ├── questions.py       # SSEストリーム + 詳細解析
│   └── document.py        # ドキュメント生成
├── services/              # ビジネスロジック
│   ├── gemini.py         # Gemini API連携
│   └── session.py        # セッション管理
├── templates/             # Jinja2テンプレート
│   └── index.html        # メインSPA
├── static/                # 静的ファイル
│   ├── css/style.css     # カスタムスタイル
│   └── js/app.js         # フロントエンドロジック
└── frame_extractor.py     # 動画フレーム抽出
```

## チェックリストカテゴリ

1. **業務フロー**: 日次/週次/月次業務、イレギュラー対応
2. **システム操作**: ログイン、画面操作、データ入力、レポート出力
3. **ツール・アクセス権**: 使用ツール、権限、共有ドライブ、API連携
4. **関係者**: 社内/社外連絡先、エスカレーション先
5. **リスク・注意点**: エラー対処、インシデント事例、禁止事項、重要日程
6. **参考資料**: マニュアル、過去の引継ぎ資料、研修資料

## 注意事項

- FFmpegがインストールされていない場合、フレーム抽出機能は利用できません（動画分析自体は可能）
- 長時間動画（30分以上）はフレーム数が多くなるため、抽出間隔を長めに設定することを推奨
- 一時ファイルは24時間後に自動削除されます

## ライセンス

MIT License
