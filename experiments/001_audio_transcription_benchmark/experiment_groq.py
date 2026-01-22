# %% [markdown]
# # Groq Whisper 検証
# 
# OpenAI の `gpt-4o-transcribe` と Groq の `whisper-large-v3` / `whisper-large-v3-turbo` を比較検証します。
# 
# ## 目的
# - Groq の Whisper モデルが「ご視聴ありがとうございました」ハルシネーションを起こさないか確認する
# - 処理速度とコストを比較する

# %%
import os
import time
import tempfile
import ffmpeg
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# クライアント初期化
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# テスト動画パス
VIDEO_PATH = "test_video.mp4"

print("クライアント初期化完了")

# %%
def clip_video_head(video_path: str, duration: int = 300) -> str:
    """動画の冒頭N秒を切り出す"""
    output_path = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
    try:
        (
            ffmpeg
            .input(video_path, ss=0, t=duration)
            .output(output_path, c="copy", avoid_negative_ts="make_zero")
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error:
        # copyで失敗した場合は再エンコード
        (
            ffmpeg
            .input(video_path, ss=0, t=duration)
            .output(output_path)
            .overwrite_output()
            .run(quiet=True)
        )
    return output_path

def extract_audio(video_path: str, fmt: str = "mp3") -> str:
    """動画から音声を抽出"""
    output_path = tempfile.NamedTemporaryFile(suffix=f'.{fmt}', delete=False).name
    
    stream = ffmpeg.input(video_path)
    
    if fmt == "mp3":
        # MP3 (圧縮)
        stream = stream.output(output_path, ac=1, ar=16000, acodec='libmp3lame', q=2)
    else:
        # WAV (非圧縮)
        stream = stream.output(output_path, ac=1, ar=16000)
        
    stream.overwrite_output().run(quiet=True)
    return output_path

print("ユーティリティ関数定義完了")

# %%
# 音声ファイル準備
start = time.time()
clip_path = clip_video_head(VIDEO_PATH, 300)
mp3_path = extract_audio(clip_path, "mp3")
print(f"準備完了: {time.time() - start:.1f}秒")

# %%
def transcribe_openai_gpt4o(audio_path: str) -> dict:
    """OpenAI gpt-4o-transcribe (Baseline)"""
    start = time.time()
    with open(audio_path, "rb") as f:
        response = openai_client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f,
            response_format="json",
            language="ja"
        )
    duration = time.time() - start
    return {"text": response.text, "time": duration}

def transcribe_groq(audio_path: str, model: str) -> dict:
    """Groq Whisper"""
    start = time.time()
    with open(audio_path, "rb") as f:
        # Prompt injection for safety
        response = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model=model,
            prompt="これは社内会議の録画です。業務の引継ぎについて話しています。",
            response_format="json",
            language="ja",
            temperature=0.0
        )
    duration = time.time() - start
    return {"text": response.text, "time": duration}

print("文字起こし関数定義完了")

# %%
# 実験実行
results = []

print("1. OpenAI gpt-4o-transcribe (Baseline) 実行中...")
try:
    res = transcribe_openai_gpt4o(mp3_path)
    results.append({"name": "OpenAI gpt-4o", **res})
    print(f"  -> 完了 ({res['time']:.1f}秒)")
except Exception as e:
    print(f"  -> エラー: {e}")
    results.append({"name": "OpenAI gpt-4o", "error": str(e)})

print("2. Groq whisper-large-v3 実行中...")
try:
    res = transcribe_groq(mp3_path, "whisper-large-v3")
    results.append({"name": "Groq V3", **res})
    print(f"  -> 完了 ({res['time']:.1f}秒)")
except Exception as e:
    print(f"  -> エラー: {e}")
    results.append({"name": "Groq V3", "error": str(e)})

print("3. Groq whisper-large-v3-turbo 実行中...")
try:
    res = transcribe_groq(mp3_path, "whisper-large-v3-turbo")
    results.append({"name": "Groq Turbo", **res})
    print(f"  -> 完了 ({res['time']:.1f}秒)")
except Exception as e:
    print(f"  -> エラー: {e}")
    results.append({"name": "Groq Turbo", "error": str(e)})

# %%
# 結果表示
print("\n" + "="*80)
print(f"{'モデル名':<20} | {'時間':<6} | {'文字数':<6} | {'ハルシネーションチェック'}")
print("-" * 80)

for r in results:
    if "error" in r:
        print(f"{r['name']:<20} | エラー: {r['error']}")
        continue
        
    text = r['text']
    hallucination = "ご視聴" in text or "ご覧いただき" in text
    status = "🚨 あり" if hallucination else "✅ なし"
    
    print(f"{r['name']:<20} | {r['time']:.1f}s  | {len(text):<6} | {status}")
    
    # テキスト冒頭を表示
    print(f"  Preview: {text[:100]}...")
    print("-" * 80)

# %%
# クリーンアップ
os.unlink(clip_path)
os.unlink(mp3_path)
