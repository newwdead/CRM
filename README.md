# 📇 BizCard CRM - Business Card Management System

> **Full-featured CRM system with OCR recognition and Telegram integration**

![Version](https://img.shields.io/badge/version-1.7-blue)
![Python](https://img.shields.io/badge/python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![React](https://img.shields.io/badge/React-18-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![UI](https://img.shields.io/badge/UI-Modern-brightgreen)

[**Русская документация**](README.ru.md) | [English Documentation](README.md)

---

## 🎯 About

BizCard CRM is a modern web-based contact management system specializing in automatic business card recognition. The system allows you to:

- 📸 **Upload business card photos** via web interface or Telegram
- 🤖 **Automatically recognize text** using multiple OCR providers with fallback
- 💼 **Manage contacts** in a modern, responsive interface
- 📱 **Integrate with Telegram** for instant card processing
- 📊 **Export data** to CSV and XLSX formats
- 🔍 **Search and filter** contacts
- 🎨 **Modern UI/UX** with drag & drop and modal dialogs
- ⚙️ **Web-based settings** for all system parameters

---

## ✨ Features

### 🖼️ OCR Recognition
- Multiple OCR providers: **Tesseract** (local, free), **Parsio** (cloud), **Google Vision** (cloud)
- **Auto mode** with intelligent fallback between providers
- Web-based OCR provider management and configuration
- Multi-pass image processing for better accuracy
- Support for Russian and English languages
- Images up to 20 MB
- Confidence scoring for OCR results

### 📱 Telegram Integration
- Automatic photo processing from Telegram
- Two modes: **webhook** (production) and **polling** (development)
- Configurable allowed chats
- OCR provider selection
- Systemd service for auto-start

### 💾 Contact Management
- Full CRUD operations
- Bulk update/delete with modal forms
- Inline comment editing
- Photo attachments
- Unique identifiers (UID)
- Real-time statistics (total, with email, with phone)
- Quick actions (email, phone, website links)
- Select all/deselect all functionality

### 📊 Import/Export
- Import from CSV and XLSX with **drag & drop**
- Export to CSV and XLSX
- Export selected contacts
- Visual progress indicators
- Status modals with detailed feedback

### 🎨 Modern UI/UX (NEW in v1.7)
- **Responsive design** for all devices (mobile, tablet, desktop)
- **Drag & drop** file uploads
- **Modal dialogs** for results and forms
- **Tab-based settings** (General, OCR, Telegram)
- **CSS variables** for consistent theming
- **Smooth animations** and transitions
- **Loading spinners** for async operations
- **Badges and alerts** for visual feedback

### ⚙️ Web Settings (NEW in v1.7)
- Interface language selection
- Default OCR provider configuration
- Notification preferences
- Auto-refresh settings
- OCR provider status dashboard
- Telegram bot configuration
- All settings managed through web UI

---

## 🛠️ Technology Stack

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Tesseract OCR  
**Frontend:** React 18, Create React App  
**Infrastructure:** Docker, Docker Compose, Nginx, SSL/TLS

---

## 📁 Project Structure

```
fastapi-bizcard-crm-ready/
│
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py      # Main app, CRUD endpoints, OCR processing
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── database.py  # Database configuration
│   │   └── ocr_utils.py # OCR functionality
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── App.js
│   │   └── index.js
│   ├── nginx.conf       # Nginx configuration
│   ├── package.json
│   └── Dockerfile
│
├── uploads/             # Uploaded business card photos
├── docker-compose.yml   # Docker Compose config
├── telegram_polling.py  # Telegram polling script
├── .env.example         # Environment variables template
│
├── README.md            # Documentation (English)
├── README.ru.md         # Documentation (Russian)
├── SSL_SETUP.md         # SSL setup guide
└── TELEGRAM_SETUP.md    # Telegram integration guide
```

---

## 🚀 Quick Start

### Prerequisites

- Docker (v20.10+)
- Docker Compose (v2.0+)
- 4 GB RAM
- 10 GB disk space

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/fastapi-bizcard-crm.git
cd fastapi-bizcard-crm-ready

# 2. (Optional) Create .env file
cp .env.example .env
# Edit .env if needed

# 3. Build and start containers
docker compose up -d --build

# 4. Wait for startup (30-60 seconds)
docker compose logs -f

# 5. Open in browser
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
# HTTPS:     https://localhost:8443
```

### Health Check

```bash
# Check container status
docker compose ps

# Check health endpoint
curl http://localhost:8000/health

# View logs
docker compose logs backend
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in project root:

```ini
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/bizcard_crm
POSTGRES_PASSWORD=your_secure_password

# Parsio Cloud OCR (optional)
PARSIO_API_KEY=your_api_key
PARSIO_API_URL=https://api.parsio.io/mailboxes/<id>/upload

# Application
APP_VERSION=v1.6
TZ=Europe/Moscow
```

### Telegram Setup

1. Create bot via [@BotFather](https://t.me/BotFather)
2. Get token
3. Configure via API:

```bash
curl -X PUT http://localhost:8000/settings/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "token": "your_token",
    "allowed_chats": "123456789",
    "provider": "tesseract"
  }'
```

4. Start polling service:

```bash
sudo systemctl enable telegram-polling
sudo systemctl start telegram-polling
```

See [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) for details.

---

## 📖 API Documentation

Interactive API documentation is automatically generated:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Main Endpoints

```http
GET    /contacts/              # List all contacts
GET    /contacts/{id}          # Get contact by ID
POST   /contacts/              # Create contact
PUT    /contacts/{id}          # Update contact
DELETE /contacts/{id}          # Delete contact
POST   /contacts/delete_bulk   # Bulk delete
PUT    /contacts/update_bulk   # Bulk update

POST   /upload/?provider=tesseract  # Upload & OCR

GET    /contacts/export        # Export to CSV
GET    /contacts/export/xlsx   # Export to XLSX
POST   /contacts/import        # Import from CSV/XLSX

GET    /settings/telegram      # Get Telegram settings
PUT    /settings/telegram      # Update Telegram settings
POST   /telegram/webhook       # Telegram webhook endpoint

GET    /health                 # Health check
GET    /version                # App version
```

---

## 🔒 SSL and HTTPS

### Self-signed Certificate (development)

```bash
# Create directory
sudo mkdir -p /etc/nginx/certs

# Generate certificate
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/nginx/certs/selfsigned.key \
  -out /etc/nginx/certs/selfsigned.crt \
  -days 365 \
  -subj "/CN=localhost/O=BizCard CRM/C=US"

# Restart frontend
docker compose restart frontend
```

See [SSL_SETUP.md](SSL_SETUP.md) for production setup with Let's Encrypt.

---

## 🚢 Deployment

### Production with Docker Compose

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Backup

```bash
# Backup database
docker compose exec db pg_dump -U postgres bizcard_crm > backup.sql

# Backup uploads
tar -czf uploads_backup.tar.gz uploads/
```

---

## 🐛 Troubleshooting

### Containers don't start

```bash
docker compose logs
docker compose down -v
docker compose up -d --build
```

### Database connection error

```bash
docker compose exec db psql -U postgres -c "SELECT version();"
docker compose exec backend env | grep DATABASE_URL
```

### Tesseract doesn't recognize Russian

```bash
docker compose exec backend tesseract --list-langs
# Should show: eng, rus

docker compose build backend
```

### Telegram not receiving messages

```bash
sudo systemctl status telegram-polling
sudo journalctl -u telegram-polling -f
curl http://localhost:8000/settings/telegram
```

---

## 📝 License

MIT License

---

## 👥 Support

- 📧 Email: support@example.com
- 💬 Telegram: @yourusername
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/fastapi-bizcard-crm/issues)

---

**Made with ❤️ for business card automation**
