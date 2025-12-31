# 📋 Конфигурация DNS для Cloudflare

## ✅ Что настроить на reg.ru

### **NS-записи (Name Servers)**

Замените существующие NS-записи на:

```
NS1: ваши-ns1.ns.cloudflare.com
NS2: ваши-ns2.ns.cloudflare.com
```

**⚠️ ВАЖНО:** Cloudflare даст вам КОНКРЕТНЫЕ NS-записи при добавлении домена.

**Пример:**
```
alice.ns.cloudflare.com
bob.ns.cloudflare.com
```

---

## ✅ Что настроить в Cloudflare

### **DNS Records**

После активации домена в Cloudflare:

| Type | Name | Target | Proxy | TTL |
|------|------|--------|-------|-----|
| **CNAME** | `@` | `ваш-проект.up.railway.app` | ✅ Proxied | Auto |
| **CNAME** | `www` | `ваш-проект.up.railway.app` | ✅ Proxied | Auto |

**⚠️ Замените `ваш-проект.up.railway.app` на реальный URL из Railway!**

---

### **SSL/TLS Settings**

**Основной режим:**
```
SSL/TLS → Overview → Encryption mode: Flexible
```

**Дополнительные настройки:**
```
SSL/TLS → Edge Certificates:
- Always Use HTTPS: ON ✅
- Automatic HTTPS Rewrites: ON ✅
- Minimum TLS Version: TLS 1.2
- Opportunistic Encryption: ON ✅
- TLS 1.3: ON ✅
```

---

### **Speed Optimization (опционально)**

```
Speed → Optimization:
- Auto Minify: JavaScript ✅, CSS ✅, HTML ✅
- Brotli: ON ✅
- Rocket Loader: ON ✅ (опционально)
```

---

### **Security Settings (опционально)**

```
Security → Settings:
- Security Level: Medium
- Browser Integrity Check: ON ✅
```

---

## 🔍 Проверка настроек

### **1. Проверить NS-записи**

Откройте терминал (CMD/PowerShell):

```bash
nslookup -type=NS pandapal.ru
```

**Должно быть:**
```
nameserver = alice.ns.cloudflare.com
nameserver = bob.ns.cloudflare.com
```

---

### **2. Проверить CNAME**

```bash
nslookup pandapal.ru
```

**Должно быть:**
```
Name: pandapal.ru
Addresses: [IP адреса Cloudflare]
```

---

### **3. Проверить SSL**

Откройте браузер:
```
https://pandapal.ru
```

Нажмите на замок 🔒 → Должно быть "Соединение защищено"

---

## 📊 Визуальная схема

```
┌─────────────┐
│ reg.ru      │
│ (Регистратор│
│  домена)    │
└──────┬──────┘
       │ NS-записи указывают на Cloudflare
       ↓
┌─────────────────────────────────┐
│ Cloudflare                      │
│ (DNS + SSL + CDN)               │
│                                 │
│ - DNS: @ → railway.app          │
│ - SSL: Flexible                 │
│ - Proxy: ON (оранжевое облако)  │
└────────────┬────────────────────┘
             │ CNAME → Railway URL
             ↓
┌─────────────────────────────────┐
│ Railway.app                     │
│ (Хостинг вашего сайта)          │
│                                 │
│ - Frontend: React + Vite        │
│ - Backend: Python Bot           │
│ - Database: PostgreSQL          │
└─────────────────────────────────┘
```

---

## ✅ Итоговый чеклист

После настройки проверьте:

- [ ] NS-записи на reg.ru изменены на Cloudflare
- [ ] Cloudflare показывает статус "Active"
- [ ] DNS Records созданы (@ и www)
- [ ] Proxy status = Proxied (оранжевое облако)
- [ ] SSL/TLS = Flexible
- [ ] Always Use HTTPS = ON
- [ ] Сайт открывается на https://pandapal.ru
- [ ] Замок 🔒 в браузере (SSL работает)
- [ ] www.pandapal.ru тоже работает
- [ ] Работает без VPN из России

---

## 🆘 Если что-то не работает

1. **Подождите 2-6 часов** после изменения NS-записей
2. **Очистите кеш DNS:**
   ```bash
   ipconfig /flushdns
   ```
3. **Очистите кеш браузера:** Ctrl+Shift+Del
4. **Проверьте Railway:** проект должен быть запущен
5. **Проверьте логи Railway:** есть ли ошибки?

---

**Документ создан:** 31.12.2025
**Для проекта:** PandaPal Bot
**Платформа:** Railway + Cloudflare
