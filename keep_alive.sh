#!/bin/bash

# Keep-alive script для Railway
# Пингует /health каждые 4 минуты чтобы держать контейнер активным

while true; do
    # Ждем 4 минуты (240 секунд)
    sleep 240

    # Пингуем локальный health endpoint
    curl -s http://localhost:8080/health > /dev/null 2>&1

    # Логируем (опционально)
    # echo "$(date): Keep-alive ping sent"
done
