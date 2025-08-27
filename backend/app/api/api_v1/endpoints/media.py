"""
メディア処理エンドポイント
画像・動画・音声のアップロード・処理・分析
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import shutil
import uuid
from pathlib import Path
import structlog

from app.services.multimodal_processor import MultimodalProcessor
from app.services.llm_service import EmbeddingService
from app.models.media import MediaFile, ProcessingStatus
from app.core.config import settings
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_media_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """メディアファイルアップロード"""
    
    # ファイルサイズチェック
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # ファイル形式チェック
    file_extension = Path(file.filename).suffix.lower().lstrip('.')
    media_type = _determine_media_type(file_extension)
    
    if not media_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_extension}"
        )
    
    try:
        # ファイル保存
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.{file_extension}"
        file_path = Path("uploads") / media_type / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # データベース保存
        media_file = MediaFile(
            uuid=file_id,
            filename=filename,
            original_name=file.filename,
            file_path=str(file_path),
            file_size=file.size,
            mime_type=file.content_type,
            media_type=media_type,
            processing_status=ProcessingStatus.PENDING
        )
        
        db.add(media_file)
        await db.commit()
        await db.refresh(media_file)
        
        # バックグラウンド処理開始
        background_tasks.add_task(process_media_file_async, media_file.id)
        
        logger.info("Media file uploaded", 
                   file_id=file_id, filename=file.filename, media_type=media_type)
        
        return {
            "id": media_file.id,
            "uuid": media_file.uuid,
            "filename": media_file.filename,
            "media_type": media_type,
            "status": ProcessingStatus.PENDING,
            "message": "File uploaded successfully. Processing started."
        }
        
    except Exception as e:
        logger.error("File upload failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files", response_model=List[Dict[str, Any]])
async def list_media_files(
    media_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """メディアファイル一覧取得"""
    
    query = db.query(MediaFile)
    
    if media_type:
        query = query.filter(MediaFile.media_type == media_type)
    
    if status:
        query = query.filter(MediaFile.processing_status == status)
    
    files = await query.offset(offset).limit(limit).all()
    
    return [file.to_dict() for file in files]


@router.get("/files/{file_id}", response_model=Dict[str, Any])
async def get_media_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """メディアファイル詳細取得"""
    
    media_file = await db.get(MediaFile, file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    # 処理結果も含めて返す
    result = media_file.to_dict()
    result["processing_results"] = [pr.to_dict() for pr in media_file.processing_results]
    
    return result


@router.post("/files/{file_id}/reprocess")
async def reprocess_media_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """メディアファイル再処理"""
    
    media_file = await db.get(MediaFile, file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    # ステータス更新
    media_file.processing_status = ProcessingStatus.PENDING
    media_file.processing_error = None
    await db.commit()
    
    # バックグラウンド処理開始
    background_tasks.add_task(process_media_file_async, file_id)
    
    return {"message": "Reprocessing started", "status": ProcessingStatus.PENDING}


@router.post("/files/{file_id}/analyze", response_model=Dict[str, Any])
async def analyze_media_content(
    file_id: int,
    analysis_type: str = "comprehensive",
    db: AsyncSession = Depends(get_db)
):
    """メディアコンテンツ分析"""
    
    media_file = await db.get(MediaFile, file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    if media_file.processing_status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="File processing not completed")
    
    try:
        processor = MultimodalProcessor()
        
        if analysis_type == "comprehensive":
            results = await processor.process_media_file(media_file)
        elif analysis_type == "text_only":
            results = {"text": media_file.extracted_text or ""}
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
        
        return {
            "file_id": file_id,
            "analysis_type": analysis_type,
            "results": results
        }
        
    except Exception as e:
        logger.error("Media analysis failed", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/search", response_model=Dict[str, Any])
async def search_media_content(
    query: str,
    media_type: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """メディアコンテンツ検索（RAG）"""
    
    try:
        embedding_service = EmbeddingService()
        
        # ベクトル検索
        search_results = await embedding_service.similarity_search(query, limit)
        
        # 結果をメディアファイル情報と合わせて返す
        enriched_results = []
        for result in search_results:
            media_id = result["metadata"].get("media_file_id")
            if media_id:
                media_file = await db.get(MediaFile, media_id)
                if media_file and (not media_type or media_file.media_type == media_type):
                    enriched_results.append({
                        "media_file": media_file.to_dict(),
                        "relevance": result["similarity"],
                        "matching_text": result["text"]
                    })
        
        return {
            "query": query,
            "total_results": len(enriched_results),
            "results": enriched_results
        }
        
    except Exception as e:
        logger.error("Media search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.delete("/files/{file_id}")
async def delete_media_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """メディアファイル削除"""
    
    media_file = await db.get(MediaFile, file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    try:
        # ファイルシステムから削除
        file_path = Path(media_file.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # データベースから削除
        await db.delete(media_file)
        await db.commit()
        
        logger.info("Media file deleted", file_id=file_id)
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error("File deletion failed", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


# ヘルパー関数
def _determine_media_type(file_extension: str) -> Optional[str]:
    """ファイル拡張子からメディアタイプ判定"""
    
    if file_extension in settings.SUPPORTED_IMAGE_FORMATS:
        return "image"
    elif file_extension in settings.SUPPORTED_VIDEO_FORMATS:
        return "video"
    elif file_extension in settings.SUPPORTED_AUDIO_FORMATS:
        return "audio"
    else:
        return None


async def process_media_file_async(file_id: int):
    """メディアファイル非同期処理"""
    
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            media_file = await db.get(MediaFile, file_id)
            if not media_file:
                return
            
            # 処理開始
            media_file.processing_status = ProcessingStatus.PROCESSING
            await db.commit()
            
            # マルチモーダル処理
            processor = MultimodalProcessor()
            results = await processor.process_media_file(media_file)
            
            if "error" in results:
                # エラー処理
                media_file.processing_status = ProcessingStatus.FAILED
                media_file.processing_error = results["error"]
            else:
                # 成功処理
                media_file.processing_status = ProcessingStatus.COMPLETED
                media_file.extracted_text = results.get("text", "")
                media_file.metadata = results
                
                # エンベディング生成・保存
                if media_file.extracted_text:
                    embedding_service = EmbeddingService()
                    embeddings = await embedding_service.create_embeddings(
                        media_file.extracted_text,
                        {"media_file_id": media_file.id, "media_type": media_file.media_type}
                    )
                    await embedding_service.store_embeddings(embeddings, f"media_{media_file.id}")
            
            await db.commit()
            
            logger.info("Media processing completed", 
                       file_id=file_id, status=media_file.processing_status)
            
    except Exception as e:
        logger.error("Background processing failed", file_id=file_id, error=str(e))
        
        # エラー状態更新
        try:
            async with AsyncSessionLocal() as db:
                media_file = await db.get(MediaFile, file_id)
                if media_file:
                    media_file.processing_status = ProcessingStatus.FAILED
                    media_file.processing_error = str(e)
                    await db.commit()
        except Exception:
            pass
