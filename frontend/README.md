# PandaPal — Фронтенд

Современный веб-интерфейс для образовательного ИИ-бота PandaPal.

## 🚀 Технологии

- **React 19** — библиотека для UI
- **TypeScript 5** — строгая типизация
- **Vite 7** — сборщик нового поколения
- **Tailwind CSS 3** — utility-first CSS фреймворк
- **ESLint** — линтинг и проверка качества кода

## 📁 Структура проекта

```
frontend/
├── src/
│   ├── components/      # Переиспользуемые компоненты
│   │   ├── Header.tsx   # Шапка сайта с навигацией
│   │   ├── Hero.tsx     # Главная секция с заголовком
│   │   ├── Features.tsx # Блок преимуществ (адаптивность, безопасность, игра)
│   │   ├── FeatureCard.tsx  # Карточка одного преимущества
│   │   ├── Section.tsx  # Универсальная секция контента
│   │   ├── Footer.tsx   # Подвал сайта
│   │   └── index.ts     # Экспорт всех компонентов
│   ├── config/          # Конфигурация и константы
│   │   └── constants.ts # Тексты, URL, настройки
│   ├── types/           # TypeScript типы и интерфейсы
│   │   └── index.ts
│   ├── utils/           # Вспомогательные функции
│   │   └── analytics.ts # Аналитика и трекинг
│   ├── hooks/           # Кастомные React хуки
│   │   └── useImageFallback.ts  # Обработка ошибок загрузки изображений
│   ├── App.tsx          # Корневой компонент приложения
│   ├── main.tsx         # Точка входа
│   └── index.css        # Глобальные стили Tailwind
├── public/
│   └── logo.png         # Логотип PandaPal (панда с книгой)
├── index.html           # HTML шаблон
├── vite.config.ts       # Конфигурация Vite (алиасы, сборка)
├── tailwind.config.js   # Конфигурация Tailwind (цвета, шрифты)
├── tsconfig.json        # Конфигурация TypeScript
└── package.json
```

## 🛠️ Команды для разработки

### Установка зависимостей
```bash
npm install
```

### Запуск dev-сервера (с hot reload)
```bash
npm run dev
```
Сайт будет доступен на http://localhost:5173

### Сборка для production
```bash
npm run build
```
Результат в папке `dist/`

### Предпросмотр production-сборки
```bash
npm run preview
```

### Проверка кода (линтинг)
```bash
npm run lint
```

## 🎨 Дизайн-система

### Цветовая палитра
- **Розовый:** `#FFC0CB` — акценты, CTA-кнопки
- **Голубой:** `#87CEEB` — второстепенные кнопки
- **Белый:** `#FFFFFF` — фон карточек
- **Градиент:** от голубого к розовому (20% прозрачность)

### Типографика
- **Open Sans** — основной шрифт для текста (400, 600)
- **Montserrat** — шрифт для заголовков (600, 700)

### UI-элементы
- Круглые кнопки (`rounded-full`)
- Мягкие тени (`shadow-sm`, `shadow-md`, `shadow-lg`)
- Плавные анимации при наведении (200ms)
- Полупрозрачный backdrop-blur для карточек

### Стиль
Минималистичный и чистый дизайн, вдохновлённый giga.chat

## 📱 Адаптивность

- **Mobile-first подход** — сначала мобильная версия
- **Поддерживаемые разрешения:** 320px – 1440px
- **Breakpoints:**
  - `md:` — планшеты и выше (768px+)
  - Используется Tailwind responsive система

## ♿ Доступность (Accessibility)

- ✅ Semantic HTML5 теги (`<header>`, `<main>`, `<footer>`, `<nav>`)
- ✅ ARIA labels для навигации
- ✅ Alt текст для всех изображений
- ✅ Навигация с клавиатуры (Tab, Enter)
- ✅ Контрастность цветов соответствует WCAG AA
- ✅ `lang="ru"` для корректного чтения screen readers

## 🔒 Безопасность

- ✅ `rel="noopener noreferrer"` для внешних ссылок (защита от tabnabbing)
- ✅ Content Security Policy готов к настройке
- ✅ Нет inline-скриптов в HTML
- ✅ Lazy loading для изображений
- ✅ Sanitize user inputs (если будут формы)

## 📈 Производительность

- ✅ **Code splitting** — разделение на vendor и app chunks
- ✅ **React.memo** — мемоизация компонентов для предотвращения лишних рендеров
- ✅ **Lazy loading** изображений (`loading="lazy"`)
- ✅ **Minification** — сжатие через Terser
- ✅ **Tree shaking** — удаление неиспользуемого кода
- ✅ **Preconnect** для шрифтов Google Fonts

## 🌐 SEO-оптимизация

- ✅ Meta description
- ✅ Open Graph теги (Facebook, LinkedIn)
- ✅ Twitter Card теги
- ✅ Semantic HTML разметка
- ✅ Правильный `<title>` и `lang`
- ✅ Готовность к sitemap.xml
- ✅ Структурированные данные (JSON-LD) — можно добавить

## 📦 Деплой

### Автоматический деплой на Render

При каждом push в ветку `main`:
1. Render автоматически клонирует репозиторий
2. Выполняет `npm ci && npm run build`
3. Публикует содержимое `dist/` на CDN
4. Обновляет https://pandapal.ru

### Настройки Render Static Site
- **Root Directory:** `frontend`
- **Build Command:** `npm ci && npm run build`
- **Publish Directory:** `dist`
- **Auto-Deploy:** Включён

### CDN и производительность
- ✅ Render Global CDN
- ✅ Автоматическое сжатие Brotli/Gzip
- ✅ HTTP/2 и HTTP/3
- ✅ SSL-сертификат Let's Encrypt (автообновление)

## 🧪 Тестирование (рекомендуется добавить)

```bash
# Установить Vitest
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Запустить тесты
npm run test
```

## 🔧 Настройка окружения

### Переменные окружения (если понадобятся)

Создайте `.env.local`:
```env
VITE_API_URL=https://api.pandapal.ru
VITE_BOT_TOKEN=your_token_here
VITE_GA_ID=G-XXXXXXXXXX
```

Используйте в коде:
```typescript
const apiUrl = import.meta.env.VITE_API_URL
```

## 📐 Архитектурные принципы

### SOLID
- **S** — Single Responsibility: каждый компонент отвечает за одну задачу
- **O** — Open/Closed: компоненты открыты для расширения через props
- **L** — Liskov Substitution: типы корректно наследуются
- **I** — Interface Segregation: минимальные интерфейсы для props
- **D** — Dependency Inversion: зависимости через import, не хардкод

### Модульность
- Компоненты изолированы и переиспользуемы
- Barrel exports (`index.ts`) для удобного импорта
- Алиасы путей (`@components`, `@config`) для читаемости

### Масштабируемость
- Добавление новых секций через `SECTIONS` массив
- Новые фичи — просто расширяем `FEATURES`
- Легко добавить i18n (интернационализацию)
- Готовность к роутингу (React Router)

## 🤝 Правила разработки

1. **Используйте TypeScript строго** — избегайте `any`
2. **Пишите JSDoc комментарии** для функций и компонентов
3. **Следуйте ESLint** — код должен проходить линтинг
4. **Тестируйте на разных разрешениях** (320px, 768px, 1440px)
5. **Комментарии на русском** для бизнес-логики
6. **Именование:** camelCase для переменных, PascalCase для компонентов
7. **Один компонент = один файл**

## 🐛 Отладка

### Проверка в браузере
1. Chrome DevTools → Lighthouse
2. Проверить Performance, Accessibility, SEO
3. Цель: все показатели 90+

### Проверка адаптивности
```
Chrome DevTools → Toggle Device Toolbar (Ctrl+Shift+M)
Тестировать: iPhone SE (375px), iPad (768px), Desktop (1440px)
```

## 📞 Контакты

- **GitHub:** https://github.com/gaus-1/pandapal-bot
- **Telegram Bot:** https://t.me/PandaPalBot
- **Website:** https://pandapal.ru

## 📄 Лицензия

© 2025 PandaPal. Все права защищены.
