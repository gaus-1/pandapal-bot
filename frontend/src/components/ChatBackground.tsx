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

      {/* SVG паттерн с doodles - профессиональный стиль Telegram, но более заметный */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ opacity: 0.12 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="doodlePattern" x="0" y="0" width="140" height="180" patternUnits="userSpaceOnUse">
            {/* Панда - крупнее и заметнее */}
            <g transform="translate(25, 35)" opacity="0.7">
              <circle cx="0" cy="0" r="12" fill="none" stroke="#94a3b8" strokeWidth="2" />
              <circle cx="-5" cy="-4" r="2.5" fill="none" stroke="#94a3b8" strokeWidth="2" />
              <circle cx="5" cy="-4" r="2.5" fill="none" stroke="#94a3b8" strokeWidth="2" />
              <ellipse cx="0" cy="4" rx="4" ry="3" fill="none" stroke="#94a3b8" strokeWidth="2" />
            </g>

            {/* Книга - крупнее */}
            <g transform="translate(70, 70)" opacity="0.6">
              <rect x="-10" y="-8" width="20" height="16" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
              <line x1="0" y1="-8" x2="0" y2="8" stroke="#94a3b8" strokeWidth="1.8" />
            </g>

            {/* Карандаш - крупнее */}
            <g transform="translate(105, 50)" opacity="0.6">
              <rect x="-4" y="-10" width="8" height="20" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
              <polygon points="-4,-10 0,-14 4,-10" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
            </g>

            {/* Звезда - крупнее */}
            <g transform="translate(35, 110)" opacity="0.6">
              <path d="M0,-10 L2.5,-2.5 L10,-2.5 L4,3 L6,10 L0,6 L-6,10 L-4,3 L-10,-2.5 L-2.5,-2.5 Z" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
            </g>

            {/* Глобус - крупнее */}
            <g transform="translate(90, 120)" opacity="0.6">
              <circle cx="0" cy="0" r="12" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
              <ellipse cx="0" cy="0" rx="12" ry="6" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <line x1="-12" y1="0" x2="12" y2="0" stroke="#94a3b8" strokeWidth="1.5" />
            </g>

            {/* Формула (x²) - крупнее */}
            <g transform="translate(25, 150)" opacity="0.7">
              <text x="0" y="0" fontSize="18" fill="#94a3b8" fontFamily="serif" textAnchor="middle" dominantBaseline="middle" fontWeight="500">x²</text>
            </g>

            {/* Карандаш (второй) - крупнее */}
            <g transform="translate(100, 160)" opacity="0.6">
              <rect x="-4" y="-10" width="8" height="20" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
              <polygon points="-4,-10 0,-14 4,-10" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
            </g>

            {/* Звезда (вторая) - крупнее */}
            <g transform="translate(50, 190)" opacity="0.6">
              <path d="M0,-9 L2,-2 L9,-2 L3.5,2.5 L5.5,9 L0,6 L-5.5,9 L-3.5,2.5 L-9,-2 L-2,-2 Z" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
            </g>

            {/* Формула (π) - крупнее */}
            <g transform="translate(80, 210)" opacity="0.7">
              <text x="0" y="0" fontSize="20" fill="#94a3b8" fontFamily="serif" textAnchor="middle" dominantBaseline="middle" fontWeight="500">π</text>
            </g>

            {/* Книга (вторая) - для разнообразия */}
            <g transform="translate(120, 100)" opacity="0.6">
              <rect x="-10" y="-8" width="20" height="16" fill="none" stroke="#94a3b8" strokeWidth="1.8" />
              <line x1="0" y1="-8" x2="0" y2="8" stroke="#94a3b8" strokeWidth="1.8" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePattern)" />
      </svg>
    </div>
  );
}
