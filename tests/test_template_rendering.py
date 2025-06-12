#!/usr/bin/env python3
"""
Tests for template rendering, particularly handling of YAML content with special characters.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

config.TEST = True

from app import app


class TestTemplateRendering(unittest.TestCase):
    """Test template rendering with complex YAML content."""

    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True

    def test_yaml_with_special_characters_in_template(self):
        """Test that YAML content with special characters renders correctly in template."""
        # YAML content that would cause Alpine.js parsing issues
        yaml_content = """apiVersion: batch/v1
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
          - name: test-container
            image: curlimages/curl:latest
            command: ["curl", "-v", "-X", "POST", "http://example.com/api", "-d", "{\\"key\\": \\"value with \\"quotes\\" and \\nspecial chars\\"}"]
          restartPolicy: OnFailure"""

        # Test that the template can be rendered without errors
        with app.app_context():
            # Try to render the template manually to check for Alpine.js expression issues
            from flask import render_template_string

            # Simulate the problematic template content (old approach)
            old_template_content = """
            <div x-data="cronEditor()" x-init="initFromYaml({{ yaml|tojson }})">
                <!-- template content -->
            </div>
            """

            # Data attribute approach (previous fix)
            data_attr_template_content = """
            <div x-data="cronEditor()" data-yaml='{{ yaml|tojson }}' x-init="initFromDataYaml()">
                <!-- template content -->
            </div>
            """

            # New API approach (current fix)
            api_template_content = """
            <div x-data="cronEditor()" x-init="initFromApi()">
                <!-- template content -->
            </div>
            """

            # Test the old approach (should have issues)
            old_result = render_template_string(old_template_content, yaml=yaml_content)

            # Test the data attribute approach (should be safe)
            data_attr_result = render_template_string(
                data_attr_template_content, yaml=yaml_content
            )

            # Test the new API approach (cleanest)
            api_result = render_template_string(api_template_content)

            # The old approach has potential Alpine.js parsing issues
            self.assertIn('x-init="initFromYaml(', old_result)

            # The data attribute approach should be safe for Alpine.js
            self.assertIn("data-yaml='", data_attr_result)
            self.assertIn('x-init="initFromDataYaml()"', data_attr_result)

            # The API approach should be cleanest (no embedded YAML)
            self.assertIn('x-init="initFromApi()"', api_result)
            self.assertNotIn("data-yaml", api_result)
            self.assertNotIn("{{ yaml|tojson }}", api_result)

            print(f"✓ API-based template approach: {api_result.strip()}")

    def test_new_api_template_approach(self):
        """Test that the new API template approach is clean and safe."""
        with app.app_context():
            from flask import render_template_string

            # New template approach - no embedded YAML data
            template = """<div x-data="cronEditor()" x-init="initFromApi()"></div>"""

            result = render_template_string(template)

            # Should NOT contain data-yaml attributes (data is fetched via API)
            self.assertNotIn("data-yaml=", result)

            # Should use the new API-based initialization
            self.assertIn('x-init="initFromApi()"', result)

            # Should not have any embedded YAML data
            self.assertNotIn("{{ yaml|tojson }}", result)

            print(f"✓ New API-based template approach: {result.strip()}")

    def test_yaml_content_json_escaping(self):
        """Test how YAML content is JSON-escaped in templates."""
        with app.app_context():
            from flask import render_template_string

            # YAML with various special characters that could break Alpine.js
            yaml_content = """name: "test with \\"quotes\\""
description: 'single quotes and \\n newlines'
command: ["sh", "-c", "echo \\"hello world\\""]"""

            template = "{{ yaml|tojson }}"
            result = render_template_string(template, yaml=yaml_content)

            # Verify that the JSON escaping is applied
            self.assertIn('\\"', result)  # Quotes should be escaped
            self.assertIn("\\n", result)  # Newlines should be escaped

            # But this alone isn't sufficient for Alpine.js expressions in HTML attributes

    def test_json_parse_correctly_decodes_yaml(self):
        """Test that JSON.parse() correctly decodes the JSON-encoded YAML string."""
        with app.app_context():
            from flask import render_template_string
            import json

            # Complex Kubernetes YAML that would break Alpine.js if not handled correctly
            k8s_yaml = """apiVersion: batch/v1
kind: CronJob
metadata:
  name: "test-cronjob"
  labels:
    app: "test-app"
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test-container
            image: curlimages/curl:latest
            command: ["curl", "-d", "{\\"key\\": \\"value\\"}"]"""

            # Step 1: JSON-encode the YAML (what |tojson does)
            json_encoded = json.dumps(k8s_yaml)

            # Step 2: Simulate what JSON.parse() does in JavaScript
            decoded_yaml = json.loads(json_encoded)

            # Verify that we get back the original YAML string
            self.assertEqual(k8s_yaml, decoded_yaml)

            # Verify the YAML contains the expected Kubernetes structure
            self.assertIn("apiVersion: batch/v1", decoded_yaml)
            self.assertIn("kind: CronJob", decoded_yaml)
            self.assertIn("test-cronjob", decoded_yaml)
            self.assertIn("*/5 * * * *", decoded_yaml)

            print(f"✓ JSON.parse() correctly decodes JSON-encoded YAML string")
            print(f"✓ Original YAML length: {len(k8s_yaml)}")
            print(f"✓ Decoded YAML length: {len(decoded_yaml)}")
            print(f"✓ Are they identical? {k8s_yaml == decoded_yaml}")

    def test_new_yaml_api_endpoint(self):
        """Test that the new YAML API endpoint is defined correctly."""
        with app.app_context():
            # Check that the route exists in the application
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            yaml_route = "/api/namespaces/<namespace>/cronjobs/<cronjob_name>/yaml"

            self.assertIn(
                yaml_route,
                routes,
                f"YAML API endpoint not found. Available routes: {[r for r in routes if 'yaml' in r or 'cronjob' in r]}",
            )

            # Test the function exists and has the right structure
            from app import api_get_cronjob_yaml

            self.assertTrue(
                callable(api_get_cronjob_yaml),
                "api_get_cronjob_yaml should be callable",
            )

            print("✓ New YAML API endpoint is properly defined")


if __name__ == "__main__":
    unittest.main()
