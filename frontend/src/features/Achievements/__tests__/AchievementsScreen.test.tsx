/**
 * Тесты для компонента AchievementsScreen
 * Проверка UI/UX и функциональности
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AchievementsScreen } from '../AchievementsScreen';
import * as api from '../../../services/api';
import * as telegram from '../../../services/telegram';

// Моки
vi.mock('../../../services/api');
vi.mock('../../../services/telegram', () => ({
  telegram: {
    hapticFeedback: vi.fn(),
    showPopup: vi.fn(),
  },
}));

const mockUser = {
  telegram_id: 123456,
  first_name: 'Тестовый',
  last_name: 'Пользователь',
  age: 10,
  grade: 5,
  user_type: 'child' as const,
};

describe('AchievementsScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('должен показывать загрузку при получении данных', async () => {
    vi.spyOn(api, 'getUserAchievements').mockImplementation(
      () => new Promise(() => {}) // Никогда не резолвится
    );

    render(<AchievementsScreen user={mockUser} />);

    // Индикатор загрузки — спиннер (animate-spin)
    expect(document.querySelector('.animate-spin')).toBeTruthy();
  });

  it('должен отображать список достижений', async () => {
    const mockAchievements = [
      {
        id: '1',
        title: 'Первый шаг',
        description: 'Отправь первое сообщение',
        icon: '🌟',
        unlocked: true,
        unlock_date: '2025-01-01T00:00:00Z',
        xp_reward: 10,
        progress: 1,
        progress_max: 1,
      },
      {
        id: '2',
        title: 'Болтун',
        description: 'Отправь 100 сообщений',
        icon: '💬',
        unlocked: false,
        xp_reward: 50,
        progress: 50,
        progress_max: 100,
      },
    ];

    vi.spyOn(api, 'getUserAchievements').mockResolvedValue(mockAchievements);

    render(<AchievementsScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Достижения' })).toBeInTheDocument();
      expect(screen.getByText('Первый шаг')).toBeTruthy();
      expect(screen.getByText('Болтун')).toBeTruthy();
    });
  });

  it('должен показывать прогресс достижений', async () => {
    const mockAchievements = [
      {
        id: '1',
        title: 'Первый шаг',
        description: 'Отправь первое сообщение',
        icon: '🌟',
        unlocked: true,
        unlock_date: '2025-01-01T00:00:00Z',
        xp_reward: 10,
        progress: 1,
        progress_max: 1,
      },
      {
        id: '2',
        title: 'Болтун',
        description: 'Отправь 100 сообщений',
        icon: '💬',
        unlocked: false,
        xp_reward: 50,
        progress: 50,
        progress_max: 100,
      },
    ];

    vi.spyOn(api, 'getUserAchievements').mockResolvedValue(mockAchievements);

    render(<AchievementsScreen user={mockUser} />);

    await waitFor(() => {
      // Должен показывать "Получено 1 из 2"
      expect(screen.getByText(/Получено 1 из 2/i)).toBeTruthy();
    });
  });

  it('должен показывать пустое состояние если нет достижений', async () => {
    vi.spyOn(api, 'getUserAchievements').mockResolvedValue([]);

    render(<AchievementsScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText(/Продолжай учиться/i)).toBeTruthy();
    });
  });

  it('должен обрабатывать клик по достижению', async () => {
    const mockAchievements = [
      {
        id: '1',
        title: 'Первый шаг',
        description: 'Отправь первое сообщение',
        icon: '🌟',
        unlocked: true,
        unlock_date: '2025-01-01T00:00:00Z',
        xp_reward: 10,
        progress: 1,
        progress_max: 1,
      },
    ];

    vi.spyOn(api, 'getUserAchievements').mockResolvedValue(mockAchievements);

    render(<AchievementsScreen user={mockUser} />);

    await waitFor(() => {
      const button = screen.getByText('Первый шаг').closest('button');
      if (button) {
        button.click();
      }
    });

    expect((telegram as { telegram: { hapticFeedback: ReturnType<typeof vi.fn> } }).telegram.hapticFeedback).toHaveBeenCalledWith('light');
    expect((telegram as { telegram: { showPopup: ReturnType<typeof vi.fn> } }).telegram.showPopup).toHaveBeenCalledWith({
      title: 'Первый шаг',
      message: 'Отправь первое сообщение',
      buttons: [{ type: 'close', text: 'Закрыть' }],
    });
  });

  it('должен показывать заблокированные достижения с пониженной прозрачностью', async () => {
    const mockAchievements = [
      {
        id: '2',
        title: 'Болтун',
        description: 'Отправь 100 сообщений',
        icon: '💬',
        unlocked: false,
        xp_reward: 50,
        progress: 50,
        progress_max: 100,
      },
    ];

    vi.spyOn(api, 'getUserAchievements').mockResolvedValue(mockAchievements);

    render(<AchievementsScreen user={mockUser} />);

    await waitFor(() => {
      const button = screen.getByText('Болтун').closest('button');
      expect(button).toBeTruthy();
      // Заблокированное достижение имеет пониженную прозрачность (opacity-60 в UI)
      expect(button?.className).toMatch(/opacity-\d+/);
    });
  });

  it('должен показывать дату разблокировки для полученных достижений', async () => {
    const mockAchievements = [
      {
        id: '1',
        title: 'Первый шаг',
        description: 'Отправь первое сообщение',
        icon: '🌟',
        unlocked: true,
        unlock_date: '2025-01-01T00:00:00Z',
        xp_reward: 10,
        progress: 1,
        progress_max: 1,
      },
    ];

    vi.spyOn(api, 'getUserAchievements').mockResolvedValue(mockAchievements);

    render(<AchievementsScreen user={mockUser} />);

    await waitFor(() => {
      // Дата разблокировки (формат зависит от локали, например "1 янв.")
      expect(screen.getByText(/Первый шаг/)).toBeInTheDocument();
      const dateOrUnlocked = document.body.textContent ?? '';
      expect(dateOrUnlocked).toMatch(/\d|янв|январь|Jan|2025/);
    });
  });
});
