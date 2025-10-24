# Console.log Cleanup Plan

## Status: In Progress (Phase B)

### Goal:
Replace all `console.log/error/warn` statements with production-safe logger utility

### Utility Created:
✅ `src/utils/logger.js` - Production-safe logger

### Usage:
```javascript
import logger from '../utils/logger';

// Development-only logging
logger.log('Debug info');
logger.error('Error occurred');
logger.warn('Warning message');

// Always log (critical)
logger.always('Important production message');
```

---

## Files to Update (68 statements in 35 files):

### Priority 1 - Completed ✅:
- [ ] ContactList.js (6 statements)
- [ ] SystemSettings.js (4 statements)
- [ ] OCREditorWithBlocks.js (4 statements)
- [ ] TwoFactorSettings.js (3 statements)
- [ ] ServiceManager.js (3 statements)

**Total Priority 1:** 20 statements

### Priority 2 - To Do:
- [ ] QRViewer.js (3 statements)
- [ ] LoginWith2FA.js (3 statements)
- [ ] DuplicatesPanel.js (3 statements)
- [ ] ContactCard.js (3 statements)
- [ ] MainLayout.js (2 statements)
- [ ] OCREditorPage.js (2 statements)
- [ ] HomePage.js (2 statements)
- [ ] CameraScanner.js (2 statements)
- [ ] TwoFactorSetup.js (2 statements)
- [ ] ServiceManagerSimple.js (2 statements)

**Total Priority 2:** 24 statements

### Priority 3 - Low:
- [ ] BatchUpload.js (1 statement)
- [ ] UploadCard.js (1 statement)
- [ ] SystemResources.js (1 statement)
- [ ] ErrorBoundary.js (1 statement)
- [ ] PullToRefresh.js (1 statement)
- [ ] UserManagement.js (1 statement)
- [ ] BackupManagement.js (1 statement)
- [ ] DuplicateMergeModal.js (1 statement)
- [ ] OCREditor.js (1 statement)
- [ ] Documentation.js (2 statements)
- [ ] Settings.js (1 statement)
- [ ] DuplicateFinder.js (2 statements)
- [ ] SearchOverlay.js (1 statement)
- [ ] Companies.js (1 statement)
- [ ] ContactEdit.js (1 statement)
- [ ] Register.js (1 statement)
- [ ] TelegramSettings.js (1 statement)
- [ ] OCRSettings.js (2 statements)
- [ ] Login.js (1 statement)
- [ ] DuplicatesSimple.js (2 statements)

**Total Priority 3:** 24 statements

---

## Progress:

- **Total:** 68 statements
- **Completed:** 0 statements (0%)
- **Remaining:** 68 statements (100%)

---

## Benefits:

1. **Performance:** No console.log overhead in production
2. **Security:** Prevents sensitive data leakage in browser console
3. **Maintainability:** Centralized logging configuration
4. **Debugging:** Easy to enable/disable logging per environment

---

## Timeline:

- **Phase 1 (Priority 1):** 20 statements - ~15 minutes
- **Phase 2 (Priority 2):** 24 statements - ~20 minutes  
- **Phase 3 (Priority 3):** 24 statements - ~20 minutes

**Total Estimated Time:** ~55 minutes for complete cleanup

---

## Next Steps:

1. Complete Priority 1 files
2. Test application functionality
3. Commit changes
4. Schedule Priority 2 & 3 for future sprint

---

*Created: October 24, 2025*  
*Last Updated: October 24, 2025*

