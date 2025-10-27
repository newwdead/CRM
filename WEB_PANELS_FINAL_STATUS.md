# ✅ Web Panels - Final Status

**Date:** October 27, 2025  
**Version:** 6.0.0 (OCR v2.0)  
**Status:** ✅ BOTH WORKING

---

## 🎉 MinIO Console - WORKING ✅

### 🔐 Доступ
- **URL:** https://ibbase.ru/minio/
- **Username:** `admin`
- **Password:** `minio123456`
- **Status:** ✅ Веб-интерфейс работает полностью

### 📦 Созданные бакеты (4)
- ✅ `business-cards` - изображения визиток (public download)
- ✅ `ocr-results` - результаты OCR (private)
- ✅ `training-data` - данные обучения (private)
- ✅ `models` - ML модели (private)

### 🔧 Backend интеграция
- ✅ MinIOClient настроен
- ✅ StorageService готов
- ✅ BUCKET_NAMES экспортированы

---

## 🏷️ Label Studio - WORKING ✅

### 🔐 Доступ
- **URL:** https://ibbase.ru/label-studio/
- **Email:** `admin@ibbase.ru`
- **Password:** `_sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE`
- **Status:** ✅ Веб-интерфейс работает

### 🎨 Назначение
- Аннотирование визиток для обучения LayoutLMv3
- Создание размеченных датасетов
- Валидация OCR результатов

### 🔧 Backend интеграция
- ✅ Label Studio API готов к использованию
- ✅ Доступ к изображениям из `./uploads` (read-only)
- ✅ Конфигурация для визиток настроена

---

## 📊 Архитектура доступа

```
┌─────────────────────────────────────────┐
│  https://ibbase.ru (Nginx Reverse Proxy)│
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐      ┌────────────────┐
│ /minio/       │      │ /label-studio/ │
│ → 9001 port   │      │ → 8081 port    │
└───────────────┘      └────────────────┘
        │                       │
        ▼                       ▼
┌───────────────┐      ┌────────────────┐
│ MinIO Console │      │ Label Studio   │
│ (SPA)         │      │ (Django SPA)   │
└───────────────┘      └────────────────┘
        │
        ▼
┌───────────────┐
│ MinIO API     │
│ 9000 port     │
└───────────────┘
```

---

## 🎯 Решение проблемы входа в MinIO

### ❌ Проблема:
```
POST /minio/api/v1/login HTTP/2.0" 401 Unauthorized
```

### ✅ Решение:
Убрали переопределение `MINIO_SERVER_URL` в docker-compose.yml:

**Было:**
```yaml
MINIO_BROWSER_REDIRECT_URL: https://ibbase.ru/minio/
MINIO_SERVER_URL: https://ibbase.ru/api/minio  # ❌ Ломало аутентификацию
```

**Стало:**
```yaml
MINIO_BROWSER_REDIRECT: "on"  # ✅ MinIO сам управляет путями
```

### 📝 Причина:
MinIO Console (SPA в браузере) делал API запросы к неправильному URL, что приводило к ошибкам аутентификации. Позволив MinIO самому управлять путями, проблема решилась.

---

## 🧪 Проверка работоспособности

### MinIO Console
```bash
# 1. Откройте в браузере
https://ibbase.ru/minio/

# 2. Войдите
Username: admin
Password: minio123456

# 3. Проверьте бакеты
Buckets → Должны увидеть 4 бакета

# 4. Загрузите тестовое изображение
business-cards → Upload → Upload File
```

### Label Studio
```bash
# 1. Откройте в браузере
https://ibbase.ru/label-studio/

# 2. Войдите
Email: admin@ibbase.ru
Password: _sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE

# 3. Создайте проект
Projects → Create → Business Card Annotation
```

---

## 🔄 Интеграция с OCR v2.0

### Workflow визиток:

```
1. Пользователь загружает визитку
   ↓
2. Frontend → Backend API
   ↓
3. Backend сохраняет в MinIO
   → business-cards/card_123_20251027.jpg
   ↓
4. OCR Processing (PaddleOCR + LayoutLMv3)
   ↓
5. Результат в MinIO + Database
   → ocr-results/result_123.json
   → PostgreSQL (contact data)
   ↓
6. Label Studio (опционально)
   → Аннотация для обучения
   → training-data/annotated_123.json
   ↓
7. Training Pipeline (опционально)
   → Fine-tune LayoutLMv3
   → models/layoutlm_v3_finetuned.pt
```

---

## 📈 Мониторинг

### MinIO
- **Console Dashboard:** https://ibbase.ru/minio/
  - Object Browser
  - Storage Usage
  - Metrics (если включены)

### Label Studio
- **Dashboard:** https://ibbase.ru/label-studio/
  - Projects Overview
  - Annotation Progress
  - Team Performance

---

## 🔐 Безопасность

### Текущая конфигурация:
| Компонент | Метод доступа | Безопасность |
|-----------|---------------|--------------|
| MinIO Console | HTTPS + Auth | ✅ Хорошо |
| MinIO API | localhost only | ✅ Отлично |
| Label Studio | HTTPS + Auth | ✅ Хорошо |
| Nginx Reverse Proxy | HTTPS + SSL | ✅ Отлично |

### Рекомендации:
1. **Сменить пароли по умолчанию** (особенно MinIO)
2. **Создать отдельные Access Keys** для backend приложений
3. **Настроить 2FA** для Label Studio (опционально)
4. **Ограничить доступ по IP** (если известны фиксированные IP)

---

## 📝 Полезные команды

### MinIO
```bash
# Проверить статус контейнера
docker ps --filter name=bizcard-minio

# Посмотреть логи
docker logs bizcard-minio

# Список бакетов
docker exec bizcard-minio mc ls local/

# Загрузить файл
docker exec bizcard-minio mc cp /tmp/image.jpg local/business-cards/

# Статистика использования
docker exec bizcard-minio mc du local/business-cards/
```

### Label Studio
```bash
# Проверить статус контейнера
docker ps --filter name=bizcard-label-studio

# Посмотреть логи
docker logs bizcard-label-studio

# Перезапустить
docker compose restart label-studio
```

---

## 🎊 Итого

| Система | URL | Status | Credentials |
|---------|-----|--------|-------------|
| **MinIO Console** | https://ibbase.ru/minio/ | ✅ WORKING | admin / minio123456 |
| **Label Studio** | https://ibbase.ru/label-studio/ | ✅ WORKING | admin@ibbase.ru / [см. выше] |
| **MinIO Buckets** | 4 бакета созданы | ✅ READY | - |
| **Backend Integration** | MinIOClient + StorageService | ✅ READY | - |

---

## 🚀 Следующие шаги

1. ✅ MinIO настроен и работает
2. ✅ Label Studio настроен и работает
3. ⏳ **Протестировать загрузку визитки через UI**
4. ⏳ **Проверить сохранение в MinIO**
5. ⏳ **Проверить OCR обработку**
6. ⏳ **Настроить аннотацию в Label Studio**

---

## 🐛 Troubleshooting

### MinIO: Не могу войти
- Проверьте credentials: `admin` / `minio123456`
- Проверьте логи: `docker logs bizcard-minio`
- Перезапустите контейнер: `docker compose restart minio`

### Label Studio: Не могу войти
- Email: `admin@ibbase.ru`
- Password из `.env`: `_sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE`
- Проверьте логи: `docker logs bizcard-label-studio`

### Пустые страницы / 404 ошибки
- Проверьте Nginx: `sudo nginx -t`
- Перезагрузите Nginx: `sudo systemctl reload nginx`
- Проверьте логи: `sudo tail -f /var/log/nginx/error.log`

---

**🎉 Обе системы полностью функциональны и готовы к использованию!**

Подробности:
- [MINIO_SETUP_COMPLETE.md](./MINIO_SETUP_COMPLETE.md) - детали MinIO
- [WEB_PANELS_SETUP_COMPLETE.md](./WEB_PANELS_SETUP_COMPLETE.md) - детали обеих систем


