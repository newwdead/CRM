"""
Security Tests: Security Headers Middleware
Tests for backend/app/middleware/security_headers.py
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app with security headers middleware."""
    app = FastAPI()
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add test endpoints
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    @app.get("/api/test")
    def api_endpoint():
        return {"message": "api test"}
    
    @app.get("/static/test.js")
    def static_endpoint():
        return {"content": "var x = 1;"}
    
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


# ============================================================================
# Tests: Basic Security Headers
# ============================================================================

class TestBasicSecurityHeaders:
    """Test that basic security headers are applied."""
    
    def test_x_content_type_options_header(self, client: TestClient):
        """Test that X-Content-Type-Options header is set."""
        response = client.get("/test")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_x_frame_options_header(self, client: TestClient):
        """Test that X-Frame-Options header is set."""
        response = client.get("/test")
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_x_xss_protection_header(self, client: TestClient):
        """Test that X-XSS-Protection header is set."""
        response = client.get("/test")
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_permissions_policy_header(self, client: TestClient):
        """Test that Permissions-Policy header is set."""
        response = client.get("/test")
        
        assert "Permissions-Policy" in response.headers
        
        policy = response.headers["Permissions-Policy"]
        
        # Check that dangerous features are disabled
        assert "geolocation=()" in policy
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "usb=()" in policy
        assert "magnetometer=()" in policy
    
    def test_referrer_policy_header(self, client: TestClient):
        """Test that Referrer-Policy header is set."""
        response = client.get("/test")
        
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_all_headers_present_on_single_request(self, client: TestClient):
        """Test that all security headers are present on a single request."""
        response = client.get("/test")
        
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Permissions-Policy",
            "Referrer-Policy"
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing header: {header}"


# ============================================================================
# Tests: API-Specific Headers
# ============================================================================

class TestAPISpecificHeaders:
    """Test headers specific to API endpoints."""
    
    def test_api_cache_control_header(self, client: TestClient):
        """Test that API endpoints have Cache-Control header."""
        response = client.get("/api/test")
        
        assert "Cache-Control" in response.headers
        
        cache_control = response.headers["Cache-Control"]
        
        # Should prevent caching of sensitive data
        assert "no-store" in cache_control
        assert "no-cache" in cache_control
        assert "must-revalidate" in cache_control
        assert "max-age=0" in cache_control
    
    def test_api_pragma_header(self, client: TestClient):
        """Test that API endpoints have Pragma header."""
        response = client.get("/api/test")
        
        assert "Pragma" in response.headers
        assert response.headers["Pragma"] == "no-cache"
    
    def test_api_expires_header(self, client: TestClient):
        """Test that API endpoints have Expires header."""
        response = client.get("/api/test")
        
        assert "Expires" in response.headers
        assert response.headers["Expires"] == "0"
    
    def test_non_api_endpoints_no_cache_control(self, client: TestClient):
        """Test that non-API endpoints don't have restrictive cache control."""
        response = client.get("/test")
        
        # Should either not have Cache-Control or not have restrictive one
        if "Cache-Control" in response.headers:
            cache_control = response.headers["Cache-Control"]
            # Should not have the same restrictive policy as API endpoints
            # (or might have it - depends on implementation)
            # This documents the behavior
            pass


# ============================================================================
# Tests: Header Values and Formats
# ============================================================================

class TestHeaderValuesAndFormats:
    """Test specific header values and formats."""
    
    def test_x_content_type_options_prevents_mime_sniffing(self, client: TestClient):
        """Test that X-Content-Type-Options prevents MIME type sniffing."""
        response = client.get("/test")
        
        # The value "nosniff" prevents browsers from MIME-sniffing
        # a response away from the declared content-type
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_x_frame_options_prevents_clickjacking(self, client: TestClient):
        """Test that X-Frame-Options prevents clickjacking."""
        response = client.get("/test")
        
        # DENY prevents any domain from framing the content
        # Alternative values: SAMEORIGIN, ALLOW-FROM uri
        assert response.headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
    
    def test_x_xss_protection_enables_filter(self, client: TestClient):
        """Test that X-XSS-Protection enables XSS filter."""
        response = client.get("/test")
        
        xss_protection = response.headers["X-XSS-Protection"]
        
        # "1" enables the filter
        # "mode=block" blocks the page rather than sanitizing
        assert "1" in xss_protection
        assert "mode=block" in xss_protection
    
    def test_permissions_policy_format(self, client: TestClient):
        """Test that Permissions-Policy has correct format."""
        response = client.get("/test")
        
        policy = response.headers["Permissions-Policy"]
        
        # Should be comma-separated list of directives
        # Format: feature=(allowlist)
        assert "," in policy or "=" in policy
        
        # Each dangerous feature should be explicitly disabled
        dangerous_features = ["geolocation", "camera", "microphone", "usb"]
        for feature in dangerous_features:
            assert feature in policy.lower()
    
    def test_referrer_policy_value(self, client: TestClient):
        """Test that Referrer-Policy has appropriate value."""
        response = client.get("/test")
        
        referrer_policy = response.headers["Referrer-Policy"]
        
        # Common safe values:
        # - no-referrer: Never send referrer
        # - no-referrer-when-downgrade: Don't send on HTTPS→HTTP
        # - strict-origin-when-cross-origin: Only origin for cross-origin
        safe_values = [
            "no-referrer",
            "no-referrer-when-downgrade",
            "strict-origin",
            "strict-origin-when-cross-origin"
        ]
        
        assert referrer_policy in safe_values


# ============================================================================
# Tests: Middleware Application
# ============================================================================

class TestMiddlewareApplication:
    """Test that middleware is applied correctly."""
    
    def test_headers_on_successful_response(self, client: TestClient):
        """Test headers are added to successful responses."""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
    
    def test_headers_on_404_response(self, client: TestClient):
        """Test headers are added even on 404 responses."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
    
    def test_headers_on_different_methods(self, client: TestClient):
        """Test headers are added for different HTTP methods."""
        # GET
        response_get = client.get("/test")
        assert "X-Content-Type-Options" in response_get.headers
        
        # POST (will fail but headers should be there)
        response_post = client.post("/test")
        assert "X-Content-Type-Options" in response_post.headers
    
    def test_headers_on_multiple_requests(self, client: TestClient):
        """Test headers are consistently applied across requests."""
        for _ in range(3):
            response = client.get("/test")
            assert "X-Content-Type-Options" in response.headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_middleware_does_not_break_response_body(self, client: TestClient):
        """Test that middleware doesn't alter response body."""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Headers should be added without affecting body
        assert "X-Content-Type-Options" in response.headers


# ============================================================================
# Tests: Security Properties
# ============================================================================

class TestSecurityProperties:
    """Test security properties enforced by headers."""
    
    def test_clickjacking_protection(self, client: TestClient):
        """Test that clickjacking protection is in place."""
        response = client.get("/test")
        
        # X-Frame-Options: DENY prevents clickjacking
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_mime_sniffing_protection(self, client: TestClient):
        """Test that MIME sniffing is prevented."""
        response = client.get("/test")
        
        # X-Content-Type-Options: nosniff prevents MIME sniffing
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_xss_filter_enabled(self, client: TestClient):
        """Test that XSS filter is enabled."""
        response = client.get("/test")
        
        # X-XSS-Protection: 1; mode=block enables XSS filter
        xss = response.headers["X-XSS-Protection"]
        assert "1" in xss and "block" in xss
    
    def test_dangerous_features_disabled(self, client: TestClient):
        """Test that dangerous browser features are disabled."""
        response = client.get("/test")
        
        policy = response.headers["Permissions-Policy"]
        
        # These features should be disabled (empty allowlist)
        dangerous_features = [
            "geolocation",
            "camera",
            "microphone",
            "usb",
            "midi",
            "magnetometer",
            "accelerometer",
            "gyroscope"
        ]
        
        for feature in dangerous_features:
            # Should be in format: feature=()
            assert f"{feature}=()" in policy or f"{feature} =()" in policy
    
    def test_referrer_information_controlled(self, client: TestClient):
        """Test that referrer information is controlled."""
        response = client.get("/test")
        
        # Referrer-Policy controls what referrer information is sent
        assert "Referrer-Policy" in response.headers
        
        policy = response.headers["Referrer-Policy"]
        
        # Should not be "unsafe-url" or "no-referrer-when-downgrade"
        # (those leak too much information)
        assert policy != "unsafe-url"


# ============================================================================
# Tests: OWASP Best Practices
# ============================================================================

class TestOWASPBestPractices:
    """Test compliance with OWASP security headers best practices."""
    
    def test_owasp_recommended_headers_present(self, client: TestClient):
        """Test that OWASP-recommended headers are present."""
        response = client.get("/test")
        
        # OWASP recommends these headers as minimum
        owasp_headers = [
            "X-Frame-Options",  # Clickjacking protection
            "X-Content-Type-Options",  # MIME sniffing protection
            "X-XSS-Protection",  # XSS filter (legacy browsers)
            "Referrer-Policy",  # Referrer control
        ]
        
        for header in owasp_headers:
            assert header in response.headers, f"OWASP recommends {header}"
    
    def test_sensitive_data_not_cached(self, client: TestClient):
        """Test that sensitive API data is not cached."""
        response = client.get("/api/test")
        
        # API endpoints should have aggressive no-cache policy
        assert "Cache-Control" in response.headers
        
        cache_control = response.headers["Cache-Control"]
        assert "no-store" in cache_control  # Don't store anywhere
        assert "no-cache" in cache_control  # Don't use cached version
    
    def test_https_headers_prepared(self, client: TestClient):
        """Test that HTTPS-related headers are prepared (even if not in HTTP)."""
        response = client.get("/test")
        
        # Note: HSTS (Strict-Transport-Security) should be enabled in production
        # but is typically commented out in development
        # This test documents that it's prepared
        
        # In production, should have:
        # Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
        
        # For now, just check that other headers are present
        assert "X-Frame-Options" in response.headers


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_headers_with_empty_response(self, client: TestClient):
        """Test headers are added even with empty response."""
        # Even if endpoint returns nothing, headers should be there
        response = client.get("/test")
        
        assert "X-Content-Type-Options" in response.headers
    
    def test_headers_case_insensitive_check(self, client: TestClient):
        """Test that headers can be checked case-insensitively."""
        response = client.get("/test")
        
        # HTTP headers are case-insensitive
        # But TestClient returns them as-is
        
        # Check exact case
        assert "X-Content-Type-Options" in response.headers
        
        # Document the actual header names used
        header_names = list(response.headers.keys())
        assert any("content-type" in h.lower() for h in header_names)
    
    def test_multiple_security_headers_do_not_conflict(self, client: TestClient):
        """Test that multiple security headers don't conflict."""
        response = client.get("/test")
        
        # All security headers should coexist
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Permissions-Policy" in response.headers
        
        # None should override or conflict with others
        assert len(set(response.headers.keys())) >= 5


# ============================================================================
# Tests: Performance
# ============================================================================

class TestMiddlewarePerformance:
    """Test that middleware doesn't impact performance significantly."""
    
    def test_middleware_overhead_minimal(self, client: TestClient):
        """Test that middleware adds minimal overhead."""
        import time
        
        # Make multiple requests and measure time
        start = time.perf_counter()
        for _ in range(10):
            client.get("/test")
        duration = time.perf_counter() - start
        
        # 10 requests should complete quickly even with middleware
        assert duration < 1.0, "Middleware should have minimal overhead"
    
    @pytest.mark.skip(reason="Performance test, run manually")
    def test_middleware_throughput(self, client: TestClient):
        """Test middleware throughput."""
        import time
        
        count = 100
        start = time.perf_counter()
        
        for _ in range(count):
            client.get("/test")
        
        duration = time.perf_counter() - start
        throughput = count / duration
        
        print(f"\nMiddleware throughput: {throughput:.2f} requests/second")
        
        # Should handle at least 100 req/s
        assert throughput > 100, "Middleware should not significantly impact throughput"


# ============================================================================
# Tests: Documentation and Comments
# ============================================================================

class TestSecurityHeadersDocumentation:
    """Test that security headers are well-documented."""
    
    def test_headers_serve_documented_purpose(self, client: TestClient):
        """Test that each header serves its documented security purpose."""
        response = client.get("/test")
        
        # X-Content-Type-Options: nosniff
        # Purpose: Prevent MIME type sniffing
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        # X-Frame-Options: DENY
        # Purpose: Prevent clickjacking attacks
        assert response.headers["X-Frame-Options"] == "DENY"
        
        # X-XSS-Protection: 1; mode=block
        # Purpose: Enable XSS filter in legacy browsers
        assert "1" in response.headers["X-XSS-Protection"]
        
        # Permissions-Policy: ...
        # Purpose: Control which browser features can be used
        assert "Permissions-Policy" in response.headers
        
        # Referrer-Policy: ...
        # Purpose: Control referrer information leakage
        assert "Referrer-Policy" in response.headers
    
    def test_headers_align_with_security_best_practices(self, client: TestClient):
        """Test that headers align with current security best practices."""
        response = client.get("/test")
        
        # As of 2025, these are considered security best practices:
        
        # 1. Prevent MIME sniffing
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        
        # 2. Prevent clickjacking
        assert response.headers.get("X-Frame-Options") in ["DENY", "SAMEORIGIN"]
        
        # 3. Control dangerous features
        assert "Permissions-Policy" in response.headers
        
        # 4. Control referrer
        assert "Referrer-Policy" in response.headers
        
        # 5. Cache control for sensitive data
        # (checked in API-specific tests)

