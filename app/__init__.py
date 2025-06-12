"""Kronic application package."""

# Import functions for backward compatibility
from app_routes import _validate_cronjob_yaml, _strip_immutable_fields, healthz, api_get_cronjob_yaml
from app.core.security import verify_password, namespace_filter
from app.main import create_app
from werkzeug.security import check_password_hash  # For test compatibility

# Create app instance
app = create_app()

# Import missing legacy functions for test compatibility
# Now that the app is created and routes registered, we can access the route functions
with app.app_context():
    # Get the function from the app's view functions
    api_get_cronjob_yaml = app.view_functions.get('api_get_cronjob_yaml')
    view_cronjob_details = app.view_functions.get('view_cronjob_details')

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
