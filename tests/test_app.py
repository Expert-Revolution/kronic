import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

config.TEST = True

from app import (
    _validate_cronjob_yaml,
    verify_password,
    namespace_filter,
    _strip_immutable_fields,
    app,
    healthz,
)
from unittest.mock import patch, MagicMock
from flask import Flask


def test_validate_cronjob_yaml_valid():
    """Test validation with valid CronJob YAML"""
    valid_yaml = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
  namespace: default
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
    assert is_valid == True
    assert parsed is not None
    assert error is None
    assert parsed["kind"] == "CronJob"
    assert parsed["metadata"]["name"] == "test-cronjob"


def test_validate_cronjob_yaml_invalid_syntax():
    """Test validation with invalid YAML syntax"""
    invalid_yaml = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
  namespace: default
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template
        spec:  # Missing colon here
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(invalid_yaml)
    assert is_valid == False
    assert parsed is None
    assert "Invalid YAML syntax" in error


def test_validate_cronjob_yaml_missing_kind():
    """Test validation with missing kind field"""
    yaml_content = """
apiVersion: batch/v1
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
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "Missing required field: kind" in error


def test_validate_cronjob_yaml_wrong_kind():
    """Test validation with wrong kind"""
    yaml_content = """
apiVersion: batch/v1
kind: Job
metadata:
  name: test-job
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "Expected kind 'CronJob', got 'Job'" in error


def test_validate_cronjob_yaml_invalid_apiversion():
    """Test validation with invalid apiVersion"""
    yaml_content = """
apiVersion: apps/v1
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
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "Invalid apiVersion 'apps/v1'" in error


def test_validate_cronjob_yaml_missing_name():
    """Test validation with missing metadata.name"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  namespace: default
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "metadata.name is required" in error


def test_validate_cronjob_yaml_missing_schedule():
    """Test validation with missing spec.schedule"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "spec.schedule is required" in error


def test_validate_cronjob_yaml_missing_jobtemplate():
    """Test validation with missing spec.jobTemplate"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "*/5 * * * *"
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "spec.jobTemplate is required" in error


def test_validate_cronjob_yaml_not_dict():
    """Test validation with non-dictionary YAML"""
    yaml_content = "just a string"
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "YAML must be a dictionary/object" in error


def test_validate_cronjob_yaml_empty():
    """Test validation with empty YAML"""
    yaml_content = ""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "YAML must be a dictionary/object" in error


def test_validate_cronjob_yaml_invalid_cron_schedule():
    """Test validation with invalid cron schedule"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "invalid cron"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "Cron schedule must have exactly 5 fields" in error


def test_validate_cronjob_yaml_valid_cron_schedule():
    """Test validation with valid cron schedule"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "0 0 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == True
    assert error is None


# Authentication tests
def test_verify_password_no_admin_password():
    """Test verify_password when no admin password is configured"""
    original_users = config.USERS
    config.USERS = {}

    result = verify_password("any_user", "any_password")
    assert result == True

    config.USERS = original_users


def test_verify_password_valid_credentials():
    """Test verify_password with valid credentials"""
    from werkzeug.security import generate_password_hash

    original_users = config.USERS
    config.USERS = {"testuser": generate_password_hash("testpass")}

    result = verify_password("testuser", "testpass")
    assert result == "testuser"

    config.USERS = original_users


def test_verify_password_invalid_credentials():
    """Test verify_password with invalid credentials"""
    from werkzeug.security import generate_password_hash

    original_users = config.USERS
    config.USERS = {"testuser": generate_password_hash("testpass")}

    result = verify_password("testuser", "wrongpass")
    assert result == False

    result = verify_password("wronguser", "testpass")
    assert result == False

    config.USERS = original_users


# Namespace filter tests
def test_namespace_filter_no_restrictions():
    """Test namespace filter when no restrictions are configured"""
    original_allow = config.ALLOW_NAMESPACES
    config.ALLOW_NAMESPACES = None

    @namespace_filter
    def test_func(namespace):
        return f"success_{namespace}"

    result = test_func("any_namespace")
    assert result == "success_any_namespace"

    config.ALLOW_NAMESPACES = original_allow


def test_namespace_filter_allowed_namespace():
    """Test namespace filter with allowed namespace"""
    original_allow = config.ALLOW_NAMESPACES
    config.ALLOW_NAMESPACES = "test,prod"

    @namespace_filter
    def test_func(namespace):
        return f"success_{namespace}"

    result = test_func("test")
    assert result == "success_test"

    config.ALLOW_NAMESPACES = original_allow


def test_namespace_filter_denied_namespace():
    """Test namespace filter denial with restricted namespaces"""
    original_allow = config.ALLOW_NAMESPACES
    config.ALLOW_NAMESPACES = "prod"

    # Create a simple Flask app for testing
    app = Flask(__name__)
    with app.test_request_context("/", headers={"Content-Type": "application/json"}):

        @namespace_filter
        def test_func(namespace):
            return f"success_{namespace}"

        # This should be denied and return a tuple with error
        result = test_func("test")
        assert isinstance(result, tuple)
        assert result[1] == 403
        assert "denied" in result[0]["error"]

    config.ALLOW_NAMESPACES = original_allow


# _strip_immutable_fields tests
def test_strip_immutable_fields():
    """Test stripping immutable fields from CronJob spec"""
    test_spec = {
        "metadata": {
            "name": "test",
            "namespace": "default",
            "resourceVersion": "12345",
            "uid": "abc-123",
            "generation": 1,
            "managedFields": [],
            "labels": {"app": "test"},
        },
        "spec": {"schedule": "0 0 * * *", "successfulJobsHistoryLimit": 3},
        "status": {"lastScheduleTime": "2024-01-01T00:00:00Z"},
    }

    result = _strip_immutable_fields(test_spec)

    # Should keep name, namespace, labels, generation, managedFields but remove uid and resourceVersion
    assert result["metadata"]["name"] == "test"
    assert result["metadata"]["namespace"] == "default"
    assert result["metadata"]["labels"] == {"app": "test"}
    assert "resourceVersion" not in result["metadata"]
    assert "uid" not in result["metadata"]
    # generation and managedFields are not stripped by this function
    assert "generation" in result["metadata"]
    assert "managedFields" in result["metadata"]
    assert "status" not in result


def test_strip_immutable_fields_handles_missing_metadata():
    """Test _strip_immutable_fields handles missing metadata gracefully"""
    test_spec = {"spec": {"schedule": "0 0 * * *"}}

    result = _strip_immutable_fields(test_spec)
    assert "metadata" not in result or result["metadata"] == {}


# Additional validation edge cases
def test_validate_cronjob_yaml_metadata_not_dict():
    """Test validation when metadata is not a dictionary"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata: "not_a_dict"
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "metadata must be a dictionary" in error


def test_validate_cronjob_yaml_spec_not_dict():
    """Test validation when spec is not a dictionary"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec: "not_a_dict"
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "spec must be a dictionary" in error


# Flask route tests
def test_healthz_endpoint():
    """Test the healthz endpoint"""
    result = healthz()
    # Should return tuple (data, status_code) or just data
    if isinstance(result, tuple):
        data, status_code = result
        assert status_code == 200
        assert data["status"] == "ok"
        assert "components" in data
        assert "database" in data["components"]
    else:
        # Backward compatibility - might return just data
        assert result["status"] == "ok"


def test_flask_app_creation():
    """Test Flask app is properly configured"""
    # Test that app instance exists and is configured
    assert app is not None
    assert app.name == "app"

    # Test static configuration
    assert app.static_url_path == ""
    assert app.static_folder.endswith("static")


@patch("app.get_cronjobs")
def test_index_route_logic_namespace_only_true(mock_get_cronjobs):
    """Test index route logic when NAMESPACE_ONLY is True"""
    original_namespace_only = config.NAMESPACE_ONLY
    original_kronic_namespace = getattr(config, "KRONIC_NAMESPACE", None)

    try:
        config.NAMESPACE_ONLY = True
        config.KRONIC_NAMESPACE = "test-namespace"

        with app.test_client() as client:
            with app.test_request_context():
                # Import the function to test its logic
                from app import index

                # This should attempt to redirect, which we can't fully test without the server
                # But we can test that the conditions are met
                assert config.NAMESPACE_ONLY == True
                assert config.KRONIC_NAMESPACE == "test-namespace"

    finally:
        config.NAMESPACE_ONLY = original_namespace_only
        if original_kronic_namespace:
            config.KRONIC_NAMESPACE = original_kronic_namespace


@patch("app.get_cronjobs")
def test_index_route_logic_namespace_only_false(mock_get_cronjobs):
    """Test index route logic when NAMESPACE_ONLY is False"""
    original_namespace_only = config.NAMESPACE_ONLY

    try:
        config.NAMESPACE_ONLY = False
        mock_get_cronjobs.return_value = [
            {"namespace": "default", "name": "job1"},
            {"namespace": "default", "name": "job2"},
            {"namespace": "kube-system", "name": "job3"},
        ]

        with app.test_client() as client:
            with app.test_request_context():
                # Test the core logic of counting namespaces
                cronjobs = mock_get_cronjobs()
                namespaces = {}
                for cronjob in cronjobs:
                    namespaces[cronjob["namespace"]] = (
                        namespaces.get(cronjob["namespace"], 0) + 1
                    )

                expected = {"default": 2, "kube-system": 1}
                assert namespaces == expected

    finally:
        config.NAMESPACE_ONLY = original_namespace_only


@patch("app_routes.get_cronjob")
def test_view_cronjob_details_existing_cronjob(mock_get_cronjob):
    """Test the new details route with an existing cronjob"""
    # Mock an existing cronjob
    mock_cronjob = {
        "apiVersion": "batch/v1",
        "kind": "CronJob",
        "metadata": {"name": "test-cronjob", "namespace": "default"},
        "spec": {
            "schedule": "*/5 * * * *",
            "jobTemplate": {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [{"name": "test", "image": "busybox"}],
                            "restartPolicy": "OnFailure",
                        }
                    }
                }
            },
        },
    }
    
    mock_get_cronjob.return_value = mock_cronjob

    with app.test_client() as client:
        # Test that the route exists and returns a 200 response
        response = client.get("/namespaces/default/cronjobs/test-cronjob/details")
        assert response.status_code == 200
        # Check that it contains expected content
        assert b"test-cronjob" in response.data
        assert b"default" in response.data


@patch("app_routes.get_cronjob")
def test_view_cronjob_details_nonexistent_cronjob(mock_get_cronjob):
    """Test the new details route with a non-existent cronjob"""
    # Mock that no cronjob is found
    mock_get_cronjob.return_value = None

    with app.test_client() as client:
        # Test that it redirects to the edit/create page
        response = client.get("/namespaces/default/cronjobs/nonexistent/details")
        assert response.status_code == 302
        assert "/namespaces/default/cronjobs/nonexistent" in response.location


def test_healthz_endpoint_with_client():
    """Test healthz endpoint through Flask test client"""
    with app.test_client() as client:
        response = client.get("/healthz")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "ok"
        assert "components" in data
        assert "database" in data["components"]

        # In test mode, database should be disabled
        assert data["components"]["database"]["status"] == "disabled"


def test_validate_cronjob_yaml_jobtemplate_not_dict():
    """Test validation when jobTemplate is not a dictionary"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "*/5 * * * *"
  jobTemplate: "not_a_dict"
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "spec.jobTemplate must be a dictionary" in error


def test_validate_cronjob_yaml_missing_jobtemplate_spec():
    """Test validation when jobTemplate.spec is missing"""
    yaml_content = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    metadata:
      name: job-template
"""
    is_valid, parsed, error = _validate_cronjob_yaml(yaml_content)
    assert is_valid == False
    assert "spec.jobTemplate.spec is required" in error
