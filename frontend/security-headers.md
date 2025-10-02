# 🛡️ Конфигурация заголовков безопасности для Render

### Настройка в Render Dashboard:

**Перейдите:** `Render Dashboard → pandapal-frontend → Settings → Headers`

### Добавьте следующие заголовки:

#### 1. **X-Frame-Options** (защита от clickjacking)
```
Path: /*
Name: X-Frame-Options
Value: DENY
```

#### 2. **X-Content-Type-Options** (защита от MIME-sniffing)
```
Path: /*
Name: X-Content-Type-Options
Value: nosniff
```

#### 3. **X-XSS-Protection** (XSS фильтр для старых браузеров)
```
Path: /*
Name: X-XSS-Protection
Value: 1; mode=block
```

#### 4. **Referrer-Policy** (защита от утечки referrer)
```
Path: /*
Name: Referrer-Policy
Value: strict-origin-when-cross-origin
```

#### 5. **Permissions-Policy** (запрет доступа к устройствам)
```
Path: /*
Name: Permissions-Policy
Value: geolocation=(), microphone=(), camera=(), payment=(), usb=()
```

#### 6. **Strict-Transport-Security** (принудительный HTTPS)
```
Path: /*
Name: Strict-Transport-Security
Value: max-age=31536000; includeSubDomains; preload
```

#### 7. **Content-Security-Policy** (защита от XSS и injection)
```
Path: /*
Name: Content-Security-Policy
Value: default-src 'self'; script-src 'self' https://telegram.org https://www.googletagmanager.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.pandapal.ru; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests;
```

### ⚠️ ВАЖНО:
- Добавляйте заголовки **ПО ОДНОМУ**
- После каждого заголовка нажимайте **"Add Header"**
- Сохраните изменения и сделайте **Manual Deploy**

### 🎯 Результат:
После настройки этих заголовков PandaPal будет защищён от:
- ❌ XSS атак
- ❌ Clickjacking
- ❌ MIME-sniffing атак
- ❌ Утечки данных через referrer
- ❌ Доступа к камере/микрофону
- ❌ HTTP downgrade атак

**Максимальная защита детей обеспечена! 🛡️🐼**
