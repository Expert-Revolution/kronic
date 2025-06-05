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
        yaml_content = '''apiVersion: batch/v1
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
          restartPolicy: OnFailure'''

        # Test that the template can be rendered without errors
        with app.app_context():
            # Try to render the template manually to check for Alpine.js expression issues
            from flask import render_template_string
            
            # Simulate the problematic template content (old approach)
            old_template_content = '''
            <div x-data="cronEditor()" x-init="initFromYaml({{ yaml|tojson }})">
                <!-- template content -->
            </div>
            '''
            
            # Simulate the fixed template content (new approach)
            new_template_content = '''
            <div x-data="cronEditor()" data-yaml='{{ yaml|tojson }}' x-init="initFromDataYaml()">
                <!-- template content -->
            </div>
            '''
            
            # Test the old approach (should have issues)
            old_result = render_template_string(old_template_content, yaml=yaml_content)
            
            # Test the new approach (should be safe)
            new_result = render_template_string(new_template_content, yaml=yaml_content)
            
            # The old approach has potential Alpine.js parsing issues
            self.assertIn('x-init="initFromYaml(', old_result)
            
            # The new approach should be safe for Alpine.js
            self.assertIn("data-yaml='", new_result)
            self.assertIn('x-init="initFromDataYaml()"', new_result)
            
            # Verify that the data attribute contains properly JSON content
            import re
            match = re.search(r"data-yaml='([^']*)'", new_result)
            if match:
                json_content = match.group(1)
                # Should be valid JSON
                import json
                try:
                    parsed = json.loads(json_content)
                    self.assertIn("test-cronjob", parsed)
                except json.JSONDecodeError:
                    self.fail("data-yaml content is not valid JSON")
            else:
                self.fail("Could not find data-yaml attribute with single quotes")
            
            print(f"Fixed template approach: {new_result.strip()}")

    def test_fixed_template_yaml_handling(self):
        """Test that the new template approach handles YAML correctly."""
        with app.app_context():
            from flask import render_template_string
            
            # Test with complex YAML that would break the old approach
            complex_yaml = '''apiVersion: batch/v1
kind: CronJob
metadata:
  name: "complex-name-with-quotes"
  annotations:
    description: "This has \\"nested quotes\\" and
multiple lines"
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            command: ["sh", "-c", "echo \\"hello\\"; echo 'world'"]'''

            # New template approach
            template = '''<div x-data="cronEditor()" data-yaml='{{ yaml|tojson }}' x-init="initFromDataYaml()"></div>'''
            
            result = render_template_string(template, yaml=complex_yaml)
            
            # Should contain the data attribute with JSON content in single quotes
            self.assertIn("data-yaml='", result)
            self.assertIn('x-init="initFromDataYaml()"', result)
            
            # Should not have broken Alpine.js expressions
            self.assertNotIn('x-init="initFromYaml(', result)

    def test_yaml_content_json_escaping(self):
        """Test how YAML content is JSON-escaped in templates."""
        with app.app_context():
            from flask import render_template_string
            
            # YAML with various special characters that could break Alpine.js
            yaml_content = '''name: "test with \\"quotes\\""
description: 'single quotes and \\n newlines'
command: ["sh", "-c", "echo \\"hello world\\""]'''

            template = '{{ yaml|tojson }}'
            result = render_template_string(template, yaml=yaml_content)
            
            # Verify that the JSON escaping is applied
            self.assertIn('\\"', result)  # Quotes should be escaped
            self.assertIn('\\n', result)  # Newlines should be escaped
            
            # But this alone isn't sufficient for Alpine.js expressions in HTML attributes


if __name__ == '__main__':
    unittest.main()