"""merge subscription and user branches

Revision ID: d4337e0b268f
Revises: 6e97d652b9a0, add_saved_payment_method_id
Create Date: 2026-01-09 15:58:32.598626

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4337e0b268f"
down_revision: Union[str, None] = ("6e97d652b9a0", "add_saved_payment_method_id")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
