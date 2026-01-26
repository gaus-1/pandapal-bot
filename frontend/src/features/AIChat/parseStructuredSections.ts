/**
 * Парсинг структурированных секций из ответов AI
 */

export interface StructuredSection {
  title: string | null;
  content: string;
  type: 'definition' | 'properties' | 'how-it-works' | 'application' | 'summary' | 'other';
}

export function parseStructuredSections(content: string): StructuredSection[] {
  const sections: StructuredSection[] = [];

  // Паттерны заголовков (без **, так как мы их уже убрали)
  const headerPatterns = [
    { pattern: /^Определение:\s*$/mi, type: 'definition' as const },
    { pattern: /^Ключевые свойства:\s*$/mi, type: 'properties' as const },
    { pattern: /^Как это работает:\s*$/mi, type: 'how-it-works' as const },
    { pattern: /^Как построить:\s*$/mi, type: 'how-it-works' as const },
    { pattern: /^Как решать задачи:\s*$/mi, type: 'how-it-works' as const },
    { pattern: /^Как решать задачи на [^:]+:\s*$/mi, type: 'how-it-works' as const },
    { pattern: /^Где применяется:\s*$/mi, type: 'application' as const },
    { pattern: /^Где встречается:\s*$/mi, type: 'application' as const },
    { pattern: /^Итог:\s*$/mi, type: 'summary' as const },
  ];

  // Разбиваем по двойным переносам строк (абзацы)
  const paragraphs = content.split(/\n\n+/).filter(p => p.trim());

  let currentSection: StructuredSection | null = null;

  for (const paragraph of paragraphs) {
    const trimmed = paragraph.trim();
    if (!trimmed) continue;

    // Проверяем, является ли абзац заголовком
    let isHeader = false;
    let headerType: StructuredSection['type'] = 'other';
    let headerTitle: string | null = null;

    for (const { pattern, type } of headerPatterns) {
      if (pattern.test(trimmed)) {
        isHeader = true;
        headerType = type;
        headerTitle = trimmed.replace(/:\s*$/, '');
        break;
      }
    }

    if (isHeader) {
      // Сохраняем предыдущую секцию
      if (currentSection) {
        sections.push(currentSection);
      }
      // Проверяем, есть ли контент после заголовка в том же абзаце
      const headerMatch = trimmed.match(/^([^:\n]+:)\s*(.+)$/s);
      if (headerMatch) {
        // Заголовок и контент в одном абзаце
        currentSection = {
          title: headerMatch[1].trim(),
          content: headerMatch[2].trim(),
          type: headerType,
        };
      } else {
        // Только заголовок
        currentSection = {
          title: headerTitle,
          content: '',
          type: headerType,
        };
      }
    } else {
      // Добавляем контент к текущей секции
      if (currentSection) {
        currentSection.content += (currentSection.content ? '\n\n' : '') + trimmed;
      } else {
        // Если нет текущей секции, создаем секцию без заголовка
        currentSection = {
          title: null,
          content: trimmed,
          type: 'other',
        };
      }
    }
  }

  // Добавляем последнюю секцию
  if (currentSection) {
    sections.push(currentSection);
  }

  // Если не нашли структурированные секции, используем fallback
  if (sections.length === 0 || (sections.length === 1 && !sections[0].title)) {
    return parseFallbackSections(content);
  }

  return sections;
}

export function parseFallbackSections(content: string): StructuredSection[] {
  const sections: StructuredSection[] = [];

  // Разбиваем по двойным переносам строк (абзацы)
  const paragraphs = content.split(/\n\n+/).filter(p => p.trim());

  for (const paragraph of paragraphs) {
    const trimmed = paragraph.trim();
    if (!trimmed) continue;

    sections.push({
      title: null,
      content: trimmed,
      type: 'other',
    });
  }

  // Если даже абзацев нет, создаем одну секцию со всем контентом
  if (sections.length === 0) {
    sections.push({
      title: null,
      content: content.trim(),
      type: 'other',
    });
  }

  return sections;
}

export function parseListItems(content: string): string[] {
  const items: string[] = [];
  const lines = content.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Маркированный список: - или • в начале
    if (/^[-•]\s+/.test(trimmed)) {
      items.push(trimmed.replace(/^[-•]\s+/, ''));
    }
    // Нумерованный список: 1. или 1) в начале
    else if (/^\d+[.)]\s+/.test(trimmed)) {
      items.push(trimmed.replace(/^\d+[.)]\s+/, ''));
    }
  }

  return items;
}

export function isList(content: string): boolean {
  const lines = content.split('\n').filter(l => l.trim());
  if (lines.length < 2) return false;

  // Проверяем, что большинство строк начинаются с маркера списка
  const listLines = lines.filter(l => /^[-•]\s+/.test(l.trim()));
  return listLines.length >= lines.length * 0.5;
}

export function isNumberedList(content: string): boolean {
  const lines = content.split('\n').filter(l => l.trim());
  if (lines.length < 2) return false;

  // Проверяем, что большинство строк начинаются с номера
  const numberedLines = lines.filter(l => /^\d+[.)]\s+/.test(l.trim()));
  return numberedLines.length >= lines.length * 0.5;
}
