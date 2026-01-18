/**
 * Компонент фона чата с doodles в стиле Telegram
 * Хаотичное расположение всех элементов (не паттерн)
 */

// Фиксированные хаотичные позиции для всех элементов (чтобы не менялись при рендере)
const CHAOTIC_POSITIONS = [
  // Панды (8 штук)
  { x: 45, y: 32, type: 'panda' },
  { x: 120, y: 78, type: 'panda' },
  { x: 85, y: 145, type: 'panda' },
  { x: 200, y: 95, type: 'panda' },
  { x: 280, y: 165, type: 'panda' },
  { x: 350, y: 45, type: 'panda' },
  { x: 420, y: 125, type: 'panda' },
  { x: 180, y: 210, type: 'panda' },
  // Книги (6 штук)
  { x: 75, y: 58, type: 'book' },
  { x: 150, y: 112, type: 'book' },
  { x: 250, y: 68, type: 'book' },
  { x: 320, y: 188, type: 'book' },
  { x: 95, y: 178, type: 'book' },
  { x: 380, y: 95, type: 'book' },
  // Карандаши (6 штук)
  { x: 110, y: 25, type: 'pencil' },
  { x: 195, y: 142, type: 'pencil' },
  { x: 265, y: 88, type: 'pencil' },
  { x: 340, y: 155, type: 'pencil' },
  { x: 55, y: 128, type: 'pencil' },
  { x: 400, y: 72, type: 'pencil' },
  // Звезды (6 штук)
  { x: 30, y: 85, type: 'star' },
  { x: 160, y: 48, type: 'star' },
  { x: 230, y: 135, type: 'star' },
  { x: 310, y: 75, type: 'star' },
  { x: 140, y: 195, type: 'star' },
  { x: 365, y: 138, type: 'star' },
  // Глобусы (4 штуки)
  { x: 100, y: 98, type: 'globe' },
  { x: 220, y: 175, type: 'globe' },
  { x: 300, y: 118, type: 'globe' },
  { x: 170, y: 65, type: 'globe' },
  // Формулы x² (4 штуки)
  { x: 65, y: 155, type: 'x2' },
  { x: 240, y: 42, type: 'x2' },
  { x: 330, y: 202, type: 'x2' },
  { x: 390, y: 165, type: 'x2' },
  // Формулы π (4 штуки)
  { x: 125, y: 88, type: 'pi' },
  { x: 275, y: 152, type: 'pi' },
  { x: 355, y: 58, type: 'pi' },
  { x: 210, y: 128, type: 'pi' },
];

interface DoodleElementProps {
  x: number;
  y: number;
  type: string;
  isDark: boolean;
}

function DoodleElement({ x, y, type, isDark }: DoodleElementProps) {
  const color = isDark ? '#cbd5e1' : '#64748b';
  const opacity = isDark ? 0.5 : 0.4;

  switch (type) {
    case 'panda':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity}>
          <circle cx="0" cy="0" r="8" fill="none" stroke={color} strokeWidth="1.2" />
          <circle cx="-3" cy="-2.5" r="1.5" fill="none" stroke={color} strokeWidth="1.2" />
          <circle cx="3" cy="-2.5" r="1.5" fill="none" stroke={color} strokeWidth="1.2" />
          <ellipse cx="0" cy="2.5" rx="2.5" ry="2" fill="none" stroke={color} strokeWidth="1.2" />
        </g>
      );
    case 'book':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity - 0.05}>
          <rect x="-6" y="-5" width="12" height="10" fill="none" stroke={color} strokeWidth="1.1" />
          <line x1="0" y1="-5" x2="0" y2="5" stroke={color} strokeWidth="1.1" />
        </g>
      );
    case 'pencil':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity - 0.05}>
          <rect x="-2.5" y="-7" width="5" height="14" fill="none" stroke={color} strokeWidth="1.1" />
          <polygon points="-2.5,-7 0,-9 2.5,-7" fill="none" stroke={color} strokeWidth="1.1" />
        </g>
      );
    case 'star':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity - 0.05}>
          <path
            d="M0,-6 L1.5,-1.5 L6,-1.5 L2.5,1.5 L4,6 L0,4 L-4,6 L-2.5,1.5 L-6,-1.5 L-1.5,-1.5 Z"
            fill="none"
            stroke={color}
            strokeWidth="1.1"
          />
        </g>
      );
    case 'globe':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity - 0.05}>
          <circle cx="0" cy="0" r="8" fill="none" stroke={color} strokeWidth="1.1" />
          <ellipse cx="0" cy="0" rx="8" ry="4" fill="none" stroke={color} strokeWidth="1" />
          <line x1="-8" y1="0" x2="8" y2="0" stroke={color} strokeWidth="1" />
        </g>
      );
    case 'x2':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity}>
          <text x="0" y="0" fontSize="12" fill={color} fontFamily="serif" textAnchor="middle" dominantBaseline="middle">
            x²
          </text>
        </g>
      );
    case 'pi':
      return (
        <g transform={`translate(${x}, ${y})`} opacity={opacity}>
          <text x="0" y="0" fontSize="14" fill={color} fontFamily="serif" textAnchor="middle" dominantBaseline="middle">
            π
          </text>
        </g>
      );
    default:
      return null;
  }
}

export function ChatBackground() {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden z-0"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      {/* Градиентный фон в стиле Telegram */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-white to-pink-50/50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900" />

      {/* SVG с хаотично расположенными doodles для светлой темы */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none dark:hidden"
        style={{ opacity: 0.08 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {CHAOTIC_POSITIONS.map((pos, index) => (
          <DoodleElement key={index} x={pos.x} y={pos.y} type={pos.type} isDark={false} />
        ))}
      </svg>

      {/* SVG с хаотично расположенными doodles для темной темы */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none hidden dark:block"
        style={{ opacity: 0.08 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {CHAOTIC_POSITIONS.map((pos, index) => (
          <DoodleElement key={index} x={pos.x} y={pos.y} type={pos.type} isDark={true} />
        ))}
      </svg>
    </div>
  );
}
