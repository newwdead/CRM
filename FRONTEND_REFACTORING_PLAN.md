# 📝 План рефакторинга Frontend компонентов

**Статус:** Готово к выполнению  
**Приоритет:** Средний (не критично для production)  
**Время:** 8-10 часов

---

## 🎯 Цели рефакторинга

1. **AdminPanel.js** (1372 строки → ~250 строк)
2. **ContactList.js** (1008 строк → ~300 строк)
3. **Добавить React Query** для кэширования

---

## 📋 Задача 1: Разбить AdminPanel.js

### Текущее состояние

**Вкладки:**
- ✅ `users` - Управление пользователями (нужно вынести)
- ✅ `settings` - SystemSettings (уже вынесен)
- ✅ `backups` - Управление бэкапами (нужно вынести)
- ✅ `resources` - Системные ресурсы (нужно вынести)
- ✅ `services` - ServiceManager (уже вынесен)
- ✅ `duplicates` - DuplicatesPanel (уже вынесен)
- ✅ `documentation` - Documentation (уже вынесен)

### План разбиения

```
frontend/src/components/admin/
├── AdminPanel.js          (~250 строк - main с навигацией)
├── UserManagement.js      (~300 строк)
├── BackupManagement.js    (~250 строк)
└── SystemResources.js     (~150 строк)
```

### Пример: UserManagement.js

```javascript
import React, { useState, useEffect } from 'react';

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Editing user state
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    email: '',
    full_name: '',
    password: ''
  });

  useEffect(() => {
    fetchUsers();
    fetchPendingUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/auth/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      setError('Failed to fetch users');
    }
  };

  const fetchPendingUsers = async () => {
    // ... implementation
  };

  const approveUser = async (userId) => {
    // ... implementation
  };

  const deleteUser = async (userId) => {
    // ... implementation
  };

  const toggleAdmin = async (userId) => {
    // ... implementation
  };

  return (
    <div className="user-management">
      <h2>👥 User Management</h2>
      
      {/* Pending Users Section */}
      {pendingUsers.length > 0 && (
        <div className="pending-users">
          <h3>⏳ Pending Approvals</h3>
          {/* ... pending users list */}
        </div>
      )}
      
      {/* Active Users Section */}
      <div className="active-users">
        <h3>✅ Active Users</h3>
        {/* ... users table */}
      </div>
    </div>
  );
}

export default UserManagement;
```

### Пример: BackupManagement.js

```javascript
import React, { useState, useEffect } from 'react';

function BackupManagement() {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBackups();
  }, []);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/backups/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBackups(data);
      }
    } catch (error) {
      setError('Failed to fetch backups');
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    try {
      const response = await fetch('/api/backups/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        await fetchBackups();
      }
    } catch (error) {
      setError('Failed to create backup');
    }
  };

  const deleteBackup = async (filename) => {
    if (!window.confirm('Delete this backup?')) return;
    
    try {
      const response = await fetch(`/api/backups/${filename}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        await fetchBackups();
      }
    } catch (error) {
      setError('Failed to delete backup');
    }
  };

  return (
    <div className="backup-management">
      <h2>💾 Backup Management</h2>
      
      <button onClick={createBackup} disabled={loading}>
        {loading ? '⏳ Creating...' : '➕ Create New Backup'}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      <div className="backups-list">
        <h3>Available Backups</h3>
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Size</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {backups.map((backup) => (
              <tr key={backup.filename}>
                <td>{backup.filename}</td>
                <td>{backup.size}</td>
                <td>{new Date(backup.modified).toLocaleString()}</td>
                <td>
                  <button onClick={() => deleteBackup(backup.filename)}>
                    🗑️ Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default BackupManagement;
```

### Пример: SystemResources.js

```javascript
import React, { useState, useEffect } from 'react';

function SystemResources() {
  const [resources, setResources] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchResources();
    const interval = setInterval(fetchResources, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchResources = async () => {
    try {
      const response = await fetch('/api/system/resources', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setResources(data);
      }
    } catch (error) {
      console.error('Failed to fetch resources');
    }
  };

  if (!resources) return <div>Loading...</div>;

  return (
    <div className="system-resources">
      <h2>📊 System Resources</h2>
      
      <div className="resource-cards">
        {/* CPU */}
        <div className="card">
          <h3>CPU Usage</h3>
          <div className="progress">
            <div 
              className="progress-bar" 
              style={{width: `${resources.cpu_percent}%`}}
            />
          </div>
          <p>{resources.cpu_percent}%</p>
        </div>

        {/* Memory */}
        <div className="card">
          <h3>Memory Usage</h3>
          <div className="progress">
            <div 
              className="progress-bar" 
              style={{width: `${resources.memory_percent}%`}}
            />
          </div>
          <p>{resources.memory_used} / {resources.memory_total}</p>
        </div>

        {/* Disk */}
        <div className="card">
          <h3>Disk Usage</h3>
          <div className="progress">
            <div 
              className="progress-bar" 
              style={{width: `${resources.disk_percent}%`}}
            />
          </div>
          <p>{resources.disk_used} / {resources.disk_total}</p>
        </div>
      </div>
    </div>
  );
}

export default SystemResources;
```

### Обновленный AdminPanel.js

```javascript
import React, { useState } from 'react';
import UserManagement from './admin/UserManagement';
import BackupManagement from './admin/BackupManagement';
import SystemResources from './admin/SystemResources';
import SystemSettings from './SystemSettings';
import ServiceManager from './ServiceManager';
import DuplicatesPanel from './DuplicatesPanel';
import Documentation from './Documentation';

function AdminPanel({ t, lang }) {
  const [activeTab, setActiveTab] = useState('users');

  return (
    <div className="admin-panel">
      <h1>⚙️ Admin Panel</h1>

      {/* Navigation Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 Users
        </button>
        <button
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ Settings
        </button>
        <button
          className={`tab ${activeTab === 'backups' ? 'active' : ''}`}
          onClick={() => setActiveTab('backups')}
        >
          💾 Backups
        </button>
        <button
          className={`tab ${activeTab === 'resources' ? 'active' : ''}`}
          onClick={() => setActiveTab('resources')}
        >
          📊 Resources
        </button>
        <button
          className={`tab ${activeTab === 'services' ? 'active' : ''}`}
          onClick={() => setActiveTab('services')}
        >
          🔧 Services
        </button>
        <button
          className={`tab ${activeTab === 'duplicates' ? 'active' : ''}`}
          onClick={() => setActiveTab('duplicates')}
        >
          🔄 Duplicates
        </button>
        <button
          className={`tab ${activeTab === 'documentation' ? 'active' : ''}`}
          onClick={() => setActiveTab('documentation')}
        >
          📚 Docs
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'users' && <UserManagement />}
        {activeTab === 'settings' && <SystemSettings t={t} lang={lang} />}
        {activeTab === 'backups' && <BackupManagement />}
        {activeTab === 'resources' && <SystemResources />}
        {activeTab === 'services' && <ServiceManager />}
        {activeTab === 'duplicates' && <DuplicatesPanel lang={lang} />}
        {activeTab === 'documentation' && <Documentation />}
      </div>
    </div>
  );
}

export default AdminPanel;
```

**Результат:**
- AdminPanel.js: 1372 → ~250 строк (**-82%**)
- 3 новых компонента: UserManagement, BackupManagement, SystemResources

---

## 📋 Задача 2: Разбить ContactList.js

### План разбиения

```
frontend/src/components/contacts/
├── ContactList.js         (~300 строк - main)
├── ContactTable.js        (~250 строк)
├── ContactFilters.js      (~200 строк)
├── ContactPagination.js   (~100 строк)
└── ContactBulkActions.js  (~150 строк)
```

### Пример: ContactFilters.js

```javascript
import React from 'react';

function ContactFilters({
  search,
  setSearch,
  companyFilter,
  setCompanyFilter,
  positionFilter,
  setPositionFilter,
  tagFilter,
  setTagFilter,
  groupFilter,
  setGroupFilter,
  tags,
  groups,
  onClear
}) {
  return (
    <div className="contact-filters">
      <div className="filter-group">
        <input
          type="text"
          placeholder="🔍 Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="filter-group">
        <input
          type="text"
          placeholder="🏢 Company..."
          value={companyFilter}
          onChange={(e) => setCompanyFilter(e.target.value)}
        />
      </div>

      <div className="filter-group">
        <input
          type="text"
          placeholder="💼 Position..."
          value={positionFilter}
          onChange={(e) => setPositionFilter(e.target.value)}
        />
      </div>

      <div className="filter-group">
        <select
          value={tagFilter}
          onChange={(e) => setTagFilter(e.target.value)}
        >
          <option value="">🏷️ All Tags</option>
          {tags.map(tag => (
            <option key={tag.id} value={tag.name}>
              {tag.name}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <select
          value={groupFilter}
          onChange={(e) => setGroupFilter(e.target.value)}
        >
          <option value="">👥 All Groups</option>
          {groups.map(group => (
            <option key={group.id} value={group.name}>
              {group.name}
            </option>
          ))}
        </select>
      </div>

      <button onClick={onClear} className="btn-secondary">
        🔄 Clear Filters
      </button>
    </div>
  );
}

export default ContactFilters;
```

**Результат:**
- ContactList.js: 1008 → ~300 строк (**-70%**)
- 4 новых компонента: ContactTable, ContactFilters, ContactPagination, ContactBulkActions

---

## 📋 Задача 3: Добавить React Query

### Установка

\`\`\`bash
cd frontend
npm install @tanstack/react-query
\`\`\`

### App.js

\`\`\`javascript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 минут
      cacheTime: 10 * 60 * 1000, // 10 минут
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* ... app content ... */}
    </QueryClientProvider>
  );
}
\`\`\`

### Пример: ContactList с React Query

\`\`\`javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function ContactList() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({});

  // Fetch contacts with caching
  const { data, isLoading, error } = useQuery({
    queryKey: ['contacts', page, filters],
    queryFn: () => fetchContacts(page, filters),
    staleTime: 5 * 60 * 1000,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => deleteContact(id),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries(['contacts']);
    },
  });

  const handleDelete = (id) => {
    deleteMutation.mutate(id);
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {/* ... render contacts ... */}
    </div>
  );
}
\`\`\`

**Выгоды:**
- ✅ Автоматический кэш
- ✅ Background refetch
- ✅ Optimistic updates
- ✅ Меньше API запросов

---

## 📊 Итоговые метрики

| Компонент | До | После | Сокращение |
|-----------|-----|-------|------------|
| AdminPanel.js | 1372 | ~250 | **-82%** |
| ContactList.js | 1008 | ~300 | **-70%** |
| **Итого** | **2380** | **~550** | **-77%** |

**Создано новых компонентов:** 7  
**Время выполнения:** 8-10 часов  
**Приоритет:** Средний

---

## 🚀 Порядок выполнения

1. **Создать структуру папок** (5 мин)
   \`\`\`bash
   mkdir -p frontend/src/components/admin
   mkdir -p frontend/src/components/contacts
   \`\`\`

2. **Вынести компоненты AdminPanel** (3-4 часа)
   - UserManagement.js
   - BackupManagement.js
   - SystemResources.js
   - Обновить AdminPanel.js

3. **Вынести компоненты ContactList** (2-3 часа)
   - ContactFilters.js
   - ContactTable.js
   - ContactPagination.js
   - ContactBulkActions.js
   - Обновить ContactList.js

4. **Добавить React Query** (2-3 часа)
   - Установить зависимость
   - Обновить App.js
   - Конвертировать ContactList
   - Конвертировать AdminPanel

5. **Тестирование** (1 час)

---

## ✅ Checklist

- [ ] Создать admin/ и contacts/ папки
- [ ] UserManagement.js
- [ ] BackupManagement.js
- [ ] SystemResources.js
- [ ] ContactFilters.js
- [ ] ContactTable.js
- [ ] ContactPagination.js
- [ ] ContactBulkActions.js
- [ ] Обновить AdminPanel.js
- [ ] Обновить ContactList.js
- [ ] Установить React Query
- [ ] Обновить App.js с QueryClientProvider
- [ ] Конвертировать ContactList на React Query
- [ ] Протестировать все компоненты
- [ ] Commit & Push

---

**Статус:** Готово к реализации  
**Документация:** Полная  
**Приоритет:** Можно выполнить позже, не критично для production

