# Базовый образ Python 3.13
FROM python:3.13-slim

WORKDIR /app

# Системные зависимости (без postgresql-client — миграции с локальной машины)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    ffmpeg \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости (слой кэшируется при неизменном requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Frontend: сначала только package*.json (слой кэшируется при неизменных зависимостях)
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci

# Остальной код и сборка frontend
COPY . .
RUN cd frontend && npm run build

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
CMD ["python", "web_server.py"]
