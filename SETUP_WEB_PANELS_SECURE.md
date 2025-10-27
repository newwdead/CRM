# 🔐 Безопасная Настройка Веб-Панелей (IP Whitelist + Поддомены)

**Дата:** 27 октября 2025  
**Метод:** IP Whitelist + Поддомены  
**Безопасность:** ✅✅ Высокая

---

## 📋 Что Вы Получите

```
🔗 https://minio.ibbase.ru  →  MinIO Console (только ваш IP)
🔗 https://label.ibbase.ru  →  Label Studio (только ваш IP)
```

**Защита:**
- ✅ Доступ только с вашего IP: `92.118.231.161`
- ✅ HTTPS с SSL сертификатом
- ✅ Защита паролем
- ✅ Остальной мир видит 403 Forbidden

---

## 🚀 Инструкция по Настройке

### Шаг 1: Добавить DNS Записи (5 минут)

**Где:** Панель управления вашим доменом (reg.ru, Cloudflare, и т.д.)

**Что добавить:**

#### Запись 1 - MinIO Console
```
Тип записи: A
Имя (Name): minio
Значение (Value/IP): 95.163.183.25
TTL: 300 (или оставить по умолчанию)
```

#### Запись 2 - Label Studio
```
Тип записи: A
Имя (Name): label
Значение (Value/IP): 95.163.183.25
TTL: 300 (или оставить по умолчанию)
```

**Результат после добавления:**
- `minio.ibbase.ru` будет указывать на сервер
- `label.ibbase.ru` будет указывать на сервер

**Проверка (через 5-15 минут):**
```bash
# Выполнить на сервере:
host minio.ibbase.ru
host label.ibbase.ru

# Должно вернуть:
# minio.ibbase.ru has address 95.163.183.25
# label.ibbase.ru has address 95.163.183.25
```

---

### Шаг 2: Получить SSL Сертификаты (автоматически)

**После того как DNS записи активны**, выполнить на сервере:

```bash
# Получить сертификаты для новых поддоменов
sudo certbot certonly --webroot -w /var/www/certbot \
  -d minio.ibbase.ru \
  -d label.ibbase.ru \
  --expand
```

**Что это делает:**
- Проверяет что домены указывают на сервер
- Автоматически получает SSL сертификаты от Let's Encrypt
- Сохраняет в `/etc/letsencrypt/live/ibbase.ru-0001/`

---

### Шаг 3: Применить Nginx Конфигурацию (автоматически)

**Выполнить автоматический скрипт:**

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
sudo bash scripts/setup_secure_web_panels.sh
```

**Что делает скрипт:**
1. Проверяет DNS записи
2. Получает SSL сертификаты
3. Создает Nginx конфигурацию с IP whitelist
4. Тестирует конфигурацию
5. Перезагружает Nginx

**IP Whitelist (только эти IP будут иметь доступ):**
- `92.118.231.161` - ваш текущий IP
- `10.0.0.0/8` - внутренние сети (VPN, если настроите)
- Все остальные получат `403 Forbidden`

---

## 🔐 Безопасность

### Что Защищено

#### 1. IP Whitelist
```nginx
# В конфигурации Nginx:
allow 92.118.231.161;  # Ваш IP
allow 10.0.0.0/8;      # Внутренние сети
deny all;              # Все остальные - блокировать
```

**Результат:** Только вы сможете открыть страницы

#### 2. HTTPS/SSL
- Все данные шифруются
- Let's Encrypt сертификат
- Автоматическое обновление через Certbot

#### 3. Пароли
- MinIO: admin / minio123456 (⚠️ сменить!)
- Label Studio: admin@ibbase.ru / [из .env] (⚠️ сменить!)

---

## 📝 После Настройки

### 1. Проверить Доступ

**С вашего IP (должно работать):**
```bash
# Открыть в браузере:
https://minio.ibbase.ru
https://label.ibbase.ru
```

**С другого IP (должно заблокироваться):**
```
403 Forbidden
```

### 2. Войти и Настроить

**MinIO Console:**
1. Открыть https://minio.ibbase.ru
2. Логин: `admin` / Пароль: `minio123456`
3. Создать bucket'ы:
   - `business-cards`
   - `ocr-results`
   - `training-data`
   - `models`
4. **⚠️ ВАЖНО:** Изменить пароль в `.env`:
   ```bash
   nano /home/ubuntu/fastapi-bizcard-crm-ready/.env
   # Изменить: MINIO_ROOT_PASSWORD=НОВЫЙ_ПАРОЛЬ
   docker compose restart minio
   ```

**Label Studio:**
1. Открыть https://label.ibbase.ru
2. Логин: `admin@ibbase.ru` / Пароль: [из .env]
3. Создать проект "Business Cards OCR Training"
4. Загрузить конфигурацию из `backend/app/integrations/label_studio_config.xml`
5. **⚠️ ВАЖНО:** Изменить пароль в `.env`:
   ```bash
   nano /home/ubuntu/fastapi-bizcard-crm-ready/.env
   # Изменить: LABEL_STUDIO_PASSWORD=НОВЫЙ_ПАРОЛЬ
   docker compose restart label-studio
   ```

---

## 🔧 Управление IP Whitelist

### Добавить Новый IP

Если нужен доступ с другого компьютера/IP:

```bash
# 1. Узнать IP
curl ifconfig.me

# 2. Добавить в конфигурацию
sudo nano /etc/nginx/sites-available/minio-label-subdomains

# 3. Добавить строку в оба server блока (minio и label):
allow НОВЫЙ_IP;  # Комментарий

# 4. Перезагрузить Nginx
sudo nginx -t && sudo systemctl reload nginx
```

### Разрешить Всем (не рекомендуется!)

Если хотите открыть доступ всем:

```bash
# Закомментировать IP whitelist в конфигурации:
sudo nano /etc/nginx/sites-available/minio-label-subdomains

# Заменить:
allow 92.118.231.161;
deny all;

# На:
# allow 92.118.231.161;
# deny all;

# Перезагрузить:
sudo systemctl reload nginx
```

---

## 🆘 Troubleshooting

### Проблема: DNS не резолвится

**Симптом:** `host minio.ibbase.ru` возвращает `not found`

**Решение:**
1. Проверить DNS записи в панели управления доменом
2. Подождать 5-15 минут (DNS propagation)
3. Очистить DNS кеш:
   ```bash
   sudo systemd-resolve --flush-caches
   ```

---

### Проблема: Certbot не может получить сертификат

**Симптом:** Ошибка при запуске `certbot`

**Решение:**
1. Убедиться что DNS записи активны
2. Проверить что порт 80 открыт:
   ```bash
   sudo ufw status
   curl -I http://minio.ibbase.ru
   ```
3. Проверить логи:
   ```bash
   sudo tail -f /var/log/letsencrypt/letsencrypt.log
   ```

---

### Проблема: 403 Forbidden даже с моего IP

**Симптом:** Не могу открыть страницу, хотя мой IP должен быть разрешен

**Решение:**
1. Проверить ваш текущий IP:
   ```bash
   curl ifconfig.me
   ```
2. Сравнить с IP в конфигурации:
   ```bash
   sudo grep "allow" /etc/nginx/sites-available/minio-label-subdomains
   ```
3. Если IP изменился, обновить конфигурацию

---

### Проблема: Страницы не загружаются

**Симптом:** Белый экран или ошибка загрузки

**Решение:**
1. Проверить что контейнеры запущены:
   ```bash
   docker ps | grep -E "(minio|label-studio)"
   ```
2. Проверить логи Nginx:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```
3. Проверить прокси:
   ```bash
   curl -I http://localhost:9001  # MinIO
   curl -I http://localhost:8081  # Label Studio
   ```

---

## 📊 Мониторинг

### Проверить Кто Подключается

```bash
# Логи доступа
sudo tail -f /var/log/nginx/access.log | grep -E "(minio|label)"

# Заблокированные попытки
sudo tail -f /var/log/nginx/error.log | grep "403"
```

### Статистика Блокировок

```bash
# Сколько попыток заблокировано за последний час
sudo grep "403" /var/log/nginx/access.log | grep -E "(minio|label)" | wc -l
```

---

## ✅ Checklist После Настройки

- [ ] DNS записи добавлены и активны
- [ ] SSL сертификаты получены
- [ ] Nginx конфигурация применена
- [ ] MinIO Console открывается по https://minio.ibbase.ru
- [ ] Label Studio открывается по https://label.ibbase.ru
- [ ] Проверено что с другого IP доступ заблокирован (403)
- [ ] Пароль MinIO изменен в .env
- [ ] Пароль Label Studio изменен в .env
- [ ] Bucket'ы созданы в MinIO
- [ ] Проект создан в Label Studio

---

## 🎯 Итоговая Конфигурация

```
Защита:
✅ IP Whitelist (только 92.118.231.161)
✅ HTTPS/SSL (Let's Encrypt)
✅ Пароли (после смены)

Доступ:
🔗 MinIO Console: https://minio.ibbase.ru
🔗 Label Studio: https://label.ibbase.ru

Credentials:
📦 MinIO: admin / [NEW_PASSWORD]
🏷️ Label Studio: admin@ibbase.ru / [NEW_PASSWORD]

Безопасность: ⭐⭐⭐⭐ (4/5)
Удобство: ⭐⭐⭐⭐⭐ (5/5)
```

---

**Готово к использованию после выполнения 3 шагов!** 🚀


