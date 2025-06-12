"""Tests for database functionality."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set test mode to prevent actual database initialization
os.environ["KRONIC_TEST"] = "True"


class TestDatabaseConfiguration:
    """Test database configuration and initialization."""

    def test_database_url_from_components(self):
        """Test database URL construction from components."""
        # Import here to avoid early module loading
        import importlib

        with patch.dict(
            os.environ,
            {
                "KRONIC_DATABASE_HOST": "testhost",
                "KRONIC_DATABASE_PORT": "5433",
                "KRONIC_DATABASE_NAME": "testdb",
                "KRONIC_DATABASE_USER": "testuser",
                "KRONIC_DATABASE_PASSWORD": "testpass",
            },
        ):
            # Reload module to pick up new environment variables
            if "database" in sys.modules:
                importlib.reload(sys.modules["database"])
            import database

            url = database.get_database_url()
            expected = "postgresql://testuser:testpass@testhost:5433/testdb"
            assert url == expected

    def test_database_url_from_env_var(self):
        """Test database URL from single environment variable."""
        import importlib

        test_url = "postgresql://user:pass@localhost:5432/db"
        with patch.dict(os.environ, {"KRONIC_DATABASE_URL": test_url}):
            # Reload module to pick up new environment variables
            if "database" in sys.modules:
                importlib.reload(sys.modules["database"])
            import database

            url = database.get_database_url()
            assert url == test_url

    def test_no_database_configuration(self):
        """Test when no database configuration is provided."""
        import importlib

        # Clear all database environment variables
        env_vars_to_clear = [
            "KRONIC_DATABASE_URL",
            "KRONIC_DATABASE_HOST",
            "KRONIC_DATABASE_PORT",
            "KRONIC_DATABASE_NAME",
            "KRONIC_DATABASE_USER",
            "KRONIC_DATABASE_PASSWORD",
        ]

        # Create a clean environment without database vars
        clean_env = {k: v for k, v in os.environ.items() if k not in env_vars_to_clear}

        with patch.dict(os.environ, clean_env, clear=True):
            # Reload module to pick up new environment variables
            if "database" in sys.modules:
                importlib.reload(sys.modules["database"])
            import database

            url = database.get_database_url()
            assert url is None

    def test_database_not_available_initially(self):
        """Test that database is not available when not initialized."""
        from database import is_database_available

        # In test mode, database should not be available
        assert not is_database_available()


class TestDatabaseHealthCheck:
    """Test database health check functionality."""

    @patch("database.engine", None)
    def test_health_check_no_engine(self):
        """Test health check when no database engine is available."""
        from database import check_database_health

        result = check_database_health()
        assert result["status"] == "unhealthy"
        assert "not initialized" in result["error"]

    @patch("database.engine")
    def test_health_check_connection_error(self, mock_engine):
        """Test health check when database connection fails."""
        from database import check_database_health

        # Mock engine.connect() to raise an exception
        mock_engine.connect.side_effect = Exception("Connection failed")

        result = check_database_health()
        assert result["status"] == "unhealthy"
        assert "Connection failed" in result["error"]


class TestUserManager:
    """Test user management functionality."""

    def test_create_user_no_database(self):
        """Test user creation when database is not available."""
        from auth import UserManager

        user = UserManager.create_user("test@example.com", "password")
        assert user is None

    def test_authenticate_user_no_database(self):
        """Test user authentication when database is not available."""
        from auth import UserManager

        user = UserManager.authenticate_user("test@example.com", "password")
        assert user is None

    def test_get_user_by_email_no_database(self):
        """Test getting user by email when database is not available."""
        from auth import UserManager

        user = UserManager.get_user_by_email("test@example.com")
        assert user is None

    def test_get_user_roles_no_database(self):
        """Test getting user roles when database is not available."""
        from auth import UserManager

        roles = UserManager.get_user_roles(uuid.uuid4())
        assert roles == []


class TestRoleManager:
    """Test role management functionality."""

    def test_create_role_no_database(self):
        """Test role creation when database is not available."""
        from auth import RoleManager

        role = RoleManager.create_role("admin", {"test": "permission"})
        assert role is None

    def test_assign_role_to_user_no_database(self):
        """Test role assignment when database is not available."""
        from auth import RoleManager

        success = RoleManager.assign_role_to_user(uuid.uuid4(), 1)
        assert not success

    def test_get_role_by_name_no_database(self):
        """Test getting role by name when database is not available."""
        from auth import RoleManager

        role = RoleManager.get_role_by_name("admin")
        assert role is None


class TestDatabaseIntegration:
    """Test database integration with existing authentication."""

    def test_verify_password_falls_back_to_env_vars(self):
        """Test that authentication falls back to environment variables."""
        import config
        from app import verify_password

        # Temporarily set up users for testing
        original_users = config.USERS.copy()
        original_db_enabled = config.DATABASE_ENABLED

        try:
            # Disable database and set up env var users
            config.DATABASE_ENABLED = False
            config.USERS = {"admin": "hashed_password"}

            # Mock check_password_hash to return True
            with patch('app.core.security.check_password_hash', return_value=True):
                result = verify_password('admin', 'password')
                assert result == 'admin'
        finally:
            # Restore original values
            config.USERS = original_users
            config.DATABASE_ENABLED = original_db_enabled

    def test_verify_password_no_auth(self):
        """Test authentication bypass when no users configured."""
        import config
        from app import verify_password

        # Store original values
        original_users = config.USERS.copy()
        original_db_enabled = config.DATABASE_ENABLED

        try:
            # Clear users and disable database to test bypass
            config.USERS = {}
            config.DATABASE_ENABLED = False

            result = verify_password("anyuser", "anypass")
            assert result is True
        finally:
            # Restore original values
            config.USERS = original_users
            config.DATABASE_ENABLED = original_db_enabled

    def test_healthz_endpoint_includes_database_status(self):
        """Test that health endpoint includes database status."""
        from app import app

        with app.test_client() as client:
            response = client.get("/healthz")
            assert response.status_code in [200, 503]  # Either healthy or degraded

            data = response.get_json()
            assert "components" in data
            assert "database" in data["components"]

            # Should show database as disabled in test mode
            db_status = data["components"]["database"]
            assert db_status["status"] == "disabled"


class TestModelDefinitions:
    """Test that model definitions are valid."""

    def test_user_model_attributes(self):
        """Test User model has required attributes."""
        from models import User

        # Check that User class has expected attributes
        assert hasattr(User, "__tablename__")
        assert User.__tablename__ == "users"
        assert hasattr(User, "id")
        assert hasattr(User, "email")
        assert hasattr(User, "password_hash")
        assert hasattr(User, "created_at")
        assert hasattr(User, "updated_at")
        assert hasattr(User, "is_active")
        assert hasattr(User, "is_verified")
        assert hasattr(User, "last_login")

    def test_role_model_attributes(self):
        """Test Role model has required attributes."""
        from models import Role

        assert hasattr(Role, "__tablename__")
        assert Role.__tablename__ == "roles"
        assert hasattr(Role, "id")
        assert hasattr(Role, "name")
        assert hasattr(Role, "permissions")

    def test_user_role_model_attributes(self):
        """Test UserRole model has required attributes."""
        from models import UserRole

        assert hasattr(UserRole, "__tablename__")
        assert UserRole.__tablename__ == "user_roles"
        assert hasattr(UserRole, "user_id")
        assert hasattr(UserRole, "role_id")


class TestMigrations:
    """Test migration files and configuration."""

    def test_migration_file_exists(self):
        """Test that initial migration file exists."""
        migration_dir = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "versions"
        )
        migration_files = [
            f
            for f in os.listdir(migration_dir)
            if f.endswith(".py") and not f.startswith("__")
        ]
        assert len(migration_files) >= 1

        # Check that the migration file contains expected content
        migration_file = migration_files[0]
        migration_path = os.path.join(migration_dir, migration_file)

        with open(migration_path, "r") as f:
            content = f.read()
            assert "create_table" in content
            assert "users" in content
            assert "roles" in content
            assert "user_roles" in content

    def test_alembic_config_exists(self):
        """Test that alembic configuration file exists."""
        alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        assert os.path.exists(alembic_ini)

    def test_alembic_env_file_exists(self):
        """Test that alembic env.py file exists and is configured."""
        env_file = os.path.join(os.path.dirname(__file__), "..", "migrations", "env.py")
        assert os.path.exists(env_file)

        with open(env_file, "r") as f:
            content = f.read()
            assert "from models import Base" in content
            assert "target_metadata = Base.metadata" in content
