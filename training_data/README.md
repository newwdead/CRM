# Training Data Directory

This directory contains training data for LayoutLMv3 model fine-tuning.

## Structure

```
training_data/
├── datasets/          # Training datasets (JSON format)
├── annotations/       # Raw annotations from Label Studio
└── README.md         # This file
```

## Dataset Format

Training datasets should follow LayoutLMv3 format:

```json
{
  "image_path": "path/to/image.jpg",
  "words": ["John", "Doe", "CEO"],
  "bboxes": [[10, 20, 50, 40], [60, 20, 100, 40], [10, 50, 50, 70]],
  "labels": [1, 2, 3]
}
```

## Label Mapping

- 0: O (Other)
- 1: B-NAME
- 2: I-NAME
- 3: B-POSITION
- 4: I-POSITION
- 5: B-COMPANY
- 6: I-COMPANY
- 7: B-EMAIL
- 8: B-PHONE
- 9: I-PHONE
- 10: B-ADDRESS
- 11: I-ADDRESS
- 12: B-WEBSITE

## Usage

1. Export annotated data from Label Studio
2. Convert to LayoutLMv3 format using `training_service.py`
3. Place in `datasets/` directory
4. Run training pipeline

