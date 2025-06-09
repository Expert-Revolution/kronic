# Docker Commands and Usage

This document provides comprehensive Docker usage instructions for Kronic.

## Image Building

### Build Production Image
```bash
# Build the production image (final stage)
docker build -t kronic:latest --target final .

# Build development image (dev stage) 
docker build -t kronic:dev --target dev .
```

### Multi-stage Build Targets
- `deps`: Base stage with production dependencies
- `dev`: Development stage with dev dependencies and tools
- `final`: Production stage (default, optimized for size)

### Image Size Optimization
The production image is optimized to be under 200MB:
```bash
# Check image size
docker images kronic:latest

# Expected output: ~172MB
```

## Running Containers

### Quick Start (Production)
```bash
# Run with minimal configuration
docker run -p 8000:8000 kronic:latest

# Run with custom kubeconfig
docker run -p 8000:8000 \
  -v ~/.kube:/home/kronic/.kube:ro \
  kronic:latest

# Run with environment variables
docker run -p 8000:8000 \
  -e KRONIC_ALLOW_NAMESPACES="default,kube-system" \
  -e KRONIC_ADMIN_PASSWORD="secure_password" \
  kronic:latest
```

### Development Mode
```bash
# Run development container with live reload
docker run -p 5000:5000 \
  -v $(pwd):/app \
  -v ~/.kube:/home/kronic/.kube:ro \
  kronic:dev
```

## Docker Compose

### Development Environment
```bash
# Start PostgreSQL database and Kronic
docker compose up -d

# Start with Redis cache (optional)
docker compose --profile full up -d

# View logs
docker compose logs -f kronic

# Stop services
docker compose down
```

### Testing Environment
```bash
# Run tests in isolated environment
docker compose -f docker-compose.test.yml --profile test up --abort-on-container-exit

# Run specific test files
docker compose -f docker-compose.test.yml run --rm kronic-test python -m pytest tests/test_specific.py -v

# Clean up test environment
docker compose -f docker-compose.test.yml down -v
```

## Environment Variables

### Core Configuration
```bash
# Namespace restrictions
KRONIC_ALLOW_NAMESPACES=""                    # Comma-separated list of allowed namespaces
KRONIC_NAMESPACE_ONLY="false"                 # Limit to current namespace only

# Authentication
KRONIC_ADMIN_PASSWORD="changeme"              # Admin password
KRONIC_ADMIN_EMAIL="admin@example.com"        # Admin email

# Kubernetes Configuration
KUBECONFIG="/home/kronic/.kube/config"        # Kubeconfig file path
```

### Database Configuration (Optional)
```bash
# PostgreSQL connection
KRONIC_DATABASE_HOST="postgres"               # Database hostname
KRONIC_DATABASE_PORT="5432"                   # Database port
KRONIC_DATABASE_NAME="kronic"                 # Database name
KRONIC_DATABASE_USER="kronic"                 # Database username
KRONIC_DATABASE_PASSWORD="kronic123"          # Database password

# Or use connection URL
KRONIC_DATABASE_URL="postgresql://user:pass@host:port/db"
```

### Redis Configuration (Optional)
```bash
# Redis connection for session management and rate limiting
REDIS_URL="redis://redis:6379/0"             # Redis connection URL
RATE_LIMIT_ENABLED="true"                     # Enable rate limiting
```

### Security Configuration
```bash
# JWT Authentication
JWT_SECRET_KEY="your-secret-key"              # JWT signing key (change in production!)
JWT_ACCESS_TOKEN_EXPIRES="3600"               # Access token TTL in seconds
JWT_REFRESH_TOKEN_EXPIRES="2592000"           # Refresh token TTL in seconds
```

## Health Checks

### Application Health Check
```bash
# Check application health
curl http://localhost:8000/api/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "v1",
#   "database": "healthy" | "disabled"
# }
```

### Container Health
```bash
# Check Docker container health
docker ps

# Health status should show as "healthy" after startup
```

## Volume Mounts

### Required Mounts
```bash
# Kubernetes configuration (required)
-v ~/.kube:/home/kronic/.kube:ro
```

### Optional Mounts
```bash
# Development mode (live code reload)
-v $(pwd):/app

# Custom configuration directory
-v /path/to/config:/app/config
```

## Networking

### Port Mapping
- `5000`: Development server (Flask debug mode)
- `8000`: Production server (Gunicorn)

### Internal Service Communication
```bash
# Database connection
postgres:5432

# Redis connection (if enabled)
redis:6379
```

## Security Best Practices

### Production Deployment
1. **Never expose publicly without proper authentication**
2. **Use strong passwords and change defaults**
3. **Mount kubeconfig with read-only permissions**
4. **Use specific image tags, not 'latest'**
5. **Run security scanning (see below)**

### Container Security
```bash
# Run as non-root user (uid 3000)
USER kronic

# Read-only filesystem (recommended)
docker run --read-only --tmpfs /tmp kronic:latest

# Drop capabilities (if needed)
docker run --cap-drop=ALL kronic:latest
```

## Security Scanning

### Vulnerability Scanning
```bash
# Scan image for vulnerabilities using Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image kronic:latest

# Scan for high/critical vulnerabilities only
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH,CRITICAL kronic:latest
```

### Dockerfile Best Practices
- Multi-stage builds for smaller images
- Non-root user execution
- Minimal base image (Alpine Linux)
- Explicit dependency versions
- Health checks included

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Fix kubeconfig permissions
chmod 644 ~/.kube/config

# Or use specific user mapping
docker run --user $(id -u):$(id -g) ...
```

#### Database Connection Issues
```bash
# Check database health
docker compose exec postgres pg_isready -U kronic -d kronic

# View database logs
docker compose logs postgres
```

#### Memory Issues
```bash
# Increase container memory limit
docker run -m 512m kronic:latest

# Monitor container resource usage
docker stats
```

### Debug Mode
```bash
# Run with debug logging
docker run -e FLASK_ENV=development \
  -e FLASK_DEBUG=1 \
  kronic:dev

# Access container shell for debugging
docker compose exec kronic /bin/sh
```

## Advanced Usage

### Custom Configuration
```bash
# Use custom configuration file
docker run -v /path/to/config.py:/app/config.py kronic:latest
```

### Backup and Restore
```bash
# Backup database
docker compose exec postgres pg_dump -U kronic kronic > backup.sql

# Restore database
docker compose exec -T postgres psql -U kronic kronic < backup.sql
```

### Performance Tuning
```bash
# Adjust Gunicorn workers
docker run -e GUNICORN_WORKERS=8 kronic:latest

# Custom Gunicorn configuration
docker run -v /path/to/gunicorn.conf:/app/gunicorn.conf \
  kronic:latest gunicorn --config gunicorn.conf app:app
```