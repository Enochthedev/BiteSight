"""Add admin tables and roles

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admin tables and roles."""

    # Create admin_users table
    op.create_table(
        'admin_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, default='admin'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for admin_users table
    op.create_index('ix_admin_users_email', 'admin_users', ['email'])
    op.create_index('ix_admin_users_role', 'admin_users', ['role'])
    op.create_index('ix_admin_users_is_active', 'admin_users', ['is_active'])

    # Create admin_permissions table
    op.create_table(
        'admin_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for admin_permissions table
    op.create_index('ix_admin_permissions_name', 'admin_permissions', ['name'])
    op.create_index('ix_admin_permissions_resource',
                    'admin_permissions', ['resource'])

    # Create admin_role_permissions table (many-to-many)
    op.create_table(
        'admin_role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('admin_permissions.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for admin_role_permissions table
    op.create_index('ix_admin_role_permissions_role',
                    'admin_role_permissions', ['role'])
    op.create_index('ix_admin_role_permissions_permission_id',
                    'admin_role_permissions', ['permission_id'])

    # Create unique constraint for role-permission combination
    op.create_index('ix_admin_role_permissions_unique', 'admin_role_permissions',
                    ['role', 'permission_id'], unique=True)

    # Create admin_sessions table for session management
    op.create_table(
        'admin_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('admin_users.id'), nullable=False),
        sa.Column('session_token', sa.String(
            255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )

    # Create indexes for admin_sessions table
    op.create_index('ix_admin_sessions_admin_user_id',
                    'admin_sessions', ['admin_user_id'])
    op.create_index('ix_admin_sessions_session_token',
                    'admin_sessions', ['session_token'])
    op.create_index('ix_admin_sessions_expires_at',
                    'admin_sessions', ['expires_at'])
    op.create_index('ix_admin_sessions_is_active',
                    'admin_sessions', ['is_active'])


def downgrade() -> None:
    """Drop admin tables."""

    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('admin_sessions')
    op.drop_table('admin_role_permissions')
    op.drop_table('admin_permissions')
    op.drop_table('admin_users')
