#!/bin/bash

# Kronic Development Environment Setup Script

set -e

echo "🚀 Setting up Kronic development environment..."

# Create mock kubeconfig if it doesn't exist
if [ ! -f "/tmp/mock-kube/config" ]; then
    echo "📝 Creating mock kubeconfig..."
    mkdir -p /tmp/mock-kube
    cat > /tmp/mock-kube/config << EOF
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
fi

# Stop and remove existing containers
echo "🧹 Cleaning up existing containers..."
docker compose down --volumes --remove-orphans || true

# Build and start services in detached mode
echo "🏗️  Building and starting services..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
docker compose exec -T postgres pg_isready -U kronic -d kronic
docker compose exec -T redis redis-cli ping

# Initialize database and run migrations
echo "📊 Initializing database..."
docker compose exec -T kronic alembic upgrade head

# Seed database with admin user
echo "🌱 Seeding database with admin user..."
docker compose exec -T kronic python scripts/seed_database.py

echo "✅ Development environment is ready!"
echo ""
echo "🌐 Application URL: http://localhost:5001"
echo "📊 PostgreSQL: localhost:5432 (user: kronic, password: kronic123)"
echo "📦 Redis: localhost:6379"
echo ""
echo "👤 Admin Login:"
echo "   Email: admin@kronic.dev"
echo "   Password: admin123!"
echo ""
echo "📋 Available commands:"
echo "   docker compose logs -f kronic    # View application logs"
echo "   docker compose exec kronic bash  # Access application container"
echo "   ./scripts/run-tests.sh           # Run unit tests"
echo "   docker compose down              # Stop all services"
