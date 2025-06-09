import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_config_admin_password_setup():
    """Test admin password configuration"""
    # Import here to avoid interference with module-level config
    import importlib
    import config

    # Store original values
    original_admin_password = os.environ.get("KRONIC_ADMIN_PASSWORD")
    original_admin_username = os.environ.get("KRONIC_ADMIN_USERNAME")

    try:
        # Test with admin password set
        os.environ["KRONIC_ADMIN_PASSWORD"] = "testpass"
        os.environ["KRONIC_ADMIN_USERNAME"] = "testuser"

        # Reload config module to pick up new env vars
        importlib.reload(config)

        assert "testuser" in config.USERS
        assert config.USERS["testuser"] is not None  # password hash exists

    finally:
        # Restore original values
        if original_admin_password:
            os.environ["KRONIC_ADMIN_PASSWORD"] = original_admin_password
        else:
            os.environ.pop("KRONIC_ADMIN_PASSWORD", None)

        if original_admin_username:
            os.environ["KRONIC_ADMIN_USERNAME"] = original_admin_username
        else:
            os.environ.pop("KRONIC_ADMIN_USERNAME", None)

        # Reload config to restore original state
        importlib.reload(config)


def test_config_no_admin_password():
    """Test configuration when no admin password is set"""
    import importlib
    import config

    # Store original values
    original_admin_password = os.environ.get("KRONIC_ADMIN_PASSWORD")

    try:
        # Remove admin password
        os.environ.pop("KRONIC_ADMIN_PASSWORD", None)

        # Reload config module
        importlib.reload(config)

        assert config.USERS == {}

    finally:
        # Restore original value
        if original_admin_password:
            os.environ["KRONIC_ADMIN_PASSWORD"] = original_admin_password

        # Reload config to restore original state
        importlib.reload(config)


@patch("sys.exit")
def test_config_namespace_only_missing_kronic_namespace(mock_exit):
    """Test NAMESPACE_ONLY mode without KRONIC_NAMESPACE set"""
    import importlib
    import config

    # Store original values
    original_namespace_only = os.environ.get("KRONIC_NAMESPACE_ONLY")
    original_kronic_namespace = os.environ.get("KRONIC_NAMESPACE")

    try:
        # Set NAMESPACE_ONLY but remove KRONIC_NAMESPACE
        os.environ["KRONIC_NAMESPACE_ONLY"] = "true"
        os.environ.pop("KRONIC_NAMESPACE", None)

        # Reload config module - should call sys.exit(1)
        importlib.reload(config)

        # Should have called sys.exit(1)
        mock_exit.assert_called_with(1)

    finally:
        # Restore original values
        if original_namespace_only:
            os.environ["KRONIC_NAMESPACE_ONLY"] = original_namespace_only
        else:
            os.environ.pop("KRONIC_NAMESPACE_ONLY", None)

        if original_kronic_namespace:
            os.environ["KRONIC_NAMESPACE"] = original_kronic_namespace

        # Reload config to restore original state
        importlib.reload(config)


def test_config_namespace_only_with_kronic_namespace():
    """Test NAMESPACE_ONLY mode with KRONIC_NAMESPACE set"""
    import importlib
    import config

    # Store original values
    original_namespace_only = os.environ.get("KRONIC_NAMESPACE_ONLY")
    original_kronic_namespace = os.environ.get("KRONIC_NAMESPACE")

    try:
        # Set both NAMESPACE_ONLY and KRONIC_NAMESPACE
        os.environ["KRONIC_NAMESPACE_ONLY"] = "true"
        os.environ["KRONIC_NAMESPACE"] = "test-namespace"

        # Reload config module
        importlib.reload(config)

        # Should set ALLOW_NAMESPACES to the KRONIC_NAMESPACE
        assert config.KRONIC_NAMESPACE == "test-namespace"
        assert config.ALLOW_NAMESPACES == "test-namespace"

    finally:
        # Restore original values
        if original_namespace_only:
            os.environ["KRONIC_NAMESPACE_ONLY"] = original_namespace_only
        else:
            os.environ.pop("KRONIC_NAMESPACE_ONLY", None)

        if original_kronic_namespace:
            os.environ["KRONIC_NAMESPACE"] = original_kronic_namespace
        else:
            os.environ.pop("KRONIC_NAMESPACE", None)

        # Reload config to restore original state
        importlib.reload(config)


def test_config_log_level_configuration():
    """Test log level configuration from environment"""
    import importlib
    import config

    # Store original value
    original_log_level = os.environ.get("KRONIC_LOG_LEVEL")

    try:
        # Set custom log level
        os.environ["KRONIC_LOG_LEVEL"] = "DEBUG"

        # Reload config module
        importlib.reload(config)

        assert config.LOG_LEVEL == "DEBUG"

    finally:
        # Restore original value
        if original_log_level:
            os.environ["KRONIC_LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("KRONIC_LOG_LEVEL", None)

        # Reload config to restore original state
        importlib.reload(config)
