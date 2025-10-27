# ✅ Nginx Web Panels Setup - Complete

**Дата:** 27 октября 2025  
**Время:** 06:38 UTC  
**Статус:** ✅ УСПЕШНО НАСТРОЕНО

---

## 🎉 Что Сделано

### 1. Настроен Nginx Reverse Proxy

**Файл:** `/etc/nginx/sites-available/ibbase.ru`

**Добавленные location блоки:**

#### MinIO Console
```nginx
location /minio/ {
    proxy_pass http://localhost:9001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support for real-time updates
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Increase timeouts
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
```

#### Label Studio
```nginx
location /label-studio/ {
    proxy_pass http://localhost:8081/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # For large file uploads (business card images)
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    client_max_body_size 100M;
    
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 2. Проверка и Запуск

```bash
✅ Backup created: /etc/nginx/sites-available/ibbase.ru.backup.*
✅ Configuration added successfully
✅ Syntax test passed: nginx -t
✅ Nginx reloaded: systemctl reload nginx
✅ Access verified: Logs show successful requests (304 Not Modified)
```

---

## 🌐 Доступ к Веб-Панелям

### 📦 MinIO Console (S3 Storage Management)

**URL:** https://ibbase.ru/minio/

**Credentials:**
- **Access Key:** `admin`
- **Secret Key:** `minio123456`

**Features:**
- File browser for business card images
- Bucket management
- Access control & policies
- Storage statistics
- Search & filtering

**First Steps:**
1. Login with credentials above
2. Click "Create Bucket +"
3. Create buckets:
   - `business-cards` - original images
   - `ocr-results` - OCR recognition results
   - `training-data` - annotated training data
   - `models` - trained ML models
4. Configure access policies for each bucket
5. **⚠️ Change password in .env file:**
   ```bash
   MINIO_ROOT_PASSWORD=YOUR_SECURE_PASSWORD
   ```

---

### 🏷️ Label Studio (Business Card Annotation)

**URL:** https://ibbase.ru/label-studio/

**Credentials:**
- **Email:** `admin@ibbase.ru`
- **Password:** `_sAYqjD3qtrlx726a6lU1ZpfLdTmCfCE`

**Features:**
- Visual annotation interface
- Draw bounding boxes around text
- Label business card fields (name, company, phone, email...)
- Export training data in JSON/COCO format
- Team collaboration

**First Steps:**
1. Login with credentials above
2. Click "Create Project"
3. Project name: "Business Cards OCR Training"
4. Import configuration from: `backend/app/integrations/label_studio_config.xml`
5. Start annotating business card images!
6. **⚠️ Change password in .env file:**
   ```bash
   LABEL_STUDIO_PASSWORD=YOUR_SECURE_PASSWORD
   ```

---

## 📊 Verification

### Access Logs (Success!)

```
92.118.231.161 - "GET /minio/ HTTP/2.0" 304 
92.118.231.161 - "GET /label-studio/ HTTP/2.0" 304
```

**Status Code 304 = SUCCESS** (Not Modified - using browser cache)

### Test Commands

```bash
# Test MinIO
curl -I https://ibbase.ru/minio/

# Test Label Studio
curl -I https://ibbase.ru/label-studio/

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log | grep -E "(minio|label-studio)"
```

---

## 🔐 Security Recommendations

### 1. Change Default Passwords (IMPORTANT!)

**Edit .env file:**
```bash
cd /home/ubuntu/fastapi-bizcard-crm-ready
nano .env

# Change these lines:
MINIO_ROOT_PASSWORD=YOUR_STRONG_PASSWORD_HERE
LABEL_STUDIO_PASSWORD=YOUR_STRONG_PASSWORD_HERE

# Save and restart containers:
docker compose down
docker compose up -d
```

### 2. Restrict Access by IP (Optional)

**Edit Nginx config:**
```bash
sudo nano /etc/nginx/sites-available/ibbase.ru
```

**Add inside location blocks:**
```nginx
location /minio/ {
    allow 192.168.1.0/24;  # Your office network
    allow 10.0.0.0/8;      # Your VPN range
    deny all;
    
    proxy_pass http://localhost:9001/;
    # ... rest of config
}
```

### 3. Enable HTTP Basic Auth (Optional)

```bash
# Install htpasswd tool
sudo apt-get install apache2-utils

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Add to Nginx location:
location /minio/ {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://localhost:9001/;
    # ... rest of config
}
```

---

## 📚 Documentation

### Full Guides:
- **Web Panels Guide:** `OCR_V2_WEB_PANELS_GUIDE.md`
- **OCR Architecture:** `OCR_ARCHITECTURE_MIGRATION_v2.md`
- **Monitoring Dashboard:** `MONITORING_DASHBOARD_COMPLETE.md`

### Key Files:
- Nginx config: `/etc/nginx/sites-available/ibbase.ru`
- Docker compose: `docker-compose.yml`
- MinIO config: Lines 135-152
- Label Studio config: Lines 117-133

---

## 🎯 Next Steps

### 1. MinIO Setup (5 minutes)

1. Open https://ibbase.ru/minio/
2. Login: admin / minio123456
3. Create 4 buckets (see above)
4. Optional: Create service account for application
5. Change password in .env

### 2. Label Studio Setup (10 minutes)

1. Open https://ibbase.ru/label-studio/
2. Login: admin@ibbase.ru / [password from .env]
3. Create project "Business Cards OCR Training"
4. Upload label config from `backend/app/integrations/label_studio_config.xml`
5. Import business card images from `/label-studio/files`
6. Start annotating!
7. Change password in .env

### 3. Start Using OCR v2.0

```python
# In your application code:
from app.services.storage_service import StorageService
from app.services.training.dataset_preparer import DatasetPreparer

# Save business card image to MinIO
storage = StorageService()
storage.save_business_card_image(
    image_data=file_bytes,
    contact_id=123,
    original_filename="card.jpg"
)

# After annotating in Label Studio:
preparer = DatasetPreparer()
dataset = preparer.prepare_from_label_studio(
    annotations_path="exports/annotations.json",
    images_path="uploads/"
)

# Train custom model (after 100+ annotations):
from app.services.training.model_trainer import ModelTrainer
trainer = ModelTrainer()
trainer.train(
    train_dataset=dataset,
    output_dir="models/layoutlm-custom"
)
```

---

## 🐛 Troubleshooting

### Problem: 404 Not Found

**Solution:** Check that services are running:
```bash
docker ps | grep -E "(minio|label-studio)"
```

### Problem: Cannot login to MinIO

**Solution:** Check environment variables:
```bash
docker logs bizcard-minio | grep -i "root"
```

### Problem: Label Studio not loading

**Solution:** Check logs:
```bash
docker logs bizcard-label-studio --tail 50
```

### Problem: Nginx error after setup

**Solution:** Restore backup:
```bash
sudo cp /etc/nginx/sites-available/ibbase.ru.backup.* /etc/nginx/sites-available/ibbase.ru
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 System Status

| Component | Status | Port | Access |
|-----------|--------|------|--------|
| **Nginx** | ✅ Running | 80, 443 | https://ibbase.ru |
| **MinIO** | ✅ Healthy | 9000, 9001 | https://ibbase.ru/minio/ |
| **Label Studio** | ✅ Running | 8081 | https://ibbase.ru/label-studio/ |
| **Backend** | ✅ Healthy | 8000 | https://ibbase.ru/api/ |
| **Frontend** | ✅ Running | 3000 | https://ibbase.ru |
| **Celery** | ✅ Running | - | Background tasks |
| **PostgreSQL** | ✅ Running | 5432 | Database |
| **Redis** | ✅ Healthy | 6379 | Cache & Queue |

---

## ✅ Success Checklist

- [x] Nginx configuration added
- [x] Syntax validated
- [x] Nginx reloaded
- [x] MinIO accessible via https://ibbase.ru/minio/
- [x] Label Studio accessible via https://ibbase.ru/label-studio/
- [x] WebSocket support enabled
- [x] SSL/HTTPS working
- [x] Access logs show successful requests
- [ ] MinIO buckets created (TODO for user)
- [ ] Label Studio project created (TODO for user)
- [ ] Default passwords changed (TODO for user)

---

## 🎊 Готово!

Теперь у вас есть полноценный доступ к:
- ✅ S3-совместимому хранилищу (MinIO)
- ✅ Инструменту для аннотации (Label Studio)
- ✅ Мониторингу системы (Admin Panel)
- ✅ AI моделям (PaddleOCR + LayoutLMv3)

**Все веб-панели доступны через браузер без SSH!**

**Следующий шаг:** Зайдите в MinIO и Label Studio, создайте bucket'ы и проект, измените пароли! 🚀

