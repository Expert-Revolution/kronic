"""Kronic application package."""

# Import functions for backward compatibility
from app_routes import _validate_cronjob_yaml, _strip_immutable_fields, healthz
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

# Import kron functions for test compatibility
try:
    from kron import get_cronjobs, get_cronjob, get_jobs, get_pods
except ImportError:
    # Mock functions for tests that don't have kron available
    def get_cronjobs(*args, **kwargs):
        return []
    def get_cronjob(*args, **kwargs):
        return None
    def get_jobs(*args, **kwargs):
        return []
    def get_pods(*args, **kwargs):
        return []

# Add index function from legacy routes for test compatibility  
def index():
    """Index route function for test compatibility."""
    from app.core.config import NAMESPACE_ONLY, KRONIC_NAMESPACE
    from flask import redirect
    
    if NAMESPACE_ONLY:
        return redirect(f"/namespaces/{KRONIC_NAMESPACE}", code=302)
    
    cronjobs = get_cronjobs()
    namespaces = {}
    # Count cronjobs per namespace
    for cronjob in cronjobs:
        namespaces[cronjob["namespace"]] = namespaces.get(cronjob["namespace"], 0) + 1
    
    from flask import render_template
    return render_template("index.html", namespaces=namespaces)

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