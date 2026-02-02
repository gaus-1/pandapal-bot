"""merge heads before drop analytics

Revision ID: 20260201_merge
Revises: 42ccec998518, 20260201_rest
Create Date: 2026-02-01

Объединение веток: news (42ccec998518) и panda rest (20260201_rest).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260201_merge"
down_revision: Union[str, Sequence[str], None] = ("42ccec998518", "20260201_rest")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
