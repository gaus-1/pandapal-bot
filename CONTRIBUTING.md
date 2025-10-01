# Руководство по разработке PandaPal

## 📐 Принципы архитектуры

### SOLID принципы

#### S — Single Responsibility (Единственная ответственность)
Каждый компонент отвечает за одну задачу:
- `Header` — только шапка сайта
- `Hero` — только главная секция с CTA
- `FeatureCard` — только отображение одной карточки

#### O — Open/Closed (Открыт для расширения, закрыт для модификации)
Добавление новых секций НЕ требует изменения компонентов:
```typescript
// Просто добавьте новую секцию в массив
export const SECTIONS = [
  ...existing,
  { id: 'new', title: 'Новая секция', description: '...' }
]
```

#### L — Liskov Substitution (Подстановка Лисков)
Все компоненты типа `Section` взаимозаменяемы:
```typescript
<Section section={parentsSection} />
<Section section={teachersSection} />
// Оба работают одинаково
```

#### I — Interface Segregation (Разделение интерфейсов)
Минимальные props для каждого компонента:
```typescript
// FeatureCard принимает только то, что нужно
interface FeatureCardProps {
  feature: Feature; // Только данные карточки, ничего лишнего
}
```

#### D — Dependency Inversion (Инверсия зависимостей)
Компоненты зависят от абстракций (типов), а не от конкретики:
```typescript
import type { Feature } from '@types';
// Зависим от интерфейса, а не от конкретной реализации
```

---

## 🏗️ Структура проекта

### Папки и их назначение

```
src/
├── components/       # UI-компоненты (переиспользуемые блоки)
│   ├── Header.tsx    # Шапка: логотип + навигация
│   ├── Hero.tsx      # Главная секция: заголовок + CTA
│   ├── Features.tsx  # Контейнер для карточек преимуществ
│   ├── FeatureCard.tsx  # Карточка одного преимущества
│   ├── Section.tsx   # Универсальная секция контента
│   ├── Footer.tsx    # Подвал: логотип + копирайт
│   └── index.ts      # Barrel export (удобный импорт)
│
├── config/           # Конфигурация и константы
│   └── constants.ts  # Все тексты, URL, настройки (ЕДИНСТВЕННЫЙ ФАЙЛ ДЛЯ ПРАВОК)
│
├── types/            # TypeScript типы и интерфейсы
│   └── index.ts      # Feature, Section, SiteConfig и т.д.
│
├── utils/            # Вспомогательные функции
│   └── analytics.ts  # Трекинг событий (GA4, Yandex Metrika)
│
├── hooks/            # Кастомные React хуки
│   └── useImageFallback.ts  # Обработка ошибок загрузки изображений
│
├── App.tsx           # Корневой компонент (композиция страницы)
├── main.tsx          # Entry point (рендеринг в DOM)
└── index.css         # Глобальные стили Tailwind
```

---

## 📝 Правила написания кода

### 1. Комментарии на русском языке

```typescript
// ✅ ХОРОШО: понятный русский комментарий
// Получаем текущий год автоматически (не нужно обновлять вручную)
const currentYear = new Date().getFullYear();

// ❌ ПЛОХО: английский или без комментария
const year = new Date().getFullYear();
```

### 2. JSDoc для функций и компонентов

```typescript
/**
 * Карточка преимущества с hover-эффектом
 * Используется в компоненте Features для отображения списка преимуществ
 * Мемоизирована для оптимизации производительности
 */
export const FeatureCard: React.FC<FeatureCardProps> = ...
```

### 3. Строгая типизация TypeScript

```typescript
// ✅ ХОРОШО: явные типы
interface FeatureCardProps {
  feature: Feature;
}

// ❌ ПЛОХО: any или без типов
const props: any = ...
```

### 4. Именование

- **Компоненты:** PascalCase (`FeatureCard`, `Header`)
- **Функции:** camelCase (`trackButtonClick`, `handleError`)
- **Константы:** UPPER_SNAKE_CASE (`SITE_CONFIG`, `FEATURES`)
- **Файлы компонентов:** PascalCase.tsx (`Header.tsx`)
- **Файлы утилит:** camelCase.ts (`analytics.ts`)

---

## 🔄 Процесс разработки

### 1. Создание нового компонента

```bash
# 1. Создайте файл
frontend/src/components/NewComponent.tsx

# 2. Шаблон компонента:
```

```typescript
/**
 * Компонент NewComponent (краткое описание)
 * Подробное описание назначения
 * @module components/NewComponent
 */

import React from 'react';

/**
 * Props для NewComponent
 */
interface NewComponentProps {
  /** Описание пропса */
  someProp: string;
}

/**
 * Описание функциональности компонента
 */
export const NewComponent: React.FC<NewComponentProps> = React.memo(
  ({ someProp }) => {
    return (
      <div>
        {/* JSX с комментариями */}
        {someProp}
      </div>
    );
  }
);

NewComponent.displayName = 'NewComponent';
```

```bash
# 3. Добавьте в barrel export
frontend/src/components/index.ts:
export { NewComponent } from './NewComponent';
```

### 2. Добавление новой секции

Отредактируйте `constants.ts`:

```typescript
export const SECTIONS: readonly Section[] = [
  ...existing,
  {
    id: 'new-section',  // Уникальный ID
    title: 'Заголовок', // Отображается на странице
    description: 'Текст описания секции.',
  },
];
```

Компонент `Section` автоматически отрендерит новую секцию!

### 3. Изменение текстов

**ВСЕ тексты** в одном файле: `src/config/constants.ts`

Не нужно лезть в компоненты — просто меняйте константы.

---

## 🧪 Тестирование

### Перед коммитом проверьте:

1. **Линтинг:**
```bash
npm run lint
```

2. **Сборка:**
```bash
npm run build
```

3. **Адаптивность:**
- Chrome DevTools → Device Toolbar (Ctrl+Shift+M)
- Тестируйте: 320px, 768px, 1440px

4. **Accessibility:**
- Lighthouse → Accessibility (должно быть 90+)
- Проверьте навигацию с клавиатуры (Tab, Enter)

---

## 🚀 Деплой

### Автоматический деплой

При `git push origin main`:
1. GitHub получает код
2. Render автоматически запускает сборку
3. Через 2-3 минуты сайт обновляется

### Мануальный деплой

Если нужно срочно обновить без коммита:
```bash
curl -X POST "https://api.render.com/deploy/srv-xxx?key=xxx"
```

---

## 📊 Метрики качества кода

### Обязательные требования:
- ✅ **TypeScript errors:** 0
- ✅ **ESLint warnings:** 0
- ✅ **Bundle size:** < 500 KB
- ✅ **Lighthouse Performance:** 90+
- ✅ **Lighthouse Accessibility:** 95+
- ✅ **Lighthouse SEO:** 100

### Рекомендуемые:
- ✅ Test coverage: 70%+
- ✅ React.memo где возможно
- ✅ Lazy loading для больших компонентов

---

## 🤝 Git Workflow

### Branching strategy

```bash
main          # Production (деплоится на pandapal.ru)
├── develop   # Staging (тестирование перед релизом)
├── feature/  # Новые фичи
└── hotfix/   # Срочные исправления
```

### Commit messages

Используйте Conventional Commits:

```
feat: добавлен компонент MobileMenu
fix: исправлена ошибка загрузки логотипа
refactor: разделён компонент App на подкомпоненты
docs: обновлён README с инструкциями
style: исправлено форматирование в Header.tsx
```

---

## ⚡ Performance Best Practices

### 1. Мемоизация

```typescript
// ✅ Используйте React.memo для предотвращения лишних рендеров
export const Header = React.memo(() => { ... });

// ✅ useCallback для функций
const handleClick = useCallback(() => { ... }, [deps]);

// ✅ useMemo для вычислений
const expensiveValue = useMemo(() => compute(), [deps]);
```

### 2. Code Splitting

```typescript
// ✅ Lazy load для больших компонентов
const Dashboard = lazy(() => import('./Dashboard'));

// В vite.config.ts настроены chunks:
manualChunks: {
  vendor: ['react', 'react-dom'], // Библиотеки отдельно
}
```

### 3. Изображения

```typescript
// ✅ Указывайте width/height (предотвращает layout shift)
<img width="48" height="48" ... />

// ✅ Lazy loading для изображений ниже fold
<img loading="lazy" ... />

// ✅ Eager для важных (логотип, hero-изображение)
<img loading="eager" ... />
```

---

## 🔐 Безопасность

### Checklist перед релизом:

- ✅ `rel="noopener noreferrer"` на всех внешних ссылках
- ✅ Нет `dangerouslySetInnerHTML` без sanitize
- ✅ Валидация user inputs (если есть формы)
- ✅ HTTPS принудительно (Render делает автоматически)
- ✅ Content Security Policy (можно добавить в Headers Render)

---

## 📞 Контакты

При вопросах обращайтесь:
- **Email:** v81158847@gmail.com
- **GitHub:** https://github.com/gaus-1/pandapal-bot
- **Telegram:** https://t.me/PandaPalBot

---

© 2025 PandaPal. Все права защищены.

