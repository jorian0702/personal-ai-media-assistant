"""
データベースモデル基底クラス
共通カラムとヘルパーメソッド
"""

from sqlalchemy import Column, Integer, DateTime, String, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base
from typing import Any
import uuid


class TimestampMixin:
    """タイムスタンプミックスイン"""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """基底モデルクラス"""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UUIDMixin:
    """UUIDミックスイン"""
    
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
