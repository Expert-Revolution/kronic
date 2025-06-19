#!/bin/bash

# Setup script for Kronic development environment
echo "🚀 Setting up Kronic development environment..."

# Change to workspace directory
cd /workspace

# Make sure we have the latest pip
pip install --upgrade pip

# Install Python dependencies if requirements have changed
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install additional development tools
pip install \
    black \
    flake8 \
    isort \
    pylint \
    pytest-cov \
    pytest-xdist \
    pre-commit

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install || echo "⚠️  Pre-commit setup skipped (no .pre-commit-config.yaml found)"

# Install frontend dependencies if package.json exists
if [ -f "frontend/package.json" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

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

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h postgres -p 5432 -U kronic; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    echo "⏳ Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Run database migrations
echo "🗄️  Setting up database..."
if command -v flask &> /dev/null && [ -f "migrations/env.py" ]; then
    export FLASK_APP=app.py
    flask db upgrade || echo "⚠️  Database migration failed or not needed"
fi

# Create helpful aliases and functions
echo "⚙️  Setting up development aliases..."
cat >> ~/.bashrc << 'EOF'

# Kronic development aliases
alias kronic-test="python -m pytest tests/ -v"
alias kronic-test-cov="python -m pytest tests/ --cov=. --cov-report=html"
alias kronic-run="flask run --debug -h 0.0.0.0"
alias kronic-shell="flask shell"
alias kronic-db-upgrade="flask db upgrade"
alias kronic-db-migrate="flask db migrate"
alias kronic-lint="flake8 . && pylint *.py"
alias kronic-format="black . && isort ."

# Kubernetes development
alias k="kubectl"
alias kns="kubectl config set-context --current --namespace"
alias kgp="kubectl get pods"
alias kgs="kubectl get services"
alias kgd="kubectl get deployments"

# Helper functions
kronic-reset-db() {
    echo "🗄️  Resetting database..."
    flask db downgrade base
    flask db upgrade
    echo "✅ Database reset complete!"
}

kronic-dev-setup() {
    echo "🛠️  Running full development setup..."
    pip install -r requirements.txt -r requirements-dev.txt
    cd frontend && npm install && cd ..
    flask db upgrade
    echo "✅ Development setup complete!"
}
EOF

echo "✅ Kronic development environment setup complete!"
echo ""
echo "🎯 Quick start commands:"
echo "  kronic-run          # Start the Flask development server"
echo "  kronic-test         # Run the test suite"
echo "  kronic-test-cov     # Run tests with coverage"
echo "  kronic-format       # Format code with Black and isort"
echo "  kronic-lint         # Run linting with flake8 and pylint"
echo "  kronic-reset-db     # Reset the database"
echo ""
echo "🌐 Frontend development:"
echo "  cd frontend && npm run dev    # Start React development server"
echo ""
echo "☸️  Kubernetes development:"
echo "  kind create cluster --name kronic-dev    # Create local k8s cluster"
echo "  k get pods                               # List pods (kubectl alias)"
echo ""
