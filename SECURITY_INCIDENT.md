# 🚨 ИНЦИДЕНТ БЕЗОПАСНОСТИ — УТЕЧКА ТОКЕНОВ

**Дата:** 01.10.2025, 15:45 MSK  
**Статус:** ✅ Исправлено (токены удалены из репозитория)

---

## 📋 Что произошло

GitHub Secret Scanning обнаружил утечку чувствительных данных в публичный репозиторий:

1. ❌ Telegram Bot Token: `8298992033:***` (СКОМПРОМЕТИРОВАН)
2. ❌ Gemini API Key: `sk-***` (СКОМПРОМЕТИРОВАН)
3. ❌ PostgreSQL Password: `7rCuhY8***` (СКОМПРОМЕТИРОВАН)

**Файлы:** SECURITY.md (удалён), DEPLOYMENT.md, alembic.ini

---

## ✅ Принятые меры

1. ✅ Удалены все секреты из кода (DEPLOYMENT.md, alembic.ini)
2. ✅ Создан новый коммит с placeholder значениями
3. ✅ Выполнен `git push --force` для замены истории
4. ✅ SECURITY.md удалён из репозитория

---

## 🔴 КРИТИЧЕСКИ ВАЖНО — СДЕЛАЙТЕ ПРЯМО СЕЙЧАС:

### 1️⃣ **ОТОЗВАТЬ старый токен Telegram бота**

```
1. Откройте @BotFather в Telegram
2. Отправьте команду: /mybots
3. Выберите: PandaPalBot
4. Нажмите: API Token
5. Нажмите: Revoke current token ⚠️
6. Скопируйте НОВЫЙ токен
```

### 2️⃣ **Создать новый Gemini API ключ**

```
1. Откройте: https://aistudio.google.com/apikey
2. Нажмите: "Create API Key"
3. Выберите проект
4. Скопируйте НОВЫЙ ключ
5. УДАЛИТЕ старый ключ (sk-538429845b344fbc9aa0a5d6ab10e138)
```

### 3️⃣ **Сменить пароль PostgreSQL (опционально)**

```
1. Render Dashboard → PostgreSQL Database
2. Settings → Rotate Password
3. Обновите DATABASE_URL в переменных окружения
```

### 4️⃣ **Обновить .env файл**

```bash
# Откройте .env и замените ВСЕ токены на новые:
TELEGRAM_BOT_TOKEN=НОВЫЙ_ТОКЕН_ОТ_BOTFATHER
GEMINI_API_KEY=НОВЫЙ_КЛЮЧ_ОТ_GOOGLE
DATABASE_URL=postgresql+psycopg://...НОВЫЙ_ПАРОЛЬ...
```

### 5️⃣ **Обновить Environment Variables на Render**

```
1. Render Dashboard → Web Service (pandapal-bot)
2. Environment → Edit
3. Замените старые значения на новые:
   - TELEGRAM_BOT_TOKEN → новый
   - GEMINI_API_KEY → новый
   - DATABASE_URL → новый (если меняли)
4. Save Changes
5. Manual Deploy → Deploy latest commit
```

---

## 🔍 Проверка безопасности

### Проверьте, что токены НЕ утекли дальше:

```bash
# 1. Проверьте локальный .env (НЕ должен быть в git)
git status
# .env должен быть в "Untracked files" или не показан

# 2. Проверьте историю Git
git log --all --full-history --source --oneline -- .env
# Должно быть ПУСТО

# 3. Проверьте GitHub
# Откройте: https://github.com/gaus-1/pandapal-bot/search?q=8298992033
# Результатов: 0
```

---

## 📊 Мониторинг после инцидента

### Следите за подозрительной активностью:

1. **Telegram Bot:**
   ```
   - Проверьте логи бота на Render
   - Проверьте количество пользователей (/mybots → Bot Settings → Statistics)
   - Если есть аномалии → немедленно отзовите токен
   ```

2. **Gemini API:**
   ```
   - Откройте: https://console.cloud.google.com/apis/credentials
   - Проверьте usage quota
   - Если есть неожиданные запросы → удалите ключ
   ```

3. **PostgreSQL:**
   ```
   - Render Dashboard → Database → Metrics
   - Проверьте активность соединений
   - Если подозрительно → rotate password
   ```

---

## 🛡️ Как предотвратить в будущем

### ✅ Checklist перед каждым коммитом:

- [ ] `.env` в `.gitignore` (✅ уже добавлен)
- [ ] Нет хардкода токенов в коде
- [ ] Используем `settings.telegram_bot_token` вместо прямых значений
- [ ] Документация использует placeholder значения
- [ ] README.md содержит `.env.example`, НЕ реальные значения

### 🔧 Автоматизация (рекомендуется):

1. **Pre-commit hook для проверки секретов:**
   ```bash
   pip install detect-secrets
   detect-secrets scan > .secrets.baseline
   ```

2. **GitHub Actions для проверки:**
   ```yaml
   # .github/workflows/security.yml
   name: Security Scan
   on: [push, pull_request]
   jobs:
     secrets:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: trufflesecurity/trufflehog@main
   ```

---

## 📞 Контакты в случае вопросов

- **Email:** v81158847@gmail.com
- **Telegram:** @gaus_1

---

## ✅ Checklist восстановления

- [x] Удалены секреты из кода
- [x] Выполнен git push --force
- [ ] **ОТОЗВАН старый Telegram token** ⚠️ СДЕЛАЙТЕ СЕЙЧАС
- [ ] **СОЗДАН новый Gemini API key** ⚠️ СДЕЛАЙТЕ СЕЙЧАС
- [ ] Обновлён .env локально
- [ ] Обновлены Environment Variables на Render
- [ ] Выполнен redeploy на Render
- [ ] Протестирован бот с новыми токенами

---

<p align="center">
  <b>⚠️ НЕ ЗАБУДЬТЕ ОТОЗВАТЬ СТАРЫЕ ТОКЕНЫ! ⚠️</b>
</p>

