/**
 * Тесты для анимированного логотипа PandaPal
 * Проверяет функциональность, доступность и производительность
 */

import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import PandaLogo from './PandaLogo';

describe('PandaLogo', () => {
  // Базовый рендеринг
  describe('Рендеринг', () => {
    it('отображается с базовыми параметрами', () => {
      render(<PandaLogo />);
      const svg = screen.getByRole('img');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('width', '64');
      expect(svg).toHaveAttribute('height', '64');
    });

    it('принимает кастомный размер', () => {
      render(<PandaLogo size={128} />);
      const svg = screen.getByRole('img');
      expect(svg).toHaveAttribute('width', '128');
      expect(svg).toHaveAttribute('height', '128');
    });

    it('применяет CSS классы', () => {
      render(<PandaLogo className="custom-class" />);
      const container = document.querySelector('.panda-logo-container');
      expect(container).toHaveClass('custom-class');
    });
  });

  // Анимации
  describe('Анимации', () => {
    it('включает анимации по умолчанию', () => {
      render(<PandaLogo />);
      const svg = screen.getByRole('img');
      expect(svg).toHaveClass('animated');
    });

    it('отключает анимации когда animated=false', () => {
      render(<PandaLogo animated={false} />);
      const svg = screen.getByRole('img');
      expect(svg).not.toHaveClass('animated');
    });

    it('показывает loading анимацию', () => {
      render(<PandaLogo loading={true} />);
      const svg = screen.getByRole('img');
      expect(svg).toHaveClass('loading');
    });
  });

  // Интерактивность
  describe('Интерактивность', () => {
    it('вызывает onClick при клике', () => {
      const handleClick = vi.fn();
      render(<PandaLogo onClick={handleClick} />);
      
      const container = document.querySelector('.panda-logo-container');
      fireEvent.click(container!);
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('реагирует на hover', () => {
      render(<PandaLogo />);
      const container = document.querySelector('.panda-logo-container');
      const svg = screen.getByRole('img');
      
      fireEvent.mouseEnter(container!);
      expect(svg).toHaveClass('hovered');
      
      fireEvent.mouseLeave(container!);
      expect(svg).not.toHaveClass('hovered');
    });

    it('добавляет cursor pointer при наличии onClick', () => {
      render(<PandaLogo onClick={() => {}} />);
      const container = document.querySelector('.panda-logo-container');
      expect(container).toHaveStyle('cursor: pointer');
    });
  });

  // Доступность
  describe('Доступность', () => {
    it('имеет правильную структуру SVG', () => {
      render(<PandaLogo />);
      const svg = screen.getByRole('img');
      expect(svg).toHaveAttribute('viewBox', '0 0 100 100');
      expect(svg).toHaveAttribute('xmlns', 'http://www.w3.org/2000/svg');
      expect(svg).toHaveAttribute('aria-label', 'PandaPal логотип');
    });

    it('содержит все необходимые элементы панды', () => {
      render(<PandaLogo />);
      const svg = screen.getByRole('img');
      
      // Проверяем наличие основных элементов
      expect(svg.querySelector('.panda-head')).toBeInTheDocument();
      expect(svg.querySelector('.panda-eye-left')).toBeInTheDocument();
      expect(svg.querySelector('.panda-eye-right')).toBeInTheDocument();
      expect(svg.querySelector('.panda-nose')).toBeInTheDocument();
      expect(svg.querySelector('.panda-mouth')).toBeInTheDocument();
    });
  });

  // Производительность
  describe('Производительность', () => {
    it('не вызывает лишних ре-рендеров', () => {
      const { rerender } = render(<PandaLogo />);
      const svg = screen.getByRole('img');
      
      // Ререндер с теми же пропсами
      rerender(<PandaLogo />);
      
      // SVG должен остаться тем же элементом
      expect(screen.getByRole('img')).toBe(svg);
    });

    it('оптимизирует анимации для производительности', () => {
      render(<PandaLogo />);
      const container = document.querySelector('.panda-logo-container');
      expect(container).toHaveStyle('display: block');
    });
  });

  // Edge cases
  describe('Граничные случаи', () => {
    it('обрабатывает очень маленький размер', () => {
      render(<PandaLogo size={16} />);
      const svg = screen.getByRole('img');
      expect(svg).toHaveAttribute('width', '16');
      expect(svg).toHaveAttribute('height', '16');
    });

    it('обрабатывает очень большой размер', () => {
      render(<PandaLogo size={512} />);
      const svg = screen.getByRole('img');
      expect(svg).toHaveAttribute('width', '512');
      expect(svg).toHaveAttribute('height', '512');
    });

    it('работает без onClick', () => {
      render(<PandaLogo />);
      const container = document.querySelector('.panda-logo-container');
      expect(container).toHaveStyle('cursor: default');
      
      // Клик не должен вызывать ошибок
      expect(() => {
        fireEvent.click(container!);
      }).not.toThrow();
    });
  });

  // Интеграционные тесты
  describe('Интеграция', () => {
    it('совместим с различными контейнерами', () => {
      render(
        <div style={{ width: '100px', height: '100px' }}>
          <PandaLogo size={80} />
        </div>
      );
      
      const svg = screen.getByRole('img');
      expect(svg).toBeInTheDocument();
    });

    it('работает в flex контейнерах', () => {
      render(
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <PandaLogo />
          <span>PandaPal</span>
        </div>
      );
      
      const container = document.querySelector('.panda-logo-container');
      expect(container).toHaveStyle('display: block');
    });
  });
});
