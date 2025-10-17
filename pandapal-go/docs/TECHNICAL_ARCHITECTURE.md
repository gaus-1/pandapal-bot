# 🏗️ Техническая архитектура PandaPal Go

## 📐 Общая архитектура

```
┌─────────────────────────────────────────┐
│         Phaser.js Game Engine           │
│          (Canvas Renderer)              │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    ┌───▼────┐           ┌──────▼──────┐
    │ Scenes │           │  Managers   │
    └────────┘           └─────────────┘
        │                       │
    ┌───┴────┐           ┌──────┴──────┐
    │Entities│           │  Services   │
    └────────┘           └─────────────┘
```

---

## 🎭 Phaser Scenes (игровые сцены)

### 1. BootScene
**Цель:** Загрузка всех ресурсов
**Переход:** → MenuScene

### 2. MenuScene
**Цель:** Главное меню
**Переход:** → GameScene

### 3. GameScene (основная)
**Цель:** Геймплей
**Содержит:**
- Player (панда)
- ObstacleManager (препятствия)
- QuizManager (вопросы)
- BackgroundManager (фон)
- ScoreManager (очки)

### 4. PauseScene (overlay)
**Цель:** Пауза
**Переход:** → GameScene (resume)

### 5. GameOverScene
**Цель:** Результаты
**Переход:** → MenuScene или GameScene (retry)

---

## 🎮 Entities (игровые объекты)

### Player (Панда)
```typescript
class Player extends Phaser.GameObjects.Sprite {
  - currentLane: number      // 0, 1, или 2
  - isJumping: boolean
  - isSliding: boolean
  - lives: number

  + jump()
  + slide()
  + switchLane(direction: 'left' | 'right')
  + takeDamage()
  + collect(item: Collectible)
}
```

### Obstacle (Препятствия)
```typescript
class Obstacle extends Phaser.GameObjects.Sprite {
  - lane: number
  - type: 'high' | 'low' | 'middle'

  + update(delta: number)  // Движение влево
  + destroy()
}
```

### Collectible (Предметы)
```typescript
class Collectible extends Phaser.GameObjects.Sprite {
  - type: 'book' | 'star' | 'medal' | 'apple'
  - points: number

  + collect()
}
```

### QuizAnswer (Ответ на вопрос)
```typescript
class QuizAnswer extends Phaser.GameObjects.Container {
  - text: string
  - isCorrect: boolean
  - lane: number

  + check(): boolean
}
```

---

## 🔧 Managers (системы управления)

### BackgroundManager
**Задача:** Бесконечный скролл фона
**Паттерн:** Object Pool (переиспользование)

```typescript
class BackgroundManager {
  - layers: Phaser.GameObjects.TileSprite[]
  - currentLocation: string

  + update(speed: number)
  + changeLocation(newLocation: string)
}
```

### ObstacleManager
**Задача:** Генерация препятствий
**Паттерн:** Factory + Object Pool

```typescript
class ObstacleManager {
  - obstacles: Obstacle[]
  - spawnTimer: number

  + update(delta: number)
  + spawnObstacle(lane: number, type: string)
  + checkCollisions(player: Player)
}
```

### QuizManager
**Задача:** Образовательные вопросы
**Источник:** Локальный JSON или API

```typescript
class QuizManager {
  - currentQuestion: Question
  - answers: QuizAnswer[]
  - questionTimer: number

  + showQuestion()
  + checkAnswer(lane: number): boolean
  + getNextQuestion(): Question
}
```

### ScoreManager
**Задача:** Очки, комбо, рекорды
**Хранение:** LocalStorage

```typescript
class ScoreManager {
  - score: number
  - combo: number
  - highScore: number

  + addPoints(amount: number)
  + increaseCombo()
  + resetCombo()
  + saveHighScore()
}
```

### LocationManager
**Задача:** Смена локаций
**Цикл:** 8 локаций → повтор

```typescript
class LocationManager {
  - locations: Location[]
  - currentIndex: number
  - timer: number

  + update(delta: number)
  + switchToNext()
  + getCurrentLocation(): Location
}
```

---

## 🔌 Services (внешние сервисы)

### ApiService
**Задача:** Связь с PandaPal backend

```typescript
class ApiService {
  + async getQuestions(subject: string, grade: number)
  + async saveScore(score: number, userId: string)
  + async syncProgress(data: GameProgress)
}
```

### QuestionLoader
**Задача:** Загрузка и кэширование вопросов

```typescript
class QuestionLoader {
  - cache: Question[]

  + async loadQuestions()
  + getRandomQuestion(difficulty: number): Question
}
```

---

## 🎨 UI Components

### HUD (Heads-Up Display)
```typescript
class HUD {
  - scoreText: Phaser.GameObjects.Text
  - livesIcons: Phaser.GameObjects.Sprite[]
  - comboText: Phaser.GameObjects.Text

  + updateScore(score: number)
  + updateLives(lives: number)
  + showCombo(multiplier: number)
}
```

---

## 🎯 Управление (Input System)

### InputHandler
**Задача:** Обработка свайпов и клавиш

```typescript
class InputHandler {
  - startX: number
  - startY: number
  - minSwipeDistance: number = 50

  + onSwipeUp(): void
  + onSwipeDown(): void
  + onSwipeLeft(): void
  + onSwipeRight(): void

  // Клавиатура (альтернатива)
  + onKeyPress(key: string): void
}
```

**Mapping:**
- Свайп ⬆️ / Space / W → Прыжок
- Свайп ⬇️ / S / Shift → Наклон
- Свайп ⬅️ / A / ← → Лево
- Свайп ➡️ / D / → → Право

---

## 📦 Оптимизация и производительность

### Object Pooling
```typescript
class ObjectPool<T> {
  - pool: T[]

  + get(): T
  + release(obj: T)
}
```

**Используется для:**
- Препятствий (избегаем создания/удаления)
- Собираемых предметов
- Частиц эффектов

### Asset Management
- **Спрайт атласы** вместо отдельных файлов
- **Texture compression** (WebP формат)
- **Lazy loading** для фонов локаций

---

## 🗂️ Структура данных

### Question (Вопрос)
```typescript
interface Question {
  id: string;
  text: string;           // "2 + 2 = ?"
  subject: string;        // "math"
  difficulty: number;     // 1-5
  answers: Answer[];      // 3 варианта
}

interface Answer {
  text: string;           // "4"
  isCorrect: boolean;
}
```

### GameState (Состояние игры)
```typescript
interface GameState {
  score: number;
  lives: number;
  combo: number;
  distance: number;       // Метры пробежал
  currentLocation: number;
  questionsAnswered: number;
  correctAnswers: number;
}
```

---

## 🔄 Game Loop (игровой цикл)

```
1. Update (каждый фрейм, ~16ms):
   ├─ Движение игрока
   ├─ Обновление препятствий
   ├─ Проверка коллизий
   ├─ Обновление фона
   ├─ Таймер вопросов
   └─ Проверка смены локации

2. Render (автоматически Phaser):
   ├─ Фон (параллакс слои)
   ├─ Препятствия и предметы
   ├─ Игрок (панда)
   └─ UI (HUD, вопросы)
```

---

## 🌐 Интеграция с PandaPal Bot

### API Endpoints (будущее)
```
GET  /api/game/questions?subject=math&grade=2
POST /api/game/score
GET  /api/game/leaderboard
POST /api/game/achievement
```

### LocalStorage (временно)
```typescript
{
  highScore: number,
  settings: {
    soundEnabled: boolean,
    musicEnabled: boolean,
  },
  achievements: string[],
}
```

---

## 📱 Адаптивность

### Responsive Design
- **Desktop:** 800x600 (оптимально)
- **Tablet:** 768x1024 (портрет)
- **Mobile:** 360x640+ (портрет)

### Scaling
```typescript
const scale = Math.min(
  window.innerWidth / 800,
  window.innerHeight / 600
);
```

---

## ⚡ Производительность

### Целевые метрики
- **FPS:** 60 (стабильно)
- **Размер:** <5MB (с ассетами)
- **Загрузка:** <3 секунды

### Оптимизации
- Sprite atlases (TexturePacker)
- Object pooling для врагов
- Отключение off-screen объектов
- Throttling для событий

---

**Архитектура готова к реализации! 🚀**

_Версия: 1.0.0_
_Дата: 17 октября 2025_
