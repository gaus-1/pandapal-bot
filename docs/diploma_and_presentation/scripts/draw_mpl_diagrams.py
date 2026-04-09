import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs("docs/diploma_and_presentation/img", exist_ok=True)

def draw_boxes(title, boxes, arrows, filename, figsize=(10, 8)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Store box coords to draw arrows easily
    box_coords = {}

    for box in boxes:
        name = box.get('name')
        x, y = box['x'], box['y']
        w, h = box.get('w', 20), box.get('h', 10)
        color = box.get('color', '#E8F5E9')
        text = box.get('text', name)

        box_coords[name] = (x, y, w, h)

        rect = patches.FancyBboxPatch((x, y), w, h,
                                      boxstyle="round,pad=1",
                                      linewidth=2, edgecolor='#2E7D32', facecolor=color)
        ax.add_patch(rect)

        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                fontsize=box.get('fontsize', 10), wrap=True, fontweight=box.get('fw', 'normal'))

    for arrow in arrows:
        name1, name2 = arrow['from'], arrow['to']
        label = arrow.get('label', '')

        if name1 not in box_coords or name2 not in box_coords:
            continue

        x1, y1, w1, h1 = box_coords[name1]
        x2, y2, w2, h2 = box_coords[name2]

        # very simple connection
        cx1, cy1 = x1 + w1/2, y1 + h1/2
        cx2, cy2 = x2 + w2/2, y2 + h2/2

        ax.annotate(label,
                    xy=(cx2, cy2), xycoords='data',
                    xytext=(cx1, cy1), textcoords='data',
                    arrowprops=dict(arrowstyle="->", color="black", lw=1.5, shrinkA=30, shrinkB=30),
                    ha='center', va='center', fontsize=9, bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.8))

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

# 1. ERD
erd_boxes = [
    {"name": "USERS", "x": 40, "y": 80, "w": 20, "h": 10, "text": "USERS\n(telegram_id, age)", "fw": "bold", "color": "#FFF9C4"},
    {"name": "CHAT_HISTORY", "x": 10, "y": 60, "w": 22, "h": 8, "text": "CHAT_HISTORY"},
    {"name": "LEARNING_SESSIONS", "x": 40, "y": 60, "w": 22, "h": 8, "text": "LEARNING_SESSIONS"},
    {"name": "PROBLEM_TOPICS", "x": 70, "y": 60, "w": 22, "h": 8, "text": "PROBLEM_TOPICS"},

    {"name": "HOMEWORK", "x": 10, "y": 45, "w": 22, "h": 8, "text": "HOMEWORK_SUBMISSIONS"},
    {"name": "USER_PROGRESS", "x": 40, "y": 45, "w": 22, "h": 8, "text": "USER_PROGRESS"},
    {"name": "PANDA_PET", "x": 70, "y": 45, "w": 22, "h": 8, "text": "PANDA_PET\n(hunger, energy)"},

    {"name": "GAME_SESSIONS", "x": 10, "y": 30, "w": 22, "h": 8, "text": "GAME_SESSIONS"},
    {"name": "GAME_STATS", "x": 10, "y": 15, "w": 22, "h": 8, "text": "GAME_STATS"},

    {"name": "PAYMENTS", "x": 40, "y": 30, "w": 22, "h": 8, "text": "PAYMENTS"},
    {"name": "SUBSCRIPTIONS", "x": 40, "y": 15, "w": 22, "h": 8, "text": "SUBSCRIPTIONS"},

    {"name": "REFERRAL_PAYOUTS", "x": 70, "y": 30, "w": 22, "h": 8, "text": "REFERRAL_PAYOUTS"},
    {"name": "REFERRERS", "x": 70, "y": 15, "w": 22, "h": 8, "text": "REFERRERS"},

    {"name": "DAILY_REQUESTS", "x": 75, "y": 80, "w": 22, "h": 8, "text": "DAILY_REQUESTS"},
    {"name": "ANALYTICS", "x": 5, "y": 80, "w": 22, "h": 8, "text": "ANALYTICS_METRICS"},
]
erd_arrows = [
    {"from": "USERS", "to": "CHAT_HISTORY", "label": "1:N"},
    {"from": "USERS", "to": "LEARNING_SESSIONS", "label": "1:N"},
    {"from": "USERS", "to": "PROBLEM_TOPICS", "label": "1:N"},
    {"from": "USERS", "to": "HOMEWORK", "label": "1:N"},
    {"from": "USERS", "to": "USER_PROGRESS", "label": "1:N"},
    {"from": "USERS", "to": "PANDA_PET", "label": "1:1"},
    {"from": "USERS", "to": "GAME_SESSIONS", "label": "1:N"},
    {"from": "USERS", "to": "GAME_STATS", "label": "1:1"},
    {"from": "USERS", "to": "PAYMENTS", "label": "1:N"},
    {"from": "USERS", "to": "SUBSCRIPTIONS", "label": "1:N"},
    {"from": "USERS", "to": "REFERRAL_PAYOUTS", "label": "1:N"},
    {"from": "REFERRERS", "to": "REFERRAL_PAYOUTS", "label": "1:N"},
    {"from": "USERS", "to": "DAILY_REQUESTS", "label": "1:N"},
    {"from": "USERS", "to": "ANALYTICS", "label": "1:N"},
]

# 2. Architecture
arch_boxes = [
    {"name": "Telegram", "x": 10, "y": 70, "w": 20, "h": 12, "text": "Telegram / Mini App\nКлиенты", "color": "#E3F2FD"},
    {"name": "WebServer", "x": 40, "y": 65, "w": 20, "h": 22, "text": "Server Core\n(Python, aiogram,\nFastAPI)", "color": "#FFF3E0"},
    {"name": "Services", "x": 40, "y": 45, "w": 20, "h": 15, "text": "Business Logic\n(RAG, Games, XP)", "color": "#FFF3E0"},
    {"name": "DB", "x": 40, "y": 20, "w": 20, "h": 15, "text": "PostgreSQL + pgvector\n(Data Layer)", "color": "#E8EAF6"},
    {"name": "Yandex", "x": 75, "y": 70, "w": 20, "h": 15, "text": "Yandex Cloud\n(GPT, STT, Embeddings)", "color": "#FFEBEE"},
    {"name": "YooKassa", "x": 75, "y": 45, "w": 20, "h": 10, "text": "YooKassa\n(Payments)", "color": "#E0F7FA"}
]
arch_arrows = [
    {"from": "Telegram", "to": "WebServer", "label": "Webhook\n(HTTPS)"},
    {"from": "WebServer", "to": "Services", "label": "Call"},
    {"from": "Services", "to": "DB", "label": "SQLAlchemy"},
    {"from": "Services", "to": "Yandex", "label": "REST API"},
    {"from": "Services", "to": "YooKassa", "label": "REST API"}
]

# 3. Sequence
seq_boxes = [
    {"name": "User", "x": 5, "y": 80, "w": 15, "h": 10, "text": "Пользователь", "color": "#F3E5F5"},
    {"name": "Server", "x": 30, "y": 80, "w": 15, "h": 10, "text": "Cервер", "color": "#FFF3E0"},
    {"name": "RAG", "x": 55, "y": 80, "w": 15, "h": 10, "text": "Knowledge DB", "color": "#E8EAF6"},
    {"name": "GPT", "x": 80, "y": 80, "w": 15, "h": 10, "text": "YandexGPT", "color": "#FFEBEE"},

    # actions
    {"name": "A1", "x": 17.5, "y": 65, "w": 10, "h": 5, "text": "Отправляет вопрос", "color": 'white'},
    {"name": "A2", "x": 42.5, "y": 50, "w": 10, "h": 5, "text": "Поиск контекста (Vector)", "color": 'white'},
    {"name": "A3", "x": 67.5, "y": 35, "w": 10, "h": 5, "text": "Промпт + Контекст", "color": 'white'},
    {"name": "A4", "x": 42.5, "y": 20, "w": 10, "h": 5, "text": "Потоковый ответ", "color": 'white'},
]
# Draw sequence manually
def custom_sequence(filename):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Схема обработки сообщений (Sequence Diagram)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Participants
    parts = {"User": 10, "Server": 40, "DB/RAG": 70, "YandexGPT": 95}
    for name, x in parts.items():
        rect = patches.FancyBboxPatch((x-7, 85), 14, 8, boxstyle="round,pad=1", facecolor='#E8F5E9', edgecolor='#2E7D32', lw=2)
        ax.add_patch(rect)
        ax.text(x, 89, name, ha='center', va='center', fontweight='bold', fontsize=11)
        ax.plot([x, x], [10, 85], ls='--', color='gray')

    def draw_msg(y, p1, p2, text):
        x1 = parts[p1]
        x2 = parts[p2]
        ax.annotate(text, xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", lw=2), ha='center', va='bottom')

    draw_msg(75, "User", "Server", "Текстовый запрос")
    draw_msg(60, "Server", "DB/RAG", "Поиск релевантного контекста")
    draw_msg(50, "DB/RAG", "Server", "Найденные фрагменты")
    draw_msg(40, "Server", "YandexGPT", "Запрос: промпт + контекст + история")
    draw_msg(30, "YandexGPT", "Server", "Ответ от LLM (SSE stream)")
    draw_msg(15, "Server", "User", "Сообщение в Telegram")

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

# 4. Deployment
dep_boxes = [
    {"name": "User", "x": 40, "y": 80, "w": 20, "h": 10, "text": "Устройство пользователя"},
    {"name": "Cloudflare", "x": 40, "y": 60, "w": 20, "h": 10, "text": "Cloudflare\n(DNS / SSL)"},
    {"name": "Railway", "x": 20, "y": 10, "w": 60, "h": 40, "text": "Railway Cloud", "color": "none"},
    {"name": "Docker", "x": 25, "y": 30, "w": 20, "h": 15, "text": "Backend Container\n(Python/FastAPI)"},
    {"name": "DB", "x": 55, "y": 30, "w": 20, "h": 15, "text": "PostgreSQL Container\n(pgvector)"},
    {"name": "Redis", "x": 25, "y": 15, "w": 20, "h": 10, "text": "Redis Server\n(Cache/Celery)"},
]
dep_arrows = [
    {"from": "User", "to": "Cloudflare"},
    {"from": "Cloudflare", "to": "Docker", "label": "HTTPS/Websockets"},
    {"from": "Docker", "to": "DB", "label": "psycopg"},
    {"from": "Docker", "to": "Redis", "label": "redis"},
]

# 5. Use Case
uc_boxes = [
    {"name": "Student", "x": 10, "y": 50, "w": 15, "h": 15, "text": "Школьник", "color": "#F3E5F5"},
    {"name": "AskAI", "x": 50, "y": 80, "w": 30, "h": 10, "text": "Задать вопрос ИИ\n(Помощь с учебой)", "color": "#E3F2FD", "fontsize": 11},
    {"name": "HW", "x": 50, "y": 65, "w": 30, "h": 10, "text": "Отправить ДЗ (Фото OCR)", "color": "#E3F2FD", "fontsize": 11},
    {"name": "Game", "x": 50, "y": 50, "w": 30, "h": 10, "text": "Развивающие игры\n(Логика/Математика)", "color": "#E3F2FD", "fontsize": 11},
    {"name": "Panda", "x": 50, "y": 35, "w": 30, "h": 10, "text": "Виртуальный питомец\n(Тамагочи)", "color": "#E3F2FD", "fontsize": 11},
    {"name": "Premium", "x": 50, "y": 20, "w": 30, "h": 10, "text": "Premium подписка\n(Безлимит)", "color": "#FFF9C4", "fontsize": 11},
    {"name": "Parent", "x": 10, "y": 20, "w": 15, "h": 15, "text": "Родитель", "color": "#E8F5E9"},
]
uc_arrows = [
    {"from": "Student", "to": "AskAI"},
    {"from": "Student", "to": "HW"},
    {"from": "Student", "to": "Game"},
    {"from": "Student", "to": "Panda"},
    {"from": "Parent", "to": "Premium"},
]

# Generate All
draw_boxes("Структура базы данных (ER-Диаграмма)", erd_boxes, erd_arrows, "docs/diploma_and_presentation/img/1_erd.png", figsize=(12,12))
draw_boxes("Общая архитектура системы", arch_boxes, arch_arrows, "docs/diploma_and_presentation/img/2_architecture.png")
custom_sequence("docs/diploma_and_presentation/img/3_sequence.png")
draw_boxes("Схема развёртывания инфраструктуры", dep_boxes, dep_arrows, "docs/diploma_and_presentation/img/4_deployment.png")
draw_boxes("Диаграмма вариантов использования продукта", uc_boxes, uc_arrows, "docs/diploma_and_presentation/img/5_usecase.png")

print("Все диаграммы успешно сформированы с помощью Matplotlib!")
