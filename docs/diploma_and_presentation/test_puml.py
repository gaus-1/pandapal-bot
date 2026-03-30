import base64
import urllib.request
import zlib


def encode_plantuml(text):
    zlibbed_str = zlib.compress(text.encode("utf-8"))
    compressed_string = zlibbed_str[2:-4]
    return (
        base64.b64encode(compressed_string).translate(bytes.maketrans(b"+/", b"-_")).decode("utf-8")
    )


puml = """
@startuml
entity "Users" as users {
  *id : int
  --
  telegram_id : string
  premium : boolean
  coins : int
}
entity "PandaPet" as pet {
  *id : int
  --
  user_id : int
  health : int
  satiety : int
}
users ||--o{ pet : "has"
@enduml
"""

try:
    url = f"http://www.plantuml.com/plantuml/png/{encode_plantuml(puml)}"
    print("URL:", url)
    urllib.request.urlretrieve(url, "test_puml.png")
    print("PlantUML success!")
except Exception as e:
    print("PlantUML failed:", e)
