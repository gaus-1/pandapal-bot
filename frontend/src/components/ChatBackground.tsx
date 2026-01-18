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

      {/* SVG паттерн с doodles - плотный и равномерный как в Telegram */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Паттерн для светлой темы - меньший размер для плотности */}
          <pattern id="doodlePatternLight" x="0" y="0" width="100" height="120" patternUnits="userSpaceOnUse">
            {/* Панда */}
            <g transform="translate(20, 25)" opacity="0.6">
              <circle cx="0" cy="0" r="10" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <circle cx="-4" cy="-3" r="2" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <circle cx="4" cy="-3" r="2" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <ellipse cx="0" cy="3" rx="3" ry="2.5" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
            </g>

            {/* Книга */}
            <g transform="translate(50, 45)" opacity="0.5">
              <rect x="-8" y="-6" width="16" height="12" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
              <line x1="0" y1="-6" x2="0" y2="6" stroke="#94a3b8" strokeWidth="1.3" />
            </g>

            {/* Карандаш */}
            <g transform="translate(75, 30)" opacity="0.5">
              <rect x="-3" y="-8" width="6" height="16" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
              <polygon points="-3,-8 0,-11 3,-8" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
            </g>

            {/* Звезда */}
            <g transform="translate(30, 70)" opacity="0.5">
              <path d="M0,-8 L2,-2 L8,-2 L3,2 L5,8 L0,5 L-5,8 L-3,2 L-8,-2 L-2,-2 Z" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
            </g>

            {/* Глобус */}
            <g transform="translate(70, 80)" opacity="0.5">
              <circle cx="0" cy="0" r="10" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
              <ellipse cx="0" cy="0" rx="10" ry="5" fill="none" stroke="#94a3b8" strokeWidth="1.2" />
              <line x1="-10" y1="0" x2="10" y2="0" stroke="#94a3b8" strokeWidth="1.2" />
            </g>

            {/* Формула (x²) */}
            <g transform="translate(20, 100)" opacity="0.6">
              <text x="0" y="0" fontSize="14" fill="#94a3b8" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(80, 110)" opacity="0.5">
              <rect x="-3" y="-8" width="6" height="16" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
              <polygon points="-3,-8 0,-11 3,-8" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(45, 115)" opacity="0.5">
              <path d="M0,-7 L1.5,-1.5 L7,-1.5 L3,1.5 L4.5,7 L0,4.5 L-4.5,7 L-3,1.5 L-7,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
            </g>

            {/* Формула (π) */}
            <g transform="translate(60, 20)" opacity="0.6">
              <text x="0" y="0" fontSize="16" fill="#94a3b8" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">π</text>
            </g>

            {/* Книга (вторая) */}
            <g transform="translate(90, 60)" opacity="0.5">
              <rect x="-8" y="-6" width="16" height="12" fill="none" stroke="#94a3b8" strokeWidth="1.3" />
              <line x1="0" y1="-6" x2="0" y2="6" stroke="#94a3b8" strokeWidth="1.3" />
            </g>

            {/* Панда (вторая) */}
            <g transform="translate(55, 95)" opacity="0.6">
              <circle cx="0" cy="0" r="9" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <circle cx="-3.5" cy="-2.5" r="1.8" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <circle cx="3.5" cy="-2.5" r="1.8" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
              <ellipse cx="0" cy="2.5" rx="2.5" ry="2" fill="none" stroke="#94a3b8" strokeWidth="1.5" />
            </g>
          </pattern>

          {/* Паттерн для темной темы - более светлые цвета */}
          <pattern id="doodlePatternDark" x="0" y="0" width="100" height="120" patternUnits="userSpaceOnUse">
            {/* Панда */}
            <g transform="translate(20, 25)" opacity="0.7">
              <circle cx="0" cy="0" r="10" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
              <circle cx="-4" cy="-3" r="2" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
              <circle cx="4" cy="-3" r="2" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
              <ellipse cx="0" cy="3" rx="3" ry="2.5" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
            </g>

            {/* Книга */}
            <g transform="translate(50, 45)" opacity="0.6">
              <rect x="-8" y="-6" width="16" height="12" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
              <line x1="0" y1="-6" x2="0" y2="6" stroke="#e2e8f0" strokeWidth="1.3" />
            </g>

            {/* Карандаш */}
            <g transform="translate(75, 30)" opacity="0.6">
              <rect x="-3" y="-8" width="6" height="16" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
              <polygon points="-3,-8 0,-11 3,-8" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
            </g>

            {/* Звезда */}
            <g transform="translate(30, 70)" opacity="0.6">
              <path d="M0,-8 L2,-2 L8,-2 L3,2 L5,8 L0,5 L-5,8 L-3,2 L-8,-2 L-2,-2 Z" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
            </g>

            {/* Глобус */}
            <g transform="translate(70, 80)" opacity="0.6">
              <circle cx="0" cy="0" r="10" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
              <ellipse cx="0" cy="0" rx="10" ry="5" fill="none" stroke="#e2e8f0" strokeWidth="1.2" />
              <line x1="-10" y1="0" x2="10" y2="0" stroke="#e2e8f0" strokeWidth="1.2" />
            </g>

            {/* Формула (x²) */}
            <g transform="translate(20, 100)" opacity="0.7">
              <text x="0" y="0" fontSize="14" fill="#e2e8f0" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(80, 110)" opacity="0.6">
              <rect x="-3" y="-8" width="6" height="16" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
              <polygon points="-3,-8 0,-11 3,-8" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(45, 115)" opacity="0.6">
              <path d="M0,-7 L1.5,-1.5 L7,-1.5 L3,1.5 L4.5,7 L0,4.5 L-4.5,7 L-3,1.5 L-7,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
            </g>

            {/* Формула (π) */}
            <g transform="translate(60, 20)" opacity="0.7">
              <text x="0" y="0" fontSize="16" fill="#e2e8f0" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">π</text>
            </g>

            {/* Книга (вторая) */}
            <g transform="translate(90, 60)" opacity="0.6">
              <rect x="-8" y="-6" width="16" height="12" fill="none" stroke="#e2e8f0" strokeWidth="1.3" />
              <line x1="0" y1="-6" x2="0" y2="6" stroke="#e2e8f0" strokeWidth="1.3" />
            </g>

            {/* Панда (вторая) */}
            <g transform="translate(55, 95)" opacity="0.7">
              <circle cx="0" cy="0" r="9" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
              <circle cx="-3.5" cy="-2.5" r="1.8" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
              <circle cx="3.5" cy="-2.5" r="1.8" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
              <ellipse cx="0" cy="2.5" rx="2.5" ry="2" fill="none" stroke="#e2e8f0" strokeWidth="1.5" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePatternLight)" className="dark:hidden" />
        <rect width="100%" height="100%" fill="url(#doodlePatternDark)" className="hidden dark:block" />
      </svg>
    </div>
  );
}
