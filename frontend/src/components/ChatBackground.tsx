/**
 * Компонент фона чата с doodles в стиле Telegram
 * Светлая тема: мягкий пастельный градиент
 * Темная тема: doodles
 */

// Позиции для темной темы (белые doodles) - в процентах, равномерно распределены
const DARK_DOODLES = [
  { x: 10, y: 8, type: 'phone' },
  { x: 30, y: 12, type: 'heart' },
  { x: 50, y: 10, type: 'sadFace' },
  { x: 70, y: 15, type: 'star' },
  { x: 90, y: 12, type: 'wifi' },
  { x: 15, y: 25, type: 'airplane' },
  { x: 35, y: 22, type: 'lightbulb' },
  { x: 55, y: 20, type: 'network' },
  { x: 75, y: 23, type: 'atSymbol' },
  { x: 85, y: 27, type: 'bubbleHeart' },
  { x: 5, y: 24, type: 'happyFace' },
  { x: 20, y: 33, type: 'cloudUp' },
  { x: 40, y: 30, type: 'video' },
  { x: 60, y: 32, type: 'bubbles' },
  { x: 80, y: 36, type: 'chart' },
  { x: 95, y: 34, type: 'laughFace' },
  { x: 25, y: 42, type: 'location' },
  { x: 45, y: 40, type: 'star2' },
  { x: 65, y: 43, type: 'wifi2' },
  { x: 85, y: 41, type: 'globe' },
  { x: 12, y: 46, type: 'exclamation' },
  { x: 15, y: 51, type: 'lock' },
  { x: 35, y: 48, type: 'bubbleHeart2' },
  { x: 55, y: 52, type: 'envelope' },
  { x: 75, y: 49, type: 'bell' },
  { x: 92, y: 53, type: 'bubbleFace' },
  { x: 18, y: 58, type: 'cursor' },
  { x: 38, y: 57, type: 'pencil' },
  { x: 58, y: 61, type: 'lightning' },
  { x: 78, y: 58, type: 'megaphone' },
  { x: 8, y: 62, type: 'bubbles2' },
  { x: 28, y: 68, type: 'sadBubble' },
  { x: 48, y: 66, type: 'images' },
  { x: 68, y: 69, type: 'magnifier' },
  { x: 88, y: 67, type: 'camera' },
];

interface DoodleElementProps {
  x: number;
  y: number;
  type: string;
  isDark: boolean;
}

function DoodleElement({ x, y, type, isDark }: DoodleElementProps) {
  // Конвертируем проценты в координаты (предполагаем viewBox="0 0 100 100")
  const coordX = x;
  const coordY = y;

  if (isDark) {
    const color = '#ffffff';
    const opacity = 0.4; // Увеличено для видимости на темном фоне

      switch (type) {
      case 'phone':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-12" y="-18" width="24" height="30" rx="3" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="0" cy="9" r="3" fill="none" stroke={color} strokeWidth="1.5" />
            <line x1="-9" y1="-12" x2="9" y2="-12" stroke={color} strokeWidth="1.5" />
            <line x1="-6" y1="-6" x2="6" y2="-6" stroke={color} strokeWidth="1.2" />
            <line x1="-6" y1="0" x2="6" y2="0" stroke={color} strokeWidth="1.2" />
          </g>
        );
      case 'heart':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M0,2 C0,-2 -4,-4 -6,-2 C-6,-4 -8,-6 -6,-8 C-4,-8 -2,-6 0,-4 C2,-6 4,-8 6,-8 C8,-6 6,-4 6,-2 C4,-4 0,-2 0,2 Z"
              fill="none"
              stroke={color}
              strokeWidth="1"
            />
          </g>
        );
      case 'sadFace':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="0" r="15" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="-4.5" cy="-3" r="2.5" fill={color} />
            <circle cx="4.5" cy="-3" r="2.5" fill={color} />
            <path d="M-6,6 Q0,3 6,6" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="-3" cy="9" r="1.2" fill={color} />
            <circle cx="3" cy="9" r="1.2" fill={color} />
          </g>
        );
      case 'star':
      case 'star2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M0,-18 L4.5,-4.5 L18,-4.5 L6.75,2.25 L11.25,15.75 L0,9 L-11.25,15.75 L-6.75,2.25 L-18,-4.5 L-4.5,-4.5 Z"
              fill="none"
              stroke={color}
              strokeWidth="2.5"
            />
          </g>
        );
      case 'wifi':
      case 'wifi2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M0,-13.5 Q-9,-4.5 -9,4.5" fill="none" stroke={color} strokeWidth="2.5" />
            <path d="M0,-13.5 Q9,-4.5 9,4.5" fill="none" stroke={color} strokeWidth="2.5" />
            <path d="M0,-6.75 Q-4.5,-2.25 -4.5,2.25" fill="none" stroke={color} strokeWidth="2.5" />
            <path d="M0,-6.75 Q4.5,-2.25 4.5,2.25" fill="none" stroke={color} strokeWidth="2.5" />
            <circle cx="0" cy="4.5" r="2.5" fill="none" stroke={color} strokeWidth="2.5" />
          </g>
        );
      case 'airplane':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-18,0 L0,-13.5 L18,0 L9,4.5 L0,0 L-9,4.5 Z" fill="none" stroke={color} strokeWidth="2.5" />
            <path d="M-13.5,2.25 Q-4.5,6.75 4.5,2.25" fill="none" stroke={color} strokeWidth="2" />
          </g>
        );
      case 'lightbulb':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="-9" r="9" fill="none" stroke={color} strokeWidth="2.5" />
            <rect x="-4.5" y="0" width="9" height="13.5" fill="none" stroke={color} strokeWidth="2.5" />
            <line x1="-2.25" y1="-13.5" x2="2.25" y2="-13.5" stroke={color} strokeWidth="2.5" />
            <path d="M-6.75,-4.5 Q-9,-6.75 -6.75,-9" fill="none" stroke={color} strokeWidth="2" />
            <path d="M6.75,-4.5 Q9,-6.75 6.75,-9" fill="none" stroke={color} strokeWidth="2" />
          </g>
        );
      case 'network':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="-6" cy="0" r="3" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="0" cy="0" r="3" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="6" cy="0" r="3" fill="none" stroke={color} strokeWidth="1.5" />
            <line x1="-3" y1="0" x2="3" y2="0" stroke={color} strokeWidth="1.5" />
            <line x1="3" y1="0" x2="9" y2="0" stroke={color} strokeWidth="1.5" />
          </g>
        );
      case 'atSymbol':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="0" r="9" fill="none" stroke={color} strokeWidth="1.5" />
            <path d="M-3,-6 L3,-6 L3,6 L-3,6" fill="none" stroke={color} strokeWidth="1.5" />
          </g>
        );
      case 'bubbleHeart':
      case 'bubbleHeart2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M-6,-4 Q-8,-6 -6,-8 Q-4,-8 -2,-6 Q0,-8 2,-6 Q4,-8 6,-8 Q8,-6 6,-4 Q4,-2 0,2 Q-4,-2 -6,-4 Z"
              fill="none"
              stroke={color}
              strokeWidth="1"
            />
            <path d="M0,-2 Q-2,-4 -2,-6 Q-2,-8 0,-8 Q2,-8 2,-6 Q2,-4 0,-2" fill="none" stroke={color} strokeWidth="0.8" />
            <path d="M-4,0 Q-2,2 0,4 Q2,2 4,0" fill="none" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'happyFace':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="0" r="15" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="-4.5" cy="-3" r="2.5" fill={color} />
            <circle cx="4.5" cy="-3" r="2.5" fill={color} />
            <path d="M-6,6 Q0,12 6,6" fill="none" stroke={color} strokeWidth="1.5" />
          </g>
        );
      case 'cloudUp':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-6,-2 Q-8,0 -6,2 Q-4,4 0,4 Q4,4 6,2 Q8,0 6,-2" fill="none" stroke={color} strokeWidth="1" />
            <path d="M0,4 L0,8 M-2,6 L0,8 L2,6" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'video':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-8" y="-6" width="16" height="12" fill="none" stroke={color} strokeWidth="1" />
            <polygon points="-2,-3 2,0 -2,3" fill={color} />
          </g>
        );
      case 'bubbles':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <ellipse cx="-4" cy="-2" rx="5" ry="4" fill="none" stroke={color} strokeWidth="1" />
            <ellipse cx="4" cy="2" rx="5" ry="4" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="-4" cy="-2" r="1" fill={color} />
            <circle cx="4" cy="2" r="1" fill={color} />
          </g>
        );
      case 'chart':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <line x1="-6" y1="6" x2="6" y2="6" stroke={color} strokeWidth="1" />
            <line x1="-6" y1="6" x2="-6" y2="-6" stroke={color} strokeWidth="1" />
            <rect x="-5" y="2" width="2" height="4" fill="none" stroke={color} strokeWidth="1" />
            <rect x="-2" y="-1" width="2" height="7" fill="none" stroke={color} strokeWidth="1" />
            <rect x="1" y="-4" width="2" height="10" fill="none" stroke={color} strokeWidth="1" />
            <rect x="4" y="0" width="2" height="6" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'laughFace':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="0" r="10" fill="none" stroke={color} strokeWidth="1" />
            <path d="M-3,-2 Q-3,-3 -2,-3" fill="none" stroke={color} strokeWidth="1" />
            <path d="M3,-2 Q3,-3 2,-3" fill="none" stroke={color} strokeWidth="1" />
            <ellipse cx="0" cy="6" rx="4" ry="3" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'location':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M0,-8 L-4,0 L0,4 L4,0 Z" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="0" cy="-2" r="2" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'globe':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="0" r="8" fill="none" stroke={color} strokeWidth="1" />
            <ellipse cx="0" cy="0" rx="8" ry="4" fill="none" stroke={color} strokeWidth="1" />
            <line x1="-8" y1="0" x2="8" y2="0" stroke={color} strokeWidth="1" />
            <path d="M-6,-4 Q0,-2 6,-4" fill="none" stroke={color} strokeWidth="0.8" />
            <path d="M-6,4 Q0,2 6,4" fill="none" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'exclamation':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <ellipse cx="0" cy="-2" rx="5" ry="4" fill="none" stroke={color} strokeWidth="1" />
            <line x1="0" y1="2" x2="0" y2="6" stroke={color} strokeWidth="1.5" />
            <circle cx="0" cy="8" r="1" fill={color} />
          </g>
        );
      case 'lock':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-4" y="0" width="8" height="10" rx="1" fill="none" stroke={color} strokeWidth="1" />
            <path d="M-6,-2 Q-6,-4 -4,-4 L4,-4 Q6,-4 6,-2" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="0" cy="5" r="1.5" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'envelope':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-6" y="-4" width="12" height="8" fill="none" stroke={color} strokeWidth="1" />
            <path d="M-6,-4 L0,0 L6,-4" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'bell':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M0,-6 Q-4,-6 -4,-2 L-4,4 Q-4,6 -2,6 L2,6 Q4,6 4,4 L4,-2 Q4,-6 0,-6" fill="none" stroke={color} strokeWidth="1" />
            <path d="M-2,6 L0,8 L2,6" fill="none" stroke={color} strokeWidth="1" />
            <path d="M-3,2 Q-2,4 0,4 Q2,4 3,2" fill="none" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'bubbleFace':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <ellipse cx="0" cy="-2" rx="6" ry="5" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="-2" cy="-4" r="1" fill={color} />
            <circle cx="2" cy="-4" r="1" fill={color} />
            <path d="M-2,0 Q0,2 2,0" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'cursor':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M0,0 L8,-8 L6,-6 L12,-6 L12,0 L6,0 Z" fill="none" stroke={color} strokeWidth="1" />
            <line x1="4" y1="-4" x2="8" y2="0" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'pencil':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-2" y="-6" width="4" height="12" fill="none" stroke={color} strokeWidth="1" />
            <polygon points="-2,-6 0,-8 2,-6" fill="none" stroke={color} strokeWidth="1" />
            <line x1="0" y1="-6" x2="0" y2="6" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'lightning':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-2,-8 L2,-4 L-1,0 L3,8 L-1,4 L-4,0 Z" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'megaphone':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-6,-4 L-2,-6 L-2,6 L-6,4" fill="none" stroke={color} strokeWidth="1" />
            <ellipse cx="0" cy="0" rx="6" ry="5" fill="none" stroke={color} strokeWidth="1" />
            <path d="M4,0 Q6,-2 8,-2 Q8,2 6,2 Q4,2 4,0" fill="none" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'bubbles2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <ellipse cx="-3" cy="-1" rx="5" ry="4" fill="none" stroke={color} strokeWidth="1" />
            <ellipse cx="3" cy="1" rx="5" ry="4" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="-2" cy="-2" r="1" fill={color} />
            <circle cx="2" cy="0" r="1" fill={color} />
            <circle cx="4" cy="2" r="1" fill={color} />
          </g>
        );
      case 'sadBubble':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <ellipse cx="0" cy="-2" rx="6" ry="5" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="-2" cy="-4" r="1" fill={color} />
            <circle cx="2" cy="-4" r="1" fill={color} />
            <path d="M-2,0 Q0,-2 2,0" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="-1" cy="2" r="0.8" fill={color} />
            <circle cx="1" cy="2" r="0.8" fill={color} />
          </g>
        );
      case 'images':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-6" y="-4" width="8" height="6" fill="none" stroke={color} strokeWidth="1" />
            <rect x="-4" y="-2" width="8" height="6" fill="none" stroke={color} strokeWidth="1" />
            <line x1="-2" y1="-4" x2="2" y2="-2" stroke={color} strokeWidth="0.8" />
            <line x1="-2" y1="-2" x2="2" y2="0" stroke={color} strokeWidth="0.8" />
          </g>
        );
      case 'magnifier':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="0" r="6" fill="none" stroke={color} strokeWidth="1" />
            <line x1="4" y1="4" x2="10" y2="10" stroke={color} strokeWidth="1" />
          </g>
        );
      case 'camera':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-6" y="-4" width="12" height="8" rx="1" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="0" cy="0" r="3" fill="none" stroke={color} strokeWidth="1" />
            <circle cx="0" cy="0" r="1.5" fill={color} />
            <rect x="4" y="-2" width="2" height="1.5" fill="none" stroke={color} strokeWidth="1" />
          </g>
        );
      default:
        return null;
    }
  }

  // Светлая тема больше не использует doodles
  return null;
}

export function ChatBackground() {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden z-0"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      {/* Мягкий пастельный фон для светлой темы */}
      <div className="absolute inset-0 dark:hidden bg-gradient-to-br from-rose-50/40 via-pink-50/30 to-purple-50/40" />

      {/* Градиентный фон для темной темы */}
      <div className="absolute inset-0 hidden dark:block bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900" />

      {/* SVG с doodles для темной темы */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none hidden dark:block"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {DARK_DOODLES.map((pos, index) => (
          <DoodleElement key={index} x={pos.x} y={pos.y} type={pos.type} isDark={true} />
        ))}
      </svg>
    </div>
  );
}
