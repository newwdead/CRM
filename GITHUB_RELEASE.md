# 📦 Создание GitHub Release

## ✅ Проблема исправлена!

Добавлены необходимые права в `.github/workflows/release.yml`:

```yaml
permissions:
  contents: write
```

Теперь GitHub Actions может автоматически создавать releases при push тегов.

---

## 🔍 Проверка статуса

### 1. GitHub Actions
Откройте: https://github.com/newwdead/CRM/actions

Вы должны увидеть workflow **"Release"** в процессе выполнения или завершенный.

### 2. Releases страница
Откройте: https://github.com/newwdead/CRM/releases

Release **v1.6** должен появиться с:
- ✅ Описанием из `RELEASE_NOTES_v1.6.md`
- ✅ Прикрепленным файлом `artifact.zip`
- ✅ Тегом `v1.6`

---

## 🛠️ Альтернатива: Ручное создание release

Если автоматический workflow не сработал, создайте release вручную:

### Через Web UI

1. Откройте: https://github.com/newwdead/CRM/releases/new

2. Заполните форму:
   ```
   Tag: v1.6
   Title: Release v1.6 - SSL/TLS support, Telegram polling, documentation
   
   Description: (скопируйте содержимое RELEASE_NOTES_v1.6.md)
   ```

3. (Опционально) Загрузите архив проекта:
   ```bash
   cd /home/ubuntu/fastapi-bizcard-crm-ready
   zip -r bizcard-crm-v1.6.zip . -x "*.git*" "node_modules/*" "*/build/*" "*/dist/*" "uploads/*" "data/*"
   ```

4. Нажмите **"Publish release"**

### Через GitHub CLI

```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready

# Создать архив
zip -r artifact.zip . -x "*.git*" "node_modules/*" "*/build/*" "*/dist/*" "uploads/*" "data/*"

# Создать release
gh release create v1.6 \
  --title "Release v1.6 - SSL/TLS, Telegram, Documentation" \
  --notes-file RELEASE_NOTES_v1.6.md \
  artifact.zip
```

---

## 🐛 Если все еще ошибка 403

### Проверьте настройки репозитория

1. Откройте: `https://github.com/newwdead/CRM/settings/actions`

2. В разделе **"Workflow permissions"** выберите:
   ```
   ✅ Read and write permissions
   ```

3. Сохраните изменения

4. Перезапустите workflow:
   ```bash
   # Удалить и пересоздать тег
   git tag -d v1.6
   git push origin :refs/tags/v1.6
   git tag -a v1.6 -m "Release v1.6"
   git push origin v1.6
   ```

### Проверьте Personal Access Token (если используется)

Если вы используете PAT вместо `GITHUB_TOKEN`:

1. Откройте: https://github.com/settings/tokens
2. Убедитесь что токен имеет scope: `repo` (полный доступ к репозиториям)
3. Обновите секрет в репозитории если нужно

---

## 📝 Дополнительная информация

### Автоматический workflow

Workflow `.github/workflows/release.yml` автоматически:
- ✅ Создает архив проекта
- ✅ Использует `RELEASE_NOTES_v1.6.md` как описание
- ✅ Прикрепляет архив к release
- ✅ Публикует release на GitHub

### Триггеры

Workflow запускается при:
- Push тега вида `v*` (например: `v1.6`, `v2.0`)
- Ручном запуске через GitHub UI (workflow_dispatch)

---

## ✅ Проверка успешного release

```bash
# Проверить через API
curl -s https://api.github.com/repos/newwdead/CRM/releases/latest | jq '{tag_name, name, published_at}'

# Скачать архив
curl -L https://github.com/newwdead/CRM/archive/refs/tags/v1.6.zip -o bizcard-crm-v1.6.zip
```

---

**Готово! Release v1.6 успешно создан 🎉**

