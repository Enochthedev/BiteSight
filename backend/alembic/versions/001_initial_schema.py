"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create students table
    op.create_table(
        'students',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('registration_date', sa.DateTime(
            timezone=True), server_default=sa.text('now()')),
        sa.Column('history_enabled', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create index on email for faster lookups
    op.create_index('ix_students_email', 'students', ['email'])

    # Create meals table
    op.create_table(
        'meals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('student_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('students.id'), nullable=False),
        sa.Column('image_path', sa.String(500), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('analysis_status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for meals table
    op.create_index('ix_meals_student_id', 'meals', ['student_id'])
    op.create_index('ix_meals_upload_date', 'meals', ['upload_date'])
    op.create_index('ix_meals_analysis_status', 'meals', ['analysis_status'])

    # Create detected_foods table
    op.create_table(
        'detected_foods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('meal_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('meals.id'), nullable=False),
        sa.Column('food_name', sa.String(255), nullable=False),
        sa.Column('confidence_score', sa.Numeric(3, 2)),
        sa.Column('food_class', sa.String(100), nullable=False),
        sa.Column('bounding_box', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for detected_foods table
    op.create_index('ix_detected_foods_meal_id', 'detected_foods', ['meal_id'])
    op.create_index('ix_detected_foods_food_class',
                    'detected_foods', ['food_class'])

    # Create feedback_records table
    op.create_table(
        'feedback_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('meal_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('meals.id'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('students.id'), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('feedback_type', sa.String(100)),
        sa.Column('recommendations', postgresql.JSON()),
        sa.Column('feedback_date', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for feedback_records table
    op.create_index('ix_feedback_records_meal_id',
                    'feedback_records', ['meal_id'])
    op.create_index('ix_feedback_records_student_id',
                    'feedback_records', ['student_id'])
    op.create_index('ix_feedback_records_feedback_date',
                    'feedback_records', ['feedback_date'])

    # Create nigerian_foods table
    op.create_table(
        'nigerian_foods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('food_name', sa.String(255), nullable=False),
        sa.Column('local_names', postgresql.JSON()),
        sa.Column('food_class', sa.String(100), nullable=False),
        sa.Column('nutritional_info', postgresql.JSON()),
        sa.Column('cultural_context', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for nigerian_foods table
    op.create_index('ix_nigerian_foods_food_name',
                    'nigerian_foods', ['food_name'])
    op.create_index('ix_nigerian_foods_food_class',
                    'nigerian_foods', ['food_class'])

    # Create nutrition_rules table
    op.create_table(
        'nutrition_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('condition_logic', postgresql.JSON()),
        sa.Column('feedback_template', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for nutrition_rules table
    op.create_index('ix_nutrition_rules_rule_name',
                    'nutrition_rules', ['rule_name'])
    op.create_index('ix_nutrition_rules_is_active',
                    'nutrition_rules', ['is_active'])
    op.create_index('ix_nutrition_rules_priority',
                    'nutrition_rules', ['priority'])

    # Create weekly_insights table
    op.create_table(
        'weekly_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('student_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('students.id'), nullable=False),
        sa.Column('week_start_date', sa.Date(), nullable=False),
        sa.Column('week_end_date', sa.Date(), nullable=False),
        sa.Column('nutrition_summary', postgresql.JSON()),
        sa.Column('recommendations', sa.Text()),
        sa.Column('generated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for weekly_insights table
    op.create_index('ix_weekly_insights_student_id',
                    'weekly_insights', ['student_id'])
    op.create_index('ix_weekly_insights_week_start_date',
                    'weekly_insights', ['week_start_date'])
    op.create_index('ix_weekly_insights_generated_at',
                    'weekly_insights', ['generated_at'])

    # Create composite index for unique weekly insights per student
    op.create_index('ix_weekly_insights_student_week', 'weekly_insights', [
                    'student_id', 'week_start_date'], unique=True)


def downgrade() -> None:
    """Drop all tables."""

    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('weekly_insights')
    op.drop_table('nutrition_rules')
    op.drop_table('nigerian_foods')
    op.drop_table('feedback_records')
    op.drop_table('detected_foods')
    op.drop_table('meals')
    op.drop_table('students')
