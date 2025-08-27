"""
コンテンツ関連データモデル
RSS、SNS、生成コンテンツ等
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, UUIDMixin
from enum import Enum
from typing import Optional, Dict, Any


class ContentSource(str, Enum):
    """コンテンツソース"""
    RSS = "rss"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    NEWS_API = "news_api"
    MANUAL = "manual"
    GENERATED = "generated"


class ContentStatus(str, Enum):
    """コンテンツステータス"""
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RSSFeed(BaseModel, UUIDMixin):
    """RSSフィード管理"""
    
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # フィード情報
    last_fetched = Column(DateTime, nullable=True)
    fetch_interval = Column(Integer, default=3600)  # 秒
    is_active = Column(Boolean, default=True)
    
    # 統計
    total_articles = Column(Integer, default=0)
    last_article_date = Column(DateTime, nullable=True)
    
    # 設定
    category_tags = Column(JSON, nullable=True)
    priority_score = Column(Float, default=1.0)
    
    # 関連付け
    articles = relationship("Article", back_populates="rss_feed")


class Article(BaseModel, UUIDMixin):
    """記事データ"""
    
    rss_feed_id = Column(Integer, ForeignKey("rssfeed.id"), nullable=True)
    
    # 基本情報
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    published_date = Column(DateTime, nullable=True)
    
    # メタデータ
    source = Column(String(20), default=ContentSource.RSS)
    language = Column(String(10), nullable=True)
    tags = Column(JSON, nullable=True)
    category = Column(String(100), nullable=True)
    
    # 分析結果
    sentiment_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    importance_score = Column(Float, nullable=True)
    
    # 処理状況
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # 関連付け
    rss_feed = relationship("RSSFeed", back_populates="articles")


class GeneratedContent(BaseModel, UUIDMixin):
    """AI生成コンテンツ"""
    
    # 基本情報
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # article, summary, script, etc.
    
    # 生成パラメータ
    prompt = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # 品質指標
    quality_score = Column(Float, nullable=True)
    coherence_score = Column(Float, nullable=True)
    originality_score = Column(Float, nullable=True)
    
    # ステータス
    status = Column(String(20), default=ContentStatus.DRAFT)
    is_human_reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text, nullable=True)
    
    # メタデータ
    target_audience = Column(String(100), nullable=True)
    tone = Column(String(50), nullable=True)
    keywords = Column(JSON, nullable=True)
    
    # 使用素材
    source_media_ids = Column(JSON, nullable=True)  # 参照メディアファイルID
    source_articles = Column(JSON, nullable=True)  # 参照記事ID


class ContentTemplate(BaseModel, UUIDMixin):
    """コンテンツテンプレート"""
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    
    # テンプレート定義
    template_structure = Column(JSON, nullable=False)  # セクション構造
    default_prompts = Column(JSON, nullable=False)  # デフォルトプロンプト
    
    # 設定
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    
    # メタデータ
    target_length = Column(Integer, nullable=True)  # 文字数目安
    suggested_tone = Column(String(50), nullable=True)
    required_fields = Column(JSON, nullable=True)


class WorkflowExecution(BaseModel, UUIDMixin):
    """ワークフロー実行履歴"""
    
    workflow_name = Column(String(200), nullable=False)
    input_data = Column(JSON, nullable=False)
    
    # 実行状況
    status = Column(String(20), nullable=False)
    current_step = Column(String(100), nullable=True)
    progress_percentage = Column(Integer, default=0)
    
    # 結果
    output_data = Column(JSON, nullable=True)
    execution_time = Column(Float, nullable=True)  # 秒
    error_log = Column(Text, nullable=True)
    
    # 統計
    steps_completed = Column(Integer, default=0)
    steps_total = Column(Integer, nullable=True)
