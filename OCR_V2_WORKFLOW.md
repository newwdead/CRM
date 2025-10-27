# 🔄 Пошаговая схема работы OCR v2.0

## 📋 Общая схема (БЕЗ Tesseract!)

```
┌─────────────────────────────────────────────────────────────┐
│                  ЗАГРУЗКА ВИЗИТКИ                           │
│             https://ibbase.ru/upload                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 1: Проверка настройки OCR версии                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│  Файл: backend/app/api/ocr.py:108                           │
│  Код:  ocr_version = get_setting(db, "ocr_version", "v2.0") │
│                                                             │
│  ✅ Ожидается: ocr_version = "v2.0"                         │
│  ❌ НЕ должно быть: "v1.0"                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 2: Проверка наличия QR-кода                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                          │
│  Файл: backend/app/api/ocr.py:94-104                        │
│  Код:  qr_data = qr_utils.extract_qr_data(card_bytes)       │
│                                                             │
│  Если QR найден → используем данные из QR                   │
│  Если QR НЕТ → переходим к OCR                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ (QR НЕТ)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 3: Инициализация PaddleOCR                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                           │
│  Файл: backend/app/api/ocr.py:20-22                         │
│  Код:                                                       │
│    ocr_manager_v1 = OCRManager()  # Только fallback!        │
│    ocr_manager_v2 = OCRManagerV2(enable_layoutlm=True)      │
│    ocr_manager = ocr_manager_v2   # Default = v2.0          │
│                                                             │
│  ✅ Используется: OCRManagerV2 (PaddleOCR)                  │
│  ⚠️  OCRManager (Tesseract) - только на случай ошибки!      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 4: Запуск PaddleOCR (основной движок)                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│  Файл: backend/app/api/ocr.py:108-130                       │
│  Код:                                                       │
│    if ocr_version == "v2.0":                                │
│        logger.info("🚀 Using OCR v2.0...")                  │
│        try:                                                 │
│            ocr_result = ocr_manager_v2.recognize(           │
│                image_data=ocr_input,                        │
│                provider_name=preferred,                     │
│                use_layout=True,  # LayoutLMv3!              │
│                filename=filename                            │
│            )                                                │
│                                                             │
│  PaddleOCR параметры:                                       │
│  • lang='cyrillic' (кириллица)                              │
│  • det_db_thresh=0.3 (чувствительная детекция)              │
│  • det_db_box_thresh=0.5                                    │
│  • det_db_unclip_ratio=1.6                                  │
│                                                             │
│  ✅ Результат: 8-15 блоков с координатами                   │
│  ✅ Provider: "PaddleOCR"                                   │
│  ✅ Confidence: 0.85-0.95                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 5: LayoutLMv3 AI классификация (опционально)           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                 │
│  Файл: backend/app/integrations/ocr/providers_v2/manager.py │
│  Код: apply_layout_classification(ocr_result)               │
│                                                             │
│  Классифицирует блоки по типам:                             │
│  • name (имя)                                               │
│  • phone (телефон)                                          │
│  • email (email)                                            │
│  • company (компания)                                       │
│  • position (должность)                                     │
│  • address (адрес)                                          │
│                                                             │
│  ✅ Добавляет field_type к каждому блоку                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 6: ValidatorService - автокоррекция                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  Файл: backend/app/api/ocr.py:135-140                       │
│  Код:                                                       │
│    validator = ValidatorService(db)                         │
│    ocr_result_validated = validator.validate_ocr_result(    │
│        ocr_result,                                          │
│        auto_correct=True                                    │
│    )                                                        │
│                                                             │
│  Исправляет:                                                │
│  • Форматы телефонов: +7 495 123-45-67                      │
│  • Email адреса: ivan@company.ru                            │
│  • Веб-сайты: www.company.com                               │
│  • Имена: правильная капитализация                          │
│                                                             │
│  ✅ Качество данных улучшено                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 7: Конвертация TextBlock → dict для JSON               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                   │
│  Файл: backend/app/api/ocr.py:178-185                       │
│  Код:                                                       │
│    blocks_data = []                                         │
│    if 'blocks' in ocr_result:                               │
│        for block in ocr_result['blocks']:                   │
│            if hasattr(block, 'to_dict'):                    │
│                blocks_data.append(block.to_dict())          │
│                                                             │
│  Структура блока:                                           │
│  {                                                          │
│    "text": "Иванов Иван",                                   │
│    "box": {                                                 │
│      "x": 100, "y": 50,                                     │
│      "width": 200, "height": 30                             │
│    },                                                       │
│    "confidence": 0.95,                                      │
│    "field_type": "name"  # от LayoutLMv3                    │
│  }                                                          │
│                                                             │
│  ✅ Блоки готовы для сохранения в БД                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 8: Сохранение в MinIO (опционально)                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                       │
│  Файл: backend/app/api/ocr.py:216-244                       │
│  Код:                                                       │
│    storage_service = StorageService(db)                     │
│                                                             │
│    # Сохранить оригинальное изображение                     │
│    image_url = storage_service.save_business_card_image(    │
│        image_data=card_bytes,                               │
│        filename=safe_name,                                  │
│        contact_id=contact.id                                │
│    )                                                        │
│                                                             │
│    # Сохранить OCR результат                                │
│    ocr_url = storage_service.save_ocr_result(               │
│        contact_id=contact.id,                               │
│        ocr_data=json.loads(raw_json)  # ← ИСПРАВЛЕНО!       │
│    )                                                        │
│                                                             │
│  ✅ Изображение: business-cards bucket                      │
│  ✅ OCR результат: ocr-results bucket                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 9: Сохранение контакта в PostgreSQL                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│  Файл: backend/app/api/ocr.py:148-172                       │
│  Код:                                                       │
│    contact = Contact(                                       │
│        first_name=data.get('first_name'),                   │
│        last_name=data.get('last_name'),                     │
│        company=data.get('company'),                         │
│        email=data.get('email'),                             │
│        phone=data.get('phone'),                             │
│        photo_path=safe_name,                                │
│        has_qr_code=False,                                   │
│        ocr_raw=json.dumps({                                 │
│            'method': 'ocr_v2.0',                            │
│            'provider': 'PaddleOCR',  # ← ВАЖНО!             │
│            'confidence': 0.87,                              │
│            'raw_text': 'весь текст...',                     │
│            'blocks': blocks_data,  # ← 8-15 блоков!         │
│            'image_width': 4744,                             │
│            'image_height': 2672,                            │
│            'block_count': 24,                               │
│            'layoutlm_used': True,                           │
│            'validation_applied': True                       │
│        }, ensure_ascii=False)                               │
│    )                                                        │
│    db.add(contact)                                          │
│    db.commit()                                              │
│                                                             │
│  ✅ contact.ocr_raw содержит ВСЕ блоки PaddleOCR            │
│  ✅ Размеры изображения сохранены                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 10: Ответ клиенту (frontend)                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                          │
│  Файл: backend/app/api/ocr.py:246-260                       │
│                                                             │
│  JSON ответ:                                                │
│  {                                                          │
│    "id": 118,                                               │
│    "first_name": "Иван",                                    │
│    "last_name": "Иванов",                                   │
│    "company": "ООО Компания",                               │
│    "email": "ivan@company.ru",                              │
│    "phone": "+7 495 123-45-67",                             │
│    "recognition_method": "PaddleOCR v2.0 + LayoutLMv3",     │
│    "confidence": 0.87,                                      │
│    "blocks_count": 24                                       │
│  }                                                          │
│                                                             │
│  ✅ Контакт создан успешно                                  │
└─────────────────────────────────────────────────────────────┘


═════════════════════════════════════════════════════════════
                  ОТКРЫТИЕ РЕДАКТОРА БЛОКОВ
          https://ibbase.ru/contacts/118/ocr-editor
═════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  ШАГ 11: Запрос блоков из БД                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                             │
│  Файл: backend/app/api/contacts.py:230-265                  │
│  Endpoint: GET /api/contacts/118/ocr-blocks                 │
│                                                             │
│  Код:                                                       │
│    if contact.ocr_raw:                                      │
│        ocr_data = json.loads(contact.ocr_raw)               │
│        if 'blocks' in ocr_data:                             │
│            saved_blocks = ocr_data['blocks']                │
│            image_width = ocr_data['image_width']            │
│            image_height = ocr_data['image_height']          │
│            logger.info(f"📦 Using saved blocks: "           │
│                       f"{len(saved_blocks)} blocks")        │
│                                                             │
│  ✅ ЕСЛИ блоки есть → использовать их!                      │
│  ❌ ТОЛЬКО если блоков НЕТ → fallback на Tesseract          │
│                                                             │
│  ПРОВЕРКА:                                                  │
│  • len(saved_blocks) > 0                                    │
│  • image_width > 0                                          │
│  • image_height > 0                                         │
│                                                             │
│  ✅ Для OCR v2.0: всегда должны быть сохраненные блоки      │
│  ❌ Tesseract НЕ должен запускаться!                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 12: Возврат блоков в frontend                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                         │
│  Файл: backend/app/api/contacts.py:267-285                  │
│                                                             │
│  JSON ответ:                                                │
│  {                                                          │
│    "contact_id": 118,                                       │
│    "image_url": "/files/xxx.jpg",                           │
│    "image_width": 4744,                                     │
│    "image_height": 2672,                                    │
│    "lines": [                                               │
│      {                                                      │
│        "text": "CTLHACK",                                   │
│        "box": {                                             │
│          "x": 137, "y": 128,                                │
│          "width": 1082, "height": 167                       │
│        },                                                   │
│        "confidence": 0.95                                   │
│      },                                                     │
│      ... еще 23 блока                                       │
│    ]                                                        │
│  }                                                          │
│                                                             │
│  ✅ Блоки из PaddleOCR (из БД)                              │
│  ❌ НЕ из Tesseract "на лету"                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ШАГ 13: Отображение в редакторе                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                         │
│  Файл: frontend/src/components/OCREditorWithBlocks.js       │
│                                                             │
│  Загрузка:                                                  │
│    const data = await fetch('/api/contacts/118/ocr-blocks')│
│    setOcrBlocks(data)                                       │
│    calculateImageScale(data.image_width, data.image_height) │
│                                                             │
│  Отображение:                                               │
│    <img width={image_width * imageScale}                    │
│         height={image_height * imageScale} />               │
│                                                             │
│    <svg width={image_width * imageScale}                    │
│         height={image_height * imageScale}>                 │
│      {lines.map(block =>                                    │
│        <rect x={block.box.x * imageScale}                   │
│              y={block.box.y * imageScale}                   │
│              width={block.box.width * imageScale}           │
│              height={block.box.height * imageScale} />      │
│      )}                                                     │
│    </svg>                                                   │
│                                                             │
│  ✅ Блоки точно на тексте картинки                          │
│  ✅ Drag&drop работает                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ FALLBACK на Tesseract (ТОЛЬКО при ошибке!)

```
┌─────────────────────────────────────────────────────────────┐
│  КОГДА ИСПОЛЬЗУЕТСЯ Tesseract (v1.0)?                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ OCR v2.0 упал с ошибкой                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                               │
│  Файл: backend/app/api/ocr.py:141-151                       │
│  Код:                                                       │
│    except Exception as v2_error:                            │
│        logger.warning(f"⚠️ OCR v2.0 failed: {v2_error}")    │
│        logger.info("🔧 Falling back to OCR v1.0...")        │
│        ocr_manager_v1 = OCRManager()                        │
│        ocr_result = ocr_manager_v1.recognize(...)           │
│                                                             │
│  Причины:                                                   │
│  • PaddleOCR модели не загружены                            │
│  • Ошибка в LayoutLMv3                                      │
│  • Проблема с изображением                                  │
│                                                             │
│  2️⃣ Редактор: контакт БЕЗ сохраненных блоков                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                     │
│  Файл: backend/app/api/contacts.py:254-265                  │
│  Код:                                                       │
│    if saved_blocks:                                         │
│        lines = saved_blocks  # ← OCR v2.0 блоки             │
│    else:                                                    │
│        logger.info("🔍 No saved blocks, Tesseract...")      │
│        result = tesseract_boxes.get_text_blocks(...)        │
│        lines = tesseract_boxes.group_blocks_by_line(...)    │
│                                                             │
│  Причины:                                                   │
│  • Контакт загружен до исправления                          │
│  • Блоки не сохранились (ошибка в коде)                     │
│  • ocr_raw пустой или без 'blocks'                          │
│                                                             │
│  3️⃣ Настройка ocr_version = "v1.0"                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                           │
│  Если админ явно переключил на v1.0 в настройках            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

❌ ВО ВСЕХ ОСТАЛЬНЫХ СЛУЧАЯХ TESSERACT НЕ ДОЛЖЕН ИСПОЛЬЗОВАТЬСЯ!
```

---

## ✅ КОНТРОЛЬНЫЕ ТОЧКИ ДЛЯ ПРОВЕРКИ

### Точка 1: Настройка OCR версии
```sql
SELECT key, value FROM app_settings WHERE key = 'ocr_version';
```
**Ожидается:** `value = 'v2.0'`

### Точка 2: Логи при загрузке визитки
```bash
docker logs bizcard-backend 2>&1 | grep "Using OCR"
```
**Ожидается:** `🚀 Using OCR v2.0 (PaddleOCR + LayoutLMv3)...`  
**НЕ должно быть:** `🔧 Using OCR v1.0 (Tesseract)...`

### Точка 3: Провайдер в БД
```sql
SELECT id, ocr_raw::json->'provider' as provider 
FROM contacts 
WHERE id = 118;
```
**Ожидается:** `provider = "PaddleOCR"`  
**НЕ должно быть:** `provider = "Tesseract"`

### Точка 4: Блоки в БД
```sql
SELECT 
  id,
  jsonb_array_length(ocr_raw::jsonb->'blocks') as blocks_count,
  ocr_raw::json->'image_width' as width,
  ocr_raw::json->'image_height' as height
FROM contacts 
WHERE id = 118;
```
**Ожидается:**
- `blocks_count >= 8`
- `width > 0`
- `height > 0`

### Точка 5: Логи редактора блоков
```bash
docker logs bizcard-backend 2>&1 | grep "ocr-blocks"
```
**Ожидается:** `📦 Using saved blocks: 24 blocks`  
**НЕ должно быть:** `🔍 No saved blocks found, extracting with Tesseract...`

### Точка 6: Frontend Network запрос
```javascript
// В DevTools → Network → /api/contacts/118/ocr-blocks
// Response должен содержать:
{
  "image_width": 4744,
  "image_height": 2672,
  "lines": [ /* 24 блока */ ]
}
```
**Проверка:** `lines.length >= 8`

---

## 🎯 КОГДА TESSERACT ДОПУСТИМ

✅ **Допустимые случаи использования Tesseract:**

1. Явный fallback при ошибке PaddleOCR (с логированием)
2. Редактор для старых контактов БЕЗ блоков (с логированием)
3. Админ переключил настройку на v1.0

❌ **НЕдопустимые случаи:**

1. При загрузке новой визитки (если ocr_version = v2.0)
2. При открытии редактора для контакта с сохраненными блоками
3. Без логирования причины fallback

---

## 📊 МЕТРИКИ УСПЕХА

| Метрика | OCR v2.0 (PaddleOCR) | OCR v1.0 (Tesseract) |
|---------|---------------------|---------------------|
| **Блоков на визитку** | 8-15 | 1-3 |
| **Точность** | 85-95% | 60-75% |
| **Скорость распознавания** | 3-5 сек | 1-2 сек |
| **Скорость редактора** | <100ms (из БД) | 3+ сек (на лету) |
| **Координаты** | Точные | Приблизительные |
| **AI классификация** | ✅ LayoutLMv3 | ❌ Нет |
| **Валидация** | ✅ Auto | ❌ Нет |

---

## 🔧 КОМАНДЫ ДЛЯ ПРОВЕРКИ

### 1. Проверить версию OCR
```bash
curl -s "https://ibbase.ru/api/ocr/settings/config" | jq '.version'
```

### 2. Проверить доступные провайдеры
```bash
curl -s "https://ibbase.ru/api/ocr/providers" | jq '.available'
```

### 3. Загрузить тестовую визитку
```bash
curl -X POST "https://ibbase.ru/api/ocr/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@business_card.jpg" \
  -F "provider=auto"
```

### 4. Проверить блоки контакта
```bash
curl -s "https://ibbase.ru/api/contacts/118/ocr-blocks" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    blocks: .lines | length,
    width: .image_width,
    height: .image_height
  }'
```

### 5. Проверить логи на Tesseract
```bash
docker logs bizcard-backend 2>&1 | grep -i tesseract | tail -20
```

**Ожидается:** ТОЛЬКО fallback логи или редактор для старых контактов

---

**Версия:** v6.1.6  
**Статус:** OCR v2.0 активен, Tesseract только fallback  
**Дата:** 27 октября 2025

