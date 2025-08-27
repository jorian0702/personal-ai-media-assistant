'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CloudArrowUpIcon, 
  CpuChipIcon, 
  DocumentTextIcon,
  ChartBarIcon,
  BoltIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { MediaUpload } from '@/components/media/MediaUpload';
import { Dashboard } from '@/components/dashboard/Dashboard';
import { MediaGallery } from '@/components/media/MediaGallery';
import { LLMChat } from '@/components/llm/LLMChat';
import { ContentGeneration } from '@/components/content/ContentGeneration';
import { Analytics } from '@/components/analytics/Analytics';

type ActiveView = 'dashboard' | 'upload' | 'gallery' | 'chat' | 'content' | 'analytics';

export default function HomePage() {
  const [activeView, setActiveView] = useState<ActiveView>('dashboard');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 初期ロード完了をシミュレート
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const menuItems = [
    {
      id: 'dashboard' as ActiveView,
      name: 'ダッシュボード',
      icon: ChartBarIcon,
      description: 'システム全体の状況を確認'
    },
    {
      id: 'upload' as ActiveView,
      name: 'メディア処理',
      icon: CloudArrowUpIcon,
      description: '画像・動画・音声のアップロード'
    },
    {
      id: 'gallery' as ActiveView,
      name: 'メディア管理',
      icon: DocumentTextIcon,
      description: '処理済みメディアの閲覧・検索'
    },
    {
      id: 'chat' as ActiveView,
      name: 'AI チャット',
      icon: SparklesIcon,
      description: 'LLM・RAGによる対話'
    },
    {
      id: 'content' as ActiveView,
      name: 'コンテンツ生成',
      icon: CpuChipIcon,
      description: 'AI記事・要約作成'
    },
    {
      id: 'analytics' as ActiveView,
      name: '分析レポート',
      icon: BoltIcon,
      description: 'テキストマイニング結果'
    }
  ];

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard />;
      case 'upload':
        return <MediaUpload />;
      case 'gallery':
        return <MediaGallery />;
      case 'chat':
        return <LLMChat />;
      case 'content':
        return <ContentGeneration />;
      case 'analytics':
        return <Analytics />;
      default:
        return <Dashboard />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="loading-dots mb-4">
            <div></div>
            <div></div>
            <div></div>
            <div></div>
          </div>
          <motion.h2 
            className="text-2xl font-bold text-gray-800 mb-2"
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            AI Media Assistant
          </motion.h2>
          <p className="text-gray-600">システムを初期化中...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar 
        activeView={activeView}
        onViewChange={setActiveView}
        menuItems={menuItems}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          currentView={menuItems.find(item => item.id === activeView)}
        />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6">
          <motion.div
            key={activeView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="max-w-7xl mx-auto"
          >
            {renderContent()}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
