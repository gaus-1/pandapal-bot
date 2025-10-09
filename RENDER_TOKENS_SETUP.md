# 🔑 Настройка 10 API токенов Gemini в Render

## 📋 **ПЕРЕМЕННЫЕ ДЛЯ RENDER DASHBOARD:**

### **1. Перейдите в Render Dashboard:**
- https://dashboard.render.com
- Найдите ваш сервис `pandapal-bot`
- Settings → Environment Variables

### **2. Добавьте переменные:**

**GEMINI_API_KEY** (основной токен):
```
AIzaSyDc24ihn9SZn5EN0hrBzA2lYQMSjxC9z6M
```

**GEMINI_API_KEYS** (дополнительные токены через запятую):
```
AIzaSyCZUurXQLCRtS8ciiHa3BcYIOpUhA4fCoU,AIzaSyBBKUir0mxvvt0b4Pg8v1a_ejKiSDGVFmw,AIzaSyChPUiERQIODpY3hetMXqYOoC6BQt48kxg,AIzaSyCaXpgIUO5dj5kEofK4RXmQNP219RjGx0I,AIzaSyBtyw1FtfxZd7Y9x4rSFjBswP-pQTUcmmo,AIzaSyD6cFYNIuUnvXwDoRYIiJclvWU_sWmhfXU,AIzaSyCBAQZiMOcVC0qxH3UAhA4lTWqVCYaVXIc,AIzaSyAaWk76xYpAK4yzu0xIVKcyJYE7RyEq7NU,AIzaSyB5gvnPzntr9MgbipSgJoahtBVz5p0aV40
```

## 🎯 **РЕЗУЛЬТАТ:**

После добавления переменных:
- ✅ **10 токенов** доступно для ротации
- ✅ **15,000 запросов в день** (10 × 1,500)
- ✅ **Автоматическое переключение** при исчерпании квоты
- ✅ **Непрерывная работа** бота 24/7

## 🔄 **КАК РАБОТАЕТ РОТАЦИЯ:**

1. **Используется основной токен** `GEMINI_API_KEY`
2. **При ошибке квоты** автоматически переключается на `GEMINI_API_KEYS`
3. **Циклическая ротация** между всеми токенами
4. **Сброс в новом дне** - токены снова доступны

## ⚡ **ПОСЛЕ НАСТРОЙКИ:**

1. **Сохраните переменные** в Render
2. **Дождитесь деплоя** (2-3 минуты)
3. **Протестируйте бота** - он должен отвечать
4. **Проверьте логи** - должны видеть переключения токенов

---

**🎯 ГЛАВНОЕ: Добавьте эти переменные в Render Dashboard!**

**После этого бот заработает с 15,000 запросов в день!** 🚀
