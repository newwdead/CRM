# 🔒 Контрольный список безопасного удаления функционала

## ❌ ЧТО ПОШЛО НЕ ТАК С ДУБЛИКАТАМИ

### Проблема:
После удаления основных файлов дубликатов (models, schemas, services, repositories) **backend не запустился** из-за оставшихся импортов в других файлах.

### Последствия:
- ❌ Backend crash при запуске
- ❌ Невозможность логина
- ❌ Система полностью недоступна

---

## ✅ ПРАВИЛЬНАЯ ПРОЦЕДУРА УДАЛЕНИЯ

### 1️⃣ **ПОИСК ВСЕХ ИСПОЛЬЗОВАНИЙ**

```bash
# Для backend (Python)
grep -r "ИмяКласса" backend/app/
grep -r "имя_модуля" backend/app/
grep -r "имя_функции" backend/app/

# Для frontend (JavaScript)
grep -r "ComponentName" frontend/src/
grep -r "functionName" frontend/src/
```

### 2️⃣ **ПРОВЕРКА КРИТИЧНЫХ МЕСТ**

#### Backend:
```
✓ models/__init__.py      - экспорты моделей
✓ schemas/__init__.py     - экспорты схем
✓ services/__init__.py    - экспорты сервисов
✓ repositories/__init__.py - экспорты репозиториев
✓ api/__init__.py         - регистрация роутеров
✓ api/*.py                - импорты в endpoint'ах
✓ services/*.py           - зависимости сервисов
✓ tests/**/*.py           - использование в тестах
✓ main.py                 - импорты приложения
```

#### Frontend:
```
✓ App.js                  - роуты
✓ components/routing/*.js - навигация
✓ components/AdminPanel.js - вкладки админки
✓ modules/*/index.js      - экспорты модулей
```

### 3️⃣ **ПОРЯДОК УДАЛЕНИЯ**

1. **Найти ВСЕ использования** (`grep -r`)
2. **Удалить импорты** в зависимых файлах
3. **Удалить вызовы функций** и использование классов
4. **Удалить параметры функций** (например, `auto_detect_duplicates`)
5. **Удалить endpoint'ы и роуты**
6. **Удалить тесты**
7. **Удалить основные файлы**
8. **Убрать из __init__.py**

### 4️⃣ **ПРОВЕРКА ПЕРЕД ДЕПЛОЕМ**

```bash
# Backend
docker compose build backend
docker compose up -d backend
docker logs bizcard-backend --tail 50

# Проверка запуска
curl http://localhost:8000/version

# Frontend
docker compose build frontend
docker compose up -d frontend
curl http://localhost:80
```

---

## 🔍 КОНТРОЛЬНЫЙ СПИСОК

### Перед удалением:

- [ ] Найти ВСЕ использования через `grep -r`
- [ ] Составить список всех файлов для изменения
- [ ] Создать TODO список

### При удалении:

- [ ] Удалить импорты в зависимых файлах
- [ ] Удалить вызовы функций/методов
- [ ] Удалить параметры функций
- [ ] Удалить endpoint'ы/роуты
- [ ] Удалить тесты
- [ ] Удалить основные файлы
- [ ] Убрать из __init__.py

### После удаления:

- [ ] `docker compose build backend frontend`
- [ ] `docker compose up -d`
- [ ] Проверить логи: `docker logs bizcard-backend`
- [ ] Проверить API: `curl http://localhost:8000/version`
- [ ] Проверить login в браузере
- [ ] Коммит с подробным описанием

---

## 📚 ПРИМЕРЫ КОМАНД

### Поиск использований:

```bash
# Backend - поиск класса модели
grep -r "DuplicateContact" backend/app/ --include="*.py"

# Backend - поиск импорта модуля
grep -r "duplicate_utils" backend/app/ --include="*.py"

# Backend - поиск параметра функции
grep -r "auto_detect_duplicates" backend/app/ --include="*.py"

# Frontend - поиск компонента
grep -r "DuplicateFinder" frontend/src/ --include="*.js" --include="*.jsx"

# Frontend - поиск роута
grep -r "/duplicates" frontend/src/ --include="*.js"
```

### Проверка импортов в файлах:

```bash
# Все импорты DuplicateContact
grep -n "from.*import.*DuplicateContact" backend/app/**/*.py

# Все импорты duplicate_utils
grep -n "import.*duplicate_utils" backend/app/**/*.py

# Все использования DuplicateRepository
grep -n "DuplicateRepository" backend/app/**/*.py
```

---

## 🎯 УРОКИ ИЗ УДАЛЕНИЯ ДУБЛИКАТОВ

### Что было упущено:

1. ❌ `api/contacts.py` - импорт `DuplicateContact`
2. ❌ `api/contacts.py` - импорт `duplicate_utils`
3. ❌ `api/contacts.py` - endpoint'ы `/find-duplicates` и `/merge-duplicates`
4. ❌ `services/contact_service.py` - импорт `DuplicateContact`
5. ❌ `services/contact_service.py` - импорт `duplicate_utils`
6. ❌ `services/contact_service.py` - параметр `auto_detect_duplicates`
7. ❌ `services/contact_service.py` - метод `_detect_and_save_duplicates()`
8. ❌ `tests/integration/test_repositories.py` - класс `TestDuplicateRepository`

### Что нужно было сделать:

```bash
# 1. Найти ВСЕ использования
grep -r "DuplicateContact" backend/app/
grep -r "duplicate_utils" backend/app/
grep -r "auto_detect_duplicates" backend/app/

# 2. Удалить ВСЕ найденное
# 3. ТОЛЬКО ПОТОМ удалять основные файлы
# 4. Пересобрать и проверить
```

---

## ⚠️ КРИТИЧНЫЕ МОМЕНТЫ

### Backend будет падать если:

1. ❌ Импорт несуществующего класса
2. ❌ Импорт несуществующего модуля
3. ❌ Вызов несуществующей функции
4. ❌ Использование несуществующего параметра

### Frontend будет падать при build если:

1. ❌ Импорт несуществующего компонента
2. ❌ Использование несуществующего хука
3. ❌ Вызов несуществующей функции API

---

## ✅ ИТОГОВЫЕ РЕКОМЕНДАЦИИ

1. **Всегда ищите ВСЕ использования** перед удалением
2. **Удаляйте в правильном порядке** (зависимости → основные файлы)
3. **Проверяйте build после каждого большого изменения**
4. **Смотрите логи backend'а** при запуске
5. **Тестируйте login** после деплоя
6. **Делайте промежуточные коммиты** при больших изменениях

---

**Создано:** 2025-10-25  
**После инцидента:** Удаление функционала дубликатов  
**Цель:** Предотвратить подобные проблемы в будущем
