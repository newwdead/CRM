"""
OCR Providers - Модуль для работы с различными OCR сервисами
Поддерживает: Tesseract, Parsio, Google Cloud Vision
"""
import os
import io
import re
import time
import json
import base64
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import requests
from urllib.parse import urlparse

# Import caching utilities
from .cache import get_cache_key, get_from_cache, set_to_cache

# Настройка логирования
logger = logging.getLogger(__name__)


class OCRProvider(ABC):
    """Базовый класс для OCR провайдеров"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.priority = 0  # Чем ниже, тем выше приоритет
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности провайдера"""
        pass
    
    @abstractmethod
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """Распознавание текста с изображения"""
        pass
    
    def normalize_result(self, raw_data: Any) -> Dict[str, Optional[str]]:
        """Нормализация результата в стандартный формат"""
        return {
            "full_name": None,
            "company": None,
            "position": None,
            "email": None,
            "phone": None,
            "address": None,
            "website": None,
        }


class TesseractProvider(OCRProvider):
    """Tesseract OCR - локальный, бесплатный"""
    
    def __init__(self):
        super().__init__("Tesseract")
        self.priority = 3  # Низкий приоритет (используется последним)
        self.languages = os.getenv("TESSERACT_LANGS", "eng+rus")
    
    def is_available(self) -> bool:
        """Проверка наличия Tesseract"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            return False
    
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """Распознавание через Tesseract с мультипасс обработкой"""
        try:
            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            texts = []
            
            # Оригинал
            texts.append(pytesseract.image_to_string(img, lang=self.languages))
            
            # Grayscale + threshold
            gray = ImageOps.grayscale(img)
            texts.append(pytesseract.image_to_string(gray, lang=self.languages))
            thr = gray.point(lambda p: 255 if p > 180 else 0)
            texts.append(pytesseract.image_to_string(thr, lang=self.languages))
            
            # Slight blur
            blur = gray.filter(ImageFilter.MedianFilter(size=3))
            texts.append(pytesseract.image_to_string(blur, lang=self.languages))
            
            # Different PSM modes
            for psm in (6, 7):
                texts.append(pytesseract.image_to_string(
                    img, lang=self.languages, config=f"--psm {psm}"
                ))
            
            # Объединение уникальных строк
            combined = []
            seen = set()
            for t in texts:
                for line in t.splitlines():
                    line = line.strip()
                    if line and line not in seen:
                        seen.add(line)
                        combined.append(line)
            
            combined_text = "\n".join(combined)
            
            return {
                "provider": self.name,
                "raw_text": combined_text,
                "data": self._parse_text(combined_text),
                "confidence": 0.7,  # Примерная уверенность для Tesseract
            }
            
        except Exception as e:
            logger.error(f"Tesseract recognition failed: {e}")
            raise
    
    def _parse_text(self, text: str) -> Dict[str, Optional[str]]:
        """Парсинг текста и извлечение полей"""
        data = {
            "full_name": None,
            "company": None,
            "position": None,
            "email": None,
            "phone": None,
            "address": None,
            "website": None,
        }
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            data["email"] = email_match.group(0)
        
        # Phone
        phone_match = re.search(r'(\+?\d[\d\s\-\(\)]{6,}\d)', text)
        if phone_match:
            data["phone"] = phone_match.group(0).strip()
        
        # Website
        website_match = re.search(r'(https?://[^\s]+|www\.[^\s]+\.[a-zA-Z]{2,})', text, re.IGNORECASE)
        if website_match:
            data["website"] = website_match.group(0)
        
        # Lines processing
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        candidate_lines = [
            l for l in lines 
            if (not data['email'] or data['email'] not in l)
            and (not data['phone'] or data['phone'] not in l)
            and (not data['website'] or data['website'] not in l)
        ]
        
        if candidate_lines:
            data["full_name"] = candidate_lines[0]
        if len(candidate_lines) > 1:
            data["company"] = candidate_lines[1]
        if len(candidate_lines) > 2:
            data["position"] = candidate_lines[2]
        
        # Address
        for l in lines:
            if re.search(
                r'\d+\s+.+(Street|St\.|Ave|Road|Rd\.|ул\.|просп|пер\.|straße|str\.|бул\.)',
                l,
                re.IGNORECASE
            ):
                data["address"] = l
                break
        
        return data


class ParsioProvider(OCRProvider):
    """Parsio - облачный OCR с высокой точностью"""
    
    def __init__(self):
        super().__init__("Parsio")
        self.priority = 1  # Высокий приоритет
        self.api_url = os.getenv("PARSIO_API_URL")
        self.api_key = os.getenv("PARSIO_API_KEY")
        self.timeout = float(os.getenv("PARSIO_TIMEOUT", "30"))
        self.poll_interval = float(os.getenv("PARSIO_POLL_INTERVAL", "2.0"))
        self.poll_max_attempts = int(os.getenv("PARSIO_POLL_MAX_ATTEMPTS", "20"))
    
    def is_available(self) -> bool:
        """Проверка настроек Parsio"""
        return bool(self.api_url and self.api_key)
    
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """Распознавание через Parsio API"""
        if not self.is_available():
            raise ValueError("Parsio not configured")
        
        # Подготовка заголовков
        header_name = os.getenv("PARSIO_AUTH_HEADER_NAME", "X-API-Key")
        header_value_tpl = os.getenv("PARSIO_AUTH_HEADER_VALUE", "{key}")
        header_value = header_value_tpl.replace("{key}", self.api_key)
        headers = {header_name: header_value}
        
        # Загрузка файла
        files = {'file': (filename or 'upload.jpg', io.BytesIO(image_data), 'image/jpeg')}
        
        try:
            resp = requests.post(self.api_url, headers=headers, files=files, timeout=self.timeout)
            
            # Попытка с альтернативным именем поля
            if resp.status_code >= 400:
                files = {'document': (filename or 'upload.jpg', io.BytesIO(image_data), 'image/jpeg')}
                resp = requests.post(self.api_url, headers=headers, files=files, timeout=self.timeout)
            
            if resp.status_code >= 400:
                raise RuntimeError(f"Parsio request failed: {resp.status_code} {resp.text[:200]}")
            
            data = resp.json() if resp.text else {}
            
            # Попытка извлечь данные напрямую
            candidate = self._extract_candidate(data)
            if candidate:
                normalized = self._normalize_parsio_data(candidate)
                if any(normalized.values()):
                    return {
                        "provider": self.name,
                        "raw_data": data,
                        "data": normalized,
                        "confidence": 0.9,
                    }
            
            # Polling document endpoint
            doc_id = self._extract_doc_id(resp, data)
            if doc_id:
                return self._poll_document(doc_id, headers)
            
            raise RuntimeError("Parsio: no data and no document ID")
            
        except Exception as e:
            logger.error(f"Parsio recognition failed: {e}")
            raise
    
    def _extract_candidate(self, obj: Any) -> Optional[Dict]:
        """Извлечение кандидата из ответа"""
        if isinstance(obj, dict):
            for key in ("data", "result", "fields", "document", "parsed"):
                if key in obj and isinstance(obj[key], (dict, list)):
                    cand = obj[key]
                    if isinstance(cand, list) and cand:
                        cand = cand[0]
                    if isinstance(cand, dict):
                        return cand
            return obj
        return None
    
    def _extract_doc_id(self, response, data: Any) -> Optional[str]:
        """Извлечение ID документа"""
        # Из Location header
        loc = response.headers.get('Location') or response.headers.get('location')
        if loc:
            try:
                parts = urlparse(loc).path.strip('/').split('/')
                for seg in ('documents', 'docs'):
                    if seg in parts:
                        idx = parts.index(seg)
                        if idx + 1 < len(parts):
                            return parts[idx + 1]
            except Exception:
                pass
        
        # Из тела ответа
        if isinstance(data, dict):
            for key in ['id', 'doc_id', 'document_id', '_id']:
                if key in data:
                    return str(data[key])
        
        return None
    
    def _poll_document(self, doc_id: str, headers: Dict) -> Dict[str, Any]:
        """Polling документа до готовности"""
        doc_url_tpl = os.getenv("PARSIO_DOCUMENT_URL_TEMPLATE", "https://api.parsio.io/docs/{id}")
        url = doc_url_tpl.format(id=doc_id)
        
        for _ in range(self.poll_max_attempts):
            try:
                r = requests.get(url, headers=headers, timeout=self.timeout)
                if r.status_code < 400:
                    dj = r.json()
                    cand = self._extract_candidate(dj)
                    if cand:
                        normalized = self._normalize_parsio_data(cand)
                        if any(normalized.values()):
                            return {
                                "provider": self.name,
                                "raw_data": dj,
                                "data": normalized,
                                "confidence": 0.9,
                            }
            except Exception:
                pass
            
            time.sleep(self.poll_interval)
        
        raise RuntimeError("Parsio document not ready after polling")
    
    def _normalize_parsio_data(self, obj: Dict) -> Dict[str, Optional[str]]:
        """Нормализация данных Parsio"""
        def first_of_list(value):
            return value[0] if isinstance(value, list) and value else value
        
        def pick(d, keys):
            for k in keys:
                if k in d and d[k]:
                    return first_of_list(d[k])
            return None
        
        result = {
            "full_name": pick(obj, ["full_name", "name", "person", "contact_name"]),
            "position": pick(obj, ["position", "title", "job_title", "role"]),
            "email": pick(obj, ["email", "e_mail", "mail"]),
            "phone": pick(obj, ["phone", "phone_number", "mobile", "tel"]),
            "address": pick(obj, ["address", "location", "addr"]),
            "company": pick(obj, ["company", "organization", "org"]),
            "website": pick(obj, ["website", "url", "web"]),
        }
        
        # Parsio specific fields
        if not result["full_name"] and "ContactNames" in obj:
            names = obj["ContactNames"]
            if isinstance(names, list) and names:
                cn = names[0]
                if isinstance(cn, dict):
                    result["full_name"] = cn.get("_source") or " ".join(
                        [cn.get("FirstName", ""), cn.get("LastName", "")]
                    ).strip()
        
        if not result["email"] and "Emails" in obj:
            emails = obj["Emails"]
            if isinstance(emails, list) and emails:
                result["email"] = emails[0]
        
        if not result["position"] and "JobTitles" in obj:
            titles = obj["JobTitles"]
            if isinstance(titles, list) and titles:
                result["position"] = titles[0]
        
        if not result["phone"]:
            if "MobilePhones" in obj and obj["MobilePhones"]:
                result["phone"] = first_of_list(obj["MobilePhones"])
            elif "WorkPhones" in obj and obj["WorkPhones"]:
                result["phone"] = first_of_list(obj["WorkPhones"])
        
        if not result["company"] and "CompanyNames" in obj:
            companies = obj["CompanyNames"]
            if isinstance(companies, list):
                for c in companies:
                    if isinstance(c, str) and c.strip():
                        result["company"] = c.strip()
                        break
        
        if not result["website"] and "Websites" in obj:
            sites = obj["Websites"]
            if isinstance(sites, list) and sites:
                result["website"] = sites[0]
        
        return result


class GoogleVisionProvider(OCRProvider):
    """Google Cloud Vision API - высокая точность"""
    
    def __init__(self):
        super().__init__("Google Vision")
        self.priority = 2  # Средний приоритет
        self.api_key = os.getenv("GOOGLE_VISION_API_KEY")
        self.endpoint = "https://vision.googleapis.com/v1/images:annotate"
    
    def is_available(self) -> bool:
        """Проверка настроек Google Vision"""
        return bool(self.api_key)
    
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """Распознавание через Google Vision API"""
        if not self.is_available():
            raise ValueError("Google Vision not configured")
        
        # Кодирование изображения в base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Запрос к API
        payload = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "TEXT_DETECTION"},
                    {"type": "DOCUMENT_TEXT_DETECTION"}
                ]
            }]
        }
        
        try:
            resp = requests.post(
                f"{self.endpoint}?key={self.api_key}",
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            
            result = resp.json()
            
            if "responses" not in result or not result["responses"]:
                raise ValueError("No response from Google Vision")
            
            response = result["responses"][0]
            
            # Извлечение текста
            text = ""
            if "fullTextAnnotation" in response:
                text = response["fullTextAnnotation"]["text"]
            elif "textAnnotations" in response and response["textAnnotations"]:
                text = response["textAnnotations"][0]["description"]
            
            if not text:
                raise ValueError("No text detected by Google Vision")
            
            # Парсинг
            parsed_data = self._parse_text(text)
            
            return {
                "provider": self.name,
                "raw_data": result,
                "raw_text": text,
                "data": parsed_data,
                "confidence": 0.95,
            }
            
        except Exception as e:
            logger.error(f"Google Vision recognition failed: {e}")
            raise
    
    def _parse_text(self, text: str) -> Dict[str, Optional[str]]:
        """Парсинг текста Google Vision (аналогично Tesseract)"""
        # Используем ту же логику что и в Tesseract
        tesseract = TesseractProvider()
        return tesseract._parse_text(text)


class OCRManager:
    """Менеджер OCR провайдеров с fallback"""
    
    def __init__(self):
        self.providers: List[OCRProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Инициализация всех доступных провайдеров"""
        # Создаем все провайдеры
        all_providers = [
            TesseractProvider(),
            ParsioProvider(),
            GoogleVisionProvider(),
        ]
        
        # Фильтруем только доступные
        for provider in all_providers:
            if provider.is_available():
                self.providers.append(provider)
                logger.info(f"OCR Provider initialized: {provider.name} (priority: {provider.priority})")
            else:
                logger.warning(f"OCR Provider not available: {provider.name}")
        
        # Сортируем по приоритету
        self.providers.sort(key=lambda p: p.priority)
        
        if not self.providers:
            logger.error("No OCR providers available!")
    
    def recognize(
        self,
        image_data: bytes,
        filename: str = None,
        preferred_provider: str = None
    ) -> Dict[str, Any]:
        """
        Распознавание с автоматическим fallback
        
        Args:
            image_data: Байты изображения
            filename: Имя файла (опционально)
            preferred_provider: Предпочитаемый провайдер (опционально)
        
        Returns:
            Dict с результатами распознавания
        """
        if not self.providers:
            raise RuntimeError("No OCR providers available")
        
        # Check cache first
        cache_key = get_cache_key("ocr", image_data, preferred_provider or "auto")
        cached_result = get_from_cache(cache_key)
        if cached_result:
            logger.info("OCR result retrieved from cache")
            return cached_result
        
        # Если указан предпочитаемый провайдер, пробуем его первым
        providers_to_try = list(self.providers)
        if preferred_provider:
            preferred = next((p for p in self.providers if p.name.lower() == preferred_provider.lower()), None)
            if preferred:
                providers_to_try.remove(preferred)
                providers_to_try.insert(0, preferred)
        
        errors = []
        
        # Пробуем каждый провайдер по очереди
        for provider in providers_to_try:
            try:
                logger.info(f"Trying OCR provider: {provider.name}")
                result = provider.recognize(image_data, filename)
                
                # Проверяем что есть хоть какие-то данные
                if result.get("data") and any(result["data"].values()):
                    logger.info(f"Successfully recognized with {provider.name}")
                    # Cache the result for 24 hours
                    set_to_cache(cache_key, result, ttl=86400)
                    return result
                else:
                    logger.warning(f"{provider.name} returned empty data")
                    errors.append(f"{provider.name}: empty data")
                    
            except Exception as e:
                logger.warning(f"{provider.name} failed: {e}")
                errors.append(f"{provider.name}: {str(e)}")
                continue
        
        # Если все провайдеры не сработали
        raise RuntimeError(
            f"All OCR providers failed. Errors: {'; '.join(errors)}"
        )
    
    def get_available_providers(self) -> List[str]:
        """Получить список доступных провайдеров"""
        return [p.name for p in self.providers]
    
    def get_provider_info(self) -> List[Dict[str, Any]]:
        """Получить информацию о провайдерах"""
        return [
            {
                "name": p.name,
                "priority": p.priority,
                "available": p.is_available()
            }
            for p in sorted(self.providers, key=lambda x: x.priority)
        ]

