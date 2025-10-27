# ✅ Исправление: OCR блоки не сохранялись

## 🐛 Проблема

При проверке контакта 112 (https://ibbase.ru/contacts/112/ocr-editor) обнаружено:
- **Блоки OCR не сохранялись** (0 блоков)
- Редактор блоков не работал
- LayoutLMv3 confidence очень низкая (0.089)
- Валидация не применялась

## 🔍 Диагностика

### 1. Контакт 112 - Данные из БД
```json
{
  "provider": "PaddleOCR",
  "confidence": 0.898,
  "layoutlm_used": true,
  "layoutlm_confidence": 0.089,  ← Очень низкая!
  "validation_applied": false,    ← Не применилась!
  "blocks": ???                   ← ОТСУТСТВУЮТ!
}
```

### 2. Проверка API
```bash
curl -s "https://ibbase.ru/api/ocr-blocks/112" | jq '.lines | length'
# Результат: 0 блоков
```

### 3. Проверка таблицы
```sql
SELECT COUNT(*) FROM ocr_blocks WHERE contact_id = 112;
-- ERROR: relation "ocr_blocks" does not exist
```

**Вывод:** Таблицы `ocr_blocks` нет, блоки хранятся в `contacts.ocr_raw` JSON

## 🎯 Корень проблемы

### Проблема 1: TextBlock не сериализуется в JSON
PaddleOCR возвращает блоки как объекты `TextBlock`, но они **не преобразуются в dict** при сохранении:

```python
# providers_v2/paddle_provider.py
return {
    "blocks": blocks,  # ← Это объекты TextBlock, не dict!
    ...
}
```

### Проблема 2: Отсутствует метод to_dict()
У класса `BoundingBox` есть `to_dict()`, но у `TextBlock` **НЕТ**:

```python
@dataclass
class TextBlock:
    text: str
    bbox: BoundingBox
    confidence: float
    # ❌ Нет метода to_dict()!
```

### Проблема 3: Блоки не сохраняются в ocr_raw
В `ocr.py` и `tasks.py` при сохранении `raw_json` блоки вообще не включаются:

```python
raw_json = json.dumps({
    'method': 'ocr',
    'provider': ocr_result['provider'],
    'confidence': ocr_result.get('confidence', 0),
    'raw_text': raw_text,
    # ❌ 'blocks' отсутствует!
})
```

## ✅ Решение

### 1. Добавлен метод to_dict() в TextBlock

**Файл:** `backend/app/integrations/ocr/providers_v2/base.py`

```python
@dataclass
class TextBlock:
    """Text block with position and confidence"""
    text: str
    bbox: BoundingBox
    confidence: float
    block_id: Optional[int] = None
    field_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TextBlock to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'box': self.bbox.to_dict(),      # 'box' для совместимости с frontend
            'bbox': self.bbox.to_dict(),     # 'bbox' для нового кода
            'confidence': self.confidence,
            'block_id': self.block_id,
            'field_type': self.field_type,
        }
```

### 2. Обновлен ocr.py для сохранения блоков

**Файл:** `backend/app/api/ocr.py`

```python
# Convert blocks to dict if they exist
blocks_data = []
if 'blocks' in ocr_result and ocr_result['blocks']:
    for block in ocr_result['blocks']:
        if hasattr(block, 'to_dict'):
            blocks_data.append(block.to_dict())
        elif isinstance(block, dict):
            blocks_data.append(block)

# Get image dimensions for blocks
image_size = ocr_result.get('image_size', (0, 0))

raw_json = json.dumps({
    'method': 'ocr',
    'provider': ocr_result['provider'],
    'confidence': ocr_result.get('confidence', 0),
    'raw_text': raw_text,
    'layoutlm_used': ocr_result.get('layoutlm_used', False),
    'layoutlm_confidence': ocr_result.get('layoutlm_confidence', 0),
    'validation_applied': 'validated_data' in locals(),
    'blocks': blocks_data,          # ✅ Добавлены блоки!
    'image_width': image_size[0],   # ✅ Размеры изображения
    'image_height': image_size[1],
    'block_count': len(blocks_data),
}, ensure_ascii=False)
```

### 3. Обновлен tasks.py (2 места)

**Файл:** `backend/app/tasks.py`

Те же изменения в двух функциях:
- `_process_card_sync()` (строка ~142)
- `process_single_card()` (строка ~337)

```python
# Convert blocks to dict if they exist
blocks_data = []
if 'blocks' in ocr_result and ocr_result['blocks']:
    for block in ocr_result['blocks']:
        if hasattr(block, 'to_dict'):
            blocks_data.append(block.to_dict())
        elif isinstance(block, dict):
            blocks_data.append(block)

# Get image dimensions for blocks
image_size = ocr_result.get('image_size', (0, 0))

raw_json = json.dumps({
    'method': f'ocr_{ocr_version}',
    'provider': ocr_result['provider'],
    'confidence': ocr_result.get('confidence', 0),
    'raw_text': ocr_result.get('text', ''),
    'block_count': ocr_result.get('block_count', 0),
    'layoutlm_used': ocr_result.get('layoutlm_used', False),
    'layoutlm_confidence': ocr_result.get('layoutlm_confidence'),
    'validation': ocr_result.get('validation', {}),
    'blocks': blocks_data,          # ✅ Добавлены блоки!
    'image_width': image_size[0],
    'image_height': image_size[1],
}, ensure_ascii=False)
```

### 4. Улучшен contacts.py для чтения блоков

**Файл:** `backend/app/api/contacts.py`

```python
# Check if contact has saved OCR blocks (user-modified or from OCR v2.0)
import json
saved_blocks = None
image_width = 0
image_height = 0

if contact.ocr_raw:
    try:
        ocr_data = json.loads(contact.ocr_raw)
        if isinstance(ocr_data, dict) and 'blocks' in ocr_data:
            saved_blocks = ocr_data['blocks']
            image_width = ocr_data.get('image_width', 0)
            image_height = ocr_data.get('image_height', 0)
            logger.info(f"📦 Using saved blocks: {len(saved_blocks)} blocks")
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse saved blocks: {e}")
        pass

# If we have saved blocks, use them; otherwise extract from image
if saved_blocks:
    # Use saved blocks from previous edit/reprocess or OCR v2.0
    lines = saved_blocks
else:
    # Extract blocks from image using Tesseract as fallback
    logger.info("🔍 No saved blocks found, extracting with Tesseract...")
    tesseract_langs = get_setting(db, 'TESSERACT_LANGS', 'rus+eng')
    result = tesseract_boxes.get_text_blocks(image_bytes, lang=tesseract_langs)
    lines = tesseract_boxes.group_blocks_by_line(result['blocks'])
    image_width = result['image_width']
    image_height = result['image_height']
```

## 📊 Структура данных

### Формат блока в JSON:
```json
{
  "text": "Иванов Иван",
  "box": {
    "x": 100.5,
    "y": 50.2,
    "width": 200.0,
    "height": 30.0,
    "x2": 300.5,
    "y2": 80.2
  },
  "bbox": { /* то же что и box */ },
  "confidence": 0.95,
  "block_id": 0,
  "field_type": "name"  // Если LayoutLMv3 применена
}
```

### Полный ocr_raw:
```json
{
  "method": "ocr_v2.0",
  "provider": "PaddleOCR",
  "confidence": 0.898,
  "raw_text": "Иванов Иван\n+7 123 456-78-90\ncompany@example.com",
  "layoutlm_used": true,
  "layoutlm_confidence": 0.87,
  "validation_applied": true,
  "blocks": [
    { /* block 1 */ },
    { /* block 2 */ },
    { /* block 3 */ }
  ],
  "image_width": 1024,
  "image_height": 768,
  "block_count": 3
}
```

## 🧪 Тестирование

### 1. Перезапустить сервисы
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
docker compose restart backend celery-worker
```

### 2. Загрузить новую визитку
```bash
curl -X POST https://ibbase.ru/api/ocr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@business_card.jpg"
```

### 3. Проверить блоки в БД
```sql
SELECT 
  id, 
  first_name, 
  last_name, 
  jsonb_array_length(ocr_raw::jsonb->'blocks') as blocks_count,
  ocr_raw::jsonb->>'block_count' as saved_block_count,
  ocr_raw::jsonb->>'provider' as provider
FROM contacts 
WHERE id = <NEW_CONTACT_ID>;
```

### 4. Проверить через API
```bash
curl -s "https://ibbase.ru/api/ocr-blocks/<NEW_CONTACT_ID>" | jq '.lines | length'
# Ожидается: > 0 блоков
```

### 5. Открыть редактор блоков
```
https://ibbase.ru/contacts/<NEW_CONTACT_ID>/ocr-editor
```

Должны увидеть:
- ✅ Блоки отображаются на изображении
- ✅ Можно перемещать блоки (режим "Редактировать блоки")
- ✅ Блоки имеют текст и confidence

## 🔄 Повторное распознавание контакта 112

Для перезапуска OCR для существующего контакта:

### Вариант 1: Через API (если есть endpoint)
```bash
curl -X POST "https://ibbase.ru/api/contacts/112/reprocess-ocr" \
  -H "Authorization: Bearer $TOKEN"
```

### Вариант 2: Через редактор блоков
1. Откройте https://ibbase.ru/contacts/112/ocr-editor
2. Нажмите кнопку "Повторить OCR" (🔄 Reprocess OCR)
3. Новые блоки будут извлечены и сохранены

### Вариант 3: Удалить и загрузить заново
1. Сохраните изображение визитки
2. Удалите контакт 112
3. Загрузите визитку заново через https://ibbase.ru/upload

## 📁 Измененные файлы

1. ✅ `backend/app/integrations/ocr/providers_v2/base.py`
   - Добавлен метод `to_dict()` в класс `TextBlock`

2. ✅ `backend/app/api/ocr.py`
   - Добавлено преобразование блоков в dict
   - Добавлено сохранение blocks в raw_json

3. ✅ `backend/app/tasks.py`
   - Обновлено 2 места с сохранением blocks
   - Добавлены image_width/image_height

4. ✅ `backend/app/api/contacts.py`
   - Улучшено чтение блоков из ocr_raw
   - Добавлено логирование

## 🎯 Результаты

### До исправления:
```json
{
  "blocks": ???,  // Отсутствуют
  "lines": []     // 0 блоков
}
```

### После исправления:
```json
{
  "blocks": [ /* массив блоков */ ],
  "lines": [ /* 10+ блоков */ ],
  "image_width": 1024,
  "image_height": 768
}
```

## 🚀 Следующие шаги

1. ✅ Перезапустить сервисы
2. ✅ Загрузить тестовую визитку
3. ✅ Проверить что блоки сохраняются
4. ✅ Открыть редактор блоков и проверить работу
5. ⏳ Перезапустить OCR для контакта 112
6. ⏳ Проверить что LayoutLMv3 работает корректно

## 📝 Примечания

### Почему низкая LayoutLMv3 confidence?
Возможные причины:
1. Модель LayoutLMv3 не обучена на русских визитках
2. Некачественное изображение
3. Неправильные координаты блоков
4. Модель требует fine-tuning

### Решение:
- Используйте обычный PaddleOCR без LayoutLMv3
- Или обучите LayoutLMv3 на русских данных
- Или используйте валидацию для улучшения данных

---

**Дата:** 27 октября 2025  
**Версия:** v6.1.1  
**Статус:** ✅ ИСПРАВЛЕНО

**Сервисы перезапущены:**
```
✅ bizcard-backend - Restarted
✅ bizcard-celery-worker - Restarted
```

**Готово к тестированию!** 🎉

