/**
 * Скрипт для анализа размера бандла
 * Соответствует стандартам 2025: бандл < 250KB
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distPath = path.join(__dirname, '../dist');

console.log('📊 Анализ размера бандла PandaPal Go 2025+\n');

if (!fs.existsSync(distPath)) {
  console.error('❌ Директория dist не найдена. Сначала выполните: npm run build');
  process.exit(1);
}

/**
 * Получить размер файла в KB
 */
const getFileSize = (filePath) => {
  const stats = fs.statSync(filePath);
  return (stats.size / 1024).toFixed(2);
};

/**
 * Рекурсивно получить все файлы
 */
const getAllFiles = (dirPath, arrayOfFiles = []) => {
  const files = fs.readdirSync(dirPath);

  files.forEach((file) => {
    const fullPath = path.join(dirPath, file);
    if (fs.statSync(fullPath).isDirectory()) {
      arrayOfFiles = getAllFiles(fullPath, arrayOfFiles);
    } else {
      arrayOfFiles.push(fullPath);
    }
  });

  return arrayOfFiles;
};

// Получаем все файлы
const allFiles = getAllFiles(distPath);

// Группируем по типам
const filesByType = {
  js: [],
  css: [],
  assets: [],
  html: [],
};

allFiles.forEach((file) => {
  const ext = path.extname(file);
  const relativePath = path.relative(distPath, file);
  const size = getFileSize(file);

  if (ext === '.js') {
    filesByType.js.push({ path: relativePath, size: parseFloat(size) });
  } else if (ext === '.css') {
    filesByType.css.push({ path: relativePath, size: parseFloat(size) });
  } else if (ext === '.html') {
    filesByType.html.push({ path: relativePath, size: parseFloat(size) });
  } else {
    filesByType.assets.push({ path: relativePath, size: parseFloat(size) });
  }
});

// Сортируем по размеру
Object.keys(filesByType).forEach((type) => {
  filesByType[type].sort((a, b) => b.size - a.size);
});

// Выводим результаты
console.log('📦 JavaScript файлы:');
console.log('━'.repeat(80));
let totalJS = 0;
filesByType.js.forEach((file) => {
  totalJS += file.size;
  const emoji = file.size > 250 ? '🔴' : file.size > 100 ? '🟡' : '🟢';
  console.log(`${emoji} ${file.path.padEnd(50)} ${file.size.toFixed(2).padStart(10)} KB`);
});
console.log('━'.repeat(80));
console.log(`📊 Всего JS: ${totalJS.toFixed(2)} KB`);

if (totalJS > 250) {
  console.log('⚠️  ПРЕДУПРЕЖДЕНИЕ: Общий размер JS > 250KB (стандарт 2025)');
  console.log('💡 Рекомендация: Используйте lazy loading для Three.js');
} else {
  console.log('✅ Размер JS соответствует стандартам 2025!');
}

console.log('\n🎨 CSS файлы:');
console.log('━'.repeat(80));
let totalCSS = 0;
filesByType.css.forEach((file) => {
  totalCSS += file.size;
  console.log(`  ${file.path.padEnd(50)} ${file.size.toFixed(2).padStart(10)} KB`);
});
console.log('━'.repeat(80));
console.log(`📊 Всего CSS: ${totalCSS.toFixed(2)} KB\n`);

console.log('🖼️  Assets файлы (топ-10):');
console.log('━'.repeat(80));
let totalAssets = 0;
filesByType.assets.slice(0, 10).forEach((file) => {
  totalAssets += file.size;
  console.log(`  ${file.path.padEnd(50)} ${file.size.toFixed(2).padStart(10)} KB`);
});
console.log('━'.repeat(80));
console.log(`📊 Всего Assets (топ-10): ${totalAssets.toFixed(2)} KB\n`);

// Общий размер
const total = totalJS + totalCSS + totalAssets;
console.log('📦 ОБЩИЙ РАЗМЕР:');
console.log('━'.repeat(80));
console.log(`  JavaScript:  ${totalJS.toFixed(2).padStart(10)} KB`);
console.log(`  CSS:         ${totalCSS.toFixed(2).padStart(10)} KB`);
console.log(`  Assets:      ${totalAssets.toFixed(2).padStart(10)} KB`);
console.log('━'.repeat(80));
console.log(`  ИТОГО:       ${total.toFixed(2).padStart(10)} KB\n`);

// Рекомендации
console.log('💡 Рекомендации по оптимизации:');
console.log('━'.repeat(80));

if (totalJS > 250) {
  console.log('1. ⚠️  Разделите Three.js на отдельный chunk с lazy loading');
  console.log('2. ⚠️  Используйте dynamic import для игровых компонентов');
}

if (totalCSS > 50) {
  console.log('3. ⚠️  Проверьте неиспользуемые CSS классы (PurgeCSS)');
}

const largeAssets = filesByType.assets.filter((f) => f.size > 100);
if (largeAssets.length > 0) {
  console.log(`4. ⚠️  Оптимизируйте большие ассеты: ${largeAssets.length} файлов > 100KB`);
}

if (total < 500) {
  console.log('✅ Общий размер отличный для стандартов 2025!');
} else if (total < 1000) {
  console.log('⚠️  Общий размер приемлемый, но можно оптимизировать');
} else {
  console.log('🔴 Общий размер превышает рекомендации для детской игры');
}

console.log('━'.repeat(80));
