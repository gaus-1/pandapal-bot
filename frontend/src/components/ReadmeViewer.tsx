/**
 * Компонент для отображения README с поддержкой переключения языков.
 * Загружает и отображает README.md или README_EN.md в зависимости от выбранного языка.
 */

import React, { useState, useEffect } from 'react';
import { LanguageSwitcher } from './LanguageSwitcher';

interface ReadmeViewerProps {
  className?: string;
}

export const ReadmeViewer: React.FC<ReadmeViewerProps> = React.memo(({ className = '' }) => {
  const [currentLang, setCurrentLang] = useState<'ru' | 'en'>('ru');
  const [readmeContent, setReadmeContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReadme();
  }, [currentLang]);

  const loadReadme = async () => {
    try {
      setLoading(true);
      setError(null);

      const filename = currentLang === 'ru' ? 'README.md' : 'README_EN.md';
      const response = await fetch(`/${filename}`);

      if (!response.ok) {
        throw new Error(`Failed to load ${filename}`);
      }

      const content = await response.text();
      setReadmeContent(content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load README');
      console.error('Error loading README:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLangChange = (lang: 'ru' | 'en') => {
    setCurrentLang(lang);
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка документации...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-8 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Ошибка загрузки документации
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={loadReadme}
                  className="bg-red-100 px-3 py-1 rounded text-sm font-medium text-red-800 hover:bg-red-200"
                >
                  Попробовать снова
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <LanguageSwitcher currentLang={currentLang} onLangChange={handleLangChange} />

      <div className="mt-6 prose prose-lg max-w-none">
        <div
          className="markdown-content"
          dangerouslySetInnerHTML={{ __html: convertMarkdownToHtml(readmeContent) }}
        />
      </div>
    </div>
  );
});

ReadmeViewer.displayName = 'ReadmeViewer';

/**
 * Простой конвертер Markdown в HTML для отображения README.
 * В реальном проекте лучше использовать библиотеку типа marked или react-markdown.
 */
const convertMarkdownToHtml = (markdown: string): string => {
  return markdown
    // Заголовки
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mt-6 mb-3">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-8 mb-4">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-8 mb-6">$1</h1>')

    // Жирный текст
    .replace(/\*\*(.*)\*\*/gim, '<strong class="font-semibold">$1</strong>')

    // Курсив
    .replace(/\*(.*)\*/gim, '<em class="italic">$1</em>')

    // Ссылки
    .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">$1</a>')

    // Код в блоках
    .replace(/```([^`]+)```/gim, '<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto"><code>$1</code></pre>')

    // Инлайн код
    .replace(/`([^`]+)`/gim, '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>')

    // Списки
    .replace(/^- (.*$)/gim, '<li class="ml-4">$1</li>')
    .replace(/(<li.*<\/li>)/s, '<ul class="list-disc list-inside space-y-1">$1</ul>')

    // Параграфы
    .replace(/^(?!<[h|u|o|p|d])(.*)$/gim, '<p class="mb-4">$1</p>')

    // Эмодзи и специальные символы
    .replace(/✅/g, '<span class="text-green-600">✅</span>')
    .replace(/🚧/g, '<span class="text-yellow-600">🚧</span>')
    .replace(/📋/g, '<span class="text-blue-600">📋</span>')
    .replace(/🆕/g, '<span class="text-purple-600">🆕</span>')
    .replace(/🐼/g, '<span class="text-gray-800">🐼</span>')
    .replace(/🎮/g, '<span class="text-pink-600">🎮</span>')
    .replace(/🚀/g, '<span class="text-blue-600">🚀</span>')
    .replace(/⭐/g, '<span class="text-yellow-500">⭐</span>');
};
