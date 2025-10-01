import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TelegramQR } from './TelegramQR';
import { SITE_CONFIG } from '../config/constants';

describe('TelegramQR Component', () => {
  it('должен отображать заголовок', () => {
    render(<TelegramQR />);
    expect(screen.getByText(/Начни общение прямо сейчас!/i)).toBeInTheDocument();
  });

  it('должен отображать QR-код', () => {
    render(<TelegramQR />);
    const qrImage = screen.getByAlt(/QR-код для Telegram бота PandaPal/i);
    expect(qrImage).toBeInTheDocument();
    expect(qrImage).toHaveAttribute('src');
  });

  it('должен содержать кнопку "Открыть в Telegram"', () => {
    render(<TelegramQR />);
    const button = screen.getByRole('button', { name: /Открыть PandaPal бота в Telegram/i });
    expect(button).toBeInTheDocument();
  });

  it('должен открывать бота при клике на кнопку', () => {
    const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    
    render(<TelegramQR />);
    const button = screen.getByRole('button', { name: /Открыть PandaPal бота в Telegram/i });
    
    fireEvent.click(button);
    
    expect(windowOpenSpy).toHaveBeenCalledWith(
      SITE_CONFIG.botUrl,
      '_blank',
      'noopener,noreferrer'
    );
    
    windowOpenSpy.mockRestore();
  });

  it('должен отображать 3 информационных блока', () => {
    render(<TelegramQR />);
    expect(screen.getByText(/Быстрый старт/i)).toBeInTheDocument();
    expect(screen.getByText(/Безопасно/i)).toBeInTheDocument();
    expect(screen.getByText(/Бесплатно/i)).toBeInTheDocument();
  });

  it('QR-код должен быть lazy-loaded', () => {
    render(<TelegramQR />);
    const qrImage = screen.getByAlt(/QR-код для Telegram бота PandaPal/i);
    expect(qrImage).toHaveAttribute('loading', 'lazy');
  });
});

