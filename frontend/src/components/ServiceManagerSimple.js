import React, { useState, useEffect } from 'react';

/**
 * Simple Service Manager - Minimal version that actually works
 * Replaces the complex ServiceManager that keeps failing
 */
const ServiceManagerSimple = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      const response = await fetch('/services/status', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Services data:', data);
      
      setServices(data.services || []);
      
    } catch (err) {
      console.error('Error fetching services:', err);
      setError(err.message || 'Failed to load services');
      setServices([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
        <p>Loading services...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px', color: '#ef4444' }}>⚠️</div>
        <h3 style={{ color: '#ef4444' }}>Error Loading Services</h3>
        <p style={{ color: '#666', marginBottom: '20px' }}>{error}</p>
        <button
          onClick={fetchServices}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          🔄 Try Again
        </button>
      </div>
    );
  }

  if (services.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>📭</div>
        <h3>No Services Found</h3>
        <p style={{ color: '#666' }}>Docker services are not available or not configured</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0 }}>🔧 Service Management</h2>
        <button
          onClick={fetchServices}
          style={{
            padding: '8px 16px',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          🔄 Refresh
        </button>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
        gap: '16px' 
      }}>
        {services.map((service, idx) => (
          <div
            key={idx}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '16px',
              backgroundColor: '#f9fafb'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>
                {service.name || service.Service || 'Unknown'}
              </h3>
              <span
                style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: '600',
                  backgroundColor: service.state === 'running' ? '#dcfce7' : '#fee2e2',
                  color: service.state === 'running' ? '#166534' : '#991b1b'
                }}
              >
                {service.state || service.State || 'unknown'}
              </span>
            </div>
            
            {service.category && (
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                Category: {service.category}
              </div>
            )}
            
            {service.ports && (
              <div style={{ fontSize: '12px', color: '#666' }}>
                Ports: {service.ports}
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ 
        marginTop: '20px', 
        padding: '12px', 
        backgroundColor: '#f3f4f6', 
        borderRadius: '6px',
        fontSize: '14px',
        color: '#666'
      }}>
        Total Services: {services.length} | 
        Running: {services.filter(s => (s.state || s.State) === 'running').length}
      </div>
    </div>
  );
};

export default ServiceManagerSimple;

