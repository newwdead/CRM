# v1.2 Release Notes

## Backend
- Parsio→Tesseract fallback: if Parsio fails or times out, automatically retry with Tesseract.
- Size limits: Parsio up to 20MB; Tesseract remains 10MB.
- Parsio accepts non-image documents: PDF/HTML/CSV/TXT/DOCX/RTF/XML in addition to images.
- Duplicate handling: new data merges into existing contact when email or phone matches (fills only empty fields).
- Pagination & sorting: `GET /contacts/?page=&size=&sort=` returns `{page,size,total,items}`.
- Health endpoint: `GET /health` returns `{ "status": "ok" }`.

## Frontend
- UploadCard: error modal with copy-to-clipboard, loading state, and success message.
- ContactList: client-side pagination controls (page/size) with server-backed pagination; simple sorting toggle by `id`.

## CI/CD
- Frontend CI: Node 18 with reliable npm cache and resilient install (npm ci if lockfile present).
- Release workflow to publish artifacts on `v*` tags.

## Notes
- Ensure Parsio credentials are configured in `.env` and compose environment if using Parsio.
- For Tesseract, only `image/*` files are supported.
