"""
ドキュメント生成関連のルート
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.session import get_session, ProcessingPhase
from services.gemini import generate_document
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
