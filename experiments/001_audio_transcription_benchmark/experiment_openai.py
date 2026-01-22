# OpenAI gpt-4o-transcribe（話者分離付き）の検証コード
# このコードをノートブックに新しいセルとしてコピーしてください

# =============================================================================
# セル1: OpenAI クライアントの初期化
# =============================================================================
"""
# OpenAI クライアントの初期化
from openai import OpenAI

# .envを再読み込み（OPENAI_API_KEYを追加した場合）
load_dotenv(project_root / '.env', override=True)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print(f"OpenAI API Key loaded: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
"""

# =============================================================================
# セル2: OpenAI Whisper関数の定義
# =============================================================================
"""
def transcribe_with_openai_diarization(audio_path: str) -> tuple[str, list]:
    '''
    OpenAI gpt-4o-transcribe を使って話者分離付きで文字起こし
    
    Returns:
        tuple: (フルテキスト, セグメントリスト)
    '''
    with open(audio_path, "rb") as audio_file:
        response = openai_client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file,
            response_format="verbose_json",
            language="ja"
        )
    
    # フルテキストを構築
    full_text = response.text
    
    # セグメント情報を取得（話者情報がある場合）
    segments = []
    if hasattr(response, 'segments'):
        for seg in response.segments:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": getattr(seg, 'speaker', 'unknown')
            })
    
    return full_text, segments


def scoping_with_openai_whisper(video_path: str, duration: int = 300) -> dict:
    '''
    OpenAI gpt-4o-transcribe方式: 話者分離付き文字起こし → スコーピング
    '''
    result = {
        "method": "OpenAI gpt-4o-transcribe",
        "clip_time": 0,
        "extract_time": 0,
        "transcribe_time": 0,
        "analysis_time": 0,
        "total_time": 0,
        "transcript": "",
        "segments": [],
        "output": ""
    }
    
    start_total = time.time()
    
    # Step 1: クリップ作成
    start = time.time()
    clip_path = clip_video_head(video_path, duration)
    result["clip_time"] = time.time() - start
    print(f"  Step 1: クリップ作成 {result['clip_time']:.1f}秒")
    
    # Step 2: 音声抽出（mp3形式で出力 - OpenAI推奨）
    start = time.time()
    audio_path = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False).name
    (
        ffmpeg
        .input(clip_path)
        .output(audio_path, ac=1, ar=16000, acodec='libmp3lame', q=2)
        .overwrite_output()
        .run(quiet=True)
    )
    result["extract_time"] = time.time() - start
    print(f"  Step 2: 音声抽出 {result['extract_time']:.1f}秒")
    
    # Step 3: OpenAI Whisperで文字起こし（話者分離付き）
    start = time.time()
    transcript, segments = transcribe_with_openai_diarization(audio_path)
    result["transcribe_time"] = time.time() - start
    result["transcript"] = transcript
    result["segments"] = segments
    print(f"  Step 3: 文字起こし {result['transcribe_time']:.1f}秒 ({len(transcript)}文字)")
    
    # 話者情報があれば表示
    if segments:
        speakers = set(s.get('speaker', 'unknown') for s in segments)
        print(f"    話者数: {len(speakers)}")
    
    # Step 4: スコーピング解析（Geminiを使用）
    start = time.time()
    prompt = f"{SCOPING_PROMPT_AUDIO_ONLY}\\n\\n【音声書き起こし】\\n{transcript}"
    response = model.generate_content(prompt)
    result["analysis_time"] = time.time() - start
    print(f"  Step 4: 解析 {result['analysis_time']:.1f}秒")
    
    result["output"] = response.text
    result["total_time"] = time.time() - start_total
    
    # クリーンアップ
    os.unlink(clip_path)
    os.unlink(audio_path)
    
    return result

print("OpenAI Whisper関数を定義しました")
"""

# =============================================================================
# セル3: 検証実行
# =============================================================================
"""
# 方式4: OpenAI gpt-4o-transcribe
print("=" * 50)
print("方式4: OpenAI gpt-4o-transcribe（話者分離付き）")
print("=" * 50)
results["openai"] = scoping_with_openai_whisper(VIDEO_PATH)
print(f"\\n合計時間: {results['openai']['total_time']:.1f}秒")
print(f"\\n結果:\\n{results['openai']['output']}")
"""

# =============================================================================
# セル4: 全方式比較
# =============================================================================
"""
# 全方式の比較表（OpenAI含む）
print("="*60)
print("全方式比較")
print("="*60)

comparison_all = {
    "方式": ["動画そのまま", "音声のみ(Gemini)", "フレーム+音声", "OpenAI gpt-4o-transcribe"],
    "合計時間(秒)": [
        results["video"]["total_time"],
        results["audio"]["total_time"],
        results["hybrid"]["total_time"],
        results["openai"]["total_time"]
    ],
    "文字起こし(秒)": [
        "-",
        results["audio"].get("transcribe_time", "-"),
        results["hybrid"].get("transcribe_time", "-"),
        results["openai"].get("transcribe_time", "-")
    ],
    "解析(秒)": [
        results["video"]["analysis_time"],
        results["audio"]["analysis_time"],
        results["hybrid"]["analysis_time"],
        results["openai"]["analysis_time"]
    ]
}

df_all = pd.DataFrame(comparison_all)
print(df_all.to_string(index=False))
"""
