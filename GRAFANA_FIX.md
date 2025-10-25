# 🔧 Проблема доступа к Grafana - ДИАГНОСТИКА

**Проблема:** https://ibbase.ru:3001 не доступна
**Дата:** 24 октября 2025

---

## ✅ ЧТО РАБОТАЕТ:

1. ✅ Grafana контейнер запущен (Up 4 days)
2. ✅ Порт 3001 слушает на 0.0.0.0
3. ✅ Локальный доступ работает: http://localhost:3001

---

## ❌ ПРОБЛЕМА:

**Nginx не настроен для проксирования Grafana!**

HTTPS доступ на порт 3001 не работает, потому что:
- SSL сертификат настроен только для порта 443 (основное приложение)
- Прямой доступ к порту 3001 через HTTPS невозможен
- Нужен Nginx reverse proxy

---

## 🔧 РЕШЕНИЕ:

### Вариант A: Nginx Reverse Proxy (Рекомендуется ✅)

Добавить в Nginx конфигурацию:

```nginx
# /etc/nginx/sites-enabled/ibbase.ru

# Grafana
location /grafana/ {
    proxy_pass http://localhost:3001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support (для real-time updates)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# Prometheus (опционально)
location /prometheus/ {
    proxy_pass http://localhost:9090/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Результат:**
- ✅ Доступ: https://ibbase.ru/grafana/
- ✅ Использует существующий SSL сертификат
- ✅ Безопасно

---

### Вариант B: Прямой HTTPS на 3001 (Не рекомендуется ⚠️)

Настроить отдельный SSL на порту 3001:
- Требует отдельный SSL сертификат
- Требует открытие порта 3001 в firewall
- Менее безопасно

---

## 🚀 БЫСТРОЕ ИСПРАВЛЕНИЕ:

### Шаг 1: Найти Nginx конфиг
```bash
ls -la /etc/nginx/sites-enabled/
```

### Шаг 2: Отредактировать конфиг
```bash
sudo nano /etc/nginx/sites-enabled/ibbase.ru
# или
sudo nano /etc/nginx/sites-enabled/default
```

### Шаг 3: Добавить Grafana location
(Вставить конфигурацию из Варианта A)

### Шаг 4: Проверить конфиг
```bash
sudo nginx -t
```

### Шаг 5: Перезагрузить Nginx
```bash
sudo systemctl reload nginx
```

### Шаг 6: Проверить доступ
```
https://ibbase.ru/grafana/
```

---

## 📋 ВРЕМЕННОЕ РЕШЕНИЕ:

Пока Nginx не настроен, можно использовать:

**SSH туннель:**
```bash
# На локальной машине:
ssh -L 3001:localhost:3001 ubuntu@ibbase.ru

# Затем открыть в браузере:
http://localhost:3001
```

**Или прямой HTTP (небезопасно!):**
```
http://ibbase.ru:3001
```
⚠️  Но это работает только если firewall разрешает!

---

## 🎯 ЧТО ДАЛЬШЕ:

1. Найти Nginx конфигурацию
2. Добавить location /grafana/
3. Reload Nginx
4. Проверить https://ibbase.ru/grafana/

---

**На русском! 🇷🇺**
