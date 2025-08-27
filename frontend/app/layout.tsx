import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Toaster } from 'react-hot-toast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Media Assistant',
  description: '妹用AIメディア処理アシスタント - ファイル整理を楽にするツール',
  keywords: ['AI', 'メディア処理', 'ファイル整理', 'Next.js', 'Python', '趣味プロジェクト'],
  authors: [{ name: '妹思いのお兄ちゃん' }],
  openGraph: {
    title: 'AI Media Assistant',
    description: '妹のメディアファイル整理用に作ったAIアプリ',
    type: 'website',
    locale: 'ja_JP',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" className="h-full">
      <body className={`${inter.className} h-full bg-background antialiased`}>
        <Providers>
          <div className="flex h-full">
            {children}
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
