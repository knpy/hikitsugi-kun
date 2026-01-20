"""
質問・回答のSSEストリーミング関連ルート
"""
import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel

from services.session import get_session, ProcessingPhase
from services.gemini import analyze_video_full, CONVERSATIONAL_QUESTIONS

router = APIRouter()


class AnswerRequest(BaseModel):
    """回答リクエスト"""
    session_id: str
    question_id: str
    answer: str


class PolicyUpdateRequest(BaseModel):
    """方針更新リクエスト"""
    session_id: str
    policy: str


@router.get("/events/{session_id}")
async def event_stream(session_id: str, request: Request):
    """SSEでリアルタイムイベントを配信"""

    async def generate():
        last_phase = None
        last_scoping = ""
        last_progress = -1

        while True:
            # クライアント切断チェック
            if await request.is_disconnected():
                break

            session = get_session(session_id)
            if not session:
                yield f"event: error\ndata: {json.dumps({'message': 'セッションが見つかりません'})}\n\n"
                break

            # フェーズが変わったら通知
            if session.phase != last_phase:
                last_phase = session.phase
                yield f"event: phase\ndata: {json.dumps({'phase': session.phase.value})}\n\n"

            # 進捗通知
            if session.processing_progress != last_progress:
                last_progress = session.processing_progress
                yield f"event: progress\ndata: {json.dumps({'step': session.processing_step, 'progress': session.processing_progress})}\n\n"

            # スコーピング結果が出たら通知
            if session.scoping_result and session.scoping_result != last_scoping:
                last_scoping = session.scoping_result
                yield f"event: scoping\ndata: {json.dumps({'result': session.scoping_result})}\n\n"

            # 完了またはエラーで終了
            if session.phase in [ProcessingPhase.COMPLETE, ProcessingPhase.ERROR]:
                yield f"event: done\ndata: {json.dumps({'phase': session.phase.value})}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/answer")
async def submit_answer(request: AnswerRequest):
    """質問への回答を送信"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    # 回答を方針に反映
    if request.answer:
        session.user_policy += f"\n- {request.answer}"
        session.update()

    return {"status": "ok"}


@router.post("/policy")
async def update_policy(request: PolicyUpdateRequest):
    """解析方針を更新"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    session.user_policy = request.policy
    session.update()

    return {"status": "ok", "policy": session.user_policy}


@router.post("/analyze/{session_id}")
async def start_analysis(session_id: str):
    """詳細解析を開始"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")

    if not session.gemini_file:
        raise HTTPException(status_code=400, detail="動画がアップロードされていません")

    try:
        session.phase = ProcessingPhase.ANALYZING
        session.update()

        # 詳細解析を実行
        result = await analyze_video_full(session.gemini_file, session.user_policy)
        session.video_analysis = result
        session.phase = ProcessingPhase.COMPLETE
        session.update()

        return {"status": "complete", "analysis": result}

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

    return {
        "phase": session.phase.value,
        "scoping_result": session.scoping_result,
        "user_policy": session.user_policy,
        "video_analysis": session.video_analysis,
    }


@router.get("/questions")
async def get_questions():
    """利用可能な質問リストを取得"""
    return {"questions": CONVERSATIONAL_QUESTIONS}
