"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('practice_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('language', sa.String(), nullable=False),
    sa.Column('expected_sentence', sa.Text(), nullable=False),
    sa.Column('english_translation', sa.Text(), nullable=False),
    sa.Column('transcription', sa.Text(), nullable=True),
    sa.Column('accuracy_score', sa.Float(), nullable=True),
    sa.Column('is_correct', sa.String(), nullable=True),
    sa.Column('audio_file_path', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practice_sessions_id'), 'practice_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_practice_sessions_user_id'), 'practice_sessions', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_practice_sessions_user_id'), table_name='practice_sessions')
    op.drop_index(op.f('ix_practice_sessions_id'), table_name='practice_sessions')
    op.drop_table('practice_sessions')
