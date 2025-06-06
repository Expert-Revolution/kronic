"""User management and authentication for Kronic application."""

import logging
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_session, is_database_available
from models import User, Role, UserRole

log = logging.getLogger("app.auth")


class UserManager:
    """Manages user operations."""

    @staticmethod
    def create_user(
        email: str, 
        password: str, 
        is_active: bool = True, 
        is_verified: bool = False
    ) -> Optional[User]:
        """Create a new user.
        
        Args:
            email: User email address
            password: Plain text password
            is_active: Whether user is active
            is_verified: Whether user is verified
            
        Returns:
            User object if created successfully, None otherwise
        """
        if not is_database_available():
            log.warning("Database not available, cannot create user")
            return None
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            # Check if user already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                log.warning(f"User with email {email} already exists")
                return None
            
            # Create new user
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=generate_password_hash(password),
                is_active=is_active,
                is_verified=is_verified
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            log.info(f"User created successfully: {email}")
            return user
            
        except Exception as e:
            log.error(f"Failed to create user {email}: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password.
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if not is_database_available():
            return None
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            user = session.query(User).filter(
                User.email == email,
                User.is_active == True
            ).first()
            
            if user and check_password_hash(user.password_hash, password):
                # Update last login
                user.last_login = datetime.utcnow()
                session.commit()
                log.info(f"User authenticated successfully: {email}")
                return user
            else:
                log.warning(f"Authentication failed for user: {email}")
                return None
                
        except Exception as e:
            log.error(f"Authentication error for user {email}: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User object if found, None otherwise
        """
        if not is_database_available():
            return None
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            user = session.query(User).filter(User.email == email).first()
            return user
            
        except Exception as e:
            log.error(f"Error retrieving user {email}: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_user_roles(user_id: uuid.UUID) -> List[Role]:
        """Get all roles for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of Role objects
        """
        if not is_database_available():
            return []
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return user.roles
            return []
            
        except Exception as e:
            log.error(f"Error retrieving roles for user {user_id}: {e}")
            return []
        finally:
            session.close()


class RoleManager:
    """Manages role operations."""

    @staticmethod
    def create_role(name: str, permissions: dict = None) -> Optional[Role]:
        """Create a new role.
        
        Args:
            name: Role name
            permissions: Dictionary of permissions
            
        Returns:
            Role object if created successfully, None otherwise
        """
        if not is_database_available():
            log.warning("Database not available, cannot create role")
            return None
            
        if permissions is None:
            permissions = {}
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            # Check if role already exists
            existing_role = session.query(Role).filter(Role.name == name).first()
            if existing_role:
                log.warning(f"Role with name {name} already exists")
                return None
            
            # Create new role
            role = Role(name=name, permissions=permissions)
            
            session.add(role)
            session.commit()
            session.refresh(role)
            
            log.info(f"Role created successfully: {name}")
            return role
            
        except Exception as e:
            log.error(f"Failed to create role {name}: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    @staticmethod
    def assign_role_to_user(user_id: uuid.UUID, role_id: int) -> bool:
        """Assign a role to a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            True if assignment successful, False otherwise
        """
        if not is_database_available():
            return False
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            # Check if assignment already exists
            existing_assignment = session.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            ).first()
            
            if existing_assignment:
                log.info(f"User {user_id} already has role {role_id}")
                return True
            
            # Create new assignment
            user_role = UserRole(user_id=user_id, role_id=role_id)
            session.add(user_role)
            session.commit()
            
            log.info(f"Role {role_id} assigned to user {user_id}")
            return True
            
        except Exception as e:
            log.error(f"Failed to assign role {role_id} to user {user_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    @staticmethod
    def get_role_by_name(name: str) -> Optional[Role]:
        """Get role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role object if found, None otherwise
        """
        if not is_database_available():
            return None
            
        try:
            session_gen = get_session()
            session = next(session_gen)
            
            role = session.query(Role).filter(Role.name == name).first()
            return role
            
        except Exception as e:
            log.error(f"Error retrieving role {name}: {e}")
            return None
        finally:
            session.close()