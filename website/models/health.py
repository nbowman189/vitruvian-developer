"""
Health Metrics Model
====================

Tracks health measurements like weight, body fat, BMI, and body measurements.
Replaces the single-user check-in-log.md file with multi-user database storage.
"""

from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Float, Integer, Date, DateTime, ForeignKey, Text, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class HealthMetric(db.Model):
    """
    Health metrics tracking model.

    Stores user health measurements over time including weight, body composition,
    measurements, vital signs, and subjective wellness indicators.

    Replaces: Health_and_Fitness/data/check-in-log.md
    """

    __tablename__ = 'health_metrics'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Recording Information
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Body Composition Metrics
    weight_lbs: Mapped[Optional[float]] = mapped_column(Float)
    body_fat_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('body_fat_percentage >= 0 AND body_fat_percentage <= 100', name='check_body_fat_range')
    )
    muscle_mass_lbs: Mapped[Optional[float]] = mapped_column(Float)
    bmi: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('bmi >= 0 AND bmi <= 100', name='check_bmi_range')
    )

    # Body Measurements (inches)
    waist_inches: Mapped[Optional[float]] = mapped_column(Float)
    chest_inches: Mapped[Optional[float]] = mapped_column(Float)
    left_arm_inches: Mapped[Optional[float]] = mapped_column(Float)
    right_arm_inches: Mapped[Optional[float]] = mapped_column(Float)
    left_thigh_inches: Mapped[Optional[float]] = mapped_column(Float)
    right_thigh_inches: Mapped[Optional[float]] = mapped_column(Float)
    hips_inches: Mapped[Optional[float]] = mapped_column(Float)
    neck_inches: Mapped[Optional[float]] = mapped_column(Float)

    # Vital Signs
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('resting_heart_rate >= 20 AND resting_heart_rate <= 300', name='check_heart_rate_range')
    )
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('blood_pressure_systolic >= 50 AND blood_pressure_systolic <= 300', name='check_systolic_range')
    )
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('blood_pressure_diastolic >= 30 AND blood_pressure_diastolic <= 200', name='check_diastolic_range')
    )

    # Subjective Wellness Indicators (1-10 scale)
    energy_level: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('energy_level >= 1 AND energy_level <= 10', name='check_energy_level_range')
    )
    mood: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('mood >= 1 AND mood <= 10', name='check_mood_range')
    )
    sleep_quality: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('sleep_quality >= 1 AND sleep_quality <= 10', name='check_sleep_quality_range')
    )
    stress_level: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('stress_level >= 1 AND stress_level <= 10', name='check_stress_level_range')
    )

    # Notes and Context
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
    user = relationship('User', back_populates='health_metrics')

    # Table Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'recorded_date', name='uq_user_health_date'),
        Index('ix_health_metrics_user_date', 'user_id', 'recorded_date'),
    )

    def __repr__(self) -> str:
        return f'<HealthMetric user_id={self.user_id} date={self.recorded_date} weight={self.weight_lbs}>'

    # Calculated Properties
    @property
    def lean_body_mass_lbs(self) -> Optional[float]:
        """
        Calculate lean body mass (LBM) from weight and body fat percentage.

        Returns:
            Lean body mass in pounds, or None if insufficient data
        """
        if self.weight_lbs is not None and self.body_fat_percentage is not None:
            return self.weight_lbs * (1 - self.body_fat_percentage / 100)
        return None

    @property
    def fat_mass_lbs(self) -> Optional[float]:
        """
        Calculate fat mass from weight and body fat percentage.

        Returns:
            Fat mass in pounds, or None if insufficient data
        """
        if self.weight_lbs is not None and self.body_fat_percentage is not None:
            return self.weight_lbs * (self.body_fat_percentage / 100)
        return None

    @property
    def blood_pressure_formatted(self) -> Optional[str]:
        """
        Format blood pressure as systolic/diastolic string.

        Returns:
            Blood pressure as "120/80" format, or None if insufficient data
        """
        if self.blood_pressure_systolic is not None and self.blood_pressure_diastolic is not None:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None

    # Serialization
    def to_dict(self, include_calculated: bool = True) -> dict:
        """
        Convert health metric to dictionary for API responses.

        Args:
            include_calculated: Include calculated fields like LBM (default: True)

        Returns:
            Dictionary representation of health metric
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'recorded_date': self.recorded_date.isoformat() if self.recorded_date else None,
            'weight_lbs': self.weight_lbs,
            'body_fat_percentage': self.body_fat_percentage,
            'muscle_mass_lbs': self.muscle_mass_lbs,
            'bmi': self.bmi,
            # Top-level access for common measurements
            'waist_inches': self.waist_inches,
            'chest_inches': self.chest_inches,
            # Nested structure for all measurements
            'measurements': {
                'waist_inches': self.waist_inches,
                'chest_inches': self.chest_inches,
                'left_arm_inches': self.left_arm_inches,
                'right_arm_inches': self.right_arm_inches,
                'left_thigh_inches': self.left_thigh_inches,
                'right_thigh_inches': self.right_thigh_inches,
                'hips_inches': self.hips_inches,
                'neck_inches': self.neck_inches,
            },
            'vital_signs': {
                'resting_heart_rate': self.resting_heart_rate,
                'blood_pressure_systolic': self.blood_pressure_systolic,
                'blood_pressure_diastolic': self.blood_pressure_diastolic,
                'blood_pressure': self.blood_pressure_formatted,
            },
            'wellness': {
                'energy_level': self.energy_level,
                'mood': self.mood,
                'sleep_quality': self.sleep_quality,
                'stress_level': self.stress_level,
            },
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_calculated:
            data['calculated'] = {
                'lean_body_mass_lbs': self.lean_body_mass_lbs,
                'fat_mass_lbs': self.fat_mass_lbs,
            }

        return data
