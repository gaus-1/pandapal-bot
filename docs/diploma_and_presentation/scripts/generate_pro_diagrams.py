"""
Генератор профессиональных диаграмм для дипломной работы PandaPal.
Создаёт 7 диаграмм: 5 основных + 2 ERD (концептуальная + физическая).
"""
import logging
import os

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

OUT_DIR = "docs/diploma_and_presentation/img"
os.makedirs(OUT_DIR, exist_ok=True)

# ===== COMMON STYLING =====
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.linewidth": 0,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "savefig.pad_inches": 0.3,
})

# Refined color palette
COLORS = {
    "primary":    "#2563EB",   # blue-600
    "primary_bg": "#EFF6FF",   # blue-50
    "secondary":  "#7C3AED",   # violet-600
    "sec_bg":     "#F5F3FF",   # violet-50
    "success":    "#059669",   # emerald-600
    "success_bg": "#ECFDF5",   # emerald-50
    "warning":    "#D97706",   # amber-600
    "warn_bg":    "#FFFBEB",   # amber-50
    "danger":     "#DC2626",   # red-600
    "danger_bg":  "#FEF2F2",   # red-50
    "cyan":       "#0891B2",   # cyan-600
    "cyan_bg":    "#ECFEFF",   # cyan-50
    "slate":      "#475569",   # slate-600
    "slate_bg":   "#F8FAFC",   # slate-50
    "yellow_bg":  "#FEF9C3",   # yellow-100
    "border":     "#CBD5E1",   # slate-300
    "text":       "#1E293B",   # slate-800
    "text_light": "#64748B",   # slate-500
    "white":      "#FFFFFF",
}


def _draw_box(ax, x, y, w, h, label, bg_color, border_color, font_size=10,
              font_weight="normal", sub_label=None, corner_radius=0.08, lw=1.5):
    """Draw a single rounded box with optional sub-label."""
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle=f"round,pad={corner_radius}",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=lw,
        zorder=2,
    )
    ax.add_patch(box)
    if sub_label:
        ax.text(x, y + 0.4, label, ha="center", va="center",
                fontsize=font_size, fontweight=font_weight, color=COLORS["text"], zorder=3)
        ax.text(x, y - 0.5, sub_label, ha="center", va="center",
                fontsize=font_size - 2, color=COLORS["text_light"], zorder=3)
    else:
        ax.text(x, y, label, ha="center", va="center",
                fontsize=font_size, fontweight=font_weight, color=COLORS["text"],
                zorder=3, wrap=True)


def _draw_arrow(ax, x1, y1, x2, y2, label="", color="#475569", style="-|>",
                lw=1.5, connectionstyle="arc3,rad=0"):
    """Draw an annotated arrow between two points."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            connectionstyle=connectionstyle,
            shrinkA=12, shrinkB=12,
        ),
        zorder=1,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.3, label, ha="center", va="bottom",
                fontsize=8, color=COLORS["text_light"],
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
                zorder=4)


# ============================================================================
# 1. ERD — CONCEPTUAL (high-level entity relationship)
# ============================================================================
def draw_erd_conceptual():
    """ER-диаграмма (концептуальная): сущности и связи без атрибутов."""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(-1, 27)
    ax.set_ylim(-1, 19)
    ax.axis("off")
    ax.set_title("ER-диаграмма базы данных PandaPal (концептуальная модель)",
                 fontsize=14, fontweight="bold", pad=18, color=COLORS["text"])

    bw, bh = 4.5, 1.6  # box width, height

    # Central entity: USERS
    cx, cy = 13, 16
    _draw_box(ax, cx, cy, 5, 2, "USERS", COLORS["yellow_bg"], COLORS["warning"],
              font_size=13, font_weight="bold", lw=2.5)

    # Tier-1 entities (directly connected to users)
    tier1 = [
        ("CHAT_HISTORY",       2,   12.5, COLORS["primary_bg"],  COLORS["primary"]),
        ("DAILY_REQUESTS",     8,   12.5, COLORS["primary_bg"],  COLORS["primary"]),
        ("LEARNING_SESSIONS",  14,  12.5, COLORS["success_bg"],  COLORS["success"]),
        ("PROBLEM_TOPICS",     20,  12.5, COLORS["success_bg"],  COLORS["success"]),
        ("HOMEWORK_SUBMIT.",   25.5, 12.5, COLORS["success_bg"],  COLORS["success"]),
    ]

    tier2 = [
        ("USER_PROGRESS",      2,   9, COLORS["sec_bg"],     COLORS["secondary"]),
        ("PANDA_PET",          8,   9, COLORS["warn_bg"],    COLORS["warning"]),
        ("GAME_SESSIONS",      14,  9, COLORS["cyan_bg"],    COLORS["cyan"]),
        ("GAME_STATS",         20,  9, COLORS["cyan_bg"],    COLORS["cyan"]),
        ("ANALYTICS_METRICS",  25.5, 9, COLORS["slate_bg"],   COLORS["slate"]),
    ]

    tier3 = [
        ("PAYMENTS",           5,   5.5, COLORS["danger_bg"],  COLORS["danger"]),
        ("SUBSCRIPTIONS",      13,  5.5, COLORS["danger_bg"],  COLORS["danger"]),
        ("REFERRAL_PAYOUTS",   21,  5.5, COLORS["sec_bg"],     COLORS["secondary"]),
    ]

    tier4 = [
        ("REFERRERS",          21,  2.5, COLORS["warn_bg"],    COLORS["warning"]),
    ]

    all_entities = tier1 + tier2 + tier3 + tier4
    for name, ex, ey, bg, border in all_entities:
        _draw_box(ax, ex, ey, bw, bh, name, bg, border, font_size=8.5, font_weight="bold")

    # Draw arrows from USERS to each entity (except REFERRERS)
    for name, ex, ey, _bg, _border in tier1 + tier2 + tier3:
        card = "1 : 1" if name == "PANDA_PET" else "1 : N"
        _draw_arrow(ax, cx, cy - 1, ex, ey + bh / 2, label=card,
                    color=COLORS["slate"])

    # REFERRERS -> REFERRAL_PAYOUTS
    _draw_arrow(ax, 21, 2.5 + bh / 2, 21, 5.5 - bh / 2, label="1 : N",
                color=COLORS["secondary"])

    # PAYMENTS -> SUBSCRIPTIONS
    _draw_arrow(ax, 5, 5.5, 13, 5.5, label="FK", color=COLORS["danger"],
                connectionstyle="arc3,rad=-0.15")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "1_erd.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# 2. ARCHITECTURE DIAGRAM
# ============================================================================
def draw_architecture():
    """Общая архитектура системы PandaPal."""
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(-1, 25)
    ax.set_ylim(-1, 17)
    ax.axis("off")
    ax.set_title("Общая архитектура системы PandaPal",
                 fontsize=14, fontweight="bold", pad=18, color=COLORS["text"])

    bw, bh = 5, 2

    # Clients layer
    clients = [
        ("Telegram Bot\n(aiogram 3)",  3,  14, COLORS["primary_bg"], COLORS["primary"]),
        ("Mini App\n(React + Vite)",   10, 14, COLORS["primary_bg"], COLORS["primary"]),
        ("Website\n(Cloudflare)",      17, 14, COLORS["primary_bg"], COLORS["primary"]),
    ]
    # Label
    ax.text(10, 16.2, "Клиенты", ha="center", fontsize=12, fontweight="bold",
            color=COLORS["text_light"])

    for name, x, y, bg, border in clients:
        _draw_box(ax, x, y, bw, bh, name, bg, border, font_size=10)

    # Server layer
    ax.add_patch(FancyBboxPatch(
        (0, 6.5), 24, 5, boxstyle="round,pad=0.3",
        facecolor="#F8FAFC", edgecolor=COLORS["border"], linewidth=1, linestyle="--", zorder=0))
    ax.text(12, 12, "Railway Cloud (Python Backend)", ha="center", fontsize=11, fontweight="bold",
            color=COLORS["text_light"])

    server_boxes = [
        ("API Gateway\n(FastAPI)",     4,  9.5, COLORS["warn_bg"],   COLORS["warning"]),
        ("Business Logic\n(Services)", 12, 9.5, COLORS["warn_bg"],   COLORS["warning"]),
        ("Bot Handlers\n(aiogram)",    20, 9.5, COLORS["warn_bg"],   COLORS["warning"]),
    ]
    for name, x, y, bg, border in server_boxes:
        _draw_box(ax, x, y, bw, bh, name, bg, border, font_size=10)

    # Data layer
    data_boxes = [
        ("PostgreSQL\n+ pgvector",     4,  4, COLORS["sec_bg"],   COLORS["secondary"]),
        ("Redis\n(Cache / Celery)",    12, 4, COLORS["danger_bg"],COLORS["danger"]),
    ]
    for name, x, y, bg, border in data_boxes:
        _draw_box(ax, x, y, bw, bh, name, bg, border, font_size=10)

    # External APIs
    ext_boxes = [
        ("Yandex Cloud\n(GPT, STT, Embeddings)", 20, 4, COLORS["cyan_bg"], COLORS["cyan"]),
        ("YooKassa\n(Платежи)",                   20, 1, COLORS["success_bg"], COLORS["success"]),
    ]
    for name, x, y, bg, border in ext_boxes:
        _draw_box(ax, x, y, bw, bh, name, bg, border, font_size=10)

    ax.text(12, 0.2, "Внешние сервисы", ha="center", fontsize=10, color=COLORS["text_light"])

    # Arrows: clients -> server
    for cx_val, _cy, _bg, _border in [(3, 14, None, None), (10, 14, None, None), (17, 14, None, None)]:
        _draw_arrow(ax, cx_val, 14 - bh / 2, 12, 9.5 + bh / 2,
                    color=COLORS["slate"], label="HTTPS")

    # Server internal
    _draw_arrow(ax, 4, 9.5 - 1, 12, 9.5 - 1, color=COLORS["warning"], label="REST")
    _draw_arrow(ax, 12, 9.5 - 1, 20, 9.5 - 1, color=COLORS["warning"])

    # Server -> Data
    _draw_arrow(ax, 4,  9.5 - bh / 2, 4,  4 + bh / 2, color=COLORS["secondary"], label="SQLAlchemy")
    _draw_arrow(ax, 12, 9.5 - bh / 2, 12, 4 + bh / 2, color=COLORS["danger"], label="redis-py")
    _draw_arrow(ax, 12, 9.5 - bh / 2, 20, 4 + bh / 2, color=COLORS["cyan"], label="REST API")
    _draw_arrow(ax, 12, 9.5 - bh / 2, 20, 1 + bh / 2, color=COLORS["success"], label="REST API")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "2_architecture.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# 3. SEQUENCE DIAGRAM
# ============================================================================
def draw_sequence():
    """Sequence diagram for message processing."""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(-1, 21)
    ax.set_ylim(-1, 21)
    ax.axis("off")
    ax.set_title("Диаграмма последовательности обработки сообщений",
                 fontsize=14, fontweight="bold", pad=18, color=COLORS["text"])

    # Participants
    parts = {
        "Пользователь": (2,  COLORS["primary_bg"],  COLORS["primary"]),
        "Сервер":       (7,  COLORS["warn_bg"],      COLORS["warning"]),
        "RAG / pgvector":(12, COLORS["sec_bg"],       COLORS["secondary"]),
        "YandexGPT":    (17, COLORS["danger_bg"],     COLORS["danger"]),
    }

    for name, (x, bg, border) in parts.items():
        _draw_box(ax, x, 19, 4, 1.5, name, bg, border, font_size=10, font_weight="bold")
        ax.plot([x, x], [1, 18.2], ls="--", color=COLORS["border"], lw=1, zorder=0)

    def seq_arrow(y, src, dst, label, dashed=False):
        x1 = parts[src][0]
        x2 = parts[dst][0]
        style = "-|>"
        ls = "--" if dashed else "-"
        ax.annotate(
            "", xy=(x2, y), xytext=(x1, y),
            arrowprops=dict(arrowstyle=style, color=COLORS["slate"], lw=1.5,
                            linestyle=ls),
            zorder=3,
        )
        mx = (x1 + x2) / 2
        ax.text(mx, y + 0.35, label, ha="center", va="bottom",
                fontsize=9, color=COLORS["text"],
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=COLORS["border"],
                          alpha=0.95, lw=0.5),
                zorder=4)

    seq_arrow(16, "Пользователь", "Сервер", "① Текстовый / голосовой запрос")
    seq_arrow(13.5, "Сервер", "RAG / pgvector", "② Векторный поиск контекста")
    seq_arrow(11, "RAG / pgvector", "Сервер", "③ Релевантные фрагменты", dashed=True)
    seq_arrow(8.5, "Сервер", "YandexGPT", "④ Промпт + контекст + история")
    seq_arrow(6, "YandexGPT", "Сервер", "⑤ SSE-стрим ответа", dashed=True)
    seq_arrow(3.5, "Сервер", "Пользователь", "⑥ Сообщение в Telegram", dashed=True)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "3_sequence.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# 4. DEPLOYMENT DIAGRAM
# ============================================================================
def draw_deployment():
    """Deployment diagram."""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(-1, 25)
    ax.set_ylim(-1, 19)
    ax.axis("off")
    ax.set_title("Схема развёртывания инфраструктуры PandaPal",
                 fontsize=14, fontweight="bold", pad=18, color=COLORS["text"])

    bw, bh = 5.5, 2

    # User device
    _draw_box(ax, 12, 17, 6, 1.8, "Устройство пользователя", COLORS["slate_bg"], COLORS["slate"],
              font_size=11, font_weight="bold")

    # Cloudflare
    _draw_box(ax, 12, 13.5, 6, 1.8, "Cloudflare (DNS / SSL / WAF)", COLORS["warn_bg"],
              COLORS["warning"], font_size=10)

    # Railway cloud -- big box
    ax.add_patch(FancyBboxPatch(
        (1, 2), 22, 8, boxstyle="round,pad=0.4",
        facecolor="#F0F9FF", edgecolor=COLORS["primary"], linewidth=2,
        linestyle="--", zorder=0))
    ax.text(12, 10.5, "Railway Cloud", ha="center", fontsize=13, fontweight="bold",
            color=COLORS["primary"])

    # Railway services
    _draw_box(ax, 5,  7.5, bw, bh, "Backend Container\n(Python 3.11 / FastAPI)", COLORS["warn_bg"],
              COLORS["warning"], font_size=9)
    _draw_box(ax, 12, 7.5, bw, bh, "PostgreSQL 16\n(+ pgvector)", COLORS["sec_bg"],
              COLORS["secondary"], font_size=9)
    _draw_box(ax, 19, 7.5, bw, bh, "Redis 7\n(Cache / Celery)", COLORS["danger_bg"],
              COLORS["danger"], font_size=9)

    _draw_box(ax, 5,  4, bw, bh, "Celery Worker\n(Фоновые задачи)", COLORS["success_bg"],
              COLORS["success"], font_size=9)
    _draw_box(ax, 12, 4, bw, bh, "Celery Beat\n(Расписание)", COLORS["success_bg"],
              COLORS["success"], font_size=9)

    # External
    _draw_box(ax, 19, 4, bw, bh, "Yandex Cloud\n(GPT, STT)", COLORS["cyan_bg"],
              COLORS["cyan"], font_size=9)

    # Arrows
    _draw_arrow(ax, 12, 17 - 0.9, 12, 13.5 + 0.9, color=COLORS["slate"], label="HTTPS")
    _draw_arrow(ax, 12, 13.5 - 0.9, 5, 7.5 + 1, color=COLORS["warning"], label="Webhook")
    _draw_arrow(ax, 5, 7.5, 12, 7.5, color=COLORS["secondary"], label="asyncpg")
    _draw_arrow(ax, 5, 7.5, 19, 7.5, color=COLORS["danger"], label="redis-py")
    _draw_arrow(ax, 5, 7.5 - 1, 5, 4 + 1, color=COLORS["success"], label="Celery")
    _draw_arrow(ax, 12, 7.5 - 1, 12, 4 + 1, color=COLORS["success"])
    _draw_arrow(ax, 5, 4, 19, 4, color=COLORS["cyan"], label="REST API",
                connectionstyle="arc3,rad=-0.1")

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "4_deployment.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# 5. USE CASE DIAGRAM
# ============================================================================
def draw_usecase():
    """Use-case diagram."""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(-1, 21)
    ax.set_ylim(-1, 19)
    ax.axis("off")
    ax.set_title("Диаграмма вариантов использования PandaPal",
                 fontsize=14, fontweight="bold", pad=18, color=COLORS["text"])

    # Actors
    def draw_actor(x, y, label, color):
        # Simple stick figure
        head = plt.Circle((x, y + 1.5), 0.4, fill=True, fc=color, ec=color, lw=2, zorder=3)
        ax.add_patch(head)
        ax.plot([x, x], [y + 1.1, y + 0.2], color=color, lw=2, zorder=3)  # body
        ax.plot([x - 0.5, x, x + 0.5], [y + 0.9, y + 0.7, y + 0.9], color=color, lw=2, zorder=3)  # arms
        ax.plot([x - 0.4, x, x + 0.4], [y - 0.3, y + 0.2, y - 0.3], color=color, lw=2, zorder=3)  # legs
        ax.text(x, y - 0.8, label, ha="center", fontsize=11, fontweight="bold", color=COLORS["text"])

    draw_actor(2, 11, "Школьник", COLORS["primary"])
    draw_actor(2, 3, "Родитель", COLORS["success"])

    # Use cases (ellipses in the system boundary)
    ax.add_patch(FancyBboxPatch(
        (5.5, 0.5), 14, 17, boxstyle="round,pad=0.5",
        facecolor=COLORS["slate_bg"], edgecolor=COLORS["border"],
        linewidth=1.5, linestyle="--", zorder=0))
    ax.text(12.5, 18, "Система PandaPal", ha="center", fontsize=12,
            fontweight="bold", color=COLORS["text_light"])

    use_cases = [
        ("Задать вопрос ИИ\n(помощь с учёбой)",       12.5, 16,  COLORS["primary_bg"], COLORS["primary"]),
        ("Отправить ДЗ\n(фото → OCR → проверка)",     12.5, 13.5, COLORS["primary_bg"], COLORS["primary"]),
        ("Развивающие игры\n(Шашки, Эрудит, 2048…)",   12.5, 11,  COLORS["cyan_bg"],    COLORS["cyan"]),
        ("Виртуальный питомец\n(Тамагочи-панда)",      12.5, 8.5, COLORS["warn_bg"],    COLORS["warning"]),
        ("Отслеживание прогресса\n(XP, уровни, рейтинг)", 12.5, 6, COLORS["success_bg"], COLORS["success"]),
        ("Premium-подписка\n(Stars / ЮKassa)",         12.5, 3.5, COLORS["danger_bg"],  COLORS["danger"]),
        ("Реферальная программа\n(кешбэк 20%)",        12.5, 1.2, COLORS["sec_bg"],     COLORS["secondary"]),
    ]

    for label, x, y, bg, border in use_cases:
        ellipse = mpatches.Ellipse((x, y), 7.5, 1.8, facecolor=bg, edgecolor=border,
                                    linewidth=1.5, zorder=2)
        ax.add_patch(ellipse)
        ax.text(x, y, label, ha="center", va="center", fontsize=9, color=COLORS["text"], zorder=3)

    # Lines from student to use cases
    for label, x, y, _bg, _border in use_cases[:5]:
        ax.plot([2.5, x - 3.5], [12, y], color=COLORS["border"], lw=1.2, zorder=1)

    # Lines from parent to use cases
    for label, x, y, _bg, _border in use_cases[5:]:
        ax.plot([2.5, x - 3.5], [4, y], color=COLORS["border"], lw=1.2, zorder=1)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "5_usecase.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# 6. ERD — PHYSICAL (with columns, for appendix)
# ============================================================================
def _draw_table_box(ax, x, y, name, columns, pk_col, fk_cols, bg, border, w=5.5):
    """Draw a database table as a box with header + columns list."""
    row_h = 0.45
    header_h = 0.65
    total_h = header_h + len(columns) * row_h + 0.2

    # Header
    header = FancyBboxPatch(
        (x - w / 2, y - header_h), w, header_h,
        boxstyle="round,pad=0.05",
        facecolor=border, edgecolor=border, linewidth=1.5, zorder=2,
    )
    ax.add_patch(header)
    ax.text(x, y - header_h / 2, name, ha="center", va="center",
            fontsize=8.5, fontweight="bold", color="white", zorder=3)

    # Body
    body = FancyBboxPatch(
        (x - w / 2, y - total_h), w, total_h - header_h,
        boxstyle="round,pad=0.05",
        facecolor=bg, edgecolor=border, linewidth=1, zorder=2,
    )
    ax.add_patch(body)

    for i, col in enumerate(columns):
        cy = y - header_h - 0.15 - (i + 0.5) * row_h
        col_color = COLORS["text"]
        display_col = col
        if col == pk_col:
            col_color = COLORS["warning"]
        elif col in fk_cols:
            col_color = COLORS["primary"]
        ax.text(x - w / 2 + 0.2, cy, display_col, ha="left", va="center",
                fontsize=7, color=col_color, zorder=3, family="monospace")

    return total_h


def draw_erd_physical():
    """Physical ERD with column names — for Appendix А."""
    fig, ax = plt.subplots(figsize=(22, 16))
    ax.set_xlim(-1, 43)
    ax.set_ylim(-2, 24)
    ax.axis("off")
    ax.set_title("Физическая ER-диаграмма базы данных PandaPal (15 таблиц)",
                 fontsize=15, fontweight="bold", pad=20, color=COLORS["text"])

    # Define all tables: (name, x, y, columns, pk_col, fk_cols, bg, border)
    tables_data = [
        ("users", 20, 22, [
            "id (PK)", "telegram_id (UQ)", "username", "first_name", "last_name",
            "age", "grade", "user_type", "parent_telegram_id (FK→users)",
            "referrer_telegram_id", "premium_until", "created_at",
            "is_active", "message_count", "gender",
        ], "id (PK)", ["parent_telegram_id (FK→users)"],
         COLORS["yellow_bg"], COLORS["warning"]),

        ("chat_history", 3, 15.5, [
            "id (PK)", "user_telegram_id (FK→users)", "message_text",
            "message_type", "timestamp", "image_url", "panda_reaction",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["primary_bg"], COLORS["primary"]),

        ("daily_request_counts", 10.5, 15.5, [
            "id (PK)", "user_telegram_id (FK→users)",
            "date", "request_count", "last_request_at",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["primary_bg"], COLORS["primary"]),

        ("learning_sessions", 17, 15.5, [
            "id (PK)", "user_telegram_id (FK→users)",
            "subject", "topic", "difficulty_level",
            "questions_answered", "correct_answers",
            "session_start", "session_end", "is_completed",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["success_bg"], COLORS["success"]),

        ("problem_topics", 24, 15.5, [
            "id (PK)", "user_telegram_id (FK→users)",
            "subject", "topic", "error_count",
            "total_attempts", "last_error_at",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["success_bg"], COLORS["success"]),

        ("homework_submissions", 31, 15.5, [
            "id (PK)", "user_telegram_id (FK→users)",
            "photo_file_id", "subject", "topic",
            "original_text", "ai_feedback",
            "has_errors", "score", "submitted_at",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["success_bg"], COLORS["success"]),

        ("user_progress", 38, 15.5, [
            "id (PK)", "user_telegram_id (FK→users)",
            "subject", "level", "difficulty_level",
            "mastery_score", "points", "achievements",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["sec_bg"], COLORS["secondary"]),

        ("panda_pet", 3, 8, [
            "id (PK)", "user_telegram_id (FK→users, UQ)",
            "hunger", "mood", "energy",
            "last_fed_at", "last_played_at",
            "consecutive_visit_days", "achievements",
        ], "id (PK)", ["user_telegram_id (FK→users, UQ)"],
         COLORS["warn_bg"], COLORS["warning"]),

        ("game_sessions", 10.5, 8, [
            "id (PK)", "user_telegram_id (FK→users)",
            "game_type", "game_state", "result",
            "score", "started_at", "duration_seconds",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["cyan_bg"], COLORS["cyan"]),

        ("game_stats", 17, 8, [
            "id (PK)", "user_telegram_id (FK→users)",
            "game_type", "total_games", "wins",
            "losses", "draws", "best_score",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["cyan_bg"], COLORS["cyan"]),

        ("analytics_metrics", 24, 8, [
            "id (PK)", "metric_name", "metric_value",
            "metric_type", "tags (JSON)", "timestamp",
            "period", "user_telegram_id",
        ], "id (PK)", [],
         COLORS["slate_bg"], COLORS["slate"]),

        ("payments", 31, 8, [
            "id (PK)", "payment_id (UQ)",
            "user_telegram_id (FK→users)",
            "subscription_id (FK→subscriptions)",
            "payment_method", "plan_id",
            "amount", "currency", "status",
            "paid_at",
        ], "id (PK)", ["user_telegram_id (FK→users)", "subscription_id (FK→subscriptions)"],
         COLORS["danger_bg"], COLORS["danger"]),

        ("subscriptions", 38, 8, [
            "id (PK)", "user_telegram_id (FK→users)",
            "plan_id", "starts_at", "expires_at",
            "is_active", "payment_method",
            "auto_renew", "saved_payment_method_id",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["danger_bg"], COLORS["danger"]),

        ("referrers", 31, 1.5, [
            "id (PK)", "telegram_id (UQ)", "comment", "created_at",
        ], "id (PK)", [],
         COLORS["warn_bg"], COLORS["warning"]),

        ("referral_payouts", 38, 1.5, [
            "id (PK)", "referrer_telegram_id",
            "user_telegram_id (FK→users)",
            "payment_id (UQ)", "amount_rub", "paid_at",
        ], "id (PK)", ["user_telegram_id (FK→users)"],
         COLORS["sec_bg"], COLORS["secondary"]),
    ]

    table_positions = {}
    for name, x, y, cols, pk, fks, bg, border in tables_data:
        h = _draw_table_box(ax, x, y, name, cols, pk, fks, bg, border)
        table_positions[name] = (x, y, h)

    # Draw FK lines from child tables to users (top center)
    users_x, users_y, users_h = table_positions["users"]
    users_bottom = users_y - users_h

    for name in [
        "chat_history", "daily_request_counts", "learning_sessions",
        "problem_topics", "homework_submissions", "user_progress",
        "panda_pet", "game_sessions", "game_stats",
        "payments", "subscriptions", "referral_payouts",
    ]:
        tx, ty, th = table_positions[name]
        ax.plot([tx, tx, users_x], [ty, ty + 0.3, users_bottom - 0.1],
                color=COLORS["border"], lw=0.8, ls="--", zorder=0)

    # payments -> subscriptions FK
    px, py, ph = table_positions["payments"]
    sx, sy, sh = table_positions["subscriptions"]
    ax.annotate("", xy=(sx - 2.75, sy), xytext=(px + 2.75, py),
                arrowprops=dict(arrowstyle="-|>", color=COLORS["danger"], lw=1.2),
                zorder=1)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "6_erd_physical.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# 7. ERD — Relational Schema (simplified for appendix Б)
# ============================================================================
def draw_erd_relational():
    """Relational schema in notation «таблица (поля)» for Appendix Б."""
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(-1, 31)
    ax.set_ylim(-1, 21)
    ax.axis("off")
    ax.set_title("Реляционная схема базы данных PandaPal",
                 fontsize=15, fontweight="bold", pad=20, color=COLORS["text"])

    # Simple notation: each table as a colored card with PK underlined
    tables = [
        ("users", 15, 19, ["id", "telegram_id", "username", "first_name", "age", "grade",
                            "user_type", "premium_until", "is_active", "created_at"],
         COLORS["yellow_bg"], COLORS["warning"]),

        ("chat_history", 3, 14, ["id", "user_telegram_id", "message_text", "message_type", "timestamp"],
         COLORS["primary_bg"], COLORS["primary"]),

        ("daily_request_counts", 10, 14, ["id", "user_telegram_id", "date", "request_count"],
         COLORS["primary_bg"], COLORS["primary"]),

        ("learning_sessions", 17, 14, ["id", "user_telegram_id", "subject", "topic", "session_start"],
         COLORS["success_bg"], COLORS["success"]),

        ("problem_topics", 24, 14, ["id", "user_telegram_id", "subject", "topic", "error_count"],
         COLORS["success_bg"], COLORS["success"]),

        ("homework_submissions", 3, 9.5, ["id", "user_telegram_id", "subject", "ai_feedback", "score"],
         COLORS["success_bg"], COLORS["success"]),

        ("user_progress", 10, 9.5, ["id", "user_telegram_id", "subject", "level", "points"],
         COLORS["sec_bg"], COLORS["secondary"]),

        ("panda_pet", 17, 9.5, ["id", "user_telegram_id", "hunger", "mood", "energy"],
         COLORS["warn_bg"], COLORS["warning"]),

        ("game_sessions", 24, 9.5, ["id", "user_telegram_id", "game_type", "result", "score"],
         COLORS["cyan_bg"], COLORS["cyan"]),

        ("game_stats", 3, 5, ["id", "user_telegram_id", "game_type", "wins", "losses", "best_score"],
         COLORS["cyan_bg"], COLORS["cyan"]),

        ("analytics_metrics", 10, 5, ["id", "metric_name", "metric_value", "timestamp", "period"],
         COLORS["slate_bg"], COLORS["slate"]),

        ("payments", 17, 5, ["id", "payment_id", "user_telegram_id", "subscription_id", "amount", "status"],
         COLORS["danger_bg"], COLORS["danger"]),

        ("subscriptions", 24, 5, ["id", "user_telegram_id", "plan_id", "expires_at", "is_active"],
         COLORS["danger_bg"], COLORS["danger"]),

        ("referrers", 10, 1, ["id", "telegram_id", "comment", "created_at"],
         COLORS["warn_bg"], COLORS["warning"]),

        ("referral_payouts", 17, 1, ["id", "referrer_telegram_id", "user_telegram_id", "amount_rub"],
         COLORS["sec_bg"], COLORS["secondary"]),
    ]

    for name, x, y, cols, bg, border in tables:
        col_str = ", ".join(cols)
        display = f"{name}\n({col_str})"
        # Compute needed width
        max_line = max(len(name), len(col_str)) * 0.14 + 0.5
        w = min(max_line, 6.5)
        h = 1.8

        box = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.1",
            facecolor=bg, edgecolor=border, linewidth=1.5, zorder=2,
        )
        ax.add_patch(box)

        # Table name bold, columns small
        ax.text(x, y + 0.3, name, ha="center", va="center",
                fontsize=9, fontweight="bold", color=COLORS["text"], zorder=3)
        ax.text(x, y - 0.4, f"({col_str})", ha="center", va="center",
                fontsize=6.5, color=COLORS["text_light"], zorder=3,
                wrap=True)

        # FK arrows to users
        if name != "users" and name != "referrers" and name != "analytics_metrics":
            ax.plot([x, 15], [y + h / 2, 19 - 0.9],
                    color=COLORS["border"], lw=0.7, ls=":", zorder=0)

    # referrers -> referral_payouts
    ax.annotate("", xy=(17 - 3, 1), xytext=(10 + 3, 1),
                arrowprops=dict(arrowstyle="-|>", color=COLORS["warning"], lw=1.2),
                zorder=1)
    ax.text(13.5, 1.4, "1:N", ha="center", fontsize=8, color=COLORS["warning"])

    # payments -> subscriptions
    ax.annotate("", xy=(24 - 3, 5), xytext=(17 + 3, 5),
                arrowprops=dict(arrowstyle="-|>", color=COLORS["danger"], lw=1.2),
                zorder=1)
    ax.text(20.5, 5.4, "FK", ha="center", fontsize=8, color=COLORS["danger"])

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "7_erd_relational.png")
    plt.savefig(path)
    plt.close()
    logger.info("Saved %s", path)


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Генерация профессиональных диаграмм для дипломной работы...")

    draw_erd_conceptual()
    logger.info("✅ 1/7  ERD (концептуальная)")

    draw_architecture()
    logger.info("✅ 2/7  Архитектура")

    draw_sequence()
    logger.info("✅ 3/7  Sequence diagram")

    draw_deployment()
    logger.info("✅ 4/7  Deployment diagram")

    draw_usecase()
    logger.info("✅ 5/7  Use Case diagram")

    draw_erd_physical()
    logger.info("✅ 6/7  ERD (физическая)")

    draw_erd_relational()
    logger.info("✅ 7/7  Реляционная схема")

    logger.info("\n🎉 Все 7 диаграмм сохранены в %s", OUT_DIR)
