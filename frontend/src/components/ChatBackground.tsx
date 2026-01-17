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

      {/* SVG паттерн с doodles - простой и видимый */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ opacity: 0.4 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="doodlePattern" x="0" y="0" width="150" height="200" patternUnits="userSpaceOnUse">
            {/* Панда */}
            <g transform="translate(25, 40)">
              <circle cx="0" cy="0" r="14" fill="#3b82f6" opacity="0.7" />
              <circle cx="-7" cy="-5" r="3.5" fill="#2563eb" opacity="0.8" />
              <circle cx="7" cy="-5" r="3.5" fill="#2563eb" opacity="0.8" />
              <ellipse cx="0" cy="5" rx="6" ry="4" fill="#3b82f6" opacity="0.7" />
            </g>

            {/* Книга */}
            <g transform="translate(70, 80)">
              <rect x="-12" y="-10" width="24" height="20" fill="none" stroke="#60a5fa" strokeWidth="2.5" opacity="0.7" />
              <line x1="0" y1="-10" x2="0" y2="10" stroke="#60a5fa" strokeWidth="2.5" opacity="0.7" />
            </g>

            {/* Карандаш */}
            <g transform="translate(120, 60)">
              <rect x="-6" y="-14" width="12" height="28" fill="#22d3ee" opacity="0.6" />
              <polygon points="-6,-14 0,-18 6,-14" fill="#06b6d4" opacity="0.7" />
            </g>

            {/* Звезда */}
            <g transform="translate(40, 140)">
              <path d="M0,-12 L3,-3 L12,-3 L4.5,3 L7.5,12 L0,8 L-7.5,12 L-4.5,3 L-12,-3 L-3,-3 Z" fill="#fbbf24" opacity="0.6" />
            </g>

            {/* Глобус */}
            <g transform="translate(100, 150)">
              <circle cx="0" cy="0" r="16" fill="none" stroke="#34d399" strokeWidth="3" opacity="0.7" />
              <ellipse cx="0" cy="0" rx="16" ry="8" fill="none" stroke="#34d399" strokeWidth="2.5" opacity="0.7" />
              <line x1="-16" y1="0" x2="16" y2="0" stroke="#34d399" strokeWidth="2.5" opacity="0.7" />
            </g>

            {/* Формула (x²) */}
            <g transform="translate(30, 180)">
              <text x="0" y="0" fontSize="24" fill="#a855f7" opacity="0.7" fontFamily="serif" textAnchor="middle" dominantBaseline="middle" fontWeight="bold">x²</text>
            </g>

            {/* Карандаш (второй) */}
            <g transform="translate(110, 200)">
              <rect x="-5" y="-12" width="10" height="24" fill="#fbbf24" opacity="0.6" />
              <polygon points="-5,-12 0,-16 5,-12" fill="#f59e0b" opacity="0.7" />
            </g>

            {/* Звезда (вторая) */}
            <g transform="translate(50, 240)">
              <path d="M0,-11 L2.5,-2.5 L11,-2.5 L4,3.5 L6.5,11 L0,7 L-6.5,11 L-4,3.5 L-11,-2.5 L-2.5,-2.5 Z" fill="#f472b6" opacity="0.6" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#doodlePattern)" />
      </svg>
    </div>
  );
}
