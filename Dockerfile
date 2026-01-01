# Базовый образ Python 3.13
FROM python:3.13-slim

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей (включая Node.js для frontend)
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    postgresql-client \
    ffmpeg \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Сборка frontend
RUN cd frontend && npm ci && npm run build && cd ..

# Переменные окружения для Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Порт для веб-сервера
EXPOSE 8000

# Запуск бота
CMD ["python", "main.py"]
