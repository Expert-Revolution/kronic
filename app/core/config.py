"""Core configuration for Kronic application."""

import logging
import os
import sys

from werkzeug.security import generate_password_hash

# Configure logging
LOG_LEVEL = os.environ.get("KRONIC_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get(
    "KRONIC_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Setup root logger configuration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("app.core.config")

## Configuration Settings
# Admin Password. Auth disabled if unset
ADMIN_PASSWORD = os.environ.get("KRONIC_ADMIN_PASSWORD", None)
ADMIN_USERNAME = os.environ.get("KRONIC_ADMIN_USERNAME", "kronic")

# Comma separated list of namespaces to allow access to
ALLOW_NAMESPACES = os.environ.get("KRONIC_ALLOW_NAMESPACES", None)

# Limit to local namespace. Supercedes `ALLOW_NAMESPACES`
NAMESPACE_ONLY = os.environ.get("KRONIC_NAMESPACE_ONLY", False)

# Boolean of whether this is a test environment, disables kubeconfig setup
TEST = os.environ.get("KRONIC_TEST", False)

# Database configuration
DATABASE_ENABLED = False

# CORS configuration
CORS_ORIGINS = os.environ.get("KRONIC_CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = (
    os.environ.get("KRONIC_CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
)

# API configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Security configuration
SECURITY_HEADERS_ENABLED = (
    os.environ.get("KRONIC_SECURITY_HEADERS_ENABLED", "true").lower() == "true"
)

# Security Headers
SECURITY_HEADERS = {
    "Strict-Transport-Security": os.environ.get(
        "KRONIC_HSTS_HEADER", "max-age=31536000; includeSubDomains"
    ),
    "X-Frame-Options": os.environ.get("KRONIC_X_FRAME_OPTIONS", "DENY"),
    "X-Content-Type-Options": os.environ.get(
        "KRONIC_X_CONTENT_TYPE_OPTIONS", "nosniff"
    ),
    "X-XSS-Protection": os.environ.get("KRONIC_X_XSS_PROTECTION", "1; mode=block"),
    "Referrer-Policy": os.environ.get(
        "KRONIC_REFERRER_POLICY", "strict-origin-when-cross-origin"
    ),
    "Content-Security-Policy": os.environ.get(
        "KRONIC_CSP",
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'",
    ),
    "Permissions-Policy": os.environ.get(
        "KRONIC_PERMISSIONS_POLICY", "geolocation=(), microphone=(), camera=()"
    ),
}

# CSRF Protection
CSRF_ENABLED = os.environ.get("KRONIC_CSRF_ENABLED", "true").lower() == "true"
CSRF_SECRET_KEY = os.environ.get(
    "KRONIC_CSRF_SECRET_KEY", "change-this-csrf-secret-key"
)

# Request size limits
MAX_CONTENT_LENGTH = int(
    os.environ.get("KRONIC_MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
)  # 16MB default

## Config Logic
USERS = {}
if ADMIN_PASSWORD:
    USERS = {ADMIN_USERNAME: generate_password_hash(ADMIN_PASSWORD)}

# Initialize database if not in test mode
if not TEST:
    try:
        from app.core.database import init_database, is_database_available

        DATABASE_ENABLED = init_database()
        if DATABASE_ENABLED:
            log.info("Database initialized successfully")
    except ImportError:
        # Fallback to old import path for compatibility
        try:
            from database import init_database, is_database_available

            DATABASE_ENABLED = init_database()
            if DATABASE_ENABLED:
                log.info("Database initialized successfully")
        except ImportError:
            log.warning("Database module not found, running without database")

# Import namespace for backward compatibility with existing code
if not TEST:
    try:
        # Try to get the current namespace
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace"):
            with open(
                "/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r"
            ) as f:
                KRONIC_NAMESPACE = f.read().strip()
        else:
            KRONIC_NAMESPACE = os.environ.get("KRONIC_NAMESPACE", "default")
    except Exception:
        KRONIC_NAMESPACE = os.environ.get("KRONIC_NAMESPACE", "default")
else:
    KRONIC_NAMESPACE = "default"

log.info(
    f"Configuration loaded - Database: {DATABASE_ENABLED}, Namespace: {KRONIC_NAMESPACE}"
)
