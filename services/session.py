"""
セッション管理サービス
"""
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ProcessingPhase(str, Enum):
    """処理フェーズ"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    QUESTIONING = "questioning"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class SessionData:
    """セッションデータ"""
    session_id: str
    phase: ProcessingPhase = ProcessingPhase.UPLOADING
    filename: Optional[str] = None
    file_path: Optional[str] = None
    gemini_file: Optional[object] = None

    # ユーザー入力
    business_title: str = ""
    author_name: str = ""
    additional_notes: str = ""

    # AI生成結果
    scoping_result: str = ""
    user_policy: str = ""
    video_analysis: str = ""
    generated_document: str = ""

    # フレーム抽出結果
    extracted_frames: list = field(default_factory=list)

    # メタデータ
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # 質問キュー（SSE用）
    questions: list = field(default_factory=list)
    current_question_index: int = 0

    # Phase1進捗情報
    processing_step: str = ""  # "クリップ作成中", "解析中"など
    processing_progress: int = 0  # 0-100

    def update(self):
        """更新日時を更新"""
        self.updated_at = time.time()


# インメモリセッションストア（本番ではRedis等に置き換え）
_sessions: dict[str, SessionData] = {}

# セッションの有効期限（24時間）
SESSION_TTL = 24 * 60 * 60


def get_session(session_id: str) -> Optional[SessionData]:
    """セッションを取得"""
    return _sessions.get(session_id)


def create_session(session_id: str) -> SessionData:
    """新しいセッションを作成"""
    session = SessionData(session_id=session_id)
    _sessions[session_id] = session
    return session


def get_or_create_session(session_id: str) -> SessionData:
    """セッションを取得、なければ作成"""
    session = get_session(session_id)
    if session is None:
        session = create_session(session_id)
    return session


def delete_session(session_id: str) -> bool:
    """セッションを削除"""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def cleanup_old_sessions():
    """古いセッションをクリーンアップ"""
    now = time.time()
    expired = [
        sid for sid, session in _sessions.items()
        if now - session.updated_at > SESSION_TTL
    ]
    for sid in expired:
        delete_session(sid)
    return len(expired)
