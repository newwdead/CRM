# 🎓 Руководство по Обучению OCR

## ibbase v2.6: Обучаемая система распознавания визиток

---

## 🎯 Обзор

Система теперь поддерживает **два режима** работы с OCR:

### 1️⃣ **Встроенный OCR Редактор** (Быстрый)
- ✅ Визуализация блоков Tesseract прямо на изображении
- ✅ Клик по блоку → назначение полю
- ✅ Автоматическое сохранение исправлений
- ✅ Интегрирован в основной интерфейс

### 2️⃣ **Label Studio** (Продвинутый)
- ✅ Профессиональный UI для аннотации
- ✅ Детальная разметка прямоугольниками
- ✅ Экспорт обучающих данных
- ✅ Отдельный сервис для сложных случаев

---

## 📦 Что реализовано

### Backend (FastAPI):
```
✅ /api/contacts/{id}/ocr-blocks
   - Получение bounding boxes от Tesseract
   - Координаты и текст блоков
   - Группировка по строкам

✅ /api/contacts/{id}/ocr-corrections
   - Сохранение исправлений OCR
   - Исходный текст + исправленный
   - Привязка к полю контакта

✅ База данных: ocr_corrections
   - Хранение всех исправлений
   - Метаданные для обучения
   - История исправлений пользователя
```

### Frontend (React):
```
✅ OCREditorWithBlocks
   - Визуализация блоков на изображении
   - SVG overlays с координатами
   - Цветовая маркировка полей
   - Клик-назначение блоков

✅ Автоматическое сохранение
   - При назначении блока → API call
   - Фоновое сохранение в БД
   - Без уведомлений пользователя
```

### Docker:
```
✅ Label Studio сервис
   - Порт: 8080
   - Доступ к файлам визиток
   - Готовая конфигурация
```

---

## 🚀 Использование

### Вариант 1: Встроенный Редактор

#### Шаг 1: Откройте контакт
```
Контакты → Найдите контакт → Кнопка "📝 OCR"
```

#### Шаг 2: Работа с блоками
```
1. Слева: изображение с подсвеченными блоками текста
2. Справа: поля контакта

3. Клик по блоку → выделяется желтым
4. Клик по стрелке "←" рядом с полем → назначение
5. Текст автоматически вставляется в поле
```

#### Шаг 3: Сохранение
```
1. Проверьте все поля
2. Нажмите "Сохранить"
3. Исправления автоматически сохраняются для обучения
```

#### Цвета полей:
```
🔵 Имя (first_name)
🟣 Фамилия (last_name)
🟣 Отчество (middle_name)
🟢 Компания (company)
🟢 Должность (position)
🟠 Email (email)
🔴 Телефон (phone)
🟣 Мобильный (phone_mobile)
🟠 Рабочий (phone_work)
🔵 Адрес (address)
🔵 Веб-сайт (website)
```

---

### Вариант 2: Label Studio

#### Запуск Label Studio:
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
docker compose up -d label-studio
```

#### Доступ:
```
URL: http://localhost:8080
Логин: admin@ibbase.ru
Пароль: labelstudio2024
```

#### Настройка проекта:
```
1. Создайте новый проект
2. Settings → Labeling Interface → 
   Upload from file → label-studio-config.xml
3. Settings → Cloud Storage → 
   Add Local Files → /label-studio/files
```

#### Импорт визиток:
```json
[
  {
    "image": "/label-studio/files/your_card.jpg",
    "extracted_text": "Текст с визитки..."
  }
]
```

#### Аннотация:
```
1. Выберите поле (First Name, Company, etc.)
2. Обведите прямоугольником текст на изображении
3. Введите распознанный текст
4. Submit
```

#### Экспорт:
```
Export → JSON → Скачать
Формат: COCO, Pascal VOC, или JSON-MIN
```

---

## 📊 База Данных Исправлений

### Таблица `ocr_corrections`:
```sql
SELECT 
    id,
    contact_id,
    original_text,           -- Что распознал OCR
    corrected_text,          -- Что исправил пользователь
    corrected_field,         -- В какое поле назначено
    ocr_provider,            -- tesseract/parsio/google
    language,                -- rus+eng
    created_at
FROM ocr_corrections
ORDER BY created_at DESC;
```

### Анализ исправлений:
```sql
-- Топ-10 самых частых ошибок
SELECT 
    original_text,
    corrected_text,
    corrected_field,
    COUNT(*) as occurrences
FROM ocr_corrections
WHERE original_text != corrected_text
GROUP BY original_text, corrected_text, corrected_field
ORDER BY occurrences DESC
LIMIT 10;
```

### Экспорт для обучения:
```bash
# Экспорт всех исправлений в JSON
docker exec bizcard-db psql -U postgres bizcard_crm -c \
  "COPY (SELECT row_to_json(t) FROM (SELECT * FROM ocr_corrections) t) TO STDOUT" \
  > ocr_training_data.json
```

---

## 🧠 Обучение Модели

### 1. Сбор данных
```
Минимум: 100-200 исправлений
Рекомендовано: 500-1000 исправлений
Оптимально: 2000+ исправлений
```

### 2. Подготовка датасета
```python
import json
import pandas as pd

# Загрузить исправления
with open('ocr_training_data.json') as f:
    data = [json.loads(line) for line in f]

df = pd.DataFrame(data)

# Фильтровать только реальные исправления
df_errors = df[df['original_text'] != df['corrected_text']]

# Группировать по полям
by_field = df_errors.groupby('corrected_field')
```

### 3. Fine-tuning Tesseract
```bash
# 1. Генерация обучающих данных
tesseract image.jpg output --psm 6 box

# 2. Ручная коррекция .box файлов
# (используйте Label Studio экспорт)

# 3. Обучение
tesstrain --model_name bizcard_rus \
          --tessdata_dir ./tessdata \
          --training_text ./ground_truth.txt \
          --fonts_dir ./fonts
```

### 4. Применение кастомной модели
```python
# backend/app/ocr_providers.py
pytesseract.image_to_string(
    image, 
    lang='bizcard_rus+eng',  # Кастомная модель
    config='--psm 6'
)
```

---

## 📈 Метрики Улучшения

### Отслеживание точности:
```python
# Расчет accuracy до и после обучения
correct = len(df[df['original_text'] == df['corrected_text']])
total = len(df)
accuracy = (correct / total) * 100

print(f"Точность OCR: {accuracy:.2f}%")
```

### Анализ по полям:
```python
field_accuracy = df.groupby('corrected_field').apply(
    lambda g: (g['original_text'] == g['corrected_text']).sum() / len(g) * 100
)
print(field_accuracy.sort_values())
```

---

## 🔧 Настройка

### Изменить язык Tesseract:
```bash
# В Admin Panel → System Settings → OCR
tesseract_langs: "rus+eng"  # Добавьте свои языки
```

### Изменить порог confidence:
```python
# backend/app/tesseract_boxes.py
if conf < 0:  # Изменить порог
    continue
```

### Добавить новые поля:
```python
# 1. Обновить модель Contact
# backend/app/models.py

# 2. Обновить OCREditor
# frontend/src/components/OCREditorWithBlocks.js
editableFields = [
    ...,
    'new_field_name'
]

# 3. Добавить в Label Studio config
# label-studio-config.xml
```

---

## 🐛 Troubleshooting

### Блоки не отображаются:
```bash
# Проверьте логи backend
docker compose logs backend | grep "OCR blocks"

# Убедитесь, что у контакта есть изображение
docker exec bizcard-db psql -U postgres bizcard_crm -c \
  "SELECT id, uid, photo_path FROM contacts WHERE id=YOUR_ID;"
```

### Label Studio не запускается:
```bash
# Проверьте порт 8080
docker compose logs label-studio

# Пересоздайте контейнер
docker compose down label-studio
docker compose up -d label-studio
```

### Исправления не сохраняются:
```bash
# Проверьте таблицу
docker exec bizcard-db psql -U postgres bizcard_crm -c \
  "SELECT COUNT(*) FROM ocr_corrections;"

# Проверьте логи
docker compose logs backend | grep "OCR correction saved"
```

---

## 📚 Дополнительные Ресурсы

### Tesseract:
- [Официальная документация](https://tesseract-ocr.github.io/)
- [Training Tesseract](https://tesseract-ocr.github.io/tessdoc/Training-Tesseract.html)
- [Улучшение точности](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)

### Label Studio:
- [Документация](https://labelstud.io/guide/)
- [ML Backend Integration](https://labelstud.io/guide/ml.html)
- [Export Formats](https://labelstud.io/guide/export.html)

### OCR Best Practices:
- Минимум 300 DPI для изображений
- Контрастность и освещение
- Предобработка (denoising, deskewing)

---

## 🎉 Готово!

Теперь у вас есть полноценная система обучения OCR:

✅ **Встроенный редактор** - для повседневного использования  
✅ **Label Studio** - для детальной аннотации  
✅ **База исправлений** - для анализа и обучения  
✅ **Экспорт данных** - для fine-tuning моделей  

**Следующие шаги:**
1. Начните исправлять визитки через встроенный редактор
2. Накопите 200+ исправлений
3. Проанализируйте данные
4. Обучите кастомную модель Tesseract
5. Увеличьте точность распознавания!

---

**Вопросы?** Проверьте логи или документацию Label Studio.

