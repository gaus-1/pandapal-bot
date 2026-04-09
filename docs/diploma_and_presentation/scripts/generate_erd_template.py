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

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 16,  # HUGE FONT BASE
    "axes.linewidth": 0,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "savefig.pad_inches": 0.1,
})

def _draw_table_block(ax, x, y, name, raw_cols, w=9.5):
    # Parse cols into (type, name)
    cols = []
    for c in raw_cols:
        if "(PK)" in c: cols.append(("PK", c.replace(" (PK)", "")))
        elif "FK" in c: cols.append(("FK", c.replace(" (FK)", "").replace(" (FK, UQ)", "")))
        elif "(UQ)" in c: cols.append(("Key", c.replace(" (UQ)", "")))
        else: cols.append(("   ", c)) # Just space for alignment

    row_h = 0.65
    header_h = 0.9
    h = header_h + len(cols) * row_h

    # Body bg
    box = FancyBboxPatch((x-w/2, y-h), w, h, boxstyle="square,pad=0", facecolor="#BBE8FA", edgecolor="black", lw=2, zorder=2)
    ax.add_patch(box)

    # Header bg
    if cols:
        head = FancyBboxPatch((x-w/2, y-header_h), w, header_h, boxstyle="square,pad=0", facecolor="#95D4EE", edgecolor="black", lw=2, zorder=3)
    else:  # For conceptual ERD (no columns)
        head = FancyBboxPatch((x-w/2, y-h), w, h, boxstyle="square,pad=0", facecolor="#95D4EE", edgecolor="black", lw=2, zorder=3)
    ax.add_patch(head)

    # Vertical line separating key col and name col
    if cols:
        ax.plot([x-w/2+1.5, x-w/2+1.5], [y-h, y-header_h], color="black", lw=2, zorder=3)

    # Center text vertically in header or full box
    if cols:
        ax.text(x, y-header_h/2, name, ha="center", va="center", fontsize=15, fontweight="bold", color="black", zorder=4)
    else:
        ax.text(x, y-h/2, name, ha="center", va="center", fontsize=16, fontweight="bold", color="black", zorder=4)

    for i, (k_type, c_name) in enumerate(cols):
        cy = y - header_h - 0.32 - i * row_h
        ax.text(x-w/2+0.15, cy, k_type, ha="left", va="center", fontsize=14, fontweight="bold", color="black", zorder=4)
        ax.text(x-w/2+1.7, cy, c_name, ha="left", va="center", fontsize=14, color="black", zorder=4)

    return h


def _draw_ortho(ax, x1, y1, x2, y2, color="black", lw=2, ls="-", dir="v", end_symbol="", label=""):
    if dir == "v":
        ymid = (y1 + y2) / 2
        ax.plot([x1, x1, x2, x2], [y1, ymid, ymid, y2], color=color, lw=lw, ls=ls, zorder=0)
        # Crow's foot at end
        if "crow" in end_symbol:
            dy = 0.4 if y2 > y1 else -0.4
            ax.plot([x2, x2-0.3], [y2, y2-dy], color=color, lw=lw, zorder=1)
            ax.plot([x2, x2+0.3], [y2, y2-dy], color=color, lw=lw, zorder=1)
            ax.plot([x2-0.3, x2+0.3], [y2-dy*1.5, y2-dy*1.5], color=color, lw=lw, zorder=1)
            if "circle" in end_symbol:
                ax.add_patch(plt.Circle((x2, y2-dy*2.2), 0.15, fill=False, color=color, lw=lw, zorder=1))
        # Add labels
        if label:
            ax.text(x2 + 0.3, ymid + 0.3, label, fontsize=12, color="gray", backgroundcolor="white", zorder=2)
    else:
        xmid = (x1 + x2) / 2
        ax.plot([x1, xmid, xmid, x2], [y1, y1, y2, y2], color=color, lw=lw, ls=ls, zorder=0)
        if "crow" in end_symbol:
            dx = 0.4 if x2 > x1 else -0.4
            ax.plot([x2, x2-dx], [y2, y2-0.3], color=color, lw=lw, zorder=1)
            ax.plot([x2, x2-dx], [y2, y2+0.3], color=color, lw=lw, zorder=1)
            ax.plot([x2-dx*1.5, x2-dx*1.5], [y2-0.3, y2+0.3], color=color, lw=lw, zorder=1)
            if "circle" in end_symbol:
                ax.add_patch(plt.Circle((x2-dx*2.2, y2), 0.15, fill=False, color=color, lw=lw, zorder=1))
        if label:
            ax.text(xmid, y1 + 0.3, label, ha="center", fontsize=12, color="gray", backgroundcolor="white", zorder=2)


def draw_erd_physical():
    # Make layout much tighter so visual percentage is large!
    fig, ax = plt.subplots(figsize=(24, 21)) # Tighter Y limit to crop white space!
    ax.set_xlim(0, 32); ax.set_ylim(6, 32); ax.axis("off")
    # Columns at x = 5.5, 16, 26.5. (Width = 9.5)
    c1, c2, c3 = 5.5, 16, 26.5
    tables = [
        ("users", c2, 32, ["id (PK)", "telegram_id (UQ)", "username", "first_name", "user_type", "premium_until", "parent_tel_id (FK)"]),
        ("chat_history", c1, 26, ["id (PK)", "user_tel_id (FK)", "message_text", "timestamp"]),
        ("daily_requests", c2, 26, ["id (PK)", "user_tel_id (FK)", "date", "request_count"]),
        ("learning_sessions", c3, 26, ["id (PK)", "user_tel_id (FK)", "subject", "topic"]),
        ("problem_topics", c1, 21.5, ["id (PK)", "user_tel_id (FK)", "subject", "error_count"]),
        ("homework_submit", c2, 21.5, ["id (PK)", "user_tel_id (FK)", "subject", "score"]),
        ("user_progress", c3, 21.5, ["id (PK)", "user_tel_id (FK)", "level", "points"]),
        ("panda_pet", c1, 16.5, ["id (PK)", "user_tel_id (FK)", "hunger", "energy"]),
        ("game_sessions", c2, 16.5, ["id (PK)", "user_tel_id (FK)", "game_type", "score"]),
        ("game_stats", c3, 16.5, ["id (PK)", "user_tel_id (FK)", "wins", "losses"]),
        ("payments", c1, 11.5, ["id (PK)", "user_tel_id (FK)", "subs_id (FK)", "amount"]),
        ("subscriptions", c2, 11.5, ["id (PK)", "user_tel_id (FK)", "plan_id", "expires_at"]),
        ("analytics_metrics", c3, 11.5, ["id (PK)", "metric_name", "value"]),
        ("referrers", c1, 7, ["id (PK)", "telegram_id", "comment"]),
        ("referral_payouts", c2, 7, ["id (PK)", "ref_tel_id", "user_tel_id (FK)", "amount"])
    ]
    for n, x, y, cols in tables:
        h = _draw_table_block(ax, x, y, n, cols, w=10)
        # Routing to Center top (USERS)
        if n != "users" and n not in ("analytics_metrics", "referrers"):
            if y in (26, 21.5, 16.5, 11.5, 7):
                _draw_ortho(ax, x, y, c2, 32-h, end_symbol="crow")
    # Horizontal links
    _draw_ortho(ax, c1+5, 7, c2-5, 7, dir="h", end_symbol="crow") # refs -> payouts
    _draw_ortho(ax, c1+5, 11.5, c2-5, 11.5, dir="h", end_symbol="crow") # payments -> subs
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "6_erd_physical.png")); plt.close()

def draw_erd_relational():
    fig, ax = plt.subplots(figsize=(24, 21))
    ax.set_xlim(0, 32); ax.set_ylim(6, 32); ax.axis("off")
    c1, c2, c3 = 5.5, 16, 26.5
    tables = [
        ("users", c2, 32, ["id (PK)", "telegram_id (UQ)", "username", "premium_until"]),
        ("chat_history", c1, 26, ["id (PK)", "user_tel_id (FK)", "message_text"]),
        ("daily_requests", c2, 26, ["id (PK)", "user_tel_id (FK)", "date"]),
        ("learning_sessions", c3, 26, ["id (PK)", "user_tel_id (FK)", "subject"]),
        ("problem_topics", c1, 21.5, ["id (PK)", "user_tel_id (FK)", "errors"]),
        ("homework_submit", c2, 21.5, ["id (PK)", "user_tel_id (FK)", "score"]),
        ("user_progress", c3, 21.5, ["id (PK)", "user_tel_id (FK)", "points"]),
        ("panda_pet", c1, 16.5, ["id (PK)", "user_tel_id (FK)", "energy"]),
        ("game_sessions", c2, 16.5, ["id (PK)", "user_tel_id (FK)", "score"]),
        ("game_stats", c3, 16.5, ["id (PK)", "user_tel_id (FK)", "wins"]),
        ("payments", c1, 11.5, ["id (PK)", "user_tel_id (FK)", "amount"]),
        ("subscriptions", c2, 11.5, ["id (PK)", "user_tel_id (FK)", "plan_id"]),
        ("analytics_metrics", c3, 11.5, ["id (PK)", "metric_name", "value"]),
        ("referrers", c1, 7, ["id (PK)", "telegram_id"]),
        ("referral_payouts", c2, 7, ["id (PK)", "ref_tel_id (FK)", "amount"])
    ]
    for n, x, y, cols in tables:
        h = _draw_table_block(ax, x, y, n, cols, w=10)
        if n != "users" and n not in ("analytics_metrics", "referrers"):
            if y in (26, 21.5, 16.5, 11.5, 7):
                _draw_ortho(ax, x, y, c2, 32-h, end_symbol="crow")
    _draw_ortho(ax, c1+5, 7, c2-5, 7, dir="h", end_symbol="crow")
    _draw_ortho(ax, c1+5, 11.5, c2-5, 11.5, dir="h", end_symbol="crow")
    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "7_erd_relational.png")); plt.close()

def draw_erd_conceptual():
    # Make it beautifully structured and completely non-overlapping!
    # Simple hierarchy tree. It will look identical to a true Conceptual ERD with crow's foot.
    fig, ax = plt.subplots(figsize=(20, 14))
    ax.set_xlim(0, 32); ax.set_ylim(2, 22); ax.axis("off")
    c1, c2, c3 = 6, 16, 26

    # Empty column list [] to draw just the header box (conceptual ERDs)
    tables = [
        ("USERS", c2, 21),
        ("CHAT_HISTORY", c1, 17), ("DAILY_REQUESTS", c2, 17), ("LEARNING_SESSIONS", c3, 17),
        ("PROBLEM_TOPICS", c1, 13), ("HOMEWORK_SUBMISSIONS", c2, 13), ("USER_PROGRESS", c3, 13),
        ("PANDA_PET", c1, 9), ("GAME_SESSIONS", c2, 9), ("GAME_STATS", c3, 9),
        ("PAYMENTS", c1, 5), ("SUBSCRIPTIONS", c2, 5), ("ANALYTICS_METRICS", c3, 5),
        ("REFERRERS", c1, 1), ("REFERRAL_PAYOUTS", c2, 1) # placed at bottom
    ]
    # Redefine tables list to fit neatly
    tables = [
        ("USERS", c2, 21),
        ("CHAT_HISTORY", c1, 17), ("DAILY_REQUESTS", c2, 17), ("LEARNING_SESSIONS", c3, 17),
        ("PROBLEM_TOPICS", c1, 13), ("HOMEWORK_SUBMIT", c2, 13), ("USER_PROGRESS", c3, 13),
        ("PANDA_PET", c1, 9), ("GAME_SESSIONS", c2, 9), ("GAME_STATS", c3, 9),
        ("PAYMENTS", c1, 5), ("SUBSCRIPTIONS", c2, 5), ("ANALYTICS_METRICS", c3, 5),
    ]
    # For referrers, put it at x=6, y=2. For payouts, x=16, y=2.
    # WAIT! Instead of just drawing the box, we can give it 1 row of placeholder so it has height?
    # No, _draw_table_block handles empty cols by drawing just the box!
    for n, x, y in tables:
        h = _draw_table_block(ax, x, y, n, [], w=8)
        if n != "USERS" and n != "ANALYTICS_METRICS":
            label = "1:1" if n == "PANDA_PET" else ""
            sym = "crow" if n != "PANDA_PET" else ""
            _draw_ortho(ax, x, y, c2, 21-h, end_symbol=sym, label=label)

    h_ref = _draw_table_block(ax, c1, 2, "REFERRERS", [], w=8)
    h_pay = _draw_table_block(ax, c2, 2, "REFERRAL_PAYOUTS", [], w=8)

    _draw_ortho(ax, c2, 2, c2, 21-h, end_symbol="crow") # payouts->users
    _draw_ortho(ax, c1+4, 2-0.45, c2-4, 2-0.45, dir="h", end_symbol="crow") # refs->payouts
    _draw_ortho(ax, c1+4, 5-0.45, c2-4, 5-0.45, dir="h", end_symbol="crow") # payments->subs

    plt.tight_layout(); plt.savefig(os.path.join(OUT_DIR, "1_erd.png")); plt.close()

if __name__ == "__main__":
    draw_erd_conceptual()
    draw_erd_physical()
    draw_erd_relational()
    logger.info("Successfully recreated all ERDs with massive fonts, tight layout and perfect crow's foot notation!")
