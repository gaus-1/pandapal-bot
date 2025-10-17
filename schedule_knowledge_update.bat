@echo off
REM Скрипт для запуска обновления базы знаний через планировщик задач Windows
REM
REM Использование:
REM 1. Откройте "Планировщик заданий" (Task Scheduler)
REM 2. Создайте новую задачу: Действие -> Создать простую задачу
REM 3. Триггер: Еженедельно, в 03:00 (ночью)
REM 4. Действие: Запустить программу -> укажите путь к этому файлу
REM

cd /d "%~dp0"
call venv\Scripts\activate.bat
python update_knowledge_base.py >> logs\knowledge_update.log 2>&1
