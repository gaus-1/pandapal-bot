/**
 * Компонент для отображения реакции панды (веселая/грустная).
 * Использует panda-happy-in-game.png и panda-sad-in-game.png — только для игр
 * (2048, шашки, крестики-нолики и т.д.). Не для экрана «Моя панда».
 * size="small" — для игр, быстрая анимация и меньший размер.
 */

interface PandaReactionProps {
  mood: 'happy' | 'sad';
  className?: string;
  /** В играх — меньше размер и быстрее появление */
  size?: 'default' | 'small';
}

export function PandaReaction({ mood, className = '', size = 'default' }: PandaReactionProps) {
  const imageSrc = mood === 'happy' ? '/panda-happy-in-game.png' : '/panda-sad-in-game.png';
  const altText = mood === 'happy' ? 'Веселая панда' : 'Грустная панда';
  const isSmall = size === 'small';
  const sizeClass = isSmall
    ? 'max-w-[100px] sm:max-w-[120px]'
    : 'max-w-[200px] sm:max-w-[250px] md:max-w-[300px]';
  const animDuration = isSmall ? '0.2s' : '0.25s';

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <img
        src={imageSrc}
        alt={altText}
        className={`w-full ${sizeClass} h-auto object-contain`}
        style={{ animation: `fadeInScale ${animDuration} ease-out` }}
        loading="eager"
        fetchPriority="high"
        width={isSmall ? 120 : 300}
        height={isSmall ? 120 : 300}
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const emoji = document.createElement('div');
          emoji.textContent = mood === 'happy' ? '🐼🎉' : '🐼😔';
          emoji.className = isSmall ? 'text-4xl' : 'text-6xl';
          target.parentElement?.appendChild(emoji);
        }}
      />
      <style>{`
        @keyframes fadeInScale {
          from { opacity: 0; transform: scale(0.85); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
