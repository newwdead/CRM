/**
 * OCR Editor translations
 * Supports English and Russian languages
 */

export const ocrEditorTranslations = {
  en: {
    title: 'OCR Editor with Blocks',
    subtitle: 'Click blocks to assign to fields',
    loadingBlocks: 'Loading OCR blocks...',
    selectBlock: 'Select a text block',
    selectedBlocks: 'Selected blocks',
    assignTo: 'Assign to field:',
    assignButton: 'Assign',
    cancelAssignment: 'Cancel',
    clearSelection: 'Clear selection',
    multiSelectMode: 'Multi-select mode',
    multiSelectHint: 'Hold Ctrl to select multiple blocks',
    noBlocks: 'No text blocks detected',
    editBlocks: 'Edit Blocks',
    reprocessOCR: 'Re-run OCR',
    reprocessing: 'Re-processing...',
    reprocessSuccess: 'OCR re-processed successfully',
    reprocessError: 'Failed to re-process OCR',
    editModeHint: 'Drag blocks to move, drag corners to resize',
    deleteBlock: 'Delete Block',
    addBlock: 'Add Block',
    editText: 'Edit Text',
    splitBlock: 'Split Block',
    saveText: 'Save',
    cancelEdit: 'Cancel',
    blockTooSmall: 'Block too small',
    blockDeleted: 'Block deleted',
    blockAdded: 'Block added',
    textSaved: 'Text saved',
    blockSplit: 'Block split into two',
    newBlock: 'Draw area for new block',
    newText: 'New text',
    deleteConfirm: 'Delete this block?',
    fields: {
      first_name: 'First Name',
      last_name: 'Last Name',
      middle_name: 'Middle Name',
      company: 'Company',
      position: 'Position',
      email: 'Email',
      phone: 'Phone',
      phone_mobile: 'Mobile Phone',
      phone_work: 'Work Phone',
      phone_additional: 'Additional Phone',
      address: 'Address',
      address_additional: 'Additional Address',
      website: 'Website',
      comment: 'Notes'
    },
    buttons: {
      save: 'Save Changes',
      cancel: 'Cancel',
      reset: 'Reset'
    },
    messages: {
      saved: 'Changes saved successfully',
      error: 'Failed to save changes',
      loadError: 'Failed to load OCR blocks',
      noChanges: 'No changes to save'
    }
  },
  ru: {
    title: 'Редактор OCR с блоками',
    subtitle: 'Нажмите на блоки для назначения полям',
    loadingBlocks: 'Загрузка блоков OCR...',
    selectBlock: 'Выберите текстовый блок',
    selectedBlocks: 'Выбрано блоков',
    assignTo: 'Назначить полю:',
    assignButton: 'Назначить',
    cancelAssignment: 'Отмена',
    clearSelection: 'Очистить выбор',
    multiSelectMode: 'Режим мультивыбора',
    multiSelectHint: 'Удерживайте Ctrl для выбора нескольких блоков',
    noBlocks: 'Текстовые блоки не обнаружены',
    editBlocks: 'Редактировать блоки',
    reprocessOCR: 'Повторить OCR',
    reprocessing: 'Обработка...',
    reprocessSuccess: 'OCR успешно перезапущен',
    reprocessError: 'Ошибка при повторной обработке',
    editModeHint: 'Перетаскивайте блоки для перемещения, углы для изменения размера',
    deleteBlock: 'Удалить блок',
    addBlock: 'Добавить блок',
    editText: 'Редактировать текст',
    splitBlock: 'Разбить блок',
    saveText: 'Сохранить',
    cancelEdit: 'Отмена',
    blockTooSmall: 'Блок слишком маленький',
    blockDeleted: 'Блок удален',
    blockAdded: 'Блок добавлен',
    textSaved: 'Текст сохранен',
    blockSplit: 'Блок разбит на два',
    newBlock: 'Выделите область для нового блока',
    newText: 'Новый текст',
    deleteConfirm: 'Удалить этот блок?',
    fields: {
      first_name: 'Имя',
      last_name: 'Фамилия',
      middle_name: 'Отчество',
      company: 'Компания',
      position: 'Должность',
      email: 'Email',
      phone: 'Телефон',
      phone_mobile: 'Мобильный',
      phone_work: 'Рабочий',
      phone_additional: 'Доп. телефон',
      address: 'Адрес',
      address_additional: 'Доп. адрес',
      website: 'Веб-сайт',
      comment: 'Примечания'
    },
    buttons: {
      save: 'Сохранить',
      cancel: 'Отмена',
      reset: 'Сбросить'
    },
    messages: {
      saved: 'Изменения сохранены',
      error: 'Не удалось сохранить',
      loadError: 'Не удалось загрузить блоки OCR',
      noChanges: 'Нет изменений для сохранения'
    }
  }
};

/**
 * Get translations for specific language
 * @param {string} language - Language code ('en' or 'ru')
 * @returns {object} Translation object
 */
export const getOCRTranslations = (language = 'en') => {
  return ocrEditorTranslations[language] || ocrEditorTranslations.en;
};

