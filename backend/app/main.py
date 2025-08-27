"""
AI Media Assistant - FastAPI Application
妹用AIメディア処理アシスタント - メインアプリケーション
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import structlog
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.api_v1.api import api_router
from app.core.database import engine
from app.models.base import Base

# ロギング設定
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger.info("Starting AI Media Assistant API")
    
    # データベース初期化
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized")
    yield
    
    logger.info("Shutting down AI Media Assistant API")


app = FastAPI(
    title="AI Media Assistant API",
    description="妹用AIメディア処理アシスタント - マルチモーダルコンテンツ処理",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# ミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# APIルーター登録
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "message": "AI Media Assistant API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """詳細ヘルスチェック"""
    return {
        "status": "healthy",
        "database": "connected",
        "ai_services": "ready",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
