/**
 * Hook для управления Docker сервисами
 * Изолированная логика работы с сервисами
 */

import { useState, useEffect, useCallback } from 'react';
import { getServicesStatus, restartService, getServiceLogs } from '../api/servicesApi';
import toast from 'react-hot-toast';

export const useServices = (language = 'ru', autoRefresh = true, refreshInterval = 10000) => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [restarting, setRestarting] = useState(null);

  const translations = {
    en: {
      loadError: 'Error loading services',
      restartSuccess: 'Service restarted successfully',
      restartError: 'Failed to restart service',
      logsError: 'Failed to load logs'
    },
    ru: {
      loadError: 'Ошибка загрузки сервисов',
      restartSuccess: 'Сервис успешно перезапущен',
      restartError: 'Ошибка перезапуска сервиса',
      logsError: 'Ошибка загрузки логов'
    }
  };

  const t = translations[language];

  // Загрузка статусов сервисов
  const loadServices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getServicesStatus();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setServices(data.services || []);
    } catch (err) {
      console.error('Error fetching services:', err);
      setError(err.message);
      toast.error(`${t.loadError}: ${err.message}`);
      setServices([]);
    } finally {
      setLoading(false);
    }
  }, [t.loadError]);

  // Автообновление
  useEffect(() => {
    loadServices();

    if (autoRefresh) {
      const interval = setInterval(loadServices, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [loadServices, autoRefresh, refreshInterval]);

  // Перезапуск сервиса
  const handleRestart = useCallback(async (serviceName) => {
    try {
      setRestarting(serviceName);
      await restartService(serviceName);
      toast.success(t.restartSuccess);
      
      // Обновляем список через 2 секунды
      setTimeout(loadServices, 2000);
    } catch (err) {
      console.error(`Error restarting service ${serviceName}:`, err);
      toast.error(`${t.restartError}: ${err.message}`);
    } finally {
      setRestarting(null);
    }
  }, [t.restartSuccess, t.restartError, loadServices]);

  // Получение логов
  const getLogs = useCallback(async (serviceName, lines = 50) => {
    try {
      const data = await getServiceLogs(serviceName, lines);
      return data.logs || '';
    } catch (err) {
      console.error(`Error fetching logs for ${serviceName}:`, err);
      toast.error(`${t.logsError}: ${err.message}`);
      return '';
    }
  }, [t.logsError]);

  // Статистика
  const stats = {
    total: services.length,
    running: services.filter(s => s.state?.toLowerCase().includes('running')).length,
    stopped: services.filter(s => 
      s.state?.toLowerCase().includes('exited') || 
      s.state?.toLowerCase().includes('stopped')
    ).length
  };

  return {
    services,
    loading,
    error,
    restarting,
    stats,
    refresh: loadServices,
    restart: handleRestart,
    getLogs
  };
};

