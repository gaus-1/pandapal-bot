# Whitelist для vulture - исключения для ложных срабатываний
# Формат: имя_переменной  # путь/к/файлу.py:номер_строки

# Абстрактные методы - параметры нужны для сигнатуры интерфейса
user_grade  # bot/interfaces.py:90
default  # bot/interfaces.py:174

# Параметры callback функций - используются фреймворком Sentry
hint  # bot/monitoring/sentry_config.py:64
hint  # bot/monitoring/sentry_config.py:87

# Параметры контекстных менеджеров - стандартная сигнатура __aexit__
exc_type  # bot/services/web_scraper.py:115
exc_val  # bot/services/web_scraper.py:115
exc_tb  # bot/services/web_scraper.py:115

# Параметры методов интерфейсов - могут использоваться в реализациях
detected_topic  # bot/services/moderation_service.py:196
