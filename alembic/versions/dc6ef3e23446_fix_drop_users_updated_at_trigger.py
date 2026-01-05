"""fix_drop_users_updated_at_trigger

Revision ID: dc6ef3e23446
Revises: f12d308e69f4
Create Date: 2026-01-05 17:20:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dc6ef3e23446"
down_revision: Union[str, None] = "f12d308e69f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем триггер, который пытается обновлять несуществующую колонку updated_at
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")


def downgrade() -> None:
    # Восстанавливаем триггер (если колонка updated_at будет восстановлена)
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS update_users_updated_at BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """
    )
