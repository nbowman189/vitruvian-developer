"""Add behavior tracking system

Revision ID: e1f2a3b4c5d6
Revises: cd6536fffee0
Create Date: 2026-01-02 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'cd6536fffee0'
branch_labels = None
depends_on = None


def upgrade():
    # Create behavior_definitions table
    op.create_table('behavior_definitions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('icon', sa.String(length=50), nullable=True),
    sa.Column('color', sa.String(length=7), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('target_frequency', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('target_frequency >= 1 AND target_frequency <= 7', name='check_target_frequency_range'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'name', name='uq_user_behavior_name')
    )
    op.create_index('ix_behavior_definitions_category', 'behavior_definitions', ['category'], unique=False)
    op.create_index('ix_behavior_definitions_user_active', 'behavior_definitions', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_behavior_definitions_user_id'), 'behavior_definitions', ['user_id'], unique=False)

    # Create behavior_logs table
    op.create_table('behavior_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('behavior_definition_id', sa.Integer(), nullable=False),
    sa.Column('tracked_date', sa.Date(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['behavior_definition_id'], ['behavior_definitions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'behavior_definition_id', 'tracked_date', name='uq_user_behavior_date')
    )
    op.create_index('ix_behavior_logs_definition_date', 'behavior_logs', ['behavior_definition_id', 'tracked_date'], unique=False)
    op.create_index('ix_behavior_logs_user_date', 'behavior_logs', ['user_id', 'tracked_date'], unique=False)
    op.create_index(op.f('ix_behavior_logs_behavior_definition_id'), 'behavior_logs', ['behavior_definition_id'], unique=False)
    op.create_index(op.f('ix_behavior_logs_tracked_date'), 'behavior_logs', ['tracked_date'], unique=False)
    op.create_index(op.f('ix_behavior_logs_user_id'), 'behavior_logs', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_behavior_logs_user_id'), table_name='behavior_logs')
    op.drop_index(op.f('ix_behavior_logs_tracked_date'), table_name='behavior_logs')
    op.drop_index(op.f('ix_behavior_logs_behavior_definition_id'), table_name='behavior_logs')
    op.drop_index('ix_behavior_logs_user_date', table_name='behavior_logs')
    op.drop_index('ix_behavior_logs_definition_date', table_name='behavior_logs')
    op.drop_table('behavior_logs')

    op.drop_index(op.f('ix_behavior_definitions_user_id'), table_name='behavior_definitions')
    op.drop_index('ix_behavior_definitions_user_active', table_name='behavior_definitions')
    op.drop_index('ix_behavior_definitions_category', table_name='behavior_definitions')
    op.drop_table('behavior_definitions')
