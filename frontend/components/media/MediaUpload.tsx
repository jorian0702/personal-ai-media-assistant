'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { 
  CloudArrowUpIcon, 
  DocumentIcon, 
  PhotoIcon, 
  VideoCameraIcon,
  MusicalNoteIcon,
  XMarkIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface UploadFile {
  file: File;
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  mediaType: 'image' | 'video' | 'audio' | 'document';
  preview?: string;
  error?: string;
}

export function MediaUpload() {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'pending',
      mediaType: getMediaType(file),
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
    }));

    setUploadFiles(prev => [...prev, ...newFiles]);
    
    // アップロード開始
    newFiles.forEach(uploadFile => {
      handleUpload(uploadFile);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive: dropzoneActive } = useDropzone({
    onDrop,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    maxSize: 50 * 1024 * 1024, // 50MB
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'],
      'video/*': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
      'audio/*': ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    }
  });

  const handleUpload = async (uploadFile: UploadFile) => {
    setUploadFiles(prev => 
      prev.map(f => f.id === uploadFile.id ? { ...f, status: 'uploading' } : f)
    );

    try {
      const formData = new FormData();
      formData.append('file', uploadFile.file);

      // アップロード進捗をシミュレート
      const simulateProgress = () => {
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 30;
          if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            
            // 処理開始
            setUploadFiles(prev => 
              prev.map(f => f.id === uploadFile.id ? { ...f, progress, status: 'processing' } : f)
            );

            // 処理完了をシミュレート
            setTimeout(() => {
              setUploadFiles(prev => 
                prev.map(f => f.id === uploadFile.id ? { ...f, status: 'completed' } : f)
              );
              toast.success(`${uploadFile.file.name} の処理が完了しました`);
            }, 2000 + Math.random() * 3000);

          } else {
            setUploadFiles(prev => 
              prev.map(f => f.id === uploadFile.id ? { ...f, progress } : f)
            );
          }
        }, 200);
      };

      simulateProgress();

      // 実際のAPI呼び出し（コメントアウト）
      /*
      const response = await fetch('/api/media/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      */

    } catch (error) {
      setUploadFiles(prev => 
        prev.map(f => f.id === uploadFile.id ? { 
          ...f, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Unknown error'
        } : f)
      );
      toast.error(`${uploadFile.file.name} のアップロードに失敗しました`);
    }
  };

  const removeFile = (id: string) => {
    setUploadFiles(prev => prev.filter(f => f.id !== id));
  };

  const getMediaType = (file: File): 'image' | 'video' | 'audio' | 'document' => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    return 'document';
  };

  const getMediaIcon = (mediaType: string) => {
    switch (mediaType) {
      case 'image': return PhotoIcon;
      case 'video': return VideoCameraIcon;
      case 'audio': return MusicalNoteIcon;
      default: return DocumentIcon;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* ドロップゾーン */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        <div
          {...getRootProps()}
          className={`
            relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-300
            ${isDragActive || dropzoneActive 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
            }
          `}
        >
          <input {...getInputProps()} />
          
          <motion.div
            animate={{ scale: isDragActive ? 1.05 : 1 }}
            transition={{ duration: 0.2 }}
          >
            <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <div className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive ? 'ファイルをドロップしてください' : 'ファイルをアップロード'}
            </div>
            <p className="text-gray-500 mb-4">
              画像、動画、音声ファイルをドラッグ&ドロップまたはクリックして選択
            </p>
            <div className="text-sm text-gray-400">
              対応形式: JPG, PNG, MP4, MP3, WAV など | 最大 50MB
            </div>
          </motion.div>

          {/* 処理中オーバーレイ */}
          <AnimatePresence>
            {isDragActive && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-blue-100 bg-opacity-50 rounded-lg flex items-center justify-center"
              >
                <div className="text-blue-600 font-medium">ファイルをドロップ！</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* アップロード済みファイル一覧 */}
      <AnimatePresence>
        {uploadFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <h3 className="text-lg font-medium text-gray-900">アップロード中のファイル</h3>
            
            {uploadFiles.map((uploadFile) => {
              const MediaIcon = getMediaIcon(uploadFile.mediaType);
              
              return (
                <motion.div
                  key={uploadFile.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
                >
                  <div className="flex items-center space-x-4">
                    {/* プレビュー/アイコン */}
                    <div className="flex-shrink-0">
                      {uploadFile.preview ? (
                        <img
                          src={uploadFile.preview}
                          alt={uploadFile.file.name}
                          className="w-12 h-12 object-cover rounded-md"
                        />
                      ) : (
                        <div className="w-12 h-12 bg-gray-100 rounded-md flex items-center justify-center">
                          <MediaIcon className="w-6 h-6 text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* ファイル情報 */}
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 truncate">
                        {uploadFile.file.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {formatFileSize(uploadFile.file.size)} • {uploadFile.mediaType}
                      </div>
                    </div>

                    {/* ステータス */}
                    <div className="flex items-center space-x-3">
                      {uploadFile.status === 'uploading' && (
                        <div className="flex items-center space-x-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <motion.div
                              className="bg-blue-600 h-2 rounded-full"
                              initial={{ width: '0%' }}
                              animate={{ width: `${uploadFile.progress}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          <span className="text-sm text-gray-500">
                            {Math.round(uploadFile.progress)}%
                          </span>
                        </div>
                      )}

                      {uploadFile.status === 'processing' && (
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
                          <span className="text-sm text-blue-600">処理中...</span>
                        </div>
                      )}

                      {uploadFile.status === 'completed' && (
                        <div className="flex items-center space-x-2">
                          <CheckCircleIcon className="w-5 h-5 text-green-500" />
                          <span className="text-sm text-green-600">完了</span>
                        </div>
                      )}

                      {uploadFile.status === 'error' && (
                        <div className="flex items-center space-x-2">
                          <XMarkIcon className="w-5 h-5 text-red-500" />
                          <span className="text-sm text-red-600">エラー</span>
                        </div>
                      )}

                      {/* 削除ボタン */}
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => removeFile(uploadFile.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </motion.button>
                    </div>
                  </div>

                  {/* エラーメッセージ */}
                  {uploadFile.error && (
                    <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                      {uploadFile.error}
                    </div>
                  )}
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 処理統計 */}
      {uploadFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-gray-50 rounded-lg p-4"
        >
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {uploadFiles.length}
              </div>
              <div className="text-sm text-gray-500">総ファイル数</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {uploadFiles.filter(f => f.status === 'uploading' || f.status === 'processing').length}
              </div>
              <div className="text-sm text-gray-500">処理中</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {uploadFiles.filter(f => f.status === 'completed').length}
              </div>
              <div className="text-sm text-gray-500">完了</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {uploadFiles.filter(f => f.status === 'error').length}
              </div>
              <div className="text-sm text-gray-500">エラー</div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
