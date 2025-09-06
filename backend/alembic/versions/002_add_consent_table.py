"""Add consent tracking table

Revision ID: 002_add_consent_table
Revises: 001_initial_schema
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_consent_table'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add consent_records table."""
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consent_type', sa.String(length=100), nullable=False),
        sa.Column('consent_given', sa.Boolean(), nullable=False),
        sa.Column('consent_date', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('consent_version', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index('ix_consent_records_student_id',
                    'consent_records', ['student_id'])
    op.create_index('ix_consent_records_consent_type',
                    'consent_records', ['consent_type'])
    op.create_index('ix_consent_records_consent_date',
                    'consent_records', ['consent_date'])

    # Create composite index for efficient consent lookups
    op.create_index(
        'ix_consent_records_student_type_date',
        'consent_records',
        ['student_id', 'consent_type', 'consent_date']
    )


def downgrade() -> None:
    """Remove consent_records table."""
    op.drop_index('ix_consent_records_student_type_date',
                  table_name='consent_records')
    op.drop_index('ix_consent_records_consent_date',
                  table_name='consent_records')
    op.drop_index('ix_consent_records_consent_type',
                  table_name='consent_records')
    op.drop_index('ix_consent_records_student_id',
                  table_name='consent_records')
    op.drop_table('consent_records')
