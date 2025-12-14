"""
Coaching Models
===============

Tracks coaching sessions, user goals, and progress photos.
Replaces the single-user Coaching_sessions.md file with multi-user database storage.
"""

from datetime import datetime, timezone, date
from typing import Optional, List
from sqlalchemy import String, Float, Integer, Date, DateTime, ForeignKey, Text, CheckConstraint, Index, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import db


class GoalType(enum.Enum):
    """Goal type enumeration"""
    WEIGHT_LOSS = 'weight_loss'
    MUSCLE_GAIN = 'muscle_gain'
    STRENGTH = 'strength'
    ENDURANCE = 'endurance'
    FLEXIBILITY = 'flexibility'
    SKILL = 'skill'
    HABIT = 'habit'
    NUTRITION = 'nutrition'
    OTHER = 'other'


class GoalStatus(enum.Enum):
    """Goal status enumeration"""
    ACTIVE = 'active'
    COMPLETED = 'completed'
    PAUSED = 'paused'
    ABANDONED = 'abandoned'


class PhotoType(enum.Enum):
    """Progress photo type enumeration"""
    FRONT = 'front'
    SIDE = 'side'
    BACK = 'back'
    FLEX = 'flex'
    COMPARISON = 'comparison'
    OTHER = 'other'


class CoachingSession(db.Model):
    """
    Coaching session tracking model.

    Stores coaching session information including discussion topics,
    feedback, action items, and follow-up planning.

    Replaces: Health_and_Fitness/data/Coaching_sessions.md
    """

    __tablename__ = 'coaching_sessions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    coach_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Session Information
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('duration_minutes > 0 AND duration_minutes <= 480', name='check_coaching_duration_range')
    )

    # Session Content
    topics: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    discussion_notes: Mapped[Optional[str]] = mapped_column(Text)
    coach_feedback: Mapped[Optional[str]] = mapped_column(Text)
    action_items: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    # Follow-up
    next_session_date: Mapped[Optional[date]] = mapped_column(Date)
    completed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Session Rating (1-10 scale)
    user_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('user_rating >= 1 AND user_rating <= 10', name='check_user_rating_range')
    )

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

    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='coaching_sessions')
    coach = relationship('User', foreign_keys=[coach_id], back_populates='coached_sessions')

    # Table Constraints
    __table_args__ = (
        Index('ix_coaching_sessions_user_date', 'user_id', 'session_date'),
        Index('ix_coaching_sessions_coach_date', 'coach_id', 'session_date'),
    )

    def __repr__(self) -> str:
        return f'<CoachingSession user_id={self.user_id} coach_id={self.coach_id} date={self.session_date}>'

    # Calculated Properties
    @property
    def is_overdue(self) -> bool:
        """Check if action items are overdue (past next session date)."""
        if not self.completed and self.next_session_date:
            return date.today() > self.next_session_date
        return False

    @property
    def days_until_next_session(self) -> Optional[int]:
        """Calculate days until next session."""
        if self.next_session_date:
            delta = self.next_session_date - date.today()
            return delta.days
        return None

    # Serialization
    def to_dict(self, include_coach_info: bool = False) -> dict:
        """
        Convert coaching session to dictionary for API responses.

        Args:
            include_coach_info: Include coach details (default: False)

        Returns:
            Dictionary representation of coaching session
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'coach_id': self.coach_id,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'duration_minutes': self.duration_minutes,
            'topics': self.topics,
            'discussion_notes': self.discussion_notes,
            'coach_feedback': self.coach_feedback,
            'action_items': self.action_items,
            'next_session_date': self.next_session_date.isoformat() if self.next_session_date else None,
            'completed': self.completed,
            'completion_notes': self.completion_notes,
            'user_rating': self.user_rating,
            'is_overdue': self.is_overdue,
            'days_until_next_session': self.days_until_next_session,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_coach_info and self.coach:
            data['coach'] = self.coach.to_dict()

        return data


class UserGoal(db.Model):
    """
    User goal tracking model.

    Tracks user goals with progress monitoring, target values,
    and deadline management.
    """

    __tablename__ = 'user_goals'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Goal Information
    goal_type: Mapped[GoalType] = mapped_column(
        db.Enum(GoalType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Target and Progress
    target_value: Mapped[Optional[float]] = mapped_column(Float)
    target_unit: Mapped[Optional[str]] = mapped_column(String(50))
    current_value: Mapped[Optional[float]] = mapped_column(Float)
    progress_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_progress_range')
    )

    # Timeline
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    target_date: Mapped[Optional[date]] = mapped_column(Date)
    completed_date: Mapped[Optional[date]] = mapped_column(Date)

    # Status
    status: Mapped[GoalStatus] = mapped_column(
        db.Enum(GoalStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=GoalStatus.ACTIVE
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    milestones: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

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

    # Relationships
    user = relationship('User', back_populates='goals')

    # Table Constraints
    __table_args__ = (
        Index('ix_user_goals_user_status', 'user_id', 'status'),
        Index('ix_user_goals_user_type', 'user_id', 'goal_type'),
    )

    def __repr__(self) -> str:
        return f'<UserGoal user_id={self.user_id} title={self.title} status={self.status.value}>'

    # Calculated Properties
    @property
    def is_overdue(self) -> bool:
        """Check if goal is overdue."""
        if self.status == GoalStatus.ACTIVE and self.target_date:
            return date.today() > self.target_date
        return False

    @property
    def days_remaining(self) -> Optional[int]:
        """Calculate days remaining until target date."""
        if self.target_date:
            delta = self.target_date - date.today()
            return delta.days
        return None

    @property
    def days_active(self) -> int:
        """Calculate number of days goal has been active."""
        delta = date.today() - self.start_date
        return delta.days

    def calculate_progress(self, current_value: Optional[float] = None) -> Optional[float]:
        """
        Calculate progress percentage based on current and target values.

        Args:
            current_value: Current value (uses stored value if not provided)

        Returns:
            Progress percentage (0-100), or None if insufficient data
        """
        current = current_value if current_value is not None else self.current_value
        if current is not None and self.target_value is not None and self.target_value != 0:
            return min(100, max(0, (current / self.target_value) * 100))
        return None

    def update_progress(self, current_value: float, auto_complete: bool = True) -> None:
        """
        Update goal progress with new value.

        Args:
            current_value: New current value
            auto_complete: Automatically complete goal if target reached (default: True)
        """
        self.current_value = current_value
        self.progress_percentage = self.calculate_progress(current_value)

        if auto_complete and self.progress_percentage and self.progress_percentage >= 100:
            self.status = GoalStatus.COMPLETED
            self.completed_date = date.today()

    # Serialization
    def to_dict(self) -> dict:
        """
        Convert user goal to dictionary for API responses.

        Returns:
            Dictionary representation of user goal
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_type': self.goal_type.value,
            'title': self.title,
            'description': self.description,
            'target': {
                'value': self.target_value,
                'unit': self.target_unit,
                'date': self.target_date.isoformat() if self.target_date else None,
            },
            'progress': {
                'current_value': self.current_value,
                'percentage': self.progress_percentage,
            },
            'timeline': {
                'start_date': self.start_date.isoformat() if self.start_date else None,
                'completed_date': self.completed_date.isoformat() if self.completed_date else None,
                'days_remaining': self.days_remaining,
                'days_active': self.days_active,
                'is_overdue': self.is_overdue,
            },
            'status': self.status.value,
            'notes': self.notes,
            'milestones': self.milestones,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ProgressPhoto(db.Model):
    """
    Progress photo tracking model.

    Stores progress photos with metadata including date, weight, body fat,
    and photo type for visual progress tracking.
    """

    __tablename__ = 'progress_photos'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Photo Information
    photo_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    photo_type: Mapped[PhotoType] = mapped_column(
        db.Enum(PhotoType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Associated Metrics (snapshot at time of photo)
    weight_lbs: Mapped[Optional[float]] = mapped_column(Float)
    body_fat_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('body_fat_percentage >= 0 AND body_fat_percentage <= 100', name='check_photo_body_fat_range')
    )

    # Context
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

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

    # Relationships
    user = relationship('User', back_populates='progress_photos')

    # Table Constraints
    __table_args__ = (
        Index('ix_progress_photos_user_date', 'user_id', 'photo_date'),
        Index('ix_progress_photos_user_type', 'user_id', 'photo_type'),
    )

    def __repr__(self) -> str:
        return f'<ProgressPhoto user_id={self.user_id} date={self.photo_date} type={self.photo_type.value}>'

    # Serialization
    def to_dict(self, include_url: bool = True) -> dict:
        """
        Convert progress photo to dictionary for API responses.

        Args:
            include_url: Include photo URL (default: True)

        Returns:
            Dictionary representation of progress photo
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'photo_date': self.photo_date.isoformat() if self.photo_date else None,
            'photo_type': self.photo_type.value,
            'weight_lbs': self.weight_lbs,
            'body_fat_percentage': self.body_fat_percentage,
            'notes': self.notes,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_url:
            data['photo_url'] = self.photo_url

        return data
