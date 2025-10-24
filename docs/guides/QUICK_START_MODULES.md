# 🚀 Quick Start: Работа с модулями

**Версия:** 2.21.7  
**Для разработчиков**

---

## ⚡ Быстрый старт (5 минут)

### 1. Импорт модуля

```javascript
// ❌ Старый способ (не использовать)
import OCREditorWithBlocks from './components/OCREditorWithBlocks';

// ✅ Новый способ (модульный)
import { OCREditorContainer } from './modules/ocr';
```

### 2. Использование хука

```javascript
// modules/ocr/hooks/useOCRBlocks.js
import { useOCRBlocks } from './modules/ocr/hooks/useOCRBlocks';

function MyComponent() {
  const {
    blocks,           // Список блоков OCR
    loading,          // Состояние загрузки
    addBlock,         // Добавить блок
    deleteBlock,      // Удалить блок
    updateBlock,      // Обновить блок
    reprocessOCR      // Повторно запустить OCR
  } = useOCRBlocks(contactId);

  return <div>...</div>;
}
```

### 3. API вызовы

```javascript
// ❌ Старый способ
const response = await axios.get(`/api/contacts/${id}/ocr-blocks`);

// ✅ Новый способ
import { fetchOCRBlocks } from './modules/ocr/api/ocrApi';

const blocks = await fetchOCRBlocks(contactId);
```

---

## 📦 Все доступные модули

### 🔍 OCR Module

```javascript
import { 
  OCREditorContainer,     // Главный компонент
  useOCRBlocks,           // Управление блоками
  useBlockDrag,           // Drag & Drop
  useBlockResize,         // Resize
  fetchOCRBlocks,         // API
  reprocessOCR            // API
} from './modules/ocr';
```

### ⚙️ Services Module

```javascript
import { 
  ServicesPanel,          // Главный компонент
  ServiceCard,            // Карточка сервиса
  useServices,            // Управление сервисами
  fetchServicesStatus,    // API
  restartService,         // API
  getServiceLogs          // API
} from './modules/admin/services';
```

### 📇 Contacts Module

```javascript
import { 
  ContactListContainer,   // Главный компонент (альтернатива ContactList)
  ContactTable,           // Таблица
  ContactFilters,         // Фильтры
  ContactActions,         // Bulk actions
  useContacts,            // Управление контактами
  useContactFilters,      // Фильтры
  fetchContacts,          // API
  deleteContact,          // API
  bulkDeleteContacts      // API
} from './modules/contacts';
```

### 🔧 Settings Module

```javascript
import { 
  SettingsPanel,          // Главный компонент
  IntegrationCard,        // Карточка интеграции
  useIntegrations,        // Управление интеграциями
  fetchIntegrationsStatus,// API
  toggleIntegration,      // API
  testIntegration,        // API
  updateIntegrationConfig // API
} from './modules/admin/settings';
```

---

## 🎯 Типичные сценарии

### Сценарий 1: Добавить новую кнопку в OCR Editor

```javascript
// 1. Открыть модуль
// frontend/src/modules/ocr/components/BlockToolbar.js

// 2. Добавить кнопку
<button onClick={handleMyAction}>
  Моя новая функция
</button>

// 3. Добавить обработчик в хук
// frontend/src/modules/ocr/hooks/useOCRBlocks.js

const handleMyAction = useCallback(() => {
  // Твоя логика
}, []);

return { ...existing, handleMyAction };

// 4. Готово! Изменения изолированы только в модуле OCR
```

### Сценарий 2: Добавить новый фильтр в Contacts

```javascript
// 1. Открыть хук фильтров
// frontend/src/modules/contacts/hooks/useContactFilters.js

// 2. Добавить новое состояние
const [myFilter, setMyFilter] = useState('');

// 3. Вернуть из хука
return { ...existing, myFilter, setMyFilter };

// 4. Использовать в компоненте
// frontend/src/modules/contacts/components/ContactFilters.js

const { myFilter, setMyFilter } = useContactFilters();

<input 
  value={myFilter} 
  onChange={(e) => setMyFilter(e.target.value)} 
/>

// 5. Готово! Логика в хуке, UI в компоненте
```

### Сценарий 3: Добавить новый API endpoint

```javascript
// 1. Добавить функцию в API файл
// frontend/src/modules/contacts/api/contactsApi.js

export const myNewApiCall = async (data) => {
  const response = await axios.post('/api/my-endpoint', data);
  return response.data;
};

// 2. Использовать в хуке
// frontend/src/modules/contacts/hooks/useContacts.js

import { myNewApiCall } from '../api/contactsApi';

const handleMyAction = useCallback(async (data) => {
  try {
    const result = await myNewApiCall(data);
    setData(result);
  } catch (error) {
    setError(error.message);
  }
}, []);

// 3. Готово! API изолирован, легко тестировать
```

---

## 🐛 Отладка модулей

### Проверить что модуль загружен

```javascript
import * as OCRModule from './modules/ocr';
console.log('OCR Module:', OCRModule);

// Должно показать:
// {
//   OCREditorContainer: ƒ,
//   useOCRBlocks: ƒ,
//   fetchOCRBlocks: ƒ,
//   ...
// }
```

### Проверить состояние хука

```javascript
const ocrState = useOCRBlocks(contactId);
console.log('OCR State:', ocrState);

// Должно показать:
// {
//   blocks: [...],
//   loading: false,
//   error: null,
//   addBlock: ƒ,
//   ...
// }
```

### Проверить API вызовы

```javascript
import { fetchOCRBlocks } from './modules/ocr/api/ocrApi';

const test = async () => {
  try {
    const blocks = await fetchOCRBlocks(123);
    console.log('Blocks:', blocks);
  } catch (error) {
    console.error('API Error:', error);
  }
};

test();
```

---

## 🔧 Полезные команды

### Найти использование модуля

```bash
# Где используется OCREditorContainer?
grep -r "OCREditorContainer" frontend/src/

# Где импортируется модуль ocr?
grep -r "from.*modules/ocr" frontend/src/
```

### Посмотреть размеры модулей

```bash
# Размер OCR модуля
find frontend/src/modules/ocr -name "*.js" -exec wc -l {} + | tail -1

# Размеры всех модулей
du -sh frontend/src/modules/*
```

### Запустить тесты модулей

```bash
# Тесты всех модулей
npm test -- --testPathPattern=modules

# Тесты конкретного модуля
npm test -- --testPathPattern=modules/ocr

# Тесты конкретного хука
npm test -- useOCRBlocks
```

---

## ⚠️ Распространённые ошибки

### ❌ Ошибка 1: Cannot find module

```
Error: Cannot find module './modules/ocr'
```

**Решение:**
```javascript
// Проверь правильность пути
import { OCREditorContainer } from '../modules/ocr';  // Относительный путь
import { OCREditorContainer } from './modules/ocr';   // Если в том же уровне
```

### ❌ Ошибка 2: Hook returns undefined

```javascript
const { blocks } = useOCRBlocks(contactId);
console.log(blocks); // undefined
```

**Решение:**
```javascript
// Хук возвращает объект, проверь деструктуризацию
const ocrState = useOCRBlocks(contactId);
console.log(ocrState); // { blocks: [...], loading: false, ... }

// Или добавь fallback
const { blocks = [] } = useOCRBlocks(contactId);
```

### ❌ Ошибка 3: Circular dependency

```
Warning: Possible circular dependency detected
```

**Решение:**
```javascript
// ❌ НЕ ДЕЛАЙ ТАК:
// modules/ocr/index.js импортирует modules/contacts
// modules/contacts/index.js импортирует modules/ocr

// ✅ ДЕЛАЙ ТАК:
// Модули должны быть независимыми
// Общую логику вынеси в utils/ или shared/
```

---

## 📚 Дополнительные ресурсы

- **Полная документация:** `frontend/src/modules/README.md`
- **Release Notes:** `RELEASE_NOTES_v2.21.7.md`
- **Migration Logs:** `MIGRATION_LOG_*.md`
- **Тестирование:** `FULL_UI_TEST_v2.21.7.sh`

---

## 💡 Советы

1. **Используй хуки** - вся бизнес-логика должна быть в хуках
2. **Изолируй API** - все axios вызовы в `api/*.js` файлах
3. **Малые компоненты** - держи компоненты < 250 строк
4. **Тестируй** - хуки легко тестировать без UI
5. **Документируй** - добавляй JSDoc комментарии

---

**Успешной разработки! 🚀**

**Вопросы?** Смотри `frontend/src/modules/README.md`

