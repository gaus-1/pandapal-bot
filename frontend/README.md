# Frontend

Современный веб-интерфейс для PandaPal. React приложение с TypeScript и Tailwind CSS.

## Технологии

- React 19 - библиотека для UI
- TypeScript 5 - строгая типизация
- Vite 7 - сборщик
- Tailwind CSS 3 - utility-first CSS
- TanStack Query 5 - API клиент и кэширование
- Zustand 5 - state management
- Telegram Mini App SDK 8.0 - интеграция с Telegram

## Структура

```
frontend/
├── src/
│   ├── components/      # Переиспользуемые компоненты
│   ├── features/        # Основные фичи (AIChat, Premium, Games)
│   ├── hooks/           # Кастомные React хуки
│   ├── services/        # API клиенты
│   ├── store/           # Zustand stores
│   ├── utils/           # Вспомогательные функции
│   └── App.tsx          # Корневой компонент
├── public/              # Статические файлы
└── e2e/                 # End-to-end тесты (Playwright)
```

## Команды

```bash
npm install              # Установка зависимостей
npm run dev              # Запуск dev-сервера (localhost:5173)
npm run build            # Сборка для production
npm run preview          # Предпросмотр production-сборки
npm run lint             # Проверка кода
npm test                 # Запуск тестов
```

## Основные фичи

**AIChat** - чат с AI ассистентом с поддержкой текста, голоса и изображений. Streaming ответы через SSE. Приветственный экран с логотипом и задержкой 5 секунд перед приветствием панды.

**Premium** - экран Premium подписки с интеграцией YooKassa (продакшн), сохранением карт, отвязкой карт. Замочки на кнопках оплаты при открытии вне мини-апп.

**Games** - PandaPalGo игры: Крестики-нолики, Шашки, 2048 с AI противником. Система достижений и статистики.

**Achievements** - экран достижений с прогрессом, уровнями и XP.

**Emergency** - экстренные номера (112, 101, 102, 103).

## Разработка

Все компоненты следуют SOLID принципам. Каждый feature изолирован и переиспользуем. Используем TypeScript строго - избегаем `any`.

Адаптивный дизайн с mobile-first подходом. Поддерживаемые разрешения: 320px - 1440px.

**Темная тема** - полная поддержка темной темы для всех экранов с автоматическим переключением.

**Streaming AI** - ответы AI приходят через Server-Sent Events (SSE) для быстрой генерации текста.

## Деплой

Автоматический деплой через Railway.app при push в main. Frontend раздается через aiohttp сервер из папки `dist/`.
