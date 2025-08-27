"""
API v1 ルーター統合
全エンドポイントの統合管理
"""

from fastapi import APIRouter
from app.api.api_v1.endpoints import media, content, llm, analytics

api_router = APIRouter()

# メディア処理エンドポイント
api_router.include_router(
    media.router,
    prefix="/media",
    tags=["media"]
)

# コンテンツ管理エンドポイント
api_router.include_router(
    content.router,
    prefix="/content",
    tags=["content"]
)

# LLM・AI機能エンドポイント
api_router.include_router(
    llm.router,
    prefix="/llm",
    tags=["llm"]
)

# 分析・ダッシュボードエンドポイント
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)
