"""merge game and learning branches

Revision ID: fab52f0ee1f2
Revises: 20260121_add_two_dots, adaptive_homework_2026
Create Date: 2026-01-23 17:40:35.987718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fab52f0ee1f2'
down_revision: Union[str, None] = ('20260121_add_two_dots', 'adaptive_homework_2026')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
