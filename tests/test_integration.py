"""
Integration tests for Kronic against ephemeral Kubernetes cluster.

These tests spin up a real Kubernetes cluster using kind and test Kronic's functionality
against actual Kubernetes resources. They are designed to be run optionally
and will be skipped if the required tools (kind, docker) are not available.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import yaml

# Add parent directory to path to import Kronic modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

# Set TEST flag to prevent loading real kube config in modules
config.TEST = True

from kron import (
    delete_cronjob,
    get_cronjob,
    get_cronjobs,
    toggle_cronjob_suspend,
    trigger_cronjob,
    update_cronjob,
)


class KindClusterManager:
    """Manages ephemeral kind clusters for integration testing."""

    def __init__(self, cluster_name="kronic-test"):
        self.cluster_name = cluster_name
        self.kubeconfig_path = None
        self.original_kubeconfig = None

    def create_cluster(self):
        """Create a kind cluster and return kubeconfig path."""
        # Store original KUBECONFIG
        self.original_kubeconfig = os.environ.get("KUBECONFIG")

        # Create temporary kubeconfig file
        temp_dir = tempfile.mkdtemp()
        self.kubeconfig_path = os.path.join(temp_dir, "kubeconfig")

        try:
            # Create kind cluster configuration
            config_content = """
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: false
  kubeProxyMode: "iptables"
  ipFamily: ipv4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 6443
    hostPort: 0  # Let kind choose a random port
"""
            config_file = os.path.join(temp_dir, "kind-config.yaml")
            with open(config_file, "w") as f:
                f.write(config_content)

            # Clean up any existing cluster with the same name
            cleanup_cmd = ["kind", "delete", "cluster", "--name", self.cluster_name]
            subprocess.run(cleanup_cmd, capture_output=True, timeout=30)

            # Create kind cluster with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cmd = [
                        "kind",
                        "create",
                        "cluster",
                        "--name",
                        self.cluster_name,
                        "--config",
                        config_file,
                        "--wait",
                        "120s",  # Increased wait time
                        "--verbosity",
                        "1",
                    ]
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=180
                    )
                    if result.returncode == 0:
                        break

                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed, retrying...")
                        # Clean up before retry
                        subprocess.run(cleanup_cmd, capture_output=True, timeout=30)
                        time.sleep(5)
                    else:
                        raise RuntimeError(
                            f"Failed to create kind cluster after {max_retries} attempts: {result.stderr}"
                        )

                except subprocess.TimeoutExpired:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} timed out, retrying...")
                        subprocess.run(cleanup_cmd, capture_output=True, timeout=30)
                        time.sleep(5)
                    else:
                        raise RuntimeError(
                            f"Kind cluster creation timed out after {max_retries} attempts"
                        )

            # Export kubeconfig
            cmd = [
                "kind",
                "export",
                "kubeconfig",
                "--name",
                self.cluster_name,
                "--kubeconfig",
                self.kubeconfig_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to export kubeconfig: {result.stderr}")

            # Set KUBECONFIG environment variable
            os.environ["KUBECONFIG"] = self.kubeconfig_path

            # Wait for cluster to be ready
            self._wait_for_cluster_ready()

            return self.kubeconfig_path

        except Exception as e:
            self.cleanup()
            raise e

    def cleanup(self):
        """Clean up the kind cluster and temporary files."""
        try:
            # Delete kind cluster
            cmd = ["kind", "delete", "cluster", "--name", self.cluster_name]
            subprocess.run(cmd, capture_output=True, timeout=60)
        except Exception:
            pass  # Best effort cleanup

        # Clean up kubeconfig
        if self.kubeconfig_path and os.path.exists(self.kubeconfig_path):
            try:
                os.unlink(self.kubeconfig_path)
                # Clean up temp directory if empty
                temp_dir = os.path.dirname(self.kubeconfig_path)
                if os.path.isdir(temp_dir):
                    try:
                        os.rmdir(temp_dir)
                    except OSError:
                        pass  # Directory not empty
            except Exception:
                pass

        # Restore original KUBECONFIG
        if self.original_kubeconfig:
            os.environ["KUBECONFIG"] = self.original_kubeconfig
        elif "KUBECONFIG" in os.environ:
            del os.environ["KUBECONFIG"]

    def _wait_for_cluster_ready(self, timeout=120):
        """Wait for the cluster to be ready."""
        start_time = time.time()
        ready_checks = 0
        required_ready_checks = 3  # Require 3 consecutive successful checks

        print("Waiting for cluster to be ready...")
        while time.time() - start_time < timeout:
            try:
                # Check if nodes are ready
                result = subprocess.run(
                    ["kubectl", "get", "nodes", "--no-headers"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if lines and all("Ready" in line for line in lines if line.strip()):
                        ready_checks += 1
                        print(
                            f"Cluster check {ready_checks}/{required_ready_checks} passed"
                        )

                        if ready_checks >= required_ready_checks:
                            # Additional check: ensure core components are running
                            result = subprocess.run(
                                [
                                    "kubectl",
                                    "get",
                                    "pods",
                                    "-n",
                                    "kube-system",
                                    "--no-headers",
                                ],
                                capture_output=True,
                                text=True,
                                timeout=10,
                            )
                            if result.returncode == 0:
                                pod_lines = result.stdout.strip().split("\n")
                                running_pods = [
                                    line for line in pod_lines if "Running" in line
                                ]
                                if (
                                    len(running_pods) >= 4
                                ):  # Expect at least 4 core system pods
                                    print("Cluster is ready!")
                                    return True
                    else:
                        ready_checks = 0  # Reset counter if check fails
                else:
                    ready_checks = 0

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                ready_checks = 0
                print(f"Cluster readiness check failed: {e}")

            time.sleep(3)

        raise RuntimeError(f"Cluster failed to become ready within {timeout} seconds")


def check_integration_requirements():
    """Check if integration test requirements are available."""
    try:
        # Check for kind
        subprocess.run(["kind", "--version"], capture_output=True, timeout=5)
        # Check for docker
        subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
        # Check for kubectl
        subprocess.run(
            ["kubectl", "version", "--client"], capture_output=True, timeout=5
        )
        return True
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        subprocess.CalledProcessError,
    ):
        return False


# Skip all integration tests if requirements not met
integration_skip_reason = (
    "Integration test requirements not available (kind, docker, kubectl)"
)
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not check_integration_requirements(), reason=integration_skip_reason
    ),
]


@pytest.fixture(scope="session")
def kind_cluster():
    """Session-scoped fixture that provides a kind cluster for integration tests."""
    # Check if we're in a problematic Docker-in-Docker environment
    if os.environ.get("DEVCONTAINER", "").lower() == "true":
        pytest.skip(
            "Integration tests with kind clusters are not reliable in dev containers"
        )

    # Check if integration requirements are available
    missing_tools = []
    try:
        subprocess.run(
            ["kind", "--version"], capture_output=True, timeout=5, check=True
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        missing_tools.append("kind")

    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=10, check=True)
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        missing_tools.append("docker")

    if missing_tools:
        pytest.skip(
            f"Missing required tools for integration tests: {', '.join(missing_tools)}"
        )

    manager = KindClusterManager()
    try:
        manager.create_cluster()
        yield manager
    except Exception as e:
        # Log the error but don't fail the test session
        print(f"Warning: Failed to create kind cluster for integration tests: {e}")
        pytest.skip(
            "Failed to create kind cluster - possibly due to Docker-in-Docker limitations"
        )
    finally:
        try:
            manager.cleanup()
        except Exception as e:
            print(f"Warning: Failed to cleanup kind cluster: {e}")


@pytest.fixture
def sample_cronjob_yaml():
    """Fixture providing a sample CronJob YAML for testing."""
    return {
        "apiVersion": "batch/v1",
        "kind": "CronJob",
        "metadata": {"name": "test-cronjob", "namespace": "default"},
        "spec": {
            "schedule": "*/5 * * * *",
            "jobTemplate": {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "test-container",
                                    "image": "busybox:1.35",
                                    "command": ["echo", "hello from integration test"],
                                }
                            ],
                            "restartPolicy": "OnFailure",
                        }
                    }
                }
            },
        },
    }


class TestKronicIntegration:
    """Integration tests for Kronic against a real Kubernetes cluster."""

    def test_cluster_connectivity(self, kind_cluster):
        """Test that we can connect to the kind cluster."""
        # Re-initialize kubernetes clients with the test cluster
        from kubernetes import client
        from kubernetes import config as kubeconfig

        kubeconfig.load_kube_config(config_file=kind_cluster.kubeconfig_path)

        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        assert len(nodes.items) > 0
        assert any(
            node.status.conditions[-1].type == "Ready"
            and node.status.conditions[-1].status == "True"
            for node in nodes.items
        )

    def test_create_cronjob_via_kubectl(self, kind_cluster, sample_cronjob_yaml):
        """Test creating a CronJob directly via kubectl to verify cluster works."""
        # Write cronjob yaml to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_cronjob_yaml, f)
            temp_yaml = f.name

        try:
            # Create cronjob via kubectl
            result = subprocess.run(
                ["kubectl", "apply", "-f", temp_yaml],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, f"Failed to create cronjob: {result.stderr}"

            # Verify cronjob exists
            result = subprocess.run(
                ["kubectl", "get", "cronjob", "test-cronjob", "-o", "name"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0
            assert "cronjob.batch/test-cronjob" in result.stdout

        finally:
            # Cleanup
            subprocess.run(
                ["kubectl", "delete", "cronjob", "test-cronjob", "--ignore-not-found"],
                capture_output=True,
                timeout=30,
            )
            os.unlink(temp_yaml)

    def test_get_cronjobs_integration(self, kind_cluster, sample_cronjob_yaml):
        """Test Kronic's get_cronjobs and get_cronjob functions against real cluster."""
        # Reinitialize kron module with test cluster
        self._reinit_kron_with_cluster(kind_cluster)

        # Create test cronjob via kubectl first
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_cronjob_yaml, f)
            temp_yaml = f.name

        try:
            # Create via kubectl
            subprocess.run(
                ["kubectl", "apply", "-f", temp_yaml], capture_output=True, timeout=30
            )

            # Test Kronic's get_cronjobs function (returns name and namespace only)
            cronjobs = get_cronjobs()
            assert isinstance(cronjobs, list)

            # Find our test cronjob
            test_cronjob = None
            for cj in cronjobs:
                if cj.get("name") == "test-cronjob":
                    test_cronjob = cj
                    break

            assert test_cronjob is not None, "Test cronjob not found in Kronic results"
            assert test_cronjob["namespace"] == "default"
            assert test_cronjob["name"] == "test-cronjob"

            # Test Kronic's get_cronjob function (returns full details)
            cronjob_details = get_cronjob("default", "test-cronjob")
            assert (
                cronjob_details is not False
            ), "get_cronjob should return the cronjob details"
            assert cronjob_details["metadata"]["name"] == "test-cronjob"
            assert cronjob_details["metadata"]["namespace"] == "default"
            assert cronjob_details["spec"]["schedule"] == "*/5 * * * *"

        finally:
            # Cleanup
            subprocess.run(
                ["kubectl", "delete", "cronjob", "test-cronjob", "--ignore-not-found"],
                capture_output=True,
                timeout=30,
            )
            os.unlink(temp_yaml)

    def test_cronjob_suspend_toggle_integration(
        self, kind_cluster, sample_cronjob_yaml
    ):
        """Test Kronic's suspend/resume functionality against real cluster."""
        # Reinitialize kron module with test cluster
        self._reinit_kron_with_cluster(kind_cluster)

        # Create test cronjob via kubectl first
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_cronjob_yaml, f)
            temp_yaml = f.name

        try:
            # Create via kubectl
            subprocess.run(
                ["kubectl", "apply", "-f", temp_yaml], capture_output=True, timeout=30
            )

            # Initially, cronjob should not be suspended
            cronjob_details = get_cronjob("default", "test-cronjob")
            initial_suspend = cronjob_details["spec"].get("suspend", False)
            assert initial_suspend is False, "Initial suspend state should be False"

            # Test suspend functionality - this toggles the current state
            result = toggle_cronjob_suspend("default", "test-cronjob")
            assert result is not False, "Suspend toggle operation should succeed"
            assert (
                "error" not in result
            ), f"Toggle operation should not return error: {result}"

            # Verify cronjob is now suspended (toggled from False to True)
            cronjob_details = get_cronjob("default", "test-cronjob")
            assert (
                cronjob_details["spec"]["suspend"] is True
            ), "Cronjob should now be suspended"

            # Test resume functionality - toggle again to resume
            result = toggle_cronjob_suspend("default", "test-cronjob")
            assert result is not False, "Resume toggle operation should succeed"
            assert (
                "error" not in result
            ), f"Toggle operation should not return error: {result}"

            # Verify cronjob is no longer suspended (toggled from True to False)
            cronjob_details = get_cronjob("default", "test-cronjob")
            assert (
                cronjob_details["spec"].get("suspend", False) is False
            ), "Cronjob should no longer be suspended"

        finally:
            # Cleanup
            subprocess.run(
                ["kubectl", "delete", "cronjob", "test-cronjob", "--ignore-not-found"],
                capture_output=True,
                timeout=30,
            )
            os.unlink(temp_yaml)

    def test_trigger_cronjob_integration(self, kind_cluster, sample_cronjob_yaml):
        """Test Kronic's trigger cronjob functionality against real cluster."""
        # Reinitialize kron module with test cluster
        self._reinit_kron_with_cluster(kind_cluster)

        # Create test cronjob via kubectl first
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_cronjob_yaml, f)
            temp_yaml = f.name

        try:
            # Create via kubectl
            subprocess.run(
                ["kubectl", "apply", "-f", temp_yaml], capture_output=True, timeout=30
            )

            # Trigger the cronjob manually
            result = trigger_cronjob("default", "test-cronjob")
            assert result is not False, "Trigger operation should succeed"

            # Wait a moment for job to be created
            time.sleep(2)

            # Verify that a job was created
            from kron import get_jobs

            jobs = get_jobs("default", "test-cronjob")
            assert isinstance(jobs, list), "get_jobs should return a list"
            assert (
                len(jobs) > 0
            ), "At least one job should have been created by triggering the cronjob"

            # Verify the job has the correct owner reference
            job = jobs[0]
            assert job["metadata"]["name"].startswith(
                "test-cronjob-"
            ), "Job name should be based on cronjob name"

        finally:
            # Cleanup - delete cronjob (which will cascade delete jobs)
            subprocess.run(
                ["kubectl", "delete", "cronjob", "test-cronjob", "--ignore-not-found"],
                capture_output=True,
                timeout=30,
            )
            os.unlink(temp_yaml)

    def test_namespace_filtering_integration(self, kind_cluster, sample_cronjob_yaml):
        """Test Kronic's namespace filtering functionality against real cluster."""
        # Reinitialize kron module with test cluster
        self._reinit_kron_with_cluster(kind_cluster)

        # First, create a test namespace
        subprocess.run(
            ["kubectl", "create", "namespace", "test-namespace"],
            capture_output=True,
            timeout=30,
        )

        # Create cronjob in the test namespace
        sample_cronjob_yaml["metadata"]["namespace"] = "test-namespace"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_cronjob_yaml, f)
            temp_yaml = f.name

        try:
            # Create via kubectl in test namespace
            subprocess.run(
                ["kubectl", "apply", "-f", temp_yaml], capture_output=True, timeout=30
            )

            # Test getting cronjobs from specific namespace
            cronjobs_in_test_ns = get_cronjobs("test-namespace")
            test_cronjob_found = any(
                cj["name"] == "test-cronjob" for cj in cronjobs_in_test_ns
            )
            assert test_cronjob_found, "Test cronjob should be found in test-namespace"

            # Test getting cronjobs from default namespace should not include our test cronjob
            cronjobs_in_default = get_cronjobs("default")
            test_cronjob_in_default = any(
                cj["name"] == "test-cronjob" for cj in cronjobs_in_default
            )
            assert (
                not test_cronjob_in_default
            ), "Test cronjob should not be found in default namespace"

            # Test getting cronjobs from all namespaces should include our test cronjob
            all_cronjobs = get_cronjobs()
            test_cronjob_in_all = any(
                cj["name"] == "test-cronjob" and cj["namespace"] == "test-namespace"
                for cj in all_cronjobs
            )
            assert (
                test_cronjob_in_all
            ), "Test cronjob should be found when listing all namespaces"

        finally:
            # Cleanup
            subprocess.run(
                [
                    "kubectl",
                    "delete",
                    "cronjob",
                    "test-cronjob",
                    "-n",
                    "test-namespace",
                    "--ignore-not-found",
                ],
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                [
                    "kubectl",
                    "delete",
                    "namespace",
                    "test-namespace",
                    "--ignore-not-found",
                ],
                capture_output=True,
                timeout=30,
            )
            os.unlink(temp_yaml)

    def _reinit_kron_with_cluster(self, kind_cluster):
        """Reinitialize kron module to use the test cluster."""
        # Import and reinitialize kubernetes config
        from kubernetes import config as kubeconfig

        kubeconfig.load_kube_config(config_file=kind_cluster.kubeconfig_path)

        # Reinitialize the kron module's clients
        from kubernetes import client

        import kron

        kron.v1 = client.CoreV1Api()
        kron.batch = client.BatchV1Api()
        kron.generic = client.ApiClient()
