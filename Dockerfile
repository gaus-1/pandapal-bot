# Базовый образ Python 3.13
FROM python:3.13-slim

WORKDIR /app

# Системные зависимости: gcc для Python-пакетов, nodejs. ffmpeg — статический бинарник (apt ffmpeg тянет 270+ пакетов).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    curl \
    ca-certificates \
    xz-utils \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Статический ffmpeg (для speech_service: WebM -> OGG). Без apt — иначе mesa/x11/wayland и долгая сборка.
RUN curl -sL "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" | tar -xJ -C /tmp \
    && cp /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && chmod +x /usr/local/bin/ffmpeg \
    && rm -rf /tmp/ffmpeg-*

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
