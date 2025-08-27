# Python 3.9 ベースイメージ
FROM python:3.9-slim

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# Pythonの依存関係をコピー・インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# アップロードディレクトリ作成
RUN mkdir -p uploads/image uploads/video uploads/audio

# ユーザー作成（セキュリティ向上）
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーション起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
