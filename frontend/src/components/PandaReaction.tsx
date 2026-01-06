/**
 * Компонент для отображения реакции панды (веселая/грустная)
 */

interface PandaReactionProps {
  mood: 'happy' | 'sad';
  className?: string;
}

export function PandaReaction({ mood, className = '' }: PandaReactionProps) {
  // Vite копирует файлы из public/ в корень dist/, поэтому путь без /assets/
  // Файлы должны быть в frontend/public/panda-happy.png и frontend/public/panda-sad.png
  const imageSrc = mood === 'happy'
    ? '/panda-happy.png'
    : '/panda-sad.png';

  const altText = mood === 'happy'
    ? 'Веселая панда'
    : 'Грустная панда';

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <img
        src={imageSrc}
        alt={altText}
        className="w-full max-w-[200px] sm:max-w-[250px] md:max-w-[300px] h-auto object-contain animate-[fadeInScale_0.5s_ease-out]"
        style={{
          animation: 'fadeInScale 0.5s ease-out',
        }}
        onError={(e) => {
          // Fallback если изображение не загрузилось
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const emoji = document.createElement('div');
          emoji.textContent = mood === 'happy' ? '🐼🎉' : '🐼😔';
          emoji.className = 'text-6xl';
          target.parentElement?.appendChild(emoji);
        }}
      />
      <style>{`
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.8);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}
