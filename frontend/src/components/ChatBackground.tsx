/**
 * Компонент фона чата с doodles в стиле Telegram
 * Doodles из предоставленных изображений
 */

// Позиции для светлой темы (светлые doodles) - в процентах от ширины/высоты
const LIGHT_DOODLES = [
  { x: 8, y: 8, type: 'pinkBlob' },
  { x: 75, y: 12, type: 'brownBlob' },
  { x: 32, y: 45, type: 'brownSteps' },
  { x: 92, y: 52, type: 'brownCrown' },
  { x: 48, y: 22, type: 'tealLoop' },
  { x: 66, y: 9, type: 'tealWave' },
  { x: 25, y: 35, type: 'tealSpring' },
  { x: 84, y: 30, type: 'tealLeaf' },
  { x: 16, y: 50, type: 'pinkDashes' },
  { x: 100, y: 40, type: 'pinkDashes2' },
  { x: 53, y: 6, type: 'whiteCircle' },
  { x: 40, y: 52, type: 'whiteCircle2' },
];

// Позиции для темной темы (белые doodles) - в процентах
const DARK_DOODLES = [
  { x: 12, y: 8, type: 'phone' },
  { x: 32, y: 14, type: 'heart' },
  { x: 53, y: 10, type: 'sadFace' },
  { x: 74, y: 17, type: 'star' },
  { x: 92, y: 13, type: 'wifi' },
  { x: 15, y: 26, type: 'airplane' },
  { x: 21, y: 25, type: 'lightbulb' },
  { x: 42, y: 21, type: 'network' },
  { x: 63, y: 24, type: 'atSymbol' },
  { x: 84, y: 28, type: 'bubbleHeart' },
  { x: 5, y: 26, type: 'happyFace' },
  { x: 16, y: 35, type: 'cloudUp' },
  { x: 37, y: 31, type: 'video' },
  { x: 58, y: 34, type: 'bubbles' },
  { x: 79, y: 38, type: 'chart' },
  { x: 100, y: 36, type: 'laughFace' },
  { x: 26, y: 44, type: 'location' },
  { x: 47, y: 41, type: 'star2' },
  { x: 68, y: 45, type: 'wifi2' },
  { x: 89, y: 43, type: 'globe' },
  { x: 10, y: 48, type: 'exclamation' },
  { x: 13, y: 53, type: 'lock' },
  { x: 34, y: 50, type: 'bubbleHeart2' },
  { x: 55, y: 54, type: 'envelope' },
  { x: 76, y: 51, type: 'bell' },
  { x: 97, y: 55, type: 'bubbleFace' },
  { x: 18, y: 60, type: 'cursor' },
  { x: 39, y: 59, type: 'pencil' },
  { x: 60, y: 63, type: 'lightning' },
  { x: 81, y: 60, type: 'megaphone' },
  { x: 2, y: 64, type: 'bubbles2' },
  { x: 29, y: 70, type: 'sadBubble' },
  { x: 50, y: 68, type: 'images' },
  { x: 71, y: 71, type: 'magnifier' },
  { x: 92, y: 69, type: 'camera' },
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
    const opacity = 0.12; // Увеличено для видимости на темном фоне

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
              d="M0,-12 L3,-3 L12,-3 L4.5,1.5 L7.5,10.5 L0,6 L-7.5,10.5 L-4.5,1.5 L-12,-3 L-3,-3 Z"
              fill="none"
              stroke={color}
              strokeWidth="1.5"
            />
          </g>
        );
      case 'wifi':
      case 'wifi2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M0,-9 Q-6,-3 -6,3" fill="none" stroke={color} strokeWidth="1.5" />
            <path d="M0,-9 Q6,-3 6,3" fill="none" stroke={color} strokeWidth="1.5" />
            <path d="M0,-4.5 Q-3,-1.5 -3,1.5" fill="none" stroke={color} strokeWidth="1.5" />
            <path d="M0,-4.5 Q3,-1.5 3,1.5" fill="none" stroke={color} strokeWidth="1.5" />
            <circle cx="0" cy="3" r="1.5" fill="none" stroke={color} strokeWidth="1.5" />
          </g>
        );
      case 'airplane':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-12,0 L0,-9 L12,0 L6,3 L0,0 L-6,3 Z" fill="none" stroke={color} strokeWidth="1.5" />
            <path d="M-9,1.5 Q-3,4.5 3,1.5" fill="none" stroke={color} strokeWidth="1.2" />
          </g>
        );
      case 'lightbulb':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <circle cx="0" cy="-4" r="4" fill="none" stroke={color} strokeWidth="1" />
            <rect x="-2" y="0" width="4" height="6" fill="none" stroke={color} strokeWidth="1" />
            <line x1="-1" y1="-6" x2="1" y2="-6" stroke={color} strokeWidth="1" />
            <path d="M-3,-2 Q-4,-3 -3,-4" fill="none" stroke={color} strokeWidth="0.8" />
            <path d="M3,-2 Q4,-3 3,-4" fill="none" stroke={color} strokeWidth="0.8" />
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
  } else {
    // Светлая тема - светлые цвета
    const pinkColor = '#f8b4cb';
    const brownColor = '#d4a574';
    const tealColor = '#2d7a7a';
    const opacity = 0.3;

    switch (type) {
      case 'pinkBlob':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M-8,-4 Q-10,-6 -8,-8 Q-6,-10 -4,-8 Q-2,-10 0,-8 Q2,-10 4,-8 Q6,-10 8,-8 Q10,-6 8,-4 Q10,-2 8,0 Q10,2 8,4 Q6,6 4,4 Q2,6 0,4 Q-2,6 -4,4 Q-6,6 -8,4 Q-10,2 -8,0 Q-10,-2 -8,-4 Z"
              fill={pinkColor}
            />
            <circle cx="-6" cy="-6" r="2" fill={tealColor} />
          </g>
        );
      case 'brownBlob':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M-6,-5 Q-8,-7 -6,-9 Q-4,-11 -2,-9 Q0,-11 2,-9 Q4,-11 6,-9 Q8,-7 6,-5 Q8,-3 6,-1 Q8,1 6,3 Q4,5 2,3 Q0,5 -2,3 Q-4,5 -6,3 Q-8,1 -6,-1 Q-8,-3 -6,-5 Z"
              fill={brownColor}
            />
          </g>
        );
      case 'brownSteps':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <rect x="-8" y="0" width="6" height="4" fill="none" stroke={brownColor} strokeWidth="1.2" />
            <rect x="-4" y="-2" width="6" height="6" fill="none" stroke={brownColor} strokeWidth="1.2" />
            <rect x="2" y="-4" width="6" height="8" fill="none" stroke={brownColor} strokeWidth="1.2" />
          </g>
        );
      case 'brownCrown':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M-6,2 L-4,-4 L-2,0 L0,-6 L2,0 L4,-4 L6,2 L4,4 L-4,4 Z"
              fill="none"
              stroke={brownColor}
              strokeWidth="1.2"
            />
          </g>
        );
      case 'tealLoop':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M-4,-6 Q-6,-4 -6,-2 Q-6,0 -4,2 Q-2,4 0,4 Q2,4 4,2 Q6,0 6,-2 Q6,-4 4,-6"
              fill="none"
              stroke={tealColor}
              strokeWidth="1"
            />
          </g>
        );
      case 'tealWave':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-8,0 Q-4,-2 0,0 Q4,2 8,0" fill="none" stroke={tealColor} strokeWidth="1" />
          </g>
        );
      case 'tealSpring':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M-6,4 Q-4,2 -2,4 Q0,2 2,4 Q4,2 6,4 Q4,6 2,4 Q0,6 -2,4 Q-4,6 -6,4"
              fill="none"
              stroke={tealColor}
              strokeWidth="1"
            />
          </g>
        );
      case 'tealLeaf':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path
              d="M0,-6 L-3,-2 L-2,2 L0,4 L2,2 L3,-2 Z"
              fill="none"
              stroke={tealColor}
              strokeWidth="1"
            />
            <line x1="-1" y1="0" x2="1" y2="0" stroke={tealColor} strokeWidth="0.8" />
            <line x1="-2" y1="-1" x2="2" y2="-1" stroke={tealColor} strokeWidth="0.8" />
          </g>
        );
      case 'pinkDashes':
      case 'pinkDashes2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity}>
            <path d="M-2,-4 Q0,-3 2,-4" fill="none" stroke={pinkColor} strokeWidth="1" />
            <path d="M-2,-2 Q0,-1 2,-2" fill="none" stroke={pinkColor} strokeWidth="1" />
            <path d="M-2,0 Q0,1 2,0" fill="none" stroke={pinkColor} strokeWidth="1" />
          </g>
        );
      case 'whiteCircle':
      case 'whiteCircle2':
        return (
          <g transform={`translate(${coordX}, ${coordY})`} opacity={opacity * 0.8}>
            <circle cx="0" cy="0" r="3" fill="#ffffff" />
          </g>
        );
      default:
        return null;
    }
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

      {/* SVG с doodles для светлой темы */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none dark:hidden"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        style={{ opacity: 0.15 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {LIGHT_DOODLES.map((pos, index) => (
          <DoodleElement key={index} x={pos.x} y={pos.y} type={pos.type} isDark={false} />
        ))}
      </svg>

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
