# Kronic Development Container

This directory contains the development container configuration for the Kronic project. The devcontainer provides a complete, consistent development environment with all necessary tools and dependencies pre-installed.

## What's Included

### Development Tools
- **Python 3.12** with all project dependencies
- **Node.js 20** for frontend development
- **PostgreSQL 15** database
- **Redis 7** for caching
- **Docker** for containerization
- **Kubernetes tools**: kubectl, helm, kind
- **Development utilities**: git, curl, vim, nano

### VS Code Extensions
- Python development (linting, formatting, debugging)
- TypeScript/React development
- Kubernetes and Docker support
- YAML editing
- GitHub integration
- Code formatting and linting

### Pre-configured Services
- PostgreSQL database on port 5432
- Redis cache on port 6379
- Flask app on port 5000
- React dev server on port 3000

## Quick Start

1. **Open in VS Code**: Make sure you have the "Dev Containers" extension installed
2. **Reopen in Container**: Use the command palette (Cmd/Ctrl+Shift+P) and select "Dev Containers: Reopen in Container"
3. **Wait for setup**: The container will build and run the setup script automatically
4. **Start developing**: All tools and dependencies are ready!

## Development Commands

The setup script creates helpful aliases for common development tasks:

### Backend Development
```bash
kronic-run          # Start Flask development server
kronic-test         # Run test suite
kronic-test-cov     # Run tests with coverage report
kronic-lint         # Run code linting
kronic-format       # Format code with Black and isort
kronic-shell        # Open Flask shell
kronic-db-upgrade   # Run database migrations
kronic-reset-db     # Reset database to clean state
```

### Frontend Development
```bash
cd frontend
npm run dev         # Start React development server
npm run build       # Build for production
```

### Kubernetes Development
```bash
kind create cluster --name kronic-dev    # Create local K8s cluster
k get pods                               # kubectl alias
kns default                              # Set namespace
helm install kronic ./chart/kronic       # Install Helm chart
```

## Database Setup

The devcontainer automatically:
- Creates a PostgreSQL database named `kronic`
- Sets up user `kronic` with password `kronicpass`
- Runs database migrations on startup
- Provides connection string: `postgresql://kronic:kronicpass@postgres:5432/kronic`

## Environment Variables

The following environment variables are automatically configured:
- `FLASK_ENV=development`
- `FLASK_DEBUG=1`
- `DATABASE_URL=postgresql://kronic:kronicpass@postgres:5432/kronic`
- `REDIS_URL=redis://redis:6379/0`

## Port Forwarding

These ports are automatically forwarded to your local machine:
- **5000**: Flask application
- **3000**: React development server
- **5432**: PostgreSQL database
- **6379**: Redis cache

## Customization

### Adding VS Code Extensions
Edit `.devcontainer/devcontainer.json` and add extension IDs to the `extensions` array.

### Adding System Packages
Edit `.devcontainer/Dockerfile` and add packages to the `apt-get install` command.

### Adding Python Packages
Add packages to `requirements-dev.txt` and rebuild the container.

### Modifying Services
Edit `.devcontainer/docker-compose.yml` to add or modify services.

## Troubleshooting

### Container Won't Start
- Make sure Docker is running
- Try rebuilding: "Dev Containers: Rebuild Container"
- Check Docker logs for error messages

### Database Connection Issues
- Wait for PostgreSQL to fully start (check with `pg_isready -h postgres`)
- Verify environment variables are set correctly
- Try resetting the database with `kronic-reset-db`

### Permission Issues
- The container runs as user `vscode` (non-root)
- Use `sudo` for system-level operations if needed

### Performance Issues
- Ensure Docker has sufficient resources allocated
- Consider using Docker Desktop's performance optimizations
- Close unused applications to free up system resources

## Development Workflow

1. **Start the environment**: Open in devcontainer
2. **Backend development**: Use `kronic-run` to start the Flask server
3. **Frontend development**: In another terminal, `cd frontend && npm run dev`
4. **Testing**: Run `kronic-test` for backend tests
5. **Linting**: Use `kronic-format` and `kronic-lint` before committing
6. **Database changes**: Use `flask db migrate` and `kronic-db-upgrade`

## CI/CD Integration

The devcontainer environment matches the CI/CD pipeline configuration, ensuring consistency between local development and automated testing.
