#!/usr/bin/env python3
"""Seed data script for Kronic database."""

import logging
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import UserManager, RoleManager
from database import init_database, create_tables

log = logging.getLogger("app.seed")


def create_default_roles():
    """Create default roles."""
    log.info("Creating default roles...")

    # Admin role with full permissions
    admin_permissions = {
        "cronjobs": {
            "create": True,
            "read": True,
            "update": True,
            "delete": True,
            "trigger": True,
            "suspend": True,
        },
        "namespaces": {"all": True},
        "users": {"manage": True},
    }

    # User role with limited permissions
    user_permissions = {
        "cronjobs": {
            "create": True,
            "read": True,
            "update": True,
            "delete": False,
            "trigger": True,
            "suspend": True,
        },
        "namespaces": {
            "all": False,
            "allowed": [],  # Will be populated based on user assignment
        },
        "users": {"manage": False},
    }

    # Viewer role with read-only permissions
    viewer_permissions = {
        "cronjobs": {
            "create": False,
            "read": True,
            "update": False,
            "delete": False,
            "trigger": False,
            "suspend": False,
        },
        "namespaces": {"all": False, "allowed": []},
        "users": {"manage": False},
    }

    # Create roles
    admin_role = RoleManager.create_role("admin", admin_permissions)
    user_role = RoleManager.create_role("user", user_permissions)
    viewer_role = RoleManager.create_role("viewer", viewer_permissions)

    if admin_role:
        log.info("Admin role created successfully")
    if user_role:
        log.info("User role created successfully")
    if viewer_role:
        log.info("Viewer role created successfully")

    return admin_role, user_role, viewer_role


def create_admin_user():
    """Create admin user from environment variables."""
    admin_email = os.environ.get("KRONIC_ADMIN_EMAIL", "admin@kronic.local")
    admin_password = os.environ.get("KRONIC_ADMIN_PASSWORD")

    if not admin_password:
        log.warning("KRONIC_ADMIN_PASSWORD not set, skipping admin user creation")
        return None

    log.info(f"Creating admin user: {admin_email}")

    # Create admin user
    admin_user = UserManager.create_user(
        email=admin_email, password=admin_password, is_active=True, is_verified=True
    )

    if admin_user:
        # Assign admin role
        admin_role = RoleManager.get_role_by_name("admin")
        if admin_role:
            success = RoleManager.assign_role_to_user(admin_user.id, admin_role.id)
            if success:
                log.info(f"Admin role assigned to user {admin_email}")
            else:
                log.error(f"Failed to assign admin role to user {admin_email}")
        else:
            log.error("Admin role not found")

    return admin_user


def main():
    """Main seed data function."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    log.info("Starting database seeding...")

    # Initialize database
    if not init_database():
        log.error("Failed to initialize database")
        sys.exit(1)

    # Create tables
    try:
        create_tables()
        log.info("Database tables created successfully")
    except Exception as e:
        log.error(f"Failed to create tables: {e}")
        sys.exit(1)

    # Create default roles
    try:
        create_default_roles()
    except Exception as e:
        log.error(f"Failed to create default roles: {e}")
        sys.exit(1)

    # Create admin user
    try:
        admin_user = create_admin_user()
        if admin_user:
            log.info("Admin user created successfully")
        else:
            log.info("Admin user creation skipped")
    except Exception as e:
        log.error(f"Failed to create admin user: {e}")
        sys.exit(1)

    log.info("Database seeding completed successfully")


if __name__ == "__main__":
    main()
