# 引継ぎくん

業務引継ぎを支援するAIアプリケーション。動画や資料から詳細な引継ぎドキュメントを自動生成します。

## 機能

- 動画（MP4/MOV/AVI/WebM）からの業務手順抽出
- PDF/Excel/Word資料の分析
- タイムスタンプ付き操作手順の生成
- 6カテゴリの詳細チェックリスト
- Notion貼り付け用Markdownドキュメント生成
- 動画フレームの自動抽出・可視化

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
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。

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

- **フロントエンド**: Streamlit
- **AI**: Google Gemini API (gemini-2.5-flash-lite)
- **動画処理**: FFmpeg + ffmpeg-python
- **画像処理**: Pillow
- **言語**: Python 3.14

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
