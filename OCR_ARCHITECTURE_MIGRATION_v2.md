# OCR Architecture Migration v2.0 - LayoutLMv3 + PaddleOCR

> **Дата создания**: October 26, 2025  
> **Версия**: 2.0.0  
> **Статус**: 🚀 Planning Phase

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Текущая архитектура](#текущая-архитектура)
3. [Целевая архитектура](#целевая-архитектура)
4. [План миграции](#план-миграции)
5. [Технический стек](#технический-стек)
6. [Структура проекта](#структура-проекта)
7. [Roadmap](#roadmap)

---

## 🎯 Обзор

### Проблемы текущей архитектуры

1. **Низкая точность** простого regex-парсинга после OCR
2. **Отсутствие контекстной классификации** полей визитки
3. **Нет механизма обучения** на пользовательских данных
4. **Зависимость от внешних API** (Parsio, Google Vision)
5. **Нет учета layout** визитки (расположение текста)

### Цели миграции

1. ✅ **Повысить точность** распознавания до 95%+
2. ✅ **Добавить контекстную классификацию** с помощью LayoutLMv3
3. ✅ **Создать pipeline обучения** на собственных данных
4. ✅ **Снизить зависимость от API** - использовать локальные модели
5. ✅ **Улучшить обработку layout** визиток

---

## 🏗️ Текущая архитектура

### Компоненты (v5.3.0)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend  │────▶│   FastAPI    │────▶│     OCR      │
│   (React)   │     │   Backend    │     │   Manager    │
└─────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  PostgreSQL  │     │  Providers:  │
                    │              │     │ - Tesseract  │
                    └──────────────┘     │ - Parsio     │
                                         │ - Google     │
                                         └──────────────┘
```

### Текущий flow обработки

1. **Загрузка изображения** → FastAPI endpoint
2. **QR код** → Проверка QR кода (если есть)
3. **OCR** → Один из провайдеров (Tesseract/Parsio/Google)
4. **Regex парсинг** → Извлечение полей (email, phone, name, etc.)
5. **Сохранение** → PostgreSQL

### Проблемы

- ❌ Regex не учитывает контекст
- ❌ Нет понимания layout визитки
- ❌ Нет обучения на исправлениях пользователя
- ❌ Зависимость от внешних API
- ❌ Низкая точность для нестандартных визиток

---

## 🚀 Целевая архитектура v2.0

### Компоненты

| Компонент | Технология | Задача | Статус |
|-----------|------------|--------|--------|
| **OCR** | PaddleOCR | Распознавание текста + bbox | ⚠️ Частично |
| **Layout Model** | LayoutLMv3 | Классификация текста по полям | 🔴 Новое |
| **Validator** | FastAPI + spaCy/GPT | Проверка и исправление | 🟡 Upgrade |
| **Training** | HuggingFace Transformers | Дообучение моделей | 🔴 Новое |
| **Annotation** | Label Studio | Визуальная аннотация | ✅ Установлен |
| **Storage** | PostgreSQL + MinIO | Данные + изображения | 🟡 +MinIO |
| **Orchestration** | Docker Compose | Изоляция сервисов | ✅ Есть |

### Архитектурная схема v2.0

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  • OCR Editor • Contact List • Duplicate Manager • Training UI  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   OCR API    │  │  Training    │  │  Validation  │          │
│  │   Endpoint   │  │     API      │  │     API      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ML Services Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PaddleOCR   │  │  LayoutLMv3  │  │   Validator  │          │
│  │   Service    │  │   Service    │  │   (spaCy)    │          │
│  │              │  │              │  │              │          │
│  │ • Text OCR   │  │ • Field      │  │ • Format     │          │
│  │ • Bbox       │  │   Classify   │  │   Check      │          │
│  │ • Multicard  │  │ • Layout     │  │ • Regex      │          │
│  │              │  │   Analysis   │  │ • Correction │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    MinIO     │  │    Redis     │          │
│  │              │  │              │  │              │          │
│  │ • Contacts   │  │ • Images     │  │ • Cache      │          │
│  │ • Training   │  │ • Trained    │  │ • Queue      │          │
│  │   Data       │  │   Models     │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
          ▲
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Label Studio                                │
│  • Manual Annotation • Ground Truth Creation • Model Training   │
└─────────────────────────────────────────────────────────────────┘
```

### Новый flow обработки

```
┌──────────────┐
│   Upload     │
│   Image      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  QR Check    │
│  (Optional)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  PaddleOCR   │  ←─── Step 1: Text Extraction + BBox
│  • Text      │
│  • Coords    │
│  • Layout    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ LayoutLMv3   │  ←─── Step 2: Field Classification
│  Classifier  │        (понимает layout + контекст)
│              │
│  Input:      │
│  • Text      │
│  • BBox      │
│  • Image     │
│              │
│  Output:     │
│  • full_name │
│  • position  │
│  • company   │
│  • email     │
│  • phone     │
│  • website   │
│  • address   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validator   │  ←─── Step 3: Format Check & Correction
│  • Email     │
│  • Phone     │
│  • URL       │
│  • NER       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Save      │
│  PostgreSQL  │
└──────────────┘
```

---

## 📋 План миграции

### Этап 0: Подготовка (1-2 недели)

#### 0.1 Анализ и планирование
- [x] Анализ текущей архитектуры
- [x] Создание детального плана
- [ ] Оценка требований к ресурсам (CPU/GPU/RAM)
- [ ] Выбор версии LayoutLMv3 (base/large)

#### 0.2 Инфраструктура
- [ ] Установка MinIO для хранения изображений
- [ ] Настройка Label Studio для аннотации
- [ ] Подготовка GPU (если требуется)
- [ ] Создание dev окружения

#### 0.3 Data Preparation
- [ ] Экспорт существующих контактов с изображениями
- [ ] Подготовка training/validation split
- [ ] Создание schema для Label Studio
- [ ] Baseline аннотация (100+ визиток)

**Deliverables:**
- ✅ `OCR_ARCHITECTURE_MIGRATION_v2.md` (этот документ)
- ⬜ MinIO в docker-compose
- ⬜ Label Studio project настроен
- ⬜ Dataset для обучения (100+ образцов)

---

### Этап 1: PaddleOCR Integration (2-3 недели)

#### 1.1 Установка PaddleOCR
```bash
# backend/requirements.txt
paddlepaddle==2.5.0  # CPU version
# paddlepaddle-gpu==2.5.0  # GPU version (если есть GPU)
paddleocr==2.7.0
```

#### 1.2 Создание PaddleOCR Provider
```python
# backend/app/integrations/ocr/providers/paddle_provider.py
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image

class PaddleOCRProvider(OCRProvider):
    """PaddleOCR - высокая точность + bbox + layout"""
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self.priority = 0  # Наивысший приоритет
        self.ocr = PaddleOCR(
            use_angle_cls=True,  # Поворот текста
            lang='en',           # Можно добавить 'ru', 'ch'
            use_gpu=False,       # True если есть GPU
            show_log=False
        )
    
    def is_available(self) -> bool:
        return True  # Всегда доступен локально
    
    def recognize(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Распознавание с PaddleOCR
        
        Returns:
            {
                'provider': 'PaddleOCR',
                'raw_text': str,
                'blocks': [
                    {
                        'text': str,
                        'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
                        'confidence': float
                    }
                ],
                'data': {...},  # Parsed fields
                'confidence': float
            }
        """
        # Convert bytes to numpy array
        img = Image.open(io.BytesIO(image_data))
        img_np = np.array(img)
        
        # Run OCR
        result = self.ocr.ocr(img_np, cls=True)
        
        # Extract blocks with bboxes
        blocks = []
        all_text = []
        
        for line in result[0]:
            bbox, (text, confidence) = line
            blocks.append({
                'text': text,
                'bbox': bbox,
                'confidence': confidence
            })
            all_text.append(text)
        
        combined_text = '\n'.join(all_text)
        
        return {
            'provider': self.name,
            'raw_text': combined_text,
            'blocks': blocks,  # NEW: Structured blocks with coordinates
            'data': self._parse_text(combined_text),
            'confidence': np.mean([b['confidence'] for b in blocks]) if blocks else 0
        }
```

#### 1.3 Интеграция в OCRManager
```python
# backend/app/integrations/ocr/providers.py
from .paddle_provider import PaddleOCRProvider

class OCRManager:
    def _initialize_providers(self):
        all_providers = [
            PaddleOCRProvider(),        # ← NEW: Priority 0
            ParsioProvider(),           # Priority 1
            GoogleVisionProvider(),     # Priority 2
            TesseractProvider(),        # Priority 3
        ]
```

#### 1.4 Тестирование
- [ ] Unit tests для PaddleOCRProvider
- [ ] Integration tests с реальными визитками
- [ ] Benchmark: точность vs Tesseract/Google
- [ ] Performance: скорость обработки

**Deliverables:**
- ⬜ `paddle_provider.py` реализован
- ⬜ Интегрирован в OCRManager
- ⬜ Tests проходят (90%+ coverage)
- ⬜ Benchmark отчет

---

### Этап 2: LayoutLMv3 Integration (3-4 недели)

#### 2.1 Установка LayoutLMv3
```bash
# backend/requirements.txt
transformers==4.35.0
torch==2.1.0  # CPU version
# torch==2.1.0+cu118  # GPU version
pillow==10.1.0
numpy==1.24.0
```

#### 2.2 Создание LayoutLMv3 Service
```python
# backend/app/services/layoutlm_service.py
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
import torch
from PIL import Image

class LayoutLMv3Service:
    """
    Service for field classification using LayoutLMv3
    
    Model understands:
    - Text content
    - Spatial layout (bbox)
    - Visual features (image)
    """
    
    def __init__(self, model_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load pre-trained model or fine-tuned model
        model_name = model_path or "microsoft/layoutlmv3-base"
        
        self.processor = LayoutLMv3Processor.from_pretrained(model_name)
        self.model = LayoutLMv3ForTokenClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Label mapping for business cards
        self.id2label = {
            0: 'O',          # Other
            1: 'B-NAME',     # Begin Name
            2: 'I-NAME',     # Inside Name
            3: 'B-POSITION', # Begin Position
            4: 'I-POSITION',
            5: 'B-COMPANY',
            6: 'I-COMPANY',
            7: 'B-EMAIL',
            8: 'B-PHONE',
            9: 'I-PHONE',
            10: 'B-ADDRESS',
            11: 'I-ADDRESS',
            12: 'B-WEBSITE',
        }
        
        self.label2id = {v: k for k, v in self.id2label.items()}
    
    def classify_fields(
        self,
        image: Image.Image,
        ocr_blocks: List[Dict]
    ) -> Dict[str, Any]:
        """
        Classify OCR blocks into business card fields
        
        Args:
            image: PIL Image
            ocr_blocks: List of dicts with 'text' and 'bbox' from PaddleOCR
        
        Returns:
            {
                'full_name': str,
                'position': str,
                'company': str,
                'email': str,
                'phone': str,
                'address': str,
                'website': str,
                'confidence': float,
                'predictions': List[Dict]  # Raw predictions
            }
        """
        # Prepare input for LayoutLMv3
        words = [block['text'] for block in ocr_blocks]
        boxes = [self._normalize_bbox(block['bbox'], image.size) for block in ocr_blocks]
        
        # Encode
        encoding = self.processor(
            image,
            words,
            boxes=boxes,
            return_tensors="pt",
            padding="max_length",
            truncation=True
        )
        
        # Move to device
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**encoding)
            predictions = outputs.logits.argmax(-1).squeeze().tolist()
        
        # Decode predictions
        classified_fields = self._decode_predictions(
            words,
            predictions,
            ocr_blocks
        )
        
        return classified_fields
    
    def _normalize_bbox(self, bbox, image_size):
        """
        Normalize bbox coordinates to [0, 1000] scale
        LayoutLMv3 expects: [x_min, y_min, x_max, y_max]
        """
        width, height = image_size
        
        # Extract coordinates from PaddleOCR format
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        
        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)
        
        # Normalize to 1000x1000
        return [
            int(x_min / width * 1000),
            int(y_min / height * 1000),
            int(x_max / width * 1000),
            int(y_max / height * 1000)
        ]
    
    def _decode_predictions(
        self,
        words: List[str],
        predictions: List[int],
        ocr_blocks: List[Dict]
    ) -> Dict[str, Any]:
        """
        Decode model predictions into structured contact fields
        """
        # Group words by predicted labels
        field_map = {
            'full_name': [],
            'position': [],
            'company': [],
            'email': [],
            'phone': [],
            'address': [],
            'website': []
        }
        
        current_field = None
        
        for i, (word, pred_id) in enumerate(zip(words, predictions)):
            label = self.id2label.get(pred_id, 'O')
            
            if label == 'O':
                current_field = None
                continue
            
            # Parse label (e.g., 'B-NAME' -> 'NAME')
            bio, field_type = label.split('-')
            
            # Map to our field names
            field_name_map = {
                'NAME': 'full_name',
                'POSITION': 'position',
                'COMPANY': 'company',
                'EMAIL': 'email',
                'PHONE': 'phone',
                'ADDRESS': 'address',
                'WEBSITE': 'website'
            }
            
            field_name = field_name_map.get(field_type)
            if not field_name:
                continue
            
            if bio == 'B':  # Begin
                current_field = field_name
                field_map[field_name].append(word)
            elif bio == 'I' and current_field == field_name:  # Inside
                field_map[field_name].append(word)
        
        # Join words into strings
        result = {
            field: ' '.join(words) if words else None
            for field, words in field_map.items()
        }
        
        # Calculate confidence (simplified)
        confidence = len([w for w in words if w]) / len(words) if words else 0
        
        result['confidence'] = confidence
        result['predictions'] = [
            {
                'word': word,
                'label': self.id2label.get(pred_id, 'O'),
                'bbox': ocr_blocks[i]['bbox']
            }
            for i, (word, pred_id) in enumerate(zip(words, predictions))
        ]
        
        return result
```

#### 2.3 Integration с OCR Pipeline
```python
# backend/app/tasks.py

from .services.layoutlm_service import LayoutLMv3Service

# Initialize LayoutLMv3 service (singleton)
layoutlm_service = LayoutLMv3Service()

def _process_card_sync(...):
    # ... QR code check ...
    
    # Step 1: PaddleOCR for text + bbox
    ocr_result = ocr_manager.recognize(
        ocr_input,
        filename=filename,
        preferred_provider='paddleocr'  # Force PaddleOCR
    )
    
    # Step 2: LayoutLMv3 for field classification
    if 'blocks' in ocr_result and ocr_result['blocks']:
        img = Image.open(io.BytesIO(image_data))
        
        classified_data = layoutlm_service.classify_fields(
            image=img,
            ocr_blocks=ocr_result['blocks']
        )
        
        # Use classified data instead of regex parsing
        data = classified_data
        recognition_method = 'paddleocr_layoutlm'
    else:
        # Fallback to old method
        data = ocr_result['data']
        recognition_method = ocr_result['provider']
```

#### 2.4 Тестирование
- [ ] Unit tests для LayoutLMv3Service
- [ ] Integration tests с PaddleOCR
- [ ] Benchmark: точность классификации полей
- [ ] A/B testing с текущей версией

**Deliverables:**
- ⬜ `layoutlm_service.py` реализован
- ⬜ Интегрирован в OCR pipeline
- ⬜ Tests проходят
- ⬜ A/B test показывает улучшение

---

### Этап 3: Validator & Post-processing (1-2 недели)

#### 3.1 Установка зависимостей
```bash
# backend/requirements.txt
spacy==3.7.0
# python -m spacy download en_core_web_sm
# python -m spacy download ru_core_news_sm
phonenumbers==8.13.0
email-validator==2.1.0
```

#### 3.2 Создание Validator Service
```python
# backend/app/services/validator_service.py
import re
import spacy
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from typing import Dict, Optional

class ValidatorService:
    """
    Service for validating and correcting extracted contact fields
    """
    
    def __init__(self):
        self.nlp_en = spacy.load('en_core_web_sm')
        # self.nlp_ru = spacy.load('ru_core_news_sm')  # If needed
    
    def validate_and_correct(self, data: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """
        Validate and correct all fields
        
        Returns corrected data
        """
        corrected = data.copy()
        
        # Email validation
        if corrected.get('email'):
            corrected['email'] = self._validate_email(corrected['email'])
        
        # Phone validation
        if corrected.get('phone'):
            corrected['phone'] = self._validate_phone(corrected['phone'])
        
        # Website validation
        if corrected.get('website'):
            corrected['website'] = self._validate_website(corrected['website'])
        
        # Name validation (use NER if needed)
        if corrected.get('full_name'):
            corrected['full_name'] = self._validate_name(corrected['full_name'])
        
        return corrected
    
    def _validate_email(self, email: str) -> Optional[str]:
        """Validate and normalize email"""
        try:
            valid = validate_email(email, check_deliverability=False)
            return valid.email
        except EmailNotValidError:
            # Try to extract email from text
            email_pattern = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}'
            match = re.search(email_pattern, email)
            return match.group(0) if match else None
    
    def _validate_phone(self, phone: str) -> Optional[str]:
        """Validate and normalize phone number"""
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone, None)
            
            if phonenumbers.is_valid_number(parsed):
                # Format in international format
                return phonenumbers.format_number(
                    parsed,
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
        except:
            pass
        
        # Fallback: clean up phone number
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned if len(cleaned) >= 7 else None
    
    def _validate_website(self, website: str) -> Optional[str]:
        """Validate and normalize website"""
        # Add http:// if missing
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        # Basic URL validation
        url_pattern = r'https?://[^\s]+'
        if re.match(url_pattern, website):
            return website
        
        return None
    
    def _validate_name(self, name: str) -> Optional[str]:
        """Validate name using NER"""
        # Use spaCy NER to check if it looks like a name
        doc = self.nlp_en(name)
        
        # Check if any entities are detected as PERSON
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        
        if persons:
            return persons[0]  # Return the first person name found
        
        # Fallback: just clean up the name
        return name.strip()
```

#### 3.3 Integration
```python
# backend/app/tasks.py

validator_service = ValidatorService()

def _process_card_sync(...):
    # ... OCR + LayoutLM ...
    
    # Step 3: Validation and correction
    data = validator_service.validate_and_correct(data)
    
    # ... save to database ...
```

**Deliverables:**
- ⬜ `validator_service.py` реализован
- ⬜ Tests проходят
- ⬜ Интеграция в pipeline

---

### Этап 4: Training Pipeline (3-4 недели)

#### 4.1 Label Studio Configuration

```xml
<!-- label-studio-config.xml -->
<View>
  <Image name="image" value="$image"/>
  <Labels name="label" toName="image">
    <Label value="NAME" background="red"/>
    <Label value="POSITION" background="blue"/>
    <Label value="COMPANY" background="green"/>
    <Label value="EMAIL" background="purple"/>
    <Label value="PHONE" background="orange"/>
    <Label value="ADDRESS" background="yellow"/>
    <Label value="WEBSITE" background="cyan"/>
  </Labels>
  <Rectangle name="bbox" toName="image" strokeWidth="3"/>
  <Text name="transcription" toName="image" editable="true"/>
</View>
```

#### 4.2 Data Export Pipeline
```python
# backend/app/services/training_service.py

class TrainingService:
    """
    Service for managing training data and model fine-tuning
    """
    
    def export_for_labeling(self, contact_ids: List[int]) -> str:
        """
        Export contacts to Label Studio format
        
        Returns: Path to exported JSON file
        """
        # Get contacts from database
        contacts = self.db.query(Contact).filter(
            Contact.id.in_(contact_ids)
        ).all()
        
        # Convert to Label Studio format
        tasks = []
        for contact in contacts:
            task = {
                'data': {
                    'image': f'/label-studio/files/{contact.photo_path}'
                },
                'predictions': [{
                    'result': self._contact_to_annotations(contact)
                }]
            }
            tasks.append(task)
        
        # Save to file
        output_path = f'/tmp/export_{uuid.uuid4().hex}.json'
        with open(output_path, 'w') as f:
            json.dump(tasks, f)
        
        return output_path
    
    def import_annotations(self, label_studio_export: str):
        """
        Import annotations from Label Studio
        
        Creates training dataset for LayoutLMv3
        """
        # Load Label Studio export
        with open(label_studio_export, 'r') as f:
            tasks = json.load(f)
        
        # Convert to LayoutLMv3 training format
        training_data = []
        
        for task in tasks:
            image_path = task['data']['image']
            annotations = task['annotations'][0]['result']
            
            # Parse annotations
            training_example = self._parse_annotations(
                image_path,
                annotations
            )
            
            training_data.append(training_example)
        
        # Save training dataset
        dataset_path = f'/app/training_data/dataset_{int(time.time())}.json'
        with open(dataset_path, 'w') as f:
            json.dump(training_data, f)
        
        return dataset_path
    
    def fine_tune_model(
        self,
        training_data_path: str,
        base_model: str = 'microsoft/layoutlmv3-base',
        epochs: int = 10,
        batch_size: int = 4
    ):
        """
        Fine-tune LayoutLMv3 model on training data
        """
        # Load training data
        with open(training_data_path, 'r') as f:
            training_data = json.load(f)
        
        # Create HuggingFace dataset
        from datasets import Dataset
        dataset = Dataset.from_dict(training_data)
        
        # Split train/val
        dataset = dataset.train_test_split(test_size=0.1)
        
        # Load model and tokenizer
        from transformers import (
            LayoutLMv3ForTokenClassification,
            LayoutLMv3Processor,
            Trainer,
            TrainingArguments
        )
        
        processor = LayoutLMv3Processor.from_pretrained(base_model)
        model = LayoutLMv3ForTokenClassification.from_pretrained(
            base_model,
            num_labels=len(self.label2id)
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir='/app/models/layoutlmv3_finetuned',
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='/app/logs',
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset['train'],
            eval_dataset=dataset['test'],
            tokenizer=processor,
        )
        
        # Train
        trainer.train()
        
        # Save model
        model_path = f'/app/models/layoutlmv3_finetuned_{int(time.time())}'
        trainer.save_model(model_path)
        
        return model_path
```

#### 4.3 API Endpoints для обучения
```python
# backend/app/api/training.py

from fastapi import APIRouter, Depends, UploadFile, File
from ..services.training_service import TrainingService

router = APIRouter(prefix="/api/training", tags=["training"])

@router.post("/export")
async def export_for_labeling(
    contact_ids: List[int],
    service: TrainingService = Depends(get_training_service)
):
    """Export contacts to Label Studio format"""
    export_path = service.export_for_labeling(contact_ids)
    return {"export_path": export_path}

@router.post("/import")
async def import_annotations(
    file: UploadFile = File(...),
    service: TrainingService = Depends(get_training_service)
):
    """Import annotations from Label Studio"""
    # Save uploaded file
    temp_path = f'/tmp/{file.filename}'
    with open(temp_path, 'wb') as f:
        f.write(await file.read())
    
    dataset_path = service.import_annotations(temp_path)
    return {"dataset_path": dataset_path}

@router.post("/train")
async def train_model(
    dataset_path: str,
    epochs: int = 10,
    service: TrainingService = Depends(get_training_service)
):
    """Start model training"""
    model_path = service.fine_tune_model(
        training_data_path=dataset_path,
        epochs=epochs
    )
    return {"model_path": model_path}
```

**Deliverables:**
- ⬜ Label Studio настроен для аннотации
- ⬜ `training_service.py` реализован
- ⬜ API endpoints для обучения
- ⬜ Обучена первая версия модели

---

### Этап 5: MinIO Integration (1 неделя)

#### 5.1 Docker Compose Setup
```yaml
# docker-compose.yml

services:
  minio:
    image: minio/minio:latest
    container_name: bizcard-minio
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-admin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minio123456}
    volumes:
      - minio_data:/data
    ports:
      - '127.0.0.1:9000:9000'  # API
      - '127.0.0.1:9001:9001'  # Console
    command: server /data --console-address ":9001"
    restart: unless-stopped

volumes:
  minio_data:
```

#### 5.2 MinIO Client Service
```python
# backend/app/services/storage_service.py

from minio import Minio
from minio.error import S3Error
import io

class StorageService:
    """
    Service for managing file storage in MinIO
    """
    
    def __init__(self):
        self.client = Minio(
            os.getenv('MINIO_ENDPOINT', 'minio:9000'),
            access_key=os.getenv('MINIO_ROOT_USER', 'admin'),
            secret_key=os.getenv('MINIO_ROOT_PASSWORD'),
            secure=False  # Use True in production with SSL
        )
        
        # Create buckets if they don't exist
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Create required buckets"""
        buckets = ['business-cards', 'trained-models', 'training-data']
        
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
    
    def upload_image(self, image_data: bytes, filename: str) -> str:
        """
        Upload business card image to MinIO
        
        Returns: Object path (bucket/filename)
        """
        bucket = 'business-cards'
        
        self.client.put_object(
            bucket,
            filename,
            io.BytesIO(image_data),
            length=len(image_data),
            content_type='image/jpeg'
        )
        
        return f'{bucket}/{filename}'
    
    def get_image(self, object_path: str) -> bytes:
        """Get image from MinIO"""
        bucket, filename = object_path.split('/', 1)
        
        response = self.client.get_object(bucket, filename)
        data = response.read()
        response.close()
        response.release_conn()
        
        return data
    
    def upload_model(self, model_path: str, model_name: str) -> str:
        """Upload trained model to MinIO"""
        bucket = 'trained-models'
        
        self.client.fput_object(
            bucket,
            model_name,
            model_path
        )
        
        return f'{bucket}/{model_name}'
```

**Deliverables:**
- ⬜ MinIO добавлен в docker-compose
- ⬜ `storage_service.py` реализован
- ⬜ Миграция существующих изображений

---

### Этап 6: Frontend Integration (2 недели)

#### 6.1 Training UI Component
```javascript
// frontend/src/components/TrainingPanel.js

import React, { useState } from 'react';
import axios from 'axios';

const TrainingPanel = () => {
  const [selectedContacts, setSelectedContacts] = useState([]);
  const [training, setTraining] = useState(false);
  
  const exportForLabeling = async () => {
    const response = await axios.post('/api/training/export', {
      contact_ids: selectedContacts
    });
    
    // Open Label Studio with exported data
    window.open(`http://localhost:8081/projects/1`, '_blank');
  };
  
  const startTraining = async () => {
    setTraining(true);
    
    const response = await axios.post('/api/training/train', {
      dataset_path: '/app/training_data/latest.json',
      epochs: 10
    });
    
    setTraining(false);
    alert('Training completed! Model saved to: ' + response.data.model_path);
  };
  
  return (
    <div className="training-panel">
      <h2>Model Training</h2>
      
      <button onClick={exportForLabeling}>
        Export to Label Studio
      </button>
      
      <button onClick={startTraining} disabled={training}>
        {training ? 'Training...' : 'Start Training'}
      </button>
    </div>
  );
};
```

#### 6.2 Enhanced OCR Editor
```javascript
// frontend/src/components/OCREditorWithLayoutLM.js

// Show confidence for each field
// Highlight predicted bounding boxes
// Allow manual correction
```

**Deliverables:**
- ⬜ Training UI компонент
- ⬜ Enhanced OCR Editor
- ⬜ Integration с Label Studio

---

## 📦 Технический стек

### Backend

```python
# backend/requirements.txt

# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
celery==5.3.4
redis==5.0.1

# OCR & ML
paddlepaddle==2.5.0  # or paddlepaddle-gpu
paddleocr==2.7.0
transformers==4.35.0
torch==2.1.0  # or torch-gpu
pillow==10.1.0
numpy==1.24.0

# Validation
spacy==3.7.0
phonenumbers==8.13.0
email-validator==2.1.0

# Storage
psycopg2-binary==2.9.9
minio==7.2.0

# Utils
python-dotenv==1.0.0
pydantic==2.5.0
python-multipart==0.0.6
```

### Frontend

```json
// frontend/package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.0"
  }
}
```

### Infrastructure

```yaml
# docker-compose.yml

services:
  backend: ...
  frontend: ...
  postgres: ...
  redis: ...
  minio: ...
  label-studio: ...
```

---

## 📁 Структура проекта

```
fastapi-bizcard-crm-ready/
├── backend/
│   ├── app/
│   │   ├── integrations/
│   │   │   └── ocr/
│   │   │       ├── providers/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── base.py
│   │   │       │   ├── tesseract.py
│   │   │       │   ├── paddle.py           ← NEW
│   │   │       │   ├── google.py
│   │   │       │   └── parsio.py
│   │   │       └── manager.py
│   │   ├── services/
│   │   │   ├── ocr_service.py
│   │   │   ├── layoutlm_service.py         ← NEW
│   │   │   ├── validator_service.py        ← NEW
│   │   │   ├── training_service.py         ← NEW
│   │   │   └── storage_service.py          ← NEW
│   │   ├── api/
│   │   │   ├── ocr.py
│   │   │   └── training.py                 ← NEW
│   │   └── models/
│   │       └── training.py                 ← NEW
│   ├── models/                              ← NEW
│   │   ├── layoutlmv3_finetuned/
│   │   └── checkpoints/
│   └── training_data/                       ← NEW
│       └── datasets/
├── frontend/
│   └── src/
│       └── components/
│           ├── OCREditorWithLayoutLM.js    ← NEW
│           └── TrainingPanel.js            ← NEW
├── label-studio-config.xml
├── docker-compose.yml
└── OCR_ARCHITECTURE_MIGRATION_v2.md        ← THIS FILE
```

---

## 🗓️ Roadmap

### Q1 2025 (Weeks 1-12)

| Неделя | Этап | Задачи | Статус |
|--------|------|--------|--------|
| 1-2 | Этап 0 | Подготовка, MinIO, Label Studio | 🟡 In Progress |
| 3-5 | Этап 1 | PaddleOCR Integration | ⬜ |
| 6-9 | Этап 2 | LayoutLMv3 Integration | ⬜ |
| 10-11 | Этап 3 | Validator & Post-processing | ⬜ |
| 12 | - | Testing & Benchmarking | ⬜ |

### Q2 2025 (Weeks 13-24)

| Неделя | Этап | Задачи | Статус |
|--------|------|--------|--------|
| 13-16 | Этап 4 | Training Pipeline | ⬜ |
| 17 | Этап 5 | MinIO Migration | ⬜ |
| 18-19 | Этап 6 | Frontend Integration | ⬜ |
| 20-22 | - | Annotate 500+ cards | ⬜ |
| 23 | - | Train production model | ⬜ |
| 24 | - | Deploy v2.0 to production | ⬜ |

---

## 📊 Метрики успеха

### Целевые показатели

| Метрика | Текущий (v5.3.0) | Целевой (v2.0) | Статус |
|---------|------------------|----------------|--------|
| **Точность извлечения** | ~70% | >95% | ⬜ |
| **Скорость обработки** | 2-5 сек | <3 сек | ⬜ |
| **Зависимость от API** | Высокая | Низкая | ⬜ |
| **Поддержка обучения** | Нет | Да | ⬜ |
| **Layout awareness** | Нет | Да | ⬜ |

### KPI

- [ ] **Precision**: >95% для каждого поля
- [ ] **Recall**: >90% для каждого поля
- [ ] **F1-Score**: >92% overall
- [ ] **User corrections**: <5% на 100 визиток
- [ ] **Processing time**: <3 секунды/визитка

---

## 🔄 Continuous Improvement

### Post-launch (Q3 2025+)

1. **Active Learning Loop**
   - Собирать user corrections
   - Периодически переобучать модель
   - A/B testing новых версий

2. **Multi-language Support**
   - Добавить русский язык
   - Добавить китайский язык
   - Мультиязычные визитки

3. **Advanced Features**
   - Logo detection and extraction
   - Company recognition from logo
   - Social media links detection
   - Duplicate detection improvements

---

## 📚 Ссылки и ресурсы

### Документация

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [LayoutLMv3](https://huggingface.co/docs/transformers/model_doc/layoutlmv3)
- [Label Studio](https://labelstud.io/guide/)
- [MinIO](https://min.io/docs/minio/linux/index.html)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)

### Papers

- **LayoutLMv3**: [Microsoft Research Paper](https://arxiv.org/abs/2204.08387)
- **PaddleOCR**: [Baidu Research](https://github.com/PaddlePaddle/PaddleOCR)

### Tutorials

- [Fine-tuning LayoutLMv3](https://huggingface.co/docs/transformers/model_doc/layoutlmv3#fine-tuning-layoutlmv3)
- [Label Studio ML Backend](https://labelstud.io/guide/ml.html)

---

## ✅ Next Steps

1. **Immediate (This Week)**
   - [ ] Установить MinIO
   - [ ] Настроить Label Studio project
   - [ ] Подготовить первую партию данных (100 визиток)

2. **Short-term (Next 2 Weeks)**
   - [ ] Реализовать PaddleOCR Provider
   - [ ] Протестировать на существующих визитках
   - [ ] Benchmark vs Tesseract

3. **Medium-term (Next Month)**
   - [ ] Реализовать LayoutLMv3 Service
   - [ ] Интеграция с PaddleOCR
   - [ ] Начать аннотацию данных

---

**Версия документа**: 2.0.0  
**Последнее обновление**: October 26, 2025  
**Автор**: AI Assistant  
**Статус**: 🚀 Planning Phase

---

*Этот план миграции является живым документом и будет обновляться по мере прогресса проекта.*

