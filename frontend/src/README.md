# Frontend Source - Исходный код

Исходный код React приложения для PandaPal.

## Структура

```
src/
├── components/     # Переиспользуемые UI компоненты
├── features/       # Функциональные модули (AIChat, Games, Premium)
├── services/        # API клиенты и внешние сервисы
├── hooks/          # Кастомные React хуки
├── store/          # State management (Zustand)
├── types/          # TypeScript типы и интерфейсы
├── utils/          # Вспомогательные функции
├── config/         # Конфигурация и константы
└── App.tsx         # Корневой компонент
```

## Features

Каждая фича - отдельный модуль с экраном:
- `AIChat/` - чат с AI ассистентом
- `Games/` - игры (TicTacToe, Checkers, 2048)
- `Premium/` - Premium подписка
- `Donation/` - донаты через Telegram Stars
- `Emergency/` - экстренные номера
- `Achievements/` - достижения и статистика
- `Settings/` - настройки пользователя

## Services

- `api.ts` - HTTP клиент для API (TanStack Query)
- `telegram.ts` - интеграция с Telegram Mini App SDK

## State Management

Zustand store в `store/appStore.ts`:
- Навигация между экранами
- Состояние авторизации
- Настройки приложения

## TypeScript

Строгая типизация:
- Все компоненты типизированы
- Интерфейсы в `types/index.ts`
- Избегать `any`, использовать `unknown` при необходимости

## Стили

Tailwind CSS для стилизации:
- Utility-first подход
- Dark/light темы
- Адаптивный дизайн (mobile-first)

## Тестирование

- Unit тесты рядом с компонентами (`__tests__/`)
- E2E тесты в `frontend/e2e/`
- Playwright для браузерных тестов
