"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-12-14

Creates all tables for the multi-user health & fitness tracking application:
- users: User accounts and authentication
- health_metrics: Health measurements tracking
- workout_sessions: Workout session tracking
- exercise_logs: Individual exercise performance
- exercise_definitions: Shared exercise reference data
- coaching_sessions: Coaching sessions and feedback
- user_goals: Goal tracking with progress
- progress_photos: Progress photo management
- meal_logs: Nutrition and meal tracking
- user_sessions: Session management for security
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('profile_photo_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create health_metrics table
    op.create_table(
        'health_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recorded_date', sa.Date(), nullable=False),
        sa.Column('weight_lbs', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('muscle_mass_lbs', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('waist_inches', sa.Float(), nullable=True),
        sa.Column('chest_inches', sa.Float(), nullable=True),
        sa.Column('left_arm_inches', sa.Float(), nullable=True),
        sa.Column('right_arm_inches', sa.Float(), nullable=True),
        sa.Column('left_thigh_inches', sa.Float(), nullable=True),
        sa.Column('right_thigh_inches', sa.Float(), nullable=True),
        sa.Column('hips_inches', sa.Float(), nullable=True),
        sa.Column('neck_inches', sa.Float(), nullable=True),
        sa.Column('resting_heart_rate', sa.Integer(), nullable=True),
        sa.Column('blood_pressure_systolic', sa.Integer(), nullable=True),
        sa.Column('blood_pressure_diastolic', sa.Integer(), nullable=True),
        sa.Column('energy_level', sa.Integer(), nullable=True),
        sa.Column('mood', sa.Integer(), nullable=True),
        sa.Column('sleep_quality', sa.Integer(), nullable=True),
        sa.Column('stress_level', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'recorded_date', name='uq_user_health_date'),
        sa.CheckConstraint('body_fat_percentage >= 0 AND body_fat_percentage <= 100', name='check_body_fat_range'),
        sa.CheckConstraint('bmi >= 0 AND bmi <= 100', name='check_bmi_range'),
        sa.CheckConstraint('resting_heart_rate >= 20 AND resting_heart_rate <= 300', name='check_heart_rate_range'),
        sa.CheckConstraint('blood_pressure_systolic >= 50 AND blood_pressure_systolic <= 300', name='check_systolic_range'),
        sa.CheckConstraint('blood_pressure_diastolic >= 30 AND blood_pressure_diastolic <= 200', name='check_diastolic_range'),
        sa.CheckConstraint('energy_level >= 1 AND energy_level <= 10', name='check_energy_level_range'),
        sa.CheckConstraint('mood >= 1 AND mood <= 10', name='check_mood_range'),
        sa.CheckConstraint('sleep_quality >= 1 AND sleep_quality <= 10', name='check_sleep_quality_range'),
        sa.CheckConstraint('stress_level >= 1 AND stress_level <= 10', name='check_stress_level_range')
    )
    op.create_index(op.f('ix_health_metrics_user_id'), 'health_metrics', ['user_id'])
    op.create_index(op.f('ix_health_metrics_recorded_date'), 'health_metrics', ['recorded_date'])
    op.create_index('ix_health_metrics_user_date', 'health_metrics', ['user_id', 'recorded_date'])

    # Create exercise_definitions table (no foreign keys to users)
    op.create_table(
        'exercise_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('muscle_groups', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('equipment_needed', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('tips', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(length=500), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_exercise_definitions_name'), 'exercise_definitions', ['name'], unique=True)
    op.create_index(op.f('ix_exercise_definitions_category'), 'exercise_definitions', ['category'])

    # Create workout_sessions table
    op.create_table(
        'workout_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('program_phase', sa.String(length=100), nullable=True),
        sa.Column('week_number', sa.Integer(), nullable=True),
        sa.Column('day_number', sa.Integer(), nullable=True),
        sa.Column('intensity', sa.Integer(), nullable=True),
        sa.Column('fatigue', sa.Integer(), nullable=True),
        sa.Column('soreness', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('coach_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('duration_minutes > 0 AND duration_minutes <= 480', name='check_duration_range'),
        sa.CheckConstraint('intensity >= 1 AND intensity <= 10', name='check_intensity_range'),
        sa.CheckConstraint('fatigue >= 1 AND fatigue <= 10', name='check_fatigue_range'),
        sa.CheckConstraint('soreness >= 1 AND soreness <= 10', name='check_soreness_range')
    )
    op.create_index(op.f('ix_workout_sessions_user_id'), 'workout_sessions', ['user_id'])
    op.create_index(op.f('ix_workout_sessions_session_date'), 'workout_sessions', ['session_date'])
    op.create_index('ix_workout_sessions_user_date', 'workout_sessions', ['user_id', 'session_date'])

    # Create exercise_logs table
    op.create_table(
        'exercise_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workout_session_id', sa.Integer(), nullable=False),
        sa.Column('exercise_definition_id', sa.Integer(), nullable=True),
        sa.Column('exercise_name', sa.String(length=200), nullable=False),
        sa.Column('sets', sa.Integer(), nullable=True),
        sa.Column('reps', sa.Integer(), nullable=True),
        sa.Column('weight_lbs', sa.Float(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('distance_miles', sa.Float(), nullable=True),
        sa.Column('form_quality', sa.Integer(), nullable=True),
        sa.Column('rpe', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['workout_session_id'], ['workout_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_definition_id'], ['exercise_definitions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('sets > 0 AND sets <= 50', name='check_sets_range'),
        sa.CheckConstraint('reps > 0 AND reps <= 500', name='check_reps_range'),
        sa.CheckConstraint('rest_seconds >= 0 AND rest_seconds <= 600', name='check_rest_range'),
        sa.CheckConstraint('form_quality >= 1 AND form_quality <= 10', name='check_form_range'),
        sa.CheckConstraint('rpe >= 1 AND rpe <= 10', name='check_rpe_range')
    )
    op.create_index(op.f('ix_exercise_logs_workout_session_id'), 'exercise_logs', ['workout_session_id'])
    op.create_index(op.f('ix_exercise_logs_exercise_definition_id'), 'exercise_logs', ['exercise_definition_id'])
    op.create_index('ix_exercise_logs_session', 'exercise_logs', ['workout_session_id', 'order_index'])

    # Create coaching_sessions table
    op.create_table(
        'coaching_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('discussion_notes', sa.Text(), nullable=True),
        sa.Column('coach_feedback', sa.Text(), nullable=True),
        sa.Column('action_items', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('next_session_date', sa.Date(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['coach_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('duration_minutes > 0 AND duration_minutes <= 480', name='check_coaching_duration_range'),
        sa.CheckConstraint('user_rating >= 1 AND user_rating <= 10', name='check_user_rating_range')
    )
    op.create_index(op.f('ix_coaching_sessions_user_id'), 'coaching_sessions', ['user_id'])
    op.create_index(op.f('ix_coaching_sessions_coach_id'), 'coaching_sessions', ['coach_id'])
    op.create_index(op.f('ix_coaching_sessions_session_date'), 'coaching_sessions', ['session_date'])
    op.create_index('ix_coaching_sessions_user_date', 'coaching_sessions', ['user_id', 'session_date'])
    op.create_index('ix_coaching_sessions_coach_date', 'coaching_sessions', ['coach_id', 'session_date'])

    # Create user_goals table
    op.create_table(
        'user_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('goal_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('target_unit', sa.String(length=50), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('milestones', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_progress_range')
    )
    op.create_index(op.f('ix_user_goals_user_id'), 'user_goals', ['user_id'])
    op.create_index(op.f('ix_user_goals_goal_type'), 'user_goals', ['goal_type'])
    op.create_index('ix_user_goals_user_status', 'user_goals', ['user_id', 'status'])
    op.create_index('ix_user_goals_user_type', 'user_goals', ['user_id', 'goal_type'])

    # Create progress_photos table
    op.create_table(
        'progress_photos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('photo_date', sa.Date(), nullable=False),
        sa.Column('photo_url', sa.String(length=500), nullable=False),
        sa.Column('photo_type', sa.String(length=50), nullable=False),
        sa.Column('weight_lbs', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('body_fat_percentage >= 0 AND body_fat_percentage <= 100', name='check_photo_body_fat_range')
    )
    op.create_index(op.f('ix_progress_photos_user_id'), 'progress_photos', ['user_id'])
    op.create_index(op.f('ix_progress_photos_photo_date'), 'progress_photos', ['photo_date'])
    op.create_index('ix_progress_photos_user_date', 'progress_photos', ['user_id', 'photo_date'])
    op.create_index('ix_progress_photos_user_type', 'progress_photos', ['user_id', 'photo_type'])

    # Create meal_logs table
    op.create_table(
        'meal_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('meal_date', sa.Date(), nullable=False),
        sa.Column('meal_time', sa.Time(), nullable=True),
        sa.Column('meal_type', sa.String(length=50), nullable=False),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('protein_g', sa.Float(), nullable=True),
        sa.Column('carbs_g', sa.Float(), nullable=True),
        sa.Column('fat_g', sa.Float(), nullable=True),
        sa.Column('fiber_g', sa.Float(), nullable=True),
        sa.Column('sugar_g', sa.Float(), nullable=True),
        sa.Column('sodium_mg', sa.Integer(), nullable=True),
        sa.Column('water_oz', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('foods', sa.Text(), nullable=True),
        sa.Column('recipe_name', sa.String(length=200), nullable=True),
        sa.Column('adherence_to_plan', sa.String(length=20), nullable=True),
        sa.Column('planned_meal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('satisfaction', sa.Integer(), nullable=True),
        sa.Column('hunger_before', sa.Integer(), nullable=True),
        sa.Column('hunger_after', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('calories >= 0 AND calories <= 10000', name='check_calories_range'),
        sa.CheckConstraint('protein_g >= 0 AND protein_g <= 1000', name='check_protein_range'),
        sa.CheckConstraint('carbs_g >= 0 AND carbs_g <= 1000', name='check_carbs_range'),
        sa.CheckConstraint('fat_g >= 0 AND fat_g <= 500', name='check_fat_range'),
        sa.CheckConstraint('fiber_g >= 0 AND fiber_g <= 200', name='check_fiber_range'),
        sa.CheckConstraint('sugar_g >= 0 AND sugar_g <= 500', name='check_sugar_range'),
        sa.CheckConstraint('sodium_mg >= 0 AND sodium_mg <= 50000', name='check_sodium_range'),
        sa.CheckConstraint('water_oz >= 0 AND water_oz <= 300', name='check_water_range'),
        sa.CheckConstraint('satisfaction >= 1 AND satisfaction <= 10', name='check_satisfaction_range'),
        sa.CheckConstraint('hunger_before >= 1 AND hunger_before <= 10', name='check_hunger_before_range'),
        sa.CheckConstraint('hunger_after >= 1 AND hunger_after <= 10', name='check_hunger_after_range')
    )
    op.create_index(op.f('ix_meal_logs_user_id'), 'meal_logs', ['user_id'])
    op.create_index(op.f('ix_meal_logs_meal_date'), 'meal_logs', ['meal_date'])
    op.create_index(op.f('ix_meal_logs_meal_type'), 'meal_logs', ['meal_type'])
    op.create_index('ix_meal_logs_user_date', 'meal_logs', ['user_id', 'meal_date'])
    op.create_index('ix_meal_logs_user_date_type', 'meal_logs', ['user_id', 'meal_date', 'meal_type'])

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(length=200), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('browser', sa.String(length=100), nullable=True),
        sa.Column('os', sa.String(length=100), nullable=True),
        sa.Column('remember_me', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'])
    op.create_index(op.f('ix_user_sessions_created_at'), 'user_sessions', ['created_at'])
    op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'])
    op.create_index(op.f('ix_user_sessions_is_active'), 'user_sessions', ['is_active'])
    op.create_index('ix_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('user_sessions')
    op.drop_table('meal_logs')
    op.drop_table('progress_photos')
    op.drop_table('user_goals')
    op.drop_table('coaching_sessions')
    op.drop_table('exercise_logs')
    op.drop_table('workout_sessions')
    op.drop_table('exercise_definitions')
    op.drop_table('health_metrics')
    op.drop_table('users')
