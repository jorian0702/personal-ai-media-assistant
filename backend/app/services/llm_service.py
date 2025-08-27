"""
LLM統合サービス
OpenAI、Claude、RAG、エンベディング検索
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import openai
import anthropic
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import structlog

from app.core.config import settings


logger = structlog.get_logger(__name__)


class EmbeddingService:
    """エンベディングサービス"""
    
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        
        # ChromaDB初期化
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # コレクション取得または作成
        try:
            self.collection = self.chroma_client.get_collection(settings.VECTOR_DB_COLLECTION)
        except:
            self.collection = self.chroma_client.create_collection(
                name=settings.VECTOR_DB_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
    
    async def create_embeddings(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """テキストからエンベディング作成"""
        if not text.strip():
            return []
        
        # テキスト分割
        chunks = self.text_splitter.split_text(text)
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            # エンベディング生成
            vector = self.model.encode(chunk).tolist()
            
            chunk_metadata = {
                "chunk_index": i,
                "chunk_size": len(chunk),
                "original_length": len(text),
                **(metadata or {})
            }
            
            embeddings.append({
                "text": chunk,
                "vector": vector,
                "metadata": chunk_metadata
            })
        
        return embeddings
    
    async def store_embeddings(self, embeddings: List[Dict[str, Any]], document_id: str):
        """エンベディングをベクトルDBに保存"""
        if not embeddings:
            return
        
        ids = [f"{document_id}_{i}" for i in range(len(embeddings))]
        texts = [emb["text"] for emb in embeddings]
        vectors = [emb["vector"] for emb in embeddings]
        metadatas = [emb["metadata"] for emb in embeddings]
        
        # ChromaDBに保存
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas
        )
        
        logger.info("Embeddings stored", 
                   document_id=document_id, count=len(embeddings))
    
    async def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """類似度検索"""
        # クエリのエンベディング生成
        query_vector = self.model.encode(query).tolist()
        
        # 検索実行
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # 結果整形
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                search_results.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i]  # コサイン距離を類似度に変換
                })
        
        return search_results


class LLMService:
    """LLMサービス"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.anthropic_client = None
        
        self.embedding_service = EmbeddingService()
    
    async def generate_completion(
        self,
        prompt: str,
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        context: List[str] = None
    ) -> Dict[str, Any]:
        """テキスト生成"""
        model = model or settings.DEFAULT_LLM_MODEL
        max_tokens = max_tokens or settings.MAX_TOKENS
        temperature = temperature or settings.TEMPERATURE
        
        # コンテキストがある場合はRAGモード
        if context:
            prompt = self._build_rag_prompt(prompt, context)
        
        try:
            if model.startswith("gpt"):
                return await self._openai_completion(prompt, model, max_tokens, temperature)
            elif model.startswith("claude"):
                return await self._anthropic_completion(prompt, model, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            logger.error("LLM completion failed", error=str(e), model=model)
            return {"error": str(e)}
    
    async def _openai_completion(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """OpenAI API完了"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "text": response.choices[0].message.content,
                "model": model,
                "usage": response.usage.dict() if response.usage else None,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def _anthropic_completion(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Anthropic API完了"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "text": response.content[0].text,
                "model": model,
                "usage": response.usage.dict() if hasattr(response, 'usage') else None
            }
        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise
    
    def _build_rag_prompt(self, query: str, context: List[str]) -> str:
        """RAGプロンプト構築"""
        context_text = "\n\n".join(context)
        
        prompt_template = """以下のコンテキスト情報を使用して、質問に答えてください。
コンテキストに情報がない場合は、「提供された情報では答えられません」と回答してください。

コンテキスト:
{context}

質問: {query}

回答:"""
        
        return prompt_template.format(context=context_text, query=query)
    
    async def rag_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """RAG検索と回答生成"""
        try:
            # 類似度検索
            search_results = await self.embedding_service.similarity_search(query, top_k)
            
            if not search_results:
                return {
                    "answer": "関連する情報が見つかりませんでした。",
                    "sources": [],
                    "confidence": 0.0
                }
            
            # コンテキスト構築
            context = [result["text"] for result in search_results]
            
            # LLM生成
            completion = await self.generate_completion(
                prompt=query,
                context=context
            )
            
            return {
                "answer": completion.get("text", ""),
                "sources": search_results,
                "confidence": min([r["similarity"] for r in search_results]),
                "model_info": completion
            }
            
        except Exception as e:
            logger.error("RAG query failed", error=str(e))
            return {"error": str(e)}


class ContentGenerationService:
    """コンテンツ生成サービス"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_article_summary(
        self,
        content: str,
        max_length: int = 200
    ) -> Dict[str, Any]:
        """記事要約生成"""
        prompt = f"""以下の記事を{max_length}文字以内で要約してください。
重要なポイントを簡潔にまとめてください。

記事内容:
{content}

要約:"""
        
        return await self.llm_service.generate_completion(
            prompt=prompt,
            max_tokens=max_length * 2,  # 安全マージン
            temperature=0.1
        )
    
    async def extract_keywords(self, content: str, max_keywords: int = 10) -> Dict[str, Any]:
        """キーワード抽出"""
        prompt = f"""以下のテキストから重要なキーワードを{max_keywords}個以内で抽出してください。
キーワードはカンマで区切って出力してください。

テキスト:
{content}

キーワード:"""
        
        return await self.llm_service.generate_completion(
            prompt=prompt,
            max_tokens=100,
            temperature=0.1
        )
    
    async def generate_content_ideas(
        self,
        topic: str,
        content_type: str = "article",
        num_ideas: int = 5
    ) -> Dict[str, Any]:
        """コンテンツアイデア生成"""
        prompt = f"""テーマ「{topic}」について、{content_type}の企画を{num_ideas}個提案してください。
各アイデアにはタイトルと簡単な概要を含めてください。

企画案:"""
        
        return await self.llm_service.generate_completion(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7
        )
    
    async def improve_content(
        self,
        content: str,
        improvement_type: str = "readability"
    ) -> Dict[str, Any]:
        """コンテンツ改善提案"""
        prompts = {
            "readability": "以下のテキストの読みやすさを向上させてください。",
            "engagement": "以下のテキストをより魅力的で関心を引く内容に改善してください。",
            "seo": "以下のテキストをSEOに適した形に最適化してください。",
            "clarity": "以下のテキストをより明確で理解しやすい内容に改善してください。"
        }
        
        prompt = f"""{prompts.get(improvement_type, prompts["readability"])}

元のテキスト:
{content}

改善されたテキスト:"""
        
        return await self.llm_service.generate_completion(
            prompt=prompt,
            temperature=0.3
        )
    
    async def analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """コンテンツ品質分析"""
        prompt = f"""以下のコンテンツの品質を分析し、以下の観点で評価してください：
1. 読みやすさ（1-10点）
2. 情報の価値（1-10点）
3. 構成の論理性（1-10点）
4. 改善提案

コンテンツ:
{content}

品質分析:"""
        
        return await self.llm_service.generate_completion(
            prompt=prompt,
            temperature=0.1
        )
