# Frontend Source - Исходный код

Исходный код React приложения для PandaPal. Здесь все что видит пользователь в Telegram Mini App.

## Структура

```
src/
├── components/     # Переиспользуемые UI компоненты (Header, Footer и т.д.)
├── features/       # Функциональные модули (AIChat, Games, Premium)
├── services/        # API клиенты и интеграция с Telegram
├── hooks/          # Кастомные React хуки
├── store/          # State management (Zustand)
├── types/          # TypeScript типы и интерфейсы
├── utils/          # Вспомогательные функции
├── config/         # Конфигурация и константы
└── App.tsx         # Корневой компонент
```

## Features

Каждая фича - отдельный модуль со своим экраном:
- `AIChat/` - чат с AI ассистентом
- `Games/` - игры (TicTacToe, Checkers, 2048)
- `Premium/` - Premium подписка
- `Donation/` - донаты через Telegram Stars
- `Emergency/` - экстренные номера
- `Achievements/` - достижения и статистика
- `Settings/` - настройки пользователя
- `Lessons/` - уроки и материалы
- `Progress/` - прогресс обучения

## Services

- `api.ts` - HTTP клиент для API (TanStack Query)
- `telegram.ts` - интеграция с Telegram Mini App SDK

## State Management

Zustand store в `store/appStore.ts`:
- Навигация между экранами
- Состояние авторизации
- Настройки приложения

Просто и удобно, без лишней сложности.

## TypeScript

Строгая типизация везде:
- Все компоненты типизированы
- Интерфейсы в `types/index.ts`
- Избегай `any`, используй `unknown` если тип неизвестен

## Стили

Tailwind CSS для стилизации:
- Utility-first подход - стили прямо в JSX
- Dark/light темы - автоматическое переключение
- Адаптивный дизайн - mobile-first, работает на всех устройствах

## Тестирование

- Unit тесты рядом с компонентами (`__tests__/`)
- E2E тесты в `frontend/e2e/`
- Playwright для браузерных тестов
