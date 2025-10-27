"""
Label Studio Service for OCR Annotations and Training Data
"""
import os
import logging
import requests
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class LabelStudioService:
    """
    Service for interacting with Label Studio
    - Create projects
    - Upload images
    - Export annotations
    - Sync OCR results for correction
    """
    
    def __init__(self):
        self.base_url = os.getenv('LABEL_STUDIO_URL', 'http://label-studio:8080')
        self.api_key = os.getenv('LABEL_STUDIO_API_KEY', '')
        self.project_id = None
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'Authorization': f'Token {self.api_key}'})
    
    def is_available(self) -> bool:
        """Check if Label Studio is available"""
        try:
            response = self.session.get(f'{self.base_url}/api/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def create_project(self, name: str = "Business Card OCR") -> Optional[int]:
        """
        Create a new Label Studio project for business card annotation
        """
        try:
            # Read configuration
            config_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'label_studio_config.xml'
            )
            
            with open(config_path, 'r') as f:
                label_config = f.read()
            
            payload = {
                'title': name,
                'label_config': label_config,
                'description': 'Business card OCR annotation for model training'
            }
            
            response = self.session.post(
                f'{self.base_url}/api/projects',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                self.project_id = response.json()['id']
                logger.info(f"✅ Created Label Studio project: {self.project_id}")
                return self.project_id
            else:
                logger.error(f"❌ Failed to create project: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating Label Studio project: {e}")
            return None
    
    def upload_task(
        self,
        image_url: str,
        contact_id: int,
        ocr_predictions: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Upload a business card image as a task to Label Studio
        with optional OCR predictions
        """
        if not self.project_id:
            logger.error("No project_id set")
            return None
        
        try:
            task_data = {
                'image': image_url,
                'contact_id': contact_id
            }
            
            # Add OCR predictions for faster annotation
            predictions = []
            if ocr_predictions and 'blocks' in ocr_predictions:
                for block in ocr_predictions['blocks']:
                    if not block.get('box'):
                        continue
                    
                    box = block['box']
                    # Convert to Label Studio format (percentages)
                    img_width = ocr_predictions.get('image_width', 1)
                    img_height = ocr_predictions.get('image_height', 1)
                    
                    prediction = {
                        'type': 'rectanglelabels',
                        'value': {
                            'x': (box['x'] / img_width) * 100,
                            'y': (box['y'] / img_height) * 100,
                            'width': (box['width'] / img_width) * 100,
                            'height': (box['height'] / img_height) * 100,
                            'rotation': 0,
                            'rectanglelabels': [block.get('field_type', 'OTHER').upper()]
                        },
                        'from_name': 'bbox',
                        'to_name': 'image'
                    }
                    
                    # Add transcription
                    if block.get('text'):
                        transcription = {
                            'type': 'textarea',
                            'value': {
                                'text': [block['text']]
                            },
                            'from_name': 'transcription',
                            'to_name': 'image'
                        }
                        predictions.append(prediction)
                        predictions.append(transcription)
            
            payload = {
                'data': task_data
            }
            
            if predictions:
                payload['predictions'] = [{
                    'result': predictions,
                    'model_version': 'paddle_ocr_v2'
                }]
            
            response = self.session.post(
                f'{self.base_url}/api/projects/{self.project_id}/tasks',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                task_id = response.json()['id']
                logger.info(f"✅ Uploaded task {task_id} for contact {contact_id}")
                return task_id
            else:
                logger.error(f"❌ Failed to upload task: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error uploading task: {e}")
            return None
    
    def get_annotations(self, min_annotations: int = 1) -> List[Dict]:
        """
        Export annotations from Label Studio for training
        """
        if not self.project_id:
            logger.error("No project_id set")
            return []
        
        try:
            response = self.session.get(
                f'{self.base_url}/api/projects/{self.project_id}/export',
                params={'exportType': 'JSON'},
                timeout=30
            )
            
            if response.status_code == 200:
                annotations = response.json()
                # Filter completed annotations
                completed = [
                    ann for ann in annotations
                    if len(ann.get('annotations', [])) >= min_annotations
                ]
                logger.info(f"✅ Exported {len(completed)} completed annotations")
                return completed
            else:
                logger.error(f"❌ Failed to export annotations: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error exporting annotations: {e}")
            return []
    
    def get_annotation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about annotations
        """
        if not self.project_id:
            return {}
        
        try:
            response = self.session.get(
                f'{self.base_url}/api/projects/{self.project_id}',
                timeout=10
            )
            
            if response.status_code == 200:
                project = response.json()
                return {
                    'total_tasks': project.get('task_number', 0),
                    'completed_tasks': project.get('num_tasks_with_annotations', 0),
                    'total_annotations': project.get('total_annotations_number', 0)
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}
    
    def convert_annotation_to_training_data(self, annotation: Dict) -> Dict:
        """
        Convert Label Studio annotation to training format
        """
        image_url = annotation['data'].get('image', '')
        contact_id = annotation['data'].get('contact_id')
        
        blocks = []
        for result in annotation.get('annotations', [{}])[0].get('result', []):
            if result['type'] == 'rectanglelabels':
                value = result['value']
                # Convert percentages back to pixels (needs image dimensions)
                block = {
                    'x': value['x'],  # percentage
                    'y': value['y'],
                    'width': value['width'],
                    'height': value['height'],
                    'label': value['rectanglelabels'][0],
                    'text': ''  # Will be filled from transcription
                }
                blocks.append(block)
        
        return {
            'image_url': image_url,
            'contact_id': contact_id,
            'blocks': blocks
        }

