"""People's secret calendar feed address (`people.feed_token`).

Nullable: a person has no address until they press Create feed address. The unique
index lets many people have none (SQLite treats NULLs as distinct).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("people", sa.Column("feed_token", sa.String(), nullable=True))
    op.create_index("uq_people_feed_token", "people", ["feed_token"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_people_feed_token", table_name="people")
    # A plain ALTER TABLE ... DROP COLUMN (SQLite 3.35+): a batch rebuild would drop and
    # recreate `people`, which bookings reference.
    op.drop_column("people", "feed_token")
