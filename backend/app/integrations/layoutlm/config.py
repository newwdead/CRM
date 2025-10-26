"""
LayoutLMv3 Configuration
Field labels for business card classification
"""
from typing import Dict, List
from dataclasses import dataclass


# Business card field labels for LayoutLMv3
BUSINESS_CARD_LABELS = {
    'O': 0,          # Other (не поле)
    'B-NAME': 1,     # Begin name
    'I-NAME': 2,     # Inside name
    'B-COMPANY': 3,  # Begin company
    'I-COMPANY': 4,  # Inside company
    'B-POSITION': 5, # Begin position/title
    'I-POSITION': 6, # Inside position
    'B-EMAIL': 7,    # Begin email
    'I-EMAIL': 8,    # Inside email
    'B-PHONE': 9,    # Begin phone
    'I-PHONE': 10,   # Inside phone
    'B-ADDRESS': 11, # Begin address
    'I-ADDRESS': 12, # Inside address
    'B-WEBSITE': 13, # Begin website
    'I-WEBSITE': 14, # Inside website
}

# Reverse mapping
LABEL_TO_NAME = {v: k for k, v in BUSINESS_CARD_LABELS.items()}


# Field aggregation mapping (from BIO tags to final fields)
FIELD_AGGREGATION = {
    'NAME': 'full_name',
    'COMPANY': 'company',
    'POSITION': 'position',
    'EMAIL': 'email',
    'PHONE': 'phone',
    'ADDRESS': 'address',
    'WEBSITE': 'website',
}


@dataclass
class LayoutLMConfig:
    """Configuration for LayoutLMv3 model"""
    
    # Model settings
    model_name: str = "microsoft/layoutlmv3-base"
    num_labels: int = len(BUSINESS_CARD_LABELS)
    
    # Input settings
    max_length: int = 512
    image_size: tuple = (224, 224)
    
    # Classification settings
    confidence_threshold: float = 0.7
    use_gpu: bool = False  # Set to True if GPU available
    
    # Fine-tuned model path (if available)
    fine_tuned_path: str = None
    
    # Training settings (for Phase 6)
    learning_rate: float = 5e-5
    batch_size: int = 4
    num_epochs: int = 10


# Example input format for LayoutLMv3
EXAMPLE_INPUT = {
    "words": ["John", "Doe", "CEO", "john@example.com"],
    "boxes": [[10, 10, 100, 30], [110, 10, 200, 30], [10, 40, 80, 60], [10, 70, 200, 90]],
    "image": "<PIL.Image>"  # PIL Image object
}


# Example output format
EXAMPLE_OUTPUT = {
    "predictions": [1, 2, 5, 7],  # Label IDs
    "confidence": [0.95, 0.92, 0.88, 0.99],
    "fields": {
        "full_name": "John Doe",
        "position": "CEO",
        "email": "john@example.com"
    }
}

