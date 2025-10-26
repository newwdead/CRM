"""
Dataset Preparer
Prepares training datasets from annotated data
"""
import logging
from typing import List, Dict, Any, Tuple
import json
from PIL import Image
import io

logger = logging.getLogger(__name__)


class DatasetPreparer:
    """
    Prepares datasets for LayoutLMv3 training
    
    Features:
    - Converts Label Studio annotations to LayoutLMv3 format
    - Handles bounding boxes and labels
    - Splits data into train/val/test
    - Data augmentation (future)
    """
    
    def __init__(self):
        self.label_map = {
            'NAME': 1,
            'COMPANY': 2,
            'POSITION': 3,
            'EMAIL': 4,
            'PHONE': 5,
            'PHONE_MOBILE': 6,
            'PHONE_WORK': 7,
            'ADDRESS': 8,
            'WEBSITE': 9,
            'FAX': 10,
            'OTHER': 11,
        }
    
    def prepare_from_label_studio(
        self,
        annotations: List[Dict[str, Any]],
        images: List[bytes]
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Convert Label Studio annotations to training format
        
        Args:
            annotations: List of Label Studio annotation JSONs
            images: List of image bytes
        
        Returns:
            Tuple of (prepared_samples, labels)
        """
        prepared_samples = []
        all_labels = []
        
        for idx, (annotation, image_data) in enumerate(zip(annotations, images)):
            try:
                sample = self._convert_annotation(annotation, image_data, idx)
                if sample:
                    prepared_samples.append(sample)
                    all_labels.extend(sample['labels'])
            except Exception as e:
                logger.error(f"Failed to prepare sample {idx}: {e}")
                continue
        
        logger.info(f"✅ Prepared {len(prepared_samples)} training samples")
        return prepared_samples, all_labels
    
    def _convert_annotation(
        self,
        annotation: Dict[str, Any],
        image_data: bytes,
        sample_id: int
    ) -> Dict[str, Any]:
        """
        Convert single Label Studio annotation
        
        Args:
            annotation: Label Studio annotation
            image_data: Image bytes
            sample_id: Sample ID
        
        Returns:
            Prepared sample dictionary
        """
        # Load image
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        
        # Extract annotations
        results = annotation.get('annotations', [{}])[0].get('result', [])
        
        words = []
        boxes = []
        labels = []
        
        for result in results:
            if result['type'] == 'rectanglelabels':
                # Extract bbox (in percentage)
                bbox_pct = result['value']
                x = bbox_pct['x'] * width / 100
                y = bbox_pct['y'] * height / 100
                w = bbox_pct['width'] * width / 100
                h = bbox_pct['height'] * height / 100
                
                # Convert to LayoutLMv3 format [x, y, x+w, y+h]
                box = [int(x), int(y), int(x + w), int(y + h)]
                boxes.append(box)
                
                # Extract label
                label_name = result['value']['rectanglelabels'][0]
                label_id = self.label_map.get(label_name, 0)
                labels.append(label_id)
                
                # Extract text (from transcription if available)
                text = result.get('value', {}).get('text', '')
                if not text and 'transcription' in result:
                    text = result['transcription']
                words.append(text)
        
        if not words:
            logger.warning(f"No annotations for sample {sample_id}")
            return None
        
        return {
            'id': sample_id,
            'words': words,
            'boxes': boxes,
            'labels': labels,
            'image': image_data,
            'image_size': (width, height),
        }
    
    def split_dataset(
        self,
        samples: List[Dict[str, Any]],
        train_ratio: float = 0.8,
        val_ratio: float = 0.1
    ) -> Tuple[List, List, List]:
        """
        Split dataset into train/val/test
        
        Args:
            samples: All samples
            train_ratio: Train split ratio
            val_ratio: Validation split ratio
        
        Returns:
            (train_samples, val_samples, test_samples)
        """
        import random
        random.shuffle(samples)
        
        total = len(samples)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        
        train_samples = samples[:train_end]
        val_samples = samples[train_end:val_end]
        test_samples = samples[val_end:]
        
        logger.info(
            f"📊 Dataset split: train={len(train_samples)}, "
            f"val={len(val_samples)}, test={len(test_samples)}"
        )
        
        return train_samples, val_samples, test_samples
    
    def save_dataset(self, samples: List[Dict[str, Any]], output_path: str):
        """
        Save prepared dataset to disk
        
        Args:
            samples: Prepared samples
            output_path: Output JSON file path
        """
        # Remove image bytes for JSON serialization
        serializable_samples = []
        for sample in samples:
            serializable = sample.copy()
            serializable.pop('image', None)  # Remove binary data
            serializable_samples.append(serializable)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_samples, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved dataset to {output_path}")

