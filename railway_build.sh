#!/bin/bash
# Railway build script - создает обфусцированные файлы перед запуском
# Это обеспечивает защиту от копирования кода

set -e

echo "🔨 Railway build script started..."

# Устанавливаем зависимости (включая PyArmor)
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Создаем обфусцированные файлы конфигурации
echo "📦 Creating obfuscated config files..."
if [ -f "scripts/optimize_config.py" ]; then
    python scripts/optimize_config.py
else
    echo "⚠️ WARNING: scripts/optimize_config.py not found, skipping config obfuscation"
fi

# Создаем обфусцированные файлы сервисов
echo "📦 Creating obfuscated service files..."
if [ -f "scripts/optimize_service.py" ]; then
    python scripts/optimize_service.py
else
    echo "⚠️ WARNING: scripts/optimize_service.py not found, skipping service obfuscation"
fi

echo "✅ Build completed successfully!"
