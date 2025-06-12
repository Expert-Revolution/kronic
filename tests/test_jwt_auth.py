"""Test JWT authentication system."""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Set test environment before importing app modules
import os

os.environ["KRONIC_TEST"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app import app
from jwt_auth import (
    JWTManager,
    PasswordValidator,
    SecurePasswordManager,
    BruteForceProtection,
)
from auth_api import auth_bp


class TestJWTAuthentication:
    """Test JWT authentication features."""

    def setup_method(self):
        """Set up test client."""
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Valid password
        result = PasswordValidator.validate_password_strength("StrongPass123!")
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

        # Weak passwords
        weak_cases = [
            "short",  # Too short
            "alllowercase123!",  # No uppercase
            "ALLUPPERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecialChar123",  # No special characters
            "password",  # Common weak password
        ]

        for weak_password in weak_cases:
            result = PasswordValidator.validate_password_strength(weak_password)
            assert result["is_valid"] is False
            assert len(result["errors"]) > 0

    def test_secure_password_hashing(self):
        """Test bcrypt password hashing."""
        password = "TestPassword123!"

        # Hash password
        hashed = SecurePasswordManager.hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format

        # Verify password
        assert SecurePasswordManager.verify_password(password, hashed) is True
        assert SecurePasswordManager.verify_password("WrongPassword", hashed) is False

    def test_jwt_token_generation_and_verification(self):
        """Test JWT token generation and verification."""
        user_id = "test-user-id"
        email = "test@example.com"

        # Generate tokens
        tokens = JWTManager.generate_tokens(user_id, email)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens

        # Verify access token
        payload = JWTManager.verify_token(tokens["access_token"], "access")
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "access"

        # Verify refresh token
        payload = JWTManager.verify_token(tokens["refresh_token"], "refresh")
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "refresh"

    def test_jwt_token_refresh(self):
        """Test JWT token refresh functionality."""
        user_id = "test-user-id"
        email = "test@example.com"

        # Generate initial tokens
        tokens = JWTManager.generate_tokens(user_id, email)
        refresh_token = tokens["refresh_token"]

        # Refresh tokens
        new_tokens = JWTManager.refresh_access_token(refresh_token)
        assert new_tokens is not None
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

        # Verify new access token
        payload = JWTManager.verify_token(new_tokens["access_token"], "access")
        assert payload is not None
        assert payload["user_id"] == user_id

    def test_brute_force_protection(self):
        """Test brute force protection mechanism."""
        identifier = "test@example.com"

        # Skip this test if Redis is not available
        from jwt_auth import redis_client

        if not redis_client:
            pytest.skip("Redis not available for brute force protection testing")

        # Initially should not be blocked
        assert BruteForceProtection.is_blocked(identifier) is False

        # Record multiple failed attempts
        for _ in range(5):
            BruteForceProtection.record_failed_attempt(identifier)

        # Should now be blocked
        assert BruteForceProtection.is_blocked(identifier) is True

        # Clear attempts
        BruteForceProtection.clear_failed_attempts(identifier)
        assert BruteForceProtection.is_blocked(identifier) is False

    def test_login_page_renders(self):
        """Test that login page renders correctly."""
        response = self.client.get("/login")
        assert response.status_code == 200
        # Check for React mount point instead of static text
        assert b"login-root" in response.data
        # Check for React script inclusion
        assert b"/dist/login.js" in response.data

    @patch("auth_api.UserManager.authenticate_user")
    def test_login_api_success(self, mock_auth):
        """Test successful login API call."""
        # Mock successful authentication
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.is_verified = False  # Set explicit value instead of mock
        mock_user.last_login = datetime.now().astimezone()
        mock_auth.return_value = mock_user

        # Test login
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "test@example.com"

    @patch("auth_api.UserManager.authenticate_user")
    def test_login_api_failure(self, mock_auth):
        """Test failed login API call."""
        # Mock failed authentication
        mock_auth.return_value = None

        # Test login with wrong credentials
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword"},
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    @patch("auth_api.UserManager.create_user")
    def test_register_api_success(self, mock_create):
        """Test successful registration API call."""
        # Mock successful user creation
        mock_user = MagicMock()
        mock_user.id = "new-user-id"
        mock_user.email = "newuser@example.com"
        mock_user.is_verified = False
        mock_create.return_value = mock_user

        # Test registration
        response = self.client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "StrongPassword123!"},
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_api_weak_password(self):
        """Test registration with weak password."""
        response = self.client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "weak"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "details" in data

    def test_unauthenticated_redirect_to_login(self):
        """Test that unauthenticated web requests redirect to login."""
        # Mock authentication configured but user not authenticated (to test redirect behavior)
        with patch("config.USERS", {"admin": "hashed_password"}), patch(
            "config.DATABASE_ENABLED", False
        ), patch("kron.batch.list_cron_job_for_all_namespaces") as mock_list_cronjobs:
            # Mock an empty list of cronjobs
            mock_list_cronjobs.return_value.items = []

            response = self.client.get("/")
            assert response.status_code == 302
            # The redirect should go to the auth login page
            assert "/login" in response.location

    def test_api_requests_return_401_when_unauthenticated(self):
        """Test that API requests return 401 when unauthenticated."""
        # Test API endpoint without authentication
        response = self.client.get("/api/auth/profile")
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__])
