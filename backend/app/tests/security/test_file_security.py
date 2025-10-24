"""
Tests for File Security utilities
"""
import pytest
import os
import tempfile
from pathlib import Path
from PIL import Image
import io

from app.utils.file_security import (
    sanitize_filename,
    detect_file_type,
    validate_file_size,
    strip_exif_data,
    validate_and_secure_file,
    get_file_info
)


class TestFilenameSanitization:
    """Test filename sanitization"""
    
    def test_basic_sanitization(self):
        """Test basic filename sanitization"""
        assert sanitize_filename("test.jpg") == "test.jpg"
        assert sanitize_filename("My Document.pdf") == "My_Document.pdf"
    
    def test_remove_path_components(self):
        """Test removal of directory traversal attempts"""
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\windows\\system32\\config") == "config"
    
    def test_remove_special_characters(self):
        """Test removal of dangerous characters"""
        assert sanitize_filename("file;rm -rf.jpg") == "filerm_-rf.jpg"
        assert sanitize_filename("file<script>.jpg") == "filescript.jpg"
    
    def test_remove_leading_dots(self):
        """Test removal of hidden file prefixes"""
        assert sanitize_filename(".htaccess") == "htaccess"
        assert sanitize_filename("...hidden") == "hidden"
    
    def test_length_limit(self):
        """Test filename length limiting"""
        long_name = "a" * 300 + ".jpg"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".jpg")
    
    def test_empty_filename(self):
        """Test handling of empty filenames"""
        result = sanitize_filename("")
        assert result.startswith("file_")
        assert result.endswith(".bin")


class TestFileTypeDetection:
    """Test file type detection using magic bytes"""
    
    def test_jpeg_detection(self):
        """Test JPEG file detection"""
        jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        assert detect_file_type(jpeg_header, "test.jpg") == "image/jpeg"
    
    def test_png_detection(self):
        """Test PNG file detection"""
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        assert detect_file_type(png_header, "test.png") == "image/png"
    
    def test_gif_detection(self):
        """Test GIF file detection"""
        gif_header = b'GIF89a'
        assert detect_file_type(gif_header, "test.gif") == "image/gif"
    
    def test_pdf_detection(self):
        """Test PDF file detection"""
        pdf_header = b'%PDF-1.4\n'
        assert detect_file_type(pdf_header, "test.pdf") == "application/pdf"
    
    def test_text_file_detection(self):
        """Test text file detection"""
        text_content = b'This is a text file\nwith multiple lines'
        assert detect_file_type(text_content, "test.txt") == "text/plain"
    
    def test_invalid_file_rejection(self):
        """Test rejection of unknown file types"""
        unknown_header = b'\x00\x00\x00\x00\x00\x00'
        assert detect_file_type(unknown_header, "test.exe") is None
    
    def test_extension_spoofing(self):
        """Test protection against extension spoofing"""
        # File claims to be .jpg but is actually .exe
        exe_header = b'MZ\x90\x00'  # PE executable header
        result = detect_file_type(exe_header, "image.jpg")
        # Should detect it's not actually an image
        assert result != "image/jpeg"


class TestFileSizeValidation:
    """Test file size validation"""
    
    def test_within_limit(self):
        """Test file within size limit"""
        assert validate_file_size(5 * 1024 * 1024, "image/jpeg") is True
    
    def test_exceeds_limit(self):
        """Test file exceeding size limit"""
        assert validate_file_size(50 * 1024 * 1024, "image/jpeg") is False
    
    def test_default_limit(self):
        """Test default size limit for unknown types"""
        assert validate_file_size(5 * 1024 * 1024, "application/unknown") is True
        assert validate_file_size(50 * 1024 * 1024, "application/unknown") is False


class TestEXIFStripping:
    """Test EXIF metadata removal"""
    
    def test_strip_exif_from_image(self):
        """Test EXIF data removal from image"""
        # Create temporary image with EXIF data
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create test image
            img = Image.new('RGB', (100, 100), color='red')
            
            # Add some EXIF data
            exif = img.getexif()
            exif[0x0112] = 1  # Orientation
            exif[0x010F] = "Test Camera"  # Make
            
            img.save(tmp.name, 'JPEG', exif=exif)
            tmp_path = tmp.name
        
        try:
            # Strip EXIF
            result = strip_exif_data(tmp_path)
            assert result is True
            
            # Verify EXIF is gone
            img_after = Image.open(tmp_path)
            exif_after = img_after._getexif()
            assert exif_after is None or len(exif_after) == 0
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_strip_exif_gps_data(self):
        """Test removal of GPS data from image"""
        # This is important for privacy - GPS coordinates should be removed
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (100, 100), color='blue')
            
            # Add GPS EXIF data
            exif = img.getexif()
            exif[0x8825] = {  # GPSInfo tag
                1: 'N',
                2: ((37, 1), (46, 1), (4329, 100)),  # Latitude
                3: 'W',
                4: ((122, 1), (25, 1), (912, 100)),  # Longitude
            }
            
            img.save(tmp.name, 'JPEG', exif=exif)
            tmp_path = tmp.name
        
        try:
            # Strip EXIF (including GPS)
            result = strip_exif_data(tmp_path)
            assert result is True
            
            # Verify GPS data is gone
            img_after = Image.open(tmp_path)
            exif_after = img_after._getexif()
            if exif_after:
                assert 0x8825 not in exif_after  # GPSInfo should be removed
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestComprehensiveFileValidation:
    """Test comprehensive file validation and securing"""
    
    def test_valid_jpeg_upload(self):
        """Test valid JPEG file upload"""
        # Create test JPEG
        img = Image.new('RGB', (200, 200), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        jpeg_bytes = img_bytes.getvalue()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, 'test.jpg')
            
            success, message = validate_and_secure_file(
                file_content=jpeg_bytes,
                filename='test.jpg',
                save_path=save_path
            )
            
            assert success is True
            assert message == "success"
            assert os.path.exists(save_path)
    
    def test_invalid_file_type(self):
        """Test rejection of invalid file type"""
        # Create fake executable
        exe_bytes = b'MZ\x90\x00' + b'\x00' * 100
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, 'malware.exe')
            
            success, message = validate_and_secure_file(
                file_content=exe_bytes,
                filename='malware.exe',
                save_path=save_path
            )
            
            assert success is False
            assert "Invalid or dangerous file type" in message
            assert not os.path.exists(save_path)
    
    def test_oversized_file(self):
        """Test rejection of oversized file"""
        # Create large fake JPEG
        jpeg_header = b'\xFF\xD8\xFF\xE0'
        large_bytes = jpeg_header + b'\x00' * (50 * 1024 * 1024)  # 50MB
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, 'huge.jpg')
            
            success, message = validate_and_secure_file(
                file_content=large_bytes,
                filename='huge.jpg',
                save_path=save_path
            )
            
            assert success is False
            assert "exceeds limit" in message
    
    def test_directory_traversal_attempt(self):
        """Test protection against directory traversal"""
        img = Image.new('RGB', (50, 50), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        jpeg_bytes = img_bytes.getvalue()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to save outside tmpdir
            malicious_filename = '../../../etc/passwd'
            save_path = os.path.join(tmpdir, 'safe.jpg')
            
            success, message = validate_and_secure_file(
                file_content=jpeg_bytes,
                filename=malicious_filename,
                save_path=save_path
            )
            
            # Should succeed but with sanitized filename
            assert success is True
            assert os.path.exists(save_path)
            # Verify file is inside tmpdir
            assert os.path.dirname(save_path) == tmpdir


class TestFileInfo:
    """Test file information retrieval"""
    
    def test_get_file_info(self):
        """Test getting file information"""
        # Create test file
        img = Image.new('RGB', (100, 100), color='yellow')
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            info = get_file_info(tmp_path)
            
            assert 'filename' in info
            assert 'size' in info
            assert 'mime_type' in info
            assert info['mime_type'] == 'image/jpeg'
            assert info['is_image'] is True
            assert info['size'] > 0
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# Integration tests (require ClamAV - skip if not available)
class TestClamAVIntegration:
    """Test ClamAV integration"""
    
    def test_clamav_clean_file(self):
        """Test ClamAV scanning of clean file"""
        # This test requires ClamAV to be installed and running
        # If not available, it should gracefully handle the absence
        pytest.skip("ClamAV integration test - requires ClamAV daemon")
    
    def test_clamav_infected_file(self):
        """Test ClamAV detection of infected file"""
        # Use EICAR test file (safe test virus signature)
        # This test requires ClamAV to be installed and running
        pytest.skip("ClamAV integration test - requires ClamAV daemon")


# Security regression tests
class TestSecurityRegression:
    """Test for known security vulnerabilities"""
    
    def test_zip_bomb_protection(self):
        """Test protection against zip bombs"""
        # TODO: Implement when archive support is added
        pytest.skip("Not yet implemented")
    
    def test_path_traversal_variants(self):
        """Test various path traversal attack patterns"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f",  # URL encoded
            "..%252f..%252f..%252fetc/passwd",  # Double URL encoded
        ]
        
        for dangerous_path in dangerous_paths:
            result = sanitize_filename(dangerous_path)
            # Should not contain any path traversal
            assert ".." not in result
            assert "/" not in result
            assert "\\" not in result
            assert "%" not in result
    
    def test_null_byte_injection(self):
        """Test protection against null byte injection"""
        # Null byte can truncate filenames in some systems
        result = sanitize_filename("test.jpg\x00.exe")
        assert "\x00" not in result
    
    def test_unicode_normalization(self):
        """Test handling of unicode in filenames"""
        unicode_name = "файл.jpg"  # Russian
        result = sanitize_filename(unicode_name)
        # Should handle unicode gracefully
        assert result != ""
        assert len(result) <= 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

