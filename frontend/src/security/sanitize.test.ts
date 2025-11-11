/**
 * Тесты для security/sanitize модуля
 * Проверяем защиту от OWASP A03:2021 - Injection
 * @module security/sanitize.test
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  sanitizeInput,
  isValidEmail,
  isValidURL,
  sanitizeQueryParam,
  detectSQLInjection,
  RateLimiter,
} from './sanitize';

describe('Security: Input Sanitization (OWASP A03)', () => {
  /**
   * ТЕСТ-НАБОР 1: sanitizeInput (защита от XSS)
   */
  describe('sanitizeInput', () => {
    it('должен экранировать HTML теги', () => {
      const input = '<script>alert("XSS")</script>';
      const result = sanitizeInput(input);

      expect(result).toBe('&lt;script&gt;alert(&quot;XSS&quot;)&lt;&#x2F;script&gt;');
      expect(result).not.toContain('<script>');
    });

    it('должен экранировать кавычки', () => {
      const input = 'He said "Hello" and she said \'Hi\'';
      const result = sanitizeInput(input);

      expect(result).toContain('&quot;');
      expect(result).toContain('&#x27;');
    });

    it('должен экранировать амперсанды', () => {
      const input = 'Tom & Jerry';
      const result = sanitizeInput(input);

      expect(result).toBe('Tom &amp; Jerry');
    });

    it('должен обрабатывать пустую строку', () => {
      expect(sanitizeInput('')).toBe('');
    });

    it('должен обрабатывать сложные XSS-паттерны', () => {
      const xssAttempts = [
        '<img src=x onerror=alert("XSS")>',
        '<svg onload=alert("XSS")>',
        'javascript:alert("XSS")',
        '<iframe src="evil.com"></iframe>',
      ];

      xssAttempts.forEach((attempt) => {
        const result = sanitizeInput(attempt);
        expect(result).not.toContain('<');
        expect(result).not.toContain('>');
      });
    });
  });

  /**
   * ТЕСТ-НАБОР 2: isValidEmail
   */
  describe('isValidEmail', () => {
    it('должен валидировать корректные email', () => {
      const validEmails = [
        'test@example.com',
        'user.name@example.co.uk',
        'user+tag@example.com',
      ];

      validEmails.forEach((email) => {
        expect(isValidEmail(email)).toBe(true);
      });
    });

    it('должен отклонять некорректные email', () => {
      const invalidEmails = [
        '',
        'notanemail',
        '@example.com',
        'user@',
        'user @example.com',
        'a'.repeat(255) + '@example.com', // Слишком длинный
      ];

      invalidEmails.forEach((email) => {
        expect(isValidEmail(email)).toBe(false);
      });
    });
  });

  /**
   * ТЕСТ-НАБОР 3: isValidURL (защита от Open Redirect - OWASP A01)
   */
  describe('isValidURL', () => {
    it('должен разрешать безопасные URL', () => {
      const safeUrls = [
        'https://pandapal.ru/page',
        'https://www.pandapal.ru',
        'https://t.me/PandaPalBot',
      ];

      safeUrls.forEach((url) => {
        expect(isValidURL(url)).toBe(true);
      });
    });

    it('должен блокировать HTTP (только HTTPS)', () => {
      expect(isValidURL('http://pandapal.ru')).toBe(false);
    });

    it('должен блокировать неразрешённые домены', () => {
      const maliciousUrls = [
        'https://evil.com',
        'https://pandapal.ru.evil.com', // Поддомен зла
        'https://pandapalru.com', // Опечатка
      ];

      maliciousUrls.forEach((url) => {
        expect(isValidURL(url)).toBe(false);
      });
    });

    it('должен обрабатывать некорректные URL', () => {
      expect(isValidURL('not-a-url')).toBe(false);
      expect(isValidURL('javascript:alert("XSS")')).toBe(false);
    });
  });

  /**
   * ТЕСТ-НАБОР 4: sanitizeQueryParam (защита от SQL Injection)
   */
  describe('sanitizeQueryParam', () => {
    it('должен удалять опасные символы', () => {
      const dangerous = "'; DROP TABLE users; --";
      const result = sanitizeQueryParam(dangerous);

      expect(result).not.toContain("'");
      expect(result).not.toContain(';');
      expect(result).not.toContain('-');
    });

    it('должен оставлять безопасные символы', () => {
      const safe = 'user123_testname';
      const result = sanitizeQueryParam(safe);

      expect(result).toBe(safe);
    });
  });

  /**
   * ТЕСТ-НАБОР 5: detectSQLInjection
   */
  describe('detectSQLInjection', () => {
    it('должен детектировать SQL Injection попытки', () => {
      const sqlInjections = [
        "' OR '1'='1",
        'SELECT * FROM users',
        '1; DROP TABLE users; --',
        'UNION SELECT password FROM admin',
        "admin'--",
      ];

      sqlInjections.forEach((injection) => {
        expect(detectSQLInjection(injection)).toBe(true);
      });
    });

    it('должен пропускать безопасные строки', () => {
      const safeInputs = [
        'Привет, мир!',
        'Моё имя Вася',
        '123456',
        'user@example.com',
      ];

      safeInputs.forEach((input) => {
        expect(detectSQLInjection(input)).toBe(false);
      });
    });
  });

  /**
   * ТЕСТ-НАБОР 6: RateLimiter (защита от Brute Force - OWASP A04)
   */
  describe('RateLimiter', () => {
    let limiter: RateLimiter;

    beforeEach(() => {
      limiter = new RateLimiter();
    });

    it('должен разрешать запросы в пределах лимита', () => {
      const key = 'user123';

      // Первые 5 запросов должны пройти
      for (let i = 0; i < 5; i++) {
        expect(limiter.checkLimit(key, 5, 60000)).toBe(true);
      }
    });

    it('должен блокировать запросы при превышении лимита', () => {
      const key = 'user456';

      // Делаем 5 запросов
      for (let i = 0; i < 5; i++) {
        limiter.checkLimit(key, 5, 60000);
      }

      // 6-й запрос должен быть заблокирован
      expect(limiter.checkLimit(key, 5, 60000)).toBe(false);
    });

    it('должен сбрасывать счётчик после истечения окна', () => {
      const key = 'user789';

      // Делаем 5 запросов с окном 100ms
      for (let i = 0; i < 5; i++) {
        limiter.checkLimit(key, 5, 100);
      }

      // Ждём 150ms (окно истекло)
      return new Promise((resolve) => {
        setTimeout(() => {
          // Новый запрос должен пройти
          expect(limiter.checkLimit(key, 5, 100)).toBe(true);
          resolve(true);
        }, 150);
      });
    });

    it('должен изолировать лимиты для разных пользователей', () => {
      const user1 = 'alice';
      const user2 = 'bob';

      // Блокируем user1
      for (let i = 0; i < 6; i++) {
        limiter.checkLimit(user1, 5, 60000);
      }

      // user2 не должен быть заблокирован
      expect(limiter.checkLimit(user2, 5, 60000)).toBe(true);
    });

    it('должен очищать историю запросов', () => {
      const key = 'user-clear';

      // Блокируем пользователя
      for (let i = 0; i < 6; i++) {
        limiter.checkLimit(key, 5, 60000);
      }

      // Очищаем
      limiter.clear(key);

      // Должен снова разрешить запросы
      expect(limiter.checkLimit(key, 5, 60000)).toBe(true);
    });
  });
});
