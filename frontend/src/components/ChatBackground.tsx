/**
 * Компонент фона чата с doodles в стиле PandaPal
 * Сдержанный образовательный стиль с низкой opacity
 */

export function ChatBackground() {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* Градиентный фон */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50/60 via-white/85 to-pink-50/60 dark:from-slate-900/85 dark:via-slate-900/92 dark:to-slate-800/85" />

      {/* SVG паттерн с doodles */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.12] dark:opacity-[0.08]"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 400 600"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Панда */}
        <g transform="translate(50, 80)">
          <circle cx="0" cy="0" r="8" fill="currentColor" className="text-blue-500" />
          <circle cx="-4" cy="-2" r="2" fill="currentColor" className="text-blue-600" />
          <circle cx="4" cy="-2" r="2" fill="currentColor" className="text-blue-600" />
          <ellipse cx="0" cy="2" rx="3" ry="2" fill="currentColor" className="text-blue-500" />
        </g>

        {/* Книга */}
        <g transform="translate(120, 150)">
          <rect x="-6" y="-4" width="12" height="8" fill="none" stroke="currentColor" strokeWidth="1" className="text-blue-400" />
          <line x1="0" y1="-4" x2="0" y2="4" stroke="currentColor" strokeWidth="1" className="text-blue-400" />
        </g>

        {/* Карандаш */}
        <g transform="translate(200, 100)">
          <rect x="-3" y="-8" width="6" height="16" fill="currentColor" className="text-cyan-400" />
          <polygon points="-3,-8 0,-12 3,-8" fill="currentColor" className="text-cyan-500" />
        </g>

        {/* Звезда */}
        <g transform="translate(280, 180)">
          <path d="M0,-6 L1.5,-1.5 L6,-1.5 L2.5,1.5 L4,6 L0,3.5 L-4,6 L-2.5,1.5 L-6,-1.5 L-1.5,-1.5 Z" fill="currentColor" className="text-yellow-400" />
        </g>

        {/* Глобус */}
        <g transform="translate(350, 120)">
          <circle cx="0" cy="0" r="10" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-green-400" />
          <ellipse cx="0" cy="0" rx="10" ry="5" fill="none" stroke="currentColor" strokeWidth="1" className="text-green-400" />
          <line x1="-10" y1="0" x2="10" y2="0" stroke="currentColor" strokeWidth="1" className="text-green-400" />
        </g>

        {/* Формула (x²) */}
        <g transform="translate(80, 250)" className="text-purple-400">
          <text x="0" y="0" fontSize="12" fill="currentColor" fontFamily="serif">x²</text>
        </g>

        {/* Лупа */}
        <g transform="translate(180, 280)">
          <circle cx="0" cy="0" r="8" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-blue-400" />
          <line x1="5" y1="5" x2="10" y2="10" stroke="currentColor" strokeWidth="2" className="text-blue-400" />
        </g>

        {/* Сердечко */}
        <g transform="translate(250, 220)">
          <path d="M0,-3 C-2,-5 -5,-5 -5,-2 C-5,0 -2,3 0,5 C2,3 5,0 5,-2 C5,-5 2,-5 0,-3 Z" fill="currentColor" className="text-pink-400" />
        </g>

        {/* Книга (вторая) */}
        <g transform="translate(320, 300)">
          <rect x="-5" y="-3" width="10" height="6" fill="none" stroke="currentColor" strokeWidth="1" className="text-cyan-400" />
          <line x1="0" y1="-3" x2="0" y2="3" stroke="currentColor" strokeWidth="1" className="text-cyan-400" />
        </g>

        {/* Карандаш (второй) */}
        <g transform="translate(100, 380)">
          <rect x="-2" y="-6" width="4" height="12" fill="currentColor" className="text-yellow-400" />
          <polygon points="-2,-6 0,-9 2,-6" fill="currentColor" className="text-yellow-500" />
        </g>

        {/* Звезда (вторая) */}
        <g transform="translate(220, 400)">
          <path d="M0,-5 L1.2,-1.2 L5,-1.2 L2,1.2 L3.2,5 L0,3 L-3.2,5 L-2,1.2 L-5,-1.2 L-1.2,-1.2 Z" fill="currentColor" className="text-pink-400" />
        </g>

        {/* Панда (вторая) */}
        <g transform="translate(300, 450)">
          <circle cx="0" cy="0" r="7" fill="currentColor" className="text-blue-500" />
          <circle cx="-3" cy="-2" r="1.5" fill="currentColor" className="text-blue-600" />
          <circle cx="3" cy="-2" r="1.5" fill="currentColor" className="text-blue-600" />
          <ellipse cx="0" cy="2" rx="2.5" ry="1.5" fill="currentColor" className="text-blue-500" />
        </g>

        {/* Глобус (второй) */}
        <g transform="translate(150, 500)">
          <circle cx="0" cy="0" r="9" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-green-400" />
          <ellipse cx="0" cy="0" rx="9" ry="4.5" fill="none" stroke="currentColor" strokeWidth="1" className="text-green-400" />
          <line x1="-9" y1="0" x2="9" y2="0" stroke="currentColor" strokeWidth="1" className="text-green-400" />
        </g>

        {/* Формула (π) */}
        <g transform="translate(280, 550)" className="text-purple-400">
          <text x="0" y="0" fontSize="14" fill="currentColor" fontFamily="serif">π</text>
        </g>
      </svg>
    </div>
  );
}
