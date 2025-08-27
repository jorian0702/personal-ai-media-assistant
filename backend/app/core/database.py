"""
データベース接続とセッション管理
PostgreSQL + SQLAlchemy async
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 非同期エンジン作成
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=True,  # 開発時のSQL出力
    pool_pre_ping=True,
    pool_recycle=300,
)

# セッションファクトリー
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ベースクラス
Base = declarative_base()


async def get_db() -> AsyncSession:
    """データベースセッション取得"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
