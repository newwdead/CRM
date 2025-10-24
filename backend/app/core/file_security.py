"""
File Security Utilities
Provides comprehensive file upload security checks including:
- Magic bytes validation (actual file type detection)
- File size limits
- Filename sanitization
- EXIF metadata stripping from images
- ClamAV antivirus scanning (optional)
"""

import os
import re
import logging
import mimetypes
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)

# Allowed MIME types and their magic bytes signatures
ALLOWED_FILE_TYPES = {
    # Images
    'image/jpeg': [b'\xFF\xD8\xFF'],
    'image/jpg': [b'\xFF\xD8\xFF'],
    'image/png': [b'\x89PNG\r\n\x1a\n'],
    'image/gif': [b'GIF87a', b'GIF89a'],
    'image/webp': [b'RIFF'],
    'image/bmp': [b'BM'],
    'image/tiff': [b'II*\x00', b'MM\x00*'],
    
    # Documents
    'application/pdf': [b'%PDF-'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [b'PK\x03\x04'],  # .docx
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [b'PK\x03\x04'],  # .xlsx
    
    # Text
    'text/plain': [b''],  # Text files don't have magic bytes, validated separately
    'text/csv': [b''],
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    'image/jpeg': 10 * 1024 * 1024,  # 10 MB
    'image/png': 10 * 1024 * 1024,   # 10 MB
    'image/gif': 5 * 1024 * 1024,    # 5 MB
    'application/pdf': 20 * 1024 * 1024,  # 20 MB
    'default': 10 * 1024 * 1024,     # 10 MB default
}

# ClamAV configuration
CLAMAV_ENABLED = os.getenv("CLAMAV_ENABLED", "false").lower() == "true"
CLAMAV_SOCKET = os.getenv("CLAMAV_SOCKET", "/var/run/clamav/clamd.sock")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove any leading dots (hidden files)
    filename = filename.lstrip('.')
    
    # Limit length to 255 characters (filesystem limit)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # If filename is empty after sanitization, generate a random one
    if not filename:
        import uuid
        filename = f"file_{uuid.uuid4().hex[:8]}.bin"
    
    return filename


def detect_file_type(file_bytes: bytes, filename: str) -> Optional[str]:
    """
    Detect actual file type using magic bytes (not extension).
    
    Args:
        file_bytes: First 512 bytes of file
        filename: Original filename (for fallback)
        
    Returns:
        Detected MIME type or None if unknown/dangerous
    """
    # Check against known magic bytes
    for mime_type, signatures in ALLOWED_FILE_TYPES.items():
        for signature in signatures:
            if signature and file_bytes.startswith(signature):
                logger.debug(f"Detected {mime_type} by magic bytes")
                return mime_type
    
    # Special case for text files (no magic bytes)
    if filename.lower().endswith(('.txt', '.csv')):
        try:
            # Try to decode as UTF-8 text
            file_bytes.decode('utf-8')
            mime_type = 'text/plain' if filename.lower().endswith('.txt') else 'text/csv'
            logger.debug(f"Detected {mime_type} by UTF-8 decoding")
            return mime_type
        except UnicodeDecodeError:
            logger.warning(f"File claims to be text but is not valid UTF-8: {filename}")
            return None
    
    # Fallback: check MIME type by extension (less secure)
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and mime_type in ALLOWED_FILE_TYPES:
        logger.warning(f"Using extension-based MIME type (less secure): {mime_type}")
        return mime_type
    
    logger.error(f"Unknown or dangerous file type: {filename}")
    return None


def validate_file_size(file_size: int, mime_type: str) -> bool:
    """
    Validate file size against limits.
    
    Args:
        file_size: Size of file in bytes
        mime_type: MIME type of file
        
    Returns:
        True if size is acceptable, False otherwise
    """
    max_size = MAX_FILE_SIZES.get(mime_type, MAX_FILE_SIZES['default'])
    
    if file_size > max_size:
        logger.warning(f"File size {file_size} exceeds limit {max_size} for {mime_type}")
        return False
    
    return True


def strip_exif_data(image_path: str) -> bool:
    """
    Remove EXIF metadata from image file.
    This removes sensitive data like GPS coordinates, camera info, etc.
    
    Args:
        image_path: Path to image file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open image
        image = Image.open(image_path)
        
        # Get current EXIF data (for logging)
        exif_data = image._getexif()
        if exif_data:
            logger.info(f"Stripping EXIF data from {os.path.basename(image_path)}")
            logger.debug(f"Found {len(exif_data)} EXIF tags")
            
            # Log GPS data if present (privacy concern)
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag in ('GPSInfo', 'GPS'):
                    logger.warning(f"Removing GPS data from image: {os.path.basename(image_path)}")
        
        # Create new image without EXIF data
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        
        # Save without EXIF
        image_without_exif.save(image_path, quality=95, optimize=True)
        
        logger.info(f"EXIF data stripped successfully: {os.path.basename(image_path)}")
        return True
        
    except Exception as e:
        logger.error(f"Error stripping EXIF data: {e}")
        return False


def scan_file_with_clamav(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Scan file with ClamAV antivirus (if enabled).
    
    Args:
        file_path: Path to file to scan
        
    Returns:
        Tuple of (is_safe, threat_name)
        - (True, None) if file is safe
        - (False, threat_name) if threat detected
        - (True, None) if ClamAV disabled
    """
    if not CLAMAV_ENABLED:
        logger.debug("ClamAV scanning disabled")
        return (True, None)
    
    try:
        import pyclamd
        
        # Connect to ClamAV daemon
        if os.path.exists(CLAMAV_SOCKET):
            cd = pyclamd.ClamdUnixSocket(CLAMAV_SOCKET)
        else:
            cd = pyclamd.ClamdNetworkSocket()
        
        # Check if ClamAV is available
        if not cd.ping():
            logger.error("ClamAV daemon is not responding")
            # Fail open: allow file if ClamAV unavailable (or fail closed for security)
            return (True, None)  # Change to (False, "ClamAV unavailable") for fail-closed
        
        # Scan file
        result = cd.scan_file(file_path)
        
        if result is None:
            # File is clean
            logger.info(f"ClamAV: File is clean - {os.path.basename(file_path)}")
            return (True, None)
        else:
            # Threat detected
            threat_name = result[file_path][1] if file_path in result else "Unknown threat"
            logger.error(f"ClamAV: Threat detected - {threat_name} in {os.path.basename(file_path)}")
            return (False, threat_name)
            
    except ImportError:
        logger.warning("pyclamd library not installed, ClamAV scanning disabled")
        return (True, None)
    except Exception as e:
        logger.error(f"ClamAV scan error: {e}")
        # Fail open: allow file if scan fails (or fail closed for security)
        return (True, None)  # Change to (False, str(e)) for fail-closed


def validate_and_secure_file(
    file_content: bytes,
    filename: str,
    save_path: str
) -> Tuple[bool, str]:
    """
    Comprehensive file validation and security processing.
    
    Steps:
    1. Sanitize filename
    2. Detect actual file type (magic bytes)
    3. Validate file size
    4. Save file temporarily
    5. Strip EXIF data (for images)
    6. Scan with ClamAV (if enabled)
    7. Move to final location
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        save_path: Path where to save the file
        
    Returns:
        Tuple of (success, error_message)
        - (True, "success") if all checks pass
        - (False, error_message) if any check fails
    """
    try:
        # Step 1: Sanitize filename
        safe_filename = sanitize_filename(filename)
        logger.info(f"Processing file: {filename} -> {safe_filename}")
        
        # Step 2: Detect actual file type
        file_size = len(file_content)
        mime_type = detect_file_type(file_content[:512], safe_filename)
        
        if not mime_type:
            return (False, "Invalid or dangerous file type detected")
        
        # Step 3: Validate file size
        if not validate_file_size(file_size, mime_type):
            max_size = MAX_FILE_SIZES.get(mime_type, MAX_FILE_SIZES['default'])
            return (False, f"File size ({file_size} bytes) exceeds limit ({max_size} bytes)")
        
        # Step 4: Save file temporarily
        temp_path = f"{save_path}.tmp"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(file_content)
        
        logger.debug(f"File saved temporarily: {temp_path}")
        
        # Step 5: Strip EXIF data for images
        if mime_type.startswith('image/'):
            try:
                strip_exif_data(temp_path)
            except Exception as e:
                logger.warning(f"Could not strip EXIF data: {e}")
                # Continue anyway, not critical
        
        # Step 6: Scan with ClamAV
        is_safe, threat = scan_file_with_clamav(temp_path)
        
        if not is_safe:
            # Delete infected file
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Could not delete infected file: {e}")
            
            return (False, f"Malware detected: {threat}")
        
        # Step 7: Move to final location
        if os.path.exists(save_path):
            # Backup existing file
            backup_path = f"{save_path}.bak"
            os.rename(save_path, backup_path)
            logger.debug(f"Backed up existing file: {backup_path}")
        
        os.rename(temp_path, save_path)
        logger.info(f"File secured and saved: {save_path}")
        
        return (True, "success")
        
    except Exception as e:
        logger.error(f"Error in file validation: {e}", exc_info=True)
        
        # Cleanup temporary file if exists
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass
        
        return (False, f"File processing error: {str(e)}")


def get_file_info(file_path: str) -> dict:
    """
    Get comprehensive information about a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = os.stat(file_path)
        
        # Read first 512 bytes for magic byte detection
        with open(file_path, 'rb') as f:
            header = f.read(512)
        
        mime_type = detect_file_type(header, file_path)
        
        return {
            'filename': os.path.basename(file_path),
            'size': stat.st_size,
            'mime_type': mime_type,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'is_image': mime_type.startswith('image/') if mime_type else False,
            'has_exif': False,  # TODO: Implement EXIF detection
        }
        
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return {}
