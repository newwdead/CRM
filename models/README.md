# Models Directory

This directory contains trained ML models for OCR processing.

## Structure

```
models/
├── layoutlmv3/        # Fine-tuned LayoutLMv3 models
├── checkpoints/       # Training checkpoints
└── README.md         # This file
```

## Models

### LayoutLMv3

Fine-tuned model for business card field classification.

**Base Model**: `microsoft/layoutlmv3-base`

**Task**: Token Classification (Named Entity Recognition for business card fields)

**Input**: 
- Image (PIL Image)
- Text tokens (from PaddleOCR)
- Bounding boxes (from PaddleOCR)

**Output**:
- Field labels: NAME, POSITION, COMPANY, EMAIL, PHONE, ADDRESS, WEBSITE

## Model Files

After training, models are saved in the following format:

```
models/layoutlmv3/
└── layoutlmv3_finetuned_<timestamp>/
    ├── config.json
    ├── pytorch_model.bin
    ├── training_args.bin
    └── tokenizer/
```

## Loading Models

```python
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor

model = LayoutLMv3ForTokenClassification.from_pretrained(
    '/app/models/layoutlmv3/layoutlmv3_finetuned_<timestamp>'
)
processor = LayoutLMv3Processor.from_pretrained(
    '/app/models/layoutlmv3/layoutlmv3_finetuned_<timestamp>'
)
```

## Model Performance

Track model performance metrics in training logs:

- Precision, Recall, F1-Score per field
- Overall accuracy
- Training/Validation loss

