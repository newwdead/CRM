"""
Tests for Settings API endpoints
"""
import pytest
from fastapi import status


class TestSettingsEndpoints:
    """Test suite for /settings endpoints"""
    
    def test_get_system_settings_as_admin(self, client, admin_auth_token, db_session):
        """Test getting system settings as admin"""
        response = client.get(
            "/settings/system",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "database" in data
        assert "ocr" in data
        assert "telegram" in data
        assert "authentication" in data
        assert "application" in data
    
    def test_get_system_settings_as_regular_user(self, client, auth_token):
        """Test that regular users cannot access system settings"""
        response = client.get(
            "/settings/system",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_pending_users_as_admin(self, client, admin_auth_token):
        """Test getting pending users list as admin"""
        response = client.get(
            "/settings/pending-users",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_get_editable_settings_as_admin(self, client, admin_auth_token):
        """Test getting editable settings as admin"""
        response = client.get(
            "/settings/editable",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "ocr" in data
        assert "telegram" in data
        assert "redis" in data
        assert "celery" in data
    
    def test_update_editable_settings_as_admin(self, client, admin_auth_token, db_session):
        """Test updating editable settings as admin"""
        settings_data = {
            "ocr": {
                "tesseract_langs": "eng+rus+ukr"
            }
        }
        response = client.put(
            "/settings/editable",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
            json=settings_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_get_integrations_status_as_admin(self, client, admin_auth_token):
        """Test getting integrations status as admin"""
        response = client.get(
            "/settings/integrations/status",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "integrations" in data
        assert len(data["integrations"]) >= 4  # telegram, whatsapp, google_vision, parsio
    
    def test_toggle_integration_as_admin(self, client, admin_auth_token, db_session):
        """Test toggling integration on/off as admin"""
        response = client.post(
            "/settings/integrations/telegram/toggle",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
            json={"enabled": True}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["integration_id"] == "telegram"
        assert data["enabled"] is True
    
    def test_test_integration_as_admin(self, client, admin_auth_token):
        """Test integration connection test as admin"""
        response = client.post(
            "/settings/integrations/telegram/test",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.skip(reason="Requires parsio integration to be configured in test environment")
    def test_update_integration_config_as_admin(self, client, admin_auth_token, db_session):
        """Test updating integration configuration as admin"""
        config_data = {
            "api_key": "test_key_123",
            "timeout": 30
        }
        response = client.put(
            "/settings/integrations/parsio/config",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
            json=config_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_invalid_integration_id(self, client, admin_auth_token):
        """Test invalid integration ID returns error"""
        response = client.post(
            "/settings/integrations/invalid_integration/toggle",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
            json={"enabled": True}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

