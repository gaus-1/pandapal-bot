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
      <div className="mx-auto w-full sm:w-[22rem] md:w-[23rem] lg:w-[24rem] max-w-[calc(100%-5.5rem)]">
        <div className="flex items-center justify-between gap-3 mb-3 sm:mb-4">
          <h3 className="font-display text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-50">
            Интерфейс Mini App
          </h3>
          <span className="text-xs sm:text-sm text-gray-500 dark:text-slate-400">
            {currentIndex + 1} / {total}
          </span>
        </div>
      </div>

      <div className="relative mx-auto w-full sm:w-[22rem] md:w-[23rem] lg:w-[24rem] max-w-[calc(100%-5.5rem)]">
        <div
          className="relative flex items-center justify-center"
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

          <div className="w-full rounded-2xl sm:rounded-3xl overflow-hidden border border-gray-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 shadow-md hover:shadow-xl dark:hover:shadow-2xl transition-all duration-300">
            <div className="relative w-full aspect-[9/16] max-h-[520px] overflow-hidden">
              <div
                className="flex h-full transition-transform duration-500 ease-out"
                style={{ transform: `translateX(-${currentIndex * 100}%)` }}
              >
                {MINIAPP_SCREENSHOTS.map((item) => (
                  <div key={item.id} className="relative h-full w-full flex-shrink-0">
                    {broken[item.id] ? (
                      <div className="w-full h-full flex flex-col items-center justify-center text-center p-5">
                        <p className="font-medium text-gray-700 dark:text-slate-200 mb-2">
                          {item.title}
                        </p>
                        <p className="text-xs sm:text-sm text-gray-500 dark:text-slate-400">
                          Добавь файл: <code>{item.src}</code>
                        </p>
                      </div>
                    ) : (
                      <img
                        src={item.src}
                        alt={item.title}
                        loading="lazy"
                        className="absolute inset-0 m-auto block max-w-full max-h-full w-auto h-auto object-contain object-center"
                        onError={() => setBroken((prev) => ({ ...prev, [item.id]: true }))}
                      />
                    )}
                  </div>
                ))}
              </div>
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
    </section>
  );
});

MiniAppScreenshotsCarousel.displayName = 'MiniAppScreenshotsCarousel';
