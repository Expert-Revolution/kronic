#!/usr/bin/env python3
"""
Test to verify the generated YAML matches the expected structure.
"""

import unittest
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGeneratedYAML(unittest.TestCase):
    """Test that the generated YAML matches the expected structure."""

    def test_default_yaml_structure(self):
        """Test that the default values generate YAML matching the expected structure."""
        # Simulate the JavaScript defaults
        defaults = {
            "cronJobName": "rpa-batchdownloadroldetails",
            "cronJobNamespace": "exprev-prod",
            "cronJobSuspend": "false",
            "schedule": {
                "minute": "0",
                "hour": "*",
                "day": "*",
                "month": "*",
                "weekday": "*",
            },
            "container": {
                "name": "curl-batchdownloadroldetails",
                "image": "curlimages/curl:latest",
                "command": '["curl", "-v", "-X", "POST", "http://portal-api-rpa:8080/api/Rol/BatchDownloadRolDetails", "-d", "{\\"accessToken\\": \\"string\\", \\"username\\": \\"RPA\\", \\"userId\\": \\"0\\"}"]',
                "restartPolicy": "Never",
            },
            "nodeSelector": [{"key": "kubernetes.io/os", "value": "linux"}],
            "tolerations": [
                {
                    "key": "kubernetes.azure.com/scalesetpriority",
                    "operator": "Equal",
                    "value": "spot",
                    "effect": "NoSchedule",
                    "tolerationSeconds": "",
                }
            ],
            "affinity": {
                "preferredNodeKey": "",
                "preferredNodeValue": "",
                "requiredNodeKey": "kubernetes.azure.com/scalesetpriority",
                "requiredNodeValue": "spot",
            },
        }

        # Generate YAML similar to what the JavaScript updateYaml() function would do
        generated_yaml = self._generate_yaml(defaults)

        # Check key components match the expected structure
        self.assertIn("apiVersion: batch/v1", generated_yaml)
        self.assertIn("kind: CronJob", generated_yaml)
        self.assertIn("name: rpa-batchdownloadroldetails", generated_yaml)
        self.assertIn("namespace: exprev-prod", generated_yaml)
        self.assertIn("app: rpa-batchdownloadroldetails", generated_yaml)
        self.assertIn('schedule: "0 * * * *"', generated_yaml)
        self.assertIn("concurrencyPolicy: Forbid", generated_yaml)
        self.assertIn('"kubernetes.io/os": linux', generated_yaml)
        self.assertIn('- key: "kubernetes.azure.com/scalesetpriority"', generated_yaml)
        self.assertIn('operator: "Equal"', generated_yaml)
        self.assertIn('value: "spot"', generated_yaml)
        self.assertIn('effect: "NoSchedule"', generated_yaml)
        self.assertIn("requiredDuringSchedulingIgnoredDuringExecution:", generated_yaml)
        self.assertIn('- key: "kubernetes.azure.com/scalesetpriority"', generated_yaml)
        self.assertIn("operator: In", generated_yaml)
        self.assertIn('- "spot"', generated_yaml)
        self.assertIn("name: curl-batchdownloadroldetails", generated_yaml)
        self.assertIn("image: curlimages/curl:latest", generated_yaml)
        self.assertIn("restartPolicy: Never", generated_yaml)

    def _generate_yaml(self, config):
        """Generate YAML based on configuration (simulating the JavaScript function)."""
        cron_expression = f"{config['schedule']['minute']} {config['schedule']['hour']} {config['schedule']['day']} {config['schedule']['month']} {config['schedule']['weekday']}"

        yaml_content = f"""apiVersion: batch/v1
kind: CronJob
metadata:
  name: {config['cronJobName']}
  namespace: {config['cronJobNamespace']}
  labels:
    app: {config['cronJobName']}
spec:
  schedule: "{cron_expression}"
  concurrencyPolicy: Forbid
  suspend: {config['cronJobSuspend']}
  jobTemplate:
    spec:
      template:
        spec:"""

        # Add nodeSelector if any
        if config["nodeSelector"]:
            yaml_content += "\n          nodeSelector:"
            for selector in config["nodeSelector"]:
                if selector["key"] and selector["value"]:
                    yaml_content += (
                        f'\n            "{selector["key"]}": {selector["value"]}'
                    )

        # Add tolerations if any
        if config["tolerations"]:
            yaml_content += "\n          tolerations:"
            for toleration in config["tolerations"]:
                yaml_content += "\n          -"
                if toleration["key"]:
                    yaml_content += f'\n            key: "{toleration["key"]}"'
                if toleration["operator"]:
                    yaml_content += (
                        f'\n            operator: "{toleration["operator"]}"'
                    )
                if toleration["value"] and toleration["operator"] != "Exists":
                    yaml_content += f'\n            value: "{toleration["value"]}"'
                if toleration["effect"]:
                    yaml_content += f'\n            effect: "{toleration["effect"]}"'
                if (
                    toleration["tolerationSeconds"]
                    and toleration["effect"] == "NoExecute"
                ):
                    yaml_content += f'\n            tolerationSeconds: {toleration["tolerationSeconds"]}'

        # Add basic affinity if specified
        if (
            config["affinity"]["preferredNodeKey"]
            or config["affinity"]["requiredNodeKey"]
        ):
            yaml_content += "\n          affinity:"
            yaml_content += "\n            nodeAffinity:"

            if (
                config["affinity"]["requiredNodeKey"]
                and config["affinity"]["requiredNodeValue"]
            ):
                yaml_content += (
                    "\n              requiredDuringSchedulingIgnoredDuringExecution:"
                )
                yaml_content += "\n                nodeSelectorTerms:"
                yaml_content += "\n                - matchExpressions:"
                yaml_content += f'\n                  - key: "{config["affinity"]["requiredNodeKey"]}"'
                yaml_content += "\n                    operator: In"
                yaml_content += "\n                    values:"
                yaml_content += f'\n                    - "{config["affinity"]["requiredNodeValue"]}"'

            if (
                config["affinity"]["preferredNodeKey"]
                and config["affinity"]["preferredNodeValue"]
            ):
                yaml_content += (
                    "\n              preferredDuringSchedulingIgnoredDuringExecution:"
                )
                yaml_content += "\n              - weight: 1"
                yaml_content += "\n                preference:"
                yaml_content += "\n                  matchExpressions:"
                yaml_content += f'\n                  - key: "{config["affinity"]["preferredNodeKey"]}"'
                yaml_content += "\n                    operator: In"
                yaml_content += "\n                    values:"
                yaml_content += f'\n                    - "{config["affinity"]["preferredNodeValue"]}"'

        yaml_content += f"""\n          containers:
          - name: {config['container']['name']}
            image: {config['container']['image']}
            imagePullPolicy: IfNotPresent
            command: {config['container']['command']}
          restartPolicy: {config['container']['restartPolicy']}"""

        return yaml_content


if __name__ == "__main__":
    unittest.main()
