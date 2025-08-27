'use client';

import { motion } from 'framer-motion';
import { BellIcon, Cog6ToothIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';

interface MenuItem {
  id: string;
  name: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  description: string;
}

interface HeaderProps {
  currentView?: MenuItem;
}

export function Header({ currentView }: HeaderProps) {
  const [notifications, setNotifications] = useState(3);

  return (
    <motion.header
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-white border-b border-gray-200 shadow-sm px-6 py-4"
    >
      <div className="flex items-center justify-between">
        {/* 現在のビュー情報 */}
        <div className="flex items-center space-x-4">
          {currentView && (
            <>
              <currentView.icon className="w-6 h-6 text-blue-600" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{currentView.name}</h2>
                <p className="text-sm text-gray-500">{currentView.description}</p>
              </div>
            </>
          )}
        </div>

        {/* 右側のアクション */}
        <div className="flex items-center space-x-4">
          {/* 通知 */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <BellIcon className="w-6 h-6" />
            {notifications > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
              >
                {notifications}
              </motion.span>
            )}
          </motion.button>

          {/* 設定 */}
          <motion.button
            whileHover={{ scale: 1.05, rotate: 15 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <Cog6ToothIcon className="w-6 h-6" />
          </motion.button>

          {/* ユーザープロフィール */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <UserCircleIcon className="w-8 h-8 text-gray-400" />
            <div className="text-left">
              <div className="text-sm font-medium text-gray-900">Admin User</div>
              <div className="text-xs text-gray-500">システム管理者</div>
            </div>
          </motion.button>
        </div>
      </div>

      {/* プログレスバー（処理中の場合） */}
      <motion.div
        initial={{ width: '0%' }}
        animate={{ width: '100%' }}
        transition={{ duration: 2, ease: 'easeInOut' }}
        className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-600 opacity-0"
        style={{
          display: 'none' // 実際の処理状況に応じて表示
        }}
      />
    </motion.header>
  );
}
