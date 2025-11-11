/**
 * Тесты для security/validation модуля
 * Проверяем валидацию пользовательских данных
 * @module security/validation.test
 */

import { describe, it, expect } from 'vitest';
import {
  validateUsername,
  validateEmail,
  validateMessage,
  validateAge,
  validateGrade,
} from './validation';

describe('Security: Input Validation (OWASP A04)', () => {
  /**
   * ТЕСТ-НАБОР 1: validateUsername
   */
  describe('validateUsername', () => {
    it('должен принимать корректные имена', () => {
      const validUsernames = ['Вася', 'user123', 'test-user', 'мария_петрова'];

      validUsernames.forEach((username) => {
        const result = validateUsername(username);
        expect(result.valid).toBe(true);
        expect(result.error).toBeUndefined();
      });
    });

    it('должен отклонять слишком короткие имена', () => {
      const result = validateUsername('ab');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Минимум 3 символа');
    });

    it('должен отклонять слишком длинные имена', () => {
      const longName = 'a'.repeat(100);
      const result = validateUsername(longName);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Максимум');
    });

    it('должен отклонять пустое значение', () => {
      const result = validateUsername('');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('обязательно');
    });

    it('должен отклонять спецсимволы', () => {
      const invalidUsernames = ['user@123', 'test<script>', 'name;DROP'];

      invalidUsernames.forEach((username) => {
        const result = validateUsername(username);
        expect(result.valid).toBe(false);
      });
    });
  });

  /**
   * ТЕСТ-НАБОР 2: validateEmail
   */
  describe('validateEmail', () => {
    it('должен принимать валидные email', () => {
      const validEmails = [
        'test@example.com',
        'user.name@example.co.uk',
        'user+tag@example.com',
      ];

      validEmails.forEach((email) => {
        const result = validateEmail(email);
        expect(result.valid).toBe(true);
      });
    });

    it('должен отклонять невалидные email', () => {
      const invalidEmails = [
        '',
        'notanemail',
        '@example.com',
        'user@',
        'user @example.com',
      ];

      invalidEmails.forEach((email) => {
        const result = validateEmail(email);
        expect(result.valid).toBe(false);
      });
    });

    it('должен отклонять слишком длинные email', () => {
      const longEmail = 'a'.repeat(300) + '@example.com';
      const result = validateEmail(longEmail);
      expect(result.valid).toBe(false);
    });
  });

  /**
   * ТЕСТ-НАБОР 3: validateMessage (защита от XSS и DoS)
   */
  describe('validateMessage', () => {
    it('должен принимать обычный текст', () => {
      const result = validateMessage('Привет, как дела?');
      expect(result.valid).toBe(true);
    });

    it('должен отклонять пустые сообщения', () => {
      const result = validateMessage('   ');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('не может быть пустым');
    });

    it('должен отклонять слишком длинные сообщения', () => {
      const longMessage = 'a'.repeat(5000);
      const result = validateMessage(longMessage);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Максимум');
    });

    it('должен детектировать script-теги (XSS)', () => {
      const xssMessages = [
        '<script>alert("XSS")</script>',
        '<SCRIPT SRC=http://evil.com/xss.js></SCRIPT>',
      ];

      xssMessages.forEach((message) => {
        const result = validateMessage(message);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('опасный контент');
      });
    });

    it('должен детектировать iframe (XSS)', () => {
      const result = validateMessage('<iframe src="evil.com"></iframe>');
      expect(result.valid).toBe(false);
    });

    it('должен детектировать event handlers (XSS)', () => {
      const xssAttempts = [
        '<img src=x onerror=alert(1)>',
        '<div onclick="steal()">',
      ];

      xssAttempts.forEach((attempt) => {
        const result = validateMessage(attempt);
        expect(result.valid).toBe(false);
      });
    });

    it('должен детектировать javascript: protocol (XSS)', () => {
      const result = validateMessage('<a href="javascript:alert(1)">Click</a>');
      expect(result.valid).toBe(false);
    });
  });

  /**
   * ТЕСТ-НАБОР 4: validateAge (бизнес-логика)
   */
  describe('validateAge', () => {
    it('должен принимать возраст в диапазоне 6-18', () => {
      for (let age = 6; age <= 18; age++) {
        const result = validateAge(age);
        expect(result.valid).toBe(true);
      }
    });

    it('должен отклонять возраст младше 6', () => {
      const result = validateAge(5);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('от 6 до 18');
    });

    it('должен отклонять возраст старше 18', () => {
      const result = validateAge(19);
      expect(result.valid).toBe(false);
    });

    it('должен отклонять нецелые числа', () => {
      const result = validateAge(10.5);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('целым числом');
    });

    it('должен отклонять отрицательные значения', () => {
      const result = validateAge(-5);
      expect(result.valid).toBe(false);
    });
  });

  /**
   * ТЕСТ-НАБОР 5: validateGrade (бизнес-логика)
   */
  describe('validateGrade', () => {
    it('должен принимать классы 1-11', () => {
      for (let grade = 1; grade <= 11; grade++) {
        const result = validateGrade(grade);
        expect(result.valid).toBe(true);
      }
    });

    it('должен отклонять класс 0', () => {
      const result = validateGrade(0);
      expect(result.valid).toBe(false);
    });

    it('должен отклонять класс 12', () => {
      const result = validateGrade(12);
      expect(result.valid).toBe(false);
    });

    it('должен отклонять нецелые числа', () => {
      const result = validateGrade(5.5);
      expect(result.valid).toBe(false);
    });
  });
});
