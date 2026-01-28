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
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version \
    && npm --version

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Сборка frontend
RUN cd frontend && npm install && npm run build && cd ..

# Переменные окружения для Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Порт для веб-сервера
EXPOSE 8000

# Запуск веб-сервера
CMD ["python", "web_server.py"]
