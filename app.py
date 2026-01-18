import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import os
import time
import tempfile
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path

from frame_extractor import (
    extract_frames,
    cleanup_frames,
    generate_frames_summary,
    replace_image_placeholders,
)

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# モデル設定（最安のgemini-2.5-flash-lite）
model = genai.GenerativeModel('gemini-2.5-flash-lite')


def parse_retry_delay(error_message: str) -> int:
    """エラーメッセージからリトライ待機時間を抽出"""
    match = re.search(r'retry in (\d+(?:\.\d+)?)', str(error_message), re.IGNORECASE)
    if match:
        return int(float(match.group(1))) + 1
    return 30  # デフォルト30秒


def generate_with_retry(contents, stream=False, max_retries=3):
    """リトライ機能付きのAPI呼び出し"""
    for attempt in range(max_retries):
        try:
            return model.generate_content(contents, stream=stream)
        except google_exceptions.ResourceExhausted as e:
            wait_time = parse_retry_delay(str(e))
            if attempt < max_retries - 1:
                with st.spinner(f"⏳ レート制限中... {wait_time}秒後にリトライします"):
                    time.sleep(wait_time)
            else:
                raise e
        except Exception as e:
            raise e

# 詳細システムプロンプト
SYSTEM_PROMPT = """あなたは業務引継ぎ専門の支援AIです。

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

## 出力形式
### [MM:SS] ステップタイトル
- **操作**: 具体的なクリック/入力内容
- **画面**: 表示されている画面名/URL
- **音声説明**: 「〜」（話者の言葉をそのまま記録）
- **注意点**: 動画内で言及された注意事項

## チェックリスト充填基準（90%以上 = 細部までカバー）
- 全操作手順が省略なく記録されている
- システム固有の用語/パスが正確に記載
- 例外処理・エラー対応が含まれている
- 担当者名・連絡先が把握されている
"""

# 詳細チェックリストテンプレート（6カテゴリ）
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


def upload_and_wait_for_processing(uploaded_file):
    """ファイルをアップロードし、処理完了まで待機（動画は1fps + 音声解析）"""
    file = genai.upload_file(uploaded_file, mime_type=uploaded_file.type)

    # 動画の場合は処理完了を待つ
    if uploaded_file.type.startswith("video/"):
        with st.spinner("動画を処理中...（フレーム抽出 + 音声解析）"):
            while file.state.name == "PROCESSING":
                time.sleep(2)
                file = genai.get_file(file.name)

            if file.state.name != "ACTIVE":
                st.error(f"動画処理に失敗しました: {file.state.name}")
                return None

            st.success("動画処理完了")

    return file


def cleanup_old_temp_dirs(base_path: str = "/tmp", max_age_hours: int = 24):
    """24時間以上前の一時ディレクトリを自動削除"""
    try:
        base = Path(base_path)
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        for item in base.glob("hikitsugi_frames_*"):
            if item.is_dir():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff:
                    shutil.rmtree(item)
    except Exception:
        pass  # クリーンアップ失敗は無視


def extract_frames_from_uploaded_video(uploaded_file, interval_seconds: int = 5):
    """アップロードされた動画からフレームを抽出"""
    # 一時ファイルに保存
    temp_video = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{uploaded_file.name.split('.')[-1]}"
    )
    try:
        temp_video.write(uploaded_file.getvalue())
        temp_video.close()

        # フレーム抽出
        frames = extract_frames(
            temp_video.name,
            interval_seconds=interval_seconds,
            max_width=800
        )
        return frames
    finally:
        # 一時ファイル削除
        try:
            os.unlink(temp_video.name)
        except Exception:
            pass


# 起動時クリーンアップ
cleanup_old_temp_dirs()

# セッション状態で会話履歴保持
if "messages" not in st.session_state:
    st.session_state.messages = []

# ファイル処理（セッションでキャッシュ）
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None
    st.session_state.processed_file_name = None

# フレーム抽出結果
if "extracted_frames" not in st.session_state:
    st.session_state.extracted_frames = None

# フレーム抽出間隔
if "frame_interval" not in st.session_state:
    st.session_state.frame_interval = 5

# 動画分析結果（初回のみ動画を送信し、結果を保存）
if "video_analysis" not in st.session_state:
    st.session_state.video_analysis = None

# ページ設定
st.set_page_config(page_title="引継ぎくん", page_icon="📋", layout="wide")

st.title("📋 引継ぎくん - 業務引継ぎ支援AI")

# サイドバー設定パネル
with st.sidebar:
    st.header("⚙️ 設定")

    # フレーム抽出間隔
    frame_interval = st.slider(
        "フレーム抽出間隔（秒）",
        min_value=1,
        max_value=30,
        value=st.session_state.frame_interval,
        help="動画からフレームを抽出する間隔を設定します。短いほど詳細になりますが、処理時間が増加します。"
    )
    st.session_state.frame_interval = frame_interval

    # 抽出済みフレーム情報
    if st.session_state.extracted_frames:
        st.success(generate_frames_summary(st.session_state.extracted_frames))

        if st.button("🗑️ フレームをクリア"):
            cleanup_frames(st.session_state.extracted_frames)
            st.session_state.extracted_frames = None
            st.rerun()
    else:
        st.info("動画をアップロードするとフレームが抽出されます")

    st.divider()

    # 動画分析状況
    st.subheader("📹 動画分析")
    if st.session_state.video_analysis:
        st.success("分析済み（トークン節約モード）")
        if st.button("🔄 再分析する"):
            st.session_state.video_analysis = None
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("未分析（初回チャットで分析）")

    st.divider()

    # チェックリスト表示
    st.subheader("📝 チェックリスト項目")
    st.markdown("""
    1. 業務フロー
    2. システム操作
    3. ツール・アクセス権
    4. 関係者
    5. リスク・注意点
    6. 参考資料
    """)

# ファイルアップロード（2GB制限 - Gemini File API）
MAX_FILE_SIZE_MB = 2000  # 2GB
uploaded_file = st.file_uploader(
    "📁 資料 or 録画(MP4)をアップロード",
    type=["pdf", "xlsx", "docx", "mp4", "mov", "avi", "webm"]
)

file_part = None
if uploaded_file:
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"ファイルが大きすぎます（{file_size_mb:.1f}MB）。2GB以下にしてください。")
    elif st.session_state.processed_file_name != uploaded_file.name:
        # 新しいファイルをアップロード
        st.info(f"アップロード中: {uploaded_file.name} ({file_size_mb:.1f}MB)")
        file_part = upload_and_wait_for_processing(uploaded_file)
        if file_part:
            st.session_state.processed_file = file_part
            st.session_state.processed_file_name = uploaded_file.name

            # 動画の場合はフレーム抽出
            if uploaded_file.type.startswith("video/"):
                with st.spinner("フレームを抽出中..."):
                    try:
                        frames = extract_frames_from_uploaded_video(
                            uploaded_file,
                            interval_seconds=st.session_state.frame_interval
                        )
                        st.session_state.extracted_frames = frames
                        st.success(f"フレーム抽出完了: {len(frames)}枚")
                    except Exception as e:
                        st.warning(f"フレーム抽出に失敗しました（FFmpegが必要です）: {e}")
    else:
        # 既にアップロード済み
        file_part = st.session_state.processed_file
        st.success(f"✅ ファイル読み込み済み: {uploaded_file.name}")

# チャット表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("業務説明や質問をどうぞ"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini呼び出し
    contents = [SYSTEM_PROMPT]

    # 初回かつ動画がある場合：動画を送信して詳細分析
    is_first_message = len(st.session_state.messages) == 1
    has_video = file_part and st.session_state.processed_file_name and \
                st.session_state.processed_file_name.lower().endswith(('.mp4', '.mov', '.avi', '.webm'))

    if is_first_message and has_video and st.session_state.video_analysis is None:
        # 初回：動画を送信して詳細分析を取得
        contents.append(file_part)
        contents.append(f"""
{prompt}

以下のチェックリストを基に、動画の内容を詳細に分析してください。
この分析結果は後続の会話で参照されるため、省略せず全ての情報を記録してください。

{CHECKLIST_TEMPLATE}
""")
        st.info("📹 動画を分析中...（初回のみ動画を送信します）")
    elif st.session_state.video_analysis:
        # 2回目以降：保存された分析結果を使用（動画は送らない）
        contents.append(f"""
## 以前の動画分析結果
{st.session_state.video_analysis}

## ユーザーの質問
{prompt}

上記の分析結果を基に回答してください。
""")
    elif file_part and not has_video:
        # 動画以外のファイル（PDF等）は毎回送信
        contents.append(file_part)
        contents.append(prompt)
        if is_first_message:
            contents.append(f"\n\n以下のチェックリストを基に分析してください:\n{CHECKLIST_TEMPLATE}")
    else:
        # ファイルなしの場合
        contents.append(prompt)

    try:
        response = generate_with_retry(contents, stream=True)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in response:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # 初回の動画分析結果を保存
        if is_first_message and has_video and st.session_state.video_analysis is None:
            st.session_state.video_analysis = full_response
            st.success("✅ 動画分析完了！以降の会話では分析結果を参照します（トークン節約）")

    except google_exceptions.ResourceExhausted as e:
        wait_time = parse_retry_delay(str(e))
        st.error(f"⚠️ APIレート制限に達しました。{wait_time}秒後に再度お試しください。")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# ドキュメント生成セクション
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 ドキュメント生成（Notion貼り付け用）", use_container_width=True):
        if len(st.session_state.messages) > 1:
            frame_table = ""  # 使用しないが互換性のため残す

            # 会話履歴と分析結果をまとめる
            history_text = ""
            if st.session_state.video_analysis:
                history_text += f"## 動画分析結果\n{st.session_state.video_analysis}\n\n"

            for msg in st.session_state.messages:
                role = "ユーザー" if msg["role"] == "user" else "AI"
                history_text += f"## {role}の発言\n{msg['content']}\n\n"

            final_prompt = f"""
以下のこれまでの会話履歴と分析結果を元に、Notion貼り付け用Markdownドキュメントを作成してください。

---
{history_text}
---

出力は必ず**日本語**で行ってください。

## 画像挿入指示 (重要)
操作手順の各ステップにおいて、**必ず**その時点のタイムスタンプに対応する画像プレースホルダー `[IMAGE: MM:SS]` を挿入してください。
動画分析結果にあるタイムスタンプ（例: 01:25, 03:30）をそのまま利用してください。

**出力例（このように出力してください）:**
1. ログイン画面を開きます。
[IMAGE: 00:05]
2. ユーザー名を入力します。
[IMAGE: 01:25]
3. エラーが発生しました。
[IMAGE: 08:21]

※ `[IMAGE: MM:SS]` の形式を厳守してください。これ以外（例: (画像: 00:05) など）は機能しません。
※ 分析結果にタイムスタンプがある箇所は、積極的に画像を挿入してください。

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
            try:
                with st.spinner("ドキュメントを生成中..."):
                    response = generate_with_retry(final_prompt, stream=False)
                
                # 画像プレースホルダーを実際の画像に置換
                if st.session_state.extracted_frames:
                    full_markdown = replace_image_placeholders(response.text, st.session_state.extracted_frames)
                else:
                    full_markdown = response.text

                st.markdown("### 📄 生成されたドキュメント")
                st.markdown(full_markdown, unsafe_allow_html=True)
            except google_exceptions.ResourceExhausted as e:
                wait_time = parse_retry_delay(str(e))
                st.error(f"⚠️ APIレート制限に達しました。{wait_time}秒後に再度お試しください。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
        else:
            st.warning("会話が進んでから押してください。")

with col2:
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.processed_file = None
        st.session_state.processed_file_name = None
        st.session_state.extracted_frames = None
        st.session_state.video_analysis = None
        st.rerun()
