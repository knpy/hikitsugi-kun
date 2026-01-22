# Whisper-1 ハルシネーション対策の検証コード
# このコードをノートブックにコピーしてください

# =============================================================================
# セル: 対策版 Whisper-1 関数定義
# =============================================================================
"""
def transcribe_with_whisper1_robust(audio_path: str, prompt: str = None, temperature: float = 0.0) -> str:
    '''
    OpenAI whisper-1 で文字起こし（対策版）
    Args:
        prompt: コンテキストを与えるためのプロンプト
        temperature: 生成の多様性（0.0は最も決定的）
    '''
    params = {
        "model": "whisper-1",
        "file": open(audio_path, "rb"),
        "response_format": "json",
        "language": "ja",
        "temperature": temperature
    }
    
    if prompt:
        params["prompt"] = prompt
        
    response = openai_client.audio.transcriptions.create(**params)
    return response.text

print("対策版 Whisper関数を定義しました")
"""

# =============================================================================
# セル: 検証実行（3パターン）
# =============================================================================
"""
# 検証用の共通関数
def run_whisper_experiment(name: str, audio_path: str, prompt: str = None, temp: float = 0.0):
    print("=" * 60)
    print(f"実験: {name}")
    print("=" * 60)
    
    start = time.time()
    try:
        transcript = transcribe_with_whisper1_robust(audio_path, prompt, temp)
        duration = time.time() - start
        
        print(f"処理時間: {duration:.1f}秒")
        print(f"文字数: {len(transcript)}")
        print("-" * 30)
        print(transcript[:200] + "..." if len(transcript) > 200 else transcript)
        
        # ハルシネーション簡易チェック
        if "ご視聴ありがとうございました" in transcript:
            print("🚨 警告: ハルシネーション検出")
        else:
            print("✅ ハルシネーションなし")
            
        return {"name": name, "time": duration, "length": len(transcript), "hallucination": "ご視聴" in transcript}
            
    except Exception as e:
        print(f"エラー: {e}")
        return {"name": name, "error": str(e)}

# --- 準備: 音声ファイル作成 ---
start = time.time()
clip_path = clip_video_head(VIDEO_PATH, 300)

# MP3 (圧縮)
mp3_path = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False).name
ffmpeg.input(clip_path).output(mp3_path, ac=1, ar=16000, acodec='libmp3lame', q=2).overwrite_output().run(quiet=True)

# WAV (非圧縮)
wav_path = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
ffmpeg.input(clip_path).output(wav_path, ac=1, ar=16000).overwrite_output().run(quiet=True)
print(f"音声ファイル準備完了 ({time.time() - start:.1f}秒)")

# --- 実験実行 ---
exp_results = []

# 実験A: MP3 + プロンプトあり
exp_results.append(run_whisper_experiment(
    "A: MP3 + プロンプト", 
    mp3_path, 
    prompt="これは社内会議の録画です。業務の引継ぎについて話しています。"
))

# 実験B: WAV + プロンプトあり
exp_results.append(run_whisper_experiment(
    "B: WAV + プロンプト", 
    wav_path, 
    prompt="これは社内会議の録画です。業務の引継ぎについて話しています。"
))

# 実験C: MP3 + プロンプト + temperature=0.2 (少し緩める)
exp_results.append(run_whisper_experiment(
    "C: MP3 + プロンプト + temp=0.2", 
    mp3_path, 
    prompt="これは社内会議の録画です。業務の引継ぎについて話しています。",
    temp=0.2
))

# クリーンアップ
os.unlink(clip_path)
os.unlink(mp3_path)
os.unlink(wav_path)
"""

# =============================================================================
# セル: 比較結果表示
# =============================================================================
"""
print("="*60)
print("Whisper-1 対策検証結果")
print("="*60)
print(f"{'実験名':<30} | {'時間':<6} | {'文字数':<6} | {'ハルシネーション'}")
print("-" * 70)
for r in exp_results:
    if "error" in r:
        print(f"{r['name']:<30} | エラー: {r['error']}")
    else:
        status = "🚨 あり" if r['hallucination'] else "✅ なし"
        print(f"{r['name']:<30} | {r['time']:.1f}s  | {r['length']:<6} | {status}")
"""
