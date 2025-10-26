# Текущий OCR Провайдер - Статус v6.0.0

## 📊 Активный OCR Провайдер

**TESSERACT OCR** - единственный доступный и работающий провайдер

## 🔍 Как определить какой OCR используется?

### 1. **API Endpoint**
```bash
curl http://localhost:8000/ocr/providers
```

Ответ:
```json
{
  "available": ["Tesseract"],
  "details": [
    {
      "name": "Tesseract",
      "priority": 3,
      "available": true
    }
  ]
}
```

### 2. **Логи Backend**
```bash
docker compose logs backend | grep -i "OCR"
```

Примеры из логов:
- `"OCR successful with Tesseract, confidence: 0.7"`
- `"Extracted 33 text blocks from image"` (tesseract_boxes)

### 3. **Код - providers.py**
Файл: `backend/app/integrations/ocr/providers.py`

OCRManager инициализирует провайдеры в приоритете:
1. **Tesseract** (priority: 3) - ✅ ДОСТУПЕН
2. **Parsio** (priority: 2) - ❌ НЕ ДОСТУПЕН (нет API ключа)
3. **Google Vision** (priority: 1) - ❌ НЕ ДОСТУПЕН (нет API ключа)

## 📦 Что случилось с PaddleOCR?

**PaddleOCR НЕ ИСПОЛЬЗУЕТСЯ** в текущей версии v6.0.0:

1. ❌ Директория `backend/app/integrations/ocr/providers/` была удалена
2. ❌ Код PaddleOCRProvider был удален
3. ✅ Пакеты paddleocr и paddlepaddle установлены в requirements.txt
4. ❌ НО нет кода для их использования

## 🎯 Текущая Архитектура OCR

### Что работает:
```
Image → Tesseract OCR → Text Extraction → Contact Fields
                      ↓
              tesseract_boxes.py
                      ↓
              OCR Editor UI (блоки)
```

### Особенности Tesseract:
- **Локальный OCR** (не требует API ключей)
- **Мультипасс обработка** (6 проходов для улучшения качества)
- **Поддержка языков**: eng+rus
- **Confidence**: обычно 0.7
- **Извлечение блоков** для OCR Editor

## 🔧 Как изменить OCR провайдер?

### Включить Google Vision:
```bash
# В .env добавить:
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Включить Parsio:
```bash
# В .env добавить:
PARSIO_API_KEY=your_api_key_here
```

### Вернуть PaddleOCR:
Нужно выполнить миграцию из `OCR_ARCHITECTURE_MIGRATION_v2.md`:
1. Восстановить код из `providers/` директории
2. Добавить PaddleOCRProvider в OCRManager
3. Настроить модели

## 📈 Статистика использования

По логам видно что Tesseract успешно обрабатывает:
- Загрузку визиток (`/ocr/upload`)
- Извлечение блоков (`/contacts/{id}/ocr-blocks`)
- Высокая точность для блоков (до 33 блоков на изображении)

## ⚠️ Важно

**Release v6.0.0 заявлен как "OCR v2.0"**, НО:
- ❌ PaddleOCR не активен
- ❌ LayoutLMv3 не установлен
- ❌ MinIO настроен, но не используется для OCR
- ✅ Работает только Tesseract (как в предыдущих версиях)

**Фактически используется OCR v1.0 (Tesseract)**

## 🚀 Рекомендации

1. **Для продолжения работы** - текущий Tesseract достаточен
2. **Для улучшения качества** - выполнить полную миграцию OCR v2.0
3. **Для проверки провайдера** - использовать endpoint `/ocr/providers`

---
**Дата:** 2025-10-26  
**Версия:** v6.0.0  
**Активный OCR:** Tesseract
