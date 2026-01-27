"""add_news_table

Создает таблицу news для хранения новостей детского новостного бота.

Revision ID: 76c9942db20e
Revises: fab52f0ee1f2
Create Date: 2026-01-27 16:56:59.851336

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "76c9942db20e"
down_revision: Union[str, None] = "fab52f0ee1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание таблицы news."""
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("grade_min", sa.Integer(), nullable=True),
        sa.Column("grade_max", sa.Integer(), nullable=True),
        sa.Column("published_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_moderated",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Индексы для быстрого поиска
    op.create_index("idx_news_title", "news", ["title"])
    op.create_index("idx_news_source", "news", ["source"])
    op.create_index("idx_news_category", "news", ["category"])
    op.create_index("idx_news_age_min", "news", ["age_min"])
    op.create_index("idx_news_age_max", "news", ["age_max"])
    op.create_index("idx_news_grade_min", "news", ["grade_min"])
    op.create_index("idx_news_grade_max", "news", ["grade_max"])
    op.create_index("idx_news_published_date", "news", ["published_date"])
    op.create_index("idx_news_created_at", "news", ["created_at"])
    op.create_index("idx_news_is_active", "news", ["is_active"])

    # Составные индексы для оптимизации запросов
    op.create_index("idx_news_category_active", "news", ["category", "is_active"])
    op.create_index("idx_news_age_range", "news", ["age_min", "age_max"])
    op.create_index("idx_news_grade_range", "news", ["grade_min", "grade_max"])

    # Constraints для валидации данных
    op.create_check_constraint(
        "ck_news_category",
        "news",
        "category IN ('игры', 'мода', 'образование', 'еда', 'спорт', 'животные', 'природа', 'факты', 'события', 'приколы')",
    )
    op.create_check_constraint(
        "ck_news_age_min",
        "news",
        "age_min IS NULL OR (age_min >= 6 AND age_min <= 15)",
    )
    op.create_check_constraint(
        "ck_news_age_max",
        "news",
        "age_max IS NULL OR (age_max >= 6 AND age_max <= 15)",
    )
    op.create_check_constraint(
        "ck_news_grade_min",
        "news",
        "grade_min IS NULL OR (grade_min >= 1 AND grade_min <= 9)",
    )
    op.create_check_constraint(
        "ck_news_grade_max",
        "news",
        "grade_max IS NULL OR (grade_max >= 1 AND grade_max <= 9)",
    )


def downgrade() -> None:
    """Откат изменений."""
    # Удаляем constraints
    op.drop_constraint("ck_news_grade_max", "news", type_="check")
    op.drop_constraint("ck_news_grade_min", "news", type_="check")
    op.drop_constraint("ck_news_age_max", "news", type_="check")
    op.drop_constraint("ck_news_age_min", "news", type_="check")
    op.drop_constraint("ck_news_category", "news", type_="check")

    # Удаляем индексы
    op.drop_index("idx_news_grade_range", table_name="news")
    op.drop_index("idx_news_age_range", table_name="news")
    op.drop_index("idx_news_category_active", table_name="news")
    op.drop_index("idx_news_is_active", table_name="news")
    op.drop_index("idx_news_created_at", table_name="news")
    op.drop_index("idx_news_published_date", table_name="news")
    op.drop_index("idx_news_grade_max", table_name="news")
    op.drop_index("idx_news_grade_min", table_name="news")
    op.drop_index("idx_news_age_max", table_name="news")
    op.drop_index("idx_news_age_min", table_name="news")
    op.drop_index("idx_news_category", table_name="news")
    op.drop_index("idx_news_source", table_name="news")
    op.drop_index("idx_news_title", table_name="news")

    # Удаляем таблицу
    op.drop_table("news")
