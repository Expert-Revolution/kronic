import unittest


class TestTerminalCurlFix(unittest.TestCase):
    """Test the Terminal CURL functionality fix"""

    def setUp(self):
        """Set up test fixtures"""
        # Simulate the JavaScript behavior with Python equivalent
        self.container = {"command": 'echo "hello world"'}  # Initial command
        self.jsonData = '{"accessToken": "string", "username": "RPA", "userId": "0"}'

    def simulate_format_json_for_curl_old(self):
        """Simulate the old buggy behavior that appends instead of replacing"""
        import json
        import re

        try:
            parsed = json.loads(self.jsonData)
            compact_json = json.dumps(parsed, separators=(",", ":"))
            self.jsonData = compact_json

            # Old behavior: only modifies K8s command array format
            if "-d" in self.container["command"]:
                # Update existing -d parameter (K8s style)
                escaped_json = compact_json.replace('"', '\\"')
                d_param_regex = r'"-d",\s*"[^"]*"'
                replacement = f'"-d", "{escaped_json}"'

                if re.search(d_param_regex, self.container["command"]):
                    self.container["command"] = re.sub(
                        d_param_regex, replacement, self.container["command"]
                    )
            else:
                # Bug: appends to existing command instead of replacing
                self.container["command"] += f" && curl -d '{compact_json}'"
        except Exception:
            pass

    def simulate_format_json_for_curl_new(self):
        """Simulate the new fixed behavior that replaces the command"""
        import json
        import re

        try:
            parsed = json.loads(self.jsonData)
            compact_json = json.dumps(parsed, separators=(",", ":"))
            self.jsonData = compact_json

            # Extract endpoint from existing command if available
            endpoint = "https://example.com/api/endpoint"
            command_str = self.container["command"]

            # Try to extract URL from the existing command
            url_patterns = [
                r'"([^"]*://[^"]*|https?://[^"]*)"',
                r"'([^']*://[^']*|https?://[^']*)'",
                r'([a-zA-Z]+://[^\s"\']+)',
            ]

            for pattern in url_patterns:
                match = re.search(pattern, command_str)
                if match:
                    endpoint = match.group(1)
                    break

            # Generate terminal curl command - REPLACE the entire command field
            terminal_curl_command = (
                f"curl -v -X POST \"{endpoint}\" -d '{compact_json}'"
            )
            self.container["command"] = terminal_curl_command

        except Exception:
            pass

    def test_old_behavior_appends_to_command(self):
        """Test that the old behavior incorrectly appends to the command"""
        original_command = self.container["command"]
        self.simulate_format_json_for_curl_old()

        # Should append to the original command (the bug)
        self.assertIn(original_command, self.container["command"])
        self.assertIn("&&", self.container["command"])
        self.assertIn("curl -d", self.container["command"])

    def test_new_behavior_replaces_command(self):
        """Test that the new behavior correctly replaces the command"""
        original_command = self.container["command"]
        self.simulate_format_json_for_curl_new()

        # Should NOT contain the original command (replaced entirely)
        self.assertNotIn(original_command, self.container["command"])
        self.assertNotIn("echo", self.container["command"])

        # Should be a proper curl command
        self.assertTrue(self.container["command"].startswith("curl -v -X POST"))
        self.assertIn(
            '-d \'{"accessToken":"string","username":"RPA","userId":"0"}\'',
            self.container["command"],
        )

    def test_new_behavior_extracts_endpoint_from_existing_command(self):
        """Test that the new behavior extracts endpoints from existing commands"""
        # Test with K8s command array format
        self.container["command"] = (
            '["curl", "-v", "-X", "POST", "https://api.myservice.com/webhook", "-d", "{\\"key\\": \\"value\\"}"]'
        )
        self.simulate_format_json_for_curl_new()

        # Should extract the endpoint and use it in the new command
        self.assertIn("https://api.myservice.com/webhook", self.container["command"])
        self.assertTrue(self.container["command"].startswith("curl -v -X POST"))

    def test_new_behavior_handles_command_without_endpoint(self):
        """Test that the new behavior uses default endpoint when none found"""
        self.container["command"] = 'echo "no endpoint here"'
        self.simulate_format_json_for_curl_new()

        # Should use default endpoint
        self.assertIn("https://example.com/api/endpoint", self.container["command"])
        self.assertTrue(self.container["command"].startswith("curl -v -X POST"))

    def test_new_behavior_handles_invalid_json(self):
        """Test that the new behavior handles invalid JSON gracefully"""
        self.jsonData = '{"invalid": json}'  # Invalid JSON
        original_command = self.container["command"]

        self.simulate_format_json_for_curl_new()

        # Should not modify the command if JSON is invalid
        self.assertEqual(self.container["command"], original_command)


if __name__ == "__main__":
    unittest.main()
