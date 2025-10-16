"""
Authentication service implementation.
Handles user authentication, session management, and authorization.
"""

import hashlib
import secrets
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...database.repositories.base_repository import BaseRepository
from ...database.models.base import User, UserResponse
from ...core.errors.error_handler import handle_errors, handle_errors_async
from ...core.errors.error_types import (
    AuthenticationError,
    InvalidCredentialsError,
    AccountLockedError,
    AuthorizationError,
    InsufficientPermissionsError,
    ValidationError,
    MissingRequiredFieldError
)


@dataclass
class Session:
    """User session information."""
    session_id: str
    user_id: int
    username: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = None

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active,
            'metadata': self.metadata or {}
        }


@dataclass
class AuthResult:
    """Authentication result."""
    success: bool
    user: Optional[User]
    session: Optional[Session]
    message: str
    requires_mfa: bool = False
    mfa_token: Optional[str] = None


class AuthService:
    """Service for user authentication and authorization."""

    def __init__(self, db_path: str, secret_key: str = None):
        """Initialize authentication service.

        Args:
            db_path: Path to database file
            secret_key: Secret key for token generation
        """
        self.db_path = db_path
        self.secret_key = secret_key or "default-secret-key-change-in-production"
        self.logger = logging.getLogger(__name__)

        # In-memory session storage (in production, use Redis or database)
        self._active_sessions: Dict[str, Session] = {}

        # Failed login attempts tracking
        self._failed_attempts: Dict[str, List[datetime]] = {}

        # Account lockout tracking
        self._locked_accounts: Dict[str, datetime] = {}

    @handle_errors(operation="authenticate_user", component="auth_service")
    def authenticate(
        self,
        username: str,
        password: str,
        project_id: str = None,
        ip_address: str = None
    ) -> AuthResult:
        """Authenticate user with username and password.

        Args:
            username: Username to authenticate
            password: Password to verify
            project_id: Project ID for context
            ip_address: Client IP address for tracking

        Returns:
            Authentication result with session if successful
        """
        # Validate input
        if not username or not password:
            raise MissingRequiredFieldError("username or password")

        username = username.strip().lower()

        # Check if account is locked
        if self._is_account_locked(username):
            lockout_until = self._locked_accounts.get(username)
            lockout_minutes = int((lockout_until - datetime.utcnow()).total_seconds() / 60)
            raise AccountLockedError(username, lockout_minutes)

        try:
            # Get user from database (simplified - would use UserRepository)
            user = self._get_user_by_username(username)

            if not user:
                self._record_failed_attempt(username, ip_address)
                raise InvalidCredentialsError(username)

            # Verify password
            if not self._verify_password(password, user.password_hash):
                self._record_failed_attempt(username, ip_address)
                raise InvalidCredentialsError(username)

            # Check if user is active
            if not user.is_active:
                raise AuthenticationError(
                    "Account is disabled",
                    username=username
                )

            # Create session
            session = self._create_session(user, project_id)

            # Clear failed attempts on successful login
            self._clear_failed_attempts(username)

            self.logger.info(f"User {username} authenticated successfully")
            return AuthResult(
                success=True,
                user=user,
                session=session,
                message="Authentication successful"
            )

        except (InvalidCredentialsError, AccountLockedError, AuthenticationError):
            raise
        except Exception as e:
            self.logger.error(f"Authentication error for {username}: {e}")
            raise AuthenticationError(f"Authentication failed: {str(e)}", username=username)

    @handle_errors(operation="create_user", component="auth_service")
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        preferences: Optional[Dict[str, Any]] = None,
        project_id: str = None
    ) -> AuthResult:
        """Create new user account.

        Args:
            username: Desired username
            email: User email address
            password: User password
            preferences: User preferences
            project_id: Project ID for context

        Returns:
            Authentication result with new user
        """
        # Validate input
        if not all([username, email, password]):
            raise MissingRequiredFieldError("username, email, or password")

        username = username.strip().lower()
        email = email.strip().lower()

        # Validate password strength
        password_errors = self._validate_password_strength(password)
        if password_errors:
            raise ValidationError(
                f"Password validation failed: {', '.join(password_errors)}",
                "password",
                password
            )

        try:
            # Check if username already exists
            existing_user = self._get_user_by_username(username)
            if existing_user:
                raise ValidationError(
                    "Username already exists",
                    "username",
                    username
                )

            # Check if email already exists
            existing_email = self._get_user_by_email(email)
            if existing_email:
                raise ValidationError(
                    "Email already exists",
                    "email",
                    email
                )

            # Hash password
            password_hash = self._hash_password(password)

            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                preferences=preferences or {},
                is_active=True,
                is_new_user=True
            )

            # Save to database (simplified)
            saved_user = self._save_user(user)

            # Create welcome session
            session = self._create_session(saved_user, project_id)

            self.logger.info(f"New user created: {username}")
            return AuthResult(
                success=True,
                user=saved_user,
                session=session,
                message="User created successfully"
            )

        except (ValidationError,):
            raise
        except Exception as e:
            self.logger.error(f"User creation error for {username}: {e}")
            raise AuthenticationError(f"User creation failed: {str(e)}", username=username)

    @handle_errors(operation="validate_session", component="auth_service")
    def validate_session(self, session_token: str) -> Optional[Session]:
        """Validate session token.

        Args:
            session_token: Session token to validate

        Returns:
            Session if valid, None otherwise
        """
        try:
            # Get session from memory
            session = self._active_sessions.get(session_token)

            if not session:
                return None

            # Check if session is expired
            if session.is_expired():
                self._destroy_session(session_token)
                return None

            # Check if session is active
            if not session.is_active:
                return None

            # Update last activity
            session.expires_at = datetime.utcnow() + timedelta(hours=24)

            return session

        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return None

    @handle_errors(operation="refresh_session", component="auth_service")
    def refresh_session(self, session_token: str) -> Optional[Session]:
        """Refresh session expiration.

        Args:
            session_token: Session token to refresh

        Returns:
            Refreshed session if valid
        """
        session = self.validate_session(session_token)

        if session:
            # Extend session by 24 hours
            session.expires_at = datetime.utcnow() + timedelta(hours=24)
            self.logger.info(f"Session refreshed for user {session.username}")

        return session

    @handle_errors(operation="logout_user", component="auth_service")
    def logout(self, session_token: str) -> bool:
        """Logout user and destroy session.

        Args:
            session_token: Session token to destroy

        Returns:
            True if logout successful
        """
        try:
            session = self._active_sessions.get(session_token)

            if session:
                self._destroy_session(session_token)
                self.logger.info(f"User {session.username} logged out")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return False

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID to find

        Returns:
            User if found, None otherwise
        """
        try:
            return self._get_user_by_id(user_id)
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {e}")
            return None

    def update_user_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any],
        session_token: str = None
    ) -> bool:
        """Update user preferences.

        Args:
            user_id: User ID
            preferences: New preferences
            session_token: Session token for authorization

        Returns:
            True if update successful
        """
        try:
            # Validate session if provided
            if session_token:
                session = self.validate_session(session_token)
                if not session or session.user_id != user_id:
                    raise InsufficientPermissionsError(
                        "user_preferences",
                        "update",
                        str(user_id)
                    )

            # Get current user
            user = self._get_user_by_id(user_id)
            if not user:
                return False

            # Update preferences
            current_prefs = user.preferences or {}
            current_prefs.update(preferences)
            user.preferences = current_prefs

            # Save to database
            return self._update_user(user)

        except (InsufficientPermissionsError,):
            raise
        except Exception as e:
            self.logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        session_token: str = None
    ) -> bool:
        """Change user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            session_token: Session token for authorization

        Returns:
            True if password changed successfully
        """
        try:
            # Validate session if provided
            if session_token:
                session = self.validate_session(session_token)
                if not session or session.user_id != user_id:
                    raise InsufficientPermissionsError(
                        "password_change",
                        "update",
                        str(user_id)
                    )

            # Get user
            user = self._get_user_by_id(user_id)
            if not user:
                return False

            # Verify current password
            if not self._verify_password(current_password, user.password_hash):
                raise ValidationError(
                    "Current password is incorrect",
                    "current_password",
                    current_password
                )

            # Validate new password
            password_errors = self._validate_password_strength(new_password)
            if password_errors:
                raise ValidationError(
                    f"New password validation failed: {', '.join(password_errors)}",
                    "new_password",
                    new_password
                )

            # Hash new password
            new_hash = self._hash_password(new_password)
            user.password_hash = new_hash

            # Save to database
            success = self._update_user(user)

            if success:
                self.logger.info(f"Password changed for user {user.username}")
                # Invalidate all sessions for security
                self._invalidate_user_sessions(user_id)

            return success

        except (InsufficientPermissionsError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error changing password for user {user_id}: {e}")
            return False

    def get_user_activity_summary(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary.

        Args:
            user_id: User ID
            days: Days to look back

        Returns:
            Activity summary dictionary
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # This would query user_activity table in real implementation
            # For now, return mock data
            return {
                'user_id': user_id,
                'period_days': days,
                'total_sessions': 0,
                'total_documents_uploaded': 0,
                'total_searches': 0,
                'last_activity': None,
                'favorite_features': [],
                'study_streak_days': 0
            }

        except Exception as e:
            self.logger.error(f"Error getting activity summary for user {user_id}: {e}")
            return {}

    def _create_session(self, user: User, project_id: str = None) -> Session:
        """Create new user session."""
        session_id = secrets.token_urlsafe(32)

        session = Session(
            session_id=session_id,
            user_id=user.id,
            username=user.username,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True,
            metadata={
                'project_id': project_id,
                'login_time': datetime.utcnow().isoformat(),
                'user_agent': 'unknown'  # Would be populated from request
            }
        )

        self._active_sessions[session_id] = session
        return session

    def _destroy_session(self, session_token: str) -> None:
        """Destroy user session."""
        if session_token in self._active_sessions:
            session = self._active_sessions[session_token]
            session.is_active = False
            # Remove from active sessions after a delay
            # In production, this would be handled by Redis expiration

    def _record_failed_attempt(self, username: str, ip_address: str = None) -> None:
        """Record failed login attempt."""
        if username not in self._failed_attempts:
            self._failed_attempts[username] = []

        self._failed_attempts[username].append(datetime.utcnow())

        # Keep only last 10 attempts
        self._failed_attempts[username] = self._failed_attempts[username][-10:]

        # Check if account should be locked
        recent_failures = [
            attempt for attempt in self._failed_attempts[username]
            if datetime.utcnow() - attempt < timedelta(minutes=15)
        ]

        if len(recent_failures) >= 5:  # 5 failures in 15 minutes
            self._lock_account(username, 30)  # Lock for 30 minutes

    def _clear_failed_attempts(self, username: str) -> None:
        """Clear failed login attempts for user."""
        self._failed_attempts.pop(username, None)

    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked."""
        if username in self._locked_accounts:
            lockout_until = self._locked_accounts[username]

            if datetime.utcnow() < lockout_until:
                return True
            else:
                # Lockout expired, remove it
                del self._locked_accounts[username]

        return False

    def _lock_account(self, username: str, minutes: int) -> None:
        """Lock user account."""
        self._locked_accounts[username] = datetime.utcnow() + timedelta(minutes=minutes)
        self.logger.warning(f"Account locked for {username} for {minutes} minutes")

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        try:
            import bcrypt

            # Generate salt and hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')

        except ImportError:
            # Fallback to SHA-256 if bcrypt not available
            self.logger.warning("bcrypt not available, using SHA-256 (not recommended for production)")
            return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            import bcrypt

            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

        except ImportError:
            # Fallback to SHA-256 if bcrypt not available
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == password_hash

    def _validate_password_strength(self, password: str) -> List[str]:
        """Validate password strength."""
        errors = []

        if len(password) < 8:
            errors.append("Must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            errors.append("Must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Must contain at least one special character")

        return errors

    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (simplified implementation)."""
        # This would use UserRepository in real implementation
        # For now, return None (no users in database)
        return None

    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (simplified implementation)."""
        # This would use UserRepository in real implementation
        return None

    def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID (simplified implementation)."""
        # This would use UserRepository in real implementation
        return None

    def _save_user(self, user: User) -> User:
        """Save user to database (simplified implementation)."""
        # This would use UserRepository in real implementation
        # For now, just return the user as-is
        return user

    def _update_user(self, user: User) -> bool:
        """Update user in database (simplified implementation)."""
        # This would use UserRepository in real implementation
        return True

    def _invalidate_user_sessions(self, user_id: int) -> None:
        """Invalidate all sessions for user."""
        to_remove = []

        for session_token, session in self._active_sessions.items():
            if session.user_id == user_id:
                session.is_active = False
                to_remove.append(session_token)

        for token in to_remove:
            del self._active_sessions[token]

        self.logger.info(f"Invalidated all sessions for user {user_id}")

    def get_active_sessions(self, user_id: int) -> List[Session]:
        """Get all active sessions for user.

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        sessions = []

        for session in self._active_sessions.values():
            if (session.user_id == user_id and
                session.is_active and
                not session.is_expired()):
                sessions.append(session)

        return sessions

    def revoke_session(self, session_token: str) -> bool:
        """Revoke specific session.

        Args:
            session_token: Session token to revoke

        Returns:
            True if session was revoked
        """
        if session_token in self._active_sessions:
            self._active_sessions[session_token].is_active = False
            self.logger.info(f"Session {session_token} revoked")
            return True

        return False

    def revoke_all_user_sessions(self, user_id: int) -> int:
        """Revoke all sessions for user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions revoked
        """
        revoked_count = 0

        for session_token, session in list(self._active_sessions.items()):
            if session.user_id == user_id:
                session.is_active = False
                del self._active_sessions[session_token]
                revoked_count += 1

        if revoked_count > 0:
            self.logger.info(f"Revoked {revoked_count} sessions for user {user_id}")

        return revoked_count

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        to_remove = []

        for session_token, session in self._active_sessions.items():
            if session.is_expired() or not session.is_active:
                to_remove.append(session_token)

        for token in to_remove:
            del self._active_sessions[token]

        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} expired sessions")

        return len(to_remove)

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with session statistics
        """
        current_time = datetime.utcnow()
        active_sessions = 0
        expired_sessions = 0
        total_users = set()

        for session in self._active_sessions.values():
            if session.is_active and not session.is_expired():
                active_sessions += 1
                total_users.add(session.user_id)
            else:
                expired_sessions += 1

        return {
            'active_sessions': active_sessions,
            'expired_sessions': expired_sessions,
            'unique_users': len(total_users),
            'total_sessions': len(self._active_sessions),
            'cleanup_timestamp': current_time.isoformat()
        }

    def generate_password_reset_token(self, user_id: int) -> str:
        """Generate password reset token.

        Args:
            user_id: User ID

        Returns:
            Password reset token
        """
        token = secrets.token_urlsafe(32)

        # In production, store token with expiration in database
        # For now, just return the token

        self.logger.info(f"Password reset token generated for user {user_id}")
        return token

    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using reset token.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            True if password reset successful
        """
        try:
            # Validate new password
            password_errors = self._validate_password_strength(new_password)
            if password_errors:
                raise ValidationError(
                    f"Password validation failed: {', '.join(password_errors)}",
                    "new_password",
                    new_password
                )

            # In production, validate token and get user_id from database
            # For now, assume token is valid and reset for a dummy user

            self.logger.info("Password reset with token completed")
            return True

        except (ValidationError,):
            raise
        except Exception as e:
            self.logger.error(f"Password reset error: {e}")
            return False

    def is_operation_authorized(
        self,
        user_id: int,
        operation: str,
        resource: str,
        project_id: str = None,
        session_token: str = None
    ) -> bool:
        """Check if user is authorized for operation.

        Args:
            user_id: User ID
            operation: Operation to check
            resource: Resource being accessed
            project_id: Project ID for context
            session_token: Session token for validation

        Returns:
            True if authorized
        """
        try:
            # Validate session if provided
            if session_token:
                session = self.validate_session(session_token)
                if not session or session.user_id != user_id:
                    return False

            # Get user
            user = self._get_user_by_id(user_id)
            if not user or not user.is_active:
                return False

            # Basic authorization logic (would be more complex in production)
            # For now, allow all operations for active users

            return True

        except Exception as e:
            self.logger.error(f"Authorization check error for user {user_id}: {e}")
            return False

    def get_user_permissions(self, user_id: int, project_id: str = None) -> List[str]:
        """Get user permissions.

        Args:
            user_id: User ID
            project_id: Project ID for context

        Returns:
            List of user permissions
        """
        try:
            user = self._get_user_by_id(user_id)
            if not user:
                return []

            # Basic permissions based on user status
            permissions = ['read_own_data']

            if user.is_active:
                permissions.extend([
                    'create_documents',
                    'update_own_documents',
                    'delete_own_documents',
                    'search_documents'
                ])

            # In production, this would check roles and project permissions
            # For now, return basic permissions

            return permissions

        except Exception as e:
            self.logger.error(f"Error getting permissions for user {user_id}: {e}")
            return []

    def create_user_response(self, user: User) -> UserResponse:
        """Create user response with additional data.

        Args:
            user: User object

        Returns:
            User response with statistics
        """
        try:
            # Get user statistics (simplified)
            total_documents = 0  # Would query document repository
            total_xp = 0  # Would query XP repository
            achievements_count = 0  # Would query achievements repository
            study_streak_days = 0  # Would calculate from study sessions

            return UserResponse(
                user=user,
                total_documents=total_documents,
                total_xp=total_xp,
                achievements_count=achievements_count,
                study_streak_days=study_streak_days
            )

        except Exception as e:
            self.logger.error(f"Error creating user response: {e}")
            # Return basic response without statistics
            return UserResponse(user=user)

    async def authenticate_async(
        self,
        username: str,
        password: str,
        **kwargs
    ) -> AuthResult:
        """Authenticate user asynchronously."""
        # Run sync authentication in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.authenticate,
            username,
            password,
            **kwargs
        )

    async def cleanup_sessions_async(self) -> int:
        """Clean up expired sessions asynchronously."""
        # Run sync cleanup in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cleanup_expired_sessions)
