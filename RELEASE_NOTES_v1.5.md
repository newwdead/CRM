# Release Notes v1.5

## Новое / Изменения
- **VK Cloud (без домена) подготовка деплоя**
  - `frontend/nginx.conf`: проксирование `/api/*` → `backend:8000`, `/files/*` → `backend:8000/files/*`.
  - Фронтенд переведён на относительные URL (`/api`, `/files`) в:
    - `frontend/src/components/ContactList.js`
    - `frontend/src/components/ContactEdit.js`
    - `frontend/src/components/ImportExport.js`
    - `frontend/src/components/UploadCard.js`
    - `frontend/src/components/TelegramSettings.js`
  - Добавлен `docker-compose.prod.yml`: наружу публикуется только фронт `80:80`, бэкенд доступен через прокси; тома для БД и `uploads/`.
- **Надёжная инициализация БД**
  - В `backend/app/main.py` добавлена функция `init_db_with_retry()` для гарантированного создания таблиц и лёгких миграций (ретраи при старте).
  - Безопасный бэкофилл `uid`.

## Ранее (v1.4)
- **UI**: колонка `Действия` (Фото/Ред.), страница `ContactEdit` с предпросмотром фото.
- **Settings/Telegram**: API настроек и вебхук обработчик (отложено до появления домена/HTTPS).

## Как деплоить без домена (кратко)
1. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
2. Открыть `http://<PUBLIC_IP>/`
3. Данные: БД в volume `pgdata`, фото в `./uploads`.

## Известные моменты
- Для Telegram Webhook нужен публичный HTTPS-домен — будет добавлено позже (Caddy/Nginx/Let’s Encrypt или LB).
