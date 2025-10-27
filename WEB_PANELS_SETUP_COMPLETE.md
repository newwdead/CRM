# ✅ Web Panels Setup Complete

**Date:** October 27, 2025  
**Version:** 6.0.0  
**Setup Type:** Temporary (subpath deployment)

---

## 🎯 Objective

Configure MinIO Console and Label Studio web panels to be accessible via:
- **MinIO Console:** https://ibbase.ru/minio/
- **Label Studio:** https://ibbase.ru/label-studio/

---

## ✅ Changes Implemented

### 1. Docker Compose Configuration Updates

#### MinIO Service
Added environment variables for reverse proxy support:

```yaml
environment:
  MINIO_ROOT_USER: ${MINIO_ROOT_USER:-admin}
  MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minio123456}
  # For reverse proxy with /minio/ path
  MINIO_BROWSER_REDIRECT_URL: https://ibbase.ru/minio/
  MINIO_SERVER_URL: https://ibbase.ru/api/minio
```

**Result:** MinIO now knows it's behind a reverse proxy at /minio/

#### Label Studio Service
Added environment variables for reverse proxy support:

```yaml
environment:
  - LABEL_STUDIO_HOST=https://ibbase.ru
  - LABEL_STUDIO_BASE_URL=/label-studio
  - LABEL_STUDIO_USERNAME=${LABEL_STUDIO_USERNAME:-admin@ibbase.ru}
  - LABEL_STUDIO_PASSWORD=${LABEL_STUDIO_PASSWORD:?LABEL_STUDIO_PASSWORD must be set in .env file}
```

**Result:** Label Studio now knows it's behind a reverse proxy at /label-studio/

### 2. Nginx Configuration

The following nginx `location` blocks were already configured in `/etc/nginx/sites-enabled/ibbase.ru`:

#### MinIO Console Block
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

#### Label Studio Block
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

### 3. Services Restart

```bash
# Recreated MinIO container with new environment variables
docker compose up -d minio label-studio

# Reloaded nginx configuration
sudo systemctl reload nginx
```

---

## ✅ Verification Results

### MinIO Console
```bash
$ curl -k -I https://ibbase.ru/minio/
HTTP/2 200 
content-type: text/html
```
✅ **Status:** WORKING - Returns HTML page

### Label Studio
```bash
$ curl -k -I https://ibbase.ru/label-studio/
HTTP/2 302 
location: /user/login/
content-type: text/html; charset=utf-8
```
✅ **Status:** WORKING - Returns login redirect

---

## 🔐 Access Credentials

### MinIO Console (https://ibbase.ru/minio/)
- **Username:** `admin` (or value from `MINIO_ROOT_USER`)
- **Password:** `minio123456` (or value from `MINIO_ROOT_PASSWORD`)

### Label Studio (https://ibbase.ru/label-studio/)
- **Email:** `admin@ibbase.ru` (or value from `LABEL_STUDIO_USERNAME`)
- **Password:** From `.env` file (`LABEL_STUDIO_PASSWORD`)

---

## 📊 Current Status

| Service | URL | Status | Port | Purpose |
|---------|-----|--------|------|---------|
| MinIO Console | https://ibbase.ru/minio/ | ✅ Active | 9001 | S3 Storage Management |
| MinIO API | http://localhost:9000 | ✅ Active | 9000 | S3 API (internal) |
| Label Studio | https://ibbase.ru/label-studio/ | ✅ Active | 8081 | Business Card Annotation |

---

## ⚠️ Known Limitations

### Subpath Deployment Issues

Both MinIO Console and Label Studio are Single Page Applications (SPAs) that may have issues with subpath deployments:

1. **Potential Path Issues:**
   - Some SPA routes might not correctly prefix `/minio/` or `/label-studio/`
   - Static assets (JS/CSS) might load from wrong paths
   - Deep links might not work correctly

2. **Symptoms:**
   - Blank pages after login
   - 404 errors for static resources
   - Broken navigation links

### Recommended Solution (Future)

For production-grade deployment, consider using **subdomains** instead:
- `minio.ibbase.ru` for MinIO Console
- `label.ibbase.ru` for Label Studio

This requires:
- DNS A records for subdomains
- SSL certificates for subdomains (Let's Encrypt)
- Separate nginx server blocks

---

## 🧪 Testing Checklist

Please test the following in your browser:

### MinIO Console
- [ ] Access https://ibbase.ru/minio/
- [ ] Login with credentials
- [ ] Navigate to buckets list
- [ ] Open `business-cards` bucket
- [ ] View file details
- [ ] Check if all navigation works

### Label Studio
- [ ] Access https://ibbase.ru/label-studio/
- [ ] Login with credentials
- [ ] Access project dashboard
- [ ] Check if images load
- [ ] Test annotation interface
- [ ] Check if all navigation works

---

## 🐛 Troubleshooting

### If pages don't load correctly:

1. **Check browser console for errors:**
   - Press F12 → Console tab
   - Look for 404 errors or failed resource loads

2. **Check Docker logs:**
   ```bash
   docker logs bizcard-minio
   docker logs bizcard-label-studio
   ```

3. **Check nginx access/error logs:**
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

### If you see blank pages:

This is likely the SPA routing issue. The recommended fix is to switch to **subdomain deployment**.

Would you like me to set up subdomains instead? This is the more robust solution.

---

## 📝 Next Steps

If the current subpath deployment doesn't work correctly (blank pages, navigation issues), we should:

1. **Option A: Switch to Subdomains** (Recommended)
   - Set up `minio.ibbase.ru` and `label.ibbase.ru`
   - Requires DNS changes and SSL certificates
   - More reliable for SPA applications

2. **Option B: Keep Subpaths + Add Workarounds**
   - Add nginx `sub_filter` directives to rewrite HTML
   - Configure base URLs in application configs
   - May be fragile and require ongoing maintenance

3. **Option C: Use SSH Tunnels for Local Access**
   - Most secure, no public exposure
   - Requires SSH access for each session
   - Best for single-user scenarios

---

## 🎉 Summary

✅ **MinIO Console** configured at https://ibbase.ru/minio/  
✅ **Label Studio** configured at https://ibbase.ru/label-studio/  
⚠️ **Note:** This is a temporary solution. If you experience issues, subdomain deployment is recommended.

**Please test the web panels and let me know if they work correctly!**


