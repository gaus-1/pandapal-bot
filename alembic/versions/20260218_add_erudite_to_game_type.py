"""add erudite to game_type

Revision ID: 20260218_erudite
Revises: 20260218_bamboo
Create Date: 2026-02-18

Добавляет erudite в check constraint для game_sessions и game_stats (игра Эрудит).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "20260218_erudite"
down_revision: Union[str, None] = "20260218_bamboo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    for table, ck_name in (
        ("game_sessions", "ck_game_sessions_game_type"),
        ("game_stats", "ck_game_stats_game_type"),
    ):
        result = conn.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = :t AND constraint_name = :ck
        """), {"t": table, "ck": ck_name})
        if result.fetchone():
            op.drop_constraint(ck_name, table, type_="check")
        op.create_check_constraint(
            ck_name,
            table,
            "game_type IN ('tic_tac_toe', 'checkers', '2048', 'two_dots', 'erudite')",
        )


def downgrade() -> None:
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
