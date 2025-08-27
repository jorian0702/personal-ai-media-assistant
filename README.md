# AI Media Assistant - AIメディア処理アシスタント 🤖

## プロジェクト概要

個人的な学習プロジェクトとして作成したAI駆動のメディア処理アシスタントです。
最新のAI技術（LLM、マルチモーダル処理）を使って、画像・動画・音声の自動処理や分析ができるWebアプリケーションを作ってみました。

**※これは個人の趣味・学習目的で作成したプロジェクトです**

## 実装した機能 🛠️

### 🎬 メディア処理機能
- **画像解析** - OCR技術で文字抽出（Tesseract、EasyOCR）
- **動画処理** - OpenCVとffmpegを使った動画解析
- **音声文字起こし** - Whisperを使った音声→テキスト変換
- **コンテンツ抽出** - メディアファイルからの情報抽出

### 🧠 AI統合機能
- **大規模言語モデル** - OpenAI GPTやClaudeとの連携
- **RAG（検索拡張生成）** - ベクトル検索を使ったコンテンツ生成
- **テキスト要約** - 長文の自動要約機能
- **テキストマイニング** - RSSフィードやWebデータの収集・分析

### 🎨 モダンなWebアプリ
- **インタラクティブUI** - ドラッグ&ドロップでファイルアップロード
- **リアルタイム処理** - 進捗状況のライブ表示
- **AIチャット機能** - コンテンツとの対話型インターフェース
- **分析ダッシュボード** - 美しいグラフとチャート

## 学習した技術スタック 📚

### フロントエンド
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** コンポーネント
- **Framer Motion** - スムーズなアニメーション
- **React Query** - 状態管理

### バックエンド  
- **Python FastAPI** - 高性能API開発
- **PostgreSQL** + **Redis** - データストレージ
- **Celery** - バックグラウンドタスク処理
- **SQLAlchemy** - 非同期ORM

### AI/ML パイプライン
- **OpenAI GPT-4** と **Claude-3** の統合
- **Whisper** - 音声認識
- **OpenCV** + **ffmpeg** - メディア処理
- **ChromaDB** - ベクトルストレージと類似検索
- **LangChain** - RAG実装

### インフラ・デプロイ
- **Docker** + **Docker Compose** - コンテナ化
- **Google Cloud Platform** (Cloud Run, Cloud Functions)
- **GitHub Actions** - CI/CD自動化
- **Prometheus** + **Grafana** - 監視・ログ

## 主要機能 🌟

### 📁 スマートメディア処理
- 画像、動画、音声ファイルのアップロード
- OCRや音声認識を使った自動コンテンツ抽出
- 知的なタグ付けとメタデータ生成
- リアルタイム処理とプログレス表示

### 🔍 AI検索機能
- ベクトルベースのセマンティック検索
- 「この内容について教えて」で自然言語検索
- コンテキストを理解した検索結果
- 関連度スコア付きの結果表示

### ✍️ コンテンツ生成
- AI駆動の記事作成と要約
- コンテンツ改善提案
- 多言語対応
- カスタムトーンとスタイル調整

### 📊 分析ダッシュボード
- リアルタイム処理統計
- コンテンツ分析トレンド
- パフォーマンス監視
- 美しいデータ可視化

## セットアップ方法 🚀

### 必要な環境
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose

### インストール手順
```bash
# リポジトリをクローン
git clone <your-repo-url>
cd ai_media_assistant

# 環境変数をコピー
cp env.example .env
# .env ファイルにAPIキーなどを設定

# Dockerで起動
docker-compose up -d

# または個別に起動
cd frontend && npm install && npm run dev
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

### 環境変数の設定
```bash
# AI APIキー（各プロバイダーから取得）
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key

# データベース
DATABASE_URL=postgresql://user:pass@localhost:5432/aidb
REDIS_URL=redis://localhost:6379

# オプション: GCP（ファイルストレージ用）
GCP_PROJECT_ID=your_project
```

## スクリーンショット 📸

### メインダッシュボード
![Dashboard](docs/screenshots/dashboard.png)

### メディアアップロード
![Upload](docs/screenshots/upload.png)

### AIチャット機能  
![Chat](docs/screenshots/chat.png)

## このプロジェクトで学んだこと 🎓

- **マルチモーダルAI処理** - テキスト、画像、音声を組み合わせたAI活用
- **ベクトルデータベース** とセマンティック検索の実装
- **大規模言語モデル統合** とプロンプトエンジニアリング
- **モダンReactパターン** - Next.js 14の最新機能活用
- **非同期Python開発** - FastAPIでの高性能API構築
- **コンテナオーケストレーション** - Dockerを使った開発環境構築
- **クラウドデプロイ** - GCPでの本格運用
- **AI/MLパイプライン設計** と最適化

## 今後の改善アイデア 💡

- [ ] より多くのファイル形式に対応
- [ ] リアルタイムコラボレーション機能
- [ ] モバイルアプリ版の開発
- [ ] 追加のAIモデル・プロバイダー対応
- [ ] プラグインシステムで拡張性向上
- [ ] 高度な分析・レポート機能

## 貢献・フィードバック 🤝

個人学習プロジェクトですが、以下は大歓迎です：
- バグや改善提案のIssue作成
- 機能改善のPull Request
- 実験結果や改良版の共有

## ライセンス 📄

MIT License - 学習目的でのコード利用は自由です！

## 参考・感謝 🙏

このプロジェクトは以下の素晴らしいオープンソースプロジェクトの上に成り立っています：
- OpenAIとAnthropic - AIを身近にしてくれて
- Next.jsとFastAPIチーム - 優秀なフレームワークに感謝
- オープンソースコミュニティの皆様

---

**楽しくコーディング！** 🚀