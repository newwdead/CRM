import pytesseract
from PIL import Image, ImageOps, ImageFilter
import re
import os
import time
import requests
from urllib.parse import urlparse

def clean_lines(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines

def parse_text(text):
    data = {
        "full_name": None,
        "company": None,
        "position": None,
        "email": None,
        "phone": None,
        "address": None,
    }

    # email and phone
    email = re.search(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', text)
    phone = re.search(r'(\+?\d[\d\s\-\(\)]{6,}\d)', text)
    if email:
        data["email"] = email.group(0)
    if phone:
        data["phone"] = phone.group(0).strip()

    lines = clean_lines(text)
    # heuristics: first non-email/phone line as name, next as company/position
    candidate_lines = [l for l in lines if (data['email'] not in l if data['email'] else True) and (data['phone'] not in l if data['phone'] else True)]
    if candidate_lines:
        data["full_name"] = candidate_lines[0]
    if len(candidate_lines) > 1:
        data["company"] = candidate_lines[1]
    if len(candidate_lines) > 2:
        data["position"] = candidate_lines[2]
    # address: line containing street or digits and common street keywords
    for l in lines:
        if re.search(r'\d+\s+.+(Street|St\.|Ave|Road|Rd\.|ул\.|просп|пер\.|straße|str\.|бул\.)', l, re.IGNORECASE):
            data["address"] = l
            break
    return data

def ocr_image_fileobj(fileobj):
    # Tesseract supports multiple languages; make sure langs are installed in container: eng + rus
    img = Image.open(fileobj)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    texts = []

    # Original
    texts.append(pytesseract.image_to_string(img, lang="eng+rus"))

    # Grayscale + threshold
    gray = ImageOps.grayscale(img)
    texts.append(pytesseract.image_to_string(gray, lang="eng+rus"))
    thr = gray.point(lambda p: 255 if p > 180 else 0)
    texts.append(pytesseract.image_to_string(thr, lang="eng+rus"))

    # Slight blur to reduce noise
    blur = gray.filter(ImageFilter.MedianFilter(size=3))
    texts.append(pytesseract.image_to_string(blur, lang="eng+rus"))

    # Try different page segmentation modes
    for psm in (6, 7):
        texts.append(pytesseract.image_to_string(img, lang="eng+rus", config=f"--psm {psm}"))

    # Merge unique lines across passes
    combined = []
    seen = set()
    for t in texts:
        for line in t.splitlines():
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                combined.append(line)
    combined_text = "\n".join(combined)
    return parse_text(combined_text)

def _normalize_contact(obj: dict):
    """Normalize various external OCR/Parser response schemas into our Contact shape.
    Supports flat keys and Parsio-like arrays (ContactNames, Emails, JobTitles, MobilePhones, WorkPhones, Departments).
    """

    def first_of_list(value):
        if isinstance(value, list) and value:
            return value[0]
        return value

    def pick(d, keys):
        for k in keys:
            if k in d and d[k]:
                return first_of_list(d[k])
        return None

    # Start with flat picks
    full_name = pick(obj, ["full_name","name","person","contact_name"]) or None
    position = pick(obj, ["position","title","job_title","role"]) or None
    email = pick(obj, ["email","e_mail","mail"]) or None
    phone = pick(obj, ["phone","phone_number","mobile","tel"]) or None
    address = pick(obj, ["address","location","addr"]) or None
    company = pick(obj, ["company","organization","org","employer"]) or None
    comment = pick(obj, ["comment","notes","note"]) or None

    # Parsio-style arrays and nested structures
    # ContactNames: [{ _source: "...", FirstName: "...", LastName: "..." }]
    if not full_name and isinstance(obj.get("ContactNames"), list) and obj["ContactNames"]:
        cn = obj["ContactNames"][0]
        if isinstance(cn, dict):
            # Prefer _source; else concatenate available parts
            full_name = cn.get("_source") or " ".join([p for p in [cn.get("FirstName"), cn.get("LastName")] if p]) or None

    # Emails / JobTitles / Phones / Departments
    if not email and isinstance(obj.get("Emails"), list) and obj["Emails"]:
        email = obj["Emails"][0]
    if not position and isinstance(obj.get("JobTitles"), list) and obj["JobTitles"]:
        position = obj["JobTitles"][0]
    # Prefer mobile; fallback to work
    if not phone:
        if isinstance(obj.get("MobilePhones"), list) and obj["MobilePhones"]:
            phone = obj["MobilePhones"][0]
        elif isinstance(obj.get("WorkPhones"), list) and obj["WorkPhones"]:
            phone = obj["WorkPhones"][0]
    # Use departments as comment if present
    if not comment and isinstance(obj.get("Departments"), list) and obj["Departments"]:
        comment = ", ".join([str(x) for x in obj["Departments"] if x])

    # CompanyNames (Parsio) → company
    if not company and isinstance(obj.get("CompanyNames"), list) and obj["CompanyNames"]:
        # pick first non-empty
        for v in obj["CompanyNames"]:
            if isinstance(v, str) and v.strip():
                company = v.strip()
                break

    # Websites (Parsio) → append to comment if present
    if isinstance(obj.get("Websites"), list) and obj["Websites"]:
        sites = ", ".join([s for s in obj["Websites"] if isinstance(s, str) and s.strip()])
        if sites:
            if comment:
                comment = f"{comment}; {sites}"
            else:
                comment = sites

    return {
        "full_name": full_name,
        "company": company,
        "position": position,
        "email": email,
        "phone": phone,
        "address": address,
        "comment": comment,
    }

def ocr_parsio(fileobj, filename: str | None = None):
    url = os.getenv("PARSIO_API_URL")
    api_key = os.getenv("PARSIO_API_KEY")
    if not url or not api_key:
        raise RuntimeError("Parsio is not configured: PARSIO_API_URL and PARSIO_API_KEY are required")

    header_name = os.getenv("PARSIO_AUTH_HEADER_NAME", "Authorization")
    header_value_tpl = os.getenv("PARSIO_AUTH_HEADER_VALUE", "Bearer {key}")
    header_value = header_value_tpl.replace("{key}", api_key)
    headers = {header_name: header_value}

    files_primary = {
        'file': (filename or 'upload.jpg', fileobj, 'application/octet-stream')
    }
    try:
        timeout = float(os.getenv("PARSIO_TIMEOUT", "30"))
    except ValueError:
        timeout = 30.0

    # Try primary field name 'file'; on 4xx retry with 'document'
    resp = requests.post(url, headers=headers, files=files_primary, timeout=timeout)
    if resp.status_code >= 400:
        try:
            fileobj.seek(0)
        except Exception:
            pass
        files_alt = {
            'document': (filename or 'upload.jpg', fileobj, 'application/octet-stream')
        }
        resp = requests.post(url, headers=headers, files=files_alt, timeout=timeout)
    if resp.status_code >= 400:
        raise RuntimeError(f"Parsio request failed: {resp.status_code} {resp.text[:200]}")
    try:
        data = resp.json()
    except Exception:
        # Some Parsio endpoints may return plain text (e.g., an id) or empty body
        try:
            data = resp.text or ""
        except Exception:
            data = {}

    # Collect debug info
    debug = {
        'upload_status': resp.status_code,
        'upload_location': resp.headers.get('Location') or resp.headers.get('location'),
        'initial_top_keys': list(data.keys()) if isinstance(data, dict) else (type(data).__name__),
        'mailbox_list_status': None,
        'mailbox_list_suffix': None,
    }

    # Try to locate contact-like object immediately
    def extract_candidate(obj):
        cand = None
        if isinstance(obj, dict):
            for key in ("data","result","fields","document","parsed","payload","json"):
                if key in obj and isinstance(obj[key], (dict,list)):
                    cand = obj[key]
                    break
            if cand is None:
                cand = obj
        elif isinstance(obj, list) and obj:
            cand = obj[0]
        if isinstance(cand, list) and cand:
            cand = cand[0]
        return cand if isinstance(cand, dict) else None

    candidate = extract_candidate(data)
    if candidate:
        normalized = _normalize_contact(candidate)
        if any(normalized.values()):
            return normalized

    # If immediate data not present, poll document endpoint using returned id
    def extract_id(obj):
        # Deep traversal looking for any *id key
        stack = [obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                # direct id-like keys
                for k, v in cur.items():
                    if isinstance(k, str) and 'id' in k.lower():
                        if v:
                            return v
                # enqueue values
                for v in cur.values():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(cur, list):
                for it in cur:
                    if isinstance(it, (dict, list)):
                        stack.append(it)
        return None

    # Try Location header first: /documents/{id}
    doc_id = None
    loc = resp.headers.get('Location') or resp.headers.get('location')
    if loc:
        try:
            p = urlparse(loc)
            parts = p.path.strip('/').split('/')
            for seg in ('documents','docs'):
                if seg in parts:
                    idx = parts.index(seg)
                    if idx + 1 < len(parts):
                        doc_id = parts[idx+1]
                        break
        except Exception:
            doc_id = None
    if not doc_id:
        # try to extract id from JSON or plain string body
        if isinstance(data, (dict, list)):
            doc_id = extract_id(data)
        elif isinstance(data, str):
            import re
            m = re.search(r"[a-f0-9]{24}", data, re.IGNORECASE)
            if m:
                doc_id = m.group(0)
    if not doc_id:
        # Try to fetch the latest document from the mailbox if URL includes mailbox id
        mailbox_id = os.getenv("PARSIO_MAILBOX_ID")
        if not mailbox_id:
            try:
                p = urlparse(url)
                parts = p.path.strip('/').split('/')
                if 'mailboxes' in parts:
                    idx = parts.index('mailboxes')
                    if idx + 1 < len(parts):
                        mailbox_id = parts[idx+1]
            except Exception:
                mailbox_id = None
        if mailbox_id:
            for suffix in ("documents","docs"):
                list_url = f"https://api.parsio.io/mailboxes/{mailbox_id}/{suffix}"
                lr = requests.get(list_url, headers=headers, timeout=timeout)
                debug['mailbox_list_status'] = lr.status_code
                debug['mailbox_list_suffix'] = suffix
                if lr.status_code < 400:
                    try:
                        lj = lr.json()
                        items = None
                        if isinstance(lj, list):
                            items = lj
                        elif isinstance(lj, dict):
                            for k in ("documents","docs","items","results","data"):
                                if k in lj and isinstance(lj[k], list):
                                    items = lj[k]
                                    break
                            if not items:
                                # maybe doc-like dict
                                doc_id = extract_id(lj)
                                if doc_id:
                                    break
                        if items and len(items):
                            cand = items[0]
                            if isinstance(cand, dict):
                                doc_id = extract_id(cand) or cand.get('_id') or cand.get('id')
                            else:
                                doc_id = extract_id(cand)
                            if doc_id:
                                break
                    except Exception:
                        pass
    if not doc_id:
        raise RuntimeError(f"Parsio response format unsupported: no fields and no document id | debug={debug}")

    doc_url_tpl = os.getenv("PARSIO_DOCUMENT_URL_TEMPLATE", "https://api.parsio.io/docs/{id}")
    poll_interval = float(os.getenv("PARSIO_POLL_INTERVAL", "2.0"))
    max_attempts = int(os.getenv("PARSIO_POLL_MAX_ATTEMPTS", "20"))

    for _ in range(max_attempts):
        r = requests.get(doc_url_tpl.format(id=doc_id), headers=headers, timeout=timeout)
        if r.status_code >= 400:
            time.sleep(poll_interval)
            continue
        try:
            dj = r.json()
        except Exception:
            time.sleep(poll_interval)
            continue
        cand = extract_candidate(dj)
        if cand:
            normalized = _normalize_contact(cand)
            if any(normalized.values()):
                return normalized
        time.sleep(poll_interval)

    # Include debug context for troubleshooting
    debug['final_doc_id'] = doc_id
    raise RuntimeError(f"Parsio document not ready or contained no fields after polling | debug={debug}")
