/**
 * Индикатор прокрутки для Hero-секции
 * Анимированная стрелка вниз
 */

import React, { useEffect, useState } from 'react';

export const ScrollIndicator: React.FC = React.memo(() => {
  const [isVisible, setIsVisible] = useState<boolean>(true);

  useEffect(() => {
    const handleScroll = () => {
      // Скрываем индикатор после прокрутки на 100px
      setIsVisible(window.scrollY < 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToContent = () => {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (!isVisible) return null;

  return (
    <div className="flex flex-col items-center gap-2 animate-bounce">
      <button
        onClick={scrollToContent}
        className="flex flex-col items-center gap-2 text-gray-600 hover:text-pink transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-pink focus:ring-offset-2 rounded-lg p-2"
        aria-label="Прокрутить вниз к контенту"
      >
        <span className="text-sm font-medium">Прокрути вниз 🐼</span>

        {/* Анимированная стрелка вниз */}
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      </button>
    </div>
  );
});

ScrollIndicator.displayName = 'ScrollIndicator';
