"""
Unit tests for phone number formatting utilities
"""
import pytest
from ...core.phone import format_phone_number


class TestPhoneFormatting:
    """Test phone number formatting functionality"""
    
    def test_russian_number_with_7(self):
        """Test formatting Russian number starting with 7"""
        assert format_phone_number("79001234567") == "+7 (900) 123-45-67"
    
    def test_russian_number_with_8(self):
        """Test formatting Russian number starting with 8 (converts to 7)"""
        assert format_phone_number("89001234567") == "+7 (900) 123-45-67"
    
    def test_russian_number_without_country_code(self):
        """Test formatting Russian mobile starting with 9 (adds 7)"""
        assert format_phone_number("9001234567") == "+7 (900) 123-45-67"
    
    def test_formatted_input(self):
        """Test already formatted number"""
        result = format_phone_number("+7 (900) 123-45-67")
        assert result == "+7 (900) 123-45-67"
    
    def test_number_with_spaces(self):
        """Test number with spaces"""
        result = format_phone_number("7 900 123 45 67")
        assert result == "+7 (900) 123-45-67"
    
    def test_number_with_dashes(self):
        """Test number with dashes"""
        result = format_phone_number("7-900-123-45-67")
        assert result == "+7 (900) 123-45-67"
    
    def test_number_with_parentheses(self):
        """Test number with parentheses but no plus"""
        result = format_phone_number("7(900)1234567")
        assert result == "+7 (900) 123-45-67"
    
    def test_empty_string(self):
        """Test empty string returns empty"""
        assert format_phone_number("") == ""
    
    def test_none_input(self):
        """Test None input returns empty"""
        assert format_phone_number(None) == ""
    
    def test_non_digit_only(self):
        """Test string with no digits returns empty"""
        assert format_phone_number("abc") == ""
    
    def test_short_number(self):
        """Test short number (not 11 digits) returns cleaned digits"""
        result = format_phone_number("123")
        assert result == "123"
    
    def test_international_number_not_russian(self):
        """Test non-Russian international number is formatted correctly"""
        result = format_phone_number("19175551234")  # US number
        # Function formats US numbers with country code and formatting
        assert result == "+1 (917) 555-1234"
    
    def test_special_characters(self):
        """Test number with special characters gets cleaned"""
        result = format_phone_number("+7 (900) 123-45-67 ext.100")
        assert "+7 (900) 123-45-67" in result or result.startswith("+7")
    
    def test_whitespace_only(self):
        """Test whitespace only returns empty"""
        assert format_phone_number("   ") == ""
    
    def test_multiple_formats(self):
        """Test various input formats normalize to same output"""
        formats = [
            "79001234567",
            "89001234567",
            "+79001234567",
            "7-900-123-45-67",
            "7 (900) 123-45-67",
            "+7 900 123 45 67"
        ]
        expected = "+7 (900) 123-45-67"
        
        for phone_format in formats:
            result = format_phone_number(phone_format)
            assert result == expected, f"Failed for format: {phone_format}"
    
    def test_preserves_valid_format(self):
        """Test that already valid format is preserved"""
        valid = "+7 (900) 123-45-67"
        assert format_phone_number(valid) == valid

