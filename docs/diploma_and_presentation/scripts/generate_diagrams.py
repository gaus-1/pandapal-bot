import os
import requests
import json

def generate_diagram(text, diag_type, filename):
    url = "https://kroki.io"
    payload = {
        "diagram_source": text,
        "diagram_type": diag_type,
        "output_format": "png"
    }

    print(f"Генерация {filename} ({diag_type})...")
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            with open(filename, "wb") as f:
                f.write(res.content)
            print(f"✅ Успешно сохранено: {filename}\n")
        else:
            print(f"❌ Ошибка генерации {filename}: {res.status_code} - {res.text}\n")
    except Exception as e:
        print(f"Exception for {filename}: {e}")

os.makedirs("docs/diploma_and_presentation/img", exist_ok=True)

erd = """erDiagram
    USERS ||--o{ CHAT_HISTORY : sends
    USERS ||--o{ LEARNING_SESSIONS : completes
    USERS ||--o{ PROBLEM_TOPICS : has
    USERS ||--o{ HOMEWORK_SUBMISSIONS : submits
    USERS ||--o{ GAME_SESSIONS : plays
    USERS ||--o{ GAME_STATS : tracks
    USERS ||--o| PANDA_PET : owns
    USERS ||--o{ PAYMENTS : makes
    USERS ||--o{ SUBSCRIPTIONS : buys
    USERS ||--|{ USER_PROGRESS : achieves
    USERS ||--o{ ANALYTICS_METRICS : triggered
    USERS ||--o{ REFERRAL_PAYOUTS : received
    REFERRERS ||--o{ REFERRAL_PAYOUTS : earns

    USERS {
        int id PK
        bigint telegram_id UK
        string username
        string first_name
        string user_type
        datetime created_at
    }
    CHAT_HISTORY {
        int id PK
        bigint user_telegram_id FK
        text message_text
        string message_type
        datetime timestamp
    }
    LEARNING_SESSIONS {
        int id PK
        bigint user_telegram_id FK
        string subject
        int correct_answers
    }
    PROBLEM_TOPICS {
        int id PK
        bigint user_telegram_id FK
        string topic
        int error_count
    }
    HOMEWORK_SUBMISSIONS {
        int id PK
        bigint user_telegram_id FK
        text original_text
        boolean has_errors
    }
    GAME_SESSIONS {
        int id PK
        bigint user_telegram_id FK
        string game_type
        string result
    }
    GAME_STATS {
        int id PK
        bigint user_telegram_id FK
        string game_type
        int wins
    }
    PANDA_PET {
        int id PK
        bigint user_telegram_id FK
        int hunger
        int mood
        int energy
    }
    PAYMENTS {
        int id PK
        string payment_id UK
        bigint user_telegram_id FK
        int subscription_id FK
        float amount
        string status
    }
    SUBSCRIPTIONS {
        int id PK
        bigint user_telegram_id FK
        string plan_id
        datetime expires_at
        boolean is_active
    }
    USER_PROGRESS {
        int id PK
        bigint user_telegram_id FK
        string subject
        int level
        int points
    }
    DAILY_REQUEST_COUNTS {
        int id PK
        bigint user_telegram_id FK
        date date
        int request_count
    }
    ANALYTICS_METRICS {
        int id PK
        string metric_name
        float metric_value
        bigint user_telegram_id FK
    }
    REFERRERS {
        int id PK
        bigint telegram_id UK
    }
    REFERRAL_PAYOUTS {
        int id PK
        bigint referrer_telegram_id FK
        bigint user_telegram_id FK
        float amount_rub
    }
"""
generate_diagram(erd, "mermaid", "docs/diploma_and_presentation/img/1_erd.png")

arch = """
@startuml
skinparam handwritten false
skinparam componentStyle uml2
skinparam backgroundColor white

package "Клиенты" {
    [Telegram Bot\n(aiogram)] as Bot
    [Mini App\n(React/TS)] as MiniApp
    [Веб-сайт\n(pandapal.ru)] as Website
}

node "Railway (PaaS)" {
    component "web_server.py\n(Python 3.13)" as WebServer {
        port "Webhook" as WH
        port "REST API" as API
        [Middleware\n(Auth, Rate Limit)] as MW
        [Handlers\n(Message, Voice, Photo)] as Handlers
        [Services\n(AI, RAG, Games, Moderation)] as Services

        WH -down-> MW
        API -down-> MW
        MW -down-> Handlers
        Handlers -down-> Services
    }
}

database "PostgreSQL 17\n+ pgvector" as DB
database "Redis\n(Upstash)" as Redis

cloud "Yandex Cloud" as YC {
    [YandexGPT Pro]
    [SpeechKit STT]
    [Vision OCR]
    [Embeddings API]
}

cloud "YooKassa" as Yoo

Bot -down-> WH : HTTPS
MiniApp -down-> API : HTTPS
Website -down-> API : HTTPS

Services -down-> DB : SQLAlchemy (ORM)
Services -down-> Redis : Cache / Sessions
Services -down-> YC : REST
Services -down-> Yoo : REST

@enduml
"""
generate_diagram(arch, "plantuml", "docs/diploma_and_presentation/img/2_architecture.png")

seq = """
@startuml
actor "Ученик" as User
participant "Telegram" as TG
participant "web_server.py" as Server
participant "Moderation\\nService" as Mod
participant "RAG\\nPipeline" as RAG
database "PostgreSQL" as DB
participant "YandexGPT" as GPT

User -> TG: Текстовое сообщение
TG -> Server: Webhook (POST)
Server -> Server: Rate Limit & Auth
Server -> Mod: Проверка паттернов
activate Mod
Mod -> Server: Контент безопасен
deactivate Mod
Server -> RAG: Поиск контекста (vector search)
activate RAG
RAG -> DB: Косинусное расстояние
DB --> RAG: Релевантные знания
RAG --> Server: Расширенный контекст
deactivate RAG
Server -> GPT: Адаптивный промпт +\\nКонтекст +\\nСообщение
activate GPT
GPT --> Server: AI-ответ (потоковый/SSE)
deactivate GPT
Server -> Server: Обновление активности,\\nначисление XP
Server -> TG: Ответное сообщение
TG -> User: Отображение ответа
@enduml
"""
generate_diagram(seq, "plantuml", "docs/diploma_and_presentation/img/3_sequence.png")

deploy = """
@startuml
node "Устройства пользователей" {
    [Смартфон (Telegram/Браузер)]
    [ПК (Браузер)]
}

cloud "Cloudflare" as CF {
    [DNS / CDN]
    [WAF / DDoS Protection]
}

node "Railway" as Railway {
    node "Docker Container" {
        [PandaPal Backend\\n(Python/aiohttp)] as Backend
    }
    database "Managed PostgreSQL\\n(Relational + pgvector)" as PG
}

cloud "Yandex Cloud" as YC {
    [AI Services (GPT, OCR, STT)]
}

cloud "Upstash" as Upstash {
    database "Redis"
}

[Смартфон (Telegram/Браузер)] -down-> CF
[ПК (Браузер)] -down-> CF

CF -down-> Backend : HTTPS / WSS
Backend -down-> PG : TCP/IP (psycopg 3)
Backend -right-> Redis : TCP/IP
Backend -left-> YC : REST API
Backend -up-> Telegram : Bot API
@enduml
"""
generate_diagram(deploy, "plantuml", "docs/diploma_and_presentation/img/4_deployment.png")

usecase = """
@startuml
left to right direction
actor "Школьник (1-9 класс)" as Student
actor "Система (Бэкенд)" as System
actor "Подписчик" as Subscriber

package "Образовательная платформа PandaPal" {
    usecase "Задать вопрос AI-помощнику" as UC1
    usecase "Отправить ДЗ фото" as UC2
    usecase "Играть в развивающие игры" as UC3
    usecase "Ухаживать за виртуальной пандой" as UC4
    usecase "Получить прогресс и достижения" as UC5
    usecase "Безлимитные запросы к ИИ" as UC6
    usecase "Модерация контента" as UC7
    usecase "RAG-поиск по базе" as UC8
}

Student --> UC1
Student --> UC2
Student --> UC3
Student --> UC4
Student --> UC5

Student <|-- Subscriber
Subscriber --> UC6

UC1 .> UC7 : <<include>>
UC1 .> UC8 : <<include>>
UC2 .> UC7 : <<include>>

System --> UC7
System --> UC8
@enduml
"""
generate_diagram(usecase, "plantuml", "docs/diploma_and_presentation/img/5_usecase.png")

print("Генерация завершена.")
