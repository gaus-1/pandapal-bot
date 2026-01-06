/**
 * Тесты для EmergencyScreen
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EmergencyScreen } from '../EmergencyScreen';
import { telegram } from '../../../services/telegram';

vi.mock('../../../services/telegram');

describe('EmergencyScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(telegram.showConfirm).mockResolvedValue(true);
    vi.mocked(telegram.hapticFeedback).mockImplementation(() => {});
    vi.mocked(telegram.notifySuccess).mockImplementation(() => {});

    // Mock window.location.href
    delete (window as { location?: { href: string } }).location;
    (window as { location: { href: string } }).location = { href: '' };
  });

  it('отображает все экстренные номера', async () => {
    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText('🚨 Экстренные номера')).toBeInTheDocument();
    });

    // Проверяем наличие всех номеров
    expect(screen.getByText(/112/)).toBeInTheDocument();
    expect(screen.getByText(/101/)).toBeInTheDocument();
    expect(screen.getByText(/102/)).toBeInTheDocument();
    expect(screen.getByText(/103/)).toBeInTheDocument();
    expect(screen.getByText(/8-800-2000-122/)).toBeInTheDocument();
  });

  it('показывает подтверждение перед звонком', async () => {
    const user = userEvent.setup();
    vi.mocked(telegram.showConfirm).mockResolvedValue(true);

    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText(/112/)).toBeInTheDocument();
    });

    const callButton = screen.getByLabelText(/Позвонить в Единая служба спасения: 112/);
    await user.click(callButton);

    await waitFor(() => {
      expect(telegram.showConfirm).toHaveBeenCalledWith(
        expect.stringContaining('112')
      );
    });
  });

  it('совершает звонок при подтверждении', async () => {
    const user = userEvent.setup();
    vi.mocked(telegram.showConfirm).mockResolvedValue(true);

    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText(/112/)).toBeInTheDocument();
    });

    const callButton = screen.getByLabelText(/Позвонить в Единая служба спасения: 112/);
    await user.click(callButton);

    await waitFor(() => {
      expect(telegram.showConfirm).toHaveBeenCalled();
      expect(window.location.href).toBe('tel:112');
      expect(telegram.notifySuccess).toHaveBeenCalled();
    });
  });

  it('не звонит при отмене подтверждения', async () => {
    const user = userEvent.setup();
    vi.mocked(telegram.showConfirm).mockResolvedValue(false);

    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText(/112/)).toBeInTheDocument();
    });

    const callButton = screen.getByLabelText(/Позвонить в Единая служба спасения: 112/);
    await user.click(callButton);

    await waitFor(() => {
      expect(telegram.showConfirm).toHaveBeenCalled();
    });

    // Не должно быть звонка
    expect(window.location.href).toBe('');
    expect(telegram.notifySuccess).not.toHaveBeenCalled();
  });

  it('вызывает haptic feedback при клике на кнопку', async () => {
    const user = userEvent.setup();
    vi.mocked(telegram.showConfirm).mockResolvedValue(false);

    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText(/112/)).toBeInTheDocument();
    });

    const callButton = screen.getByLabelText(/Позвонить в Единая служба спасения: 112/);
    await user.click(callButton);

    await waitFor(() => {
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('heavy');
    });
  });

  it('отображает правильные номера для всех служб', async () => {
    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText('Единая служба спасения')).toBeInTheDocument();
      expect(screen.getByText('Пожарная служба МЧС')).toBeInTheDocument();
      expect(screen.getByText('Полиция')).toBeInTheDocument();
      expect(screen.getByText('Скорая помощь')).toBeInTheDocument();
      expect(screen.getByText('Детский телефон доверия')).toBeInTheDocument();
    });
  });

  it('отображает информацию о том, когда звонить', async () => {
    render(<EmergencyScreen />);

    await waitFor(() => {
      expect(screen.getByText('Звони, если:')).toBeInTheDocument();
    });
  });
});
