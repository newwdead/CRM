/**
 * Hook для управления интеграциями
 */

import { useState, useEffect, useCallback } from 'react';
import { getIntegrationsStatus, toggleIntegration, testIntegration, updateIntegrationConfig } from '../api/settingsApi';
import toast from 'react-hot-toast';

export const useIntegrations = (language = 'ru') => {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(null);

  const t = {
    en: { loadError: 'Failed to load integrations', testSuccess: 'Test successful', testError: 'Test failed', toggleSuccess: 'Integration updated', toggleError: 'Failed to update', configSuccess: 'Configuration saved', configError: 'Failed to save' },
    ru: { loadError: 'Ошибка загрузки интеграций', testSuccess: 'Тест успешен', testError: 'Ошибка теста', toggleSuccess: 'Интеграция обновлена', toggleError: 'Ошибка обновления', configSuccess: 'Конфигурация сохранена', configError: 'Ошибка сохранения' }
  }[language];

  const loadIntegrations = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getIntegrationsStatus();
      setIntegrations(data.integrations || []);
    } catch (error) {
      toast.error(t.loadError);
    } finally {
      setLoading(false);
    }
  }, [t.loadError]);

  useEffect(() => {
    loadIntegrations();
  }, [loadIntegrations]);

  const handleToggle = useCallback(async (id, enabled) => {
    try {
      await toggleIntegration(id, enabled);
      toast.success(t.toggleSuccess);
      await loadIntegrations();
    } catch (error) {
      toast.error(t.toggleError);
    }
  }, [t.toggleSuccess, t.toggleError, loadIntegrations]);

  const handleTest = useCallback(async (id) => {
    try {
      setTesting(id);
      await testIntegration(id);
      toast.success(t.testSuccess);
    } catch (error) {
      toast.error(t.testError);
    } finally {
      setTesting(null);
    }
  }, [t.testSuccess, t.testError]);

  const handleUpdateConfig = useCallback(async (id, config) => {
    try {
      await updateIntegrationConfig(id, config);
      toast.success(t.configSuccess);
      await loadIntegrations();
    } catch (error) {
      toast.error(t.configError);
    }
  }, [t.configSuccess, t.configError, loadIntegrations]);

  return { integrations, loading, testing, refresh: loadIntegrations, toggle: handleToggle, test: handleTest, updateConfig: handleUpdateConfig };
};

