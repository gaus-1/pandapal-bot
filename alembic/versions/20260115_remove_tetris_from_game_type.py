"""remove tetris from game_type

Revision ID: 20260115_remove_tetris
Revises: db528ed1d582
Create Date: 2026-01-15 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260115_remove_tetris"
down_revision: Union[str, None] = "db528ed1d582"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем tetris из check-constraint'ов game_sessions и game_stats
    op.drop_constraint("ck_game_sessions_game_type", "game_sessions", type_="check")
    op.drop_constraint("ck_game_stats_game_type", "game_stats", type_="check")

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
    # Возвращаем tetris в constraints
    op.drop_constraint("ck_game_sessions_game_type", "game_sessions", type_="check")
    op.drop_constraint("ck_game_stats_game_type", "game_stats", type_="check")

    op.create_check_constraint(
        "ck_game_sessions_game_type",
        "game_sessions",
        "game_type IN ('tic_tac_toe', 'checkers', '2048', 'tetris')",
    )
    op.create_check_constraint(
        "ck_game_stats_game_type",
        "game_stats",
        "game_type IN ('tic_tac_toe', 'checkers', '2048', 'tetris')",
    )
