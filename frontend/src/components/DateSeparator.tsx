/**
 * Компонент отсечки даты для группировки сообщений в чате
 * Показывает "Сегодня", "Вчера" или конкретную дату
 */

interface DateSeparatorProps {
  date: Date;
}

export function DateSeparator({ date }: DateSeparatorProps) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const messageDate = new Date(date);
  messageDate.setHours(0, 0, 0, 0);

  let label: string;

  if (messageDate.getTime() === today.getTime()) {
    label = 'Сегодня';
  } else if (messageDate.getTime() === yesterday.getTime()) {
    label = 'Вчера';
  } else {
    // Форматируем дату: "15 января"
    label = messageDate.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
    });
  }

  return (
    <div className="flex items-center justify-center my-4">
      <div className="px-3 py-1.5 rounded-full bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-gray-200/50 dark:border-slate-700/50 shadow-sm">
        <span className="text-xs sm:text-sm font-medium text-gray-600 dark:text-slate-400">
          {label}
        </span>
      </div>
    </div>
  );
}
