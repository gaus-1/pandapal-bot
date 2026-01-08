# Features - Функциональные модули

Основные функциональные модули приложения. Каждый модуль - отдельная фича со своим экраном.

## Структура модуля

Обычно так:
```
FeatureName/
├── FeatureNameScreen.tsx    # Главный компонент экрана
├── components/              # Локальные компоненты (если нужны)
└── __tests__/              # Тесты модуля
```

## Модули

### AIChat
Чат с AI ассистентом. Поддержка текста, голоса, изображений. Streaming ответы через SSE для быстрых ответов.

### Games
Игры PandaPalGo:
- TicTacToe - крестики-нолики с AI противником
- Checkers - шашки с AI
- Game2048 - игра 2048
- GamesScreen - главный экран выбора игры

### Premium
Управление Premium подпиской, оплата через YooKassa. Показывает статус подписки, позволяет оплатить.

### Donation
Донаты через Telegram Stars для поддержки проекта.

### Emergency
Экстренные номера: 112, 101, 102, 103. Быстрый доступ к помощи.

### Achievements
Достижения, уровни, XP, статистика. Мотивирует детей учиться.

### Settings
Настройки пользователя, тема (dark/light), язык.

## Примеры

### Простой экран

```typescript
import { useState } from 'react';

export function FeatureScreen() {
  const [state, setState] = useState();

  return (
    <div className="feature-container">
      {/* Твой UI здесь */}
    </div>
  );
}
```

### С API

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export function FeatureScreen() {
  const { data, isLoading } = useQuery({
    queryKey: ['feature'],
    queryFn: () => api.getFeature(),
  });

  if (isLoading) return <div>Загрузка...</div>;
  return <div>{data?.result}</div>;
}
```

### С навигацией

```typescript
import { useAppStore } from '../store/appStore';

export function FeatureScreen() {
  const setCurrentScreen = useAppStore((state) => state.setCurrentScreen);

  return (
    <button onClick={() => setCurrentScreen('home')}>
      Назад
    </button>
  );
}
```

## Тестирование

Каждый модуль должен иметь тесты:
- Unit тесты компонентов
- Тесты взаимодействия
- Тесты API интеграции
