# ⚡ OCR Блоки - Быстрое исправление

## ❌ Проблема
Контакт 112: блоки OCR не сохранялись, редактор не работал

## ✅ Исправлено

### 1. Добавлен метод to_dict() в TextBlock
```python
# backend/app/integrations/ocr/providers_v2/base.py
class TextBlock:
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'box': self.bbox.to_dict(),
            'confidence': self.confidence,
            ...
        }
```

### 2. Блоки теперь сохраняются в ocr_raw
```python
# backend/app/api/ocr.py + backend/app/tasks.py (3 места)
blocks_data = [block.to_dict() for block in ocr_result['blocks']]

raw_json = json.dumps({
    'blocks': blocks_data,  # ✅ Добавлено!
    'image_width': width,
    'image_height': height,
    ...
})
```

### 3. Улучшено чтение блоков
```python
# backend/app/api/contacts.py
if contact.ocr_raw:
    ocr_data = json.loads(contact.ocr_raw)
    saved_blocks = ocr_data.get('blocks', [])
    image_width = ocr_data.get('image_width', 0)
    image_height = ocr_data.get('image_height', 0)
```

## 📁 Измененные файлы
1. `backend/app/integrations/ocr/providers_v2/base.py` - метод to_dict()
2. `backend/app/api/ocr.py` - сохранение блоков
3. `backend/app/tasks.py` - сохранение блоков (2 места)
4. `backend/app/api/contacts.py` - чтение блоков

## 🧪 Тестирование

### Загрузить новую визитку:
```bash
curl -X POST https://ibbase.ru/api/ocr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@card.jpg"
```

### Проверить блоки:
```bash
curl -s "https://ibbase.ru/api/ocr-blocks/<CONTACT_ID>" | jq '.lines | length'
# Ожидается: > 0 блоков
```

### Открыть редактор:
```
https://ibbase.ru/contacts/<CONTACT_ID>/ocr-editor
```

## ✅ Статус
- ✅ Backend: Перезапущен (healthy)
- ✅ Celery: Перезапущен (starting)
- ✅ Исправления применены
- ✅ Push выполнен
- ⏳ Требуется тестирование на новых загрузках

## 🔄 Контакт 112
Для перезапуска OCR:
1. Откройте: https://ibbase.ru/contacts/112/ocr-editor
2. Кнопка "🔄 Повторить OCR"
3. Блоки будут извлечены заново

---
**Версия:** v6.1.1  
**Дата:** 27 октября 2025

