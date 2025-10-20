"""
Tesseract Bounding Boxes Module
Extract bounding boxes and text blocks from images using Tesseract OCR
"""
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def get_text_blocks(image_bytes: bytes, lang='rus+eng') -> dict:
    """
    Extract text blocks with bounding boxes from image using Tesseract.
    
    Returns:
        {
            'blocks': [
                {
                    'text': 'Extracted text',
                    'confidence': 95.5,
                    'box': {'x': 100, 'y': 50, 'width': 200, 'height': 30},
                    'level': 4  # word level
                },
                ...
            ],
            'image_width': 1200,
            'image_height': 800
        }
    """
    try:
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        image_width, image_height = image.size
        
        # Get detailed OCR data with bounding boxes
        # level: 1=page, 2=block, 3=para, 4=line, 5=word
        ocr_data = pytesseract.image_to_data(
            image, 
            lang=lang, 
            output_type=pytesseract.Output.DICT
        )
        
        # Extract blocks
        blocks = []
        n_boxes = len(ocr_data['text'])
        
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            conf = float(ocr_data['conf'][i])
            
            # Skip empty text and low confidence
            if not text or conf < 0:
                continue
            
            # Get bounding box coordinates
            x = int(ocr_data['left'][i])
            y = int(ocr_data['top'][i])
            w = int(ocr_data['width'][i])
            h = int(ocr_data['height'][i])
            
            # Get level (5=word, 4=line, 3=para, 2=block)
            level = int(ocr_data['level'][i])
            
            blocks.append({
                'text': text,
                'confidence': conf,
                'box': {
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                },
                'level': level,
                'block_num': int(ocr_data['block_num'][i]),
                'par_num': int(ocr_data['par_num'][i]),
                'line_num': int(ocr_data['line_num'][i]),
                'word_num': int(ocr_data['word_num'][i])
            })
        
        logger.info(f"Extracted {len(blocks)} text blocks from image")
        
        return {
            'blocks': blocks,
            'image_width': image_width,
            'image_height': image_height
        }
        
    except Exception as e:
        logger.error(f"Error extracting text blocks: {e}")
        raise


def group_blocks_by_line(blocks: list) -> list:
    """
    Group word-level blocks into lines for easier visualization.
    
    Returns:
        [
            {
                'text': 'Full line text',
                'confidence': 92.3,
                'box': {'x': 100, 'y': 50, 'width': 300, 'height': 25},
                'words': [...]  # original word blocks
            },
            ...
        ]
    """
    if not blocks:
        return []
    
    # Group by line_num
    lines_dict = {}
    for block in blocks:
        line_key = (block['block_num'], block['par_num'], block['line_num'])
        if line_key not in lines_dict:
            lines_dict[line_key] = []
        lines_dict[line_key].append(block)
    
    # Create line objects
    lines = []
    for line_key, words in lines_dict.items():
        if not words:
            continue
        
        # Combine text
        text = ' '.join(w['text'] for w in words)
        
        # Average confidence
        avg_conf = sum(w['confidence'] for w in words) / len(words)
        
        # Calculate bounding box for entire line
        min_x = min(w['box']['x'] for w in words)
        min_y = min(w['box']['y'] for w in words)
        max_x = max(w['box']['x'] + w['box']['width'] for w in words)
        max_y = max(w['box']['y'] + w['box']['height'] for w in words)
        
        lines.append({
            'text': text,
            'confidence': avg_conf,
            'box': {
                'x': min_x,
                'y': min_y,
                'width': max_x - min_x,
                'height': max_y - min_y
            },
            'words': words
        })
    
    # Sort by Y position (top to bottom)
    lines.sort(key=lambda l: l['box']['y'])
    
    return lines

