/**
 * Реакция панды в чате (фидбек пользователя).
 * Только 4 состояния: happy, eating, offended, questioning.
 * Отдельно от PandaReaction (игры: победа/поражение).
 */

import type { PandaChatReactionType } from '../hooks/useChat';

interface PandaChatReactionProps {
  reaction: PandaChatReactionType;
  className?: string;
}

export function PandaChatReaction({ reaction, className = '' }: PandaChatReactionProps) {
  const src = `/panda-chat-reactions/panda-${reaction}.png`;
  return (
    <img
      src={src}
      alt="Панда"
      className={`max-w-[140px] sm:max-w-[160px] md:max-w-[180px] h-auto object-contain rounded-xl shadow-md mb-2 ${className}`}
      loading="lazy"
    />
  );
}
