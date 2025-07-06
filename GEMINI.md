
# Kronic AI Agent Guide

This guide provides essential information for AI agents to effectively contribute to the Kronic codebase.

## 1. Project Overview

Kronic is a Flask-based web application that provides a user-friendly interface for managing Kubernetes CronJobs. It allows users to view, create, edit, delete, and trigger CronJobs across different namespaces.

- **Backend:** Python/Flask, Gunicorn
- **Frontend:** Primarily server-rendered Jinja2 templates with Alpine.js and PicoCSS. A newer React-based frontend for the login page is in `frontend/`.
- **Data:** Interacts directly with the Kubernetes API. Optionally uses a PostgreSQL database for user authentication and management.
- **Deployment:** Docker and a Helm chart (`chart/kronic`).

## 2. Architecture

The application follows a monolithic structure with clear separation of concerns.

- **`app.py`**: The main Flask application file. It defines all web and API routes, handles request validation, and orchestrates calls to the business logic.
- **`kron.py`**: This module contains all the logic for interacting with the Kubernetes API via the `kubernetes-client`. All functions for getting, creating, updating, and deleting Kubernetes resources (CronJobs, Jobs, Pods) are here.
- **Authentication**: Kronic supports multiple authentication layers, checked in order:
    1.  **JWT (`jwt_auth.py`)**: For API and UI sessions, using tokens stored in cookies.
    2.  **Database (`auth.py`, `models.py`)**: If a database is configured, it manages users and hashed passwords.
    3.  **Basic Auth (`app.py`)**: As a fallback, uses environment variables (`KRONIC_ADMIN_PASSWORD`).
- **Configuration (`config.py`)**: All configuration is managed via environment variables, loaded into this module.
- **Database (`database.py`, `models.py`, `migrations/`)**: When enabled, uses SQLAlchemy for the PostgreSQL connection and Alembic for database schema migrations.

## 3. Development Workflow

### Recommended Setup

The fastest way to get a complete local development environment is to use the provided script. This will spin up a `k3d` Kubernetes cluster and all necessary services.

```bash
# Start the entire local development stack
./scripts/dev.sh up

# Stop and clean up the environment
./scripts/dev.sh down
```

### Testing

The project has both unit and integration tests.

- **Code Quality**: Before committing, ensure your code passes linting and formatting checks.
  ```bash
  black --check --diff .
  flake8 . --statistics
  ```
- **Unit Tests**: These are fast and have no external dependencies.
  ```bash
  pytest -m "not integration"
  ```
- **Integration Tests**: These tests require Docker and `kind` to spin up an ephemeral Kubernetes cluster.
  ```bash
  pytest -m "integration"
  ```
- **All Tests**:
  ```bash
  pytest
  ```
The CI pipeline in `.github/workflows/build.yaml` runs all these checks.

## 4. Coding Conventions

- **Kubernetes Logic**: All code that interacts with the Kubernetes API should be in `kron.py`. Functions should be clearly named and handle API exceptions gracefully.
- **Routes**: All Flask routes are defined in `app.py`. API routes are prefixed with `/api/`.
- **YAML Validation**: When handling raw CronJob YAML from a user, use the `_validate_cronjob_yaml` function in `app.py` as a template for validation. It ensures the YAML is syntactically correct and has the required CronJob structure.
- **Frontend**: For changes to the main UI, modify the Jinja2 templates in the `templates/` directory and use Alpine.js for interactivity. For the login UI, work within the `frontend/` directory, which uses React and Vite.
- **Database**: If adding or modifying database tables, create a new model in `models.py` and generate a migration file using `alembic`.
- **Dependencies**: Add new Python dependencies to `requirements.txt` and `requirements-dev.txt`. Add frontend dependencies to `frontend/package.json`.

## 5. Key Files

- `app.py`: Main application entrypoint, routes, and high-level logic.
- `kron.py`: Core Kubernetes interaction logic.
- `config.py`: Environment variable-based configuration.
- `auth.py` / `jwt_auth.py`: Authentication logic.
- `templates/`: Server-side rendered HTML templates.
- `static/`: CSS, JS, and image assets.
- `frontend/`: React-based frontend source code.
- `tests/`: Unit and integration tests.
- `chart/kronic/`: Helm chart for deployment.
- `scripts/dev.sh`: Local development environment setup script.
- `.github/workflows/build.yaml`: CI/CD pipeline definition.

## 6. Committing & Versioning

The Helm chart version is automatically managed based on commit messages (Conventional Commits). Use prefixes like `feat:`, `fix:`, `chore:`, etc., in your commit messages to trigger the correct version bump. The versioning logic is handled by the `bump-chart-version.sh` script and the GitHub Actions workflows.
