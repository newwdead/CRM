# UX Issues Found in v4.8.0 - User Testing Results

**Date:** October 24, 2025  
**Version:** v4.8.0  
**Tester:** User  
**Total Issues:** 14 (18 sub-issues)  

---

## 🔴 P1: Critical Issues (4)

### Issue #2: Админ панель - горизонтальное меню не работает
**URL:** https://ibbase.ru/admin?tab=backups  
**Problem:** При переходе на вкладку через dropdown (например, backups), горизонтальное меню перестает работать. Переключение на другие вкладки (settings, users) невозможно. Работает только при заходе на /admin.  
**Impact:** HIGH - блокирует навигацию  
**Root Cause:** URL параметр не синхронизируется с activeTab после первого рендера  
**Fix:** useEffect должен отслеживать изменения searchParams  

### Issue #5: Управление Сервисами - кнопки не работают
**URL:** https://ibbase.ru/admin?tab=services  
**Problem:** Кнопки "Подробности" не открывают детали сервиса  
**Impact:** HIGH - функция не работает  
**Root Cause:** Возможно, onClick handler не привязан или логика не реализована  

### Issue #9: OCR editor - повторный запуск OCR
**URL:** https://ibbase.ru/contacts/4/ocr-editor  
**Problem:** При изменении блоков (resize, split, new) повторный запуск OCR должен распознать текст согласно новым блокам и показать привязку полей  
**Impact:** HIGH - основная функция не работает правильно  
**Current:** OCR запускается на всем изображении  
**Expected:** OCR должен запускаться на каждом блоке отдельно  

### Issue #14: OCR editor - дублирование значений
**URL:** https://ibbase.ru/contacts/4/ocr-editor  
**Problem:** При сохранении привязки полей, значение появляется в новом поле, но остается в старом  
**Impact:** HIGH - данные дублируются  
**Expected:** 
- Убрать из старого поля при переносе
- Показать страницу подтверждения изменений
- Подсветить что будет удалено (красный) и заменено (желтый)

---

## 🟡 P2: High Priority UX Issues (7)

### Issue #1: Верхнее меню - разный формат
**Problem:** Основное меню (Главная, Контакты, Организации, Настройки) отличается форматом от dropdown меню (Действия, Админ панель)  
**Impact:** MEDIUM - визуальная несогласованность  
**Fix:** Унифицировать стиль всех пунктов меню  

### Issue #3: Интеграции Системы - проверка
**URL:** https://ibbase.ru/admin?tab=settings  
**Problem:** Нужно проверить наличие всех систем и пересмотреть отображение  
**Action:** Audit всех интеграций  

### Issue #4: System Resources - Grafana ссылка
**URL:** https://ibbase.ru/admin?tab=resources  
**Problem:** Grafana пытается открыть https://ibbase.ru:3001/ но не удается  
**Impact:** MEDIUM - мониторинг недоступен  
**Fix:** Проверить правильный URL Grafana (возможно :3000 или другой host)  

### Issue #6: Telegram интеграция - настройки
**URL:** https://ibbase.ru/admin?tab=settings > Telegram  
**Problem:** Меню настроек неправильное, попытки подключения не получились  
**Impact:** MEDIUM - интеграция не работает  
**Action:** Проверить поля настроек Telegram  

### Issue #8: Меню на английском
**Problem:** Часть меню отображается на английском языке  
**Impact:** MEDIUM - несогласованность языка  
**Fix:** Перевести все меню на русский  

### Issue #10: Язык интерфейса в /settings
**URL:** https://ibbase.ru/settings  
**Problem:** Поле "Язык интерфейса" не работает, работает только кнопка в header  
**Impact:** MEDIUM - вводит в заблуждение  
**Fix:** Убрать блок "Язык интерфейса" из настроек  

### Issue #11: Верхний блок неинформативен
**Problem:** Header с названием сайта, "Добро пожаловать" и кнопкой выхода выглядит некрасиво и неинформативно  
**Impact:** MEDIUM - первое впечатление  
**Fix:** Переделать header, сделать более информативным и стильным  

---

## 🟢 P3: Medium Priority Improvements (7)

### Issue #4.1: Telegram Bot дублируется
**URL:** https://ibbase.ru/admin?tab=resources  
**Problem:** Telegram Bot есть в Resources и в Интеграциях (дублирование)  
**Fix:** Убрать из Resources, оставить только в Интеграциях  

### Issue #7: Аутентификация - непонятно
**URL:** https://ibbase.ru/admin?tab=settings > Аутентификация  
**Problem:** Непонятно что делать и как это работает  
**Impact:** LOW - UX улучшение  
**Fix:** Добавить help (!) во всех модулях с объяснением  

### Issue #9.1: OCR - несколько блоков в одно поле
**URL:** https://ibbase.ru/contacts/4/ocr-editor  
**Problem:** Если текст распознан несколькими блоками, но является одним предложением, должна быть возможность выбора очередности блоков  
**Expected:** Весь текст попадает в одно поле в правильном порядке  

### Issue #9.2: OCR - две кнопки "Сохранить"
**URL:** https://ibbase.ru/contacts/4/ocr-editor  
**Problem:** На странице две кнопки "Сохранить", непонятно зачем  
**Fix:** Убрать дубль, оставить одну кнопку  

### Issue #12: Keyboard Shortcuts - нет отключения
**Problem:** ⌨️ Keyboard Shortcuts показывается, но нет способа отключить  
**Fix:** Добавить кнопку закрытия или настройку "Показывать подсказки"  

### Issue #13: Контакты - лишние функции
**URL:** https://ibbase.ru/contacts  
**Problem:** Возможность растягивать поля мышкой и кнопка "Выбрать все" не нужны  
**Fix:** Убрать растягивание колонок и кнопку "Выбрать все"  

### Issue #18: OCR - страница подтверждения
**URL:** https://ibbase.ru/contacts/4/ocr-editor  
**Problem:** При сохранении изменений нет страницы подтверждения  
**Expected:** 
- Показать что будет изменено
- Подсветить удаления (красный) и замены (желтый)
- Кнопки "Применить" / "Отмена"

---

## 📊 SUMMARY

**By Priority:**
- 🔴 P1 Critical: 4 issues (need immediate fix)
- 🟡 P2 High: 7 issues (important UX)
- 🟢 P3 Medium: 7 issues (improvements)

**By Category:**
- Navigation/Menu: 5 issues (#1, #2, #8, #11, #12)
- Admin Panel: 7 issues (#2, #3, #4, #4.1, #5, #6, #7)
- OCR Editor: 5 issues (#9, #9.1, #9.2, #14, #18)
- Settings: 1 issue (#10)
- Contacts: 1 issue (#13)

**Estimated Time:**
- P1 Critical: 3-4 hours
- P2 High: 2-3 hours
- P3 Medium: 2-3 hours
- **Total: 7-10 hours**

---

## 🎯 RECOMMENDED APPROACH

### Phase 1: Critical Fixes (3-4 hours)
1. Fix Issue #2: Admin panel navigation
2. Fix Issue #5: Services buttons
3. Fix Issue #9: OCR re-recognition with blocks
4. Fix Issue #14: OCR field duplication

### Phase 2: High Priority UX (2-3 hours)
5. Fix Issue #1: Menu uniformity
6. Fix Issue #3, #6: Integrations audit
7. Fix Issue #4: Grafana link
8. Fix Issue #8, #11: Language & header
9. Fix Issue #10: Remove language from settings

### Phase 3: Improvements (2-3 hours)
10. Fix Issue #4.1, #9.2, #12, #13: Small fixes
11. Fix Issue #7, #9.1, #18: Advanced features

---

**Next Steps:** Start with Phase 1 - Critical Fixes
