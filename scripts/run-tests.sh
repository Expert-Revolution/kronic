#!/bin/bash
set -e

echo "🧪 Running Kronic Unit Tests..."

# Check if docker compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose not found. Please install Docker and Docker Compose."
    exit 1
fi

# Check if containers are running
if ! $DOCKER_COMPOSE ps | grep -q "kronic.*Up"; then
    echo "❌ Kronic container is not running. Please run './scripts/dev-setup.sh' first."
    exit 1
fi

# Run different test categories
echo "📋 Running all tests..."
$DOCKER_COMPOSE exec kronic python -m pytest tests/ -v

echo ""
echo "🔐 Running authentication tests..."
$DOCKER_COMPOSE exec kronic python -m pytest tests/test_jwt_auth.py -v

echo ""
echo "📊 Running database tests..."
$DOCKER_COMPOSE exec kronic python -m pytest tests/test_database.py -v

echo ""
echo "🌐 Running app tests..."
$DOCKER_COMPOSE exec kronic python -m pytest tests/test_app.py -v

echo ""
echo "⚙️ Running configuration tests..."
$DOCKER_COMPOSE exec kronic python -m pytest tests/test_config.py -v

echo "✅ All tests completed!"
