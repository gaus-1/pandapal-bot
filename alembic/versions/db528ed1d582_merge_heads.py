"""merge_heads

Revision ID: db528ed1d582
Revises: a1b2c3d4e5f8, 1cd95f9f0125
Create Date: 2026-01-14 16:28:55.992706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db528ed1d582'
down_revision: Union[str, None] = ('a1b2c3d4e5f8', '1cd95f9f0125')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
