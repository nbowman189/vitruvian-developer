"""
User Model
==========

User authentication and profile management with Flask-Login integration.
Supports multiple user roles (user, admin, coach) and security features.
"""

from datetime import datetime, timezone
from typing import Optional
from flask_login import UserMixin
from sqlalchemy import String, Boolean, DateTime, Integer, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import bcrypt
import enum

from . import db


class UserRole(enum.Enum):
    """User role enumeration"""
    USER = 'user'
    ADMIN = 'admin'
    COACH = 'coach'


class User(UserMixin, db.Model):
    """
    User model for authentication and profile management.

    Implements Flask-Login UserMixin for authentication support.
    Includes security features like password hashing and account locking.
    """

    __tablename__ = 'users'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Authentication Fields
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role and Status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Profile Fields
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    profile_photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Security Fields
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    health_metrics = relationship('HealthMetric', back_populates='user', cascade='all, delete-orphan')
    workout_sessions = relationship('WorkoutSession', back_populates='user', cascade='all, delete-orphan')
    coaching_sessions = relationship('CoachingSession', foreign_keys='CoachingSession.user_id', back_populates='user', cascade='all, delete-orphan')
    coached_sessions = relationship('CoachingSession', foreign_keys='CoachingSession.coach_id', back_populates='coach', cascade='all, delete-orphan')
    goals = relationship('UserGoal', back_populates='user', cascade='all, delete-orphan')
    progress_photos = relationship('ProgressPhoto', back_populates='user', cascade='all, delete-orphan')
    meal_logs = relationship('MealLog', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')
    conversation_logs = relationship('ConversationLog', back_populates='user', cascade='all, delete-orphan')
    behavior_definitions = relationship('BehaviorDefinition', back_populates='user', cascade='all, delete-orphan')
    behavior_logs = relationship('BehaviorLog', back_populates='user', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    # Password Management
    def set_password(self, password: str) -> None:
        """
        Hash and set user password using bcrypt.

        Args:
            password: Plain text password to hash
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    # Flask-Login Integration
    @property
    def is_authenticated(self) -> bool:
        """Return True if user is authenticated."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Return False as this is not an anonymous user."""
        return False

    def get_id(self) -> str:
        """Return user ID as string for Flask-Login."""
        return str(self.id)

    # Account Security
    def is_locked(self) -> bool:
        """
        Check if account is currently locked.

        Returns:
            True if account is locked, False otherwise
        """
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock account for specified duration.

        Args:
            duration_minutes: Duration to lock account (default: 30 minutes)
        """
        from datetime import timedelta
        self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0

    def unlock_account(self) -> None:
        """Unlock account and reset failed login attempts."""
        self.locked_until = None
        self.failed_login_attempts = 0

    def increment_failed_login(self, max_attempts: int = 5) -> None:
        """
        Increment failed login attempts and lock account if threshold exceeded.

        Args:
            max_attempts: Maximum allowed failed attempts before locking (default: 5)
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lock_account()

    def reset_failed_login(self) -> None:
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0

    def update_last_login(self) -> None:
        """Update last login timestamp to current time."""
        self.last_login = datetime.now(timezone.utc)

    # Role Checks
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def is_coach(self) -> bool:
        """Check if user has coach role."""
        return self.role == UserRole.COACH

    def is_regular_user(self) -> bool:
        """Check if user has regular user role."""
        return self.role == UserRole.USER

    # Serialization
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary for API responses.

        Args:
            include_sensitive: Include sensitive fields like email (default: False)

        Returns:
            Dictionary representation of user
        """
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role.value,
            'is_active': self.is_active,
            'full_name': self.full_name,
            'profile_photo_url': self.profile_photo_url,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

        if include_sensitive:
            data.update({
                'email': self.email,
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_locked(),
                'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            })

        return data
