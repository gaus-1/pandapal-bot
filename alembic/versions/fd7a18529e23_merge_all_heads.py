"""merge_all_heads

Revision ID: fd7a18529e23
Revises: db528ed1d582, 51eec1cc4ab3
Create Date: 2026-01-14 16:57:47.830243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd7a18529e23'
down_revision: Union[str, None] = ('db528ed1d582', '51eec1cc4ab3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
