"""Test security headers and middleware implementation."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import json

# Set test mode before importing any modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

config.TEST = True

from app.main import create_app
from app.core.security import (
    apply_security_headers,
    generate_csrf_token,
    validate_csrf_token,
)
from app.core.config import SECURITY_HEADERS


class TestSecurityHeaders:
    """Test security headers functionality."""

    def setup_method(self):
        """Set up test client."""
        with patch("app.core.config.TEST", True):
            self.app = create_app()
            self.client = self.app.test_client()
            self.app_context = self.app.app_context()
            self.app_context.push()

    def teardown_method(self):
        """Clean up after test."""
        if hasattr(self, "app_context"):
            self.app_context.pop()

    def test_security_headers_applied_to_responses(self):
        """Test that security headers are applied to all responses."""
        response = self.client.get("/api/v1/health")

        # Check that all expected security headers are present
        assert (
            response.headers.get("Strict-Transport-Security")
            == "max-age=31536000; includeSubDomains"
        )
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert (
            response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        )
        assert response.headers.get("Content-Security-Policy") is not None
        assert response.headers.get("Permissions-Policy") is not None

    def test_request_id_header_present(self):
        """Test that X-Request-ID header is present."""
        response = self.client.get("/api/v1/health")
        assert response.headers.get("X-Request-ID") is not None
        assert response.headers.get("X-Request-ID") != "unknown"

    def test_security_headers_can_be_disabled(self):
        """Test that security headers can be disabled via configuration."""
        with patch("app.core.config.SECURITY_HEADERS_ENABLED", False):
            with self.app.test_request_context():
                from flask import make_response

                response = make_response("test")
                result = apply_security_headers(response)

                # Headers should not be added when disabled
                assert "Strict-Transport-Security" not in result.headers
                assert "X-Frame-Options" not in result.headers

    def test_content_length_validation(self):
        """Test request content length validation."""
        # Test with content that exceeds the limit
        large_data = "x" * (17 * 1024 * 1024)  # 17MB, exceeds default 16MB limit

        response = self.client.post(
            "/api/v1/health", data=large_data, content_type="text/plain"
        )

        # Should return 413 Request Entity Too Large
        assert response.status_code == 413

    @patch("app.core.config.CSRF_ENABLED", True)
    def test_csrf_token_generation(self):
        """Test CSRF token generation."""
        with self.app.test_request_context():
            from flask import session

            token = generate_csrf_token()
            assert token is not None
            assert len(token) > 0
            assert session.get("csrf_token") == token

            # Second call should return same token
            token2 = generate_csrf_token()
            assert token == token2

    @patch("app.core.config.CSRF_ENABLED", False)
    def test_csrf_token_disabled(self):
        """Test CSRF token when disabled."""
        with self.app.test_request_context():
            token = generate_csrf_token()
            assert token is None

    @patch("app.core.config.CSRF_ENABLED", True)
    def test_csrf_validation_for_get_requests(self):
        """Test that CSRF validation is skipped for GET requests."""
        with self.app.test_request_context(method="GET"):
            result = validate_csrf_token()
            assert result is True

    @patch("app.core.config.CSRF_ENABLED", True)
    def test_csrf_validation_for_api_with_auth(self):
        """Test that CSRF validation is skipped for API requests with Authorization header."""
        with self.app.test_request_context(
            "/api/test", method="POST", headers={"Authorization": "Bearer token"}
        ):
            result = validate_csrf_token()
            assert result is True

    def test_csp_header_contains_required_directives(self):
        """Test that CSP header contains required security directives."""
        response = self.client.get("/api/v1/health")
        csp = response.headers.get("Content-Security-Policy")

        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "style-src" in csp

    def test_permissions_policy_header_present(self):
        """Test that Permissions-Policy header restricts dangerous features."""
        response = self.client.get("/api/v1/health")
        permissions = response.headers.get("Permissions-Policy")

        assert permissions is not None
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions

    def test_hsts_header_includes_subdomains(self):
        """Test that HSTS header includes subdomain protection."""
        response = self.client.get("/api/v1/health")
        hsts = response.headers.get("Strict-Transport-Security")

        assert hsts is not None
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    def test_x_frame_options_prevents_clickjacking(self):
        """Test that X-Frame-Options header prevents clickjacking."""
        response = self.client.get("/api/v1/health")
        frame_options = response.headers.get("X-Frame-Options")

        assert frame_options == "DENY"

    def test_x_content_type_options_prevents_mime_sniffing(self):
        """Test that X-Content-Type-Options prevents MIME sniffing."""
        response = self.client.get("/api/v1/health")
        content_type_options = response.headers.get("X-Content-Type-Options")

        assert content_type_options == "nosniff"

    def test_referrer_policy_limits_referrer_leakage(self):
        """Test that Referrer-Policy limits referrer information leakage."""
        response = self.client.get("/api/v1/health")
        referrer_policy = response.headers.get("Referrer-Policy")

        assert referrer_policy == "strict-origin-when-cross-origin"

    @patch("app.core.config.CSRF_ENABLED", True)
    def test_csrf_token_template_global(self):
        """Test that CSRF token is available in templates."""
        with self.app.test_request_context():
            from flask import render_template_string

            # Create a simple template that uses the csrf_token() function
            template = "{{ csrf_token() }}"
            result = render_template_string(template)

            # Should return a token string
            assert result is not None
            assert len(result) > 0
