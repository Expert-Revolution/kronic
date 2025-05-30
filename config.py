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

log = logging.getLogger("app.config")

## Configuration Setings
# Admin Password. Auth disabled if unset
ADMIN_PASSWORD = os.environ.get("KRONIC_ADMIN_PASSWORD", None)
ADMIN_USERNAME = os.environ.get("KRONIC_ADMIN_USERNAME", "kronic")

# Comma separated list of namespaces to allow access to
ALLOW_NAMESPACES = os.environ.get("KRONIC_ALLOW_NAMESPACES", None)

# Limit to local namespace. Supercedes `ALLOW_NAMESPACES`
NAMESPACE_ONLY = os.environ.get("KRONIC_NAMESPACE_ONLY", False)

# Boolean of whether this is a test environment, disables kubeconfig setup
TEST = os.environ.get("KRONIC_TEST", False)


## Config Logic
USERS = {}
if ADMIN_PASSWORD:
    USERS = {ADMIN_USERNAME: generate_password_hash(ADMIN_PASSWORD)}

# Set allowed namespaces to the installed namespace only
if NAMESPACE_ONLY:
    try:
        KRONIC_NAMESPACE = os.environ["KRONIC_NAMESPACE"]
        ALLOW_NAMESPACES = KRONIC_NAMESPACE
    except KeyError as e:
        log.error(
            "ERROR: KRONIC_NAMESPACE variable not set and a NAMESPACE_ONLY mode was specified."
        )
        sys.exit(1)
