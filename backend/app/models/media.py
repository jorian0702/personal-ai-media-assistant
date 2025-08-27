"""
メディア関連データモデル
画像・動画・音声ファイルの管理
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, UUIDMixin
from enum import Enum
from typing import Optional, Dict, Any


class MediaType(str, Enum):
    """メディアタイプ"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class ProcessingStatus(str, Enum):
    """処理ステータス"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaFile(BaseModel, UUIDMixin):
    """メディアファイルモデル"""
    
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    media_type = Column(String(20), nullable=False)
    
    # メタデータ
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # 秒
    fps = Column(Float, nullable=True)
    
    # 処理状況
    processing_status = Column(String(20), default=ProcessingStatus.PENDING)
    processing_error = Column(Text, nullable=True)
    
    # 抽出されたコンテンツ
    extracted_text = Column(Text, nullable=True)  # OCR/音声認識結果
    metadata = Column(JSON, nullable=True)
    
    # 関連付け
    processing_results = relationship("ProcessingResult", back_populates="media_file")


class ProcessingResult(BaseModel, UUIDMixin):
    """処理結果モデル"""
    
    media_file_id = Column(Integer, ForeignKey("mediafile.id"), nullable=False)
    processor_type = Column(String(50), nullable=False)  # ocr, whisper, sentiment, etc.
    
    # 結果データ
    result_data = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)  # 秒
    
    # エラー情報
    error_message = Column(Text, nullable=True)
    
    # 関連付け
    media_file = relationship("MediaFile", back_populates="processing_results")


class ContentAnalysis(BaseModel, UUIDMixin):
    """コンテンツ分析結果"""
    
    media_file_id = Column(Integer, ForeignKey("mediafile.id"), nullable=False)
    
    # テキスト分析
    sentiment_score = Column(Float, nullable=True)
    emotion_scores = Column(JSON, nullable=True)  # 感情スコア辞書
    keywords = Column(JSON, nullable=True)  # キーワードリスト
    entities = Column(JSON, nullable=True)  # 固有表現
    topics = Column(JSON, nullable=True)  # トピック分類
    
    # 画像分析
    objects_detected = Column(JSON, nullable=True)  # 物体検出結果
    scene_description = Column(Text, nullable=True)
    
    # 音声分析
    speaker_count = Column(Integer, nullable=True)
    language_detected = Column(String(10), nullable=True)
    
    # LLM生成コンテンツ
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
    suggested_tags = Column(JSON, nullable=True)
    
    media_file = relationship("MediaFile")


class EmbeddingVector(BaseModel, UUIDMixin):
    """ベクトル埋め込み"""
    
    media_file_id = Column(Integer, ForeignKey("mediafile.id"), nullable=False)
    content_text = Column(Text, nullable=False)  # 埋め込み対象テキスト
    model_name = Column(String(100), nullable=False)  # 使用モデル
    vector_data = Column(JSON, nullable=False)  # ベクトルデータ
    chunk_index = Column(Integer, default=0)  # チャンクインデックス
    
    media_file = relationship("MediaFile")
