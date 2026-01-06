# Features - Функциональные модули

Основные функциональные модули приложения. Каждый модуль - отдельная фича с собственным экраном.

## Структура модуля

```
FeatureName/
├── FeatureNameScreen.tsx    # Главный компонент экрана
├── FeatureNameScreen.test.tsx  # Тесты
└── components/              # Локальные компоненты (если нужны)
```

## Модули

### AIChat
Чат с AI ассистентом. Поддержка текста, голоса, изображений.

### Games
Игры PandaPalGo:
- TicTacToe - крестики-нолики с AI
- Checkers - шашки с AI
- Game2048 - игра 2048
- GamesScreen - главный экран выбора игры

### Premium
Управление Premium подпиской, оплата через YooKassa.

### Donation
Донаты через Telegram Stars для поддержки проекта.

### Emergency
Экстренные номера: 112, 101, 102, 103.

### Achievements
Достижения, уровни, XP, статистика.

### Settings
Настройки пользователя, тема, язык.

### Lessons
Уроки и образовательные материалы.

### Progress
Прогресс обучения, статистика, достижения.

## Паттерны

### Базовый экран
```typescript
import { useState } from 'react';

export function FeatureScreen() {
  const [state, setState] = useState();

  return (
    <div className="feature-container">
      {/* UI */}
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

  if (isLoading) return <div>Loading...</div>;

  return <div>{data?.result}</div>;
}
```

### С навигацией
```typescript
import { useAppStore } from '../store/appStore';

export function FeatureScreen() {
  const navigate = useAppStore((state) => state.navigate);

  return (
    <button onClick={() => navigate('home')}>
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
