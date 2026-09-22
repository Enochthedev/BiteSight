"""Add image metadata table

The image_metadata table was used by ImageMetadataService but never had a
migration (it only existed via Base.metadata.create_all).

Revision ID: 004_add_image_metadata
Revises: 003_add_admin_tables
Create Date: 2026-09-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "004_add_image_metadata"
down_revision = "003_add_admin_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "image_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("format", sa.String(length=20), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("raw_image_path", sa.String(length=500), nullable=True),
        sa.Column("processed_image_path", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_path", sa.String(length=500), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("quality_issues", sa.JSON(), nullable=True),
        sa.Column("quality_warnings", sa.JSON(), nullable=True),
        sa.Column("exif_data", sa.JSON(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column(
            "upload_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("processed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["meal_id"],
            ["meals.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_image_metadata_file_hash"),
        "image_metadata",
        ["file_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_image_metadata_meal_id"), "image_metadata", ["meal_id"], unique=True
    )
    op.create_index(
        op.f("ix_image_metadata_student_id"),
        "image_metadata",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_image_metadata_upload_date"),
        "image_metadata",
        ["upload_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_image_metadata_upload_date"), table_name="image_metadata")
    op.drop_index(op.f("ix_image_metadata_student_id"), table_name="image_metadata")
    op.drop_index(op.f("ix_image_metadata_meal_id"), table_name="image_metadata")
    op.drop_index(op.f("ix_image_metadata_file_hash"), table_name="image_metadata")
    op.drop_table("image_metadata")
    # ### end Alembic commands ###
