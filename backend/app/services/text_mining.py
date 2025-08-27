"""
テキストマイニング・データ収集サービス
RSS、SNS、ニュースAPI等からのデータ収集と分析
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import spacy
import nltk
from collections import Counter
import numpy as np
import structlog

from app.core.config import settings
from app.models.content import RSSFeed, Article
from app.services.llm_service import LLMService


logger = structlog.get_logger(__name__)


class RSSCollector:
    """RSS収集サービス"""
    
    def __init__(self):
        self.session = None
        self.llm_service = LLMService()
        
        # spaCyモデル初期化
        try:
            self.nlp = spacy.load("ja_core_news_sm")
        except OSError:
            logger.warning("Japanese spaCy model not found, using English model")
            self.nlp = spacy.load("en_core_web_sm")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_rss_feed(self, feed_url: str) -> Dict[str, Any]:
        """RSS フィード取得"""
        try:
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if feed.bozo:
                    logger.warning("RSS feed has parsing errors", url=feed_url, error=feed.bozo_exception)
                
                return {
                    "title": feed.feed.get("title", ""),
                    "description": feed.feed.get("description", ""),
                    "link": feed.feed.get("link", ""),
                    "last_updated": feed.feed.get("updated", ""),
                    "entries": feed.entries,
                    "total_entries": len(feed.entries)
                }
                
        except Exception as e:
            logger.error("RSS feed fetch failed", url=feed_url, error=str(e))
            raise
    
    async def collect_articles_from_feed(self, rss_feed: RSSFeed) -> List[Dict[str, Any]]:
        """RSS フィードから記事収集"""
        articles = []
        
        try:
            feed_data = await self.fetch_rss_feed(rss_feed.url)
            
            for entry in feed_data["entries"]:
                # 記事データ抽出
                article_data = await self._extract_article_data(entry)
                
                # コンテンツ取得（フルテキスト）
                if article_data["url"]:
                    full_content = await self._fetch_article_content(article_data["url"])
                    article_data["content"] = full_content
                
                # テキスト分析
                if article_data["content"]:
                    analysis = await self._analyze_article_text(article_data["content"])
                    article_data.update(analysis)
                
                articles.append(article_data)
                
                # レート制限
                await asyncio.sleep(settings.SCRAPING_DELAY)
            
            logger.info("Articles collected from RSS feed", 
                       feed_id=rss_feed.id, count=len(articles))
            
        except Exception as e:
            logger.error("Article collection failed", 
                        feed_id=rss_feed.id, error=str(e))
        
        return articles
    
    async def _extract_article_data(self, entry) -> Dict[str, Any]:
        """RSS エントリから記事データ抽出"""
        # 公開日時パース
        published_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_date = datetime(*entry.updated_parsed[:6])
        
        return {
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "content": entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
            "author": entry.get("author", ""),
            "published_date": published_date,
            "tags": [tag.term for tag in entry.get("tags", [])],
            "guid": entry.get("guid", "")
        }
    
    async def _fetch_article_content(self, url: str) -> str:
        """記事のフルコンテンツ取得"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return ""
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # メインコンテンツ抽出（複数パターン試行）
                content_selectors = [
                    'article',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    'main',
                    '#main-content',
                    '.content'
                ]
                
                content = ""
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = elements[0].get_text(strip=True)
                        break
                
                # フォールバック：bodyから抽出
                if not content:
                    body = soup.find('body')
                    if body:
                        content = body.get_text(strip=True)
                
                # 不要な改行・空白除去
                content = re.sub(r'\s+', ' ', content)
                
                return content
                
        except Exception as e:
            logger.warning("Article content fetch failed", url=url, error=str(e))
            return ""
    
    async def _analyze_article_text(self, text: str) -> Dict[str, Any]:
        """記事テキスト分析"""
        analysis = {}
        
        if not text.strip():
            return analysis
        
        try:
            # 基本統計
            analysis["stats"] = {
                "character_count": len(text),
                "word_count": len(text.split()),
                "sentence_count": len([s for s in text.split('.') if s.strip()])
            }
            
            # spaCy解析
            doc = self.nlp(text[:1000000])  # メモリ制限
            
            # 固有表現抽出
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            analysis["entities"] = entities
            
            # キーワード抽出（名詞のみ）
            keywords = [token.text for token in doc 
                       if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2]
            keyword_freq = Counter(keywords).most_common(10)
            analysis["keywords"] = keyword_freq
            
            # 感情分析（LLM使用）
            sentiment_result = await self.llm_service.generate_completion(
                prompt=f"以下のテキストの感情を分析し、ポジティブ・ネガティブ・ニュートラルのいずれかで判定してください:\n\n{text[:1000]}",
                max_tokens=50,
                temperature=0.1
            )
            analysis["sentiment"] = sentiment_result.get("text", "").strip()
            
            # トピック分類（簡易版）
            topics = await self._classify_topic(text)
            analysis["topics"] = topics
            
        except Exception as e:
            logger.error("Text analysis failed", error=str(e))
            analysis["error"] = str(e)
        
        return analysis
    
    async def _classify_topic(self, text: str) -> List[str]:
        """トピック分類"""
        # 簡易的なキーワードベース分類
        topic_keywords = {
            "technology": ["AI", "人工知能", "テクノロジー", "IT", "システム", "ソフトウェア"],
            "business": ["ビジネス", "企業", "経済", "市場", "投資", "売上"],
            "politics": ["政治", "政府", "選挙", "政策", "国会", "大臣"],
            "sports": ["スポーツ", "試合", "選手", "チーム", "リーグ", "オリンピック"],
            "entertainment": ["エンターテイメント", "映画", "音楽", "ゲーム", "アニメ"],
            "health": ["健康", "医療", "病気", "治療", "薬", "病院"],
            "science": ["科学", "研究", "実験", "発見", "技術", "理論"]
        }
        
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword.lower() in text_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics


class NewsAPICollector:
    """ニュースAPI収集サービス"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = None
        self.base_url = "https://newsapi.org/v2"
    
    async def __aenter__(self):
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_articles(
        self,
        query: str,
        language: str = "ja",
        sort_by: str = "publishedAt",
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """記事検索"""
        if not self.api_key:
            logger.warning("NewsAPI key not configured")
            return []
        
        try:
            params = {
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size
            }
            
            async with self.session.get(f"{self.base_url}/everything", params=params) as response:
                data = await response.json()
                
                if response.status != 200:
                    logger.error("NewsAPI error", status=response.status, error=data.get("message"))
                    return []
                
                return data.get("articles", [])
                
        except Exception as e:
            logger.error("NewsAPI search failed", query=query, error=str(e))
            return []


class SocialMediaCollector:
    """ソーシャルメディア収集サービス（Twitter API等）"""
    
    def __init__(self):
        # TwitterやYouTube APIの設定
        # 実際の実装では各プラットフォームのAPIキーが必要
        pass
    
    async def collect_tweets(self, hashtag: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Twitter投稿収集"""
        # Twitter API v2を使用した実装
        # ここでは簡易版として空のリストを返す
        logger.info("Twitter collection not implemented yet", hashtag=hashtag)
        return []
    
    async def collect_youtube_comments(self, video_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """YouTube コメント収集"""
        # YouTube Data API v3を使用した実装
        logger.info("YouTube collection not implemented yet", video_id=video_id)
        return []


class TextMiningPipeline:
    """テキストマイニングパイプライン"""
    
    def __init__(self):
        self.rss_collector = None
        self.news_collector = None
        self.social_collector = SocialMediaCollector()
        self.llm_service = LLMService()
    
    async def run_collection_pipeline(self, sources: List[str] = None) -> Dict[str, Any]:
        """データ収集パイプライン実行"""
        results = {
            "rss_articles": [],
            "news_articles": [],
            "social_posts": [],
            "processing_errors": []
        }
        
        # RSS収集
        if not sources or "rss" in sources:
            async with RSSCollector() as rss_collector:
                self.rss_collector = rss_collector
                # ここで実際のRSSフィード収集を実行
                # （データベースからRSSフィードリストを取得して処理）
                pass
        
        # ニュースAPI収集
        if not sources or "news" in sources:
            async with NewsAPICollector() as news_collector:
                self.news_collector = news_collector
                # ニュース検索・収集を実行
                pass
        
        # ソーシャルメディア収集
        if not sources or "social" in sources:
            # ソーシャルメディア収集を実行
            pass
        
        return results
    
    async def analyze_collected_content(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """収集コンテンツの一括分析"""
        analysis_results = {
            "total_items": len(content_items),
            "sentiment_distribution": {},
            "topic_distribution": {},
            "keyword_trends": {},
            "quality_scores": []
        }
        
        for item in content_items:
            # 個別分析結果を集約
            if "sentiment" in item:
                sentiment = item["sentiment"]
                analysis_results["sentiment_distribution"][sentiment] = \
                    analysis_results["sentiment_distribution"].get(sentiment, 0) + 1
            
            if "topics" in item:
                for topic in item["topics"]:
                    analysis_results["topic_distribution"][topic] = \
                        analysis_results["topic_distribution"].get(topic, 0) + 1
        
        return analysis_results
