#!/usr/bin/env python3
"""
Tests for the CronJob template defaults.
"""

import unittest
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCronJobTemplateDefaults(unittest.TestCase):
    """Test that the CronJob template has the correct default values."""

    def setUp(self):
        """Set up test environment."""
        self.template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "templates",
            "cronjob.html",
        )

    def test_template_contains_curl_defaults(self):
        """Test that the template contains the new curl-based defaults."""
        with open(self.template_path, "r") as f:
            template_content = f.read()

        # Check for curl image default
        self.assertIn("image: 'curlimages/curl:latest'", template_content)

        # Check for curl container name pattern
        self.assertIn("name: 'curl-{name-placeholder}'", template_content)

        # Check for curl command structure
        self.assertIn('["curl", "-v", "-X", "POST"', template_content)

        # Check for Never restart policy default
        self.assertIn("restartPolicy: 'Never'", template_content)

        # Check for hourly schedule default (0 * * * *)
        self.assertIn("minute: '0'", template_content)

        # Check for concurrencyPolicy in YAML generation
        self.assertIn("concurrencyPolicy: Forbid", template_content)

    def test_template_contains_json_helper(self):
        """Test that the template contains the JSON helper functionality."""
        with open(self.template_path, "r") as f:
            template_content = f.read()

        # Check for JSON helper UI elements
        self.assertIn("JSON Data Helper", template_content)
        self.assertIn("formatJson()", template_content)
        self.assertIn("updateCommandWithJson()", template_content)
        self.assertIn("x-show=\"container.command.includes('-d')\"", template_content)

    def test_template_contains_scheduling_defaults(self):
        """Test that the template contains the Kubernetes scheduling defaults."""
        with open(self.template_path, "r") as f:
            template_content = f.read()

        # Check for default nodeSelector
        self.assertIn("{ key: 'kubernetes.io/os', value: 'linux' }", template_content)

        # Check for default tolerations
        self.assertIn("key: 'kubernetes.azure.com/scalesetpriority'", template_content)
        self.assertIn("value: 'spot'", template_content)
        self.assertIn("effect: 'NoSchedule'", template_content)

        # Check for default affinity
        self.assertIn(
            "requiredNodeKey: 'kubernetes.azure.com/scalesetpriority'", template_content
        )
        self.assertIn("requiredNodeValue: 'spot'", template_content)

    def test_template_syntax_valid(self):
        """Test that the template syntax is valid Jinja2."""
        from jinja2 import Template, TemplateSyntaxError

        with open(self.template_path, "r") as f:
            template_content = f.read()

        try:
            Template(template_content)
        except TemplateSyntaxError as e:
            self.fail(f"Template syntax error: {e}")


if __name__ == "__main__":
    unittest.main()
