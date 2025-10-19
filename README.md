# fastapi-bizcard-crm (production-ready)

**What**: Business-card OCR + CRM. React frontend (multi-language RU/EN) served by Nginx, FastAPI backend (Gunicorn+Uvicorn) with Tesseract OCR built into the container. SQLite used for storage (file `./data/contacts.db`).

## Quick start (Linux / macOS / Windows with Docker Desktop)
1. Unzip or clone this project.
2. Build and run (production build):
```bash
docker-compose build
docker-compose up -d
```
3. Open frontend: http://localhost:3000  
   API /docs (FastAPI): http://localhost:8000/docs

## Notes
- Tesseract is installed in backend image (languages: eng + rus). If you need extra languages, install them into the container or into the host Tesseract.
- Data file is persisted into `./data/contacts.db` on the host because of the volume mapping in docker-compose.
- To stop and remove containers:
```bash
docker-compose down
```

# System Overview

This repository provides a production-ready Business Card OCR + lightweight CRM.

- **Frontend**: React SPA (RU/EN), built and served by Nginx (`frontend/`).
- **Backend**: FastAPI served by Gunicorn+Uvicorn (`backend/`).
- **DB**: PostgreSQL (via Docker Compose service `db`).
- **OCR Providers**:
  - Local: Tesseract (eng+rus) with multi-pass preprocessing.
  - Cloud: Parsio (via API, mailbox upload + document polling).

# Architecture

- **Containers** (see `docker-compose.yml`):
  - `db`: PostgreSQL 15.
  - `backend`: Python 3.10-slim + FastAPI + Gunicorn + Uvicorn; Tesseract installed (`eng`, `rus`).
  - `frontend`: Nginx serving a production React build.

- **Backend modules** (key files):
  - `backend/app/main.py` – FastAPI app, CRUD endpoints, upload OCR, import/export, bulk ops.
  - `backend/app/models.py` – SQLAlchemy models (`Contact`).
  - `backend/app/database.py` – SQLAlchemy engine & session; reads `DATABASE_URL`.
  - `backend/app/ocr_utils.py` – OCR with Tesseract and Parsio integration.

- **Frontend components**:
  - `frontend/src/components/UploadCard.js` – upload form with provider selector (Tesseract/Parsio).
  - `frontend/src/components/ContactList.js` – list, search, add, inline edit (`comment`), bulk edit/delete.
  - `frontend/src/components/ImportExport.js` – CSV/XLSX import/export (if present).

# Features

- **Contacts CRUD** with fields: `full_name`, `company`, `position`, `email`, `phone`, `address`, `comment`.
- **Upload & OCR** for business cards:
  - Select provider in UI: Tesseract (local) or Parsio (cloud).
  - File size limit: 10MB; content-type must be image/*.
  - Tesseract: multi-pass (grayscale, threshold, median blur, PSM variants), languages `eng+rus`.
  - Parsio: POST to mailbox upload, then poll document until fields are ready.
- **Import** contacts from CSV/XLSX; **NaN** normalized to `null`.
- **Export** contacts to CSV and XLSX (in-memory streaming).
- **Bulk actions**: delete and update selected contacts.
- **Inline edit** for `comment` directly in the table.

# Environment

Create `.env` in project root (Compose auto-loads it). Important variables:

```ini
# Database (default provided via docker-compose)
DATABASE_URL=postgresql://postgres:password@db:5432/bizcard_crm

# Parsio (Cloud OCR)
PARSIO_API_KEY=YOUR_PARSIO_API_KEY
# Mailbox upload endpoint, e.g.
PARSIO_API_URL=https://api.parsio.io/mailboxes/<mailbox_id>/upload
# Document fetch template (defaults to https://api.parsio.io/docs/{id})
PARSIO_DOCUMENT_URL_TEMPLATE=https://api.parsio.io/docs/{id}
PARSIO_AUTH_HEADER_NAME=X-API-Key
PARSIO_AUTH_HEADER_VALUE={key}
PARSIO_TIMEOUT=45
PARSIO_POLL_INTERVAL=2.0
PARSIO_POLL_MAX_ATTEMPTS=20

# Misc
TZ=Europe/Berlin
```

# Backend API

Base URL: `http://localhost:8000`

- `GET /contacts/` – list contacts.
- `POST /contacts/` – create (`ContactCreate`).
- `PUT /contacts/{id}` – update (`ContactUpdate`).
- `DELETE /contacts/{id}` – delete one.
- `POST /contacts/delete_bulk` – delete many; JSON body is an array of IDs, e.g. `[1,2,3]`.
- `PUT /contacts/update_bulk` – bulk update `{ "ids": [..], "fields": {..} }`.
- `POST /upload/?provider=tesseract|parsio` – upload image and OCR.
  - Multipart field: `file` (tries `document` as fallback for Parsio).
- `GET /contacts/export` – CSV download.
- `GET /contacts/export/xlsx` – XLSX download.
- `POST /contacts/import` – CSV/XLSX upload to import.

# OCR Providers

- **Tesseract (local)**
  - Installed in `backend` image: packages `tesseract-ocr`, `tesseract-ocr-rus`.
  - Preprocessing and PSM variants improve accuracy for RU/EN.

- **Parsio (cloud)**
  - Upload to `PARSIO_API_URL` (mailbox upload endpoint).
  - Extract `doc_id` from response (supports `Location` header and deep JSON scan).
  - Poll `PARSIO_DOCUMENT_URL_TEMPLATE` (default `/docs/{id}`) until fields are ready.
  - Normalizes typical fields to our schema from keys like:
    - `ContactNames`, `CompanyNames`, `Emails`, `MobilePhones`, `WorkPhones`, `JobTitles`, `Departments`, `Websites`.

# Running

Production-like (Docker):

```bash
docker compose up -d --build
# Frontend: http://localhost:3000
# Backend docs: http://localhost:8000/docs
```

Stop:

```bash
docker compose down
```

# Troubleshooting

- **Upload fails with 400 (type/size)**: ensure file is an image and ≤ 10MB.
- **Tesseract RU not recognized**: ensure `tesseract-ocr-rus` installed (already in Dockerfile).
- **Parsio 404 "Cannot POST /"**: `PARSIO_API_URL` must be a mailbox upload endpoint, e.g. `/mailboxes/<id>/upload`, not the base URL.
- **Parsio returns no fields**:
  - Increase `PARSIO_POLL_INTERVAL` / `PARSIO_POLL_MAX_ATTEMPTS`.
  - Verify `PARSIO_DOCUMENT_URL_TEMPLATE` matches your API (`/docs/{id}` or your host’s path).
  - Check that fields exist in document JSON; adjust mapping if your structure differs.
- **CORS**: backend allows `http://localhost:3000` and `http://127.0.0.1:3000`.

# Security Notes

- Do not commit `.env` with secrets.
- API keys are read from environment and sent via headers; never embed keys in frontend.

# Project Structure

```
backend/
  app/
    main.py
    models.py
    database.py
    ocr_utils.py
frontend/
  src/
    components/
      UploadCard.js
      ContactList.js
docker-compose.yml
```

