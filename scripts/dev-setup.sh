#!/bin/bash
set -e

echo "🚀 Starting Kronic Development Environment..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if docker compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose not found. Please install Docker and Docker Compose."
    exit 1
fi

echo "📦 Building Docker containers..."
$DOCKER_COMPOSE build

echo "🔄 Starting services..."
$DOCKER_COMPOSE up -d postgres redis

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if postgres is ready
echo "🔍 Checking PostgreSQL connection..."
until $DOCKER_COMPOSE exec postgres pg_isready -U kronic -d kronic; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Check if redis is ready
echo "🔍 Checking Redis connection..."
until $DOCKER_COMPOSE exec redis redis-cli ping; do
    echo "Waiting for Redis..."
    sleep 2
done

echo "📊 Running database migrations..."
$DOCKER_COMPOSE run --rm kronic alembic upgrade head

echo "🌱 Seeding database with initial data..."
$DOCKER_COMPOSE run --rm kronic python scripts/seed_database.py

echo "🚀 Starting Kronic application..."
$DOCKER_COMPOSE up -d kronic

echo "⏳ Waiting for application to start..."
sleep 5

# Wait for the application to be ready
echo "🔍 Checking application health..."
until curl -f http://localhost:5001/health || false; do
    echo "Waiting for application..."
    sleep 2
done

echo "✅ Development environment is ready!"
echo "📱 Application: http://localhost:5001"
echo "🐘 PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
echo "💡 Admin login credentials:"
echo "   Email: admin@kronic.dev"
echo "   Password: admin123!"
echo ""

echo "🧪 Running unit tests..."
$DOCKER_COMPOSE exec kronic python -m pytest tests/ -v

echo "🎉 Setup complete! Your development environment is running."
