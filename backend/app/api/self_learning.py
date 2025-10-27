"""
Self-Learning OCR API Endpoints
Manage training, annotations, and active learning
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from ..database import get_db
from ..models import Contact, User
from ..core import auth as auth_utils
from ..integrations.label_studio import (
    LabelStudioService,
    TrainingService,
    ActiveLearningService
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/self-learning", tags=["self-learning"])

# Initialize services
label_studio = LabelStudioService()
training_service = TrainingService()
active_learning = ActiveLearningService()


@router.get('/status')
async def get_self_learning_status(
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get status of self-learning system
    """
    try:
        # Check Label Studio availability
        ls_available = label_studio.is_available()
        
        # Get training stats
        training_stats = training_service.get_training_stats()
        
        # Get annotation stats
        annotation_stats = {}
        if ls_available and label_studio.project_id:
            annotation_stats = label_studio.get_annotation_stats()
        
        return {
            'label_studio': {
                'available': ls_available,
                'url': label_studio.base_url,
                'project_id': label_studio.project_id,
                **annotation_stats
            },
            'training': training_stats,
            'status': 'active' if ls_available else 'unavailable'
        }
        
    except Exception as e:
        logger.error(f"Error getting self-learning status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/init-label-studio')
async def initialize_label_studio(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Initialize Label Studio project (admin only)
    """
    try:
        if not label_studio.is_available():
            raise HTTPException(
                status_code=503,
                detail="Label Studio is not available"
            )
        
        project_id = label_studio.create_project()
        
        if not project_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create Label Studio project"
            )
        
        return {
            'success': True,
            'project_id': project_id,
            'message': 'Label Studio project created successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing Label Studio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send-for-annotation/{contact_id}')
async def send_contact_for_annotation(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Send a specific contact to Label Studio for annotation
    """
    try:
        # Get contact
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Check if image exists
        if not contact.photo_path:
            raise HTTPException(status_code=400, detail="Contact has no image")
        
        # Prepare image URL (accessible to Label Studio)
        image_url = f"/api/files/{contact.photo_path}"
        
        # Get OCR predictions
        import json
        ocr_predictions = None
        if contact.ocr_raw:
            try:
                ocr_predictions = json.loads(contact.ocr_raw)
            except:
                pass
        
        # Upload to Label Studio
        task_id = label_studio.upload_task(
            image_url=image_url,
            contact_id=contact_id,
            ocr_predictions=ocr_predictions
        )
        
        if not task_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload task to Label Studio"
            )
        
        return {
            'success': True,
            'task_id': task_id,
            'contact_id': contact_id,
            'message': f'Contact {contact_id} sent to Label Studio for annotation'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending contact for annotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/recommendations')
async def get_annotation_recommendations(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get recommendations for which contacts to annotate (active learning)
    """
    try:
        import json
        
        # Get recent contacts with OCR data
        contacts = db.query(Contact)\
            .filter(Contact.ocr_raw.isnot(None))\
            .order_by(Contact.created_at.desc())\
            .limit(100)\
            .all()
        
        # Prepare cards for analysis
        cards = []
        for contact in contacts:
            try:
                ocr_result = json.loads(contact.ocr_raw)
                cards.append({
                    'contact_id': contact.id,
                    'ocr_result': ocr_result
                })
            except:
                continue
        
        # Get recommendations
        recommendations = active_learning.get_annotation_recommendations(
            recent_cards=cards,
            max_recommendations=limit
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/collect-training-data')
async def collect_training_data(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Collect training data from Label Studio annotations (admin only)
    """
    try:
        # Export annotations
        annotations = label_studio.get_annotations(min_annotations=1)
        
        if not annotations:
            return {
                'success': False,
                'message': 'No completed annotations found'
            }
        
        # Collect and save training data
        result = training_service.collect_training_data(annotations)
        
        return {
            'success': True,
            **result,
            'message': f"Collected {result['samples_count']} training samples"
        }
        
    except Exception as e:
        logger.error(f"Error collecting training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/trigger-training')
async def trigger_training(
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Trigger model training/fine-tuning (admin only)
    """
    try:
        # Check if we have enough data
        if not training_service.should_trigger_training():
            stats = training_service.get_training_stats()
            return {
                'success': False,
                'message': f"Not enough training data. Have {stats['total_training_samples']}, need {stats['min_samples_required']}"
            }
        
        # TODO: Implement actual training
        # For now, just return status
        return {
            'success': True,
            'message': 'Training scheduled (implementation pending)',
            'status': 'scheduled'
        }
        
    except Exception as e:
        logger.error(f"Error triggering training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/feedback/{contact_id}')
async def save_correction_feedback(
    contact_id: int,
    feedback_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Save user corrections as feedback for training
    Called automatically when user saves corrections in table editor
    """
    try:
        import json
        
        # Get contact
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Get original blocks
        original_blocks = []
        if contact.ocr_raw:
            try:
                ocr_data = json.loads(contact.ocr_raw)
                original_blocks = ocr_data.get('blocks', [])
            except:
                pass
        
        # Get corrected blocks
        corrected_blocks = feedback_data.get('blocks', [])
        
        # Create feedback
        feedback = training_service.create_feedback_from_corrections(
            contact_id=contact_id,
            original_blocks=original_blocks,
            corrected_blocks=corrected_blocks
        )
        
        # Count corrections
        total_corrections = sum(
            len(feedback['corrections'][key])
            for key in feedback['corrections']
        )
        
        if total_corrections > 0:
            logger.info(f"💡 Received {total_corrections} corrections for contact {contact_id}")
            
            return {
                'success': True,
                'corrections_count': total_corrections,
                'message': f'Saved {total_corrections} corrections for training'
            }
        else:
            return {
                'success': True,
                'corrections_count': 0,
                'message': 'No corrections detected'
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

