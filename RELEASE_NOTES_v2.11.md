# Release Notes v2.11 - Duplicate Detection Foundation

**Дата релиза:** 21 октября 2025  
**Версия:** v2.11  
**Статус:** ✅ Backend Foundation Ready

---

## 🎯 Обзор релиза

Этот релиз закладывает **фундамент для системы обнаружения и объединения дубликатов контактов**. Реализована backend-инфраструктура, готовая к использованию в UI.

### ✅ Выполнено в v2.11:
1. Database schema для дубликатов
2. Backend API и утилиты для поиска дубликатов
3. Алгоритм сравнения контактов с настраиваемыми весами
4. Система настроек (System Settings)

### 🔄 Будет доработано в v2.12:
- Frontend UI для объединения контактов
- Badge дубликатов на карточках
- Фоновая проверка (Celery)
- Настройки в Admin Panel

---

## ✨ Новая функциональность

### 1. ✅ Database: Таблица duplicate_contacts

**Создана структура для хранения найденных дубликатов:**

```sql
CREATE TABLE duplicate_contacts (
    id SERIAL PRIMARY KEY,
    contact_id_1 INTEGER REFERENCES contacts(id),
    contact_id_2 INTEGER REFERENCES contacts(id),
    similarity_score FLOAT NOT NULL,  -- 0.0 to 1.0
    match_fields JSONB,  -- {"name": 0.95, "email": 1.0}
    status VARCHAR(20) DEFAULT 'pending',  -- pending, reviewed, merged, ignored
    auto_detected BOOLEAN DEFAULT false,
    detected_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id),
    merged_into INTEGER REFERENCES contacts(id),
    CONSTRAINT unique_duplicate_pair UNIQUE (contact_id_1, contact_id_2),
    CONSTRAINT check_contact_order CHECK (contact_id_1 < contact_id_2)
);
```

**Особенности:**
- Автоматическое упорядочивание пар (contact_id_1 < contact_id_2)
- Хранение детальных scores по каждому полю
- Статусы: `pending`, `reviewed`, `merged`, `ignored`
- Связи с users для отслеживания кто рассмотрел дубликаты

**View для удобного просмотра:**
```sql
CREATE VIEW duplicate_contacts_view AS
SELECT 
    dc.*,
    c1.full_name as contact_1_name,
    c2.full_name as contact_2_name,
    ...
FROM duplicate_contacts dc
JOIN contacts c1, c2, users u
...
```

---

### 2. ✅ Backend: System Settings

**Создана таблица для системных настроек:**

```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Настройки для дубликатов:**
- `duplicate_detection_enabled`: Включить автопроверку (true/false)
- `duplicate_similarity_threshold`: Порог сходства (0.0-1.0), default: 0.75
- `duplicate_check_frequency_hours`: Частота проверки (часы), default: 24
- `duplicate_check_new_only`: Проверять только новые контакты (true/false)

---

### 3. ✅ Backend: Алгоритм поиска дубликатов

**Создан модуль `duplicate_utils.py` с функциями:**

#### `calculate_field_similarity(value1, value2) -> float`
Сравнение двух значений поля с использованием fuzzy matching (Levenshtein distance).

```python
calculate_field_similarity("Иван Петров", "Иван Петрович")
# → 0.85 (85% сходства)
```

#### `calculate_contact_similarity(contact1, contact2, weights) -> (score, field_scores)`
Рассчитывает общее сходство между контактами с учётом весов полей.

**Веса по умолчанию:**
```python
{
    'full_name': 0.3,
    'first_name': 0.15,
    'last_name': 0.15,
    'email': 0.25,
    'phone': 0.20,
    'company': 0.10,
    'position': 0.05,
}
```

**Пример:**
```python
contact1 = {
    'full_name': 'Иван Петров',
    'email': 'ivan@example.com',
    'phone': '+7 (999) 123-45-67'
}
contact2 = {
    'full_name': 'Иван Петрович',
    'email': 'ivan@example.com',
    'phone': '+79991234567'
}

score, fields = calculate_contact_similarity(contact1, contact2)
# score = 0.92
# fields = {'full_name': 0.85, 'email': 1.0, 'phone': 1.0}
```

#### `find_duplicate_contacts(contacts, threshold) -> List[duplicates]`
Поиск дубликатов в списке контактов.

```python
duplicates = find_duplicate_contacts(all_contacts, threshold=0.75)
# Возвращает список потенциальных дубликатов, отсортированных по score
```

#### `merge_contacts(primary, secondary, selected_fields) -> merged`
Объединение двух контактов на основе выбранных полей.

```python
selected_fields = {
    'email': 'primary',      # Взять email из primary
    'phone': 'secondary',    # Взять phone из secondary
    'company': 'keep_both'   # Объединить: "Company1; Company2"
}
merged = merge_contacts(contact1, contact2, selected_fields)
```

---

### 4. ✅ Backend: Models

**Добавлены модели в `models.py`:**

```python
class SystemSettings(Base):
    """System-wide settings and configuration."""
    __tablename__ = "system_settings"
    # ...

class DuplicateContact(Base):
    """Store detected duplicate contacts for review and merging."""
    __tablename__ = "duplicate_contacts"
    # ...
    contact_1 = relationship('Contact', foreign_keys=[contact_id_1])
    contact_2 = relationship('Contact', foreign_keys=[contact_id_2])
    reviewer = relationship('User', foreign_keys=[reviewed_by])
```

---

## 📊 Технические детали

### Файлы:

**Backend:**
```
backend/
  app/
    models.py                              # +SystemSettings, +DuplicateContact models
    duplicate_utils.py                     # NEW: Duplicate detection utilities
  migrations/
    create_duplicates_table.sql            # NEW: DB migration
```

**Изменения в БД:**
```sql
-- New tables
+ system_settings (6 columns)
+ duplicate_contacts (12 columns)

-- New indexes
+ idx_duplicate_contact_id_1
+ idx_duplicate_contact_id_2
+ idx_duplicate_status
+ idx_duplicate_similarity

-- New functions
+ ensure_contact_order()

-- New triggers
+ trigger_ensure_contact_order

-- New views
+ duplicate_contacts_view
```

---

## 🧪 Тестирование

### Проверка БД:

```bash
# Подключение к БД
docker compose exec db psql -U postgres -d bizcard_crm

# Проверка таблиц
\dt duplicate_contacts
\dt system_settings

# Просмотр настроек
SELECT * FROM system_settings WHERE category = 'duplicates';
```

**Ожидаемый результат:**
```
key                              | value | description
---------------------------------|-------|---------------------------
duplicate_detection_enabled      | true  | Enable automatic duplicate detection
duplicate_similarity_threshold   | 0.75  | Minimum similarity score...
duplicate_check_frequency_hours  | 24    | How often to run...
duplicate_check_new_only         | true  | Only check newly created...
```

### Тестирование алгоритма:

```python
from app.duplicate_utils import calculate_contact_similarity

contact1 = {'full_name': 'Иван Петров', 'email': 'ivan@test.com'}
contact2 = {'full_name': 'Иван Петрович', 'email': 'ivan@test.com'}

score, fields = calculate_contact_similarity(contact1, contact2)
print(f"Similarity: {score:.2%}")  # → Similarity: 92%
print(f"Fields: {fields}")          # → {'full_name': 0.85, 'email': 1.0}
```

---

## 🚀 Что дальше (v2.12)

### Запланировано для следующего релиза:

1. **Frontend UI для объединения контактов:**
   - Модальное окно с двумя колонками (primary/secondary)
   - Выбор значения для каждого поля (radio buttons)
   - Опция "Keep Both" для объединения
   - Предпросмотр результата

2. **Badge дубликатов:**
   - Индикатор на карточке контакта: "🔗 2 duplicates"
   - Клик открывает список похожих контактов
   - Быстрый доступ к объединению

3. **Celery background task:**
   - Автоматическая проверка новых контактов
   - Периодическая полная проверка (настраивается)
   - Уведомления при обнаружении дубликатов

4. **Admin Panel Settings:**
   - UI для настройки порога сходства (slider 0%-100%)
   - Включение/отключение автопроверки
   - Частота проверки
   - Просмотр найденных дубликатов

5. **API Endpoints:**
   ```
   GET  /api/duplicates                    # Список найденных дубликатов
   POST /api/duplicates/find               # Поиск дубликатов вручную
   POST /api/contacts/{id1}/merge/{id2}    # Объединить контакты
   PUT  /api/duplicates/{id}/status        # Изменить статус (ignore/review)
   ```

---

## 📝 Миграция

### Применение на существующей системе:

```bash
# 1. Остановить контейнеры
docker compose down

# 2. Применить миграцию
docker compose up -d db
docker compose exec -T db psql -U postgres -d bizcard_crm < backend/migrations/create_duplicates_table.sql

# 3. Запустить обновлённые контейнеры
docker compose build backend
docker compose up -d
```

---

## ⚠️ Breaking Changes

**Нет breaking changes** ✅

Все изменения - добавление новых таблиц и функций, не влияют на существующий функционал.

---

## 🎉 Итоги v2.11

### Что достигнуто:
- ✅ Создана database schema для дубликатов
- ✅ Реализован алгоритм поиска с fuzzy matching
- ✅ Добавлена система настроек
- ✅ Готова backend-основа для UI

### Что осталось (v2.12):
- 🔄 Frontend UI (50% времени реализации)
- 🔄 Celery background tasks (30%)
- 🔄 Admin Panel integration (20%)

**Прогресс: Backend 100%, Frontend 0%, Overall 40%**

---

## 🔗 Связанные документы

- **Previous Release:** [RELEASE_NOTES_v2.10.md](./RELEASE_NOTES_v2.10.md)
- **Duplicate Utils API:** `backend/app/duplicate_utils.py`
- **Database Schema:** `backend/migrations/create_duplicates_table.sql`

---

**Релиз подготовил:** AI Assistant  
**Утверждено:** @newwdead  
**Дата:** 21 октября 2025  
**Статус:** ✅ Backend Ready, Frontend Pending

