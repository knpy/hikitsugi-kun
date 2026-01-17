# 引継ぎくん 開発ガイドライン

## Git ワークフロー

### ブランチ戦略
- `main`: 本番ブランチ（直接プッシュ禁止）
- `feature/xxx`: 機能追加
- `fix/xxx`: バグ修正
- `refactor/xxx`: リファクタリング

### 開発フロー
```bash
# 1. mainから最新を取得
git checkout main
git pull origin main

# 2. 機能ブランチを作成
git checkout -b feature/機能名

# 3. 変更をコミット（日本語でOK）
git add .
git commit -m "機能の説明"

# 4. リモートにプッシュ
git push -u origin feature/機能名

# 5. PRを作成
gh pr create --title "PRタイトル" --body "説明"
```

### コミットメッセージ
- 日本語で記述
- 簡潔に変更内容を説明
- 例: `チャット履歴の保存機能を追加`

## 技術スタック

- **フロントエンド**: Streamlit
- **AI**: Google Gemini API (gemini-2.5-flash-lite)
- **言語**: Python 3.14

## 環境構築

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# GOOGLE_API_KEY を設定

# 起動
streamlit run app.py
```

## 環境変数

`.env` ファイルに以下を設定:
```
GOOGLE_API_KEY=your_api_key_here
```

## Streamlit設定

`.streamlit/config.toml`:
- `maxUploadSize = 2000`: アップロード上限2GB（動画対応）

## Gemini API メモ

```python
# 低解像度で節約したい場合（動画処理）
generation_config={"media_resolution": "low"}  # または "high"
```
