#!/bin/bash
# Kronic Local Development Helper Script

set -e

CLUSTER_NAME="kronic-localdev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

usage() {
    cat << EOF
Kronic Local Development Helper

Usage: $0 <command>

Commands:
    up       Start k3d cluster and run Kronic with docker-compose
    down     Stop docker-compose and clean up k3d cluster
    restart  Restart the entire local development environment
    cluster  Manage k3d cluster only (start|stop|restart)
    status   Show status of cluster and services
    logs     Show Kronic container logs

Examples:
    $0 up                    # Start full development environment
    $0 cluster start         # Just start the k3d cluster
    $0 cluster stop          # Just stop the k3d cluster
    $0 status                # Check what's running

EOF
}

check_requirements() {
    local missing_tools=()
    
    for tool in docker python3 k3d kubectl; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    # Check for docker compose (newer) or docker-compose (legacy)
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        echo "Please install the missing tools and try again."
        return 1
    fi
    
    return 0
}

start_cluster() {
    log_info "Starting k3d cluster..."
    cd "$PROJECT_DIR"
    python scripts/localdev.py start --cluster-name "$CLUSTER_NAME"
}

stop_cluster() {
    log_info "Stopping k3d cluster..."
    cd "$PROJECT_DIR"
    python scripts/localdev.py stop --cluster-name "$CLUSTER_NAME"
}

# Helper function to run docker compose
docker_compose() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

start_services() {
    log_info "Starting Kronic with docker compose..."
    cd "$PROJECT_DIR"
    docker_compose up -d
}

stop_services() {
    log_info "Stopping docker compose services..."
    cd "$PROJECT_DIR"
    docker_compose down
}

show_status() {
    echo "=== k3d Cluster Status ==="
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_info "k3d cluster '$CLUSTER_NAME' is running"
        echo "Nodes:"
        KUBECONFIG="$HOME/.kube/$CLUSTER_NAME.yaml" kubectl get nodes
    else
        log_warn "k3d cluster '$CLUSTER_NAME' is not running"
    fi
    
    echo ""
    echo "=== Docker Compose Status ==="
    cd "$PROJECT_DIR"
    if docker_compose ps | grep -q "kronic"; then
        docker_compose ps
    else
        log_warn "No docker compose services are running"
    fi
    
    echo ""
    echo "=== Access Information ==="
    if docker_compose ps | grep -q "kronic.*Up"; then
        log_info "Kronic is available at: http://localhost:5000"
        log_info "Default credentials: kronic / test2"
    fi
}

show_logs() {
    cd "$PROJECT_DIR"
    docker_compose logs -f kronic
}

main() {
    case "${1:-}" in
        up)
            check_requirements
            start_cluster
            start_services
            log_info "Development environment started!"
            log_info "Kronic is available at: http://localhost:5000"
            log_info "Default credentials: kronic / test2"
            ;;
        down)
            stop_services
            stop_cluster
            log_info "Development environment stopped!"
            ;;
        restart)
            log_info "Restarting development environment..."
            stop_services
            stop_cluster
            start_cluster
            start_services
            log_info "Development environment restarted!"
            ;;
        cluster)
            case "${2:-}" in
                start)
                    check_requirements
                    start_cluster
                    ;;
                stop)
                    stop_cluster
                    ;;
                restart)
                    stop_cluster
                    start_cluster
                    ;;
                *)
                    echo "Usage: $0 cluster <start|stop|restart>"
                    exit 1
                    ;;
            esac
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo "Error: Unknown command '${1:-}'"
            echo ""
            usage
            exit 1
            ;;
    esac
}

main "$@"