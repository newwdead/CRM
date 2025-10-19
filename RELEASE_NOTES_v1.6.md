# Release Notes v1.6

**Дата релиза:** 19 октября 2025  
**Кодовое имя:** "Telegram Ready"

---

## 🎉 Основные улучшения

### 🔒 SSL/TLS Поддержка
- **Самоподписанные SSL сертификаты** для HTTPS доступа
- Конфигурация nginx для портов **80 (HTTP)** и **8443 (HTTPS)**
- Volume mapping для SSL сертификатов в docker-compose
- Документация по настройке Let's Encrypt для production

### 📱 Telegram Integration (Production Ready)
- **Telegram Polling скрипт** (`telegram_polling.py`) для автоматического получения сообщений
- **Systemd сервис** (`telegram-polling.service`) с автозапуском
- Поддержка двух режимов работы:
  - 🔄 **Polling** - для development и серверов за NAT
  - 🌐 **Webhook** - для production с публичным IP
- Endpoint `/telegram/webhook` теперь доступен через **HTTPS**
- Автоматическая обработка фотографий из Telegram
- Логирование и мониторинг через systemd

### 📚 Подробная документация
- **README.ru.md** - полная документация на русском языке с:
  - Подробным описанием структуры проекта
  - Комментариями к каждому модулю и файлу
  - Инструкциями по настройке и deployment
  - Разделом Troubleshooting
- **README.md** - обновленная английская версия
- **SSL_SETUP.md** - руководство по настройке SSL
- **TELEGRAM_SETUP.md** - детальная инструкция по Telegram
- **.env.example** - шаблон конфигурации

---

## 🔧 Технические изменения

### Frontend
- ✅ Добавлен endpoint `/telegram/webhook` в HTTPS блок nginx.conf (порт 8443)
- ✅ Конфигурация SSL сертификатов в nginx
- ✅ Порт 8443 добавлен в docker-compose.yml

### Backend
- ✅ Telegram webhook endpoint работает через HTTPS прокси
- ✅ Поддержка самоподписанных сертификатов

### Infrastructure
- ✅ Volume `/etc/nginx/certs` для SSL сертификатов
- ✅ Systemd сервис для автоматического запуска polling
- ✅ Скрипт `telegram_polling.py` с детальным логированием

---

## 📦 Новые файлы

```
+ README.ru.md                    # Подробная документация на русском
+ SSL_SETUP.md                    # Инструкция по SSL
+ TELEGRAM_SETUP.md               # Инструкция по Telegram
+ telegram_polling.py             # Скрипт для Telegram polling
+ telegram-polling.service        # Systemd сервис
+ .env.example                    # Шаблон переменных окружения
+ RELEASE_NOTES_v1.6.md           # Этот файл
```

---

## 🔄 Обновленные файлы

```
~ docker-compose.yml              # Добавлен порт 8443 и volume для SSL
~ frontend/nginx.conf             # Добавлен /telegram/webhook в HTTPS блок
~ README.md                       # Обновлена английская версия
```

---

## 🚀 Как обновиться с v1.5

### 1. Создать SSL сертификаты

```bash
# Создать директорию
sudo mkdir -p /etc/nginx/certs

# Сгенерировать самоподписанный сертификат
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/nginx/certs/selfsigned.key \
  -out /etc/nginx/certs/selfsigned.crt \
  -days 365 \
  -subj "/CN=localhost/O=BizCard CRM/C=RU"
```

### 2. Обновить код

```bash
git pull origin main
```

### 3. Пересобрать и перезапустить

```bash
docker compose down
docker compose up -d --build
```

### 4. Настроить Telegram (если нужно)

```bash
# Установить сервис
sudo cp telegram-polling.service /etc/systemd/system/
sudo systemctl daemon-reload

# Отредактировать токен
sudo nano /etc/systemd/system/telegram-polling.service

# Запустить
sudo systemctl enable telegram-polling
sudo systemctl start telegram-polling
```

---

## 🐛 Исправленные проблемы

- ✅ **#001** - Telegram webhook не работал через HTTPS (отсутствовал endpoint в HTTPS блоке nginx)
- ✅ **#002** - SSL сертификаты не были настроены для Telegram webhook
- ✅ **#003** - Отсутствовала документация по структуре проекта
- ✅ **#004** - Нет автоматического запуска Telegram polling

---

## 📊 Статистика

- **Новых файлов:** 7
- **Обновленных файлов:** 3
- **Строк кода:** +1,200
- **Строк документации:** +800

---

## 🔮 Планы на v1.7

### В разработке:
- 🎨 Темная тема для UI
- 🔍 Расширенный поиск и фильтрация
- 📊 Дашборд со статистикой
- 🏷️ Теги и категории для контактов
- 📧 Email уведомления
- 🔐 Аутентификация и роли пользователей
- 🌍 Поддержка дополнительных языков OCR
- 📱 PWA поддержка (Progressive Web App)

### Улучшения:
- Оптимизация OCR для лучшей точности
- Batch обработка нескольких визиток
- Интеграция с облачными хранилищами
- REST API v2 с версионированием

---

## 💡 Рекомендации

### Для Development:
- Используйте **Telegram Polling** режим
- Самоподписанный SSL сертификат достаточен
- Запускайте через `docker compose up -d`

### Для Production:
- Получите настоящий SSL сертификат (Let's Encrypt)
- Настройте **Telegram Webhook** режим
- Используйте `docker-compose.prod.yml`
- Настройте backup'ы базы данных
- Используйте прокси-сервер (Nginx/Caddy)

---

## 📝 Breaking Changes

**Нет breaking changes** - обратная совместимость с v1.5 полностью сохранена.

---

## 🙏 Благодарности

Спасибо всем, кто тестировал beta версию и оставлял фидбек!

---

## 📞 Поддержка

Если у вас возникли проблемы с обновлением:
- Прочитайте [README.ru.md](README.ru.md)
- Проверьте [SSL_SETUP.md](SSL_SETUP.md)
- Посмотрите [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
- Создайте Issue на GitHub

---

**Приятного использования v1.6! 🎉**

