"""
Training Service for Self-Learning OCR
Handles model fine-tuning based on user corrections
"""
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TrainingService:
    """
    Service for training and fine-tuning OCR models
    - Collect training data from annotations
    - Fine-tune PaddleOCR
    - Fine-tune LayoutLMv3
    - Track model versions and performance
    """
    
    def __init__(self):
        self.training_data_dir = '/app/training_data'
        self.models_dir = '/app/models'
        self.min_samples_for_training = 50  # Minimum samples before training
        self.training_in_progress = False
        
        # Create directories
        os.makedirs(self.training_data_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
    
    def collect_training_data(self, annotations: List[Dict]) -> Dict[str, Any]:
        """
        Collect and prepare training data from Label Studio annotations
        """
        training_samples = []
        
        for ann in annotations:
            try:
                # Extract image path and blocks
                image_url = ann['data'].get('image', '')
                annotations_list = ann.get('annotations', [])
                
                if not annotations_list:
                    continue
                
                # Get the latest annotation
                latest_annotation = annotations_list[-1]
                results = latest_annotation.get('result', [])
                
                # Parse rectangles and transcriptions
                blocks = []
                for result in results:
                    if result['type'] == 'rectanglelabels':
                        value = result['value']
                        block = {
                            'bbox': [
                                value['x'], value['y'],
                                value['x'] + value['width'],
                                value['y'] + value['height']
                            ],
                            'label': value['rectanglelabels'][0],
                            'text': ''
                        }
                        
                        # Find matching transcription
                        for trans_result in results:
                            if trans_result['type'] == 'textarea':
                                # Match by region_id if available
                                if result.get('id') == trans_result.get('origin'):
                                    block['text'] = trans_result['value']['text'][0]
                                    break
                        
                        blocks.append(block)
                
                if blocks:
                    training_samples.append({
                        'image': image_url,
                        'blocks': blocks,
                        'annotated_at': latest_annotation.get('created_at'),
                        'contact_id': ann['data'].get('contact_id')
                    })
                    
            except Exception as e:
                logger.error(f"Error processing annotation: {e}")
                continue
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            self.training_data_dir,
            f'training_data_{timestamp}.json'
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_samples, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Collected {len(training_samples)} training samples → {output_file}")
        
        return {
            'samples_count': len(training_samples),
            'output_file': output_file,
            'ready_for_training': len(training_samples) >= self.min_samples_for_training
        }
    
    def should_trigger_training(self) -> bool:
        """
        Check if we have enough new data to trigger training
        """
        try:
            # Count training samples
            total_samples = 0
            for filename in os.listdir(self.training_data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.training_data_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        total_samples += len(data)
            
            logger.info(f"📊 Total training samples: {total_samples}")
            return total_samples >= self.min_samples_for_training
            
        except Exception as e:
            logger.error(f"Error checking training readiness: {e}")
            return False
    
    def fine_tune_layoutlm(self, training_data_path: str) -> Dict[str, Any]:
        """
        Fine-tune LayoutLMv3 on annotated business cards
        
        This is a placeholder - actual implementation requires:
        1. Convert annotations to LayoutLM format
        2. Set up training configuration
        3. Run fine-tuning with PyTorch
        4. Evaluate and save model
        """
        logger.info(f"🎓 Starting LayoutLMv3 fine-tuning...")
        
        # TODO: Implement actual fine-tuning
        # For now, return mock results
        return {
            'status': 'scheduled',
            'message': 'LayoutLMv3 fine-tuning scheduled',
            'training_samples': 0,
            'estimated_time': '2-4 hours'
        }
    
    def fine_tune_paddleocr(self, training_data_path: str) -> Dict[str, Any]:
        """
        Fine-tune PaddleOCR on cyrillic business cards
        
        This requires:
        1. Prepare images and labels in PaddleOCR format
        2. Configure training parameters
        3. Run training
        4. Export model
        """
        logger.info(f"🎓 Starting PaddleOCR fine-tuning...")
        
        # TODO: Implement actual fine-tuning
        return {
            'status': 'scheduled',
            'message': 'PaddleOCR fine-tuning scheduled',
            'training_samples': 0,
            'estimated_time': '1-2 hours'
        }
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get statistics about training data and models
        """
        try:
            # Count training files and samples
            total_files = 0
            total_samples = 0
            
            for filename in os.listdir(self.training_data_dir):
                if filename.endswith('.json'):
                    total_files += 1
                    filepath = os.path.join(self.training_data_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        total_samples += len(data)
            
            # Check model versions
            model_versions = []
            if os.path.exists(self.models_dir):
                model_versions = os.listdir(self.models_dir)
            
            return {
                'training_data_files': total_files,
                'total_training_samples': total_samples,
                'ready_for_training': total_samples >= self.min_samples_for_training,
                'min_samples_required': self.min_samples_for_training,
                'model_versions': len(model_versions),
                'training_in_progress': self.training_in_progress
            }
            
        except Exception as e:
            logger.error(f"Error getting training stats: {e}")
            return {}
    
    def create_feedback_from_corrections(
        self,
        contact_id: int,
        original_blocks: List[Dict],
        corrected_blocks: List[Dict]
    ) -> Dict[str, Any]:
        """
        Create training feedback from user corrections in the table editor
        
        This captures:
        - Text corrections (OCR mistakes)
        - Field assignment corrections (classification mistakes)
        - Deleted blocks (false positives)
        - Added blocks (false negatives)
        """
        feedback = {
            'contact_id': contact_id,
            'timestamp': datetime.now().isoformat(),
            'corrections': {
                'text_corrections': [],
                'field_corrections': [],
                'deleted_blocks': [],
                'added_blocks': []
            }
        }
        
        # Map blocks by ID
        original_map = {b.get('block_id'): b for b in original_blocks if b.get('block_id') is not None}
        corrected_map = {b.get('block_id'): b for b in corrected_blocks if b.get('block_id') is not None}
        
        # Find text corrections
        for block_id, original in original_map.items():
            if block_id in corrected_map:
                corrected = corrected_map[block_id]
                
                # Text correction
                if original.get('text') != corrected.get('text'):
                    feedback['corrections']['text_corrections'].append({
                        'block_id': block_id,
                        'original': original.get('text'),
                        'corrected': corrected.get('text'),
                        'bbox': original.get('box')
                    })
                
                # Field correction
                if original.get('field_type') != corrected.get('field_type'):
                    feedback['corrections']['field_corrections'].append({
                        'block_id': block_id,
                        'original_field': original.get('field_type'),
                        'corrected_field': corrected.get('field_type'),
                        'text': corrected.get('text')
                    })
        
        # Find deleted blocks (in original but not in corrected)
        deleted_ids = set(original_map.keys()) - set(corrected_map.keys())
        for block_id in deleted_ids:
            feedback['corrections']['deleted_blocks'].append({
                'block_id': block_id,
                'text': original_map[block_id].get('text'),
                'bbox': original_map[block_id].get('box')
            })
        
        # Find added blocks (in corrected but not in original)
        added_ids = set(corrected_map.keys()) - set(original_map.keys())
        for block_id in added_ids:
            feedback['corrections']['added_blocks'].append({
                'block_id': block_id,
                'text': corrected_map[block_id].get('text'),
                'bbox': corrected_map[block_id].get('box')
            })
        
        # Save feedback
        feedback_file = os.path.join(
            self.training_data_dir,
            f'feedback_{contact_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)
        
        total_corrections = (
            len(feedback['corrections']['text_corrections']) +
            len(feedback['corrections']['field_corrections']) +
            len(feedback['corrections']['deleted_blocks']) +
            len(feedback['corrections']['added_blocks'])
        )
        
        logger.info(f"💾 Saved {total_corrections} corrections for contact {contact_id}")
        
        return feedback

