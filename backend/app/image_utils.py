"""
Image processing utilities
"""
import io
import os
from pathlib import Path
from PIL import Image


def downscale_image_bytes(data: bytes, max_side: int = 2000) -> bytes:
    """
    Downscale image bytes while preserving aspect ratio.
    
    Args:
        data: Original image bytes
        max_side: Maximum width or height
        
    Returns:
        Downscaled image bytes (JPEG)
    """
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert('RGB')
            # downscale in-place keeping aspect ratio
            im.thumbnail((max_side, max_side))
            out = io.BytesIO()
            im.save(out, format='JPEG', quality=90)
            return out.getvalue()
    except Exception:
        # if Pillow cannot open, return original
        return data


def create_thumbnail(image_path: str, size: tuple = (200, 200), quality: int = 85) -> str:
    """
    Create a thumbnail for the given image.
    
    Args:
        image_path: Path to the original image
        size: Thumbnail size (width, height), default (200, 200)
        quality: JPEG quality (1-100), default 85
    
    Returns:
        Path to the created thumbnail
    """
    try:
        # Generate thumbnail filename
        path_obj = Path(image_path)
        thumb_name = f"{path_obj.stem}_thumb{path_obj.suffix}"
        thumb_path = path_obj.parent / thumb_name
        
        # Open image and create thumbnail
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if 'A' in img.mode:
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG
            img.save(str(thumb_path), 'JPEG', quality=quality, optimize=True)
        
        return str(thumb_path)
        
    except Exception as e:
        # If thumbnail creation fails, return original path
        print(f"Failed to create thumbnail: {e}")
        return image_path

