# Browser Cache Issue - v3.2.0

## Проблема

Пользователь сообщает ошибку:
```
Error fetching services: SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
(anonymous) @ 725.fe4d23e7.chunk.js:1
```

**Ключевой момент:** Файл `725.fe4d23e7.chunk.js` - это **СТАРЫЙ** bundle!

## Анализ

### На Сервере (v3.2.0)
```bash
$ docker exec bizcard-frontend ls /usr/share/nginx/html/static/js/
```
**НЕТ** файла `725.fe4d23e7.chunk.js` ❌

**Есть новые файлы:**
- `main.5a42b061.js` (новая версия)
- Другие chunk файлы с новыми хешами

### У Пользователя (браузер)
Загружается `725.fe4d23e7.chunk.js` - **старый** bundle, который содержит код:
```javascript
fetch("".concat(B,"/services/status"))  // B = '', без /api/ prefix
```

## Root Cause

**Browser Cache!**

1. Пользователь ранее открывал сайт с версией v3.1.9 (или ранее)
2. Браузер закэшировал файл `725.fe4d23e7.chunk.js`
3. Мы задеплоили v3.2.0 с исправлениями
4. Новый `index.html` загружается, но JS файлы берутся из кэша браузера
5. Старый JS вызывает `/services/status` (без `/api/`)
6. Nginx возвращает HTML 404
7. JavaScript пытается распарсить HTML → ошибка

## Решение для Пользователя

### 1. Hard Refresh (Принудительная перезагрузка)

**Windows/Linux:**
- `Ctrl + Shift + R`
- Или `Ctrl + F5`

**Mac:**
- `Cmd + Shift + R`
- Или `Cmd + Option + R`

### 2. Очистка Кэша Браузера

**Chrome/Edge:**
1. Откройте DevTools (F12)
2. Правой кнопкой мыши на кнопку "Обновить" в панели инструментов
3. Выберите "Очистить кэш и выполнить жёсткую перезагрузку"

**Firefox:**
1. `Ctrl + Shift + Del`
2. Выберите "Кэш"
3. "Удалить сейчас"

**Или:**
1. Settings → Privacy → Clear browsing data
2. Выберите "Cached images and files"
3. Clear data

### 3. Incognito Mode (Проверка)

Откройте в режиме инкогнито:
- Chrome: `Ctrl + Shift + N`
- Firefox: `Ctrl + Shift + P`

Если в инкогнито работает - точно проблема кэша!

## Технические Детали

### Старый Bundle (725.fe4d23e7.chunk.js)
```javascript
const API_BASE = '';  // Пустая строка
fetch(`${API_BASE}/services/status`)  // = '/services/status'
```

### Новый Bundle (должен быть в main.5a42b061.js)
```javascript
const API_BASE = '/api';  // Добавлен /api prefix
fetch(`${API_BASE}/services/status`)  // = '/api/services/status'
```

### Почему Nginx возвращает HTML?

Без `/api/` prefix:
```
User → GET /services/status
  ↓
Nginx (location /) → Try static file
  ↓
File not found → Return index.html (SPA fallback)
  ↓
Browser gets HTML instead of JSON
  ↓
JSON.parse(HTML) → SyntaxError: Unexpected token '<'
```

С `/api/` prefix:
```
User → GET /api/services/status
  ↓
Nginx (location /api/) → Proxy to backend:8000
  ↓
Backend → Return JSON
  ↓
✅ Works!
```

## Проверка После Очистки Кэша

После hard refresh, откройте DevTools (F12) → Network tab:

1. Найдите запрос к `main.*.js`
2. Проверьте статус: должен быть **200** (не 304 Not Modified)
3. Проверьте размер: должен быть полный размер файла
4. Найдите запрос к `/api/services/status`
5. Должен возвращать JSON (не HTML)

## Prevention (Для Будущего)

### 1. Cache Busting через Service Worker

Файл: `public/service-worker.js`

```javascript
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          return caches.delete(cacheName);
        })
      );
    })
  );
});
```

### 2. Versioned Build Filenames

Create React App уже делает это! Все JS файлы имеют hash в названии:
- `main.5a42b061.js` (hash: 5a42b061)
- При изменении кода → новый hash → новое имя файла

**НО!** Это не помогает, если браузер кэширует `index.html`.

### 3. Cache-Control Headers в Nginx

Файл: `frontend/nginx.conf`

```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location / {
    try_files $uri /index.html;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    expires 0;
}
```

**Объяснение:**
- `/static/` (JS/CSS) → кэшируется 1 год (hash в имени = auto cache busting)
- `/` (index.html) → НЕ кэшируется → всегда fresh

### 4. Version Query Parameter

В `index.html`:
```html
<script src="/static/js/main.js?v=3.2.0"></script>
```

При изменении версии → браузер загрузит новый файл.

## Summary

**Проблема:** Browser cache
**Причина:** Браузер загружает старый JS bundle  
**Решение:** Hard refresh (Ctrl+Shift+R) или очистка кэша

**Это НЕ баг в коде!** Код на сервере правильный. Просто пользователю нужно обновить кэш браузера.

---

## Instructions for User (Russian)

# ⚠️ Требуется Очистка Кэша Браузера

Ваш браузер использует старую версию сайта из кэша.

## Быстрое Решение:

### 1. Жёсткая Перезагрузка (Hard Refresh)

Нажмите одновременно:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

### 2. Если не помогло:

1. Откройте DevTools (F12)
2. Правой кнопкой на кнопку "Обновить" ⟳
3. Выберите "Очистить кэш и выполнить жёсткую перезагрузку"

### 3. Проверка:

Откройте в режиме инкогнито:
- `Ctrl + Shift + N` (Chrome)
- `Ctrl + Shift + P` (Firefox)

Если в инкогнито работает → очистите кэш основного браузера.

---

## Instructions for User (English)

# ⚠️ Browser Cache Refresh Required

Your browser is using an old cached version of the site.

## Quick Fix:

### 1. Hard Refresh

Press:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

### 2. If that doesn't work:

1. Open DevTools (F12)
2. Right-click the Reload button ⟳
3. Select "Empty Cache and Hard Reload"

### 3. Test:

Open in Incognito mode:
- `Ctrl + Shift + N` (Chrome)
- `Ctrl + Shift + P` (Firefox)

If it works in incognito → clear your main browser cache.

---

**После очистки кэша все должно работать! ✅**

