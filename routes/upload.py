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
from services.gemini import upload_video_to_gemini, analyze_video_scoping
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
        session.phase = ProcessingPhase.PROCESSING
        session.update()

        # 1. 冒頭5分をクリップ（スコーピング用）
        clip_path = file_path + "_clip.mp4"
        logger.info(f"Creating clip: {clip_path}")
        clip_video_head(file_path, clip_path, duration=300)

        if os.path.exists(clip_path):
            logger.info(f"Clip created successfully. Size: {os.path.getsize(clip_path)} bytes")
        else:
            logger.error(f"Clip file not created!")

        # 2. クリップをGeminiにアップロード
        logger.info("Uploading clip to Gemini...")
        clip_file = await upload_video_to_gemini(clip_path, mime_type)
        logger.info(f"Clip uploaded. Gemini file name: {clip_file.name}")

        # 3. 初期分析（スコーピング）
        session.phase = ProcessingPhase.QUESTIONING
        session.update()

        user_context = ""
        if session.business_title:
            user_context += f"- 業務名: {session.business_title}\n"
        if session.author_name:
            user_context += f"- 担当者: {session.author_name}\n"
        if session.additional_notes:
            user_context += f"- 補足: {session.additional_notes}\n"

        logger.info(f"User context: {user_context if user_context else '(empty)'}")
        logger.info("Starting scoping analysis...")

        scoping_result = await analyze_video_scoping(clip_file, user_context)
        logger.info(f"Scoping result (first 200 chars): {scoping_result[:200] if scoping_result else '(empty)'}")

        session.scoping_result = scoping_result
        session.user_policy = scoping_result  # デフォルトで同じ

        # 4. 全編動画をアップロード（詳細解析用）
        logger.info("Uploading full video to Gemini...")
        session.gemini_file = await upload_video_to_gemini(file_path, mime_type)
        logger.info(f"Full video uploaded. Gemini file name: {session.gemini_file.name}")

        # クリップファイルを削除
        if os.path.exists(clip_path):
            os.unlink(clip_path)
            logger.info("Clip file deleted")

        session.phase = ProcessingPhase.QUESTIONING
        session.update()
        logger.info("Processing complete, phase set to QUESTIONING")

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        session.phase = ProcessingPhase.ERROR
        session.scoping_result = f"エラーが発生しました: {str(e)}"
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
    })
