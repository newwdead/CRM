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
 * v4.6.0: Fixed URL navigation + modernized with CSS classes
 * Replaced 100+ lines of inline styles with admin-tabs.css
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

  const tabs = [
    { id: 'users', icon: '👥', label: 'Users' },
    { id: 'settings', icon: '🔌', label: 'Integrations' },
    { id: 'backups', icon: '💾', label: 'Backups' },
    { id: 'resources', icon: '🔗', label: 'Resources' },
    { id: 'services', icon: '🔧', label: 'Services' },
    { id: 'duplicates', icon: '🔍', label: 'Duplicates' },
    { id: 'documentation', icon: '📚', label: 'Docs' }
  ];

  return (
    <div className="modern-page">
      {/* Header */}
      <div className="modern-page-header">
        <h1 className="modern-page-title">
          ⚙️ Admin Panel
        </h1>
        <p className="modern-page-subtitle">
          System administration and configuration
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="admin-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="admin-tab-content">
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
