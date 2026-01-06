#!/bin/bash
# Railway build script

set -e

echo "🔨 Railway build script started..."

# Устанавливаем зависимости
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Build completed successfully!"
