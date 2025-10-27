/**
 * Monitoring Dashboard Component
 * Real-time monitoring of OCR v2.0 services and business card processing
 * 
 * Features:
 * - Services status (Backend, Celery, MinIO, Redis, PostgreSQL, Label Studio)
 * - Celery queue status
 * - OCR processing stats (last 24h)
 * - Recent scans history
 * - System health indicators
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const MonitoringDashboard = ({ lang = 'ru' }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const translations = {
    en: {
      title: 'Monitoring Dashboard',
      subtitle: 'OCR v2.0 Services & Processing',
      refreshNow: 'Refresh Now',
      autoRefresh: 'Auto-refresh',
      lastUpdate: 'Last update',
      
      // Sections
      servicesStatus: 'Services Status',
      queueStatus: 'Celery Queue',
      ocrStats: 'OCR Processing (24h)',
      recentScans: 'Recent Scans',
      systemHealth: 'System Health',
      
      // Status
      healthy: 'Healthy',
      warning: 'Warning',
      error: 'Error',
      unknown: 'Unknown',
      
      // Queue
      activeTasks: 'Active Tasks',
      scheduledTasks: 'Scheduled',
      totalPending: 'Total Pending',
      workers: 'Workers',
      
      // OCR Stats
      totalScans: 'Total Scans',
      successRate: 'Success Rate',
      methods: 'Methods',
      
      // System Health
      cpu: 'CPU',
      memory: 'Memory',
      disk: 'Disk',
      
      // Recent Scans
      name: 'Name',
      company: 'Company',
      method: 'Method',
      time: 'Time',
      fields: 'Fields'
    },
    ru: {
      title: 'Панель Мониторинга',
      subtitle: 'OCR v2.0 Сервисы и Обработка',
      refreshNow: 'Обновить',
      autoRefresh: 'Авто-обновление',
      lastUpdate: 'Обновлено',
      
      // Sections
      servicesStatus: 'Статус Сервисов',
      queueStatus: 'Очередь Celery',
      ocrStats: 'Статистика OCR (24ч)',
      recentScans: 'Недавние Сканы',
      systemHealth: 'Здоровье Системы',
      
      // Status
      healthy: 'Работает',
      warning: 'Предупреждение',
      error: 'Ошибка',
      unknown: 'Неизвестно',
      
      // Queue
      activeTasks: 'Активные',
      scheduledTasks: 'Запланированные',
      totalPending: 'Всего в очереди',
      workers: 'Воркеры',
      
      // OCR Stats
      totalScans: 'Всего сканов',
      successRate: 'Успешность',
      methods: 'Методы',
      
      // System Health
      cpu: 'CPU',
      memory: 'Память',
      disk: 'Диск',
      
      // Recent Scans
      name: 'Имя',
      company: 'Компания',
      method: 'Метод',
      time: 'Время',
      fields: 'Полей'
    }
  };

  const t = translations[lang];

  useEffect(() => {
    fetchData();
    
    // Auto-refresh every 10 seconds
    if (autoRefresh) {
      const interval = setInterval(fetchData, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/monitoring/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch monitoring data');

      const result = await response.json();
      setData(result);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      toast.error('Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy': return '#28a745';
      case 'operational': return '#28a745';
      case 'warning': return '#ffc107';
      case 'error': return '#dc3545';
      case 'critical': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy': return '✅';
      case 'operational': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'critical': return '🔴';
      default: return '❓';
    }
  };

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    return `${Math.floor(diffMins / 1440)} days ago`;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div style={{
          display: 'inline-block',
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #007bff',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <p style={{ marginTop: '15px' }}>Loading monitoring data...</p>
        <style>
          {`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}
        </style>
      </div>
    );
  }

  if (!data) {
    return <div style={{ padding: '20px' }}>No monitoring data available</div>;
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f7fa', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: '#333' }}>
          📊 {t.title}
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
          {t.subtitle}
        </p>
      </div>

      {/* Controls */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px' 
      }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={fetchData}
            style={{
              padding: '10px 20px',
              backgroundColor: '#0366d6',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🔄 {t.refreshNow}
          </button>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ fontSize: '14px', color: '#666' }}>{t.autoRefresh}</span>
          </label>
        </div>
        
        {lastUpdate && (
          <div style={{ fontSize: '12px', color: '#666' }}>
            {t.lastUpdate}: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        
        {/* Services Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <h3 style={{ marginTop: 0, fontSize: '18px', color: '#333' }}>
            🔧 {t.servicesStatus}
          </h3>
          
          {Object.entries(data.services || {}).map(([key, service]) => (
            <div
              key={key}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                marginBottom: '8px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px',
                borderLeft: `4px solid ${getStatusColor(service.status)}`
              }}
            >
              <div>
                <div style={{ fontWeight: '600', fontSize: '14px' }}>
                  {service.name}
                </div>
                {service.version && (
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    v{service.version}
                  </div>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '18px' }}>
                  {getStatusIcon(service.status)}
                </span>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Queue Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <h3 style={{ marginTop: 0, fontSize: '18px', color: '#333' }}>
            ⚡ {t.queueStatus}
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#1976d2' }}>
                {data.queue?.active_tasks || 0}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                {t.activeTasks}
              </div>
            </div>
            
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#fff3e0', borderRadius: '8px' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f57c00' }}>
                {data.queue?.scheduled_tasks || 0}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                {t.scheduledTasks}
              </div>
            </div>
            
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f3e5f5', borderRadius: '8px' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#7b1fa2' }}>
                {data.queue?.total_pending || 0}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                {t.totalPending}
              </div>
            </div>
            
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#e8f5e9', borderRadius: '8px' }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#388e3c' }}>
                {data.queue?.workers_count || 0}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                {t.workers}
              </div>
            </div>
          </div>
        </motion.div>

        {/* OCR Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <h3 style={{ marginTop: 0, fontSize: '18px', color: '#333' }}>
            🤖 {t.ocrStats}
          </h3>
          
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '14px', color: '#666' }}>{t.totalScans}</span>
              <span style={{ fontSize: '20px', fontWeight: 'bold' }}>
                {data.ocr_stats?.total_scans || 0}
              </span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '14px', color: '#666' }}>{t.successRate}</span>
              <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#28a745' }}>
                {data.ocr_stats?.success_rate || 0}%
              </span>
            </div>
          </div>
          
          {data.ocr_stats?.methods_breakdown && (
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '10px', color: '#666' }}>
                {t.methods}:
              </div>
              {Object.entries(data.ocr_stats.methods_breakdown).map(([method, count]) => (
                <div
                  key={method}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    marginBottom: '5px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '4px'
                  }}
                >
                  <span style={{ fontSize: '13px' }}>{method || 'Unknown'}</span>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>{count}</span>
                </div>
              ))}
            </div>
          )}
        </motion.div>

        {/* System Health */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          style={{
            backgroundColor: '#fff',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <h3 style={{ marginTop: 0, fontSize: '18px', color: '#333' }}>
            💚 {t.systemHealth}
          </h3>
          
          {['cpu_percent', 'memory_percent', 'disk_percent'].map((key) => {
            const label = t[key.replace('_percent', '')];
            const value = data.system_health?.[key] || 0;
            const color = value > 90 ? '#dc3545' : value > 70 ? '#ffc107' : '#28a745';
            
            return (
              <div key={key} style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontSize: '14px' }}>{label}</span>
                  <span style={{ fontSize: '14px', fontWeight: '600', color }}>{value}%</span>
                </div>
                <div style={{ height: '8px', backgroundColor: '#e9ecef', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${value}%`, 
                    height: '100%', 
                    backgroundColor: color,
                    transition: 'width 0.3s'
                  }} />
                </div>
              </div>
            );
          })}
        </motion.div>
      </div>

      {/* Recent Scans Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        style={{
          backgroundColor: '#fff',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginTop: '20px'
        }}
      >
        <h3 style={{ marginTop: 0, fontSize: '18px', color: '#333', marginBottom: '15px' }}>
          📋 {t.recentScans}
        </h3>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa' }}>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>{t.name}</th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>{t.company}</th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>{t.method}</th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>{t.fields}</th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>{t.time}</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_scans?.map((scan) => (
                <tr key={scan.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: '12px' }}>{scan.full_name}</td>
                  <td style={{ padding: '12px', color: '#666' }}>{scan.company || '-'}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '4px 8px',
                      backgroundColor: scan.recognition_method?.includes('v2.0') ? '#d4edda' : '#fff3cd',
                      color: scan.recognition_method?.includes('v2.0') ? '#155724' : '#856404',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      {scan.recognition_method || 'unknown'}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ 
                      padding: '4px 8px',
                      backgroundColor: '#e3f2fd',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      {scan.fields_count}
                    </span>
                  </td>
                  <td style={{ padding: '12px', color: '#666', fontSize: '13px' }}>
                    {formatTime(scan.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};

export default MonitoringDashboard;

