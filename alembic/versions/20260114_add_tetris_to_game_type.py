"""add tetris to game_type

Revision ID: 20260114_add_tetris
Revises: bb9254f89058
Create Date: 2026-01-14 13:20:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260114_add_tetris"
down_revision: Union[str, None] = "bb9254f89058"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  # Добавляем поддержку tetris в check-constraint'ах game_sessions и game_stats
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


def downgrade() -> None:
  # Возвращаемся к предыдущему набору игр без tetris
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
