# Release Notes v2.11 - Duplicate Detection Foundation
**Дата релиза:** 21 октября 2025  
**Тип:** Minor Feature Release

## 🎯 Основные изменения

### ✨ Новая функциональность

#### 1. **Система обнаружения дубликатов**
   - **Backend:**
     - ✅ Новая модель `DuplicateContact` для хранения найденных дубликатов
     - ✅ Модель `SystemSettings` для конфигурации параметров поиска
     - ✅ API endpoint `GET /api/duplicates` - получение списка дубликатов
     - ✅ API endpoint `POST /api/duplicates/find` - поиск дубликатов вручную
     - ✅ API endpoint `POST /api/contacts/{id1}/merge/{id2}` - объединение контактов
     - ✅ Алгоритм сравнения контактов на основе `fuzzywuzzy` (fuzzy matching)
     - ✅ Настройки порога схожести (similarity threshold)
     - ✅ Автоматический аудит-лог при объединении

   - **Frontend:**
     - ✅ Badge дубликатов в списке контактов (оранжевый ⚠️ с количеством)
     - ✅ Модальное окно для объединения дубликатов (`DuplicateMergeModal`)
     - ✅ Интерактивный выбор полей при объединении (таблица с переключателями)
     - ✅ Отображение процента схожести и совпадающих полей
     - ✅ Hover-эффекты на badge для улучшения UX
     - ✅ Автоматическая перезагрузка списка после объединения

   - **Admin Panel:**
     - ✅ Настройки duplicate detection в System Settings:
       - `duplicate_detection_enabled` - включение/выключение функции
       - `duplicate_similarity_threshold` - минимальный порог схожести (0.0-1.0)
       - `duplicate_check_frequency_hours` - частота автоматической проверки
       - `duplicate_check_new_only` - проверять только новые контакты

#### 2. **Алгоритм сравнения контактов**
   - Сравнение по полям: `full_name`, `first_name`, `last_name`, `email`, `phone`, `company`, `position`
   - Использование `fuzzywuzzy` для fuzzy string matching
   - Учет всех телефонных номеров (mobile, work, additional)
   - Возврат детальной информации о совпадающих полях
   - Поддержка задания порога схожести от 0.0 до 1.0

#### 3. **Функциональность объединения**
   - Выбор основного контакта (primary)
   - Возможность выбрать для каждого поля: данные основного или дубликата
   - Автоматическое объединение тегов и групп
   - Переназначение OCR-коррекций
   - Удаление дубликата после объединения
   - Создание записи в audit log

### 🔧 Технические улучшения

1. **Backend:**
   - Добавлены зависимости: `fuzzywuzzy==0.18.0`, `python-Levenshtein==0.25.0`
   - Новый модуль `backend/app/duplicate_utils.py` с функциями для работы с дубликатами
   - Миграция БД: `backend/migrations/create_duplicates_table.sql`
   - Исправлен тип данных `match_fields` в модели: `String` → `JSON` (jsonb в PostgreSQL)
   - Удален ненужный `json.dumps()` при сохранении дубликатов

2. **Frontend:**
   - Новый компонент `DuplicateMergeModal.js` (360 строк)
   - Расширен `ContactList.js`:
     - State для дубликатов и модального окна
     - Функция `loadDuplicates()` для загрузки дубликатов из API
     - Обработчик клика на badge
   - Добавлен tooltip для badge дубликатов
   - Улучшена читаемость кода с комментариями

3. **Database:**
   - Новая таблица `duplicate_contacts` с constraint `unique_duplicate_pair`
   - Новая таблица `system_settings` для глобальных настроек
   - Trigger `ensure_contact_order` для автоматической сортировки contact_id
   - View `duplicate_contacts_view` для удобного просмотра дубликатов
   - Индексы для ускорения запросов по status и similarity_score

### 🐛 Исправления ошибок

1. **Backend:**
   - ✅ Исправлена ошибка `TypeError: the JSON object must be str, bytes or bytearray, not dict` в endpoint `/api/duplicates`
   - ✅ Исправлена ошибка `DatatypeMismatch: column "match_fields" is of type jsonb but expression is of type character varying`
   - ✅ Обновлен импорт в `models.py`: добавлен `JSON` из SQLAlchemy
   - ✅ Удален `json.loads()` при чтении `match_fields` (SQLAlchemy автоматически десериализует JSON)

2. **Database:**
   - ✅ Обновлена категория system_settings: `duplicates` → `Duplicate Detection`

### 📊 Структура данных

#### DuplicateContact Model
```python
class DuplicateContact(Base):
    __tablename__ = "duplicate_contacts"
    id: int
    contact_id_1: int  # FK to contacts.id
    contact_id_2: int  # FK to contacts.id
    similarity_score: float  # 0.0 to 1.0
    match_fields: JSON  # {"name": 0.95, "email": 1.0}
    status: str  # 'pending', 'reviewed', 'merged', 'ignored'
    auto_detected: bool
    detected_at: datetime
    reviewed_at: datetime
    reviewed_by: int  # FK to users.id
    merged_into: int  # FK to contacts.id
```

### 🧪 Тестирование

**Протестировано:**
- ✅ Backend API endpoints (GET, POST, PUT для дубликатов)
- ✅ Алгоритм поиска дубликатов (26 дубликатов найдено на тестовой базе)
- ✅ Badge дубликатов в списке контактов
- ✅ Модальное окно объединения
- ✅ Сохранение настроек в System Settings

### 📝 Известные ограничения

- Автоматическое обнаружение дубликатов при создании контактов пока не реализовано (запланировано для v2.12)
- Фоновая задача для периодической проверки дубликатов не реализована
- UI для массового объединения дубликатов отсутствует

### 🚀 Что дальше (v2.12)

Планируется:
1. Автоматическое обнаружение дубликатов при создании нового контакта
2. Фоновая задача (Celery) для периодической проверки всех контактов
3. Раздел "Дубликаты" в админ-панели с таблицей всех найденных пар
4. Массовое объединение дубликатов
5. Улучшение алгоритма сравнения (weighted scoring)
6. Экспорт списка дубликатов в CSV

### 📦 Установка и обновление

```bash
# 1. Обновить код из репозитория
git pull origin main

# 2. Применить миграции
docker compose exec db psql -U postgres -d bizcard_crm < backend/migrations/create_duplicates_table.sql
docker compose exec db psql -U postgres -d bizcard_crm -c "UPDATE system_settings SET category='Duplicate Detection' WHERE category='duplicates';"

# 3. Пересобрать контейнеры
docker compose up -d --build

# 4. Проверить работу
curl -X POST "http://localhost:8000/api/duplicates/find?threshold=0.75" \
  -H "Authorization: Bearer <token>"
```

### 📚 Документация

- [Алгоритм обнаружения дубликатов](./docs/duplicate_detection.md)
- [API Reference для дубликатов](./docs/api_duplicates.md)
- [Руководство пользователя](./docs/user_guide_duplicates.md)

### 🙏 Благодарности

Спасибо за использование ibbase CRM! Ваши отзывы помогают нам становиться лучше.

---

**Версия:** v2.11  
**Commit:** (будет добавлен при релизе)  
**Docker Images:** 
- Backend: `ghcr.io/newwdead/crm-backend:v2.11`
- Frontend: `ghcr.io/newwdead/crm-frontend:v2.11`
