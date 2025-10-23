/**
 * Hook для управления OCR блоками
 * Изолированная логика работы с блоками распознавания
 */

import { useState, useEffect, useCallback } from 'react';
import { getOCRBlocks, reprocessOCR, updateContactFromOCR } from '../api/ocrApi';
import toast from 'react-hot-toast';

export const useOCRBlocks = (contact, language = 'ru') => {
  const [blocks, setBlocks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reprocessing, setReprocessing] = useState(false);
  const [imageScale, setImageScale] = useState(1);
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });

  const translations = {
    en: {
      loadError: 'Failed to load OCR blocks',
      reprocessSuccess: 'OCR re-processed successfully',
      reprocessError: 'Failed to re-process OCR',
      blockAdded: 'Block added',
      blockDeleted: 'Block deleted',
      textSaved: 'Text saved',
      blockSplit: 'Block split into two'
    },
    ru: {
      loadError: 'Ошибка загрузки блоков OCR',
      reprocessSuccess: 'OCR успешно перезапущен',
      reprocessError: 'Ошибка при повторной обработке',
      blockAdded: 'Блок добавлен',
      blockDeleted: 'Блок удален',
      textSaved: 'Текст сохранен',
      blockSplit: 'Блок разбит на два'
    }
  };

  const t = translations[language];

  // Загрузка блоков
  const loadBlocks = useCallback(async () => {
    if (!contact?.id) return;
    
    try {
      setLoading(true);
      const data = await getOCRBlocks(contact.id);
      setBlocks(data);
    } catch (error) {
      console.error('Error loading OCR blocks:', error);
      toast.error(t.loadError);
      setBlocks({ lines: [], image_width: 800, image_height: 600 });
    } finally {
      setLoading(false);
    }
  }, [contact?.id, t.loadError]);

  useEffect(() => {
    loadBlocks();
  }, [loadBlocks]);

  // Обновить блок
  const updateBlock = useCallback((blockIndex, updates) => {
    setBlocks(prev => ({
      ...prev,
      lines: prev.lines.map((block, idx) => 
        idx === blockIndex ? { ...block, ...updates } : block
      )
    }));
  }, []);

  // Удалить блок
  const deleteBlock = useCallback((blockIndex) => {
    setBlocks(prev => ({
      ...prev,
      lines: prev.lines.filter((_, idx) => idx !== blockIndex)
    }));
    toast.success(t.blockDeleted);
  }, [t.blockDeleted]);

  // Добавить блок
  const addBlock = useCallback((newBlock) => {
    setBlocks(prev => ({
      ...prev,
      lines: [...prev.lines, newBlock]
    }));
    toast.success(t.blockAdded);
  }, [t.blockAdded]);

  // Обновить текст блока
  const updateBlockText = useCallback((blockIndex, newText) => {
    updateBlock(blockIndex, { text: newText });
    toast.success(t.textSaved);
  }, [updateBlock, t.textSaved]);

  // Разбить блок на два
  const splitBlock = useCallback((blockIndex) => {
    const block = blocks.lines[blockIndex];
    const midY = block.box.y + block.box.height / 2;
    const midText = Math.floor(block.text.length / 2);
    
    const block1 = {
      ...block,
      box: { ...block.box, height: block.box.height / 2 },
      text: block.text.substring(0, midText)
    };
    
    const block2 = {
      ...block,
      box: { ...block.box, y: midY, height: block.box.height / 2 },
      text: block.text.substring(midText)
    };
    
    setBlocks(prev => ({
      ...prev,
      lines: [
        ...prev.lines.slice(0, blockIndex),
        block1,
        block2,
        ...prev.lines.slice(blockIndex + 1)
      ]
    }));
    
    toast.success(t.blockSplit);
  }, [blocks, t.blockSplit]);

  // Повторная обработка OCR
  const handleReprocess = useCallback(async (onSuccess) => {
    if (!blocks || !contact?.id) return;
    
    try {
      setReprocessing(true);
      const result = await reprocessOCR(contact.id, blocks.lines);
      
      toast.success(t.reprocessSuccess);
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      return result;
    } catch (error) {
      console.error('Error reprocessing OCR:', error);
      toast.error(t.reprocessError);
      throw error;
    } finally {
      setReprocessing(false);
    }
  }, [blocks, contact?.id, t.reprocessSuccess, t.reprocessError]);

  return {
    blocks,
    setBlocks,
    loading,
    reprocessing,
    imageScale,
    imageOffset,
    setImageScale,
    setImageOffset,
    updateBlock,
    deleteBlock,
    addBlock,
    updateBlockText,
    splitBlock,
    handleReprocess,
    reload: loadBlocks
  };
};

