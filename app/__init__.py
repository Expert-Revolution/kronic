"""Kronic application package."""

# Import functions for backward compatibility
from app_routes import _validate_cronjob_yaml, _strip_immutable_fields, healthz, api_get_cronjob_yaml, index, view_cronjob_details
from app.core.security import verify_password, namespace_filter
from app.main import create_app
from werkzeug.security import check_password_hash  # For test compatibility

# Import kron functions for test compatibility
try:
    from kron import get_cronjobs, get_cronjob, get_jobs, get_pods
except ImportError:
    # Create mock functions for tests
    def get_cronjobs(*args, **kwargs):
        return []
    def get_cronjob(*args, **kwargs):
        return None
    def get_jobs(*args, **kwargs):
        return []
    def get_pods(*args, **kwargs):
        return []

# Create app instance
app = create_app()

__all__ = [
    '_validate_cronjob_yaml',
    '_strip_immutable_fields',
    'verify_password',
    'namespace_filter', 
    'healthz',
    'app',
    'get_cronjobs',
    'get_cronjob',
    'get_jobs',
    'get_pods',
    'index',
    'api_get_cronjob_yaml',
    'view_cronjob_details',
    'check_password_hash'
]
