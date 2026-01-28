/**
 * Компонент фона чата
 * Светлая тема: мягкий пастельный градиент
 * Темная тема: градиентный фон
 */

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
    </div>
  );
}
