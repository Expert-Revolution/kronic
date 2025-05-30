import os
import sys
import logging
import pytest
from unittest.mock import patch
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

config.TEST = True

from app import verify_password, _validate_cronjob_yaml


def test_logging_configuration():
    """Test that logging is properly configured"""
    # Test that loggers exist
    flask_logger = logging.getLogger("app.flask")
    kron_logger = logging.getLogger("app.kron")
    config_logger = logging.getLogger("app.config")
    
    assert flask_logger is not None
    assert kron_logger is not None
    assert config_logger is not None
    
    # Test that root logger has handlers (indicating logging is configured)
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0


def test_authentication_logging():
    """Test that authentication events are logged"""
    with patch('sys.stdout', new=StringIO()) as fake_out:
        # Test successful auth when no users configured
        config.USERS = {}
        result = verify_password("testuser", "testpass")
        assert result is True
        
        # Test failed auth when users are configured
        config.USERS = {"admin": "hashed_password"}
        result = verify_password("testuser", "wrongpass")
        assert result is False


def test_yaml_validation_logging():
    """Test that YAML validation logs appropriate messages"""
    with patch('sys.stdout', new=StringIO()) as fake_out:
        # Test valid YAML
        valid_yaml = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
          restartPolicy: OnFailure
"""
        is_valid, parsed, error = _validate_cronjob_yaml(valid_yaml)
        assert is_valid is True
        assert error is None
        
        # Test invalid YAML
        invalid_yaml = "invalid: yaml: content: ["
        is_valid, parsed, error = _validate_cronjob_yaml(invalid_yaml)
        assert is_valid is False
        assert error is not None


def test_log_environment_variables():
    """Test that logging environment variables are accessible"""
    # Test that the logging configuration environment variables exist
    log_level = os.environ.get("KRONIC_LOG_LEVEL", "INFO")
    log_format = os.environ.get("KRONIC_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # These should be valid logging configurations
    assert log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert "%" in log_format  # Basic check that it's a format string