import React, { useState, useEffect } from 'react';

/**
 * System Resources Component
 * Displays system services, URLs, and environment information
 */
function SystemResources() {
  const [resources, setResources] = useState(null);
  const [loading, setLoading] = useState(false);

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
      }
    } catch (error) {
      console.error('Error fetching resources:', error);
    } finally {
      setLoading(false);
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
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '20px',
          marginTop: '20px'
        }}>
          {Object.entries(resources.services).map(([key, service]) => (
            <div key={key} className="resource-card" style={{
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '20px',
              backgroundColor: '#f9f9f9'
            }}>
              <h4 style={{ marginTop: 0, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                {service.name}
              </h4>
              <p style={{ color: '#666', fontSize: '0.9em', marginBottom: '15px' }}>
                {service.description}
              </p>
              
              {service.url ? (
                <div style={{ marginBottom: '10px' }}>
                  <strong style={{ fontSize: '0.85em', color: '#666' }}>Production URL:</strong>
                  <div>
                    <a 
                      href={service.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-primary btn-sm"
                      style={{ marginTop: '5px', display: 'inline-block' }}
                    >
                      🌐 Open {service.name}
                    </a>
                  </div>
                </div>
              ) : (
                <div style={{ marginBottom: '10px' }}>
                  <span className="badge badge-secondary" style={{ fontSize: '0.8em' }}>
                    Internal Only
                  </span>
                </div>
              )}

              <div>
                <strong style={{ fontSize: '0.85em', color: '#666' }}>Local URL:</strong>
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
              </div>
            </div>
          ))}
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

