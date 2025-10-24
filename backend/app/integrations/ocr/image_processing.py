"""
Image processing utilities for business card recognition.

Functions:
- auto_crop_card: Automatically detect and crop business card from image
- detect_multiple_cards: Detect and extract multiple business cards from single image
- enhance_image: Pre-process image for better OCR results
"""

import cv2
import numpy as np
from PIL import Image
import io
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to OpenCV format."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def cv2_to_bytes(img: np.ndarray, format: str = '.jpg', quality: int = 95) -> bytes:
    """Convert OpenCV image to bytes."""
    if format == '.jpg':
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    else:
        encode_param = []
    
    success, encoded_img = cv2.imencode(format, img, encode_param)
    if success:
        return encoded_img.tobytes()
    else:
        raise Exception("Failed to encode image")


def auto_crop_card(image_bytes: bytes, margin: int = 10) -> bytes:
    """
    Automatically detect and crop business card boundaries.
    
    Algorithm:
    1. Convert to grayscale
    2. Apply edge detection (Canny)
    3. Find largest contour (card boundary)
    4. Crop to bounding rectangle with margin
    
    Args:
        image_bytes: Input image as bytes
        margin: Extra margin to add around detected card (pixels)
    
    Returns:
        Cropped image as bytes
    """
    try:
        # Convert to OpenCV format
        img = bytes_to_cv2(image_bytes)
        if img is None:
            logger.warning("Failed to decode image for cropping")
            return image_bytes
        
        original_height, original_width = img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate edges to connect nearby contours
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            logger.warning("No contours found, returning original image")
            return image_bytes
        
        # Find the largest contour (likely the card)
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        
        # If contour is too small (< 10% of image), don't crop
        min_area = original_width * original_height * 0.1
        if contour_area < min_area:
            logger.warning(f"Largest contour too small ({contour_area} < {min_area}), returning original")
            return image_bytes
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Add margin
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(original_width - x, w + 2 * margin)
        h = min(original_height - y, h + 2 * margin)
        
        # Crop image
        cropped = img[y:y+h, x:x+w]
        
        # Convert back to bytes
        cropped_bytes = cv2_to_bytes(cropped)
        
        # Calculate space saved
        original_size = len(image_bytes)
        cropped_size = len(cropped_bytes)
        saved_percent = ((original_size - cropped_size) / original_size) * 100
        
        logger.info(f"Image cropped: {original_width}x{original_height} -> {w}x{h}, "
                   f"saved {saved_percent:.1f}% space ({original_size} -> {cropped_size} bytes)")
        
        return cropped_bytes
        
    except Exception as e:
        logger.error(f"Error in auto_crop_card: {e}")
        return image_bytes


def detect_multiple_cards(image_bytes: bytes, min_card_area_ratio: float = 0.05) -> List[bytes]:
    """
    Detect and extract multiple business cards from a single image.
    
    Algorithm:
    1. Convert to grayscale
    2. Apply edge detection
    3. Find all rectangular contours
    4. Filter contours by size and aspect ratio (typical business card proportions)
    5. Extract each detected card
    
    Args:
        image_bytes: Input image as bytes
        min_card_area_ratio: Minimum card area as ratio of total image (default 5%)
    
    Returns:
        List of extracted card images as bytes
    """
    try:
        # Convert to OpenCV format
        img = bytes_to_cv2(image_bytes)
        if img is None:
            logger.warning("Failed to decode image for multi-card detection")
            return [image_bytes]
        
        original_height, original_width = img.shape[:2]
        total_area = original_width * original_height
        min_card_area = total_area * min_card_area_ratio
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 30, 150)
        
        # Dilate edges
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and aspect ratio
        card_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Skip if too small
            if area < min_card_area:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Business cards typically have aspect ratio between 1.5:1 and 2:1
            aspect_ratio = max(w, h) / min(w, h)
            if 1.3 <= aspect_ratio <= 2.2:
                card_contours.append((x, y, w, h, area))
        
        # Sort contours by area (largest first)
        card_contours.sort(key=lambda c: c[4], reverse=True)
        
        # If no cards detected, return original image
        if len(card_contours) == 0:
            logger.info("No business cards detected, returning original image")
            return [image_bytes]
        
        # If only one card detected, just crop it
        if len(card_contours) == 1:
            x, y, w, h, _ = card_contours[0]
            cropped = img[y:y+h, x:x+w]
            logger.info(f"Single card detected and cropped: {w}x{h}")
            return [cv2_to_bytes(cropped)]
        
        # Multiple cards detected - extract each one
        extracted_cards = []
        for i, (x, y, w, h, area) in enumerate(card_contours[:5]):  # Limit to 5 cards max
            # Add small margin
            margin = 5
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(original_width - x, w + 2 * margin)
            h = min(original_height - y, h + 2 * margin)
            
            # Extract card
            card_img = img[y:y+h, x:x+w]
            card_bytes = cv2_to_bytes(card_img)
            extracted_cards.append(card_bytes)
            
            logger.info(f"Card {i+1} extracted: {w}x{h} ({area} px²)")
        
        logger.info(f"Detected and extracted {len(extracted_cards)} business cards")
        return extracted_cards
        
    except Exception as e:
        logger.error(f"Error in detect_multiple_cards: {e}")
        return [image_bytes]


def enhance_image_for_ocr(image_bytes: bytes) -> bytes:
    """
    Enhance image quality for better OCR results.
    
    Enhancements:
    - Increase contrast
    - Sharpen
    - Denoise
    - Adjust brightness if needed
    
    Args:
        image_bytes: Input image as bytes
    
    Returns:
        Enhanced image as bytes
    """
    try:
        img = bytes_to_cv2(image_bytes)
        if img is None:
            return image_bytes
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply adaptive histogram equalization for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Sharpen
        kernel = np.array([[-1,-1,-1], 
                          [-1, 9,-1], 
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Convert back to BGR for consistency
        result = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
        
        return cv2_to_bytes(result)
        
    except Exception as e:
        logger.error(f"Error in enhance_image_for_ocr: {e}")
        return image_bytes


def process_business_card_image(image_bytes: bytes, 
                                auto_crop: bool = True,
                                detect_multi: bool = True,
                                enhance: bool = False) -> List[bytes]:
    """
    Complete business card image processing pipeline.
    
    Args:
        image_bytes: Input image as bytes
        auto_crop: Whether to auto-crop the card
        detect_multi: Whether to detect multiple cards
        enhance: Whether to enhance image for OCR
    
    Returns:
        List of processed card images (1 or more)
    """
    try:
        # Step 1: Detect multiple cards if enabled
        if detect_multi:
            cards = detect_multiple_cards(image_bytes)
        else:
            cards = [image_bytes]
        
        # Step 2: Process each card
        processed_cards = []
        for idx, card_bytes in enumerate(cards):
            # Auto-crop if enabled (skip for multi-cards as they're already cropped)
            if auto_crop and len(cards) == 1:  # Only crop if single card
                card_bytes = auto_crop_card(card_bytes)
                logger.info(f"Applied auto-crop to single card")
            elif len(cards) > 1:
                logger.info(f"Card {idx+1}/{len(cards)}: Already cropped during detection")
            
            # Enhance if enabled
            if enhance:
                card_bytes = enhance_image_for_ocr(card_bytes)
            
            processed_cards.append(card_bytes)
        
        logger.info(f"Processed {len(processed_cards)} card(s) for OCR")
        
        return processed_cards
        
    except Exception as e:
        logger.error(f"Error in process_business_card_image: {e}")
        return [image_bytes]

