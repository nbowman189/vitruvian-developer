"""
Behavior Tracking Models
========================

Tracks user-defined behaviors and daily completion logs.
Enables flexible habit tracking with custom categories.
"""

from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Text, Boolean, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import db


class BehaviorCategory(enum.Enum):
    """Behavior category enumeration"""
    HEALTH = 'health'
    FITNESS = 'fitness'
    NUTRITION = 'nutrition'
    LEARNING = 'learning'
    PRODUCTIVITY = 'productivity'
    WELLNESS = 'wellness'
    CUSTOM = 'custom'


class BehaviorDefinition(db.Model):
    """
    User-defined behavior categories for tracking.

    Similar to ExerciseDefinition pattern - defines what can be tracked.
    Each user creates their own behavior definitions.
    Supports soft delete to preserve historical data.
    """

    __tablename__ = 'behavior_definitions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Behavior Information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[BehaviorCategory] = mapped_column(
        db.Enum(BehaviorCategory, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    # Display Settings
    icon: Mapped[Optional[str]] = mapped_column(String(50))  # Bootstrap icon class (e.g., "bi-check-circle")
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code (e.g., "#1a237e")
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Tracking Settings
    target_frequency: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('target_frequency >= 1 AND target_frequency <= 7', name='check_target_frequency_range')
    )  # Target days per week (1-7)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Soft delete

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
    user = relationship('User', back_populates='behavior_definitions')
    behavior_logs = relationship('BehaviorLog', back_populates='behavior_definition', cascade='all, delete-orphan')

    # Table Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_behavior_name'),
        Index('ix_behavior_definitions_user_active', 'user_id', 'is_active'),
    )

    def to_dict(self, include_stats: bool = False) -> dict:
        """
        Serialize to dict for API responses.

        Args:
            include_stats: Whether to include completion statistics

        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'icon': self.icon,
            'color': self.color,
            'display_order': self.display_order,
            'target_frequency': self.target_frequency,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_stats:
            # Calculate recent completion stats
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            recent_logs = [log for log in self.behavior_logs
                           if log.tracked_date >= start_date and log.tracked_date <= end_date]

            completed_count = sum(1 for log in recent_logs if log.completed)
            data['stats'] = {
                'recent_completion_rate': round((completed_count / len(recent_logs) * 100) if recent_logs else 0, 1),
                'recent_completed': completed_count,
                'recent_total': len(recent_logs)
            }

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<BehaviorDefinition {self.id}: '{self.name}' ({self.category.value})>"


class BehaviorLog(db.Model):
    """
    Daily behavior completion tracking.

    Binary completion: did the user complete this behavior on this date?
    One log entry per behavior per day (enforced by unique constraint).
    """

    __tablename__ = 'behavior_logs'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    behavior_definition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('behavior_definitions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Tracking Data
    tracked_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optional Context
    notes: Mapped[Optional[str]] = mapped_column(Text)

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
    user = relationship('User', back_populates='behavior_logs')
    behavior_definition = relationship('BehaviorDefinition', back_populates='behavior_logs')

    # Table Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'behavior_definition_id', 'tracked_date', name='uq_user_behavior_date'),
        Index('ix_behavior_logs_user_date', 'user_id', 'tracked_date'),
        Index('ix_behavior_logs_definition_date', 'behavior_definition_id', 'tracked_date'),
    )

    def to_dict(self) -> dict:
        """Serialize to dict for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'behavior_definition_id': self.behavior_definition_id,
            'behavior_name': self.behavior_definition.name if self.behavior_definition else None,
            'behavior_category': self.behavior_definition.category.value if self.behavior_definition else None,
            'behavior_icon': self.behavior_definition.icon if self.behavior_definition else None,
            'behavior_color': self.behavior_definition.color if self.behavior_definition else None,
            'tracked_date': self.tracked_date.isoformat() if self.tracked_date else None,
            'completed': self.completed,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.completed else "✗"
        behavior_name = self.behavior_definition.name if self.behavior_definition else "Unknown"
        return f"<BehaviorLog {self.id}: {status} {behavior_name} on {self.tracked_date}>"
