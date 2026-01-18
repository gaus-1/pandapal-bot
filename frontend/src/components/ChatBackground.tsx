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

      {/* SVG паттерн с doodles - по логике Telegram: черный паттерн на прозрачном, накладывается с intensity */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ opacity: 0.08 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Паттерн для светлой темы - все элементы внутри границ 80x100 */}
          <pattern id="doodlePatternLight" x="0" y="0" width="80" height="100" patternUnits="userSpaceOnUse">
            {/* Панда - левый верхний угол */}
            <g transform="translate(15, 20)" opacity="0.4">
              <circle cx="0" cy="0" r="8" fill="none" stroke="#64748b" strokeWidth="1.2" />
              <circle cx="-3" cy="-2.5" r="1.5" fill="none" stroke="#64748b" strokeWidth="1.2" />
              <circle cx="3" cy="-2.5" r="1.5" fill="none" stroke="#64748b" strokeWidth="1.2" />
              <ellipse cx="0" cy="2.5" rx="2.5" ry="2" fill="none" stroke="#64748b" strokeWidth="1.2" />
            </g>

            {/* Книга - центр верх */}
            <g transform="translate(40, 25)" opacity="0.35">
              <rect x="-6" y="-5" width="12" height="10" fill="none" stroke="#64748b" strokeWidth="1.1" />
              <line x1="0" y1="-5" x2="0" y2="5" stroke="#64748b" strokeWidth="1.1" />
            </g>

            {/* Карандаш - правый верх */}
            <g transform="translate(65, 20)" opacity="0.35">
              <rect x="-2.5" y="-7" width="5" height="14" fill="none" stroke="#64748b" strokeWidth="1.1" />
              <polygon points="-2.5,-7 0,-9 2.5,-7" fill="none" stroke="#64748b" strokeWidth="1.1" />
            </g>

            {/* Звезда - левый центр */}
            <g transform="translate(20, 50)" opacity="0.35">
              <path d="M0,-6 L1.5,-1.5 L6,-1.5 L2.5,1.5 L4,6 L0,4 L-4,6 L-2.5,1.5 L-6,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#64748b" strokeWidth="1.1" />
            </g>

            {/* Глобус - центр */}
            <g transform="translate(50, 55)" opacity="0.35">
              <circle cx="0" cy="0" r="8" fill="none" stroke="#64748b" strokeWidth="1.1" />
              <ellipse cx="0" cy="0" rx="8" ry="4" fill="none" stroke="#64748b" strokeWidth="1" />
              <line x1="-8" y1="0" x2="8" y2="0" stroke="#64748b" strokeWidth="1" />
            </g>

            {/* Формула (x²) - правый центр */}
            <g transform="translate(65, 50)" opacity="0.4">
              <text x="0" y="0" fontSize="12" fill="#64748b" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">x²</text>
            </g>

            {/* Карандаш (второй) - левый низ */}
            <g transform="translate(15, 75)" opacity="0.35">
              <rect x="-2.5" y="-7" width="5" height="14" fill="none" stroke="#64748b" strokeWidth="1.1" />
              <polygon points="-2.5,-7 0,-9 2.5,-7" fill="none" stroke="#64748b" strokeWidth="1.1" />
            </g>

            {/* Звезда (вторая) - центр низ */}
            <g transform="translate(40, 80)" opacity="0.35">
              <path d="M0,-6 L1.5,-1.5 L6,-1.5 L2.5,1.5 L4,6 L0,4 L-4,6 L-2.5,1.5 L-6,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#64748b" strokeWidth="1.1" />
            </g>

            {/* Формула (π) - правый низ */}
            <g transform="translate(65, 75)" opacity="0.4">
              <text x="0" y="0" fontSize="14" fill="#64748b" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">π</text>
            </g>

            {/* Книга (вторая) - центр */}
            <g transform="translate(50, 30)" opacity="0.35">
              <rect x="-6" y="-5" width="12" height="10" fill="none" stroke="#64748b" strokeWidth="1.1" />
              <line x1="0" y1="-5" x2="0" y2="5" stroke="#64748b" strokeWidth="1.1" />
            </g>

            {/* Панда (вторая) - правый верх */}
            <g transform="translate(65, 45)" opacity="0.4">
              <circle cx="0" cy="0" r="7" fill="none" stroke="#64748b" strokeWidth="1.2" />
              <circle cx="-3" cy="-2" r="1.3" fill="none" stroke="#64748b" strokeWidth="1.2" />
              <circle cx="3" cy="-2" r="1.3" fill="none" stroke="#64748b" strokeWidth="1.2" />
              <ellipse cx="0" cy="2" rx="2" ry="1.5" fill="none" stroke="#64748b" strokeWidth="1.2" />
            </g>
          </pattern>

          {/* Паттерн для темной темы - более светлые цвета, та же структура */}
          <pattern id="doodlePatternDark" x="0" y="0" width="80" height="100" patternUnits="userSpaceOnUse">
            {/* Панда */}
            <g transform="translate(15, 20)" opacity="0.5">
              <circle cx="0" cy="0" r="8" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
              <circle cx="-3" cy="-2.5" r="1.5" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
              <circle cx="3" cy="-2.5" r="1.5" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
              <ellipse cx="0" cy="2.5" rx="2.5" ry="2" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
            </g>

            {/* Книга */}
            <g transform="translate(40, 25)" opacity="0.45">
              <rect x="-6" y="-5" width="12" height="10" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
              <line x1="0" y1="-5" x2="0" y2="5" stroke="#cbd5e1" strokeWidth="1.1" />
            </g>

            {/* Карандаш */}
            <g transform="translate(65, 20)" opacity="0.45">
              <rect x="-2.5" y="-7" width="5" height="14" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
              <polygon points="-2.5,-7 0,-9 2.5,-7" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
            </g>

            {/* Звезда */}
            <g transform="translate(20, 50)" opacity="0.45">
              <path d="M0,-6 L1.5,-1.5 L6,-1.5 L2.5,1.5 L4,6 L0,4 L-4,6 L-2.5,1.5 L-6,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
            </g>

            {/* Глобус */}
            <g transform="translate(50, 55)" opacity="0.45">
              <circle cx="0" cy="0" r="8" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
              <ellipse cx="0" cy="0" rx="8" ry="4" fill="none" stroke="#cbd5e1" strokeWidth="1" />
              <line x1="-8" y1="0" x2="8" y2="0" stroke="#cbd5e1" strokeWidth="1" />
            </g>

            {/* Формула (x²) */}
            <g transform="translate(65, 50)" opacity="0.5">
              <text x="0" y="0" fontSize="12" fill="#cbd5e1" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(15, 75)" opacity="0.45">
              <rect x="-2.5" y="-7" width="5" height="14" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
              <polygon points="-2.5,-7 0,-9 2.5,-7" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(40, 80)" opacity="0.45">
              <path d="M0,-6 L1.5,-1.5 L6,-1.5 L2.5,1.5 L4,6 L0,4 L-4,6 L-2.5,1.5 L-6,-1.5 L-1.5,-1.5 Z" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
            </g>

            {/* Формула (π) */}
            <g transform="translate(65, 75)" opacity="0.5">
              <text x="0" y="0" fontSize="14" fill="#cbd5e1" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">π</text>
            </g>

            {/* Книга (вторая) */}
            <g transform="translate(50, 30)" opacity="0.45">
              <rect x="-6" y="-5" width="12" height="10" fill="none" stroke="#cbd5e1" strokeWidth="1.1" />
              <line x1="0" y1="-5" x2="0" y2="5" stroke="#cbd5e1" strokeWidth="1.1" />
            </g>

            {/* Панда (вторая) */}
            <g transform="translate(65, 45)" opacity="0.5">
              <circle cx="0" cy="0" r="7" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
              <circle cx="-3" cy="-2" r="1.3" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
              <circle cx="3" cy="-2" r="1.3" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
              <ellipse cx="0" cy="2" rx="2" ry="1.5" fill="none" stroke="#cbd5e1" strokeWidth="1.2" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePatternLight)" className="dark:hidden" />
        <rect width="100%" height="100%" fill="url(#doodlePatternDark)" className="hidden dark:block" />
      </svg>
    </div>
  );
}
