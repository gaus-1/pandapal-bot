/**
 * Универсальный компонент Tabs для переключения контента
 */

import React, { useState } from 'react';

export interface Tab {
  id: string;
  label: string;
  icon?: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
}

/**
 * Компонент табов с адаптивным дизайном
 * На мобильных - вертикальный список, на десктопе - горизонтальный
 */
export const Tabs: React.FC<TabsProps> = React.memo(({ tabs, defaultTab }) => {
  const [activeTab, setActiveTab] = useState<string>(defaultTab || tabs[0]?.id);

  const activeContent = tabs.find((tab) => tab.id === activeTab)?.content;

  return (
    <div className="w-full">
      {/* Навигация табов */}
      <div
        className="flex flex-col md:flex-row gap-2 md:gap-4 mb-8 md:mb-12 border-b border-gray-200 pb-4"
        role="tablist"
        aria-label="Информация о PandaPal"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            className={`
              px-6 py-3 rounded-lg font-semibold text-left md:text-center transition-all duration-300
              ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-sky to-pink text-white shadow-lg transform scale-105'
                  : 'bg-white text-gray-700 hover:bg-gray-50 hover:text-gray-900 border border-gray-200'
              }
            `}
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Контент активного таба */}
      <div
        id={`panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
        className="animate-fadeIn"
      >
        {activeContent}
      </div>
    </div>
  );
});

Tabs.displayName = 'Tabs';
