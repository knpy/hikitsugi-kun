"""
ドキュメント生成関連のルート
"""
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.session import get_session, ProcessingPhase
from services.gemini import generate_document, analyze_video_full
from frame_extractor import replace_image_placeholders

router = APIRouter()


class DocumentRequest(BaseModel):
    """ドキュメント生成リクエスト"""
    session_id: str


@router.post("/generate-document")
async def generate_doc(request: DocumentRequest):
    """引継ぎドキュメントを生成"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    if not session.video_analysis:
        raise HTTPException(status_code=400, detail="動画解析が完了していません")

    try:
        # ドキュメント生成
        document = await generate_document(
            session.video_analysis,
            session.user_policy
        )

        # 画像プレースホルダーを置換
        if session.extracted_frames:
            document = replace_image_placeholders(document, session.extracted_frames)

        session.generated_document = document
        session.update()

        return JSONResponse({
            "status": "success",
            "document": document,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{session_id}")
async def get_document(session_id: str):
    """生成済みドキュメントを取得"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    return JSONResponse({
        "document": session.generated_document,
        "video_analysis": session.video_analysis,
    })


@router.post("/analyze/{session_id}")
async def analyze_video(session_id: str):
    """動画の詳細解析を開始"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # アップロード状態を確認
    if session.upload_status == "pending":
        raise HTTPException(status_code=400, detail="動画のアップロードがまだ開始されていません")
    elif session.upload_status == "failed":
        raise HTTPException(status_code=500, detail=f"動画のアップロードに失敗しました: {session.upload_error}")

    # アップロードが完了していない場合は待機
    if session.upload_status == "uploading":
        # 最大60秒待機
        max_wait = 60
        waited = 0
        while session.upload_status == "uploading" and waited < max_wait:
            await asyncio.sleep(2)
            waited += 2

        if session.upload_status != "completed":
            raise HTTPException(status_code=408, detail="動画のアップロード完了待機がタイムアウトしました")

    if not session.gemini_file:
        raise HTTPException(status_code=400, detail="動画がアップロードされていません")

    # 詳細解析を開始
    session.phase = ProcessingPhase.ANALYZING
    session.update()

    try:
        # 詳細解析を実行
        video_analysis = await analyze_video_full(session.gemini_file, session.user_policy)
        session.video_analysis = video_analysis
        session.phase = ProcessingPhase.COMPLETE
        session.update()

        return JSONResponse({
            "status": "success",
            "message": "動画の詳細解析が完了しました",
        })

    except Exception as e:
        session.phase = ProcessingPhase.ERROR
        session.update()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{session_id}")
async def get_analysis(session_id: str):
    """解析結果を取得"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    return JSONResponse({
        "video_analysis": session.video_analysis,
        "phase": session.phase.value,
    })
