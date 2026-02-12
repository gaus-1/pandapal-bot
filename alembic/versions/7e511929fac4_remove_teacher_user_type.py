"""remove_teacher_user_type

Удаление типа пользователя 'teacher' из системы.
Теперь поддерживаются только 'child' и 'parent'.

Revision ID: 7e511929fac4
Revises: 0fb5d4bc5f51
Create Date: 2025-10-17 14:13:36.114736

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e511929fac4"
down_revision: Union[str, None] = "0fb5d4bc5f51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Удаляет поддержку user_type='teacher' из системы.

    1. Обновляет всех пользователей с типом 'teacher' на 'parent'
    2. Пересоздаёт constraint для поддержки только 'child' и 'parent'
    """
    # Шаг 1: Обновить всех учителей на родителей (если есть)
    op.execute("UPDATE users SET user_type = 'parent' WHERE user_type = 'teacher'")

    # Шаг 2: Удалить старый constraint (если есть — в initial schema его нет)
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_user_type")

    # Шаг 3: Создать новый constraint без 'teacher'
    op.create_check_constraint("ck_users_user_type", "users", "user_type IN ('child', 'parent')")


def downgrade() -> None:
    """
    Откат: возвращает поддержку 'teacher'.
    """
    # Удалить новый constraint
    op.drop_constraint("ck_users_user_type", "users", type_="check")

    # Создать старый constraint с 'teacher'
    op.create_check_constraint(
        "ck_users_user_type", "users", "user_type IN ('child', 'parent', 'teacher')"
    )
