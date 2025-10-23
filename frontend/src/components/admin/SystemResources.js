import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

/**
 * System Resources Component
 * Displays system services, URLs, and environment information with configuration options
 */
function SystemResources() {
  const [resources, setResources] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [serviceConfig, setServiceConfig] = useState({});

  useEffect(() => {
    fetchResources();
  }, []);

  const fetchResources = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/system/resources', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setResources(data);
        // Load saved configurations from localStorage
        const savedConfig = localStorage.getItem('service_config');
        if (savedConfig) {
          setServiceConfig(JSON.parse(savedConfig));
        }
      }
    } catch (error) {
      console.error('Error fetching resources:', error);
      toast.error('Не удалось загрузить ресурсы');
    } finally {
      setLoading(false);
    }
  };

  const handleEditService = (key, service) => {
    setEditingService(key);
    setServiceConfig(prev => ({
      ...prev,
      [key]: {
        name: service.name,
        description: service.description,
        url: service.url || '',
        local_url: service.local_url || '',
        status: service.status
      }
    }));
  };

  const handleSaveService = (key) => {
    // Save to localStorage
    const updatedConfig = { ...serviceConfig };
    localStorage.setItem('service_config', JSON.stringify(updatedConfig));
    
    // Update resources state with new configuration
    if (resources && resources.services) {
      const updatedServices = { ...resources.services };
      if (serviceConfig[key]) {
        updatedServices[key] = {
          ...updatedServices[key],
          ...serviceConfig[key]
        };
      }
      setResources({ ...resources, services: updatedServices });
    }
    
    setEditingService(null);
    toast.success('Настройки сохранены');
  };

  const handleCancelEdit = () => {
    setEditingService(null);
  };

  const handleConfigChange = (key, field, value) => {
    setServiceConfig(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: value
      }
    }));
  };

  const testServiceConnection = async (serviceKey, url) => {
    if (!url) {
      toast.error('URL не указан');
      return;
    }
    
    toast.loading('Проверка соединения...');
    try {
      const response = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
      toast.dismiss();
      toast.success(`${serviceKey}: Соединение установлено`);
    } catch (error) {
      toast.dismiss();
      toast.error(`${serviceKey}: Не удалось подключиться`);
    }
  };

  return (
    <div className="system-resources">
      <h3>🔗 System Resources & Links</h3>
      <p style={{ marginBottom: '20px', color: '#666' }}>
        Quick access to all deployed services and monitoring dashboards
      </p>

      {loading && <p>Loading resources...</p>}

      {resources && resources.services ? (
        <div className="resources-grid" style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', 
          gap: '20px',
          marginTop: '20px'
        }}>
          {Object.entries(resources.services).map(([key, service]) => {
            const isEditing = editingService === key;
            const currentConfig = serviceConfig[key] || service;
            
            return (
              <div key={key} className="resource-card" style={{
                border: isEditing ? '2px solid #4CAF50' : '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '20px',
                backgroundColor: isEditing ? '#f0f9f0' : '#f9f9f9',
                transition: 'all 0.3s'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <h4 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isEditing ? (
                      <input 
                        type="text"
                        value={currentConfig.name}
                        onChange={(e) => handleConfigChange(key, 'name', e.target.value)}
                        style={{ 
                          fontSize: '1em', 
                          fontWeight: 'bold',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          width: '100%'
                        }}
                      />
                    ) : (
                      service.name
                    )}
                  </h4>
                  {!isEditing && (
                    <button
                      onClick={() => handleEditService(key, service)}
                      style={{
                        padding: '4px 10px',
                        fontSize: '12px',
                        backgroundColor: '#2196F3',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                      title="Настроить"
                    >
                      ⚙️
                    </button>
                  )}
                </div>
                
                {isEditing ? (
                  <textarea
                    value={currentConfig.description}
                    onChange={(e) => handleConfigChange(key, 'description', e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: '60px',
                      fontSize: '0.9em',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      marginBottom: '15px',
                      resize: 'vertical'
                    }}
                  />
                ) : (
                  <p style={{ color: '#666', fontSize: '0.9em', marginBottom: '15px' }}>
                    {service.description}
                  </p>
                )}
                
                {service.url || isEditing ? (
                  <div style={{ marginBottom: '10px' }}>
                    <strong style={{ fontSize: '0.85em', color: '#666' }}>Production URL:</strong>
                    {isEditing ? (
                      <div style={{ display: 'flex', gap: '5px', marginTop: '5px' }}>
                        <input
                          type="text"
                          value={currentConfig.url}
                          onChange={(e) => handleConfigChange(key, 'url', e.target.value)}
                          placeholder="https://example.com"
                          style={{
                            flex: 1,
                            padding: '6px',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontSize: '0.85em'
                          }}
                        />
                        <button
                          onClick={() => testServiceConnection(key, currentConfig.url)}
                          style={{
                            padding: '6px 12px',
                            fontSize: '12px',
                            backgroundColor: '#FF9800',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                          title="Проверить соединение"
                        >
                          🔍
                        </button>
                      </div>
                    ) : service.url ? (
                      <div>
                        <a 
                          href={service.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ 
                            marginTop: '5px',
                            display: 'inline-block',
                            padding: '6px 12px',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            textDecoration: 'none',
                            borderRadius: '4px',
                            fontSize: '0.85em'
                          }}
                        >
                          🌐 Open {service.name}
                        </a>
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div style={{ marginBottom: '10px' }}>
                    <span style={{ 
                      display: 'inline-block',
                      padding: '4px 8px',
                      backgroundColor: '#999',
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '0.8em'
                    }}>
                      Internal Only
                    </span>
                  </div>
                )}

                <div>
                  <strong style={{ fontSize: '0.85em', color: '#666' }}>Local URL:</strong>
                  {isEditing ? (
                    <input
                      type="text"
                      value={currentConfig.local_url}
                      onChange={(e) => handleConfigChange(key, 'local_url', e.target.value)}
                      placeholder="http://localhost:8000"
                      style={{
                        width: '100%',
                        marginTop: '5px',
                        padding: '8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.85em',
                        fontFamily: 'monospace'
                      }}
                    />
                  ) : (
                    <div>
                      <code style={{ 
                        display: 'block', 
                        padding: '8px', 
                        backgroundColor: '#fff', 
                        borderRadius: '4px',
                        fontSize: '0.85em',
                        marginTop: '5px',
                        border: '1px solid #ddd'
                      }}>
                        {service.local_url}
                      </code>
                    </div>
                  )}
                </div>

                {isEditing && (
                  <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
                    <button
                      onClick={() => handleSaveService(key)}
                      style={{
                        flex: 1,
                        padding: '8px',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: 'bold'
                      }}
                    >
                      ✅ Сохранить
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      style={{
                        flex: 1,
                        padding: '8px',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: 'bold'
                      }}
                    >
                      ❌ Отмена
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <p>Failed to load resources</p>
      )}

      {resources && resources.environment && (
        <div className="alert info" style={{ marginTop: '30px' }}>
          <h4 style={{ marginTop: 0 }}>🌍 Environment Info</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            <div>
              <strong>Domain:</strong> <code>{resources.environment.domain}</code>
            </div>
            <div>
              <strong>Protocol:</strong> <code>{resources.environment.protocol}</code>
            </div>
            <div>
              <strong>Server:</strong> <code>{resources.environment.server_host}</code>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SystemResources;

