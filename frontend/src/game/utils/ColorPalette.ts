/**
 * Цветовые палитры для школьных локаций
 * Пастельные, приятные глазу цвета
 */

export interface ColorScheme {
  background: string;
  primary: string;
  secondary: string;
  accent: string;
  text: string;
  particle: string;
}

/**
 * Палитры для каждой локации
 */
export class ColorPalette {
  /**
   * Уровень 1: Спортзал
   * Пастельный синий + мягкий зеленый
   */
  static readonly GYM: ColorScheme = {
    background: '#E8F4F8', // Светло-голубой
    primary: '#A8D8EA', // Мягкий голубой
    secondary: '#B8E6D5', // Мятный
    accent: '#FFB6C1', // Розовый
    text: '#5C6B73', // Серо-синий
    particle: '#FFFFFF', // Белые частицы
  };

  /**
   * Уровень 2: Класс математики
   * Бежевый + оранжевый + мягкий желтый
   */
  static readonly CLASSROOM: ColorScheme = {
    background: '#FFF8E7', // Кремовый
    primary: '#FFD89B', // Персиковый
    secondary: '#FFCBA4', // Абрикосовый
    accent: '#FF9A8B', // Коралловый
    text: '#8B7355', // Коричневый
    particle: '#FFE4B5', // Светло-персиковый
  };

  /**
   * Уровень 3: Столовая
   * Персиковый + желтый + мягкий красный
   */
  static readonly CANTEEN: ColorScheme = {
    background: '#FFF0E0', // Светлый персик
    primary: '#FFCDB2', // Персик
    secondary: '#FFB4A2', // Лососевый
    accent: '#E5989B', // Розово-красный
    text: '#6D6875', // Серо-фиолетовый
    particle: '#FFDAB9', // Персиковый
  };

  /**
   * Уровень 4: Школьный двор
   * Зеленый + голубое небо + теплые акценты
   */
  static readonly PLAYGROUND: ColorScheme = {
    background: '#E0F2F7', // Небесно-голубой
    primary: '#B2DFD5', // Мятно-зеленый
    secondary: '#9FD8CB', // Бирюзовый
    accent: '#F4A261', // Оранжевый
    text: '#577590', // Синий
    particle: '#C7F0DB', // Светло-зеленый
  };

  /**
   * Уровень 5: Библиотека
   * Фиолетовый + синий + золотые акценты
   */
  static readonly LIBRARY: ColorScheme = {
    background: '#E6E6FA', // Лавандовый
    primary: '#B8B5D1', // Серо-фиолетовый
    secondary: '#9D9CB4', // Фиолетовый
    accent: '#FFD700', // Золотой
    text: '#4A4A6A', // Темно-фиолетовый
    particle: '#E0BBE4', // Светло-фиолетовый
  };

  /**
   * Общая палитра для UI
   */
  static readonly UI: ColorScheme = {
    background: '#FFFFFF',
    primary: '#4A5568',
    secondary: '#718096',
    accent: '#48BB78',
    text: '#2D3748',
    particle: '#E2E8F0',
  };

  /**
   * Панда (всегда одинаковая)
   */
  static readonly PANDA = {
    body: '#FFFFFF', // Белый
    spots: '#2D3748', // Черный
    nose: '#FF69B4', // Розовый нос
    eyes: '#2D3748', // Черные глаза
  };

  /**
   * Получить палитру по номеру уровня
   */
  static getLevelPalette(level: number): ColorScheme {
    const palettes = [
      this.GYM,
      this.CLASSROOM,
      this.CANTEEN,
      this.PLAYGROUND,
      this.LIBRARY,
    ];
    return palettes[level % palettes.length];
  }

  /**
   * Интерполяция между двумя цветами
   * @param color1 Первый цвет в формате #RRGGBB
   * @param color2 Второй цвет в формате #RRGGBB
   * @param t Значение от 0 до 1
   */
  static lerpColor(color1: string, color2: string, t: number): string {
    const r1 = parseInt(color1.slice(1, 3), 16);
    const g1 = parseInt(color1.slice(3, 5), 16);
    const b1 = parseInt(color1.slice(5, 7), 16);

    const r2 = parseInt(color2.slice(1, 3), 16);
    const g2 = parseInt(color2.slice(3, 5), 16);
    const b2 = parseInt(color2.slice(5, 7), 16);

    const r = Math.round(r1 + (r2 - r1) * t);
    const g = Math.round(g1 + (g2 - g1) * t);
    const b = Math.round(b1 + (b2 - b1) * t);

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  /**
   * Добавить альфа-канал к цвету
   */
  static withAlpha(color: string, alpha: number): string {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}
