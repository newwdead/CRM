# Pages - Страницы приложения

Директория с полноэкранными страницами приложения.

## 📄 Список страниц

### HomePage.js
Главная страница приложения с дашбордом и статистикой.

**Использование:**
```jsx
import HomePage from './components/pages/HomePage';
<Route path="/" element={<HomePage lang={lang} />} />
```

---

### ContactsPage.js
Страница списка контактов с фильтрами и поиском.

**Использование:**
```jsx
import ContactsPage from './components/pages/ContactsPage';
<Route path="/contacts" element={<ContactsPage lang={lang} />} />
```

---

### ContactPage.js
Страница редактирования отдельного контакта.

**URL:** `/contacts/:id`

**Query параметры:**
- `mode=ocr` - автоматически перенаправляет на `/contacts/:id/ocr-editor`

**Использование:**
```jsx
import ContactPage from './components/pages/ContactPage';
<Route path="/contacts/:id" element={<ContactPage lang={lang} />} />
```

---

### OCREditorPage.js ⭐ NEW
Отдельная страница для редактирования OCR блоков визитки.

**URL:** `/contacts/:id/ocr-editor`

**Функциональность:**
- Загрузка контакта по ID
- Полноэкранный OCR редактор
- Редактирование блоков распознавания
- Сохранение изменений
- Навигация назад

**Преимущества:**
- ✅ Собственный URL (можно делиться ссылкой)
- ✅ Можно добавить в закладки
- ✅ F5 обновляет страницу (не теряется контекст)
- ✅ Breadcrumbs для навигации
- ✅ Полноэкранный режим

**Использование:**
```jsx
import OCREditorPage from './components/pages/OCREditorPage';

<Route 
  path="/contacts/:id/ocr-editor" 
  element={<OCREditorPage lang={lang} />} 
/>
```

**Навигация:**
```jsx
// Из ContactList
navigate(`/contacts/${contactId}/ocr-editor`);

// Прямая ссылка
<a href="/contacts/123/ocr-editor">Редактировать OCR</a>
```

**Структура:**
```
OCREditorPage
├── Header
│   ├── Кнопка "Назад"
│   ├── Название
│   └── Info о контакте
├── OCREditorContainer (из modules/ocr)
│   ├── ImageViewer
│   ├── BlockCanvas
│   ├── BlockToolbar
│   └── BlocksList
└── Loading/Error states
```

**Props:**
- `lang` - Язык интерфейса ('ru' | 'en')

**API Calls:**
```javascript
// Load contact
GET /api/contacts/:id

// Save OCR data
PUT /api/contacts/:id
```

**Error Handling:**
- Loading state с спиннером
- Error state с описанием ошибки
- 404 если контакт не найден
- Redirect на /login если нет токена

---

## 🔗 Навигация между страницами

```
/                           → HomePage
/contacts                   → ContactsPage
/contacts/:id               → ContactPage
/contacts/:id/ocr-editor    → OCREditorPage ⭐
/companies                  → Companies
/duplicates                 → DuplicateFinder
/upload                     → UploadCard
/batch-upload               → BatchUpload
/import-export              → ImportExport
/settings                   → Settings
/admin/*                    → AdminPanel
```

## 📱 Mobile Support

Все страницы поддерживают адаптивный дизайн:
- Responsive layout
- Touch-friendly UI
- Mobile navigation
- Pull-to-refresh (где применимо)

## 🎨 UI Guidelines

### Структура страницы
```jsx
<div className="min-h-screen bg-gray-50">
  {/* Header (опционально) */}
  <header className="bg-white shadow-sm border-b">
    {/* Navigation, title, actions */}
  </header>

  {/* Content */}
  <main className="max-w-7xl mx-auto px-4 py-6">
    {/* Page content */}
  </main>
</div>
```

### Loading State
```jsx
<div className="min-h-screen bg-gray-50 flex items-center justify-center">
  <div className="text-center">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
    <p className="text-gray-600">Загрузка...</p>
  </div>
</div>
```

### Error State
```jsx
<div className="min-h-screen bg-gray-50 flex items-center justify-center">
  <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
    <div className="text-red-600 text-center mb-4">
      <svg className="h-12 w-12 mx-auto mb-4" /* ... */ />
      <h2 className="text-xl font-semibold mb-2">Ошибка</h2>
      <p className="text-gray-600">{error}</p>
    </div>
    <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg">
      Действие
    </button>
  </div>
</div>
```

## 🧪 Testing

Для тестирования страниц используйте:

```javascript
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import OCREditorPage from './OCREditorPage';

test('renders OCR editor page', () => {
  render(
    <BrowserRouter>
      <OCREditorPage lang="ru" />
    </BrowserRouter>
  );
  // assertions
});
```

## 📚 Best Practices

1. **Всегда используй PageTitle** для SEO
2. **Loading states** для лучшего UX
3. **Error boundaries** для обработки ошибок
4. **Responsive design** для всех устройств
5. **Accessibility** (aria-labels, keyboard navigation)

## 🔄 Migration Notes

### Переход с модального окна на отдельную страницу

**Было (Modal):**
```jsx
{editingOCR && (
  <OCREditorContainer
    contact={editingOCR}
    onClose={() => setEditingOCR(null)}
  />
)}
```

**Стало (Page):**
```jsx
// В ContactList.js
navigate(`/contacts/${contactId}/ocr-editor`);

// В App.js
<Route 
  path="/contacts/:id/ocr-editor" 
  element={<OCREditorPage lang={lang} />} 
/>
```

**Преимущества:**
- ✅ Чище код (-111 строк modal logic)
- ✅ Лучший UX (полноэкранный режим)
- ✅ Можно делиться ссылками
- ✅ История браузера работает правильно

---

## 📝 Changelog

### v2.23.0
- ✨ Добавлена `OCREditorPage.js` - отдельная страница для OCR редактора
- 🔧 `ContactPage.js` теперь перенаправляет `?mode=ocr` на новый URL
- 🗑️ Удалена modal логика из `ContactList.js`

---

## 🆘 Support

Если возникают проблемы:
1. Проверьте роуты в `App.js`
2. Убедитесь, что токен в `localStorage`
3. Проверьте API endpoints в DevTools
4. Посмотрите console для ошибок

