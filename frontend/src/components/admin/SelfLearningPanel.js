import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

/**
 * Self-Learning System Management Panel
 * - View training status
 * - Get annotation recommendations
 * - Collect training data
 * - Trigger model training
 */
const SelfLearningPanel = () => {
  const [language] = useState(localStorage.getItem('language') || 'ru');
  const [status, setStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  
  const translations = {
    ru: {
      title: 'Система самообучения OCR',
      description: 'Система автоматически улучшается на основе ваших исправлений',
      labelStudio: 'Label Studio',
      trainingData: 'Обучающие данные',
      recommendations: 'Рекомендации для аннотации',
      status: 'Статус',
      available: 'Доступен',
      unavailable: 'Недоступен',
      projectId: 'ID проекта',
      totalTasks: 'Всего задач',
      completedTasks: 'Завершено',
      trainingSamples: 'Образцов для обучения',
      readyForTraining: 'Готово к обучению',
      yes: 'Да',
      no: 'Нет',
      contactId: 'ID контакта',
      priority: 'Приоритет',
      confidence: 'Уверенность',
      reasons: 'Причины',
      actions: 'Действия',
      sendToAnnotation: 'Отправить на аннотацию',
      initLabelStudio: 'Инициализировать Label Studio',
      collectData: 'Собрать данные',
      triggerTraining: 'Начать обучение',
      refresh: 'Обновить',
      loading: 'Загрузка...',
      noRecommendations: 'Нет рекомендаций',
      success: 'Успешно',
      error: 'Ошибка',
      howItWorks: 'Как это работает',
      howItWorksText: [
        '1. Система распознает визитки через PaddleOCR + LayoutLMv3',
        '2. Когда вы исправляете ошибки в редакторе, система сохраняет ваши правки',
        '3. Active Learning выбирает сложные кейсы для ручной проверки',
        '4. После накопления 50+ образцов, система может дообучиться',
        '5. Качество распознавания автоматически улучшается'
      ]
    },
    en: {
      title: 'OCR Self-Learning System',
      description: 'System automatically improves based on your corrections',
      labelStudio: 'Label Studio',
      trainingData: 'Training Data',
      recommendations: 'Annotation Recommendations',
      status: 'Status',
      available: 'Available',
      unavailable: 'Unavailable',
      projectId: 'Project ID',
      totalTasks: 'Total tasks',
      completedTasks: 'Completed',
      trainingSamples: 'Training samples',
      readyForTraining: 'Ready for training',
      yes: 'Yes',
      no: 'No',
      contactId: 'Contact ID',
      priority: 'Priority',
      confidence: 'Confidence',
      reasons: 'Reasons',
      actions: 'Actions',
      sendToAnnotation: 'Send to Annotation',
      initLabelStudio: 'Initialize Label Studio',
      collectData: 'Collect Data',
      triggerTraining: 'Start Training',
      refresh: 'Refresh',
      loading: 'Loading...',
      noRecommendations: 'No recommendations',
      success: 'Success',
      error: 'Error',
      howItWorks: 'How it works',
      howItWorksText: [
        '1. System recognizes cards via PaddleOCR + LayoutLMv3',
        '2. When you correct errors in editor, system saves your edits',
        '3. Active Learning selects difficult cases for manual review',
        '4. After collecting 50+ samples, system can be retrained',
        '5. Recognition quality automatically improves'
      ]
    }
  };
  
  const t = translations[language];
  
  useEffect(() => {
    loadStatus();
    loadRecommendations();
  }, []);
  
  const loadStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/self-learning/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Error loading status:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const loadRecommendations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/self-learning/recommendations?limit=10', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Error loading recommendations:', error);
    }
  };
  
  const initLabelStudio = async () => {
    try {
      setProcessing(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/self-learning/init-label-studio', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`${t.success}: Project ID ${data.project_id}`);
        await loadStatus();
      } else {
        const error = await response.json();
        toast.error(error.detail || t.error);
      }
    } catch (error) {
      toast.error(t.error);
    } finally {
      setProcessing(false);
    }
  };
  
  const sendForAnnotation = async (contactId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/self-learning/send-for-annotation/${contactId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        toast.success(`${t.success}: Contact ${contactId} sent to Label Studio`);
        await loadRecommendations();
      } else {
        const error = await response.json();
        toast.error(error.detail || t.error);
      }
    } catch (error) {
      toast.error(t.error);
    }
  };
  
  const collectData = async () => {
    try {
      setProcessing(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/self-learning/collect-training-data', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`${t.success}: ${data.samples_count} samples collected`);
        await loadStatus();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed');
      }
    } catch (error) {
      toast.error(t.error);
    } finally {
      setProcessing(false);
    }
  };
  
  const triggerTraining = async () => {
    try {
      setProcessing(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/self-learning/trigger-training', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      if (response.ok && data.success) {
        toast.success(data.message);
      } else {
        toast.error(data.message || t.error);
      }
    } catch (error) {
      toast.error(t.error);
    } finally {
      setProcessing(false);
    }
  };
  
  if (loading) {
    return <div className="p-8 text-center">{t.loading}</div>;
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold mb-2">{t.title}</h2>
        <p className="text-gray-600">{t.description}</p>
      </div>
      
      {/* How it works */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold mb-2">💡 {t.howItWorks}</h3>
        <ul className="text-sm text-gray-700 space-y-1">
          {t.howItWorksText.map((text, idx) => (
            <li key={idx}>{text}</li>
          ))}
        </ul>
      </div>
      
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Label Studio Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4">📊 {t.labelStudio}</h3>
          {status && status.label_studio ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">{t.status}:</span>
                <span className={status.label_studio.available ? 'text-green-600 font-semibold' : 'text-red-600'}>
                  {status.label_studio.available ? t.available : t.unavailable}
                </span>
              </div>
              {status.label_studio.project_id && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-600">{t.projectId}:</span>
                    <span>{status.label_studio.project_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">{t.totalTasks}:</span>
                    <span>{status.label_studio.total_tasks || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">{t.completedTasks}:</span>
                    <span>{status.label_studio.completed_tasks || 0}</span>
                  </div>
                </>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">{t.unavailable}</p>
          )}
          
          {!status?.label_studio?.project_id && (
            <button
              onClick={initLabelStudio}
              disabled={processing}
              className="mt-4 w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {t.initLabelStudio}
            </button>
          )}
        </div>
        
        {/* Training Data Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4">🎓 {t.trainingData}</h3>
          {status && status.training ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">{t.trainingSamples}:</span>
                <span className="font-semibold">{status.training.total_training_samples || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">{t.readyForTraining}:</span>
                <span className={status.training.ready_for_training ? 'text-green-600 font-semibold' : 'text-gray-500'}>
                  {status.training.ready_for_training ? t.yes : t.no}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Minimum: {status.training.min_samples_required} samples
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No data</p>
          )}
          
          <div className="mt-4 space-y-2">
            <button
              onClick={collectData}
              disabled={processing}
              className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {t.collectData}
            </button>
            <button
              onClick={triggerTraining}
              disabled={processing || !status?.training?.ready_for_training}
              className="w-full bg-purple-600 text-white py-2 rounded hover:bg-purple-700 disabled:opacity-50"
            >
              {t.triggerTraining}
            </button>
          </div>
        </div>
      </div>
      
      {/* Recommendations */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">🎯 {t.recommendations}</h3>
          <button
            onClick={loadRecommendations}
            className="text-blue-600 hover:text-blue-700 text-sm"
          >
            {t.refresh}
          </button>
        </div>
        
        {recommendations.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-2 text-left">{t.contactId}</th>
                  <th className="p-2 text-left">{t.priority}</th>
                  <th className="p-2 text-left">{t.confidence}</th>
                  <th className="p-2 text-left">{t.reasons}</th>
                  <th className="p-2 text-left">{t.actions}</th>
                </tr>
              </thead>
              <tbody>
                {recommendations.map((rec) => (
                  <tr key={rec.contact_id} className="border-t">
                    <td className="p-2">{rec.contact_id}</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        rec.priority >= 3 ? 'bg-red-100 text-red-800' :
                        rec.priority === 2 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {rec.priority}
                      </span>
                    </td>
                    <td className="p-2">{(rec.confidence * 100).toFixed(0)}%</td>
                    <td className="p-2 text-xs text-gray-600">
                      {rec.reasons.slice(0, 2).join(', ')}
                    </td>
                    <td className="p-2">
                      <button
                        onClick={() => sendForAnnotation(rec.contact_id)}
                        className="text-blue-600 hover:text-blue-700 text-xs"
                      >
                        {t.sendToAnnotation}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">{t.noRecommendations}</p>
        )}
      </div>
    </div>
  );
};

export default SelfLearningPanel;

