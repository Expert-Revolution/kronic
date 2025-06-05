#!/usr/bin/env python3

"""
Tests for cronjob editing functionality to ensure YAML parsing works correctly
"""

import unittest
import yaml
import json
from app import _strip_immutable_fields


class TestCronjobEditing(unittest.TestCase):
    """Test cronjob editing functionality, specifically the YAML parsing issue"""
    
    def test_strip_immutable_fields_preserves_content(self):
        """Test that _strip_immutable_fields preserves necessary content for editing"""
        
        sample_cronjob = {
            "apiVersion": "batch/v1",
            "kind": "CronJob", 
            "metadata": {
                "name": "test-cronjob",
                "namespace": "default",
                "labels": {
                    "app": "test-cronjob"
                },
                # These should be stripped
                "uid": "12345-67890",
                "resourceVersion": "123456"
            },
            "spec": {
                "schedule": "0 2 * * *",
                "suspend": False,
                "concurrencyPolicy": "Forbid",
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "nodeSelector": {
                                    "kubernetes.io/os": "linux",
                                    "node-type": "worker"
                                },
                                "tolerations": [
                                    {
                                        "key": "dedicated",
                                        "operator": "Equal", 
                                        "value": "gpu",
                                        "effect": "NoSchedule"
                                    }
                                ],
                                "containers": [
                                    {
                                        "name": "curl-test",
                                        "image": "curlimages/curl:latest",
                                        "imagePullPolicy": "IfNotPresent",
                                        "command": [
                                            "curl", "-v", "-X", "POST",
                                            "http://example.com/api",
                                            "-d", '{"accessToken": "string", "username": "RPA", "userId": "0"}'
                                        ]
                                    }
                                ],
                                "restartPolicy": "OnFailure"
                            }
                        }
                    }
                }
            },
            "status": {
                "lastScheduleTime": "2023-01-01T02:00:00Z"
            }
        }
        
        # Test stripping immutable fields
        stripped = _strip_immutable_fields(sample_cronjob.copy())
        
        # Check that status is removed
        self.assertNotIn('status', stripped)
        
        # Check that uid and resourceVersion are removed from metadata
        self.assertNotIn('uid', stripped['metadata'])
        self.assertNotIn('resourceVersion', stripped['metadata'])
        
        # Check that other fields remain intact for editing
        self.assertEqual(stripped['metadata']['name'], 'test-cronjob')
        self.assertEqual(stripped['metadata']['namespace'], 'default')
        self.assertEqual(stripped['spec']['schedule'], '0 2 * * *')
        self.assertEqual(stripped['spec']['suspend'], False)
        
        # Check nested structure is preserved
        containers = stripped['spec']['jobTemplate']['spec']['template']['spec']['containers']
        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0]['name'], 'curl-test')
        self.assertEqual(containers[0]['image'], 'curlimages/curl:latest')
        
        # Check nodeSelector is preserved
        node_selector = stripped['spec']['jobTemplate']['spec']['template']['spec']['nodeSelector']
        self.assertEqual(node_selector['kubernetes.io/os'], 'linux')
        self.assertEqual(node_selector['node-type'], 'worker')
        
        # Check tolerations are preserved
        tolerations = stripped['spec']['jobTemplate']['spec']['template']['spec']['tolerations']
        self.assertEqual(len(tolerations), 1)
        self.assertEqual(tolerations[0]['key'], 'dedicated')
        self.assertEqual(tolerations[0]['operator'], 'Equal')
        self.assertEqual(tolerations[0]['value'], 'gpu')
        self.assertEqual(tolerations[0]['effect'], 'NoSchedule')
        
    def test_yaml_generation_for_template(self):
        """Test that YAML generation produces parseable content for the template"""
        
        sample_cronjob = {
            "apiVersion": "batch/v1",
            "kind": "CronJob",
            "metadata": {
                "name": "test-cronjob",
                "namespace": "default",
                "labels": {
                    "app": "test-cronjob"
                }
            },
            "spec": {
                "schedule": "0 2 * * *",
                "suspend": False,
                "concurrencyPolicy": "Forbid",
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "nodeSelector": {
                                    "kubernetes.io/os": "linux",
                                    "node-type": "worker"
                                },
                                "containers": [
                                    {
                                        "name": "curl-test",
                                        "image": "curlimages/curl:latest",
                                        "imagePullPolicy": "IfNotPresent",
                                        "command": ["curl", "-v", "http://example.com"]
                                    }
                                ],
                                "restartPolicy": "OnFailure"
                            }
                        }
                    }
                }
            }
        }
        
        # Generate YAML for the template
        cronjob_yaml = yaml.dump(sample_cronjob)
        
        # Test that the YAML contains expected structure that can be parsed
        self.assertIn('name: test-cronjob', cronjob_yaml)
        self.assertIn('namespace: default', cronjob_yaml)
        self.assertIn('schedule: 0 2 * * *', cronjob_yaml)
        self.assertIn('suspend: false', cronjob_yaml)
        self.assertIn('containers:', cronjob_yaml)
        self.assertIn('name: curl-test', cronjob_yaml)
        self.assertIn('image: curlimages/curl:latest', cronjob_yaml)
        self.assertIn('nodeSelector:', cronjob_yaml)
        self.assertIn('kubernetes.io/os: linux', cronjob_yaml)
        self.assertIn('node-type: worker', cronjob_yaml)
        
        # Test JSON encoding (what the template does with {{ yaml|tojson }})
        yaml_as_json = json.dumps(cronjob_yaml)
        self.assertIsInstance(yaml_as_json, str)
        
        # Decode and verify it's still valid
        decoded_yaml = json.loads(yaml_as_json)
        self.assertEqual(decoded_yaml, cronjob_yaml)
        
    def test_yaml_parsing_basic_fields(self):
        """Test that basic fields can be extracted from YAML (simulates template parsing)"""
        
        sample_yaml = """apiVersion: batch/v1
kind: CronJob
metadata:
  labels:
    app: test-cronjob
  name: test-cronjob
  namespace: default
spec:
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - command:
            - curl
            - -v
            - http://example.com
            image: curlimages/curl:latest
            imagePullPolicy: IfNotPresent
            name: curl-test
          nodeSelector:
            kubernetes.io/os: linux
            node-type: worker
          restartPolicy: OnFailure
  schedule: 0 2 * * *
  suspend: false"""

        lines = sample_yaml.split('\n')
        
        # Test basic field extraction (this should work with the fixed parsing)
        name_line = next((line for line in lines if line.strip().startswith('name:')), None)
        self.assertIsNotNone(name_line)
        name = name_line.split(':')[1].strip().replace("'", "").replace('"', '')
        self.assertEqual(name, 'test-cronjob')
        
        namespace_line = next((line for line in lines if line.strip().startswith('namespace:')), None) 
        self.assertIsNotNone(namespace_line)
        namespace = namespace_line.split(':')[1].strip().replace("'", "").replace('"', '')
        self.assertEqual(namespace, 'default')
        
        schedule_line = next((line for line in lines if line.strip().startswith('schedule:')), None)
        self.assertIsNotNone(schedule_line)
        schedule_str = schedule_line.split(':')[1].strip().replace("'", "").replace('"', '')
        parts = schedule_str.split(' ')
        self.assertEqual(len(parts), 5)
        self.assertEqual(parts, ['0', '2', '*', '*', '*'])
        
        suspend_line = next((line for line in lines if line.strip().startswith('suspend:')), None)
        self.assertIsNotNone(suspend_line) 
        suspend = suspend_line.split(':')[1].strip().replace("'", "").replace('"', '')
        self.assertEqual(suspend, 'false')
        
    def test_container_extraction_simulation(self):
        """Test container info extraction (simulates the fixed template logic)"""
        
        sample_yaml = """apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
  namespace: default
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - command:
            - curl
            - -v
            - http://example.com
            image: curlimages/curl:latest
            imagePullPolicy: IfNotPresent
            name: curl-test
          restartPolicy: OnFailure"""

        lines = sample_yaml.split('\n')
        container_info = self._extract_container_info_simulation(lines)
        
        # The fixed logic should correctly extract container info
        self.assertEqual(container_info.get('name'), 'curl-test')
        self.assertEqual(container_info.get('image'), 'curlimages/curl:latest')
        
    def test_node_selector_extraction_simulation(self):
        """Test nodeSelector extraction (simulates the fixed template logic)"""
        
        sample_yaml = """spec:
  jobTemplate:
    spec:
      template:
        spec:
          nodeSelector:
            kubernetes.io/os: linux
            node-type: worker
          restartPolicy: OnFailure
          tolerations:
          - key: test"""

        lines = sample_yaml.split('\n')
        node_selectors = self._extract_node_selectors_simulation(lines)
        
        # The fixed logic should correctly extract nodeSelector and stop at the right boundary
        self.assertEqual(len(node_selectors), 2)
        self.assertIn({'key': 'kubernetes.io/os', 'value': 'linux'}, node_selectors)
        self.assertIn({'key': 'node-type', 'value': 'worker'}, node_selectors)
        
        # It should NOT include restartPolicy (that was the bug)
        restartPolicy_entries = [ns for ns in node_selectors if ns['key'] == 'restartPolicy']
        self.assertEqual(len(restartPolicy_entries), 0)
        
    def _extract_container_info_simulation(self, lines):
        """Simulate the fixed container extraction logic from the template"""
        container_info = {}
        
        # Find the containers section
        containers_start = next((i for i, line in enumerate(lines) if line.strip() == 'containers:'), None)
        if containers_start is None:
            return container_info
        
        # Look for the first container
        in_first_container = False
        current_indent = None
        
        for i in range(containers_start + 1, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            if stripped == '':
                continue
                
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            
            # Start of first container
            if stripped.startswith('- ') and not in_first_container:
                in_first_container = True
                current_indent = indent
                continue
            
            # If we're in the first container
            if in_first_container:
                # Check if we've moved to a new section (same or lower indent)
                if indent <= current_indent and not stripped.startswith('-'):
                    break
                    
                # Extract container properties
                if ':' in stripped and not stripped.startswith('-'):
                    prop, value = stripped.split(':', 1)
                    prop = prop.strip()
                    value = value.strip().replace("'", "").replace('"', '')
                    if prop in ['name', 'image']:
                        container_info[prop] = value
        
        return container_info
    
    def _extract_node_selectors_simulation(self, lines):
        """Simulate the fixed nodeSelector extraction logic from the template"""
        node_selectors = []
        
        # Find nodeSelector section
        node_selector_start = next((i for i, line in enumerate(lines) if line.strip() == 'nodeSelector:'), None)
        if node_selector_start is None:
            return node_selectors
        
        base_indent = len(lines[node_selector_start]) - len(lines[node_selector_start].lstrip())
        
        for i in range(node_selector_start + 1, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            if stripped == '':
                continue
                
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            
            # If we've moved to a section at the same or lower indent level, stop
            if indent <= base_indent:
                break
                
            # Extract key-value pairs
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip().replace("'", "").replace('"', '')
                if key and value:
                    node_selectors.append({'key': key, 'value': value})
        
        return node_selectors


if __name__ == '__main__':
    unittest.main()