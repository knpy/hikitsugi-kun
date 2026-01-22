"""
ファイルアップロード関連のルート
"""
import os
import tempfile
import shutil
import asyncio
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from services.session import get_or_create_session, ProcessingPhase
from services.gemini import upload_video_to_gemini, analyze_video_scoping, analyze_audio_scoping_from_video
from frame_extractor import extract_frames, clip_video_head

router = APIRouter()

# アップロード上限（2GB）
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

# 一時ファイル保存先
TEMP_DIR = Path(tempfile.gettempdir()) / "hikitsugi_uploads"
TEMP_DIR.mkdir(exist_ok=True)


def process_video_background(session_id: str, file_path: str, mime_type: str):
    """バックグラウンドで動画を処理（同期ラッパー）"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting background processing for session {session_id}")
    logger.info(f"File path: {file_path}")
    logger.info(f"MIME type: {mime_type}")
    logger.info(f"File exists: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        logger.info(f"File size: {os.path.getsize(file_path)} bytes")
    try:
        asyncio.run(_process_video_async(session_id, file_path, mime_type))
        logger.info(f"Background processing completed for session {session_id}")
    except Exception as e:
        logger.error(f"Background processing failed: {e}", exc_info=True)


def upload_video_background(session_id: str, file_path: str, mime_type: str):
    """バックグラウンドで動画をGeminiにアップロード（同期ラッパー）"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting background video upload for session {session_id}")
    try:
        asyncio.run(_upload_video_async(session_id, file_path, mime_type))
        logger.info(f"Background video upload completed for session {session_id}")
    except Exception as e:
        logger.error(f"Background video upload failed: {e}", exc_info=True)


async def _upload_video_async(session_id: str, file_path: str, mime_type: str):
    """動画をGemini File APIにアップロード"""
    import logging
    logger = logging.getLogger(__name__)

    from services.session import get_session

    session = get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return

    try:
        session.upload_status = "uploading"
        session.update()

        # ログコールバック関数
        def log_callback(msg):
            import time
            timestamp = time.strftime("%H:%M:%S")
            log_entry = {"timestamp": timestamp, "message": msg}
            session.processing_logs.append(log_entry)
            logger.info(f"[Frontend Log] {msg}")

        logger.info("Uploading full video to Gemini...")
        session.gemini_file = await upload_video_to_gemini(file_path, mime_type, log_callback=log_callback)
        logger.info(f"Full video uploaded. Gemini file name: {session.gemini_file.name}")

        session.upload_status = "completed"
        session.update()

    except Exception as e:
        logger.error(f"Video upload error: {e}", exc_info=True)
        session.upload_status = "failed"
        session.upload_error = str(e)
        session.update()


async def _process_video_async(session_id: str, file_path: str, mime_type: str):
    """動画処理の非同期実装"""
    import logging
    logger = logging.getLogger(__name__)

    from services.session import get_session

    session = get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return

    try:
        # 1. PROCESSING開始
        session.phase = ProcessingPhase.PROCESSING
        session.processing_step = "準備中"
        session.processing_progress = 0
        session.update()

        # 2. 音声ベースのスコーピング実行 (GPT-4o + Gemini)
        session.processing_step = "動画を解析中（冒頭シーンを確認）"
        session.processing_progress = 20
        session.update()

        user_context = ""
        if session.business_title:
            user_context += f"- 業務名: {session.business_title}\n"
        if session.author_name:
            user_context += f"- 担当者: {session.author_name}\n"
        if session.additional_notes:
            user_context += f"- 補足: {session.additional_notes}\n"

        logger.info(f"User context: {user_context if user_context else '(empty)'}")
        logger.info("Starting audio scoping analysis...")

        # 音声抽出 -> 文字起こし -> スコーピング (高速処理)
        def log_callback(msg):
            import time
            timestamp = time.strftime("%H:%M:%S")
            log_entry = {"timestamp": timestamp, "message": msg}
            session.processing_logs.append(log_entry)
            logger.info(f"[Frontend Log] {msg}")

        scoping_result = await analyze_audio_scoping_from_video(file_path, user_context, log_callback=log_callback)
        logger.info(f"Scoping result (first 200 chars): {scoping_result[:200] if scoping_result else '(empty)'}")

        session.scoping_result = scoping_result
        session.user_policy = scoping_result  # デフォルトで同じ

        # スコーピング完了後の進捗表示

        session.processing_step = "動画を解析中（業務フローを把握）"
        session.processing_progress = 60
        session.update()

        await asyncio.sleep(1)
        session.processing_step = "動画を解析中（重要ポイントを抽出）"
        session.processing_progress = 65
        session.update()

        await asyncio.sleep(1)
        session.processing_progress = 70
        session.update()

        # 5. 完了（動画アップロードはバックグラウンドで実行）
        session.processing_step = "解析完了"
        session.processing_progress = 100
        session.phase = ProcessingPhase.QUESTIONING
        session.update()
        logger.info("Processing complete, phase set to QUESTIONING")

        # 6. バックグラウンドで動画をアップロード
        logger.info("Starting background video upload...")
        asyncio.create_task(_upload_video_async(session_id, file_path, mime_type))
        logger.info("Background video upload task created")

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        session.phase = ProcessingPhase.ERROR
        session.processing_step = f"エラー: {str(e)}"
        session.update()


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    business_title: str = Form(""),
    author_name: str = Form(""),
    additional_notes: str = Form(""),
):
    """ファイルをアップロードして処理を開始"""

    # ファイルサイズチェック
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"ファイルが大きすぎます（{file_size / (1024*1024*1024):.1f}GB）。2GB以下にしてください。"
        )

    # セッション取得または作成
    session = get_or_create_session(session_id)
    session.filename = file.filename
    session.business_title = business_title
    session.author_name = author_name
    session.additional_notes = additional_notes
    session.phase = ProcessingPhase.UPLOADING
    session.update()

    # 一時ファイルに保存
    file_path = TEMP_DIR / f"{session_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    session.file_path = str(file_path)

    # 動画の場合はバックグラウンド処理を開始
    if file.content_type and file.content_type.startswith("video/"):
        background_tasks.add_task(
            process_video_background,
            session_id,
            str(file_path),
            file.content_type
        )
        return JSONResponse({
            "status": "processing",
            "message": "動画の処理を開始しました",
            "session_id": session_id,
        })
    else:
        # 動画以外は直接完了
        session.phase = ProcessingPhase.COMPLETE
        session.update()
        return JSONResponse({
            "status": "complete",
            "message": "ファイルをアップロードしました",
            "session_id": session_id,
        })


@router.get("/status/{session_id}")
async def get_status(session_id: str):
    """処理状況を取得"""
    from services.session import get_session

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    return JSONResponse({
        "phase": session.phase.value,
        "filename": session.filename,
        "scoping_result": session.scoping_result,
        "user_policy": session.user_policy,
        "processing_logs": session.processing_logs,
    })
