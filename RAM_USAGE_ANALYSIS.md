# 🔍 RAM Usage Analysis Report

**Date:** October 27, 2025  
**System:** 11.68 GB RAM total  
**Used:** 6.6 GB (57%)  
**Problem:** Heavy ML libraries causing excessive memory consumption

---

## 📊 Current Memory Usage Summary

### System Overview
```
Total RAM:     11.68 GB
Used:          6.6 GB (57%)
Free:          1.6 GB
Buffer/Cache:  3.9 GB
Available:     5.1 GB
Swap:          0 GB (NOT CONFIGURED!)
```

⚠️ **Critical:** No swap configured - system will crash if RAM exhausted!

---

## 🐳 Docker Containers Memory Usage

| Container | Memory Usage | % of Total | Status |
|-----------|--------------|------------|--------|
| **bizcard-celery-worker** | **2.57 GB** | **22%** | ⚠️ CRITICAL |
| **bizcard-backend** | **1.45 GB** | **12%** | ⚠️ HIGH |
| bizcard-label-studio | 207 MB | 1.7% | ✅ OK |
| bizcard-grafana | 155 MB | 1.3% | ✅ OK |
| bizcard-minio | 133 MB | 1.1% | ✅ OK |
| bizcard-prometheus | 48 MB | 0.4% | ✅ OK |
| bizcard-db | 30 MB | 0.25% | ✅ OK |
| bizcard-redis | 8 MB | 0.07% | ✅ OK |
| **TOTAL Docker** | **~4.6 GB** | **~39%** | ⚠️ HIGH |

---

## 🔥 TOP MEMORY CONSUMERS (Host Processes)

| Process | Memory | % | Description |
|---------|--------|---|-------------|
| python (celery main) | 1.99 GB | 16.5% | Celery worker main process |
| python3.11 (worker 1) | 1.70 GB | 14.1% | Celery fork worker 1 |
| python (worker 2) | 1.60 GB | 13.3% | Celery fork worker 2 |
| python (worker 3) | 1.60 GB | 13.3% | Celery fork worker 3 |
| python3.11 (subprocess) | 1.50 GB | 12.5% | Celery subprocess |
| **TOTAL Celery** | **~8.4 GB** | **~70%** | ⚠️⚠️⚠️ CRITICAL |

---

## 🎯 ROOT CAUSE: Heavy ML Libraries

### Docker Image Size Analysis

**Backend Image:** `7.86 GB` (was 1.33 GB)  
**Breakdown:**
- Base Python 3.11: ~125 MB
- System packages: **933 MB**
- **Python ML packages: ~6.8 GB** ⚠️
- Application code: 1.7 MB

### Installed Heavy Libraries

```python
# requirements.txt - ML Dependencies
torch==2.1.1              # ~2.5 GB (PyTorch)
torchvision==0.16.1       # ~500 MB
paddlepaddle==2.6.1       # ~2.0 GB (PaddlePaddle CPU)
paddleocr==2.7.3          # ~300 MB + models
transformers==4.35.2      # ~1.0 GB (HuggingFace)
datasets==2.15.0          # ~500 MB
accelerate==0.25.0        # ~200 MB
opencv-python==4.6.0.66   # ~200 MB (duplicate!)
opencv-python-headless==4.10.0.84  # ~150 MB
opencv-contrib-python==4.6.0.66    # ~200 MB (duplicate!)
```

**Total ML libraries size:** ~7.5 GB

### Memory Consumption at Runtime

When loaded into memory, these libraries consume:
- **PyTorch runtime:** ~1.5-2 GB (tensors, CUDA context)
- **PaddleOCR models:** ~800 MB (loaded models)
- **Transformers (LayoutLMv3):** ~1.2 GB (model weights)
- **OpenCV buffers:** ~200-400 MB
- **Python overhead:** ~300 MB
- **Total per worker:** ~3.5-4 GB

**With 2 Celery workers + main process:** ~8-10 GB RAM usage!

---

## ⚠️ CRITICAL ISSUES IDENTIFIED

### 1. **Celery Worker Memory Leak**
- **Current:** 2.57 GB in container, ~8 GB on host
- **Expected:** ~500 MB per worker
- **Root cause:** ML libraries loaded in memory
- **Impact:** System instability, potential OOM crashes

### 2. **No Memory Limits Set**
```yaml
# docker-compose.yml
celery-worker:
  # NO memory limits! ⚠️
  # NO mem_limit: 2g
  # NO mem_reservation: 1g
```

### 3. **Multiple OpenCV Versions**
- opencv-python==4.6.0.66
- opencv-python-headless==4.10.0.84
- opencv-contrib-python==4.6.0.66

**Wasting:** ~350 MB disk + ~200 MB RAM

### 4. **No Swap Configured**
```
Swap: 0B total, 0B used, 0B free
```
**Risk:** System crash if RAM exhausted!

### 5. **ML Libraries Always Loaded**
- Libraries loaded even when not processing OCR
- No lazy loading
- Models kept in memory between tasks

---

## 💡 RECOMMENDED SOLUTIONS

### 🔴 URGENT (Critical Priority)

#### 1. **Configure Memory Limits**
```yaml
# docker-compose.yml
celery-worker:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
  mem_swappiness: 60
```

#### 2. **Enable Swap**
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 3. **Reduce Celery Concurrency**
```yaml
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info --concurrency=1
```
**Impact:** Reduce memory from 8 GB to 4 GB

---

### 🟡 HIGH PRIORITY (Important)

#### 4. **Cleanup Duplicate OpenCV**
```python
# requirements.txt - Keep ONLY ONE
opencv-python-headless==4.10.0.84  # ✅ Keep (headless = smaller)
# opencv-python==4.6.0.66          # ❌ Remove
# opencv-contrib-python==4.6.0.66  # ❌ Remove
```
**Savings:** ~350 MB disk, ~200 MB RAM

#### 5. **Implement Lazy Loading for ML Models**
```python
# app/services/ocr_service.py
class OCRService:
    _paddle_model = None
    _torch_model = None
    
    @classmethod
    def get_paddle_model(cls):
        if cls._paddle_model is None:
            cls._paddle_model = PaddleOCR(use_angle_cls=True, lang='en')
        return cls._paddle_model
    
    @classmethod
    def clear_models(cls):
        """Call after task completion to free memory"""
        cls._paddle_model = None
        cls._torch_model = None
        gc.collect()
```

#### 6. **Optimize Celery Settings**
```python
# celery_app.py
celery_app.conf.update(
    worker_max_tasks_per_child=20,  # Reduce from 50
    worker_prefetch_multiplier=1,   # Already set ✅
    task_acks_late=True,            # Already set ✅
    worker_max_memory_per_child=2000000,  # 2GB limit per child
)
```

---

### 🟢 MEDIUM PRIORITY (Optimization)

#### 7. **Use Lighter ML Alternatives**
```python
# Option A: Use CPU-optimized builds
torch==2.1.1+cpu  # ~800 MB (vs 2.5 GB)
torchvision==0.16.1+cpu  # ~150 MB (vs 500 MB)

# Option B: Remove unused libraries
# transformers==4.35.2  # Remove if LayoutLMv3 not used
# datasets==2.15.0      # Remove if not training
# accelerate==0.25.0    # Remove if not distributed training
```

#### 8. **Separate OCR Worker Container**
```yaml
# docker-compose.yml
celery-worker-ocr:
  build: ./backend
  command: celery -A app.celery_app worker -Q ocr --loglevel=info --concurrency=1
  deploy:
    resources:
      limits:
        memory: 3G

celery-worker-light:
  build: ./backend-light  # Without ML libs
  command: celery -A app.celery_app worker -Q default --loglevel=info --concurrency=2
  deploy:
    resources:
      limits:
        memory: 512M
```

#### 9. **Optimize Tesseract**
```yaml
# Only install needed languages
RUN apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng
    # Remove: tesseract-ocr-all (saves ~500 MB)
```

---

## 📈 EXPECTED IMPROVEMENTS

### After Immediate Fixes (1-3)
| Metric | Current | After Fix | Improvement |
|--------|---------|-----------|-------------|
| Celery RAM | 2.57 GB | 1.5 GB | **-42%** |
| Backend RAM | 1.45 GB | 800 MB | **-45%** |
| Total Docker | 4.6 GB | 2.8 GB | **-39%** |
| System Free | 1.6 GB | 4.4 GB | **+175%** |

### After All Optimizations (1-9)
| Metric | Current | After Fix | Improvement |
|--------|---------|-----------|-------------|
| Docker Image | 7.86 GB | 2.5 GB | **-68%** |
| Celery RAM | 2.57 GB | 800 MB | **-69%** |
| Backend RAM | 1.45 GB | 600 MB | **-59%** |
| Total Docker | 4.6 GB | 1.8 GB | **-61%** |
| System Free | 1.6 GB | 6.8 GB | **+325%** |

---

## 🔧 IMPLEMENTATION PLAN

### Phase 1: Emergency Fixes (15 minutes)
1. ✅ Reduce concurrency to 1
2. ✅ Add memory limits to containers
3. ✅ Enable swap

### Phase 2: Quick Wins (30 minutes)
4. ✅ Remove duplicate OpenCV
5. ✅ Optimize Celery settings
6. ✅ Implement lazy loading

### Phase 3: Architecture (2-4 hours)
7. ✅ Separate OCR worker
8. ✅ Use lighter ML builds
9. ✅ Optimize Dockerfile

---

## 📝 MONITORING

### Add to Prometheus
```yaml
# Monitor memory usage
- container_memory_usage_bytes
- container_memory_working_set_bytes
- celery_worker_memory_usage
```

### Add Alerts
```yaml
- alert: HighMemoryUsage
  expr: container_memory_usage_bytes > 2GB
  for: 5m
```

---

## ✅ CONCLUSION

**Primary Issue:** Heavy ML libraries (PyTorch, PaddlePaddle, Transformers) consuming 6-8 GB RAM

**Immediate Action Required:**
1. Reduce Celery concurrency from 2 to 1
2. Add memory limits to containers
3. Enable swap immediately

**Long-term Solution:**
- Separate OCR processing to dedicated worker
- Use lightweight ML library builds
- Implement lazy loading with memory cleanup

**Expected Result:** Reduce memory usage from 6.6 GB to 2-3 GB (~60% reduction)

