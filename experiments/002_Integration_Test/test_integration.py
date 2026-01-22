# %% [markdown]
# # 統合テスト: 音声スコーピング処理
#
# `services/gemini.py` に実装された `analyze_audio_scoping_from_video` 関数をテストします。

# %%
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(os.getcwd())
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.gemini import analyze_audio_scoping_from_video

# 環境変数読み込み
load_dotenv()

# ロガー設定 (これがないと services/gemini.py のログが出ない)
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# テスト動画パス (001実験から流用)
VIDEO_PATH = project_root / "experiments/001_audio_transcription_benchmark/test_video.mp4"

print(f"テスト対象動画: {VIDEO_PATH}")
print(f"存在確認: {VIDEO_PATH.exists()}")

if not VIDEO_PATH.exists():
    raise FileNotFoundError(f"Test video not found at {VIDEO_PATH}")

# %%
async def main():
    print("=" * 60)
    print("統合テスト開始: analyze_audio_scoping_from_video")
    print("=" * 60)

    # ログコールバック関数を定義
    logged_messages = []
    def log_callback(msg):
        logged_messages.append(msg)
        print(f"[LOG CALLBACK] {msg}")

    try:
        # スコーピング実行（log_callbackを渡す）
        result = await analyze_audio_scoping_from_video(str(VIDEO_PATH), user_context="これはテスト実行です。", log_callback=log_callback)

        print("\n" + "=" * 60)
        print("✅ テスト成功: 結果")
        print("=" * 60)
        print(result)

        print("\n" + "=" * 60)
        print("📊 ログコールバック確認")
        print("=" * 60)
        print(f"ログメッセージ数: {len(logged_messages)}")
        for i, msg in enumerate(logged_messages, 1):
            print(f"{i}. {msg}")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ テスト失敗: エラー")
        print("=" * 60)
        print(e)
        raise e

# %%
# 実行
if __name__ == "__main__":
    asyncio.run(main())
