/**
 * Компонент фона чата с doodles в стиле Telegram
 * Профессиональная реализация: тонкие, едва заметные doodles как в Telegram
 */

export function ChatBackground() {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden z-0"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      {/* Градиентный фон в стиле Telegram - очень легкий */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-white to-pink-50/50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900" />

      {/* SVG паттерн с doodles - профессиональный стиль Telegram */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ opacity: 0.08 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="doodlePattern" x="0" y="0" width="120" height="160" patternUnits="userSpaceOnUse">
            {/* Панда - маленькая и тонкая */}
            <g transform="translate(20, 30)" opacity="0.6">
              <circle cx="0" cy="0" r="8" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <circle cx="-4" cy="-3" r="2" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <circle cx="4" cy="-3" r="2" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <ellipse cx="0" cy="3" rx="3" ry="2" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
            </g>

            {/* Книга - тонкая линия */}
            <g transform="translate(60, 60)" opacity="0.5">
              <rect x="-8" y="-6" width="16" height="12" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
              <line x1="0" y1="-6" x2="0" y2="6" stroke="#94a3b8" strokeWidth="1.2" />
            </g>

            {/* Карандаш - тонкий */}
            <g transform="translate(90, 40)" opacity="0.5">
              <rect x="-3" y="-8" width="6" height="16" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
              <polygon points="-3,-8 0,-11 3,-8" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
            </g>

            {/* Звезда - тонкая */}
            <g transform="translate(30, 100)" opacity="0.5">
              <path d="M0,-8 L2,-2 L8,-2 L3,2 L5,8 L0,5 L-5,8 L-3,2 L-8,-2 L-2,-2 Z" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
            </g>

            {/* Глобус - тонкий контур */}
            <g transform="translate(80, 110)" opacity="0.5">
              <circle cx="0" cy="0" r="10" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
              <ellipse cx="0" cy="0" rx="10" ry="5" fill="none" stroke="#94a3b8" strokeWidth="1" />
              <line x1="-10" y1="0" x2="10" y2="0" stroke="#94a3b8" strokeWidth="1" />
            </g>

            {/* Формула (x²) - тонкий текст */}
            <g transform="translate(20, 140)" opacity="0.6">
              <text x="0" y="0" fontSize="14" fill="#94a3b8" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(90, 150)" opacity="0.5">
              <rect x="-3" y="-8" width="6" height="16" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
              <polygon points="-3,-8 0,-11 3,-8" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(40, 180)" opacity="0.5">
              <path d="M0,-7 L1.5,-1.5 L7,-1.5 L2.5,2 L4,7 L0,5 L-4,7 L-2.5,2 L-7,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
            </g>

            {/* Формула (π) */}
            <g transform="translate(70, 200)" opacity="0.6">
              <text x="0" y="0" fontSize="16" fill="#94a3b8" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">π</text>
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePattern)" />
      </svg>
    </div>
  );
}
