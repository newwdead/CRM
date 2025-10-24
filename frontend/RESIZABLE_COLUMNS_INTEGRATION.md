# Resizable Columns Integration Guide

**Version:** v5.0.2  
**Component:** ContactList.js  
**Feature:** Drag-to-resize table columns  

---

## FILES CREATED

1. ✅ `/frontend/src/styles/resizable-table.css` - CSS styles
2. ✅ `/frontend/src/hooks/useResizableColumns.js` - React hook

---

## INTEGRATION STEPS

### Step 1: Import необходимые файлы

В `frontend/src/components/ContactList.js` добавьте импорты:

```javascript
// В начало файла, после существующих импортов
import useResizableColumns from '../hooks/useResizableColumns';
import '../styles/resizable-table.css';
```

### Step 2: Добавить hook в компонент

После существующих useState hooks:

```javascript
// После строки: const [tableColumns, setTableColumns] = useState(...)
const { handleMouseDown, isResizing } = useResizableColumns(tableColumns, setTableColumns);
```

### Step 3: Добавить className к table

Найдите `<table>` элемент и добавьте классы:

```javascript
<table className={`resizable-table ${isResizing ? 'is-resizing' : ''}`}>
```

### Step 4: Обновить table headers

В `<thead>` секции, для каждого `<th>`:

```javascript
<th 
  key={col.key}
  data-column-key={col.key}
  style={{ width: `${col.width}px` }}
>
  <div className="column-header-content">
    {col.label}
    {/* Sort indicator если есть */}
  </div>
  {/* Добавить resizer handle */}
  <div 
    className="column-resizer"
    onMouseDown={(e) => handleMouseDown(e, col.key)}
    onClick={(e) => e.stopPropagation()}
  />
</th>
```

---

## EXAMPLE: Полный Header Cell

```javascript
{visibleColumns.map(col => (
  <th 
    key={col.key}
    data-column-key={col.key}
    style={{ width: `${col.width}px` }}
    className={`
      ${sortBy === col.key ? 'sorted' : ''}
      ${col.key !== 'select' && col.key !== 'actions' ? 'sortable' : ''}
    `}
    onClick={() => {
      if (col.key !== 'select' && col.key !== 'actions') {
        handleSort(col.key);
      }
    }}
  >
    <div className="column-header-content">
      <span>{col.label}</span>
      {sortBy === col.key && (
        <span style={{ marginLeft: '4px' }}>
          {sortOrder === 'asc' ? '↑' : '↓'}
        </span>
      )}
    </div>
    
    {/* Resizer Handle */}
    <div 
      className="column-resizer"
      onMouseDown={(e) => handleMouseDown(e, col.key)}
      onClick={(e) => e.stopPropagation()}
    />
  </th>
))}
```

---

## FEATURES

✅ **Drag to resize** - Перетащите правый край колонки  
✅ **Auto-save** - Ширина сохраняется в localStorage  
✅ **Min/Max** - Min 40px, Max 800px  
✅ **Visual feedback** - Синяя полоска при наведении  
✅ **Smooth** - Плавное изменение размера  
✅ **Mobile** - Отключено на маленьких экранах  

---

## TESTING

1. Откройте https://ibbase.ru/contacts
2. Наведите курсор на правый край header cell
3. Увидите синюю полоску и курсор `col-resize`
4. Зажмите левую кнопку мыши и тяните влево/вправо
5. Отпустите - ширина сохранится
6. Перезагрузите страницу - ширина восстановится

---

## ALTERNATIVE: Быстрая интеграция через patch

Если не хотите вручную редактировать ContactList.js:

```bash
# Backup
cp frontend/src/components/ContactList.js frontend/src/components/ContactList.js.backup

# Apply automated patch (если создан)
# patch frontend/src/components/ContactList.js < resizable-columns.patch
```

---

## TROUBLESHOOTING

**Проблема:** Resize не работает  
**Решение:** Проверьте что hook импортирован и вызван

**Проблема:** Ширина не сохраняется  
**Решение:** Проверьте localStorage permissions в браузере

**Проблема:** Конфликт с сортировкой  
**Решение:** `onClick` на resizer должен иметь `e.stopPropagation()`

---

## NEXT STEPS

После интеграции:
1. ✅ Test на разных браузерах
2. ✅ Test на мобильных устройствах
3. ✅ Commit changes
4. ✅ Deploy v5.0.2

---

**Ready to integrate! 🚀**
