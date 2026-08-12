"""initial game schema

Revision ID: 0001_initial
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_scores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("player_score", sa.Integer, nullable=False),
        sa.Column("ai_score", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("game_scores")
