import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# モデル設定（最安のgemini-2.5-flash-lite）
model = genai.GenerativeModel('gemini-2.5-flash-lite')


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

# セッション状態で会話履歴保持
if "messages" not in st.session_state:
    st.session_state.messages = []

# チェックリストテンプレート（MVP用固定）
CHECKLIST_TEMPLATE = """
業務フロー, 主要ツール操作, リスク・注意点, 顧客対応, 関係者一覧, etc. (合計10項目)
各項目に現状充填度(0-100%)を付けて。
"""

st.title("引継ぎくん MVP - 離職/異動専用")

# ファイルアップロード（2GB制限 - Gemini File API）
MAX_FILE_SIZE_MB = 2000  # 2GB
uploaded_file = st.file_uploader(
    "資料 or 録画(MP4)をアップロード",
    type=["pdf", "xlsx", "docx", "mp4"]
)

# ファイル処理（セッションでキャッシュ）
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None
    st.session_state.processed_file_name = None

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
    else:
        # 既にアップロード済み
        file_part = st.session_state.processed_file
        st.success(f"ファイル読み込み済み: {uploaded_file.name}")

# チャット表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("業務説明や質問をどうぞ"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini呼び出し（ファイルがあれば含めて）
    contents = []
    if file_part:
        # 処理済みファイルを含める（動画は自動で1fps + 音声解析済み）
        contents.append(file_part)
    contents.append(prompt)

    # システムプロンプトで引継ぎモード固定
    # 低解像度で節約したい場合
    # generation_config={"media_resolution": "low"}  # または "high"
    response = model.generate_content(
        ["あなたは引継ぎ支援AIです。資料を基に業務理解し、チェックリストを作成。不足項目を質問で埋め、90%以上でMarkdownドキュメント生成。"] + contents,
        stream=True,  # ストリーミングでリアルタイム表示
        # generation_config={"media_resolution": "low"}  # コスト節約用（後で有効化）
    )

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 最終出力ボタン（充填完了したら押す）
if st.button("ドキュメント生成（Notion貼り付け用）"):
    if len(st.session_state.messages) > 1:
        final_prompt = "現在の会話とチェックリストから、Notion貼り付け用Markdownドキュメントを作成。# 業務引継ぎドキュメント 見出し/リスト/テーブル/図解(nano banana生成)。"
        response = model.generate_content(final_prompt)
        st.markdown("### 生成されたMarkdown（コピーしてNotionにペースト）")
        st.code(response.text, language="markdown")
    else:
        st.warning("会話が進んでから押してください。")