"""Add conversation_logs table for AI coaching

Revision ID: cd6536fffee0
Revises: b72667ea0290
Create Date: 2025-12-16 21:16:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cd6536fffee0'
down_revision = 'b72667ea0290'
branch_labels = None
depends_on = None


def upgrade():
    # Create conversation_logs table
    op.create_table('conversation_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('conversation_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('messages', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('message_count', sa.Integer(), nullable=False),
    sa.Column('records_created', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('message_count >= 0', name='check_message_count_positive'),
    sa.CheckConstraint('records_created >= 0', name='check_records_created_positive'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_logs_conversation_date', 'conversation_logs', ['conversation_date'], unique=False)
    op.create_index('ix_conversation_logs_user_active', 'conversation_logs', ['user_id', 'is_active'], unique=False)
    op.create_index('ix_conversation_logs_user_date', 'conversation_logs', ['user_id', 'conversation_date'], unique=False)
    op.create_index(op.f('ix_conversation_logs_user_id'), 'conversation_logs', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_conversation_logs_user_id'), table_name='conversation_logs')
    op.drop_index('ix_conversation_logs_user_date', table_name='conversation_logs')
    op.drop_index('ix_conversation_logs_user_active', table_name='conversation_logs')
    op.drop_index('ix_conversation_logs_conversation_date', table_name='conversation_logs')
    op.drop_table('conversation_logs')
