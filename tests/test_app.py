import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

config.TEST = True

from app import _validate_cronjob_yaml


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
