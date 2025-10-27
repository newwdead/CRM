# 🔄 Endpoint для полного перезапуска OCR

## 📋 Проблема

Контакт 112 был распознан до внедрения OCR v2.0, поэтому:
- ❌ Блоки не сохранены (0 блоков)
- ❌ В редакторе показывается только 1 блок (Tesseract fallback)
- ✅ Текст распознан (11 строк)

## ✅ Решение

Создан новый API endpoint для полного перезапуска OCR с нуля:

### Endpoint: `POST /api/contacts/{contact_id}/rerun-ocr`

**Требования:**
- Авторизация: Admin token
- Метод: POST
- Параметры: contact_id в URL

**Что делает:**
1. Читает оригинальное изображение контакта
2. Запускает OCR v2.0 (PaddleOCR + LayoutLMv3) заново
3. Сохраняет все блоки в `ocr_raw`
4. Обновляет поля контакта (имя, email, телефон и т.д.)
5. Применяет валидацию данных

## 🧪 Использование

### Вариант 1: Через curl (требуется admin token)

```bash
# Получить admin token
TOKEN="your_admin_token_here"

# Перезапустить OCR для контакта 112
curl -X POST "https://ibbase.ru/api/contacts/112/rerun-ocr" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Вариант 2: Через Python

```python
import requests

token = "your_admin_token_here"
contact_id = 112

response = requests.post(
    f"https://ibbase.ru/api/contacts/{contact_id}/rerun-ocr",
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
print(f"Blocks detected: {result['blocks_count']}")
print(f"Provider: {result['provider']}")
print(f"Confidence: {result['confidence']}")
```

### Вариант 3: Интеграция в frontend

Добавьте кнопку в редактор OCR (`OCREditorWithBlocks.js`):

```javascript
const handleRerunOCR = async () => {
  setReprocessing(true);
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/contacts/${contact.id}/rerun-ocr`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) throw new Error('Failed to rerun OCR');

    const result = await response.json();
    toast.success(
      `OCR перезапущен! Найдено блоков: ${result.blocks_count}`
    );
    
    // Перезагрузить блоки
    fetchOcrBlocks();
    
  } catch (error) {
    console.error('Error rerunning OCR:', error);
    toast.error('Ошибка при перезапуске OCR');
  } finally {
    setReprocessing(false);
  }
};

// Кнопка в UI
<button onClick={handleRerunOCR} disabled={reprocessing}>
  {reprocessing ? '⏳ Обработка...' : '🔄 Перезапустить OCR'}
</button>
```

## 📊 Ожидаемый ответ

```json
{
  "success": true,
  "message": "OCR rerun successful: 11 blocks detected",
  "blocks_count": 11,
  "provider": "PaddleOCR",
  "confidence": 0.898,
  "ocr_version": "v2.0",
  "contact": {
    "id": 112,
    "first_name": "Полина",
    "last_name": "Терентьева",
    "middle_name": "Сергеевна",
    "company": "CTRLHACK",
    "position": "Менеджер по работе с партнерами",
    "email": "p.terenteva@ctrlhack.ru",
    "phone": "+7 495 225-99-61",
    "phone_mobile": "+7 903 227-48-27",
    "website": "www.ctrlhack.ru"
  }
}
```

## 🔍 Проверка результата

### 1. Через API блоков
```bash
curl -s "https://ibbase.ru/api/ocr-blocks/112" | jq '{
  blocks_count: .lines | length,
  image_width: .image_width,
  image_height: .image_height
}'
```

**Ожидаемый результат:**
```json
{
  "blocks_count": 11,
  "image_width": 1024,
  "image_height": 768
}
```

### 2. В редакторе блоков
Откройте: https://ibbase.ru/contacts/112/ocr-editor

Должны увидеть:
- ✅ 11 блоков на изображении (вместо 1)
- ✅ Каждый блок с текстом и координатами
- ✅ Можно перемещать блоки в режиме редактирования

### 3. В базе данных
```sql
SELECT 
  id,
  first_name,
  last_name,
  jsonb_array_length(ocr_raw::jsonb->'blocks') as blocks_count,
  ocr_raw::jsonb->>'provider' as provider,
  ocr_raw::jsonb->>'confidence' as confidence
FROM contacts 
WHERE id = 112;
```

**Ожидаемый результат:**
```
 id  | first_name | last_name  | blocks_count | provider  | confidence 
-----+------------+------------+--------------+-----------+------------
 112 | Полина     | Терентьева |           11 | PaddleOCR | 0.898
```

## 🔧 Технические детали

### Код endpoint (backend/app/api/contacts.py):

```python
@router.post('/{contact_id}/rerun-ocr')
def rerun_contact_ocr(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Completely rerun OCR for a contact from scratch.
    Re-processes the image with current OCR v2.0 settings and saves new blocks.
    Requires admin privileges.
    """
    # 1. Read image
    # 2. Check OCR version (v1.0 or v2.0)
    # 3. Run OCR with current settings
    # 4. Convert blocks to dict
    # 5. Update contact fields
    # 6. Save blocks in ocr_raw
    # 7. Return results
```

### Что происходит:

1. **Читается изображение** из `uploads/{photo_path}`
2. **Проверяется версия OCR** из настроек (`ocr_version`)
3. **Запускается OCR:**
   - v2.0: PaddleOCR + LayoutLMv3 + Validator
   - v1.0: Tesseract (если v2.0 недоступен)
4. **Извлекаются блоки** (TextBlock objects)
5. **Конвертируются в dict** через `to_dict()`
6. **Обновляются поля контакта** (first_name, email, phone и т.д.)
7. **Сохраняется ocr_raw** с blocks, image_width, image_height
8. **Возвращается результат**

### Преимущества перед старым `/reprocess-ocr`:

| Функция | `/reprocess-ocr` | `/rerun-ocr` |
|---------|------------------|--------------|
| Требует blocks_data | ✅ Да | ❌ Нет |
| Перезапускает OCR | ❌ Нет | ✅ Да |
| Использует OCR v2.0 | ❌ | ✅ |
| Сохраняет координаты блоков | ❌ | ✅ |
| Применяет валидацию | ❌ | ✅ |
| Fallback на v1.0 | ❌ | ✅ |

## 🚀 Следующие шаги

### Шаг 1: Перезапустить OCR для контакта 112

```bash
TOKEN="your_admin_token"
curl -X POST "https://ibbase.ru/api/contacts/112/rerun-ocr" \
  -H "Authorization: Bearer $TOKEN"
```

### Шаг 2: Проверить результат
```
https://ibbase.ru/contacts/112/ocr-editor
```

### Шаг 3: Проверить количество блоков
```bash
curl -s "https://ibbase.ru/api/ocr-blocks/112" | jq '.lines | length'
# Ожидается: 11 (вместо 0)
```

### Шаг 4: Добавить кнопку в frontend

Интегрируйте кнопку "Перезапустить OCR" в редактор блоков для удобства пользователей.

## ❗ Важные замечания

1. **Требуются admin права** - endpoint доступен только администраторам
2. **Перезаписывает данные** - старые блоки будут заменены новыми
3. **Обновляет поля контакта** - имя, email, телефон и т.д. будут перезаписаны
4. **Длительная операция** - может занять 3-5 секунд для OCR v2.0
5. **Требует наличие изображения** - файл должен существовать в `uploads/`

## 🔐 Безопасность

- ✅ Требуется авторизация (JWT token)
- ✅ Требуются admin права
- ✅ Валидация contact_id
- ✅ Проверка существования файла
- ✅ Обработка ошибок с логированием
- ✅ Rollback при ошибках

## 📝 Логи

После запуска проверьте логи:

```bash
# Backend logs
docker logs bizcard-backend | grep "Rerunning OCR\|OCR rerun"

# Ожидаемый вывод:
# 🔄 Rerunning OCR for contact 112...
# 🚀 Using OCR v2.0 (PaddleOCR + LayoutLMv3)...
# ✅ OCR v2.0 successful
# ✅ OCR rerun complete for contact 112: 11 blocks saved
```

---

**Файл:** `backend/app/api/contacts.py` (строки 536-691)  
**Версия:** v6.1.2  
**Дата:** 27 октября 2025  
**Статус:** ✅ ГОТОВО К ИСПОЛЬЗОВАНИЮ

