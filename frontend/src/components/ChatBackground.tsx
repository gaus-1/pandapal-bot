/**
 * Компонент фона чата с doodles в стиле Telegram + PandaPal
 * Градиентный фон как в Telegram, но с образовательными doodles
 */

export function ChatBackground() {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* Градиентный фон в стиле Telegram - более насыщенный и заметный */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-100 via-white to-pink-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900" />

      {/* SVG паттерн с doodles - повторяющийся паттерн для видимости */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.25] dark:opacity-[0.2]"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 200 300"
        preserveAspectRatio="none"
      >
        <defs>
          <pattern id="doodlePattern" x="0" y="0" width="200" height="300" patternUnits="userSpaceOnUse">
            {/* Панда */}
            <g transform="translate(30, 50)">
              <circle cx="0" cy="0" r="10" fill="#3b82f6" opacity="0.3" />
              <circle cx="-5" cy="-3" r="2.5" fill="#2563eb" opacity="0.4" />
              <circle cx="5" cy="-3" r="2.5" fill="#2563eb" opacity="0.4" />
              <ellipse cx="0" cy="3" rx="4" ry="2.5" fill="#3b82f6" opacity="0.3" />
            </g>

            {/* Книга */}
            <g transform="translate(80, 100)">
              <rect x="-8" y="-6" width="16" height="12" fill="none" stroke="#60a5fa" strokeWidth="1.5" opacity="0.4" />
              <line x1="0" y1="-6" x2="0" y2="6" stroke="#60a5fa" strokeWidth="1.5" opacity="0.4" />
            </g>

            {/* Карандаш */}
            <g transform="translate(140, 70)">
              <rect x="-4" y="-10" width="8" height="20" fill="#22d3ee" opacity="0.35" />
              <polygon points="-4,-10 0,-14 4,-10" fill="#06b6d4" opacity="0.4" />
            </g>

            {/* Звезда */}
            <g transform="translate(170, 120)">
              <path d="M0,-8 L2,-2 L8,-2 L3,2 L5,8 L0,5 L-5,8 L-3,2 L-8,-2 L-2,-2 Z" fill="#fbbf24" opacity="0.35" />
            </g>

            {/* Глобус */}
            <g transform="translate(50, 180)">
              <circle cx="0" cy="0" r="12" fill="none" stroke="#34d399" strokeWidth="2" opacity="0.4" />
              <ellipse cx="0" cy="0" rx="12" ry="6" fill="none" stroke="#34d399" strokeWidth="1.5" opacity="0.4" />
              <line x1="-12" y1="0" x2="12" y2="0" stroke="#34d399" strokeWidth="1.5" opacity="0.4" />
            </g>

            {/* Формула (x²) */}
            <g transform="translate(120, 200)">
              <text x="0" y="0" fontSize="16" fill="#a855f7" opacity="0.4" fontFamily="serif" textAnchor="middle" dominantBaseline="middle">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(60, 250)">
              <rect x="-3" y="-8" width="6" height="16" fill="#fbbf24" opacity="0.35" />
              <polygon points="-3,-8 0,-12 3,-8" fill="#f59e0b" opacity="0.4" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(150, 270)">
              <path d="M0,-7 L1.5,-1.5 L7,-1.5 L2.5,2 L4,7 L0,4 L-4,7 L-2.5,2 L-7,-1.5 L-1.5,-1.5 Z" fill="#f472b6" opacity="0.35" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePattern)" />
      </svg>
    </div>
  );
}
