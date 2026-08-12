"""add tenant-scoped domain records

Revision ID: 0002_domain_records
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_domain_records"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domain_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="active"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_domain_records_tenant_entity", "domain_records", ["tenant_id", "entity_type"])


def downgrade() -> None:
    op.drop_index("ix_domain_records_tenant_entity", table_name="domain_records")
    op.drop_table("domain_records")
