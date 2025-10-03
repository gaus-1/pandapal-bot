/**
 * Анимированный логотип PandaPal
 * Создан специально для детской образовательной платформы
 * @component PandaLogo
 * @author Senior Frontend Animator
 */

import React, { useState, useEffect } from 'react';
import './PandaLogo.css';

interface PandaLogoProps {
  /** Размер логотипа в пикселях */
  size?: number;
  /** Включить/выключить анимации */
  animated?: boolean;
  /** Дополнительный CSS класс */
  className?: string;
  /** Обработчик клика */
  onClick?: () => void;
  /** Показать loading анимацию */
  loading?: boolean;
}

const PandaLogo: React.FC<PandaLogoProps> = ({
  size = 64,
  animated = true,
  className = '',
  onClick,
  loading = false
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  // Обработка клика с анимацией
  const handleClick = () => {
    if (animated) {
      setIsClicked(true);
      setTimeout(() => setIsClicked(false), 600);
    }
    onClick?.();
  };

  // Автоматическое моргание
  useEffect(() => {
    if (!animated) return;

    const blinkInterval = setInterval(() => {
      // Моргание реализовано через CSS анимацию
    }, 3500 + Math.random() * 2000); // Случайный интервал 3.5-5.5 сек

    return () => clearInterval(blinkInterval);
  }, [animated]);

  return (
    <div
      className={`panda-logo-container ${className}`}
      style={{ 
        width: size, 
        height: size,
        cursor: onClick ? 'pointer' : 'default'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="PandaPal логотип"
        className={`panda-logo ${animated ? 'animated' : ''} ${isHovered ? 'hovered' : ''} ${isClicked ? 'clicked' : ''} ${loading ? 'loading' : ''}`}
      >
        {/* Голова панды */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="#FFFFFF"
          stroke="#333333"
          strokeWidth="2"
          className="panda-head"
        />
        
        {/* Уши */}
        <circle
          cx="35"
          cy="25"
          r="12"
          fill="#333333"
          className="panda-ear-left"
        />
        <circle
          cx="65"
          cy="25"
          r="12"
          fill="#333333"
          className="panda-ear-right"
        />
        
        {/* Внутренняя часть ушей */}
        <circle
          cx="35"
          cy="25"
          r="6"
          fill="#FFFFFF"
          className="panda-ear-inner-left"
        />
        <circle
          cx="65"
          cy="25"
          r="6"
          fill="#FFFFFF"
          className="panda-ear-inner-right"
        />
        
        {/* Глаза (основные) */}
        <circle
          cx="40"
          cy="40"
          r="8"
          fill="#333333"
          className="panda-eye-left"
        />
        <circle
          cx="60"
          cy="40"
          r="8"
          fill="#333333"
          className="panda-eye-right"
        />
        
        {/* Зрачки */}
        <circle
          cx="42"
          cy="42"
          r="3"
          fill="#FFFFFF"
          className="panda-pupil-left"
        />
        <circle
          cx="58"
          cy="42"
          r="3"
          fill="#FFFFFF"
          className="panda-pupil-right"
        />
        
        {/* Веки для моргания */}
        <ellipse
          cx="40"
          cy="40"
          rx="8"
          ry="4"
          fill="#FFFFFF"
          className="panda-eyelid-left"
        />
        <ellipse
          cx="60"
          cy="40"
          rx="8"
          ry="4"
          fill="#FFFFFF"
          className="panda-eyelid-right"
        />
        
        {/* Нос */}
        <ellipse
          cx="50"
          cy="55"
          rx="3"
          ry="2"
          fill="#333333"
          className="panda-nose"
        />
        
        {/* Рот */}
        <path
          d="M 45 65 Q 50 70 55 65"
          stroke="#333333"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
          className="panda-mouth"
        />
        
        {/* Щеки (розовые) */}
        <circle
          cx="30"
          cy="55"
          r="6"
          fill="#FFB6C1"
          opacity="0.7"
          className="panda-cheek-left"
        />
        <circle
          cx="70"
          cy="55"
          r="6"
          fill="#FFB6C1"
          opacity="0.7"
          className="panda-cheek-right"
        />
        
        {/* Loading пузырьки */}
        {loading && (
          <>
            <circle cx="50" cy="10" r="2" fill="#4A90E2" className="bubble bubble-1">
              <animate attributeName="cy" values="10;5;10" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle cx="45" cy="15" r="1.5" fill="#4A90E2" className="bubble bubble-2">
              <animate attributeName="cy" values="15;8;15" dur="2.5s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="1;0.3;1" dur="2.5s" repeatCount="indefinite" />
            </circle>
            <circle cx="55" cy="12" r="1" fill="#4A90E2" className="bubble bubble-3">
              <animate attributeName="cy" values="12;6;12" dur="3s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="1;0.3;1" dur="3s" repeatCount="indefinite" />
            </circle>
          </>
        )}
      </svg>

    </div>
  );
};

export default PandaLogo;
