"""add_checkers_to_game_type

Revision ID: a1b2c3d4e5f7
Revises: dc6ef3e23446
Create Date: 2026-01-05 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "dc6ef3e23446"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем старый constraint
    op.drop_constraint("ck_game_sessions_game_type", "game_sessions", type_="check")
    op.drop_constraint("ck_game_stats_game_type", "game_stats", type_="check")

    # Создаем новый constraint с checkers вместо hangman
    op.create_check_constraint(
        "ck_game_sessions_game_type",
        "game_sessions",
        "game_type IN ('tic_tac_toe', 'checkers', '2048')",
    )
    op.create_check_constraint(
        "ck_game_stats_game_type",
        "game_stats",
        "game_type IN ('tic_tac_toe', 'checkers', '2048')",
    )


def downgrade() -> None:
    # Возвращаем старый constraint с hangman
    op.drop_constraint("ck_game_sessions_game_type", "game_sessions", type_="check")
    op.drop_constraint("ck_game_stats_game_type", "game_stats", type_="check")

    op.create_check_constraint(
        "ck_game_sessions_game_type",
        "game_sessions",
        "game_type IN ('tic_tac_toe', 'hangman', '2048')",
    )
    op.create_check_constraint(
        "ck_game_stats_game_type",
        "game_stats",
        "game_type IN ('tic_tac_toe', 'hangman', '2048')",
    )
