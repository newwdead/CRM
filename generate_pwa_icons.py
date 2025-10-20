#!/usr/bin/env python3
"""
Generate PWA icons from SVG
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a simple PWA icon"""
    # Create image with gradient-like background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient effect
    for y in range(size):
        # Interpolate between two colors
        r1, g1, b1 = 102, 126, 234  # #667eea
        r2, g2, b2 = 118, 75, 162   # #764ba2
        
        t = y / size
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    
    # Draw business card
    card_width = int(size * 0.625)
    card_height = int(size * 0.39)
    card_x = (size - card_width) // 2
    card_y = int(size * 0.27)
    card_radius = int(size * 0.03)
    
    # Shadow
    shadow_offset = int(size * 0.03)
    draw.rounded_rectangle(
        [card_x + shadow_offset, card_y + shadow_offset,
         card_x + card_width + shadow_offset, card_y + card_height + shadow_offset],
        radius=card_radius,
        fill=(255, 255, 255, 51)
    )
    
    # Card
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_width, card_y + card_height],
        radius=card_radius,
        fill='white'
    )
    
    # Card details (lines)
    line_x = card_x + int(size * 0.078)
    line_y_start = card_y + int(size * 0.078)
    line_height = int(size * 0.031)
    line_spacing = int(size * 0.059)
    
    # First line (thicker, colored)
    draw.rounded_rectangle(
        [line_x, line_y_start, 
         line_x + int(size * 0.273), line_y_start + line_height],
        radius=int(size * 0.008),
        fill='#667eea'
    )
    
    # Other lines (gray)
    for i in range(1, 4):
        y = line_y_start + (i * line_spacing)
        width = int(size * (0.39 if i == 1 else 0.313 if i == 2 else 0.352))
        draw.rounded_rectangle(
            [line_x, y, line_x + width, y + int(size * 0.023)],
            radius=int(size * 0.008),
            fill='#999999'
        )
    
    # QR code icon (top right)
    qr_size = int(size * 0.098)
    qr_x = card_x + card_width - qr_size - int(size * 0.059)
    qr_y = card_y + int(size * 0.078)
    
    # QR background
    draw.rounded_rectangle(
        [qr_x, qr_y, qr_x + qr_size, qr_y + qr_size],
        radius=int(size * 0.008),
        fill=(102, 126, 234, 51)
    )
    
    # QR pattern
    block_size = int(qr_size / 5)
    qr_pattern = [
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1],
    ]
    
    for row in range(5):
        for col in range(5):
            if qr_pattern[row][col]:
                x = qr_x + (col * block_size) + int(block_size * 0.1)
                y = qr_y + (row * block_size) + int(block_size * 0.1)
                draw.rectangle(
                    [x, y, x + int(block_size * 0.8), y + int(block_size * 0.8)],
                    fill='#667eea'
                )
    
    # Save
    img.save(output_path, 'PNG', optimize=True)
    print(f'Created: {output_path} ({size}x{size})')

if __name__ == '__main__':
    output_dir = 'frontend/public'
    
    # Create icons
    create_icon(192, os.path.join(output_dir, 'icon-192.png'))
    create_icon(512, os.path.join(output_dir, 'icon-512.png'))
    
    print('PWA icons generated successfully!')

