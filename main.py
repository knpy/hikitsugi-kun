"""
引継ぎくん - FastAPI + htmx版
"""
import socket
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from routes import upload, questions, document
from services.session import cleanup_old_sessions

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: 古いセッションをクリーンアップ
    cleanup_old_sessions()
    yield
    # 終了時: 必要に応じてクリーンアップ


app = FastAPI(
    title="引継ぎくん",
    description="業務引継ぎ支援AI - 動画をアップロードするだけで引継ぎドキュメントを自動生成",
    version="2.0.0",
    lifespan=lifespan,
)

# 静的ファイル
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# テンプレート
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ルーター登録
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(questions.router, prefix="/api", tags=["questions"])
app.include_router(document.router, prefix="/api", tags=["document"])


@app.get("/")
async def index(request: Request):
    """メインページ"""
    session_id = str(uuid.uuid4())
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "session_id": session_id}
    )


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """空いているポートを探す"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"ポート {start_port}-{start_port + max_attempts} が全て使用中です")


if __name__ == "__main__":
    import uvicorn

    port = find_available_port(8000)
    print(f"\n🚀 引継ぎくん を起動中... http://localhost:{port}\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
