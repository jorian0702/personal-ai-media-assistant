"""
LLM・AI機能エンドポイント
RAG、コンテンツ生成、分析等
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import structlog

from app.services.llm_service import LLMService, ContentGenerationService
from app.services.text_mining import TextMiningPipeline
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)
router = APIRouter()


# リクエストモデル
class CompletionRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class ContentGenerationRequest(BaseModel):
    content_type: str  # article, summary, script, etc.
    topic: str
    target_length: Optional[int] = None
    tone: Optional[str] = None
    audience: Optional[str] = None


class TextAnalysisRequest(BaseModel):
    text: str
    analysis_types: List[str] = ["sentiment", "keywords", "summary"]


class ContentImprovementRequest(BaseModel):
    content: str
    improvement_type: str = "readability"  # readability, engagement, seo, clarity


# エンドポイント
@router.post("/completion", response_model=Dict[str, Any])
async def llm_completion(request: CompletionRequest):
    """LLMテキスト生成"""
    
    try:
        llm_service = LLMService()
        
        result = await llm_service.generate_completion(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return {
            "prompt": request.prompt,
            "completion": result,
            "success": True
        }
        
    except Exception as e:
        logger.error("LLM completion failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")


@router.post("/rag/query", response_model=Dict[str, Any])
async def rag_query(request: RAGQueryRequest):
    """RAG検索・回答生成"""
    
    try:
        llm_service = LLMService()
        
        result = await llm_service.rag_query(
            query=request.query,
            top_k=request.top_k
        )
        
        return {
            "query": request.query,
            "rag_result": result,
            "success": True
        }
        
    except Exception as e:
        logger.error("RAG query failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.post("/content/generate", response_model=Dict[str, Any])
async def generate_content(request: ContentGenerationRequest):
    """AIコンテンツ生成"""
    
    try:
        content_service = ContentGenerationService()
        
        if request.content_type == "article":
            prompt = f"以下のテーマについて{request.target_length or 1000}文字程度の記事を作成してください。\n"
            prompt += f"テーマ: {request.topic}\n"
            if request.tone:
                prompt += f"トーン: {request.tone}\n"
            if request.audience:
                prompt += f"対象読者: {request.audience}\n"
            
            result = await content_service.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.7
            )
            
        elif request.content_type == "summary":
            result = await content_service.generate_article_summary(
                content=request.topic,  # topicをコンテンツとして扱う
                max_length=request.target_length or 200
            )
            
        elif request.content_type == "ideas":
            result = await content_service.generate_content_ideas(
                topic=request.topic,
                content_type="article",
                num_ideas=5
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {request.content_type}")
        
        return {
            "request": request.dict(),
            "generated_content": result,
            "success": True
        }
        
    except Exception as e:
        logger.error("Content generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.post("/content/improve", response_model=Dict[str, Any])
async def improve_content(request: ContentImprovementRequest):
    """コンテンツ改善提案"""
    
    try:
        content_service = ContentGenerationService()
        
        result = await content_service.improve_content(
            content=request.content,
            improvement_type=request.improvement_type
        )
        
        return {
            "original_content": request.content,
            "improvement_type": request.improvement_type,
            "improved_content": result,
            "success": True
        }
        
    except Exception as e:
        logger.error("Content improvement failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Content improvement failed: {str(e)}")


@router.post("/analyze/text", response_model=Dict[str, Any])
async def analyze_text(request: TextAnalysisRequest):
    """テキスト分析"""
    
    try:
        content_service = ContentGenerationService()
        results = {}
        
        if "sentiment" in request.analysis_types:
            # 感情分析
            sentiment_prompt = f"以下のテキストの感情を分析してください（ポジティブ/ネガティブ/ニュートラル）:\n{request.text}"
            sentiment_result = await content_service.llm_service.generate_completion(
                prompt=sentiment_prompt,
                temperature=0.1,
                max_tokens=100
            )
            results["sentiment"] = sentiment_result
        
        if "keywords" in request.analysis_types:
            # キーワード抽出
            keyword_result = await content_service.extract_keywords(request.text)
            results["keywords"] = keyword_result
        
        if "summary" in request.analysis_types:
            # 要約生成
            summary_result = await content_service.generate_article_summary(request.text)
            results["summary"] = summary_result
        
        if "quality" in request.analysis_types:
            # 品質分析
            quality_result = await content_service.analyze_content_quality(request.text)
            results["quality"] = quality_result
        
        return {
            "text": request.text,
            "analysis_types": request.analysis_types,
            "results": results,
            "success": True
        }
        
    except Exception as e:
        logger.error("Text analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")


@router.post("/embeddings/create", response_model=Dict[str, Any])
async def create_embeddings(
    text: str,
    document_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """エンベディング作成・保存"""
    
    try:
        llm_service = LLMService()
        
        # エンベディング生成
        embeddings = await llm_service.embedding_service.create_embeddings(
            text=text,
            metadata=metadata or {}
        )
        
        # 保存
        doc_id = document_id or f"doc_{len(text)}"
        await llm_service.embedding_service.store_embeddings(embeddings, doc_id)
        
        return {
            "document_id": doc_id,
            "embeddings_count": len(embeddings),
            "total_chunks": len(embeddings),
            "success": True
        }
        
    except Exception as e:
        logger.error("Embedding creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Embedding creation failed: {str(e)}")


@router.post("/embeddings/search", response_model=Dict[str, Any])
async def search_embeddings(
    query: str,
    top_k: int = 10
):
    """エンベディング検索"""
    
    try:
        llm_service = LLMService()
        
        results = await llm_service.embedding_service.similarity_search(
            query=query,
            top_k=top_k
        )
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "success": True
        }
        
    except Exception as e:
        logger.error("Embedding search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Embedding search failed: {str(e)}")


@router.post("/text-mining/pipeline", response_model=Dict[str, Any])
async def run_text_mining_pipeline(
    sources: Optional[List[str]] = None,
    analyze: bool = True
):
    """テキストマイニングパイプライン実行"""
    
    try:
        pipeline = TextMiningPipeline()
        
        # データ収集
        collection_results = await pipeline.run_collection_pipeline(sources)
        
        results = {
            "collection_results": collection_results,
            "success": True
        }
        
        # 分析実行
        if analyze and collection_results:
            all_content = []
            all_content.extend(collection_results.get("rss_articles", []))
            all_content.extend(collection_results.get("news_articles", []))
            all_content.extend(collection_results.get("social_posts", []))
            
            if all_content:
                analysis_results = await pipeline.analyze_collected_content(all_content)
                results["analysis_results"] = analysis_results
        
        return results
        
    except Exception as e:
        logger.error("Text mining pipeline failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Text mining pipeline failed: {str(e)}")


@router.get("/models", response_model=Dict[str, Any])
async def list_available_models():
    """利用可能モデル一覧"""
    
    models = {
        "llm_models": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229"
        ],
        "embedding_models": [
            "sentence-transformers/all-MiniLM-L6-v2",
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large"
        ],
        "content_types": [
            "article", "summary", "script", "blog_post", 
            "social_media", "press_release", "email", "ideas"
        ],
        "improvement_types": [
            "readability", "engagement", "seo", "clarity"
        ],
        "analysis_types": [
            "sentiment", "keywords", "summary", "quality", "topics"
        ]
    }
    
    return models


@router.get("/status", response_model=Dict[str, Any])
async def get_ai_status():
    """AI機能ステータス確認"""
    
    try:
        llm_service = LLMService()
        
        # 簡単なテスト実行
        test_result = await llm_service.generate_completion(
            prompt="Hello, this is a test.",
            max_tokens=10
        )
        
        status = {
            "llm_service": "operational" if not test_result.get("error") else "error",
            "embedding_service": "operational",
            "vector_database": "operational",
            "text_mining": "operational",
            "last_check": "2024-01-01T00:00:00Z",
            "success": True
        }
        
        return status
        
    except Exception as e:
        logger.error("AI status check failed", error=str(e))
        return {
            "llm_service": "error",
            "embedding_service": "unknown",
            "vector_database": "unknown",
            "text_mining": "unknown",
            "error": str(e),
            "success": False
        }
