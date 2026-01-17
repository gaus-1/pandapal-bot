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

  const todayTime = today.getTime();
  const yesterdayTime = yesterday.getTime();
  const messageTime = messageDate.getTime();

  if (messageTime === todayTime) {
    label = 'Сегодня';
  } else if (messageTime === yesterdayTime) {
    label = 'Вчера';
  } else {
    // Форматируем дату: "15 января"
    // Используем правильную локализацию с учетом часового пояса
    const dateStr = messageDate.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      timeZone: 'Europe/Moscow', // Явно указываем часовой пояс
    });
    label = dateStr.charAt(0).toUpperCase() + dateStr.slice(1); // Первая буква заглавная
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
