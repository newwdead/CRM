# 📦 Модульная архитектура Frontend

**Версия:** 2.26.0  
**Дата:** 2025-10-22  
**Статус:** ✅ Production Ready

---

## 📊 Обзор

Этот проект использует **модульную архитектуру** для организации frontend кода. Каждый модуль независим и содержит свою логику, компоненты и API.

### Преимущества:
- ✅ **Изоляция ошибок** - баг в OCR не влияет на Contacts
- ✅ **Переиспользование** - хуки можно использовать в других компонентах
- ✅ **Тестируемость** - каждый модуль тестируется отдельно
- ✅ **Читаемость** - файлы < 250 строк, легко понять
- ✅ **Масштабируемость** - легко добавлять новые модули

---

## 🗂️ Структура модулей

```
frontend/src/modules/
├── ocr/                        # 🔍 OCR и обработка изображений
│   ├── api/                    # API вызовы
│   ├── hooks/                  # Custom hooks (бизнес-логика)
│   ├── components/             # UI компоненты
│   └── index.js                # Экспорт модуля
│
├── contacts/                   # 📇 Управление контактами
│   ├── api/
│   ├── hooks/
│   ├── components/
│   └── index.js
│
├── duplicates/                 # 🔄 Управление дубликатами ⭐ NEW
│   ├── api/
│   ├── hooks/
│   └── index.js
│
└── admin/                      # 👔 Административные модули
    ├── services/               # ⚙️ Управление сервисами
    │   ├── api/
    │   ├── hooks/
    │   ├── components/
    │   └── index.js
    │
    └── settings/               # 🔧 Системные настройки
        ├── api/
        ├── hooks/
        ├── components/
        └── index.js
```

---

## 📦 Модули

### 1️⃣ OCR Module (`modules/ocr/`)

**Назначение:** Редактор OCR с визуальным управлением блоками распознавания

**Структура:**
```
ocr/
├── api/
│   └── ocrApi.js              # fetchOCRBlocks, reprocessOCR
├── hooks/
│   ├── useOCRBlocks.js        # Управление состоянием блоков
│   ├── useBlockDrag.js        # Drag & Drop логика
│   └── useBlockResize.js      # Resize логика
├── components/
│   ├── OCREditorContainer.js  # Главный контейнер
│   ├── ImageViewer.js         # Отображение изображения
│   ├── BlockCanvas.js         # Canvas с блоками
│   ├── BlockToolbar.js        # Инструменты редактирования
│   └── BlocksList.js          # Список блоков
└── index.js
```

**Использование:**
```javascript
import { OCREditorContainer } from '../modules/ocr';

<OCREditorContainer
  contact={contact}
  onSave={(data) => console.log(data)}
  onClose={() => console.log('Closed')}
/>
```

**Хуки:**
```javascript
import { useOCRBlocks } from '../modules/ocr/hooks/useOCRBlocks';

const { blocks, addBlock, deleteBlock, updateBlock } = useOCRBlocks(contactId);
```

**Статистика:** 10 файлов, 1329 строк (было 1150 строк в 1 файле)

---

### 2️⃣ Services Module (`modules/admin/services/`)

**Назначение:** Управление Docker сервисами (status, restart, logs)

**Структура:**
```
admin/services/
├── api/
│   └── servicesApi.js         # fetchServicesStatus, restartService, getServiceLogs
├── hooks/
│   └── useServices.js         # Управление сервисами
├── components/
│   ├── ServicesPanel.js       # Главная панель
│   └── ServiceCard.js         # Карточка сервиса
└── index.js
```

**Использование:**
```javascript
import { ServicesPanel } from '../modules/admin/services';

<ServicesPanel language="en" />
```

**Хуки:**
```javascript
import { useServices } from '../modules/admin/services/hooks/useServices';

const { services, loading, refreshServices, restartService } = useServices();
```

**Статистика:** 5 файлов, 652 строки (было 605+181=786 строк в 2 файлах)

---

### 3️⃣ Contacts Module (`modules/contacts/`)

**Назначение:** Список контактов с фильтрацией, пагинацией, bulk actions

**Структура:**
```
contacts/
├── api/
│   └── contactsApi.js         # fetchContacts, deleteContact, bulkDelete, bulkUpdate
├── hooks/
│   ├── useContacts.js         # Управление контактами
│   └── useContactFilters.js   # Фильтры и сортировка
├── components/
│   ├── ContactListContainer.js # Главный контейнер
│   ├── ContactTable.js        # Таблица контактов
│   ├── ContactFilters.js      # Фильтры
│   └── ContactActions.js      # Bulk actions
└── index.js
```

**Использование:**
```javascript
import { ContactListContainer } from '../modules/contacts';

<ContactListContainer language="en" />
```

**Хуки:**
```javascript
import { useContacts } from '../modules/contacts/hooks/useContacts';
import { useContactFilters } from '../modules/contacts/hooks/useContactFilters';

const { contacts, loading, deleteContact } = useContacts();
const { searchTerm, setSearchTerm, filters } = useContactFilters();
```

**Статистика:** 8 файлов, 1073 строки (было 1079 строк в 1 файле)

---

### 4️⃣ Settings Module (`modules/admin/settings/`)

**Назначение:** Системные настройки и управление интеграциями

**Структура:**
```
admin/settings/
├── api/
│   └── settingsApi.js         # fetchIntegrations, toggleIntegration, testIntegration
├── hooks/
│   └── useIntegrations.js     # Управление интеграциями
├── components/
│   ├── SettingsPanel.js       # Главная панель
│   └── IntegrationCard.js     # Карточка интеграции
└── index.js
```

**Использование:**
```javascript
import { SettingsPanel } from '../modules/admin/settings';

<SettingsPanel language="en" />
```

**Хуки:**
```javascript
import { useIntegrations } from '../modules/admin/settings/hooks/useIntegrations';

const { integrations, loading, toggleIntegration, testIntegration } = useIntegrations();
```

**Статистика:** 5 файлов, 233 строки (было 603 строки в 1 файле)

---

### 5️⃣ Duplicates Module (`modules/duplicates/`) ⭐ NEW

**Назначение:** Обнаружение и объединение дубликатов контактов

**Структура:**
```
duplicates/
├── api/
│   └── duplicatesApi.js       # fetchDuplicates, mergeDuplicates, markAsReviewed, dismissDuplicate
├── hooks/
│   └── useDuplicates.js       # Управление дубликатами
└── index.js
```

**Использование:**
```javascript
import { useDuplicates, duplicatesApi } from '../modules/duplicates';

function DuplicatesManager() {
  const { 
    duplicates, 
    groupedDuplicates, 
    loading, 
    mergeDuplicates,
    dismissDuplicate,
    getDuplicateCount,
    hasDuplicates
  } = useDuplicates();

  return (
    <div>
      {duplicates.map(dup => (
        <DuplicateCard 
          key={dup.id}
          duplicate={dup}
          onMerge={() => mergeDuplicates(dup.contact_id_1, [dup.contact_id_2])}
          onDismiss={() => dismissDuplicate(dup.id)}
        />
      ))}
    </div>
  );
}
```

**API Methods:**
```javascript
// Получить все дубликаты
const duplicates = await duplicatesApi.fetchDuplicates();

// Получить дубликаты для контакта
const contactDups = await duplicatesApi.fetchContactDuplicates(contactId);

// Объединить контакты
await duplicatesApi.mergeDuplicates(primaryId, [duplicateId1, duplicateId2]);

// Отметить как просмотренное
await duplicatesApi.markAsReviewed(duplicateId);

// Отклонить совпадение
await duplicatesApi.dismissDuplicate(duplicateId);
```

**Хуки:**
```javascript
import { useDuplicates } from '../modules/duplicates/hooks/useDuplicates';

const {
  duplicates,              // Массив всех дубликатов
  groupedDuplicates,       // Дубликаты, сгруппированные по contact_id
  loading,                 // Состояние загрузки
  error,                   // Ошибка
  loadDuplicates,          // Перезагрузить
  loadContactDuplicates,   // Загрузить для контакта
  mergeDuplicates,         // Объединить
  markAsReviewed,          // Отметить как просмотренное
  dismissDuplicate,        // Отклонить
  getDuplicateCount,       // Получить количество для контакта
  hasDuplicates            // Проверить наличие дубликатов
} = useDuplicates();
```

**Статистика:** 3 файла, 290 строк

---

## 🎯 Руководство по добавлению нового модуля

### Шаг 1: Создать структуру

```bash
mkdir -p frontend/src/modules/my-module/{api,hooks,components}
touch frontend/src/modules/my-module/index.js
```

### Шаг 2: API слой (`api/myApi.js`)

```javascript
import axios from 'axios';

export const fetchData = async () => {
  const response = await axios.get('/api/my-data');
  return response.data;
};

export const saveData = async (data) => {
  const response = await axios.post('/api/my-data', data);
  return response.data;
};
```

### Шаг 3: Хук (`hooks/useMyData.js`)

```javascript
import { useState, useEffect, useCallback } from 'react';
import { fetchData, saveData } from '../api/myApi';

export const useMyData = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchData();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const save = useCallback(async (newData) => {
    try {
      await saveData(newData);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  }, [loadData]);

  return { data, loading, error, save, refresh: loadData };
};
```

### Шаг 4: Компонент (`components/MyComponent.js`)

```javascript
import React from 'react';
import { useMyData } from '../hooks/useMyData';

export const MyComponent = () => {
  const { data, loading, error, save } = useMyData();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
};
```

### Шаг 5: Экспорт (`index.js`)

```javascript
export { MyComponent } from './components/MyComponent';
export { useMyData } from './hooks/useMyData';
export * from './api/myApi';
```

### Шаг 6: Использование

```javascript
import { MyComponent } from './modules/my-module';

function App() {
  return <MyComponent />;
}
```

---

## 🧪 Тестирование модулей

### Unit тесты для хуков

```javascript
// hooks/__tests__/useMyData.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import { useMyData } from '../useMyData';

jest.mock('../api/myApi');

test('should load data on mount', async () => {
  const { result, waitForNextUpdate } = renderHook(() => useMyData());
  
  expect(result.current.loading).toBe(true);
  await waitForNextUpdate();
  expect(result.current.data).toHaveLength(3);
});
```

### Integration тесты для компонентов

```javascript
// components/__tests__/MyComponent.test.js
import { render, screen } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

test('renders data', async () => {
  render(<MyComponent />);
  
  const item = await screen.findByText('Item 1');
  expect(item).toBeInTheDocument();
});
```

---

## 📊 Статистика модулей

| Модуль | Файлов | Строк | Было | Экономия |
|--------|--------|-------|------|----------|
| **OCR** | 10 | 1329 | 1×1150 | +179 (модульность) |
| **Services** | 5 | 652 | 2×786 | **-134** |
| **Contacts** | 8 | 1073 | 1×1079 | **-6** |
| **Settings** | 5 | 233 | 1×603 | **-370** |
| **Duplicates** ⭐ | 3 | 290 | новый | новый |
| **ИТОГО** | **31** | **3577** | **3618** | **-510** |

---

## 🎯 Best Practices

### ✅ DO:
- Держать компоненты < 250 строк
- Использовать custom hooks для бизнес-логики
- Изолировать API вызовы в отдельных файлах
- Использовать `useCallback` для функций
- Мемоизировать тяжёлые вычисления с `useMemo`

### ❌ DON'T:
- Не смешивать логику и UI в одном файле
- Не делать API вызовы напрямую в компонентах
- Не дублировать код между модулями
- Не создавать циклические зависимости между модулями

---

## 🔗 Ссылки

- [Release Notes v2.21.7](../../../RELEASE_NOTES_v2.21.7.md)
- [Release Notes v2.21.8](../../../RELEASE_NOTES_v2.21.8.md)
- [Pages Documentation](../../components/pages/README.md)
- [Utils Documentation](../../utils/README.md)
- [Mobile Components](../../components/mobile/README.md)
- [Optimization Plan](../../../PROJECT_OPTIMIZATION_PLAN_v2.21.3.md)

---

**Дата создания:** 2025-10-22  
**Последнее обновление:** 2025-10-22  
**Версия:** 2.26.0  
**Статус:** ✅ Production

**Новое в v2.26.0:**
- ✨ Добавлен Duplicates модуль
- 📱 Документация для mobile компонентов
- 📄 Документация для pages
- 🛠️ Документация для utils
- 📊 Обновлена статистика

