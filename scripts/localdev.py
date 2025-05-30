#!/usr/bin/env python3
"""
Local development automation for Kronic using k3d.

This script provides automated k3d cluster provisioning for local development,
similar to the KindClusterManager used in integration tests.
"""

import os
import sys
import subprocess
import tempfile
import time
import argparse
from pathlib import Path


class K3dClusterManager:
    """Manages k3d clusters for local development."""
    
    def __init__(self, cluster_name="kronic-localdev"):
        self.cluster_name = cluster_name
        self.network_name = f"k3d-{cluster_name}"
        self.kubeconfig_path = None
        self.original_kubeconfig = None
        
    def create_cluster(self):
        """Create a k3d cluster and return kubeconfig path."""
        print(f"Creating k3d cluster '{self.cluster_name}'...")
        
        # Store original KUBECONFIG 
        self.original_kubeconfig = os.environ.get("KUBECONFIG")
        
        # Create kubeconfig directory if it doesn't exist
        kube_dir = Path.home() / ".kube"
        kube_dir.mkdir(exist_ok=True)
        
        # Set kubeconfig path
        self.kubeconfig_path = str(kube_dir / f"{self.cluster_name}.yaml")
        
        try:
            # Create k3d cluster with specific network
            cmd = [
                "k3d", "cluster", "create", self.cluster_name,
                "--servers", "1",
                "--agents", "0",
                "--wait",
                "--timeout", "60s",
                "--network", self.network_name,
                "--kubeconfig-update-default=false",
                "--kubeconfig-switch-context=false"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create k3d cluster: {result.stderr}")
            
            # Export kubeconfig to specific file
            cmd = [
                "k3d", "kubeconfig", "write", self.cluster_name,
                "--output", self.kubeconfig_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to export kubeconfig: {result.stderr}")
            
            # Create container-specific kubeconfig with internal server address
            container_kubeconfig_path = self.kubeconfig_path.replace('.yaml', '-container.yaml')
            try:
                with open(self.kubeconfig_path, 'r') as f:
                    kubeconfig_content = f.read()
                
                # Replace server address for container networking
                # k3d creates a load balancer container that containers can reach via its name
                server_name = f"k3d-{self.cluster_name}-serverlb"
                
                # Find the current server line and replace it
                import re
                kubeconfig_content = re.sub(
                    r'server: https://[^:]+:\d+',
                    f'server: https://{server_name}:6443',
                    kubeconfig_content
                )
                
                with open(container_kubeconfig_path, 'w') as f:
                    f.write(kubeconfig_content)
                    
                print(f"✓ Container kubeconfig written to: {container_kubeconfig_path}")
            except Exception as e:
                print(f"Warning: Failed to create container kubeconfig: {e}")
            
            # Wait for cluster to be ready
            self._wait_for_cluster_ready()
            
            print(f"✓ k3d cluster '{self.cluster_name}' created successfully")
            print(f"✓ Kubeconfig written to: {self.kubeconfig_path}")
            print(f"✓ Network '{self.network_name}' created")
            
            return self.kubeconfig_path
            
        except Exception as e:
            self.cleanup()
            raise e
    
    def cleanup(self):
        """Clean up the k3d cluster."""
        print(f"Cleaning up k3d cluster '{self.cluster_name}'...")
        
        try:
            # Delete k3d cluster (this also removes the network if no other clusters use it)
            cmd = ["k3d", "cluster", "delete", self.cluster_name]
            subprocess.run(cmd, capture_output=True, timeout=60)
            print(f"✓ k3d cluster '{self.cluster_name}' deleted")
        except Exception:
            pass  # Best effort cleanup
        
        # Clean up kubeconfig files
        if self.kubeconfig_path and os.path.exists(self.kubeconfig_path):
            try:
                os.unlink(self.kubeconfig_path)
                print(f"✓ Kubeconfig file removed: {self.kubeconfig_path}")
            except Exception:
                pass
        
        # Clean up container kubeconfig file
        if self.kubeconfig_path:
            container_kubeconfig_path = self.kubeconfig_path.replace('.yaml', '-container.yaml')
            if os.path.exists(container_kubeconfig_path):
                try:
                    os.unlink(container_kubeconfig_path)
                    print(f"✓ Container kubeconfig file removed: {container_kubeconfig_path}")
                except Exception:
                    pass
        
        # Restore original KUBECONFIG
        if self.original_kubeconfig:
            os.environ["KUBECONFIG"] = self.original_kubeconfig
        elif "KUBECONFIG" in os.environ:
            del os.environ["KUBECONFIG"]
    
    def _wait_for_cluster_ready(self, timeout=60):
        """Wait for the cluster to be ready."""
        print("Waiting for cluster to be ready...")
        
        # Set KUBECONFIG for kubectl commands
        env = os.environ.copy()
        env["KUBECONFIG"] = self.kubeconfig_path
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if cluster is responsive
                cmd = ["kubectl", "get", "nodes", "--no-headers"]
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      timeout=10, env=env)
                
                if result.returncode == 0 and result.stdout.strip():
                    # Check if node is Ready
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Ready' in line:
                            print("✓ Cluster is ready")
                            return
                
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            
            time.sleep(2)
        
        raise RuntimeError("Timed out waiting for cluster to be ready")
    
    def cluster_exists(self):
        """Check if the cluster already exists."""
        try:
            cmd = ["k3d", "cluster", "list", "--output", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import json
                clusters = json.loads(result.stdout)
                return any(cluster["name"] == self.cluster_name for cluster in clusters)
        except Exception:
            pass
        return False


def check_requirements():
    """Check if required tools are available."""
    required_tools = ["k3d", "docker", "kubectl"]
    missing_tools = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing required tools: {', '.join(missing_tools)}")
        print("\nPlease install the missing tools:")
        for tool in missing_tools:
            if tool == "k3d":
                print("  k3d: curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash")
            elif tool == "docker":
                print("  docker: https://docs.docker.com/get-docker/")
            elif tool == "kubectl":
                print("  kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl/")
        return False
    
    return True


def start_cluster(cluster_name="kronic-localdev"):
    """Start a k3d cluster for local development."""
    if not check_requirements():
        return False
    
    manager = K3dClusterManager(cluster_name)
    
    if manager.cluster_exists():
        print(f"✓ k3d cluster '{cluster_name}' already exists")
        # Still write kubeconfig in case it's missing
        kube_dir = Path.home() / ".kube"
        kubeconfig_path = str(kube_dir / f"{cluster_name}.yaml")
        try:
            cmd = ["k3d", "kubeconfig", "write", cluster_name, "--output", kubeconfig_path]
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print(f"✓ Kubeconfig written to: {kubeconfig_path}")
            
            # Create container-specific kubeconfig
            container_kubeconfig_path = kubeconfig_path.replace('.yaml', '-container.yaml')
            try:
                with open(kubeconfig_path, 'r') as f:
                    kubeconfig_content = f.read()
                
                server_name = f"k3d-{cluster_name}-serverlb"
                import re
                kubeconfig_content = re.sub(
                    r'server: https://[^:]+:\d+',
                    f'server: https://{server_name}:6443',
                    kubeconfig_content
                )
                
                with open(container_kubeconfig_path, 'w') as f:
                    f.write(kubeconfig_content)
                    
                print(f"✓ Container kubeconfig written to: {container_kubeconfig_path}")
            except Exception as e:
                print(f"Warning: Failed to create container kubeconfig: {e}")
                
        except Exception:
            pass
        return True
    
    try:
        manager.create_cluster()
        return True
    except Exception as e:
        print(f"❌ Failed to create cluster: {e}")
        return False


def stop_cluster(cluster_name="kronic-localdev"):
    """Stop and clean up the k3d cluster."""
    manager = K3dClusterManager(cluster_name)
    manager.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Manage k3d clusters for Kronic local development")
    parser.add_argument("action", choices=["start", "stop", "restart"], 
                       help="Action to perform")
    parser.add_argument("--cluster-name", default="kronic-localdev",
                       help="Name of the k3d cluster (default: kronic-localdev)")
    
    args = parser.parse_args()
    
    if args.action == "start":
        success = start_cluster(args.cluster_name)
        sys.exit(0 if success else 1)
    elif args.action == "stop":
        stop_cluster(args.cluster_name)
    elif args.action == "restart":
        stop_cluster(args.cluster_name)
        success = start_cluster(args.cluster_name)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()