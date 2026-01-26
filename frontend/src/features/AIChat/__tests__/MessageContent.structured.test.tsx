/**
 * Тесты структурирования ответов AI
 * Проверяет парсинг ответов на блоки (Определение, Ключевые свойства, и т.д.)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageContent } from '../AIChat';

describe('MessageContent - Структурирование ответов', () => {
  describe('Ответы с полной структурой', () => {
    it('должен парсить ответ с секциями: Определение, Ключевые свойства, Как это работает, Где применяется, Итог', () => {
      const structuredResponse = `Определение:
Парабола — это график квадратичной функции y = ax² + bx + c, имеющий U-образную форму.

Ключевые свойства:
- Ветви направлены вверх, если a > 0, и вниз, если a < 0
- Вершина — точка минимума или максимума
- Ось симметрии проходит через вершину

Как это работает:
1. Найди вершину по формуле x = -b/(2a)
2. Найди точки пересечения с осями
3. Построй симметричные точки
4. Соедини плавной кривой

Где применяется:
- Траектория брошенного мяча
- Форма спутниковой антенны
- Арки мостов

Итог:
Парабола — U-образная кривая, график функции y = ax².`;

      render(<MessageContent content={structuredResponse} role="ai" />);

      // Проверяем наличие заголовков секций
      expect(screen.getByText('Определение:')).toBeInTheDocument();
      expect(screen.getByText('Ключевые свойства:')).toBeInTheDocument();
      expect(screen.getByText('Как это работает:')).toBeInTheDocument();
      expect(screen.getByText('Где применяется:')).toBeInTheDocument();
      expect(screen.getByText('Итог:')).toBeInTheDocument();

      // Проверяем наличие контента
      expect(screen.getByText(/Парабола — это график квадратичной функции/)).toBeInTheDocument();
      expect(screen.getByText(/Ветви направлены вверх/)).toBeInTheDocument();
    });

    it('должен парсить ответ с частичной структурой (только некоторые секции)', () => {
      const partialResponse = `Определение:
Сила тяжести — это сила, с которой Земля притягивает все тела.

Ключевые свойства:
- Направлена вертикально вниз
- Зависит от массы тела
- Постоянна для данного места на Земле`;

      render(<MessageContent content={partialResponse} role="ai" />);

      expect(screen.getByText('Определение:')).toBeInTheDocument();
      expect(screen.getByText('Ключевые свойства:')).toBeInTheDocument();
      expect(screen.getByText(/Сила тяжести — это сила/)).toBeInTheDocument();
    });
  });

  describe('Fallback парсинг (ответы без явной структуры)', () => {
    it('должен разбивать ответ на блоки по абзацам, если нет структурированных секций', () => {
      const unstructuredResponse = `Парабола — это график квадратичной функции.

Она имеет U-образную форму и используется в различных областях.

Например, траектория брошенного мяча описывается параболой.`;

      render(<MessageContent content={unstructuredResponse} role="ai" />);

      // Проверяем что контент отображается (разбит на блоки)
      expect(screen.getByText(/Парабола — это график/)).toBeInTheDocument();
      expect(screen.getByText(/Она имеет U-образную форму/)).toBeInTheDocument();
    });

    it('должен обрабатывать ответы со списками', () => {
      const listResponse = `Свойства параболы:
- Ветви направлены вверх или вниз
- Вершина — точка экстремума
- Ось симметрии проходит через вершину`;

      render(<MessageContent content={listResponse} role="ai" />);

      // Проверяем что списки отображаются
      expect(screen.getByText(/Ветви направлены вверх или вниз/)).toBeInTheDocument();
      expect(screen.getByText(/Вершина — точка экстремума/)).toBeInTheDocument();
      expect(screen.getByText(/Ось симметрии проходит через вершину/)).toBeInTheDocument();
    });

    it('должен обрабатывать ответы с нумерованными списками', () => {
      const numberedListResponse = `Как построить параболу:
1. Найди вершину
2. Найди точки пересечения
3. Построй симметричные точки
4. Соедини кривой`;

      render(<MessageContent content={numberedListResponse} role="ai" />);

      expect(screen.getByText(/Найди вершину/)).toBeInTheDocument();
      expect(screen.getByText(/Найди точки пересечения/)).toBeInTheDocument();
      expect(screen.getByText(/Построй симметричные точки/)).toBeInTheDocument();
    });
  });

  describe('Ответы пользователя (не структурируются)', () => {
    it('должен отображать сообщения пользователя без структурирования', () => {
      const userMessage = 'Привет, помоги с математикой';

      render(<MessageContent content={userMessage} role="user" />);

      expect(screen.getByText(userMessage)).toBeInTheDocument();
      // Проверяем что нет заголовков секций
      expect(screen.queryByText('Определение:')).not.toBeInTheDocument();
    });
  });
});
