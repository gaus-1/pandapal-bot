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

# Статический ffmpeg (для speech_service: WebM -> OGG).
# Primary source может быть временно недоступен в CI, поэтому есть fallback.
RUN set -eux; \
    FFMPEG_PRIMARY_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"; \
    FFMPEG_FALLBACK_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"; \
    if curl -fsSL --retry 5 --retry-all-errors "$FFMPEG_PRIMARY_URL" -o /tmp/ffmpeg.tar.xz; then \
        tar -xJf /tmp/ffmpeg.tar.xz -C /tmp; \
        cp /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg; \
    else \
        curl -fsSL --retry 5 --retry-all-errors "$FFMPEG_FALLBACK_URL" -o /tmp/ffmpeg.tar.xz; \
        tar -xJf /tmp/ffmpeg.tar.xz -C /tmp; \
        cp /tmp/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg /usr/local/bin/ffmpeg; \
    fi; \
    chmod +x /usr/local/bin/ffmpeg; \
    /usr/local/bin/ffmpeg -version; \
    rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg-*-amd64-static /tmp/ffmpeg-master-latest-linux64-gpl

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
