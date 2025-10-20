# Celery Batch Processing - Fix Log

**Date:** 2025-10-20  
**Version:** v2.4  

## Problem
Batch upload (ZIP) tasks were stuck in PENDING state and not processing files.

## Root Causes
1. **JSON Serialization:** Celery was configured to use JSON serializer, which cannot serialize `bytes` data
2. **Task Routing:** Custom queues (`batch_processing`, `card_processing`) were defined but worker wasn't subscribed to them
3. **Direct Function Calls:** `process_batch_upload` was calling `process_single_card()` directly (not via Celery), but `process_single_card` used `self.update_state()` which requires Celery task context

## Solutions Applied

### 1. Changed Celery Serialization (celery_app.py)
```python
task_serializer='pickle',  # Changed from 'json'
accept_content=['json', 'pickle'],
result_serializer='pickle',
```

### 2. Disabled Task Routing
Commented out custom queue routing to use default queue only:
```python
# celery_app.conf.task_routes = {
#     'app.tasks.process_batch_upload': {'queue': 'batch_processing'},
#     'app.tasks.process_single_card': {'queue': 'card_processing'},
# }
```

### 3. Added C_FORCE_ROOT (docker-compose.yml)
Celery refused to run with pickle under root user:
```yaml
celery-worker:
  environment:
    - C_FORCE_ROOT=true
```

### 4. Created Synchronous Processing Function (tasks.py)
Added `_process_card_sync()` for use in batch upload:
- Does NOT use Celery task context
- Called directly from `process_batch_upload`
- Shares same logic as `process_single_card` but without `self.update_state()`

## Test Results
- ✅ 3 files processed successfully
- ✅ 3 contacts created (Tesseract OCR)
- ✅ Task completed in 3 seconds
- ✅ Logs show all processing stages

## Performance
- **Tesseract OCR:** ~900ms per card
- **Total batch time:** ~3s for 3 cards
- **Concurrency:** 2 workers (prefork)

## Future Improvements
1. **Security:** Create non-root user for Celery worker instead of C_FORCE_ROOT
2. **Performance:** Implement parallel processing of cards in batch (currently sequential)
3. **Monitoring:** Add Celery Flower for task monitoring dashboard
4. **Result Cleanup:** Ensure old task results are cleaned up (cleanup_old_results task)

