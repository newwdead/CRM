# 📚 Frontend Documentation Index

**Версия:** 2.26.0  
**Дата:** 2025-10-22  
**Язык:** Русский

---

## 🗂️ Структура документации

### 📦 Модули (`src/modules/`)

**Главная документация:**
- [**README.md**](src/modules/README.md) - Обзор модульной архитектуры

**Модули:**
1. [**OCR Module**](src/modules/README.md#1-ocr-module) - Редактор OCR с блоками
2. [**Services Module**](src/modules/README.md#2-services-module) - Управление Docker сервисами
3. [**Contacts Module**](src/modules/README.md#3-contacts-module) - Список контактов
4. [**Settings Module**](src/modules/README.md#4-settings-module) - Системные настройки
5. [**Duplicates Module**](src/modules/README.md#5-duplicates-module) ⭐ NEW - Управление дубликатами

---

### 📄 Страницы (`src/components/pages/`)

**Документация:**
- [**README.md**](src/components/pages/README.md) - Полноэкранные страницы

**Страницы:**
1. `HomePage.js` - Главная страница
2. `ContactsPage.js` - Список контактов
3. `ContactPage.js` - Редактирование контакта
4. `OCREditorPage.js` ⭐ NEW - OCR редактор (отдельная страница)

**Особенности OCREditorPage:**
- ✅ Собственный URL: `/contacts/:id/ocr-editor`
- ✅ Можно делиться ссылкой
- ✅ Добавить в закладки
- ✅ Полноэкранный режим

---

### 📱 Мобильные компоненты (`src/components/mobile/`)

**Документация:**
- [**README.md**](src/components/mobile/README.md) - Mobile-оптимизированные компоненты

**Компоненты:**
1. `PullToRefresh.js` - Pull-to-refresh жест (167 строк)
2. `CameraScanner.js` - Прямой доступ к камере (360 строк)
3. `ContactCardView.js` - Карточный вид контактов (308 строк)
4. `BottomNavigation.js` - Нижняя навигация (132 строк)

**Статус:** ✅ Production Ready

---

### 🛠️ Утилиты (`src/utils/`)

**Документация:**
- [**README.md**](src/utils/README.md) - Вспомогательные функции

**Утилиты:**
1. `deviceDetection.js` ⭐ NEW - Определение устройства (121 строка)
   - `isMobileDevice()`
   - `hasCamera()`
   - `getDeviceType()`
   - `isIOS() / isAndroid()`
   - `getScreenSize()`
   - `isPWA()`
   - `vibrate()`
   - `getOrientation()`

---

## 🔍 Быстрый поиск

### По задачам:

**Хочу добавить новый модуль:**
→ [Руководство по добавлению модуля](src/modules/README.md#-руководство-по-добавлению-нового-модуля)

**Хочу создать новую страницу:**
→ [Документация Pages](src/components/pages/README.md)

**Хочу использовать mobile компоненты:**
→ [Mobile Components](src/components/mobile/README.md)

**Хочу определить тип устройства:**
→ [deviceDetection.js](src/utils/README.md#-devicedetectionjs--new)

**Хочу работать с дубликатами:**
→ [Duplicates Module](src/modules/README.md#5-duplicates-module)

**Хочу редактировать OCR:**
→ [OCR Module](src/modules/README.md#1-ocr-module) + [OCREditorPage](src/components/pages/README.md#ocreditorpagejs--new)

---

## 📊 Статистика проекта

### Frontend Modules
| Категория | Файлов | Строк |
|-----------|--------|-------|
| **Modules** | 31 | 3577 |
| **Mobile** | 5 | 1088 |
| **Utils** | 1 | 121 |
| **Pages** | 4 | ~800 |
| **ИТОГО** | 41 | ~5586 |

### Документация
| Файл | Строк | Статус |
|------|-------|--------|
| `modules/README.md` | 497 | ✅ |
| `pages/README.md` | 368 | ✅ |
| `mobile/README.md` | 489 | ✅ |
| `utils/README.md` | 428 | ✅ |
| `DOCUMENTATION_INDEX.md` | этот файл | ✅ |
| **ИТОГО** | ~1782 | ✅ |

---

## 🎯 Руководства

### Для новых разработчиков:

1. **Начните с модулей:**
   - Прочитайте [Модульная архитектура](src/modules/README.md)
   - Изучите структуру OCR модуля
   - Попробуйте создать свой модуль

2. **Изучите страницы:**
   - Прочитайте [Pages Documentation](src/components/pages/README.md)
   - Посмотрите на OCREditorPage как пример

3. **Mobile разработка:**
   - Прочитайте [Mobile Components](src/components/mobile/README.md)
   - Используйте [deviceDetection](src/utils/README.md)

4. **Best Practices:**
   - Держите файлы < 250 строк
   - Используйте custom hooks
   - Изолируйте API вызовы
   - Мемоизируйте компоненты

---

## 🔄 История изменений

### v2.26.0 (2025-10-22) ⭐ CURRENT
- ✨ Добавлен Duplicates модуль
- 📱 Документация mobile компонентов
- 📄 Документация pages
- 🛠️ Документация utils
- 📚 DOCUMENTATION_INDEX.md

### v2.25.0 (2025-10-22)
- ✨ deviceDetection.js утилиты
- 📱 Mobile компоненты готовы

### v2.24.0 (2025-10-22)
- 🏗️ Backend Repository Layer
- 📦 4 endpoint'а мигрировано

### v2.23.0 (2025-10-22)
- 📄 OCREditorPage - отдельная страница
- 🔗 Новый URL для OCR редактора

### v2.21.8 (2025-10-22)
- 📚 Frontend Modules документация
- 🧪 Тестирование модулей

### v2.21.7 (2025-10-22)
- ✨ Модульная архитектура
- 🔧 OCR, Services, Contacts, Settings модули

---

## 🔗 Связанные документы

### В корне проекта:
- `RELEASE_NOTES_v2.*.md` - Истории релизов
- `MOBILE_OPTIMIZATION_v2.17.md` - Mobile оптимизация
- `ARCHITECTURE_AUDIT_v2.16.md` - Аудит архитектуры
- `QUICK_START_MODULES.md` - Быстрый старт

### Backend:
- `backend/BACKEND_3_LAYER_PATTERN.md` - Backend архитектура
- `backend/app/services/` - Services layer

---

## 📞 Поддержка

**Вопросы по документации:**
1. Проверьте соответствующий README.md
2. Посмотрите примеры кода
3. Изучите существующие модули

**Нашли ошибку в документации:**
1. Проверьте версию (v2.26.0)
2. Убедитесь, что файл актуален
3. Создайте issue или PR

---

## 🎓 Обучающие материалы

### Tutorials:
1. [Создание нового модуля](src/modules/README.md#-руководство-по-добавлению-нового-модуля)
2. [Mobile компоненты](src/components/mobile/README.md#-примеры-использования)
3. [Device Detection](src/utils/README.md#-примеры-использования)
4. [OCR Editor](src/components/pages/README.md#ocreditorpagejs--new)

### Code Examples:
- [API Layer](src/modules/README.md#шаг-2-api-слой-apimyapijs)
- [Custom Hook](src/modules/README.md#шаг-3-хук-hooksusemydatajs)
- [Component](src/modules/README.md#шаг-4-компонент-componentsmycomponentjs)

---

**Дата создания:** 2025-10-22  
**Версия:** 2.26.0  
**Статус:** ✅ Complete

---

*Эта документация охватывает весь frontend проект. Для backend документации смотрите `backend/BACKEND_3_LAYER_PATTERN.md`*

