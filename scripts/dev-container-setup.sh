#!/bin/bash
# Dev Container specific setup for k3d and Kronic development

set -e

CLUSTER_NAME="kronic-localdev"
NETWORK_NAME="k3d-${CLUSTER_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}ℹ${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_docker_in_docker() {
    log_info "Checking Docker-in-Docker environment..."
    
    # Check if we're in a container
    if [ -f /.dockerenv ]; then
        log_info "Running inside Docker container"
    else
        log_warn "Not running in a Docker container"
    fi
    
    # Check Docker socket access
    if docker info >/dev/null 2>&1; then
        log_info "Docker daemon is accessible"
    else
        log_error "Cannot access Docker daemon"
        return 1
    fi
    
    # Check if Docker socket is mounted
    if [ -S /var/run/docker.sock ]; then
        log_info "Docker socket is mounted"
    else
        log_error "Docker socket is not mounted"
        return 1
    fi
}

setup_k3d_cluster() {
    log_info "Setting up k3d cluster in dev container..."
    
    # Create the Docker network first (k3d will use it)
    if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
        log_info "Creating Docker network: $NETWORK_NAME"
        docker network create "$NETWORK_NAME" || {
            log_warn "Network creation failed, it might already exist"
        }
    else
        log_info "Docker network $NETWORK_NAME already exists"
    fi
    
    # Check if cluster exists
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_info "k3d cluster '$CLUSTER_NAME' already exists"
        return 0
    fi
    
    # Create k3d cluster with dev container specific settings
    log_info "Creating k3d cluster: $CLUSTER_NAME"
    k3d cluster create "$CLUSTER_NAME" \
        --servers 1 \
        --agents 0 \
        --wait \
        --timeout 120s \
        --network "$NETWORK_NAME" \
        --kubeconfig-update-default=false \
        --kubeconfig-switch-context=false \
        --port "6443:6443@loadbalancer" \
        --port "80:80@loadbalancer" \
        --port "443:443@loadbalancer" || {
        log_error "Failed to create k3d cluster"
        return 1
    }
    
    # Export kubeconfig to user's .kube directory
    local kubeconfig_path="$HOME/.kube/${CLUSTER_NAME}.yaml"
    k3d kubeconfig write "$CLUSTER_NAME" --output "$kubeconfig_path"
    
    # Also copy kubeconfig to /tmp for docker-compose access
    cp "$kubeconfig_path" /tmp/k3d-kubeconfig.yaml
    chmod 644 /tmp/k3d-kubeconfig.yaml
    
    # Ensure the kubeconfig is available for Docker Compose named volume
    # First, copy to standard kubectl location for container access
    mkdir -p "$HOME/.kube"
    cp "$kubeconfig_path" "$HOME/.kube/config"
    chmod 644 "$HOME/.kube/config"
    
    # Test cluster connectivity
    log_info "Testing cluster connectivity..."
    KUBECONFIG="$kubeconfig_path" kubectl get nodes || {
        log_error "Failed to connect to cluster"
        return 1
    }
    
    log_info "k3d cluster setup complete!"
    log_info "Kubeconfig written to: $kubeconfig_path"
    log_info "Kubeconfig copied to: /tmp/k3d-kubeconfig.yaml"
    log_info "To use this cluster: export KUBECONFIG=$kubeconfig_path"
}

cleanup_k3d_cluster() {
    log_info "Cleaning up k3d cluster..."
    
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        k3d cluster delete "$CLUSTER_NAME"
        log_info "k3d cluster '$CLUSTER_NAME' deleted"
    else
        log_warn "k3d cluster '$CLUSTER_NAME' not found"
    fi
    
    # Clean up kubeconfig
    local kubeconfig_path="$HOME/.kube/${CLUSTER_NAME}.yaml"
    if [ -f "$kubeconfig_path" ]; then
        rm -f "$kubeconfig_path"
        log_info "Kubeconfig file removed"
    fi
}

create_mock_kubeconfig() {
    log_info "Creating mock kubeconfig for testing..."
    
    mkdir -p /tmp/mock-kube
    cat > /tmp/mock-kube/config << 'EOF'
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://mock-k8s-server:6443
    insecure-skip-tls-verify: true
  name: mock-cluster
contexts:
- context:
    cluster: mock-cluster
    user: mock-user
  name: mock-context
current-context: mock-context
users:
- name: mock-user
  user:
    token: mock-token
EOF
    
    log_info "Mock kubeconfig created at /tmp/mock-kube/config"
}

main() {
    case "${1:-setup}" in
        setup)
            check_docker_in_docker
            setup_k3d_cluster
            create_mock_kubeconfig
            ;;
        cleanup)
            cleanup_k3d_cluster
            ;;
        check)
            check_docker_in_docker
            ;;
        mock)
            create_mock_kubeconfig
            ;;
        *)
            echo "Usage: $0 {setup|cleanup|check|mock}"
            echo "  setup   - Set up k3d cluster for dev container"
            echo "  cleanup - Clean up k3d cluster"
            echo "  check   - Check Docker-in-Docker environment"
            echo "  mock    - Create mock kubeconfig for testing"
            exit 1
            ;;
    esac
}

main "$@"
