"""add two_dots to game_type

Revision ID: 20260121_add_two_dots
Revises: 20260115_remove_tetris
Create Date: 2026-01-21 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260121_add_two_dots"
down_revision: Union[str, None] = "20260115_remove_tetris"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поддержку two_dots в check-constraint'ах game_sessions и game_stats
    op.drop_constraint("ck_game_sessions_game_type", "game_sessions", type_="check")
    op.drop_constraint("ck_game_stats_game_type", "game_stats", type_="check")

    op.create_check_constraint(
        "ck_game_sessions_game_type",
        "game_sessions",
        "game_type IN ('tic_tac_toe', 'checkers', '2048', 'two_dots')",
    )
    op.create_check_constraint(
        "ck_game_stats_game_type",
        "game_stats",
        "game_type IN ('tic_tac_toe', 'checkers', '2048', 'two_dots')",
    )


def downgrade() -> None:
    # Удаляем two_dots из constraints
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
