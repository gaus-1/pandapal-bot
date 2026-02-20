import React from 'react';
import { MINIAPP_SCREENSHOTS } from '../config/miniapp-screenshots';

export const MiniAppScreenshotsCarousel: React.FC = React.memo(() => {
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [broken, setBroken] = React.useState<Record<number, boolean>>({});
  const touchStartX = React.useRef<number | null>(null);

  const total = MINIAPP_SCREENSHOTS.length;

  const goPrev = React.useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + total) % total);
  }, [total]);

  const goNext = React.useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % total);
  }, [total]);

  const handleTouchStart = React.useCallback((event: React.TouchEvent<HTMLDivElement>) => {
    touchStartX.current = event.touches[0].clientX;
  }, []);

  const handleTouchEnd = React.useCallback(
    (event: React.TouchEvent<HTMLDivElement>) => {
      if (touchStartX.current === null) return;
      const deltaX = event.changedTouches[0].clientX - touchStartX.current;
      touchStartX.current = null;
      if (Math.abs(deltaX) < 40) return;
      if (deltaX > 0) {
        goPrev();
      } else {
        goNext();
      }
    },
    [goNext, goPrev]
  );

  const current = MINIAPP_SCREENSHOTS[currentIndex];

  return (
    <section aria-label="Скриншоты Mini App" className="mt-8 sm:mt-10">
      <div className="rounded-2xl sm:rounded-3xl bg-white/80 dark:bg-slate-800/80 border border-gray-100 dark:border-slate-700 p-4 sm:p-5 md:p-6">
        <div className="flex items-center justify-between gap-3 mb-4">
          <h3 className="font-display text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-50">
            Интерфейс Mini App
          </h3>
          <span className="text-xs sm:text-sm text-gray-500 dark:text-slate-400">
            {currentIndex + 1} / {total}
          </span>
        </div>

        <div
          className="relative"
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          <button
            type="button"
            onClick={goPrev}
            className="absolute left-2 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-white/90 dark:bg-slate-900/85 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-white dark:hover:bg-slate-900 transition-colors"
            aria-label="Предыдущий скриншот"
          >
            ←
          </button>

          <div className="mx-11 rounded-xl overflow-hidden border border-gray-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
            <div className="aspect-[9/16] max-h-[540px]">
              {broken[current.id] ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-center p-5">
                  <p className="font-medium text-gray-700 dark:text-slate-200 mb-2">{current.title}</p>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-slate-400">
                    Добавь файл: <code>{current.src}</code>
                  </p>
                </div>
              ) : (
                <img
                  src={current.src}
                  alt={current.title}
                  loading="lazy"
                  className="w-full h-full object-contain"
                  onError={() => setBroken((prev) => ({ ...prev, [current.id]: true }))}
                />
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={goNext}
            className="absolute right-2 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-white/90 dark:bg-slate-900/85 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-white dark:hover:bg-slate-900 transition-colors"
            aria-label="Следующий скриншот"
          >
            →
          </button>
        </div>

        <p className="mt-3 text-sm text-gray-700 dark:text-slate-200 text-center">{current.title}</p>

        <div className="mt-4 flex justify-center gap-1.5">
          {MINIAPP_SCREENSHOTS.map((item, index) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setCurrentIndex(index)}
              className={`h-2 rounded-full transition-all ${
                index === currentIndex
                  ? 'w-6 bg-blue-500'
                  : 'w-2 bg-gray-300 dark:bg-slate-600 hover:bg-gray-400 dark:hover:bg-slate-500'
              }`}
              aria-label={`Открыть скриншот ${item.id}`}
            />
          ))}
        </div>
      </div>
    </section>
  );
});

MiniAppScreenshotsCarousel.displayName = 'MiniAppScreenshotsCarousel';
