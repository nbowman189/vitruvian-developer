"""
Workout Models
==============

Tracks workout sessions, individual exercise performance, and exercise definitions.
Replaces the single-user progress-check-in-log.md file with multi-user database storage.
"""

from datetime import datetime, timezone, date
from typing import Optional, List
from sqlalchemy import String, Float, Integer, Date, DateTime, ForeignKey, Text, CheckConstraint, Index, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import db


class SessionType(enum.Enum):
    """Workout session type enumeration"""
    STRENGTH = 'strength'
    CARDIO = 'cardio'
    FLEXIBILITY = 'flexibility'
    MARTIAL_ARTS = 'martial_arts'
    SPORTS = 'sports'
    RECOVERY = 'recovery'
    MIXED = 'mixed'


class ExerciseCategory(enum.Enum):
    """Exercise category enumeration"""
    COMPOUND = 'compound'
    ISOLATION = 'isolation'
    CARDIO = 'cardio'
    FLEXIBILITY = 'flexibility'
    CORE = 'core'
    PLYOMETRIC = 'plyometric'
    MARTIAL_ARTS = 'martial_arts'


class DifficultyLevel(enum.Enum):
    """Exercise difficulty enumeration"""
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'


class WorkoutSession(db.Model):
    """
    Workout session tracking model.

    Stores overall workout session information including type, duration,
    program details, and subjective feedback.

    Replaces: Health_and_Fitness/data/progress-check-in-log.md
    """

    __tablename__ = 'workout_sessions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Session Information
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    session_type: Mapped[SessionType] = mapped_column(
        db.Enum(SessionType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('duration_minutes > 0 AND duration_minutes <= 480', name='check_duration_range')
    )

    # Program Tracking
    program_phase: Mapped[Optional[str]] = mapped_column(String(100))
    week_number: Mapped[Optional[int]] = mapped_column(Integer)
    day_number: Mapped[Optional[int]] = mapped_column(Integer)

    # Intensity and Feedback (1-10 scale)
    intensity: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('intensity >= 1 AND intensity <= 10', name='check_intensity_range')
    )
    fatigue: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('fatigue >= 1 AND fatigue <= 10', name='check_fatigue_range')
    )
    soreness: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('soreness >= 1 AND soreness <= 10', name='check_soreness_range')
    )

    # Session Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    coach_notes: Mapped[Optional[str]] = mapped_column(Text)

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
    user = relationship('User', back_populates='workout_sessions')
    exercise_logs = relationship('ExerciseLog', back_populates='workout_session', cascade='all, delete-orphan')

    # Table Constraints
    __table_args__ = (
        Index('ix_workout_sessions_user_date', 'user_id', 'session_date'),
    )

    def __repr__(self) -> str:
        return f'<WorkoutSession user_id={self.user_id} date={self.session_date} type={self.session_type.value}>'

    # Calculated Properties
    @property
    def total_exercises(self) -> int:
        """Count total exercises in this session."""
        return len(self.exercise_logs)

    @property
    def total_sets(self) -> int:
        """Calculate total sets across all exercises."""
        return sum(exercise.sets for exercise in self.exercise_logs if exercise.sets)

    @property
    def average_rpe(self) -> Optional[float]:
        """Calculate average RPE across all exercises."""
        rpe_values = [ex.rpe for ex in self.exercise_logs if ex.rpe is not None]
        if rpe_values:
            return sum(rpe_values) / len(rpe_values)
        return None

    # Serialization
    def to_dict(self, include_exercises: bool = False) -> dict:
        """
        Convert workout session to dictionary for API responses.

        Args:
            include_exercises: Include detailed exercise logs (default: False)

        Returns:
            Dictionary representation of workout session
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'session_type': self.session_type.value,
            'duration_minutes': self.duration_minutes,
            'program': {
                'phase': self.program_phase,
                'week': self.week_number,
                'day': self.day_number,
            },
            'feedback': {
                'intensity': self.intensity,
                'fatigue': self.fatigue,
                'soreness': self.soreness,
            },
            'notes': self.notes,
            'coach_notes': self.coach_notes,
            'stats': {
                'total_exercises': self.total_exercises,
                'total_sets': self.total_sets,
                'average_rpe': self.average_rpe,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_exercises:
            data['exercises'] = [exercise.to_dict() for exercise in self.exercise_logs]

        return data


class ExerciseLog(db.Model):
    """
    Individual exercise performance log.

    Tracks specific exercise performance within a workout session including
    sets, reps, weight, rest periods, and subjective feedback.
    """

    __tablename__ = 'exercise_logs'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    workout_session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('workout_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    exercise_definition_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('exercise_definitions.id', ondelete='SET NULL'),
        index=True
    )

    # Exercise Identification (fallback if no definition linked)
    exercise_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Performance Metrics
    sets: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('sets > 0 AND sets <= 50', name='check_sets_range')
    )
    reps: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('reps > 0 AND reps <= 500', name='check_reps_range')
    )
    weight_lbs: Mapped[Optional[float]] = mapped_column(Float)
    rest_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('rest_seconds >= 0 AND rest_seconds <= 600', name='check_rest_range')
    )

    # Time-based Metrics (for cardio/endurance)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    distance_miles: Mapped[Optional[float]] = mapped_column(Float)

    # Feedback (1-10 scale)
    form_quality: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('form_quality >= 1 AND form_quality <= 10', name='check_form_range')
    )
    rpe: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('rpe >= 1 AND rpe <= 10', name='check_rpe_range')
    )

    # Order and Notes
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    workout_session = relationship('WorkoutSession', back_populates='exercise_logs')
    exercise_definition = relationship('ExerciseDefinition', back_populates='exercise_logs')

    # Table Constraints
    __table_args__ = (
        Index('ix_exercise_logs_session', 'workout_session_id', 'order_index'),
    )

    def __repr__(self) -> str:
        return f'<ExerciseLog session_id={self.workout_session_id} exercise={self.exercise_name}>'

    # Calculated Properties
    @property
    def total_volume(self) -> Optional[float]:
        """Calculate total volume (sets × reps × weight)."""
        if self.sets and self.reps and self.weight_lbs:
            return self.sets * self.reps * self.weight_lbs
        return None

    @property
    def pace_per_mile(self) -> Optional[float]:
        """Calculate pace in minutes per mile (for cardio exercises)."""
        if self.duration_seconds and self.distance_miles and self.distance_miles > 0:
            return (self.duration_seconds / 60) / self.distance_miles
        return None

    # Serialization
    def to_dict(self) -> dict:
        """
        Convert exercise log to dictionary for API responses.

        Returns:
            Dictionary representation of exercise log
        """
        return {
            'id': self.id,
            'workout_session_id': self.workout_session_id,
            'exercise_name': self.exercise_name,
            'exercise_definition_id': self.exercise_definition_id,
            'performance': {
                'sets': self.sets,
                'reps': self.reps,
                'weight_lbs': self.weight_lbs,
                'rest_seconds': self.rest_seconds,
                'duration_seconds': self.duration_seconds,
                'distance_miles': self.distance_miles,
            },
            'feedback': {
                'form_quality': self.form_quality,
                'rpe': self.rpe,
            },
            'calculated': {
                'total_volume': self.total_volume,
                'pace_per_mile': self.pace_per_mile,
            },
            'order_index': self.order_index,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ExerciseDefinition(db.Model):
    """
    Shared exercise reference database.

    Stores exercise definitions that can be referenced by multiple users.
    Provides consistent exercise information and metadata.
    """

    __tablename__ = 'exercise_definitions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Exercise Information
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    category: Mapped[ExerciseCategory] = mapped_column(
        db.Enum(ExerciseCategory, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    # Exercise Details
    muscle_groups: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    equipment_needed: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        db.Enum(DifficultyLevel, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Rich Content
    description: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    tips: Mapped[Optional[str]] = mapped_column(Text)
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Metadata
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))

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
    exercise_logs = relationship('ExerciseLog', back_populates='exercise_definition')

    def __repr__(self) -> str:
        return f'<ExerciseDefinition {self.name} ({self.category.value})>'

    # Serialization
    def to_dict(self) -> dict:
        """
        Convert exercise definition to dictionary for API responses.

        Returns:
            Dictionary representation of exercise definition
        """
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'muscle_groups': self.muscle_groups,
            'equipment_needed': self.equipment_needed,
            'difficulty_level': self.difficulty_level.value,
            'description': self.description,
            'instructions': self.instructions,
            'tips': self.tips,
            'video_url': self.video_url,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
