"""
Database Models Package
=======================

This package contains all SQLAlchemy models for the multi-user health & fitness tracking application.

Models:
- User: User accounts and authentication
- HealthMetric: Weight, body fat, measurements tracking
- WorkoutSession: Workout sessions tracking
- ExerciseLog: Individual exercise performance logs
- ExerciseDefinition: Shared exercise reference data
- CoachingSession: Coaching sessions and feedback
- UserGoal: User goals and progress tracking
- ProgressPhoto: Progress photos with metadata
- MealLog: Meal and nutrition tracking
- UserSession: Session management for security
"""

# Import the shared db instance from main __init__.py
# This must be done before importing models to avoid circular imports
from .. import db

# Import models after db initialization to avoid circular imports
from .user import User
from .health import HealthMetric
from .workout import WorkoutSession, ExerciseLog, ExerciseDefinition
from .coaching import CoachingSession, UserGoal, ProgressPhoto
from .nutrition import MealLog
from .session import UserSession

# Export all models and db instance
__all__ = [
    'db',
    'User',
    'HealthMetric',
    'WorkoutSession',
    'ExerciseLog',
    'ExerciseDefinition',
    'CoachingSession',
    'UserGoal',
    'ProgressPhoto',
    'MealLog',
    'UserSession'
]
