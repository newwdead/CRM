# Mobile Components - Мобильные компоненты

Коллекция компонентов, оптимизированных для мобильных устройств.

## 📦 Компоненты

### 1. PullToRefresh.js 🔄

Pull-to-refresh жест для обновления контента.

**Функции:**
- Распознавание pull-down жеста
- Плавная анимация (framer-motion)
- Настраиваемый порог срабатывания
- Визуальная обратная связь

**Использование:**
```jsx
import { PullToRefresh } from './components/mobile';

function ContactList() {
  const handleRefresh = async () => {
    await loadContacts();
  };

  return (
    <PullToRefresh 
      onRefresh={handleRefresh}
      threshold={80}
      lang="ru"
    >
      <div>
        {/* Ваш контент */}
      </div>
    </PullToRefresh>
  );
}
```

**Props:**
- `children: React.Node` - Контент для обёртывания
- `onRefresh: () => Promise<void>` - Callback для обновления
- `threshold?: number` - Порог в пикселях (default: 80)
- `lang?: 'ru' | 'en'` - Язык (default: 'ru')

**Состояния:**
- "Потяните для обновления" (pull distance < threshold)
- "Отпустите для обновления" (pull distance >= threshold)
- "Обновление..." (refreshing)

**Код:**
```jsx
<PullToRefresh onRefresh={async () => {
  await fetchData();
}}>
  <YourContent />
</PullToRefresh>
```

---

### 2. CameraScanner.js 📷

Прямой доступ к камере для сканирования визиток.

**Функции:**
- Предпросмотр камеры
- Захват фото
- Управление вспышкой
- Переключение камеры (фронтальная/задняя)
- Направляющая для фокусировки
- Обработка ошибок

**Использование:**
```jsx
import { CameraScanner } from './components/mobile';

function UploadPage() {
  const [showCamera, setShowCamera] = useState(false);

  const handleCapture = async (imageBlob) => {
    // Отправить на сервер
    await uploadImage(imageBlob);
    setShowCamera(false);
  };

  return (
    <div>
      <button onClick={() => setShowCamera(true)}>
        📷 Открыть камеру
      </button>

      {showCamera && (
        <CameraScanner
          onCapture={handleCapture}
          onClose={() => setShowCamera(false)}
          lang="ru"
        />
      )}
    </div>
  );
}
```

**Props:**
- `onCapture: (blob: Blob) => void` - Callback с захваченным изображением
- `onClose: () => void` - Callback для закрытия
- `lang?: 'ru' | 'en'` - Язык (default: 'ru')

**Возможности:**
- ✅ Автофокус
- ✅ Flash on/off
- ✅ Переключение камер
- ✅ Preview захваченного фото
- ✅ Retake функция

**Permissions:**
Требуется разрешение `navigator.mediaDevices.getUserMedia()`

**Browser Support:**
- ✅ Chrome Mobile 53+
- ✅ Safari iOS 11+
- ✅ Firefox Mobile 68+
- ❌ Old browsers (показывает ошибку)

---

### 3. ContactCardView.js 📇

Мобильная версия списка контактов в виде карточек.

**Функции:**
- Touch-friendly UI
- Карточный layout
- Быстрые действия (звонок, email)
- Индикатор дубликатов
- Lazy loading изображений

**Использование:**
```jsx
import { ContactCardView } from './components/mobile';

function MobileContactList({ contacts }) {
  const handleContactClick = (contact) => {
    navigate(`/contacts/${contact.id}`);
  };

  return (
    <div>
      {contacts.map(contact => (
        <ContactCardView
          key={contact.id}
          contact={contact}
          onClick={handleContactClick}
          lang="ru"
        />
      ))}
    </div>
  );
}
```

**Props:**
- `contact: Contact` - Объект контакта
- `onClick?: (contact: Contact) => void` - Callback при клике
- `lang?: 'ru' | 'en'` - Язык
- `showActions?: boolean` - Показывать кнопки действий (default: true)
- `showDuplicateBadge?: boolean` - Показывать бейдж дубликатов (default: true)

**Структура карточки:**
```
┌─────────────────────────────┐
│ [Avatar]  Name              │
│           Company           │
│           Position          │
├─────────────────────────────┤
│ 📧 email@example.com        │
│ 📱 +7 999 123-45-67         │
├─────────────────────────────┤
│ [📞 Позвонить] [✉️ Написать] │
└─────────────────────────────┘
```

---

### 4. BottomNavigation.js 🧭

Нижняя навигационная панель для мобильных устройств.

**Функции:**
- Фиксированная позиция внизу
- Индикатор активной страницы
- Touch-optimized кнопки
- Badge с счётчиками

**Использование:**
```jsx
import { BottomNavigation } from './components/mobile';

function MobileApp() {
  const items = [
    { 
      id: 'home', 
      icon: '🏠', 
      label: 'Главная', 
      path: '/' 
    },
    { 
      id: 'contacts', 
      icon: '👥', 
      label: 'Контакты', 
      path: '/contacts',
      badge: 5 
    },
    { 
      id: 'search', 
      icon: '🔍', 
      label: 'Поиск', 
      path: '/search' 
    },
    { 
      id: 'profile', 
      icon: '👤', 
      label: 'Профиль', 
      path: '/profile' 
    }
  ];

  return (
    <div>
      <main>{/* Контент */}</main>
      <BottomNavigation 
        items={items}
        activeId="contacts"
        lang="ru"
      />
    </div>
  );
}
```

**Props:**
- `items: NavigationItem[]` - Элементы навигации
- `activeId: string` - ID активного элемента
- `lang?: 'ru' | 'en'` - Язык

**NavigationItem:**
```typescript
interface NavigationItem {
  id: string;
  icon: string | React.Node;
  label: string;
  path: string;
  badge?: number;
  onClick?: () => void;
}
```

**Стили:**
```css
.bottom-navigation {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
  z-index: 999;
}
```

---

## 📱 Когда использовать

### PullToRefresh
- ✅ Списки контактов
- ✅ Новостная лента
- ✅ Обновляемый контент
- ❌ Формы ввода
- ❌ Статичные страницы

### CameraScanner
- ✅ Сканирование визиток
- ✅ OCR документов
- ✅ QR коды
- ❌ Галерея фото
- ❌ Desktop (используйте file input)

### ContactCardView
- ✅ Mobile устройства (< 768px)
- ✅ Списки с малым количеством данных
- ❌ Desktop (используйте таблицу)
- ❌ Большие списки (используйте виртуализацию)

### BottomNavigation
- ✅ Mobile устройства (< 768px)
- ✅ 3-5 основных разделов
- ❌ Desktop (используйте sidebar)
- ❌ Больше 5 разделов (используйте hamburger menu)

---

## 🎨 Styling

Все компоненты используют Tailwind CSS:

```jsx
// Пример кастомизации
<PullToRefresh 
  className="custom-pull"
  style={{ background: '#f0f0f0' }}
>
  <Content />
</PullToRefresh>
```

**Theme Variables:**
```css
:root {
  --mobile-nav-height: 60px;
  --mobile-safe-area: env(safe-area-inset-bottom);
  --mobile-touch-target: 44px;
}
```

---

## 🔄 Интеграция с другими компонентами

### С OCR Editor
```jsx
function MobileOCREditor() {
  return (
    <PullToRefresh onRefresh={reloadOCRBlocks}>
      <OCREditorContainer />
    </PullToRefresh>
  );
}
```

### С Contact List
```jsx
import { isMobileDevice } from './utils/deviceDetection';

function ContactList() {
  const isMobile = isMobileDevice();

  if (isMobile) {
    return (
      <>
        <PullToRefresh onRefresh={loadContacts}>
          {contacts.map(c => (
            <ContactCardView contact={c} />
          ))}
        </PullToRefresh>
        <BottomNavigation items={navItems} />
      </>
    );
  }

  return <ContactTable contacts={contacts} />;
}
```

---

## 📊 Performance

### Оптимизация

**1. Lazy Loading:**
```jsx
const CameraScanner = lazy(() => 
  import('./components/mobile/CameraScanner')
);

// Загружается только когда нужно
{showCamera && (
  <Suspense fallback={<Loading />}>
    <CameraScanner />
  </Suspense>
)}
```

**2. Виртуализация:**
```jsx
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={contacts.length}
  itemSize={120}
>
  {({ index, style }) => (
    <div style={style}>
      <ContactCardView contact={contacts[index]} />
    </div>
  )}
</FixedSizeList>
```

**3. Мемоизация:**
```jsx
const ContactCardView = memo(({ contact }) => {
  // ...
});
```

---

## 🧪 Testing

```javascript
import { render, fireEvent, waitFor } from '@testing-library/react';
import { PullToRefresh } from './mobile';

test('pull to refresh works', async () => {
  const onRefresh = jest.fn(() => Promise.resolve());
  
  const { container } = render(
    <PullToRefresh onRefresh={onRefresh}>
      <div>Content</div>
    </PullToRefresh>
  );

  // Simulate pull gesture
  fireEvent.touchStart(container, { touches: [{ clientY: 0 }] });
  fireEvent.touchMove(container, { touches: [{ clientY: 100 }] });
  fireEvent.touchEnd(container);

  await waitFor(() => {
    expect(onRefresh).toHaveBeenCalled();
  });
});
```

---

## 📚 Dependencies

- `framer-motion` - Анимации
- `react` - Core
- `react-router-dom` - Навигация

---

## 📝 Changelog

### v2.25.0
- ✅ Все компоненты готовы и протестированы
- ✅ Добавлена документация
- ✅ Интеграция с deviceDetection

### Existing (v2.17.0)
- ✨ PullToRefresh (167 строк)
- ✨ CameraScanner (360 строк)
- ✨ ContactCardView (308 строк)
- ✨ BottomNavigation (132 строк)

---

## 🔗 Related

- Utils: `/utils/deviceDetection.js`
- Documentation: `MOBILE_OPTIMIZATION_v2.17.md`
- OCR Module: `/modules/ocr/`

---

## 🆘 Troubleshooting

### Camera не работает
1. Проверьте HTTPS (требуется для getUserMedia)
2. Проверьте permissions
3. Проверьте browser support

### Pull-to-refresh конфликтует с scroll
1. Проверьте, что container scrollable
2. Убедитесь, что не вложены несколько PullToRefresh
3. Проверьте CSS overflow

### BottomNavigation перекрывает контент
```css
/* Добавьте padding-bottom */
main {
  padding-bottom: calc(60px + env(safe-area-inset-bottom));
}
```

