/**
 * Компонент для отображения реакции панды (веселая/грустная)
 */

interface PandaReactionProps {
  mood: 'happy' | 'sad';
  className?: string;
}

export function PandaReaction({ mood, className = '' }: PandaReactionProps) {
  const imageSrc = mood === 'happy'
    ? '/assets/panda-happy.png'
    : '/assets/panda-sad.png';

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
