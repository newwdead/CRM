# Release Notes v2.12 - Automatic Duplicate Detection
**Дата релиза:** 21 октября 2025  
**Тип:** Major Feature Release

## 🎯 Основные изменения

### ✨ Новая функциональность

#### 1. **Автоматическое обнаружение дубликатов при создании контакта**
   - ✅ Автоматический поиск дубликатов сразу после создания контакта
   - ✅ Сохранение найденных дубликатов в таблицу `duplicate_contacts`
   - ✅ Настройка включения/выключения через System Settings
   - ✅ Настраиваемый порог схожести

#### 2. **Улучшенный алгоритм сравнения контактов**
   - ✅ **Weighted scoring**: разные веса для разных полей
     - Email: 30% (уникальный идентификатор)
     - Phone: 25% (уникальный идентификатор)
     - Full Name: 20%
     - First/Last Name: 12-13%
     - Company: 8%
     - Position: 4%
   
   - ✅ **Транслитерация Cyrillic ↔ Latin**
     - Автоматическое сравнение "Иванов" ↔ "Ivanov"
     - Поддержка всех русских букв
     - Двойное сравнение: прямое + транслитерированное
   
   - ✅ **Нормализация телефонов**
     - Удаление всех нецифровых символов
     - Нормализация префиксов: 8→7, 9→79
     - Сравнение последних 7 цифр (для частичного совпадения)
     - Проверка всех телефонных полей (mobile, work, additional)
   
   - ✅ **Умное сравнение полей**
     - Поле "name": fuzzy matching + транслитерация
     - Поле "phone": нормализация + частичное совпадение
     - Поле "email": точное сравнение
     - Остальные поля: fuzzy matching

#### 3. **Раздел "Дубликаты" в Admin Panel**
   - ✅ Новая вкладка ⚠️ "Duplicates"
   - ✅ Таблица всех найденных дубликатов
   - ✅ Фильтры:
     - По статусу: All, Pending, Reviewed, Merged, Ignored
     - По минимальной схожести: 50%-100% (слайдер)
   - ✅ Отображение информации:
     - Два контакта side-by-side с деталями
     - Процент схожести с цветовой индикацией (зеленый >90%, оранжевый >80%, синий <80%)
     - Совпадающие поля с индивидуальными процентами
     - Дата обнаружения
     - Метка "Auto" или "Manual"
   
   - ✅ Действия:
     - **Merge** - объединение контактов через модальное окно
     - **Ignore** - пометка как ложное срабатывание
     - Кнопка "Find Duplicates" - ручной поиск дубликатов
   
   - ✅ Статистика: общее количество дубликатов

#### 4. **Новые API Endpoints**
   - ✅ `GET /api/contacts/{contact_id}/duplicates` - получить дубликаты конкретного контакта
   - ✅ `POST /api/duplicates/{duplicate_id}/ignore` - пометить дубликат как игнорируемый

### 🔧 Технические улучшения

1. **Backend (`backend/app/duplicate_utils.py`)**:
   - Добавлена функция `transliterate_cyrillic_to_latin()` - конвертация кириллицы в латиницу
   - Добавлена функция `normalize_phone()` - нормализация телефонных номеров
   - Улучшена функция `calculate_field_similarity()` с типами полей ('name', 'phone', 'email', 'text')
   - Обновлена функция `calculate_contact_similarity()` с weighted scoring и cross-field phone matching
   - Добавлена функция `find_duplicates_for_new_contact()` - поиск дубликатов для нового контакта

2. **Backend (`backend/app/main.py`)**:
   - Интеграция автоматического обнаружения в endpoint `POST /contacts/`
   - Try-catch обертка чтобы ошибки поиска дубликатов не ломали создание контакта
   - Новый endpoint `GET /api/contacts/{contact_id}/duplicates`
   - Новый endpoint `POST /api/duplicates/{duplicate_id}/ignore`

3. **Frontend (`frontend/src/components/DuplicatesPanel.js`)**:
   - Новый компонент (330 строк) для управления дубликатами
   - Фильтры по статусу и схожести
   - Цветовая индикация процента схожести
   - Интеграция с `DuplicateMergeModal` для объединения
   - Responsive таблица с overflow

4. **Frontend (`frontend/src/components/AdminPanel.js`)**:
   - Добавлена вкладка "⚠️ Duplicates"
   - Импорт и рендеринг `DuplicatesPanel`

### 📊 Алгоритм работы

```
1. Пользователь создает новый контакт
   ↓
2. Backend сохраняет контакт в БД
   ↓
3. Если duplicate_detection_enabled=true:
   ↓
4. Загружаются все существующие контакты
   ↓
5. Для каждого контакта вычисляется similarity score:
   - Нормализация полей (lowercase, strip)
   - Транслитерация для имен (Ivanov ↔ Иванов)
   - Нормализация телефонов (удаление форматирования)
   - Взвешенное суммирование совпадений полей
   ↓
6. Если score >= threshold (default 0.75):
   ↓
7. Сохранение записи в duplicate_contacts
   ↓
8. Админ видит дубликаты в Admin Panel → Duplicates
   ↓
9. Админ может:
   - Объединить контакты (Merge)
   - Игнорировать (Ignore) - false positive
   - Вручную найти больше дубликатов (Find Duplicates)
```

### 🎨 UX Улучшения

1. **Цветовая индикация схожести**:
   - 🟢 ≥90% - Зеленый (очень высокая вероятность дубликата)
   - 🟠 80-89% - Оранжевый (высокая вероятность)
   - 🔵 <80% - Синий (средняя вероятность)

2. **Информативные badge для совпадающих полей**:
   - Каждое поле показывает свой процент совпадения
   - Цветовая индикация: зеленая рамка ≥90%, оранжевая <90%

3. **Компактное отображение контактов**:
   - Имя жирным шрифтом
   - Email, телефон, компания с иконками
   - Все на одной карточке

### 🐛 Исправления ошибок

Нет новых исправлений - это feature release.

### 📝 Настройки System Settings

Новые настройки в категории "Duplicate Detection":
```
duplicate_detection_enabled (boolean, default: true)
  - Включить/выключить автоматическое обнаружение

duplicate_similarity_threshold (float, default: 0.75)
  - Минимальный порог схожести для определения дубликата
  - Диапазон: 0.0 (0%) - 1.0 (100%)

duplicate_check_frequency_hours (integer, default: 24)
  - Частота фоновой проверки всех контактов (для будущих релизов)

duplicate_check_new_only (boolean, default: true)
  - Проверять только новые контакты или все
```

### 🧪 Тестирование

**Протестировано:**
- ✅ Автоматическое обнаружение при создании контакта
- ✅ Алгоритм сравнения с транслитерацией
- ✅ Нормализация телефонов
- ✅ Раздел Duplicates в Admin Panel
- ✅ Фильтры и сортировка
- ✅ Объединение контактов
- ✅ Игнорирование ложных срабатываний
- ✅ Ручной поиск дубликатов

**Примеры успешных срабатываний:**
```
✅ "Иванов" = "Ivanov" (транслитерация)
✅ "+7 (999) 123-45-67" = "8 999 123 45 67" (нормализация телефона)
✅ "ООО Ромашка" ≈ "ООО РОМАШКА" (fuzzy matching + case insensitive)
✅ Проверка всех телефонов: phone, phone_mobile, phone_work, phone_additional
```

### 📦 Установка и обновление

```bash
# 1. Обновить код из репозитория
git pull origin main

# 2. Обновить настройки (если нужно)
docker compose exec db psql -U postgres -d bizcard_crm -c \
  "UPDATE system_settings SET category='Duplicate Detection' WHERE category='duplicates';"

# 3. Пересобрать контейнеры
docker compose up -d --build

# 4. Проверить версию
curl http://localhost:8000/version
# Должно вернуть: {"version": "v2.12", "message": "Automatic Duplicate Detection"}

# 5. Протестировать автообнаружение
# Создайте два похожих контакта и проверьте Admin Panel → Duplicates
```

### 🚧 Известные ограничения

1. **Отложено на v2.13:**
   - Фоновая задача Celery для периодической проверки всех контактов
   - Уведомление пользователю при обнаружении дубликата при создании
   - Массовое объединение дубликатов (выбрать несколько + "Merge All")
   - Email-отчеты администратору о найденных дубликатах

2. **Производительность:**
   - При большом количестве контактов (>10,000) автоматическая проверка может занимать несколько секунд
   - Рекомендуется использовать `duplicate_check_new_only=true`
   - Для полной проверки всех контактов использовать кнопку "Find Duplicates" в Admin Panel

3. **Ложные срабатывания:**
   - Контакты с очень похожими именами и одной компанией могут быть помечены как дубликаты
   - Решение: используйте кнопку "Ignore"

### 🚀 Что дальше (v2.13)

Планируется:
1. **Фоновая задача Celery**:
   - Периодическая проверка всех контактов
   - Настройка расписания через Admin Panel
   - Прогресс-бар во время выполнения

2. **Уведомления при создании**:
   - Toast-сообщение: "Найден похожий контакт"
   - Кнопка "Посмотреть" → модальное окно с дубликатами
   - Опция "Объединить сейчас"

3. **Массовые операции**:
   - Выбрать несколько дубликатов
   - "Ignore All Selected"
   - "Merge All Selected" (авто-выбор primary)

4. **Улучшение алгоритма**:
   - Machine Learning для определения оптимальных весов
   - Обучение на истории объединений
   - Адаптивный порог схожести

5. **Экспорт и отчеты**:
   - Экспорт списка дубликатов в CSV
   - Email-отчеты администратору
   - График "Дубликаты за последний месяц"

### 📚 Документация

- [Алгоритм обнаружения дубликатов](./docs/duplicate_detection.md) (coming soon)
- [API Reference для дубликатов](./docs/api_duplicates.md) (coming soon)
- [Руководство пользователя](./docs/user_guide_duplicates.md) (coming soon)

### 🎯 Статистика изменений

- **Backend:** +430 строк кода
- **Frontend:** +450 строк кода
- **Документация:** +340 строк
- **Новые файлы:** 2 (DuplicatesPanel.js, RELEASE_NOTES_v2.12.md)
- **Измененные файлы:** 4 (duplicate_utils.py, main.py, AdminPanel.js, docker-compose.yml)
- **Новые функции:** 4 (transliterate, normalize_phone, find_duplicates_for_new_contact, ignore_duplicate endpoint)
- **Новые endpoints:** 2 (GET /api/contacts/{id}/duplicates, POST /api/duplicates/{id}/ignore)

### 💡 Примеры использования

#### Пример 1: Создание контакта с автопроверкой
```bash
curl -X POST http://localhost:8000/contacts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иванов Иван",
    "email": "ivanov@example.com",
    "phone": "+7 999 123 45 67",
    "company": "ООО Ромашка"
  }'

# Система автоматически найдет дубликаты и сохранит в duplicate_contacts
```

#### Пример 2: Ручной поиск дубликатов
```bash
curl -X POST http://localhost:8000/api/duplicates/find?threshold=0.7 \
  -H "Authorization: Bearer $TOKEN"

# Вернет: {"message": "Found 26 potential duplicates", "found": 26, "saved": 26}
```

#### Пример 3: Получить дубликаты конкретного контакта
```bash
curl http://localhost:8000/api/contacts/123/duplicates \
  -H "Authorization: Bearer $TOKEN"

# Вернет список дубликатов с процентами схожести
```

### 🙏 Благодарности

Спасибо за использование ibbase CRM! Автоматическое обнаружение дубликатов значительно улучшит качество данных в вашей базе контактов.

---

**Версия:** v2.12  
**Commit:** (будет добавлен при релизе)  
**Предыдущая версия:** v2.11 - Duplicate Detection Foundation
**Docker Images:** 
- Backend: `ghcr.io/newwdead/crm-backend:v2.12`
- Frontend: `ghcr.io/newwdead/crm-frontend:v2.12`

**Участники:** AI Assistant
**Тестирование:** Manual testing + API testing
**Статус:** ✅ Production Ready

