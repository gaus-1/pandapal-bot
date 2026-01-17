/**
 * Компонент фона чата с doodles в стиле Telegram + PandaPal
 * Градиентный фон как в Telegram, но с образовательными doodles
 */

export function ChatBackground() {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden z-0"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      {/* Градиентный фон в стиле Telegram - более насыщенный и заметный */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-100 via-white to-pink-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900" />

      {/* SVG паттерн с doodles - повторяющийся паттерн для видимости */}
      <svg
        className="absolute inset-0 w-full h-full"
        style={{ opacity: 0.3 }}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 200 300"
        preserveAspectRatio="none"
      >
        <defs>
          <pattern id="doodlePattern" x="0" y="0" width="200" height="300" patternUnits="userSpaceOnUse">
            {/* Панда */}
            <g transform="translate(30, 50)">
              <circle cx="0" cy="0" r="12" fill="#3b82f6" opacity="0.5" />
              <circle cx="-6" cy="-4" r="3" fill="#2563eb" opacity="0.6" />
              <circle cx="6" cy="-4" r="3" fill="#2563eb" opacity="0.6" />
              <ellipse cx="0" cy="4" rx="5" ry="3" fill="#3b82f6" opacity="0.5" />
            </g>

            {/* Книга */}
            <g transform="translate(80, 100)">
              <rect x="-10" y="-8" width="20" height="16" fill="none" stroke="#60a5fa" strokeWidth="2" opacity="0.6" />
              <line x1="0" y1="-8" x2="0" y2="8" stroke="#60a5fa" strokeWidth="2" opacity="0.6" />
            </g>

            {/* Карандаш */}
            <g transform="translate(140, 70)">
              <rect x="-5" y="-12" width="10" height="24" fill="#22d3ee" opacity="0.5" />
              <polygon points="-5,-12 0,-16 5,-12" fill="#06b6d4" opacity="0.6" />
            </g>

            {/* Звезда */}
            <g transform="translate(170, 120)">
              <path d="M0,-10 L2.5,-2.5 L10,-2.5 L4,3 L6,10 L0,6 L-6,10 L-4,3 L-10,-2.5 L-2.5,-2.5 Z" fill="#fbbf24" opacity="0.5" />
            </g>

            {/* Глобус */}
            <g transform="translate(50, 180)">
              <circle cx="0" cy="0" r="14" fill="none" stroke="#34d399" strokeWidth="2.5" opacity="0.6" />
              <ellipse cx="0" cy="0" rx="14" ry="7" fill="none" stroke="#34d399" strokeWidth="2" opacity="0.6" />
              <line x1="-14" y1="0" x2="14" y2="0" stroke="#34d399" strokeWidth="2" opacity="0.6" />
            </g>

            {/* Формула (x²) */}
            <g transform="translate(120, 200)">
              <text x="0" y="0" fontSize="20" fill="#a855f7" opacity="0.6" fontFamily="serif" textAnchor="middle" dominantBaseline="middle" fontWeight="bold">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(60, 250)">
              <rect x="-4" y="-10" width="8" height="20" fill="#fbbf24" opacity="0.5" />
              <polygon points="-4,-10 0,-14 4,-10" fill="#f59e0b" opacity="0.6" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(150, 270)">
              <path d="M0,-9 L2,-2 L9,-2 L3.5,2.5 L5.5,9 L0,5 L-5.5,9 L-3.5,2.5 L-9,-2 L-2,-2 Z" fill="#f472b6" opacity="0.5" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePattern)" />
      </svg>
    </div>
  );
}
