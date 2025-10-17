/**
 * Скрипт для копирования README файлов в public директорию.
 * Позволяет фронтенду загружать README.md и README_EN.md через HTTP.
 */

const fs = require('fs');
const path = require('path');

// Пути к файлам
const sourceDir = path.join(__dirname, '../../');
const targetDir = path.join(__dirname, '../public/');

// Список файлов для копирования
const filesToCopy = ['README.md', 'README_EN.md'];

console.log('📚 Копирование README файлов для фронтенда...');

// Создаём public директорию если её нет
if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}

// Копируем файлы
filesToCopy.forEach(filename => {
  const sourcePath = path.join(sourceDir, filename);
  const targetPath = path.join(targetDir, filename);

  if (fs.existsSync(sourcePath)) {
    fs.copyFileSync(sourcePath, targetPath);
    console.log(`✅ Скопирован: ${filename}`);
  } else {
    console.log(`❌ Файл не найден: ${filename}`);
  }
});

console.log('🎉 README файлы скопированы в public/');
