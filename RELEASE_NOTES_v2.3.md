# 📋 Release Notes - Version 2.3

**Дата:** 20 октября 2025  
**Версия:** v2.3 - Enhanced CRM Features

## 🎯 Основные улучшения

### ✨ Расширенная CRM функциональность

Версия 2.3 превращает ibbase в полноценную CRM систему с расширенными полями контактов, улучшенным распознаванием визиток и профессиональным интерфейсом для управления клиентской базой.

---

## 🆕 Новые возможности

### 1️⃣ **Расширенные поля контактов**

#### **Разделение ФИО на компоненты:**
- 👤 **Фамилия** (`last_name`)
- 👤 **Имя** (`first_name`)  
- 👤 **Отчество** (`middle_name`)
- Автоматическое разделение при распознавании визиток
- Поддержка обратной совместимости с полем `full_name`

#### **Дополнительные контактные данные:**
- 📱 **Мобильный телефон** (`phone_mobile`)
- 📞 **Рабочий телефон** (`phone_work`)
- 📠 **Факс** (`fax`)
- 🏢 **Отдел** (`department`)

#### **CRM поля:**
- 🎂 **День рождения** (`birthday`)
- 📍 **Источник контакта** (`source`) - откуда пришел клиент
- 🎯 **Статус** (`status`):
  - `active` - Активный
  - `inactive` - Неактивный
  - `lead` - Лид
  - `client` - Клиент
- ⭐ **Приоритет** (`priority`):
  - `low` - Низкий
  - `medium` - Средний
  - `high` - Высокий
  - `vip` - VIP

#### **Временные метки:**
- 🕒 **Дата создания** (`created_at`) - автоматически
- 🕒 **Дата обновления** (`updated_at`) - автоматически

### 2️⃣ **Улучшенное OCR распознавание**

#### **Интеллектуальный парсинг имен** (`parse_russian_name`):
```python
"Иванов Иван Иванович" → {
  last_name: "Иванов",
  first_name: "Иван", 
  middle_name: "Иванович"
}
```

#### **Автоматическое исправление ошибок OCR** (`detect_company_and_position`):
- Определяет перепутанные местами компанию и должность
- Использует ключевые слова:
  - **Должности**: директор, менеджер, специалист, инженер, CEO, CTO и т.д.
  - **Компании**: ООО, ЗАО, ОАО, АО, ИП, Ltd, Inc, Corp и т.д.
- Автоматически исправляет при распознавании

#### **Автоматическая обработка всех OCR данных:**
```python
# Применяется ко всем загруженным визиткам
data = enhance_ocr_result(data)
```

### 3️⃣ **Полная карточка клиента (ContactCard)**

Профессиональная модальная карточка контакта в стиле CRM:

#### **Структурированная информация:**
- 📋 **Личная информация** - ФИО, день рождения
- 🏢 **Информация о компании** - компания, должность, отдел
- 📞 **Контактные данные** - все телефоны, email, сайт, адрес, факс
- 💼 **CRM данные** - статус, приоритет, источник, даты создания/обновления
- 💬 **Комментарии**
- 🖼️ **Фото визитки** в высоком качестве

#### **Функциональность:**
- ✏️ Редактирование inline (без перезагрузки страницы)
- 🗑️ Удаление контакта
- 📅 Форматирование дат (русский/английский)
- 🎨 Современный дизайн с секциями
- 🌐 Полная поддержка RU/EN

#### **Открытие карточки:**
- Клик по любой строке в списке контактов
- Автоматическое обновление списка после изменений

### 4️⃣ **Группировка по организациям (Companies)**

Новая вкладка для работы с компаниями:

#### **Автоматическая группировка:**
- Все контакты группируются по полю `company`
- Контакты без компании → группа "Без компании"
- Сортировка по количеству контактов (от большего к меньшему)

#### **Раскрывающиеся списки:**
- Клик по компании → список всех контактов
- Отображение: имя, должность, email, телефон
- Кнопка "Открыть" → полная карточка клиента

#### **Статистика:**
- Общее количество контактов
- Количество контактов в каждой компании
- Правильная склонение (1 контакт, 2 контакта, 5 контактов)

### 5️⃣ **Улучшенный список контактов**

#### **Новая структура таблицы:**
```
[☑] [№] [UID] [Имя] [Компания] [Должность] [Email] [Phone] [Адрес] [Сайт] [Комментарий] [Фото] [✏️]
```

#### **Порядковый номер:**
- Колонка **№** перед UID
- Автоматический расчет с учетом пагинации
- Пример: страница 2, лимит 20 → номера 21-40

#### **UID без кнопки копирования:**
- Только отображение (первые 8 символов)
- Серый цвет, моноширинный шрифт
- Экономия места в таблице

#### **ФИО вместо полного имени:**
- Приоритет: `last_name + first_name + middle_name`
- Fallback: `full_name` (для старых записей)
- Пример: "Иванов Иван Иванович"

#### **Клик по строке → карточка:**
- Вся строка кликабельна
- Hover эффект (подсветка)
- Исключения: checkbox, кнопки

### 6️⃣ **Навигация**

Добавлена новая вкладка:
```
🏠 Главная | 📇 Контакты | 🏢 Организации | 📤 Загрузка | 📊 Импорт/Экспорт | ⚙️ Настройки | 🛡️ Админ
```

### 7️⃣ **Исправление версии**

- Переменная окружения `APP_VERSION=v2.3` в `docker-compose.yml`
- Отображается на главной странице и в настройках
- Больше не показывает "unknown"

---

## 🔧 Технические изменения

### **База данных:**

#### Миграция `add_contact_fields.sql`:
```sql
-- Новые поля имени
ALTER TABLE contacts ADD COLUMN last_name VARCHAR;
ALTER TABLE contacts ADD COLUMN first_name VARCHAR;
ALTER TABLE contacts ADD COLUMN middle_name VARCHAR;

-- Дополнительные контакты
ALTER TABLE contacts ADD COLUMN phone_mobile VARCHAR;
ALTER TABLE contacts ADD COLUMN phone_work VARCHAR;
ALTER TABLE contacts ADD COLUMN fax VARCHAR;

-- CRM поля
ALTER TABLE contacts ADD COLUMN department VARCHAR;
ALTER TABLE contacts ADD COLUMN birthday VARCHAR;
ALTER TABLE contacts ADD COLUMN source VARCHAR;
ALTER TABLE contacts ADD COLUMN status VARCHAR DEFAULT 'active';
ALTER TABLE contacts ADD COLUMN priority VARCHAR;

-- Временные метки
ALTER TABLE contacts ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE contacts ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

-- Индексы
CREATE INDEX idx_contacts_company ON contacts(company);
CREATE INDEX idx_contacts_created_at ON contacts(created_at);

-- Автоматическое разделение существующих ФИО
UPDATE contacts SET 
  last_name = SPLIT_PART(full_name, ' ', 1),
  first_name = SPLIT_PART(full_name, ' ', 2),
  middle_name = SPLIT_PART(full_name, ' ', 3)
WHERE full_name IS NOT NULL AND last_name IS NULL;
```

### **Backend:**

#### Новые файлы:
- `backend/app/ocr_utils.py` - утилиты для улучшенного OCR парсинга
- `backend/migrations/add_contact_fields.sql` - SQL миграция

#### Обновленные модели (`models.py`):
```python
class Contact(Base):
    # Name fields
    full_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    
    # Additional CRM fields
    phone_mobile = Column(String, nullable=True)
    phone_work = Column(String, nullable=True)
    fax = Column(String, nullable=True)
    department = Column(String, nullable=True)
    birthday = Column(String, nullable=True)
    source = Column(String, nullable=True)
    status = Column(String, nullable=True, default='active')
    priority = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### Обновленные схемы (`schemas.py`):
- `ContactBase` - добавлены все новые поля
- `ContactResponse` - добавлены `created_at`, `updated_at`

#### Интеграция OCR (`main.py`):
```python
# В upload_card и telegram_webhook:
data = ocr_utils.enhance_ocr_result(data)
```

### **Frontend:**

#### Новые компоненты:
- `frontend/src/components/ContactCard.js` - полная карточка клиента (562 строки)
- `frontend/src/components/Companies.js` - группировка по организациям (266 строк)

#### Обновленные компоненты:
- `App.js` - добавлена вкладка "Организации"
- `ContactList.js` - порядковый номер, клик по строке, отображение ФИО

---

## 📊 Статистика изменений

### **Коммиты:**
1. `6a8f5bd` - Add enhanced CRM fields: name components, timestamps, CRM fields, improved OCR parsing
2. `45cc72f` - Add ContactCard and Companies components, fix backend import error
3. `bd1e1e8` - Integrate ContactCard and Companies into frontend: add navigation, update ContactList
4. `5e2334b` - Fix Companies component pagination request

### **Файлы:**
- **Создано:** 4 новых файла
- **Изменено:** 8 файлов (backend), 3 файла (frontend)
- **Строк кода:** +1,200 / -150

### **База данных:**
- **Новых полей:** 13
- **Новых индексов:** 2
- **Обновлено записей:** все существующие контакты (автоматическое разделение ФИО)

---

## 🚀 Миграция с v2.2

### **Автоматическая миграция:**
```bash
# 1. Остановить контейнеры
docker compose down

# 2. Обновить код
git pull origin main
git checkout v2.3

# 3. Применить миграцию БД (автоматически при запуске backend)
docker compose up -d

# Миграция применяется автоматически при первом запуске
```

### **Данные:**
- ✅ Все существующие контакты сохраняются
- ✅ Поле `full_name` остается без изменений (обратная совместимость)
- ✅ Автоматическое разделение `full_name` → `last_name`, `first_name`, `middle_name`
- ✅ Новые поля получают значения по умолчанию

### **API:**
- ✅ Полная обратная совместимость
- ✅ Старые запросы продолжают работать
- ✅ Новые поля опциональны

---

## 🎨 UI/UX улучшения

### **ContactCard (Карточка клиента):**
- Модальное окно во весь экран
- Секционированная информация с иконками
- Цветовые группировки (синий для заголовков)
- Inline редактирование полей
- Select для статуса и приоритета
- Форматированные даты
- Responsive дизайн

### **Companies (Организации):**
- Раскрывающиеся аккордеоны
- Иконки (🏢 для компаний, 📋 для "без компании")
- Счетчики контактов с правильным склонением
- Hover эффекты
- Таблица контактов внутри каждой компании

### **ContactList (Список контактов):**
- Порядковые номера для навигации
- Клик по всей строке (улучшенный UX)
- Hover подсветка
- Компактное отображение UID
- Приоритет нативным полям (ФИО вместо full_name)

---

## 🐛 Исправленные ошибки

1. ✅ **"Контакт не найден"** при редактировании
   - Добавлен endpoint `GET /contacts/{id}`
   
2. ✅ **Версия "unknown"**
   - Добавлена переменная `APP_VERSION=v2.3` в docker-compose.yml

3. ✅ **Ошибка импорта `ocr_utils`**
   - Удален устаревший импорт `ocr_image_fileobj`, `ocr_parsio`

4. ✅ **422 ошибка в Companies**
   - Исправлен запрос с параметрами пагинации

---

## 📝 Известные ограничения

1. **Telegram настройки** - пока остаются в отдельной вкладке Settings (планируется перенос в AdminPanel в v2.4)

2. **Лимит загрузки компаний** - максимум 100 контактов на странице Companies (для больших баз рекомендуется использовать фильтры в разделе Контакты)

3. **OCR разделение ФИО** - работает для русских имен (Фамилия Имя Отчество), для других форматов может требоваться ручная корректировка

---

## 🔮 Планы на v2.4

1. Перенос настроек Telegram в AdminPanel
2. Расширенная фильтрация по новым полям (статус, приоритет, источник)
3. Dashboard с аналитикой по компаниям
4. Экспорт контактов с учетом новых полей
5. Массовое редактирование статуса/приоритета

---

## 🙏 Благодарности

Спасибо за использование ibbase! Ваши отзывы помогают нам делать систему лучше.

---

**Следующая версия:** v2.4 (планируется на ноябрь 2025)  
**Поддержка:** [GitHub Issues](https://github.com/your-repo/issues)

