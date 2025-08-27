# AI Media Assistant - AIメディア処理アシスタント 🤖

## プロジェクト概要

妹がメディアファイルの整理で困ってたので、趣味でAI駆動のメディア処理アシスタントを作ってあげました。
最新のAI技術（LLM、マルチモーダル処理）を使って、画像・動画・音声の自動処理や分析ができるWebアプリケーションです。

**※妹用に趣味で作った個人プロジェクトです**

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

## 使用した技術スタック 📚

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

## 作ってて面白かったポイント 🎓

- **マルチモーダルAI処理** - 妹の写真や動画から自動でテキスト抽出できるのが便利
- **ベクトルデータベース** - 「あの猫の写真どこだっけ？」みたいな曖昧検索ができる
- **大規模言語モデル統合** - ChatGPTとClaudeを使い分けて最適な回答生成
- **モダンReactパターン** - Next.js 14でサクサク動くUIが作れた
- **非同期Python開発** - FastAPIで高速なAI処理APIが簡単に
- **コンテナ化** - Dockerでどこでも同じ環境で動かせる
- **クラウドデプロイ** - GCPで本格的なサービスっぽく仕上がった
- **AI処理パイプライン** - 複数のAIを連携させるのが楽しかった

## 今後やりたいこと 💡

- [ ] より多くのファイル形式に対応（妹がよく使うRAW画像とか）
- [ ] 音楽ファイルの自動タグ付け機能
- [ ] モバイルアプリ版（外出先でも使えるように）
- [ ] もっとAIモデルを試してみる
- [ ] UIをもっと可愛くする
- [ ] 処理速度の改善

## 使ってみたい人へ 🤝

妹用に作ったものですが、同じような用途で使いたい人がいたら：
- バグ報告や改善提案は歓迎
- 機能追加のPull Requestも嬉しい
- 自分なりの改良版を作ってシェアしてくれても面白そう

## ライセンス 📄

MIT License - 趣味で作ったものなので自由に使ってください！

## 参考・感謝 🙏

このプロジェクトは以下の素晴らしいオープンソースプロジェクトの上に成り立っています：
- OpenAIとAnthropic - AIを身近にしてくれて
- Next.jsとFastAPIチーム - 優秀なフレームワークに感謝
- オープンソースコミュニティの皆様

---

**妹が喜んでくれて良かった！** 🚀