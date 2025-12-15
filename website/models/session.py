"""
Session Model
=============

Manages user sessions for authentication and security tracking.
Provides session lifecycle management with expiration and security metadata.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import INET, UUID
import uuid

from . import db


class UserSession(db.Model):
    """
    User session management model.

    Tracks active user sessions with security metadata including
    IP address, user agent, and expiration management.
    """

    __tablename__ = 'user_sessions'

    # Primary Key (using UUID for session ID)
    session_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Session Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Security Information
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support (max 45 chars)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    # Session Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[Optional[str]] = mapped_column(String(200))

    # Device Information
    device_type: Mapped[Optional[str]] = mapped_column(String(50))  # mobile, tablet, desktop
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    os: Mapped[Optional[str]] = mapped_column(String(100))

    # Remember Me
    remember_me: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship('User', back_populates='sessions')

    # Table Constraints
    __table_args__ = (
        Index('ix_user_sessions_user_active', 'user_id', 'is_active'),
        Index('ix_user_sessions_expires', 'expires_at'),
    )

    def __repr__(self) -> str:
        return f'<UserSession session_id={self.session_id} user_id={self.user_id} active={self.is_active}>'

    # Class Methods
    @classmethod
    def create_session(
        cls,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False,
        duration_hours: int = 24
    ) -> 'UserSession':
        """
        Create a new user session.

        Args:
            user_id: User ID for the session
            ip_address: Client IP address
            user_agent: Client user agent string
            remember_me: Whether this is a persistent session
            duration_hours: Session duration in hours (default: 24)

        Returns:
            New UserSession instance
        """
        # Extend duration for remember me sessions
        if remember_me:
            duration_hours = 24 * 30  # 30 days

        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        return cls(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=remember_me,
            expires_at=expires_at
        )

    # Instance Methods
    def is_expired(self) -> bool:
        """
        Check if session has expired.

        Returns:
            True if session is expired, False otherwise
        """
        return datetime.now(timezone.utc) >= self.expires_at

    def is_valid(self) -> bool:
        """
        Check if session is valid (active and not expired).

        Returns:
            True if session is valid, False otherwise
        """
        return self.is_active and not self.is_expired()

    def revoke(self, reason: Optional[str] = None) -> None:
        """
        Revoke the session.

        Args:
            reason: Optional reason for revocation
        """
        self.is_active = False
        self.revoked_at = datetime.now(timezone.utc)
        if reason:
            self.revocation_reason = reason

    def extend_session(self, hours: int = 24) -> None:
        """
        Extend session expiration.

        Args:
            hours: Number of hours to extend (default: 24)
        """
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.update_activity()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    def parse_user_agent(self) -> None:
        """
        Parse user agent string to extract device, browser, and OS information.
        This is a simplified version - in production, use a library like user-agents.
        """
        if not self.user_agent:
            return

        ua_lower = self.user_agent.lower()

        # Detect device type
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            self.device_type = 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            self.device_type = 'tablet'
        else:
            self.device_type = 'desktop'

        # Detect browser
        if 'chrome' in ua_lower:
            self.browser = 'Chrome'
        elif 'firefox' in ua_lower:
            self.browser = 'Firefox'
        elif 'safari' in ua_lower:
            self.browser = 'Safari'
        elif 'edge' in ua_lower:
            self.browser = 'Edge'
        elif 'opera' in ua_lower:
            self.browser = 'Opera'

        # Detect OS
        if 'windows' in ua_lower:
            self.os = 'Windows'
        elif 'mac' in ua_lower or 'macos' in ua_lower:
            self.os = 'MacOS'
        elif 'linux' in ua_lower:
            self.os = 'Linux'
        elif 'android' in ua_lower:
            self.os = 'Android'
        elif 'ios' in ua_lower or 'iphone' in ua_lower or 'ipad' in ua_lower:
            self.os = 'iOS'

    @property
    def time_until_expiration(self) -> timedelta:
        """
        Calculate time remaining until expiration.

        Returns:
            Timedelta representing time until expiration
        """
        return self.expires_at - datetime.now(timezone.utc)

    @property
    def time_since_activity(self) -> timedelta:
        """
        Calculate time since last activity.

        Returns:
            Timedelta representing time since last activity
        """
        return datetime.now(timezone.utc) - self.last_activity

    @property
    def session_age(self) -> timedelta:
        """
        Calculate total session age.

        Returns:
            Timedelta representing session age
        """
        return datetime.now(timezone.utc) - self.created_at

    # Serialization
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user session to dictionary for API responses.

        Args:
            include_sensitive: Include sensitive fields like IP (default: False)

        Returns:
            Dictionary representation of user session
        """
        data = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'is_valid': self.is_valid(),
            'device_info': {
                'device_type': self.device_type,
                'browser': self.browser,
                'os': self.os,
            },
            'remember_me': self.remember_me,
            'session_stats': {
                'time_until_expiration': str(self.time_until_expiration),
                'time_since_activity': str(self.time_since_activity),
                'session_age': str(self.session_age),
            },
        }

        if include_sensitive:
            data.update({
                'ip_address': self.ip_address,
                'user_agent': self.user_agent,
                'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
                'revocation_reason': self.revocation_reason,
            })

        return data
