/**
 * Оптимизированный компонент изображения
 * Поддержка WebP/AVIF, lazy loading, responsive images
 * Соответствует стандартам производительности 2025
 *
 * @module components/OptimizedImage
 */

import React, { useState, useEffect, useRef } from 'react';

interface OptimizedImageProps {
  /** Базовый URL изображения (без расширения) */
  src: string;
  /** Альтернативный текст для доступности */
  alt: string;
  /** CSS классы */
  className?: string;
  /** Ширина изображения */
  width?: number;
  /** Высота изображения */
  height?: number;
  /** Ленивая загрузка */
  lazy?: boolean;
  /** Приоритет загрузки (для критических изображений) */
  priority?: boolean;
  /** Srcset для responsive изображений */
  srcSet?: string;
  /** Sizes для responsive изображений */
  sizes?: string;
  /** Callback при загрузке */
  onLoad?: () => void;
  /** Placeholder во время загрузки */
  placeholder?: string;
}

/**
 * Оптимизированное изображение с поддержкой современных форматов
 */
export const OptimizedImage: React.FC<OptimizedImageProps> = React.memo(({
  src,
  alt,
  className = '',
  width,
  height,
  lazy = true,
  priority = false,
  sizes,
  onLoad,
  placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect width="400" height="300" fill="%23f0f0f0"/%3E%3C/svg%3E',
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(!lazy || priority);
  const imgRef = useRef<HTMLImageElement>(null);

  // Intersection Observer для lazy loading
  useEffect(() => {
    if (!lazy || priority || isInView) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Начинаем загрузку за 50px до появления в viewport
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [lazy, priority, isInView]);

  // Определение формата изображения
  const getImageSources = () => {
    const formats = {
      avif: `${src}.avif`,
      webp: `${src}.webp`,
      jpg: `${src}.jpg`,
    };

    return formats;
  };

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const formats = getImageSources();

  return (
    <picture>
      {/* AVIF - самый современный формат */}
      {isInView && (
        <source
          type="image/avif"
          srcSet={formats.avif}
          sizes={sizes}
        />
      )}

      {/* WebP - широко поддерживаемый */}
      {isInView && (
        <source
          type="image/webp"
          srcSet={formats.webp}
          sizes={sizes}
        />
      )}

      {/* JPG - fallback */}
      <img
        ref={imgRef}
        src={isInView ? formats.jpg : placeholder}
        alt={alt}
        className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}
        width={width}
        height={height}
        loading={priority ? 'eager' : 'lazy'}
        decoding={priority ? 'sync' : 'async'}
        onLoad={handleLoad}
        style={{
          aspectRatio: width && height ? `${width} / ${height}` : undefined,
        }}
      />
    </picture>
  );
});

OptimizedImage.displayName = 'OptimizedImage';
