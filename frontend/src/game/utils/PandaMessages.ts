/**
 * Сообщения панды для подбадривания детей
 * После каждого уровня панда пишет что-то мотивирующее
 */

export class PandaMessages {
  /**
   * Сообщения для уровня 1 (Спортзал)
   */
  private static readonly LEVEL_1_MESSAGES = [
    'Отлично! Ты разложил весь спортинвентарь! 🏀',
    'Молодец! Спортзал теперь в порядке! 💪',
    'Здорово! Ты отлично справился с первым уровнем! ⭐',
  ];

  /**
   * Сообщения для уровня 2 (Класс)
   */
  private static readonly LEVEL_2_MESSAGES = [
    'Супер! Все примеры решены правильно! 📐',
    'Умница! Доска чистая, задачи выполнены! ✨',
    'Великолепно! Ты настоящий математик! 🎓',
  ];

  /**
   * Сообщения для уровня 3 (Столовая)
   */
  private static readonly LEVEL_3_MESSAGES = [
    'Ура! Полезный обед собран! 🍎',
    'Отлично! Теперь можно подкрепиться! 🥗',
    'Молодец! Ты выбрал самую полезную еду! 🥕',
  ];

  /**
   * Сообщения для уровня 4 (Двор)
   */
  private static readonly LEVEL_4_MESSAGES = [
    'Браво! Двор чист и убран! 🌳',
    'Замечательно! Все игрушки на месте! 🎈',
    'Отлично поработал! Можно идти играть! ⚽',
  ];

  /**
   * Сообщения для уровня 5 (Библиотека)
   */
  private static readonly LEVEL_5_MESSAGES = [
    'Невероятно! Все книги разложены! 📚',
    'Потрясающе! Ты прошёл все уровни! 🎊',
    'Ты ГЕРОЙ! Библиотека в идеальном порядке! 🏆',
  ];

  /**
   * Финальное сообщение победы
   */
  private static readonly VICTORY_MESSAGE =
    'ПОЗДРАВЛЯЮ! 🎉\nТы прошёл ВСЕ уровни!\nТы настоящий ЧЕМПИОН! 🏆';

  /**
   * Получить случайное сообщение для уровня
   */
  static getLevelMessage(level: number): string {
    const messages = [
      this.LEVEL_1_MESSAGES,
      this.LEVEL_2_MESSAGES,
      this.LEVEL_3_MESSAGES,
      this.LEVEL_4_MESSAGES,
      this.LEVEL_5_MESSAGES,
    ];

    const levelMessages = messages[level];
    if (!levelMessages) return 'Молодец! Продолжай в том же духе! 🎉';

    const randomIndex = Math.floor(Math.random() * levelMessages.length);
    return levelMessages[randomIndex];
  }

  /**
   * Получить финальное сообщение победы
   */
  static getVictoryMessage(): string {
    return this.VICTORY_MESSAGE;
  }

  /**
   * Сообщения поддержки при потере жизни
   */
  private static readonly ENCOURAGEMENT_MESSAGES = [
    'Не переживай! Попробуй ещё раз! 💪',
    'Ничего страшного! У тебя всё получится! 🌟',
    'Не сдавайся! Ты можешь это сделать! 🎯',
    'Попробуй снова! Я в тебя верю! 🐼',
  ];

  /**
   * Получить сообщение поддержки
   */
  static getEncouragementMessage(): string {
    const randomIndex = Math.floor(
      Math.random() * this.ENCOURAGEMENT_MESSAGES.length
    );
    return this.ENCOURAGEMENT_MESSAGES[randomIndex];
  }
}
