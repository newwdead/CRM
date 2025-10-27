# ⚡ Перезапуск OCR - Быстрая инструкция

## 🎯 Проблема
**Контакт 112:** Редактор показывает только 1 блок вместо множества

## ✅ Решение

### Шаг 1: Получить admin token

Войдите как администратор и получите токен из localStorage:

```javascript
// В консоли браузера (F12):
localStorage.getItem('token')
```

### Шаг 2: Вызвать API

```bash
TOKEN="ваш_токен_здесь"

curl -X POST "https://ibbase.ru/api/contacts/112/rerun-ocr" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Шаг 3: Проверить результат

Откройте редактор:
```
https://ibbase.ru/contacts/112/ocr-editor
```

**Ожидается:** 11 блоков вместо 1

## 📊 Что изменится

| До | После |
|----|-------|
| 0-1 блок | 11 блоков |
| Tesseract | PaddleOCR v2.0 |
| Нет координат | Есть координаты |
| Неточные данные | Валидированные данные |

## 🔍 Проверка

```bash
# Количество блоков
curl -s "https://ibbase.ru/api/ocr-blocks/112" | jq '.lines | length'
# Ожидается: 11
```

## 🚀 Endpoint

```
POST /api/contacts/{contact_id}/rerun-ocr
Authorization: Bearer {admin_token}
```

**Требования:**
- ✅ Admin права
- ✅ Изображение контакта существует
- ✅ OCR v2.0 доступен

**Результат:**
- ✅ Все блоки сохранены
- ✅ Поля контакта обновлены
- ✅ Координаты блоков в БД

## ⏱️ Время выполнения
- OCR v2.0: 3-5 секунд
- OCR v1.0 (fallback): 1-2 секунды

---

**Версия:** v6.1.2  
**Статус:** ✅ ГОТОВО  
**Push:** Выполнен

