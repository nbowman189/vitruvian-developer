"""
Nutrition Model
===============

Tracks meal logs and nutrition intake with macronutrient breakdown.
Supports tracking adherence to meal plans and dietary goals.
"""

from datetime import datetime, timezone, date, time
from typing import Optional
from sqlalchemy import String, Float, Integer, Date, DateTime, Time, ForeignKey, Text, CheckConstraint, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import db


class MealType(enum.Enum):
    """Meal type enumeration"""
    BREAKFAST = 'breakfast'
    LUNCH = 'lunch'
    DINNER = 'dinner'
    SNACK = 'snack'
    PRE_WORKOUT = 'pre_workout'
    POST_WORKOUT = 'post_workout'
    OTHER = 'other'


class AdherenceLevel(enum.Enum):
    """Plan adherence level enumeration"""
    PERFECT = 'perfect'
    GOOD = 'good'
    FAIR = 'fair'
    POOR = 'poor'
    OFF_PLAN = 'off_plan'


class MealLog(db.Model):
    """
    Meal and nutrition tracking model.

    Stores detailed meal information including macronutrients,
    calories, and adherence to meal plans.
    """

    __tablename__ = 'meal_logs'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Meal Information
    meal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    meal_time: Mapped[Optional[time]] = mapped_column(Time)
    meal_type: Mapped[MealType] = mapped_column(
        db.Enum(MealType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    # Nutrition Information
    calories: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('calories >= 0 AND calories <= 10000', name='check_calories_range')
    )
    protein_g: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('protein_g >= 0 AND protein_g <= 1000', name='check_protein_range')
    )
    carbs_g: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('carbs_g >= 0 AND carbs_g <= 1000', name='check_carbs_range')
    )
    fat_g: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('fat_g >= 0 AND fat_g <= 500', name='check_fat_range')
    )
    fiber_g: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('fiber_g >= 0 AND fiber_g <= 200', name='check_fiber_range')
    )
    sugar_g: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('sugar_g >= 0 AND sugar_g <= 500', name='check_sugar_range')
    )
    sodium_mg: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('sodium_mg >= 0 AND sodium_mg <= 50000', name='check_sodium_range')
    )

    # Hydration
    water_oz: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint('water_oz >= 0 AND water_oz <= 300', name='check_water_range')
    )

    # Meal Details
    description: Mapped[Optional[str]] = mapped_column(Text)
    foods: Mapped[Optional[str]] = mapped_column(Text)  # Comma-separated or JSON list
    recipe_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Plan Adherence
    adherence_to_plan: Mapped[Optional[AdherenceLevel]] = mapped_column(
        db.Enum(AdherenceLevel, native_enum=False, values_callable=lambda x: [e.value for e in x])
    )
    planned_meal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Subjective Feedback (1-10 scale)
    satisfaction: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('satisfaction >= 1 AND satisfaction <= 10', name='check_satisfaction_range')
    )
    hunger_before: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('hunger_before >= 1 AND hunger_before <= 10', name='check_hunger_before_range')
    )
    hunger_after: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint('hunger_after >= 1 AND hunger_after <= 10', name='check_hunger_after_range')
    )

    # Notes
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
    user = relationship('User', back_populates='meal_logs')

    # Table Constraints
    __table_args__ = (
        Index('ix_meal_logs_user_date', 'user_id', 'meal_date'),
        Index('ix_meal_logs_user_date_type', 'user_id', 'meal_date', 'meal_type'),
    )

    def __repr__(self) -> str:
        return f'<MealLog user_id={self.user_id} date={self.meal_date} type={self.meal_type.value}>'

    # Calculated Properties
    @property
    def calories_from_protein(self) -> Optional[int]:
        """Calculate calories from protein (4 cal/g)."""
        if self.protein_g is not None:
            return int(self.protein_g * 4)
        return None

    @property
    def calories_from_carbs(self) -> Optional[int]:
        """Calculate calories from carbs (4 cal/g)."""
        if self.carbs_g is not None:
            return int(self.carbs_g * 4)
        return None

    @property
    def calories_from_fat(self) -> Optional[int]:
        """Calculate calories from fat (9 cal/g)."""
        if self.fat_g is not None:
            return int(self.fat_g * 9)
        return None

    @property
    def calculated_total_calories(self) -> Optional[int]:
        """Calculate total calories from macronutrients."""
        protein_cal = self.calories_from_protein or 0
        carbs_cal = self.calories_from_carbs or 0
        fat_cal = self.calories_from_fat or 0

        if protein_cal or carbs_cal or fat_cal:
            return protein_cal + carbs_cal + fat_cal
        return None

    @property
    def protein_percentage(self) -> Optional[float]:
        """Calculate percentage of calories from protein."""
        if self.calories and self.calories > 0 and self.calories_from_protein:
            return (self.calories_from_protein / self.calories) * 100
        return None

    @property
    def carbs_percentage(self) -> Optional[float]:
        """Calculate percentage of calories from carbs."""
        if self.calories and self.calories > 0 and self.calories_from_carbs:
            return (self.calories_from_carbs / self.calories) * 100
        return None

    @property
    def fat_percentage(self) -> Optional[float]:
        """Calculate percentage of calories from fat."""
        if self.calories and self.calories > 0 and self.calories_from_fat:
            return (self.calories_from_fat / self.calories) * 100
        return None

    @property
    def macronutrient_ratio(self) -> Optional[str]:
        """Get macronutrient ratio as string (e.g., "40/30/30")."""
        protein_pct = self.protein_percentage
        carbs_pct = self.carbs_percentage
        fat_pct = self.fat_percentage

        if protein_pct is not None and carbs_pct is not None and fat_pct is not None:
            return f"{protein_pct:.0f}/{carbs_pct:.0f}/{fat_pct:.0f}"
        return None

    # Serialization
    def to_dict(self, include_calculated: bool = True) -> dict:
        """
        Convert meal log to dictionary for API responses.

        Args:
            include_calculated: Include calculated fields (default: True)

        Returns:
            Dictionary representation of meal log
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'meal_date': self.meal_date.isoformat() if self.meal_date else None,
            'meal_time': self.meal_time.isoformat() if self.meal_time else None,
            'meal_type': self.meal_type.value,
            'nutrition': {
                'calories': self.calories,
                'protein_g': self.protein_g,
                'carbs_g': self.carbs_g,
                'fat_g': self.fat_g,
                'fiber_g': self.fiber_g,
                'sugar_g': self.sugar_g,
                'sodium_mg': self.sodium_mg,
                'water_oz': self.water_oz,
            },
            'meal_details': {
                'description': self.description,
                'foods': self.foods,
                'recipe_name': self.recipe_name,
            },
            'adherence': {
                'level': self.adherence_to_plan.value if self.adherence_to_plan else None,
                'planned_meal': self.planned_meal,
            },
            'feedback': {
                'satisfaction': self.satisfaction,
                'hunger_before': self.hunger_before,
                'hunger_after': self.hunger_after,
            },
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_calculated:
            data['calculated'] = {
                'calories_from_protein': self.calories_from_protein,
                'calories_from_carbs': self.calories_from_carbs,
                'calories_from_fat': self.calories_from_fat,
                'calculated_total_calories': self.calculated_total_calories,
                'protein_percentage': self.protein_percentage,
                'carbs_percentage': self.carbs_percentage,
                'fat_percentage': self.fat_percentage,
                'macronutrient_ratio': self.macronutrient_ratio,
            }

        return data
