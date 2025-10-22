# Utils - Утилиты

Вспомогательные функции и утилиты для frontend приложения.

## 📱 deviceDetection.js ⭐ NEW

Утилиты для определения типа устройства и его возможностей.

### Импорт

```javascript
import {
  isMobileDevice,
  isTouchDevice,
  hasCamera,
  getDeviceType,
  isIOS,
  isAndroid,
  getScreenSize,
  isPWA,
  hasVibration,
  vibrate,
  getOrientation
} from './utils/deviceDetection';

// Или
import deviceDetection from './utils/deviceDetection';
```

---

### 📲 Основные функции

#### `isMobileDevice(): boolean`
Проверяет, является ли устройство мобильным.

```javascript
if (isMobileDevice()) {
  // Показать мобильную версию
  return <MobileView />;
}
```

**Определяет:** Android, iOS, iPad, iPod, BlackBerry, Opera Mini, Windows Phone

---

#### `isTouchDevice(): boolean`
Проверяет поддержку тач-событий.

```javascript
if (isTouchDevice()) {
  // Использовать touch events
  element.addEventListener('touchstart', handler);
} else {
  // Использовать mouse events
  element.addEventListener('mousedown', handler);
}
```

---

#### `hasCamera(): boolean`
Проверяет доступность камеры.

```javascript
if (hasCamera()) {
  return (
    <button onClick={openCameraScanner}>
      📷 Сканировать визитку
    </button>
  );
}
```

---

#### `getDeviceType(): 'mobile' | 'tablet' | 'desktop'`
Определяет тип устройства.

```javascript
const deviceType = getDeviceType();

switch(deviceType) {
  case 'mobile':
    return <MobileLayout />;
  case 'tablet':
    return <TabletLayout />;
  case 'desktop':
    return <DesktopLayout />;
}
```

---

#### `isIOS(): boolean`
Проверяет, является ли устройство iOS.

```javascript
if (isIOS()) {
  // iOS-специфичный код
  // Например, для обработки safe area
}
```

---

#### `isAndroid(): boolean`
Проверяет, является ли устройство Android.

```javascript
if (isAndroid()) {
  // Android-специфичный код
}
```

---

### 📐 Размер экрана

#### `getScreenSize(): 'small' | 'medium' | 'large' | 'xlarge'`
Определяет категорию размера экрана.

```javascript
const screenSize = getScreenSize();

const columns = {
  small: 1,    // < 640px (mobile portrait)
  medium: 2,   // < 768px (mobile landscape)
  large: 3,    // < 1024px (tablet)
  xlarge: 4    // >= 1024px (desktop)
}[screenSize];
```

**Breakpoints:**
- `small`: < 640px (Mobile Portrait)
- `medium`: 640-767px (Mobile Landscape / Small Tablet)
- `large`: 768-1023px (Tablet)
- `xlarge`: >= 1024px (Desktop)

---

### 🌐 PWA функции

#### `isPWA(): boolean`
Проверяет, запущено ли приложение как PWA.

```javascript
if (isPWA()) {
  // Скрыть prompt "Добавить на главный экран"
  hideInstallPrompt();
}
```

---

### 📳 Вибрация

#### `hasVibration(): boolean`
Проверяет поддержку вибрации.

```javascript
if (hasVibration()) {
  // Показать настройки вибрации
}
```

---

#### `vibrate(pattern: number | number[]): void`
Вызывает вибрацию устройства.

```javascript
// Одна вибрация 10ms (по умолчанию)
vibrate();

// Кастомная длительность
vibrate(200);

// Паттерн: вибрация-пауза-вибрация
vibrate([200, 100, 200]);

// Использование при событиях
button.addEventListener('click', () => {
  vibrate(10); // Тактильный feedback
});
```

**Паттерны:**
- `10` - Легкий клик
- `50` - Средний клик
- `100` - Сильный клик
- `[200, 100, 200]` - Двойная вибрация

---

### 📱 Ориентация

#### `getOrientation(): 'portrait' | 'landscape'`
Определяет ориентацию экрана.

```javascript
const orientation = getOrientation();

if (orientation === 'landscape') {
  // Показать предупреждение
  showRotateDeviceMessage();
}

// Слушать изменения
window.addEventListener('resize', () => {
  const newOrientation = getOrientation();
  console.log('Ориентация:', newOrientation);
});
```

---

## 💡 Примеры использования

### Адаптивные компоненты

```javascript
import { isMobileDevice, getScreenSize } from './utils/deviceDetection';

function ContactList() {
  const isMobile = isMobileDevice();
  const screenSize = getScreenSize();

  if (isMobile) {
    return <ContactCardView />; // Mobile: карточки
  }
  
  return <ContactTable />; // Desktop: таблица
}
```

---

### Camera Scanner

```javascript
import { hasCamera, isMobileDevice } from './utils/deviceDetection';
import CameraScanner from './components/mobile/CameraScanner';

function UploadPage() {
  const showCameraButton = hasCamera() && isMobileDevice();

  return (
    <div>
      {showCameraButton && (
        <button onClick={openCamera}>
          📷 Сканировать камерой
        </button>
      )}
      <input type="file" accept="image/*" />
    </div>
  );
}
```

---

### Тактильный feedback

```javascript
import { hasVibration, vibrate } from './utils/deviceDetection';

function ActionButton({ onClick }) {
  const handleClick = () => {
    if (hasVibration()) {
      vibrate(10); // Легкая вибрация
    }
    onClick();
  };

  return (
    <button onClick={handleClick}>
      Удалить
    </button>
  );
}
```

---

### Responsive Navigation

```javascript
import { isMobileDevice, getScreenSize } from './utils/deviceDetection';
import BottomNavigation from './components/mobile/BottomNavigation';
import SideNavigation from './components/SideNavigation';

function Navigation() {
  const isMobile = isMobileDevice();
  const screenSize = getScreenSize();

  if (isMobile || screenSize === 'small') {
    return <BottomNavigation />; // Mobile: bottom bar
  }

  return <SideNavigation />; // Desktop: sidebar
}
```

---

### PWA Install Prompt

```javascript
import { isPWA } from './utils/deviceDetection';

function InstallPrompt() {
  const isInstalled = isPWA();

  if (isInstalled) {
    return null; // Уже установлено
  }

  return (
    <div className="install-prompt">
      <p>Установите приложение на главный экран</p>
      <button>Установить</button>
    </div>
  );
}
```

---

### Platform-specific Styles

```javascript
import { isIOS, isAndroid } from './utils/deviceDetection';

function App() {
  const platform = isIOS() ? 'ios' : isAndroid() ? 'android' : 'web';

  return (
    <div className={`app app-${platform}`}>
      {/* iOS: padding-bottom для safe area */}
      {/* Android: материальный дизайн */}
      {/* Web: стандартные стили */}
    </div>
  );
}
```

---

## 🎯 Best Practices

### 1. Кэшировать результаты

```javascript
// ❌ Плохо: вызывать каждый раз
function Component() {
  if (isMobileDevice()) { /* ... */ }
  if (isMobileDevice()) { /* ... */ }
  if (isMobileDevice()) { /* ... */ }
}

// ✅ Хорошо: сохранить в переменную
function Component() {
  const isMobile = isMobileDevice();
  
  if (isMobile) { /* ... */ }
  if (isMobile) { /* ... */ }
  if (isMobile) { /* ... */ }
}
```

---

### 2. React Hook для device detection

```javascript
import { useState, useEffect } from 'react';
import { isMobileDevice, getScreenSize, getOrientation } from './utils/deviceDetection';

function useDeviceInfo() {
  const [deviceInfo, setDeviceInfo] = useState({
    isMobile: isMobileDevice(),
    screenSize: getScreenSize(),
    orientation: getOrientation()
  });

  useEffect(() => {
    const handleResize = () => {
      setDeviceInfo({
        isMobile: isMobileDevice(),
        screenSize: getScreenSize(),
        orientation: getOrientation()
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return deviceInfo;
}

// Использование
function MyComponent() {
  const { isMobile, screenSize, orientation } = useDeviceInfo();
  
  return (
    <div>
      {isMobile ? 'Mobile' : 'Desktop'}
      {screenSize} - {orientation}
    </div>
  );
}
```

---

### 3. Feature Detection vs Device Detection

```javascript
// ✅ Предпочитайте feature detection
if (hasCamera()) {
  // Показать кнопку камеры
}

// ❌ Избегайте device detection для features
if (isIOS() || isAndroid()) {
  // Может не работать на новых устройствах
}
```

---

## 📊 Browser Support

Все функции работают в:
- ✅ Chrome/Edge (последние версии)
- ✅ Firefox (последние версии)
- ✅ Safari (iOS 12+)
- ✅ Chrome Mobile (Android 5+)

---

## 🧪 Testing

```javascript
// Mock для тестов
jest.mock('./utils/deviceDetection', () => ({
  isMobileDevice: jest.fn(() => false),
  hasCamera: jest.fn(() => true),
  getDeviceType: jest.fn(() => 'desktop')
}));

test('shows desktop layout', () => {
  const { isMobileDevice } = require('./utils/deviceDetection');
  isMobileDevice.mockReturnValue(false);
  
  render(<App />);
  expect(screen.getByTestId('desktop-layout')).toBeInTheDocument();
});
```

---

## 📝 Changelog

### v2.25.0
- ✨ Добавлен `deviceDetection.js` (121 строка)
- 🎯 11 утилит для определения устройства
- 📱 Полная поддержка mobile detection
- 🔧 Helpers для PWA и вибрации

---

## 🔗 Related

- Mobile Components: `/components/mobile/`
- Responsive Design: `MOBILE_OPTIMIZATION_v2.17.md`
- PWA Configuration: `public/manifest.json`

