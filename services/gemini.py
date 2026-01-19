"""
Gemini API連携サービス
"""
import os
import re
import time
import asyncio
import logging
from typing import AsyncGenerator, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ロガー設定
logger = logging.getLogger(__name__)

# モデル設定
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# システムプロンプト
SYSTEM_PROMPT = """あなたは業務引継ぎ専門の支援AIです。

## 最重要ルール（必ず守ること）
- **動画に存在しない情報は絶対に出力しない**
- **推測や想像で情報を補完しない**
- **動画で確認できた内容のみを記述する**
- 不明な点は「動画内で言及なし」「確認できず」と明記する

## 動画分析の基本方針
1. タイムスタンプ（MM:SS形式）ごとに動画内容を分解
2. 各タイムスタンプで以下を詳細に記述：
   - 画面上で行われている操作（クリック位置、メニュー選択、入力内容）
   - 使用しているツール/システム名
   - 画面遷移の流れ
   - 音声での説明内容（ニュアンスや注意点も含む）

## 禁止事項
- 「など」「といった」での省略禁止
- 「詳細は動画を参照」禁止
- 操作手順の簡略化禁止
- **動画に存在しない情報の捏造は絶対禁止**

## 出力形式
### [MM:SS] ステップタイトル
- **操作**: 具体的なクリック/入力内容
- **画面**: 表示されている画面名/URL
- **音声説明**: 「〜」（話者の言葉をそのまま記録）
- **注意点**: 動画内で言及された注意事項

## チェックリスト充填基準
- 動画内で確認できた項目のみチェックを入れる
- 確認できなかった項目は空欄のままにする
- 推測で項目を埋めない
"""

SCOPING_PROMPT = """
あなたは業務引継ぎの専門家です。
これは引継ぎ動画の「冒頭5分間」です。この動画を見て、以下の3点を簡潔に出力してください。

1. **業務テーマ**: 何の業務についての動画か（1行で）
2. **対象者**: 誰に向けた説明か
3. **解析方針案**: この動画全体を解析して引継ぎ資料を作る際、どこを重点的に見るべきか、何に注意すべきか（箇条書き3点以内）

出力形式:
---
【業務テーマ】
...
【対象者】
...
【解析方針案】
- ...
- ...
- ...
"""

CHECKLIST_TEMPLATE = """
## 引継ぎチェックリスト

### 1. 業務フロー
- [ ] 日次業務の手順
- [ ] 週次業務の手順
- [ ] 月次業務の手順
- [ ] イレギュラー対応フロー

### 2. システム操作
- [ ] ログイン方法・認証情報の場所
- [ ] 主要画面の操作手順
- [ ] データ入力・更新手順
- [ ] レポート出力手順

### 3. ツール・アクセス権
- [ ] 使用ツール一覧
- [ ] アクセス権限の確認方法
- [ ] 共有ドライブ・フォルダのパス
- [ ] API/外部連携の設定

### 4. 関係者
- [ ] 社内連絡先（名前・役割・連絡方法）
- [ ] 社外連絡先（顧客・ベンダー）
- [ ] エスカレーション先

### 5. リスク・注意点
- [ ] よくあるエラーと対処法
- [ ] 過去のインシデント事例
- [ ] 絶対にやってはいけないこと
- [ ] 締め切り・重要日程

### 6. 参考資料
- [ ] マニュアル・ドキュメントの場所
- [ ] 過去の引継ぎ資料
- [ ] 研修資料・動画

各項目の現状充填度を0-100%で評価してください。
"""

# 企画書に基づく会話形式の質問
CONVERSATIONAL_QUESTIONS = [
    {
        "id": "business_type",
        "question": "この動画は何の業務についてですか？",
        "placeholder": "例: 月次請求書の処理フロー",
        "skippable": True,
    },
    {
        "id": "focus_points",
        "question": "特に重点的に説明してほしい箇所はありますか？",
        "placeholder": "例: エラー時の対応手順、承認フローの詳細",
        "skippable": True,
    },
    {
        "id": "handover_target",
        "question": "引継ぎ先の方はどんな方ですか？",
        "placeholder": "例: 新入社員、他部署からの異動者",
        "skippable": True,
    },
]


def parse_retry_delay(error_message: str) -> int:
    """エラーメッセージからリトライ待機時間を抽出"""
    match = re.search(r'retry in (\d+(?:\.\d+)?)', str(error_message), re.IGNORECASE)
    if match:
        return int(float(match.group(1))) + 1
    return 30


async def generate_with_retry(contents, stream: bool = False, max_retries: int = 3):
    """リトライ機能付きのAPI呼び出し（非同期）"""
    for attempt in range(max_retries):
        try:
            # 同期APIを非同期で実行
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(contents, stream=stream)
            )
            return response
        except google_exceptions.ResourceExhausted as e:
            wait_time = parse_retry_delay(str(e))
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                raise e
        except Exception as e:
            raise e


async def upload_video_to_gemini(file_path: str, mime_type: str) -> object:
    """動画をGemini File APIにアップロード"""
    logger.info(f"Uploading to Gemini: {file_path} (type: {mime_type})")

    loop = asyncio.get_event_loop()

    # アップロード
    file = await loop.run_in_executor(
        None,
        lambda: genai.upload_file(file_path, mime_type=mime_type)
    )
    logger.info(f"Upload started. File name: {file.name}, state: {file.state.name}")

    # 処理完了を待機
    wait_count = 0
    while file.state.name == "PROCESSING":
        wait_count += 1
        logger.info(f"Waiting for processing... ({wait_count * 2}s)")
        await asyncio.sleep(2)
        file = await loop.run_in_executor(
            None,
            lambda: genai.get_file(file.name)
        )

    logger.info(f"Final state: {file.state.name}")

    if file.state.name != "ACTIVE":
        raise RuntimeError(f"動画処理失敗: {file.state.name}")

    return file


async def analyze_video_scoping(gemini_file: object, user_context: str = "") -> str:
    """動画の初期診断（スコーピング）"""
    logger.info(f"Starting scoping analysis for file: {gemini_file.name}")

    prompt = SCOPING_PROMPT
    if user_context:
        prompt += f"\n【ユーザーからの事前情報】\n{user_context}"

    logger.info(f"Scoping prompt length: {len(prompt)} chars")
    logger.debug(f"Full prompt: {prompt}")

    # 動画ファイルを最初に、プロンプトを後に配置
    contents = [gemini_file, prompt]
    logger.info(f"Sending to Gemini: [video file: {gemini_file.name}] + [prompt]")

    response = await generate_with_retry(contents)
    logger.info(f"Scoping response received. Length: {len(response.text)} chars")
    return response.text


async def analyze_video_full(gemini_file: object, user_policy: str) -> str:
    """動画の詳細解析"""
    prompt = f"""
【ユーザーご指定の解析方針】
{user_policy}

上記の方針に従い、以下のシステムプロンプトに基づいて動画を詳細分析してください。
もし方針に特定の指示（例：「エラー対応を重点的に」）がある場合は、それを最優先してください。

---
{SYSTEM_PROMPT}
---
以下のチェックリストを基に、動画の内容を詳細に分析してください。
この分析結果は後続の会話で参照されるため、省略せず全ての情報を記録してください。

{CHECKLIST_TEMPLATE}
"""
    response = await generate_with_retry([gemini_file, prompt])
    return response.text


async def generate_document(video_analysis: str, user_policy: str) -> str:
    """引継ぎドキュメントを生成"""
    prompt = f"""
以下の動画分析結果を元に、Notion貼り付け用Markdownドキュメントを作成してください。

---
## 動画分析結果
{video_analysis}

## ユーザー方針
{user_policy}
---

出力は必ず**日本語**で行ってください。

## 画像挿入指示 (重要)
操作手順の各ステップにおいて、**必ず**その時点のタイムスタンプに対応する画像プレースホルダー `[IMAGE: MM:SS]` を挿入してください。

# 業務引継ぎドキュメント

## 概要
（業務の概要を3-5行で）

## タイムライン別操作手順
（動画の内容をタイムスタンプ順に記載。**各項目の直後に必ず [IMAGE: MM:SS] を入れること**）

## 詳細手順
（各操作の詳細な手順。**各ステップの直後に必ず [IMAGE: MM:SS] を入れること**）

## チェックリスト
（充填済みチェックリスト）

## 関係者一覧
（担当者・連絡先のテーブル）

## 注意事項・リスク
（重要な注意点）

---
"""
    response = await generate_with_retry(prompt)
    return response.text


async def stream_generate(contents) -> AsyncGenerator[str, None]:
    """ストリーミングで生成（SSE用）"""
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: model.generate_content(contents, stream=True)
    )
    for chunk in response:
        yield chunk.text
