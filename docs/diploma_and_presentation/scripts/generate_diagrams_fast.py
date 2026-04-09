import os
import zlib
import base64
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def plantuml_encode_string(s):
    # This is standard Kroki payload encoding!
    compressed = zlib.compress(s.encode('utf-8'), 9)
    return base64.urlsafe_b64encode(compressed).decode('ascii')

def fetch_diagram(text, diag_type, filename):
    try:
        encoded = plantuml_encode_string(text)
        url = f"https://kroki.io/{diag_type}/png/{encoded}"
        print(f"Downloading {filename} from {url[:50]}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        print(f"✅ Успешно сохранено: {filename}")
    except Exception as e:
        print(f"❌ Ошибка генерации {filename}: {e}")

os.makedirs("docs/diploma_and_presentation/img", exist_ok=True)

erd = "erDiagram\nUSERS||--o{ CHAT_HISTORY: sends\nUSERS||--o{ LEARNING_SESSIONS: completes\nUSERS||--o{ PROBLEM_TOPICS: has\nUSERS||--o{ HOMEWORK_SUBMISSIONS: submits\nUSERS||--o{ GAME_SESSIONS: plays\nUSERS||--o{ GAME_STATS: tracks\nUSERS||--o| PANDA_PET: owns\nUSERS||--o{ PAYMENTS: makes\nUSERS||--o{ SUBSCRIPTIONS: buys\nUSERS||--|{ USER_PROGRESS: achieves\nUSERS||--o{ ANALYTICS_METRICS: triggered\nUSERS||--o{ REFERRAL_PAYOUTS: received\nREFERRERS||--o{ REFERRAL_PAYOUTS: earns"
arch = "@startuml\npackage Clients {\n[Telegram Bot]\n[Mini App]\n[Website]\n}\nnode Server {\n[API]\n[Services]\n}\ndatabase DB\nClients-->API\nAPI-->Services\nServices-->DB\n@enduml"
seq = "@startuml\nUser->Server: Message\nServer->DB: Query\nServer->GPT: Generate\nGPT-->Server: Response\nServer-->User: Reply\n@enduml"
deploy = "@startuml\nnode UserDevice\ncloud Cloudflare\nnode Railway { [Backend] [PostgreSQL] }\ncloud YandexCloud\nUserDevice-->Cloudflare\nCloudflare-->Backend\nBackend-->PostgreSQL\nBackend-->YandexCloud\n@enduml"
usecase = "@startuml\nactor Student\nusecase (Ask AI)\nusecase (Play Game)\nStudent--> (Ask AI)\nStudent--> (Play Game)\n@enduml"

fetch_diagram(erd, "mermaid", "docs/diploma_and_presentation/img/1_erd.png")
fetch_diagram(arch, "plantuml", "docs/diploma_and_presentation/img/2_architecture.png")
fetch_diagram(seq, "plantuml", "docs/diploma_and_presentation/img/3_sequence.png")
fetch_diagram(deploy, "plantuml", "docs/diploma_and_presentation/img/4_deployment.png")
fetch_diagram(usecase, "plantuml", "docs/diploma_and_presentation/img/5_usecase.png")
