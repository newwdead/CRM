import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import Documentation from './Documentation';
import { ServicesPanel } from '../modules/admin/services';
import SystemSettings from './SystemSettings';
import DuplicateFinder from './DuplicateFinder';
import UserManagement from './admin/UserManagement';
import BackupManagement from './admin/BackupManagement';
import SystemResources from './admin/SystemResources';

/**
 * Admin Panel - Main Admin Dashboard
 * Orchestrates all admin-related components
 * 
 * v4.6.0: Fixed URL navigation - now reads ?tab= parameter
 * Refactored from 1372 lines to 113 lines
 */
function AdminPanel({ t, lang }) {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'users');
  
  // Update active tab when URL changes
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab');
    if (tabFromUrl && tabFromUrl !== activeTab) {
      setActiveTab(tabFromUrl);
    }
  }, [searchParams, activeTab]);

  return (
    <div className="admin-panel" style={{ padding: '20px' }}>
      <div className="header" style={{ marginBottom: '30px' }}>
        <h1 style={{ margin: '0 0 10px 0', fontSize: '2em' }}>⚙️ Admin Panel</h1>
        <p style={{ color: '#666', margin: 0 }}>System administration and configuration</p>
      </div>

      {/* Navigation Tabs */}
      <div className="tabs" style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '20px',
        borderBottom: '2px solid #e0e0e0',
        flexWrap: 'wrap'
      }}>
        <button
          style={{
            background: activeTab === 'users' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'users' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'users' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'users' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('users')}
        >
          👥 Users
        </button>
        <button
          style={{
            background: activeTab === 'settings' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'settings' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'settings' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'settings' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('settings')}
        >
          🔌 Integrations
        </button>
        <button
          style={{
            background: activeTab === 'backups' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'backups' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'backups' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'backups' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('backups')}
        >
          💾 Backups
        </button>
        <button
          style={{
            background: activeTab === 'resources' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'resources' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'resources' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'resources' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('resources')}
        >
          🔗 Resources
        </button>
        <button
          style={{
            background: activeTab === 'services' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'services' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'services' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'services' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('services')}
        >
          🔧 Services
        </button>
        <button
          style={{
            background: activeTab === 'duplicates' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'duplicates' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'duplicates' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'duplicates' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('duplicates')}
        >
          🔍 Duplicates
        </button>
        <button
          style={{
            background: activeTab === 'documentation' ? '#f5f5f5' : 'none',
            border: 'none',
            padding: '12px 20px',
            cursor: 'pointer',
            fontSize: '1em',
            color: activeTab === 'documentation' ? '#2563eb' : '#666',
            borderBottom: activeTab === 'documentation' ? '3px solid #2563eb' : '3px solid transparent',
            fontWeight: activeTab === 'documentation' ? 600 : 'normal',
            transition: 'all 0.2s'
          }}
          onClick={() => setActiveTab('documentation')}
        >
          📚 Docs
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content" style={{
        background: 'white',
                  borderRadius: '8px',
                  padding: '20px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
      }}>
        {activeTab === 'users' && <UserManagement />}
        {activeTab === 'settings' && <SystemSettings lang={lang} />}
        {activeTab === 'backups' && <BackupManagement />}
        {activeTab === 'resources' && <SystemResources />}
        {activeTab === 'services' && <ServicesPanel language={lang} />}
        {activeTab === 'duplicates' && <DuplicateFinder lang={lang} />}
        {activeTab === 'documentation' && <Documentation lang={lang} />}
        </div>
    </div>
  );
}

export default AdminPanel;
