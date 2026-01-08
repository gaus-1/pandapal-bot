/**
 * Утилита для тактильной обратной связи
 * Вынесена из AIChat.tsx для соответствия SOLID (DRY принцип)
 *
 * Обёртка над telegram.hapticFeedback для единообразия использования
 */

import { telegram } from '../services/telegram';

export type HapticStyle = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft';

/**
 * Вызвать тактильную обратную связь
 */
export function hapticFeedback(style: HapticStyle = 'medium'): void {
  telegram.hapticFeedback(style);
}

/**
 * Предопределённые методы для разных действий
 */
export const haptic = {
  light: () => hapticFeedback('light'),
  medium: () => hapticFeedback('medium'),
  heavy: () => hapticFeedback('heavy'),
  success: () => telegram.notifySuccess(),
  error: () => telegram.notifyError(),
  warning: () => telegram.notifyWarning(),
} as const;
