#!/bin/bash

# Setup script for Kronic development environment
echo "🚀 Setting up Kronic development environment..."

# Install k3d for local Kubernetes development
echo "📦 Installing k3d..."
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Change to workspace directory
cd /workspace

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h postgres -p 5432 -U kronic 2>/dev/null; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    echo "⏳ Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=postgresql://kronic:kronicpass@postgres:5432/kronic
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
EOF
fi

# Install frontend dependencies if package.json exists
if [ -f "frontend/package.json" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Run database migrations if available
echo "🗄️  Setting up database..."
if [ -f "migrations/env.py" ]; then
    export FLASK_APP=app.py
    python -m flask db upgrade 2>/dev/null || echo "⚠️  Database migration skipped"
fi

# Create helpful aliases
echo "⚙️  Setting up development aliases..."
cat >> ~/.bashrc << 'EOF'

# Kronic development aliases
alias kronic-test="python -m pytest tests/ -v"
alias kronic-run="python -m flask run --debug -h 0.0.0.0"
alias kronic-format="python -m black . && python -m isort ."
alias k="kubectl"

# Set dev container environment flag
export DEVCONTAINER=true
EOF

echo "✅ Kronic development environment setup complete!"
echo ""
echo "🎯 Quick start commands:"
echo "  kronic-run          # Start the Flask development server"
echo "  kronic-test         # Run the test suite"
echo "  kronic-format       # Format code with Black and isort"
echo ""
echo "🌐 Frontend development:"
echo "  cd frontend && npm run dev    # Start React development server"
echo ""
