"""
Active Learning Service
Automatically selects difficult cases for human annotation
"""
import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


class ActiveLearningService:
    """
    Active Learning: System intelligently selects which cards need human review
    
    Criteria for selection:
    1. Low confidence scores from OCR
    2. High disagreement between models
    3. Unusual layouts or patterns
    4. Recent model errors
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7  # Below this = needs review
        self.disagreement_threshold = 0.3  # Field assignment disagreement
    
    def should_send_for_annotation(self, ocr_result: Dict[str, Any]) -> Dict[str, bool]:
        """
        Decide if a card should be sent to Label Studio for annotation
        """
        reasons = []
        
        # Check 1: Low confidence blocks
        blocks = ocr_result.get('blocks', [])
        if blocks:
            confidences = [b.get('confidence', 1.0) for b in blocks]
            avg_confidence = np.mean(confidences)
            min_confidence = np.min(confidences)
            low_confidence_count = sum(1 for c in confidences if c < self.confidence_threshold)
            
            if avg_confidence < self.confidence_threshold:
                reasons.append(f'low_avg_confidence: {avg_confidence:.2f}')
            
            if min_confidence < 0.5:
                reasons.append(f'very_low_min_confidence: {min_confidence:.2f}')
            
            if low_confidence_count > len(blocks) * 0.3:
                reasons.append(f'many_low_confidence_blocks: {low_confidence_count}/{len(blocks)}')
        
        # Check 2: Missing critical fields
        extracted_fields = ocr_result.get('data', {})
        critical_fields = ['full_name', 'phone', 'email']
        missing_critical = [f for f in critical_fields if not extracted_fields.get(f)]
        
        if len(missing_critical) >= 2:
            reasons.append(f'missing_critical_fields: {", ".join(missing_critical)}')
        
        # Check 3: Too few or too many blocks (unusual)
        block_count = len(blocks)
        if block_count < 3:
            reasons.append(f'too_few_blocks: {block_count}')
        elif block_count > 30:
            reasons.append(f'too_many_blocks: {block_count}')
        
        # Check 4: LayoutLM uncertainty (if available)
        if 'layoutlm_confidence' in ocr_result:
            if ocr_result['layoutlm_confidence'] < 0.6:
                reasons.append(f"low_layoutlm_confidence: {ocr_result['layoutlm_confidence']:.2f}")
        
        # Decision
        should_annotate = len(reasons) > 0
        
        result = {
            'should_annotate': should_annotate,
            'reasons': reasons,
            'priority': len(reasons),  # More reasons = higher priority
            'confidence_score': np.mean(confidences) if blocks else 0.0
        }
        
        if should_annotate:
            logger.info(f"🎯 Card selected for annotation: {', '.join(reasons)}")
        
        return result
    
    def prioritize_for_annotation(self, cards: List[Dict]) -> List[Dict]:
        """
        Sort cards by priority for annotation (most difficult first)
        """
        prioritized = []
        
        for card in cards:
            analysis = self.should_send_for_annotation(card.get('ocr_result', {}))
            if analysis['should_annotate']:
                prioritized.append({
                    'contact_id': card.get('contact_id'),
                    'priority': analysis['priority'],
                    'reasons': analysis['reasons'],
                    'confidence': analysis['confidence_score']
                })
        
        # Sort by priority (descending) and confidence (ascending)
        prioritized.sort(key=lambda x: (-x['priority'], x['confidence']))
        
        return prioritized
    
    def get_annotation_recommendations(self, recent_cards: List[Dict], max_recommendations: int = 10) -> Dict[str, Any]:
        """
        Get recommendations for which cards to annotate
        """
        prioritized = self.prioritize_for_annotation(recent_cards)
        
        recommendations = prioritized[:max_recommendations]
        
        return {
            'total_candidates': len(prioritized),
            'recommendations': recommendations,
            'recommended_count': len(recommendations),
            'message': f'Found {len(recommendations)} cards that would benefit from human review'
        }
    
    def calculate_model_improvement(
        self,
        before_annotations: List[Dict],
        after_annotations: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate improvement in model performance after training on annotations
        """
        # Calculate average confidence before and after
        before_confidences = [
            np.mean([b.get('confidence', 0) for b in card.get('blocks', [])])
            for card in before_annotations
            if card.get('blocks')
        ]
        
        after_confidences = [
            np.mean([b.get('confidence', 0) for b in card.get('blocks', [])])
            for card in after_annotations
            if card.get('blocks')
        ]
        
        if not before_confidences or not after_confidences:
            return {'improvement': 0.0, 'message': 'Insufficient data'}
        
        before_avg = np.mean(before_confidences)
        after_avg = np.mean(after_confidences)
        improvement = ((after_avg - before_avg) / before_avg) * 100
        
        return {
            'before_confidence': float(before_avg),
            'after_confidence': float(after_avg),
            'improvement_percent': float(improvement),
            'sample_size_before': len(before_confidences),
            'sample_size_after': len(after_confidences),
            'message': f'Model confidence improved by {improvement:.1f}%' if improvement > 0 else 'No improvement detected'
        }

