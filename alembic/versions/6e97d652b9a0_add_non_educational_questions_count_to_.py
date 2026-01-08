"""add_non_educational_questions_count_to_users

Revision ID: 6e97d652b9a0
Revises: 50775761d394
Create Date: 2026-01-08 20:02:40.011037

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e97d652b9a0"
down_revision: Union[str, None] = "50775761d394"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле для отслеживания количества последовательных непредметных вопросов
    op.add_column(
        "users",
        sa.Column(
            "non_educational_questions_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    # Удаляем добавленное поле
    op.drop_column("users", "non_educational_questions_count")
