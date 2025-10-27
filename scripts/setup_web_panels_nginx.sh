#!/bin/bash
# Setup Nginx reverse proxy for MinIO Console and Label Studio
# Makes web panels accessible via https://ibbase.ru/minio/ and https://ibbase.ru/label-studio/

set -e

echo "🌐 Setting up Nginx reverse proxy for OCR v2.0 web panels..."

NGINX_CONFIG="/etc/nginx/sites-available/ibbase.ru"

# Check if nginx config exists
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "❌ Error: Nginx config not found at $NGINX_CONFIG"
    exit 1
fi

echo "📝 Backing up current Nginx config..."
sudo cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

echo "✏️  Adding MinIO Console location block..."
sudo bash -c "cat >> $NGINX_CONFIG" << 'EOF'

    # MinIO Console - S3 Storage Management
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

    # Label Studio - Business Card Annotation Tool
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
EOF

echo "✅ Configuration added!"

echo "🔍 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid!"
    
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "🎉 Success! Web panels are now accessible:"
    echo ""
    echo "📦 MinIO Console (S3 Storage):"
    echo "   URL: https://ibbase.ru/minio/"
    echo "   Login: admin"
    echo "   Password: minio123456"
    echo ""
    echo "🏷️  Label Studio (Annotation):"
    echo "   URL: https://ibbase.ru/label-studio/"
    echo "   Email: admin@ibbase.ru"
    echo "   Password: [see .env file]"
    echo ""
    echo "⚠️  ВАЖНО: Смените пароли в .env файле!"
    echo ""
    echo "📚 Полная документация: OCR_V2_WEB_PANELS_GUIDE.md"
    
else
    echo "❌ Nginx configuration test failed!"
    echo "🔄 Restoring backup..."
    sudo cp "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)" "$NGINX_CONFIG"
    echo "⚠️  Configuration not applied. Please check syntax."
    exit 1
fi

