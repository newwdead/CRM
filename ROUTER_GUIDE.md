# 🛣️ React Router Navigation Guide

## Обзор

**ibbase** теперь использует полноценную систему навигации с **React Router v6**, обеспечивающую современный UX и все преимущества SPA-приложений.

---

## 🎯 Что реализовано

### ✅ 1. React Router v6
- Полноценная клиентская навигация
- URL меняются при переходах
- Работают кнопки Назад/Вперед браузера
- Поддержка прямых ссылок на любую страницу

### ✅ 2. Protected Routes
- Автоматическая защита всех страниц
- Редирект на `/login` для неавторизованных
- Защита админских разделов (`requireAdmin`)
- Сохранение исходного URL для возврата после логина

### ✅ 3. Breadcrumbs (Хлебные крошки)
- Автоматическая навигационная цепочка
- Показывается на всех страницах (кроме главной и логина)
- Кликабельные элементы для быстрого перехода
- Поддержка русского и английского языков

### ✅ 4. Динамические заголовки страниц
- `document.title` меняется на каждой странице
- Формат: `"Название страницы - ibbase"`
- Видно в табах браузера
- Улучшает UX при многих открытых вкладках

### ✅ 5. Query Parameters для фильтров
```
/contacts?search=Иван&tag=клиент&page=2
/contacts?company=ООО+Рога&limit=50
```
- Закладки сохраняют фильтры
- Можно делиться ссылками с коллегами
- История поиска работает

### ✅ 6. Scroll Restoration
- Автоматическая прокрутка наверх при переходе
- Улучшает UX навигации
- Работает на всех страницах

### ✅ 7. 404 страница
- Красивая страница ошибки
- Анимированная иконка
- Кнопки возврата на главную и к контактам
- Поддержка обоих языков

### ✅ 8. Loading индикаторы
- Показываются при переходах между страницами
- Используют React Suspense
- Улучшают восприятие скорости

### ✅ 9. Deep Links для модалок
```
/contacts/123           → Редактирование контакта
/contacts/123?mode=ocr  → OCR редактор для контакта
```
- Прямые ссылки на действия
- Можно делиться с коллегами
- Работают закладки

### ✅ 10. SEO Meta-теги
- Open Graph для Facebook/VK
- Twitter Cards для Twitter/X
- Canonical URL
- Keywords и Description
- Поддержка русского и английского

### ✅ 11. Route Guards
- Проверка авторизации
- Проверка роли (admin/user)
- Автоматические редиректы
- Защита от несанкционированного доступа

---

## 📍 Карта маршрутов

### Публичные маршруты
```
/login → Страница входа
```

### Защищённые маршруты (требуют авторизации)
```
/                   → Главная (Dashboard)
/contacts           → Список контактов
/contacts/:id       → Просмотр/редактирование контакта
/contacts/:id?mode=ocr → OCR редактор контакта
/companies          → Организации
/duplicates         → Поиск дубликатов
/upload             → Загрузка визитки
/batch-upload       → Пакетная загрузка
/import-export      → Импорт/Экспорт
/settings           → Настройки
```

### Админские маршруты (требуют роль admin)
```
/admin              → Админ-панель
/admin/users        → Управление пользователями
/admin/integrations → Интеграции
/admin/services     → Сервисы
/admin/documentation → Документация
```

### Служебные маршруты
```
*                   → 404 Not Found
```

---

## 🏗️ Архитектура

### Структура файлов
```
frontend/src/
├── App.js                          → Главный файл с маршрутами
├── components/
│   ├── routing/
│   │   ├── ProtectedRoute.js      → Компонент защиты маршрутов
│   │   ├── MainLayout.js          → Общий макет (header, nav, footer)
│   │   ├── Breadcrumbs.js         → Хлебные крошки
│   │   ├── PageTitle.js           → Управление заголовками
│   │   └── NotFound.js            → Страница 404
│   ├── pages/
│   │   ├── HomePage.js            → Главная страница
│   │   ├── ContactsPage.js        → Страница списка контактов
│   │   └── ContactPage.js         → Страница контакта
│   └── ...                        → Остальные компоненты
└── translations.js                → Переводы
```

---

## 🔧 Как это работает

### 1. ProtectedRoute Component
```jsx
<ProtectedRoute requireAdmin={false}>
  <YourPage />
</ProtectedRoute>
```
- Проверяет наличие токена
- Проверяет роль (если `requireAdmin=true`)
- Редиректит на `/login` если не авторизован
- Редиректит на `/` если недостаточно прав

### 2. MainLayout Component
```jsx
<MainLayout lang={lang} toggleLanguage={...} onLogout={...}>
  {children}
</MainLayout>
```
- Оборачивает все защищённые страницы
- Содержит header с навигацией
- Breadcrumbs
- Footer
- SearchOverlay (Ctrl+K)

### 3. PageTitle Component
```jsx
<PageTitle title="Контакты" lang="ru" />
```
- Автоматически обновляет `document.title`
- Устанавливает meta description
- Работает на каждой странице

### 4. Breadcrumbs Component
```jsx
<Breadcrumbs lang={lang} contactName={contact?.name} />
```
- Автоматически парсит URL
- Генерирует цепочку навигации
- Пропускает технические параметры (UUID, ID)

---

## 🚀 Примеры использования

### Переход на страницу программно
```jsx
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();
navigate('/contacts');
navigate('/contacts/123');
navigate('/contacts/123?mode=ocr');
```

### Получение параметров URL
```jsx
import { useParams, useSearchParams } from 'react-router-dom';

const { id } = useParams(); // /contacts/:id
const [searchParams] = useSearchParams();
const mode = searchParams.get('mode'); // ?mode=ocr
```

### Создание ссылки
```jsx
import { Link } from 'react-router-dom';

<Link to="/contacts">Контакты</Link>
<Link to={`/contacts/${id}`}>Просмотр</Link>
<Link to={`/contacts/${id}?mode=ocr`}>OCR</Link>
```

### Проверка активного маршрута
```jsx
import { useLocation } from 'react-router-dom';

const location = useLocation();
const isActive = location.pathname === '/contacts';
```

---

## 📱 Deep Links

### Редактирование контакта
```
https://ibbase.ru/contacts/123
```
- Открывает контакт в режиме редактирования
- Можно сохранить в закладки
- Можно отправить коллеге

### OCR редактор
```
https://ibbase.ru/contacts/123?mode=ocr
```
- Открывает OCR редактор для визитки
- Позволяет исправлять распознанный текст
- Прямая ссылка на функцию

### Фильтрованный список
```
https://ibbase.ru/contacts?search=Иван&company=ООО
```
- Список с применёнными фильтрами
- Можно делиться с коллегами
- Сохраняется в истории браузера

---

## 🔍 SEO Оптимизация

### Meta-теги (index.html)
```html
<!-- Basic SEO -->
<meta name="description" content="..." />
<meta name="keywords" content="..." />

<!-- Open Graph (Facebook, VK) -->
<meta property="og:title" content="..." />
<meta property="og:description" content="..." />
<meta property="og:image" content="..." />

<!-- Twitter Cards -->
<meta name="twitter:card" content="..." />
<meta name="twitter:title" content="..." />

<!-- Canonical URL -->
<link rel="canonical" href="https://ibbase.ru/" />
```

### Динамические заголовки
- Каждая страница имеет уникальный `title`
- Формат: `"Название - ibbase"`
- Помогает поисковикам и пользователям

---

## ⚙️ Nginx конфигурация

### SPA Routing Support
```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```
- Все несуществующие пути отдаются на `index.html`
- React Router обрабатывает маршрутизацию
- **Уже настроено** ✅

---

## 🧪 Тестирование

### Ручное тестирование
1. ✅ Открыть https://ibbase.ru/
2. ✅ Войти в систему
3. ✅ Перейти по всем вкладкам меню
4. ✅ Проверить URL меняется
5. ✅ Нажать "Назад" - должно работать
6. ✅ Добавить страницу в закладки
7. ✅ Открыть закладку в новой вкладке
8. ✅ Перейти на `/contacts/123`
9. ✅ Перейти на `/unknown-page` → 404
10. ✅ Проверить breadcrumbs отображаются
11. ✅ Проверить заголовки вкладок

### Автоматическое тестирование
```bash
# Проверить билд
cd frontend && npm run build

# Проверить что нет ошибок
docker compose logs frontend
```

---

## 🐛 Troubleshooting

### Проблема: 404 при прямом переходе по URL
**Причина:** Nginx не настроен для SPA  
**Решение:** ✅ Уже исправлено в `nginx.conf`

### Проблема: URL не меняется
**Причина:** Используются обычные `<a>` вместо `<Link>`  
**Решение:** Заменить на `<Link to="...">` из `react-router-dom`

### Проблема: Состояние теряется при обновлении
**Причина:** Хранится в React state вместо localStorage  
**Решение:** Использовать localStorage или URL parameters

### Проблема: Breadcrumbs не показываются
**Причина:** Breadcrumbs скрыты на главной странице  
**Решение:** Это нормальное поведение

### Проблема: Защищённая страница доступна без входа
**Причина:** Не обёрнута в `<ProtectedRoute>`  
**Решение:** ✅ Все страницы защищены

---

## 📊 Производительность

### Bundle Size
```
Before (без роутинга): ~250 KB
After (с роутингом):   ~264 KB
Increase:              +14 KB (5.6%)
```
- Минимальное увеличение размера
- Оправдано функциональностью
- Gzip сжатие работает отлично

### Performance
- Переходы между страницами мгновенные
- Нет перезагрузки страницы
- Отличный UX

---

## 🎓 Best Practices

### 1. Всегда используйте Link
```jsx
// ❌ Плохо
<a href="/contacts">Контакты</a>

// ✅ Хорошо
<Link to="/contacts">Контакты</Link>
```

### 2. Используйте navigate для программных переходов
```jsx
// ❌ Плохо
window.location.href = '/contacts';

// ✅ Хорошо
navigate('/contacts');
```

### 3. Добавляйте PageTitle на каждую страницу
```jsx
<PageTitle title="My Page" lang={lang} />
```

### 4. Используйте query параметры для фильтров
```jsx
// ✅ Хорошо - сохраняется в URL
?search=John&tag=client

// ❌ Плохо - только в state
const [search, setSearch] = useState('');
```

### 5. Проверяйте права доступа
```jsx
// Для админских страниц
<ProtectedRoute requireAdmin={true}>
  <AdminPage />
</ProtectedRoute>
```

---

## 📚 Дополнительные ресурсы

- [React Router Documentation](https://reactrouter.com/)
- [SPA Best Practices](https://web.dev/spa/)
- [SEO for SPA](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)

---

## ✅ Checklist для новой страницы

При добавлении новой страницы:

- [ ] Создать компонент страницы в `components/pages/`
- [ ] Добавить маршрут в `App.js`
- [ ] Обернуть в `<ProtectedRoute>` если нужна авторизация
- [ ] Добавить `<PageTitle>` для заголовка
- [ ] Добавить перевод в `translations.js`
- [ ] Обновить breadcrumbs names если нужно
- [ ] Добавить пункт в навигацию (MainLayout.js)
- [ ] Протестировать прямой переход по URL
- [ ] Проверить работу кнопки "Назад"

---

## 🎉 Результат

✅ **Профессиональная навигация**  
✅ **SEO-friendly структура**  
✅ **Отличный UX**  
✅ **Закладки работают**  
✅ **История навигации**  
✅ **Прямые ссылки**  
✅ **Query параметры для фильтров**  
✅ **Breadcrumbs навигация**  
✅ **Динамические заголовки**  
✅ **404 страница**  
✅ **Deep links для всех функций**  

---

**Теперь ibbase - это современное SPA-приложение с полноценной навигацией! 🚀**

