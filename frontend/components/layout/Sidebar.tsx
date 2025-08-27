'use client';

import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface MenuItem {
  id: string;
  name: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  description: string;
}

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
  menuItems: MenuItem[];
}

export function Sidebar({ activeView, onViewChange, menuItems }: SidebarProps) {
  return (
    <motion.div
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      className="w-72 bg-white border-r border-gray-200 shadow-sm flex flex-col"
    >
      {/* ヘッダー */}
      <div className="p-6 border-b border-gray-200">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center space-x-3"
        >
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">AI</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Media Assistant</h1>
            <p className="text-sm text-gray-500">v1.0.0</p>
          </div>
        </motion.div>
      </div>

      {/* ナビゲーションメニュー */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item, index) => {
          const isActive = activeView === item.id;
          const Icon = item.icon;

          return (
            <motion.button
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * index }}
              onClick={() => onViewChange(item.id)}
              className={clsx(
                'w-full flex items-center p-3 rounded-lg text-left transition-all duration-200 group',
                isActive
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-700 hover:bg-gray-50'
              )}
            >
              <Icon
                className={clsx(
                  'w-5 h-5 mr-3 transition-colors',
                  isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'
                )}
              />
              <div className="flex-1">
                <div className="font-medium">{item.name}</div>
                <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
              </div>
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="w-2 h-2 bg-blue-600 rounded-full"
                />
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* ステータス */}
      <div className="p-4 border-t border-gray-200">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-green-50 border border-green-200 rounded-lg p-3"
        >
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-green-800">システム稼働中</span>
          </div>
          <div className="text-xs text-green-600 mt-1">
            全サービス正常動作
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
