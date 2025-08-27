"""
アプリケーション設定管理
環境変数とコンフィグレーション
"""

from typing import List, Optional, Union
from pydantic import BaseSettings, PostgresDsn, validator, Field
import secrets


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # API設定
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8日
    
    # CORS設定
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # プロジェクト設定
    PROJECT_NAME: str = "AI Media Assistant"
    SENTRY_DSN: Optional[str] = None
    
    # データベース設定
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "ai_media_assistant"
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis設定
    REDIS_URL: str = "redis://localhost:6379"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # AI/ML設定
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    
    # Google Cloud設定
    GCP_PROJECT_ID: Optional[str] = None
    GCP_BUCKET_NAME: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # ファイル処理設定
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    SUPPORTED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]
    SUPPORTED_VIDEO_FORMATS: List[str] = ["mp4", "avi", "mov", "wmv", "flv", "webm"]
    SUPPORTED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "flac", "ogg", "m4a"]
    
    # Whisper設定
    WHISPER_MODEL: str = "base"
    
    # OCR設定
    TESSERACT_CMD: Optional[str] = None
    
    # LLM設定
    DEFAULT_LLM_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.1
    
    # RAG設定
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DB_COLLECTION: str = "media_embeddings"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # RSS/スクレイピング設定
    USER_AGENT: str = "AI-Media-Assistant/1.0"
    SCRAPING_DELAY: float = 1.0
    MAX_CONCURRENT_REQUESTS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
