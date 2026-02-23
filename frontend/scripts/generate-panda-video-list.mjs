/**
 * Build-time: сканирует public/panda-tamagotchi-video/, собирает ключи из panda-*.mp4,
 * пишет src/features/MyPanda/generated/videoReactions.ts (REACTIONS_WITH_VIDEO).
 * Запуск: npm run generate:panda-video или перед vite build (prebuild).
 */
import { readdirSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const videoDir = join(root, 'public', 'panda-tamagotchi-video');
const outPath = join(root, 'src', 'features', 'MyPanda', 'generated', 'videoReactions.ts');

let keys = [];
try {
  const files = readdirSync(videoDir, { withFileTypes: true });
  for (const f of files) {
    if (f.isFile() && f.name.endsWith('.mp4') && f.name.startsWith('panda-')) {
      const key = f.name.replace(/^panda-|\.mp4$/g, '');
      if (key) keys.push(key);
    }
  }
  keys.sort();
} catch (_) {
  // папка пуста или не существует — оставляем пустой массив
}

const outDir = dirname(outPath);
mkdirSync(outDir, { recursive: true });
writeFileSync(
  outPath,
  `/** Сгенерировано scripts/generate-panda-video-list.mjs — не редактировать вручную */\n\nexport const REACTIONS_WITH_VIDEO: string[] = ${JSON.stringify(keys)};\n`,
  'utf-8'
);
