import logging
import os
import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

OUT_DIR = "docs/diploma_and_presentation/img"
os.makedirs(OUT_DIR, exist_ok=True)

# HUGE fonts to be readable in Word
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 14,
    "axes.linewidth": 0,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "savefig.pad_inches": 0.3,
})

COLORS = {
    "primary":    "#2563EB",
    "primary_bg": "#EFF6FF",
    "secondary":  "#7C3AED",
    "sec_bg":     "#F5F3FF",
    "success":    "#059669",
    "success_bg": "#ECFDF5",
    "warning":    "#D97706",
    "warn_bg":    "#FFFBEB",
    "danger":     "#DC2626",
    "danger_bg":  "#FEF2F2",
    "cyan":       "#0891B2",
    "cyan_bg":    "#ECFEFF",
    "slate":      "#475569",
    "slate_bg":   "#F8FAFC",
    "yellow_bg":  "#FEF9C3",
    "border":     "#CBD5E1",
    "text":       "#1E293B",
    "text_light": "#64748B",
    "white":      "#FFFFFF",
}

def _draw_box(ax, x, y, w, h, label, bg, border, font_size=12, font_weight="normal"):
    box = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.1", facecolor=bg, edgecolor=border, linewidth=2, zorder=2)
    ax.add_patch(box)
    ax.text(x, y, label, ha="center", va="center", fontsize=font_size, fontweight=font_weight, color=COLORS["text"], zorder=3, wrap=True)

def _draw_arrow(ax, x1, y1, x2, y2, label="", color="#475569", lw=2, rad=0, ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, connectionstyle=f"arc3,rad={rad}", ls=ls), zorder=1)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.5, label, ha="center", va="bottom", fontsize=10, color=COLORS["text"], bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9), zorder=4)

def _draw_ortho(ax, x1, y1, x2, y2, color, lw=2, ls="-", dir="v"):
    if dir == "v":
        ymid = (y1 + y2) / 2
        ax.plot([x1, x1, x2, x2], [y1, ymid, ymid, y2], color=color, lw=lw, ls=ls, zorder=0)
        ax.annotate("", xy=(x2, y2), xytext=(x2, ymid), arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls), zorder=1)
    else:
        xmid = (x1 + x2) / 2
        ax.plot([x1, xmid, xmid, x2], [y1, y1, y2, y2], color=color, lw=lw, ls=ls, zorder=0)
        ax.annotate("", xy=(x2, y2), xytext=(xmid, y2), arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls), zorder=1)

def draw_erd_conceptual():
    fig, ax = plt.subplots(figsize=(20, 16))
    ax.set_xlim(-1, 31); ax.set_ylim(0, 22); ax.axis("off")
    bw, bh = 5.5, 2.5
    cx, cy = 15, 11
    _draw_box(ax, cx, cy, bw, bh, "USERS\n(Пользователи)", COLORS["yellow_bg"], COLORS["warning"], 14, "bold")
    items = [
        ("CHAT_HISTORY",       7,   19, COLORS["primary_bg"],  COLORS["primary"]),
        ("DAILY_REQUESTS",     15,  19, COLORS["primary_bg"],  COLORS["primary"]),
        ("LEARNING_SESSIONS",  23,  19, COLORS["success_bg"],  COLORS["success"]),
        ("PROBLEM_TOPICS",     4,   14, COLORS["success_bg"],  COLORS["success"]),
        ("HOMEWORK_SUBMIT.",   26,  14, COLORS["success_bg"],  COLORS["success"]),
        ("USER_PROGRESS",      4,   8,  COLORS["sec_bg"],     COLORS["secondary"]),
        ("PANDA_PET",          26,  8,  COLORS["warn_bg"],    COLORS["warning"]),
        ("GAME_SESSIONS",      7,   3,  COLORS["cyan_bg"],    COLORS["cyan"]),
        ("GAME_STATS",         15,  3,  COLORS["cyan_bg"],    COLORS["cyan"]),
        ("SUBSCRIPTIONS",      23,  3,  COLORS["danger_bg"],  COLORS["danger"]),
        ("PAYMENTS",           23,  8,  COLORS["danger_bg"],  COLORS["danger"]),
        ("REFERRAL_PAYOUTS",   15,  14, COLORS["sec_bg"],     COLORS["secondary"]),
    ]
    for n, ex, ey, bg, border in items:
        _draw_box(ax, ex, ey, bw, bh, n, bg, border, 12, "bold")
        _draw_arrow(ax, cx, cy, ex, ey, label="1:N" if n!="PANDA_PET" else "1:1")
    _draw_box(ax, 3, 3, bw, bh, "ANALYTICS_METRICS", COLORS["slate_bg"], COLORS["slate"], 12, "bold")
    _draw_box(ax, 28, 19, bw, bh, "REFERRERS", COLORS["warn_bg"], COLORS["warning"], 12, "bold")
    _draw_arrow(ax, 28, 19, 15, 14, label="1:N", color=COLORS["warning"], rad=-0.1)
    _draw_arrow(ax, 23, 8 - bh/2, 23, 3 + bh/2, label="FK", color=COLORS["danger"])
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "1_erd.png")); plt.close()

def draw_architecture():
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 24); ax.set_ylim(0, 18); ax.axis("off")
    bw, bh = 5.5, 2.5
    for n, x, y, bg, bd in [("Telegram Bot\n(aiogram)", 4, 15, COLORS["primary_bg"], COLORS["primary"]),
                            ("Mini App\n(React)", 12, 15, COLORS["primary_bg"], COLORS["primary"]),
                            ("Website\n(Cloudflare)", 20, 15, COLORS["primary_bg"], COLORS["primary"])]:
        _draw_box(ax, x, y, bw, bh, n, bg, bd, 13, "bold")
    ax.add_patch(FancyBboxPatch((1, 8.5), 22, 4.5, boxstyle="round,pad=0.3", facecolor=COLORS["slate_bg"], edgecolor=COLORS["border"], linewidth=2, linestyle="--", zorder=0))
    for n, x, y, bg, bd in [("API Gateway\n(FastAPI)", 4, 10.5, COLORS["warn_bg"], COLORS["warning"]),
                            ("Business Logic", 12, 10.5, COLORS["warn_bg"], COLORS["warning"]),
                            ("Bot Handlers\n(aiogram)", 20, 10.5, COLORS["warn_bg"], COLORS["warning"])]:
        _draw_box(ax, x, y, bw, bh, n, bg, bd, 13, "bold")
        _draw_arrow(ax, x, 15 - bh/2, 12, 10.5 + bh/2, color=COLORS["slate"], label="HTTPS")
    for n, x, y, bg, bd in [("PostgreSQL 16", 4, 5, COLORS["sec_bg"], COLORS["secondary"]), ("Redis 7", 12, 5, COLORS["danger_bg"], COLORS["danger"])]:
        _draw_box(ax, x, y, bw, bh, n, bg, bd, 13, "bold")
    for n, x, y, bg, bd in [("Yandex Cloud", 20, 5, COLORS["cyan_bg"], COLORS["cyan"]), ("YooKassa", 20, 2, COLORS["success_bg"], COLORS["success"])]:
        _draw_box(ax, x, y, bw, bh, n, bg, bd, 13, "bold")
    _draw_arrow(ax, 4, 10.5, 12, 10.5, color=COLORS["warning"], label="REST")
    _draw_arrow(ax, 12, 10.5, 20, 10.5, color=COLORS["warning"])
    _draw_arrow(ax, 4, 10.5-bh/2, 4, 5+bh/2, color=COLORS["secondary"])
    _draw_arrow(ax, 12, 10.5-bh/2, 12, 5+bh/2, color=COLORS["danger"])
    _draw_arrow(ax, 12, 10.5-bh/2, 20, 5+bh/2, color=COLORS["cyan"])
    _draw_arrow(ax, 12, 10.5-bh/2, 20, 2+bh/2, color=COLORS["success"])
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "2_architecture.png")); plt.close()

def draw_sequence():
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(-1, 21); ax.set_ylim(0, 21); ax.axis("off")
    parts = {"Пользователь": 2, "Сервер": 7.5, "RAG": 13, "YandexGPT": 18.5}
    for n, x in parts.items():
        _draw_box(ax, x, 19, 4.5, 1.5, n, COLORS["primary_bg"], COLORS["primary"], 12, "bold")
        ax.plot([x, x], [1, 18.2], ls="--", color=COLORS["border"], lw=2, zorder=0)
    def seq_arrow(y, src, dst, label, dashed=False):
        x1, x2 = parts[src], parts[dst]
        ls = "--" if dashed else "-"
        ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="-|>", color=COLORS["slate"], lw=2, linestyle=ls), zorder=3)
        ax.text((x1+x2)/2, y+0.4, label, ha="center", va="bottom", fontsize=11, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9), zorder=4)
    seq_arrow(16, "Пользователь", "Сервер", "1. Запрос"); seq_arrow(13.5, "Сервер", "RAG", "2. Векторный поиск")
    seq_arrow(11, "RAG", "Сервер", "3. Вернуть фрагменты", True); seq_arrow(8.5, "Сервер", "YandexGPT", "4. Промпт + контекст")
    seq_arrow(6, "YandexGPT", "Сервер", "5. SSE-стрим", True); seq_arrow(3.5, "Сервер", "Пользователь", "6. Ответ", True)
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "3_sequence.png")); plt.close()

def draw_deployment():
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(-1, 25); ax.set_ylim(-1, 19); ax.axis("off")
    bw, bh = 6.5, 2.5
    _draw_box(ax, 12, 17, 7, 2, "Устройство пользователя", COLORS["slate_bg"], COLORS["slate"], 14, "bold")
    _draw_box(ax, 12, 13.5, 7, 2, "Cloudflare (DNS/WAF)", COLORS["warn_bg"], COLORS["warning"], 13, "bold")
    ax.add_patch(FancyBboxPatch((1, 2.5), 22, 8, boxstyle="round,pad=0.4", facecolor=COLORS["primary_bg"], edgecolor=COLORS["primary"], linewidth=2, linestyle="--", zorder=0))
    _draw_box(ax, 5,  8, bw, bh, "Backend\n(FastAPI)", COLORS["warn_bg"], COLORS["warning"], 12, "bold")
    _draw_box(ax, 12, 8, bw, bh, "PostgreSQL 16\n(pgvector)", COLORS["sec_bg"], COLORS["secondary"], 12, "bold")
    _draw_box(ax, 19, 8, bw, bh, "Redis 7\n(Cache/Celery)", COLORS["danger_bg"], COLORS["danger"], 12, "bold")
    _draw_box(ax, 5,  4, bw, bh, "Celery Worker", COLORS["success_bg"], COLORS["success"], 12, "bold")
    _draw_box(ax, 12, 4, bw, bh, "Celery Beat", COLORS["success_bg"], COLORS["success"], 12, "bold")
    _draw_box(ax, 19, 4, bw, bh, "Yandex Cloud", COLORS["cyan_bg"], COLORS["cyan"], 12, "bold")
    _draw_arrow(ax, 12, 16.1, 12, 14.4, color=COLORS["slate"]); _draw_arrow(ax, 12, 12.6, 5, 9, color=COLORS["warning"])
    _draw_arrow(ax, 5, 8, 12, 8, color=COLORS["secondary"]); _draw_arrow(ax, 5, 8, 19, 8, rad=-0.25, color=COLORS["danger"])
    _draw_arrow(ax, 5, 6.75, 5, 5.25, color=COLORS["success"]); _draw_arrow(ax, 12, 6.75, 12, 5.25, color=COLORS["success"])
    _draw_arrow(ax, 5, 4, 19, 4, rad=-0.1, color=COLORS["cyan"])
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "4_deployment.png")); plt.close()

def draw_usecase():
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(-1, 21); ax.set_ylim(0, 19); ax.axis("off")
    ax.add_patch(FancyBboxPatch((5.5, 0.5), 14, 18, boxstyle="round,pad=0.5", facecolor=COLORS["slate_bg"], edgecolor=COLORS["border"], linewidth=2, linestyle="--", zorder=0))
    _draw_box(ax, 2, 12, 3, 1, "Школьник", COLORS["white"], COLORS["primary"], 12, "bold")
    _draw_box(ax, 2, 4, 3, 1, "Родитель", COLORS["white"], COLORS["success"], 12, "bold")
    uses = [("Задать вопрос ИИ", 12.5, 17, COLORS["primary"]), ("Отправить ДЗ", 12.5, 14.5, COLORS["primary"]), ("Развивающие игры", 12.5, 12, COLORS["cyan"]), ("Тамагочи-панда", 12.5, 9.5, COLORS["warning"]), ("Отслеживание прогресса", 12.5, 7, COLORS["success"]), ("Premium-подписка", 12.5, 4.5, COLORS["danger"]), ("Реферальная программа", 12.5, 2, COLORS["secondary"])]
    for n, x, y, c in uses:
        ax.add_patch(mpatches.Ellipse((x, y), 8, 2, facecolor=COLORS["white"], edgecolor=c, linewidth=2, zorder=2))
        ax.text(x, y, n, ha="center", va="center", fontsize=12, fontweight="bold", zorder=3)
        if y >= 7: ax.plot([3.5, x-4], [12, y], color=COLORS["border"], lw=2, zorder=1)
        if y <= 7: ax.plot([3.5, x-4], [4, y], color=COLORS["border"], lw=2, zorder=1)
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "5_usecase.png")); plt.close()

def _draw_table_block(ax, x, y, name, cols, w=6.5):
    h = 0.8 + len(cols) * 0.55
    ax.add_patch(FancyBboxPatch((x-w/2, y-h), w, h, boxstyle="round,pad=0.1", facecolor=COLORS["slate_bg"], edgecolor=COLORS["border"], lw=2, zorder=2))
    ax.add_patch(FancyBboxPatch((x-w/2, y-0.8), w, 0.8, boxstyle="round,pad=0.1", facecolor=COLORS["primary"], edgecolor=COLORS["primary"], lw=2, zorder=3))
    ax.text(x, y-0.4, name, ha="center", va="center", fontsize=12, fontweight="bold", color="white", zorder=4)
    for i, c in enumerate(cols):
        ax.text(x-w/2+0.3, y-1.1-i*0.55, c, ha="left", va="center", fontsize=10, color=COLORS["text"], zorder=4)
    return h

def draw_erd_physical():
    fig, ax = plt.subplots(figsize=(26, 26))
    ax.set_xlim(-1, 35); ax.set_ylim(0, 36); ax.axis("off")
    # Giant layout for physical with huge text! 3 columns.
    tables = [
        ("users", 17, 35, ["id (PK)", "telegram_id (UQ)", "username", "first_name", "user_type", "premium_until", "parent_tel_id (FK)"]),
        ("chat_history", 5, 29, ["id (PK)", "user_tel_id (FK)", "message_text", "timestamp"]),
        ("daily_requests", 17, 29, ["id (PK)", "user_tel_id (FK)", "date", "request_count"]),
        ("learning_sessions", 29, 29, ["id (PK)", "user_tel_id (FK)", "subject", "topic"]),
        ("problem_topics", 5, 24, ["id (PK)", "user_tel_id (FK)", "subject", "error_count"]),
        ("homework_submit", 17, 24, ["id (PK)", "user_tel_id (FK)", "subject", "score"]),
        ("user_progress", 29, 24, ["id (PK)", "user_tel_id (FK)", "level", "points"]),
        ("panda_pet", 5, 19, ["id (PK)", "user_tel_id (FK)", "hunger", "energy"]),
        ("game_sessions", 17, 19, ["id (PK)", "user_tel_id (FK)", "game_type", "score"]),
        ("game_stats", 29, 19, ["id (PK)", "user_tel_id (FK)", "wins", "losses"]),
        ("payments", 5, 14, ["id (PK)", "user_tel_id (FK)", "subs_id (FK)", "amount"]),
        ("subscriptions", 17, 14, ["id (PK)", "user_tel_id (FK)", "plan_id", "expires_at"]),
        ("analytics_metrics", 29, 14, ["id (PK)", "metric_name", "value"]),
        ("referrers", 5, 9, ["id (PK)", "telegram_id", "comment"]),
        ("referral_payouts", 17, 9, ["id (PK)", "ref_tel_id", "user_tel_id", "amount"])
    ]
    for n, x, y, cols in tables:
        h = _draw_table_block(ax, x, y, n, cols, 10.5) # wide boxes
        if n != "users" and n not in ("analytics_metrics", "referrers"):
            if y == 29: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 24: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 19: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 14: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 9: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
    _draw_ortho(ax, 5+5.25, 9, 17-5.25, 9, COLORS["warning"], dir="h") # referrers
    _draw_ortho(ax, 5+5.25, 14, 17-5.25, 14, COLORS["danger"], dir="h") # payments->subs
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "6_erd_physical.png")); plt.close()

def draw_erd_relational():
    # Similar to physical, big font, less clutter
    fig, ax = plt.subplots(figsize=(26, 26))
    ax.set_xlim(-1, 35); ax.set_ylim(0, 36); ax.axis("off")
    tables = [
        ("users", 17, 35, ["id", "telegram_id", "username", "premium_until"]),
        ("chat_history", 5, 29, ["id", "user_tel_id", "message_text"]),
        ("daily_requests", 17, 29, ["id", "user_tel_id", "date"]),
        ("learning_sessions", 29, 29, ["id", "user_tel_id", "subject"]),
        ("problem_topics", 5, 24, ["id", "user_tel_id", "subject", "errors"]),
        ("homework_submit", 17, 24, ["id", "user_tel_id", "subject", "score"]),
        ("user_progress", 29, 24, ["id", "user_tel_id", "level", "points"]),
        ("panda_pet", 5, 19, ["id", "user_tel_id", "hunger", "energy"]),
        ("game_sessions", 17, 19, ["id", "user_tel_id", "game_type", "score"]),
        ("game_stats", 29, 19, ["id", "user_tel_id", "game_type", "wins"]),
        ("payments", 5, 14, ["id", "user_tel_id", "subs_id", "amount"]),
        ("subscriptions", 17, 14, ["id", "user_tel_id", "plan_id"]),
        ("analytics_metrics", 29, 14, ["id", "metric_name", "value"]),
        ("referrers", 5, 9, ["id", "telegram_id"]),
        ("referral_payouts", 17, 9, ["id", "ref_tel_id", "user_tel_id"])
    ]
    for n, x, y, cols in tables:
        h = _draw_table_block(ax, x, y, n, cols, 10.5)
        if n != "users" and n not in ("analytics_metrics", "referrers"):
            if y == 29: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 24: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 19: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 14: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
            elif y == 9: _draw_ortho(ax, x, y, 17, 35-h, COLORS["border"], dir="v")
    _draw_ortho(ax, 5+5.25, 9, 17-5.25, 9, COLORS["warning"], dir="h")
    _draw_ortho(ax, 5+5.25, 14, 17-5.25, 14, COLORS["danger"], dir="h")
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "7_erd_relational.png")); plt.close()

if __name__ == "__main__":
    draw_erd_conceptual(); draw_architecture(); draw_sequence(); draw_deployment(); draw_usecase(); draw_erd_physical(); draw_erd_relational()
