"""
マルチモーダル前処理サービス
画像・動画・音声の前処理とコンテンツ抽出
"""

import asyncio
import tempfile
import os
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import structlog

# 画像処理
import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr

# 動画処理
import moviepy.editor as mp
from moviepy.video.io.VideoFileClip import VideoFileClip

# 音声処理
import whisper
import librosa
import soundfile as sf

# 機械学習
import torch
from transformers import pipeline, AutoTokenizer, AutoModel

from app.core.config import settings
from app.models.media import MediaFile, ProcessingResult, ContentAnalysis


logger = structlog.get_logger(__name__)


class MultimodalProcessor:
    """マルチモーダル前処理器"""
    
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['ja', 'en'])
        self.whisper_model = whisper.load_model(settings.WHISPER_MODEL)
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )
        
    async def process_media_file(self, media_file: MediaFile) -> Dict[str, Any]:
        """メディアファイルの包括的処理"""
        results = {}
        
        try:
            if media_file.media_type == "image":
                results = await self._process_image(media_file)
            elif media_file.media_type == "video":
                results = await self._process_video(media_file)
            elif media_file.media_type == "audio":
                results = await self._process_audio(media_file)
            
            # 共通後処理
            if "text" in results:
                results["text_analysis"] = await self._analyze_text(results["text"])
                
        except Exception as e:
            logger.error("Media processing failed", 
                        media_id=media_file.id, error=str(e))
            results["error"] = str(e)
            
        return results
    
    async def _process_image(self, media_file: MediaFile) -> Dict[str, Any]:
        """画像処理パイプライン"""
        results = {}
        
        # 画像読み込み
        image = cv2.imread(media_file.file_path)
        if image is None:
            raise ValueError("Failed to load image")
        
        # 基本情報取得
        height, width, channels = image.shape
        results["image_info"] = {
            "width": width,
            "height": height,
            "channels": channels,
            "file_size": media_file.file_size
        }
        
        # OCR処理（複数エンジン併用）
        results["ocr"] = await self._extract_text_from_image(image)
        
        # 物体検出
        results["objects"] = await self._detect_objects(image)
        
        # 画像品質分析
        results["quality"] = await self._analyze_image_quality(image)
        
        # シーン分析
        results["scene"] = await self._analyze_scene(image)
        
        # 統合テキスト
        results["text"] = results["ocr"].get("text", "")
        
        return results
    
    async def _process_video(self, media_file: MediaFile) -> Dict[str, Any]:
        """動画処理パイプライン"""
        results = {}
        
        # 動画情報取得
        with VideoFileClip(media_file.file_path) as video:
            results["video_info"] = {
                "duration": video.duration,
                "fps": video.fps,
                "width": video.w,
                "height": video.h,
                "has_audio": video.audio is not None
            }
            
            # フレーム抽出（キーフレーム）
            frames = await self._extract_key_frames(video)
            results["frames"] = frames
            
            # 各フレームでOCR
            frame_texts = []
            for i, frame in enumerate(frames["images"]):
                frame_ocr = await self._extract_text_from_image(frame)
                frame_texts.append({
                    "timestamp": frames["timestamps"][i],
                    "text": frame_ocr.get("text", ""),
                    "confidence": frame_ocr.get("confidence", 0.0)
                })
            results["frame_ocr"] = frame_texts
            
            # 音声抽出・文字起こし
            if video.audio:
                audio_results = await self._extract_audio_from_video(video)
                results.update(audio_results)
        
        # 統合テキスト（OCR + 音声認識）
        all_text = []
        if "transcript" in results:
            all_text.append(results["transcript"]["text"])
        for frame_text in frame_texts:
            if frame_text["text"].strip():
                all_text.append(frame_text["text"])
        
        results["text"] = " ".join(all_text)
        
        return results
    
    async def _process_audio(self, media_file: MediaFile) -> Dict[str, Any]:
        """音声処理パイプライン"""
        results = {}
        
        # 音声文字起こし
        transcript = await self._transcribe_audio(media_file.file_path)
        results["transcript"] = transcript
        
        # 音声分析
        audio_analysis = await self._analyze_audio(media_file.file_path)
        results["audio_analysis"] = audio_analysis
        
        # 話者分析
        speaker_analysis = await self._analyze_speakers(media_file.file_path)
        results["speaker_analysis"] = speaker_analysis
        
        results["text"] = transcript.get("text", "")
        
        return results
    
    async def _extract_text_from_image(self, image: np.ndarray) -> Dict[str, Any]:
        """画像からテキスト抽出（OCR）"""
        results = {}
        
        # EasyOCR
        try:
            easyocr_results = self.ocr_reader.readtext(image)
            easyocr_text = " ".join([result[1] for result in easyocr_results])
            easyocr_confidence = np.mean([result[2] for result in easyocr_results]) if easyocr_results else 0.0
            
            results["easyocr"] = {
                "text": easyocr_text,
                "confidence": float(easyocr_confidence),
                "details": easyocr_results
            }
        except Exception as e:
            logger.warning("EasyOCR failed", error=str(e))
            results["easyocr"] = {"text": "", "confidence": 0.0, "error": str(e)}
        
        # Tesseract
        try:
            # 画像前処理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            tesseract_text = pytesseract.image_to_string(processed, lang='jpn+eng')
            tesseract_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
            
            # 信頼度計算
            confidences = [int(conf) for conf in tesseract_data['conf'] if int(conf) > 0]
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            results["tesseract"] = {
                "text": tesseract_text.strip(),
                "confidence": float(avg_confidence / 100.0),
                "details": tesseract_data
            }
        except Exception as e:
            logger.warning("Tesseract failed", error=str(e))
            results["tesseract"] = {"text": "", "confidence": 0.0, "error": str(e)}
        
        # 最良結果選択
        best_result = max(
            [results.get("easyocr", {}), results.get("tesseract", {})],
            key=lambda x: x.get("confidence", 0.0)
        )
        
        results["text"] = best_result.get("text", "")
        results["confidence"] = best_result.get("confidence", 0.0)
        
        return results
    
    async def _transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """音声文字起こし（Whisper）"""
        try:
            result = self.whisper_model.transcribe(
                audio_path,
                language="ja",
                task="transcribe"
            )
            
            return {
                "text": result["text"],
                "language": result["language"],
                "segments": result["segments"],
                "confidence": np.mean([seg["avg_logprob"] for seg in result["segments"]])
            }
        except Exception as e:
            logger.error("Whisper transcription failed", error=str(e))
            return {"text": "", "error": str(e)}
    
    async def _extract_key_frames(self, video: VideoFileClip, num_frames: int = 10) -> Dict[str, Any]:
        """動画からキーフレーム抽出"""
        duration = video.duration
        timestamps = np.linspace(0, duration, num_frames)
        
        frames = []
        for timestamp in timestamps:
            frame = video.get_frame(timestamp)
            frames.append(frame)
        
        return {
            "images": frames,
            "timestamps": timestamps.tolist(),
            "count": len(frames)
        }
    
    async def _extract_audio_from_video(self, video: VideoFileClip) -> Dict[str, Any]:
        """動画から音声抽出・処理"""
        results = {}
        
        # 一時ファイルに音声保存
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            try:
                video.audio.write_audiofile(temp_audio.name, logger=None)
                
                # 文字起こし
                transcript = await self._transcribe_audio(temp_audio.name)
                results["transcript"] = transcript
                
                # 音声分析
                audio_analysis = await self._analyze_audio(temp_audio.name)
                results["audio_analysis"] = audio_analysis
                
            finally:
                os.unlink(temp_audio.name)
        
        return results
    
    async def _detect_objects(self, image: np.ndarray) -> Dict[str, Any]:
        """物体検出（簡易版）"""
        # ここでは簡単な色分析のみ実装
        # 実際の物体検出にはYOLOやR-CNNなどを使用
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 主要色抽出
        colors = []
        h, s, v = cv2.split(hsv)
        
        return {
            "dominant_colors": colors,
            "brightness": float(np.mean(v)),
            "saturation": float(np.mean(s)),
            "objects": []  # TODO: 実際の物体検出実装
        }
    
    async def _analyze_image_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """画像品質分析"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # ブレ検出（ラプラシアン分散）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # ノイズレベル推定
        noise_level = np.std(gray)
        
        # コントラスト
        contrast = gray.std()
        
        return {
            "sharpness": float(laplacian_var),
            "noise_level": float(noise_level),
            "contrast": float(contrast),
            "brightness": float(gray.mean())
        }
    
    async def _analyze_scene(self, image: np.ndarray) -> Dict[str, Any]:
        """シーン分析"""
        # 簡易的な分析実装
        # 実際にはCNNベースの画像分類を使用
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # エッジ検出
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        return {
            "edge_density": float(edge_density),
            "scene_type": "unknown",  # TODO: 実際のシーン分類実装
            "complexity": float(edge_density)
        }
    
    async def _analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """音声分析"""
        try:
            y, sr = librosa.load(audio_path)
            
            # 基本特徴量
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            mfccs = librosa.feature.mfcc(y=y, sr=sr)
            
            return {
                "duration": float(len(y) / sr),
                "tempo": float(tempo),
                "spectral_centroid_mean": float(np.mean(spectral_centroids)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
                "rms_energy": float(np.sqrt(np.mean(y**2)))
            }
        except Exception as e:
            logger.error("Audio analysis failed", error=str(e))
            return {"error": str(e)}
    
    async def _analyze_speakers(self, audio_path: str) -> Dict[str, Any]:
        """話者分析"""
        # 簡易版実装
        # 実際には話者ダイアライゼーションライブラリを使用
        try:
            y, sr = librosa.load(audio_path)
            
            # 音声活動検出
            intervals = librosa.effects.split(y, top_db=20)
            
            return {
                "speech_segments": len(intervals),
                "total_speech_duration": float(np.sum(intervals[:, 1] - intervals[:, 0]) / sr),
                "estimated_speakers": 1  # TODO: 実際の話者数推定
            }
        except Exception as e:
            logger.error("Speaker analysis failed", error=str(e))
            return {"error": str(e)}
    
    async def _analyze_text(self, text: str) -> Dict[str, Any]:
        """テキスト分析"""
        if not text.strip():
            return {}
        
        results = {}
        
        # 感情分析
        try:
            sentiment = self.sentiment_analyzer(text)
            results["sentiment"] = sentiment[0] if sentiment else None
        except Exception as e:
            logger.warning("Sentiment analysis failed", error=str(e))
        
        # 基本統計
        results["stats"] = {
            "character_count": len(text),
            "word_count": len(text.split()),
            "sentence_count": len([s for s in text.split('.') if s.strip()])
        }
        
        return results
