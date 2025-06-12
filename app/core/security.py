"""Security utilities for Kronic application."""

import logging
from functools import wraps
from flask import request, jsonify, redirect, url_for, render_template

from app.core.config import USERS, DATABASE_ENABLED
from werkzeug.security import check_password_hash

log = logging.getLogger("app.core.security")


def auth_required(f):
    """Authentication decorator that supports both JWT and HTTP Basic Auth."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First try JWT authentication
        try:
            from jwt_auth import JWTManager
        except ImportError:
            from ..jwt_auth import JWTManager

        token = None
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                pass

        # Get token from cookies as fallback
        if not token:
            token = request.cookies.get("access_token")

        if token:
            payload = JWTManager.verify_token(token)
            if payload:
                # Add user info to request context for JWT
                request.current_user = {
                    "user_id": payload["user_id"],
                    "email": payload["email"],
                }
                return f(*args, **kwargs)

        # Check if this is an API request
        if (
            request.path.startswith("/api/")
            or request.headers.get("Content-Type") == "application/json"
        ):
            return jsonify({"error": "Authentication required"}), 401

        # Import config for checking authentication settings
        import config

        # For web requests, redirect to login page instead of basic auth
        if not config.USERS and not config.DATABASE_ENABLED:
            # No authentication configured, allow access
            return f(*args, **kwargs)

        # Redirect to login page for web requests
        return redirect(url_for("login_page"))

    return decorated_function


def verify_password(username, password):
    """Verify username and password for HTTP Basic Auth."""
    import config  # Import for dynamic USERS access

    # Try database authentication first if available
    if DATABASE_ENABLED:
        try:
            try:
                from auth import UserManager
            except ImportError:
                from ..auth import UserManager

            user = UserManager.get_user_by_email(username)
            if user:
                try:
                    from jwt_auth import SecurePasswordManager
                except ImportError:
                    from ..jwt_auth import SecurePasswordManager

                if SecurePasswordManager.verify_password(password, user.password_hash):
                    return username
        except Exception as e:
            log.warning(f"Database authentication failed: {e}")

    # Fall back to static user authentication - use config.USERS for dynamic access
    if not config.USERS:
        log.debug("Authentication bypassed - no users configured")
        return True

    if username in config.USERS and check_password_hash(
        config.USERS[username], password
    ):
        return username
    return False


def namespace_filter(f):
    """Decorator to filter namespace access based on configuration."""

    @wraps(f)
    def decorated_function(namespace, *args, **kwargs):
        import config  # Import for dynamic access to config values

        # Check namespace restrictions
        if config.NAMESPACE_ONLY and namespace != config.KRONIC_NAMESPACE:
            log.warning(
                f"Access denied to namespace '{namespace}' due to NAMESPACE_ONLY setting"
            )
            error_data = {
                "error": f"Request to {namespace} denied due to NAMESPACE_ONLY setting",
                "namespace": namespace,
            }
            # Check if this is an API request
            try:
                if request.headers.get(
                    "content-type", None
                ) == "application/json" or request.base_url.startswith("/api/"):
                    return error_data, 403
                else:
                    return render_template("denied.html", data=error_data)
            except:
                # If no request context, return tuple for tests
                return error_data, 403

        if config.ALLOW_NAMESPACES:
            allowed_namespaces = [
                ns.strip() for ns in config.ALLOW_NAMESPACES.split(",")
            ]
            if namespace not in allowed_namespaces:
                log.warning(
                    f"Access denied to namespace '{namespace}' due to ALLOW_NAMESPACES setting"
                )
                error_data = {
                    "error": f"Request to {namespace} denied due to ALLOW_NAMESPACES setting",
                    "namespace": namespace,
                }
                # Check if this is an API request
                try:
                    if request.headers.get(
                        "content-type", None
                    ) == "application/json" or request.base_url.startswith("/api/"):
                        return error_data, 403
                    else:
                        return render_template("denied.html", data=error_data)
                except:
                    # If no request context, return tuple for tests
                    return error_data, 403

        log.debug(f"Access granted to namespace '{namespace}'")
        return f(namespace, *args, **kwargs)

    return decorated_function


def apply_security_headers(response):
    """Apply security headers to Flask response."""
    from app.core.config import SECURITY_HEADERS_ENABLED, SECURITY_HEADERS

    if not SECURITY_HEADERS_ENABLED:
        return response

    for header, value in SECURITY_HEADERS.items():
        if value:  # Only set header if value is not empty
            response.headers[header] = value

    return response


def validate_content_length():
    """Validate request content length against configured limits."""
    from flask import request, abort
    from app.core.config import MAX_CONTENT_LENGTH

    if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
        log.warning(
            f"Request content length {request.content_length} exceeds limit {MAX_CONTENT_LENGTH}"
        )
        abort(413)  # Request Entity Too Large


def generate_csrf_token():
    """Generate a CSRF token for the current session."""
    import secrets
    from flask import session
    from app.core.config import CSRF_ENABLED

    if not CSRF_ENABLED:
        return None

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    return session["csrf_token"]


def validate_csrf_token():
    """Validate CSRF token for state-changing requests."""
    from flask import request, session, abort
    from app.core.config import CSRF_ENABLED

    if not CSRF_ENABLED:
        return True

    # Only validate CSRF for state-changing methods
    if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
        return True

    # Skip CSRF validation for API endpoints with Authorization header
    if request.path.startswith("/api/") and request.headers.get("Authorization"):
        return True

    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    session_token = session.get("csrf_token")

    if not token or not session_token or token != session_token:
        log.warning(f"CSRF token validation failed for {request.method} {request.path}")
        abort(403)

    return True
