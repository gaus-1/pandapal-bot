"""
Асинхронный процессор для обработки задач в фоне
Оптимизирует производительность за счет неблокирующей обработки
@module bot.services.async_processor
"""

import asyncio
import queue
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger


class TaskPriority(Enum):
    """Приоритеты задач"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Статусы задач"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncTask:
    """Задача для асинхронной обработки"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    func: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 3
    ttl: Optional[int] = None  # Время жизни задачи в секундах

    def __lt__(self, other):
        """Сравнение для сортировки по приоритету"""
        return self.priority.value > other.priority.value


class AsyncProcessor:
    """
    Асинхронный процессор задач
    Обрабатывает задачи в фоновом режиме с приоритизацией
    """

    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        """
        Инициализация процессора

        Args:
            max_workers: Максимальное количество воркеров
            queue_size: Максимальный размер очереди
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self._task_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=queue_size)
        self._workers: List[threading.Thread] = []
        self._running = False
        self._tasks: Dict[str, AsyncTask] = {}
        self._task_lock = threading.Lock()
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "active_workers": 0,
        }

        logger.info(f"⚡ Асинхронный процессор инициализирован (воркеров: {max_workers})")

    def start(self):
        """Запуск процессора"""
        if self._running:
            logger.warning("⚠️ Процессор уже запущен")
            return

        self._running = True

        # Создаем воркеров
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop, name=f"AsyncWorker-{i+1}", daemon=True
            )
            worker.start()
            self._workers.append(worker)

        # Запускаем очистку устаревших задач
        cleanup_thread = threading.Thread(
            target=self._cleanup_loop, name="TaskCleanup", daemon=True
        )
        cleanup_thread.start()

        logger.info(f"🚀 Асинхронный процессор запущен с {self.max_workers} воркерами")

    def stop(self, timeout: int = 30):
        """
        Остановка процессора

        Args:
            timeout: Таймаут ожидания завершения воркеров
        """
        if not self._running:
            return

        logger.info("🛑 Остановка асинхронного процессора...")
        self._running = False

        # Ждем завершения воркеров
        for worker in self._workers:
            worker.join(timeout=timeout)

        self._workers.clear()
        logger.info("✅ Асинхронный процессор остановлен")

    def submit_task(
        self,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        ttl: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Добавить задачу в очередь

        Args:
            func: Функция для выполнения
            *args: Аргументы функции
            priority: Приоритет задачи
            max_retries: Максимум попыток
            ttl: Время жизни задачи в секундах
            **kwargs: Именованные аргументы функции

        Returns:
            ID задачи
        """
        if not self._running:
            raise RuntimeError("Процессор не запущен")

        task = AsyncTask(
            func=func, args=args, kwargs=kwargs, priority=priority, max_retries=max_retries, ttl=ttl
        )

        try:
            self._task_queue.put(task, timeout=5)

            with self._task_lock:
                self._tasks[task.id] = task
                self._stats["total_tasks"] += 1

            logger.debug(f"📝 Задача добавлена: {task.id} (приоритет: {priority.name})")
            return task.id

        except queue.Full:
            logger.error("❌ Очередь задач переполнена")
            raise RuntimeError("Очередь задач переполнена")

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Получить статус задачи

        Args:
            task_id: ID задачи

        Returns:
            Статус задачи или None если не найдена
        """
        with self._task_lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    def get_task_result(self, task_id: str) -> Any:
        """
        Получить результат задачи

        Args:
            task_id: ID задачи

        Returns:
            Результат задачи или None
        """
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                return task.result
            elif task and task.status == TaskStatus.FAILED:
                raise task.error
            return None

    def cancel_task(self, task_id: str) -> bool:
        """
        Отменить задачу

        Args:
            task_id: ID задачи

        Returns:
            True если задача отменена
        """
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self._stats["cancelled_tasks"] += 1
                logger.info(f"❌ Задача отменена: {task_id}")
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику процессора

        Returns:
            Словарь со статистикой
        """
        with self._task_lock:
            return {
                **self._stats,
                "queue_size": self._task_queue.qsize(),
                "active_tasks": len(
                    [t for t in self._tasks.values() if t.status == TaskStatus.PROCESSING]
                ),
                "pending_tasks": len(
                    [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
                ),
                "running": self._running,
            }

    def _worker_loop(self):
        """Основной цикл воркера"""
        logger.debug(f"🔄 Воркер {threading.current_thread().name} запущен")

        while self._running:
            try:
                # Получаем задачу из очереди
                task = self._task_queue.get(timeout=1)

                # Проверяем не отменена ли задача
                if task.status == TaskStatus.CANCELLED:
                    continue

                # Проверяем TTL
                if task.ttl and datetime.utcnow() - task.created_at > timedelta(seconds=task.ttl):
                    task.status = TaskStatus.CANCELLED
                    self._stats["cancelled_tasks"] += 1
                    continue

                # Выполняем задачу
                self._execute_task(task)

                self._task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Ошибка воркера: {e}")

        logger.debug(f"🛑 Воркер {threading.current_thread().name} завершен")

    def _execute_task(self, task: AsyncTask):
        """Выполнение задачи"""
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.utcnow()

        logger.debug(f"⚡ Выполнение задачи: {task.id}")

        try:
            # Выполняем функцию
            if asyncio.iscoroutinefunction(task.func):
                # Для async функций создаем новый event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(task.func(*task.args, **task.kwargs))
                finally:
                    loop.close()
            else:
                # Для обычных функций
                result = task.func(*task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self._stats["completed_tasks"] += 1

            logger.debug(f"✅ Задача выполнена: {task.id}")

        except Exception as e:
            task.error = e
            task.retry_count += 1

            if task.retry_count <= task.max_retries:
                logger.warning(
                    f"⚠️ Ошибка задачи {task.id}, попытка {task.retry_count}/{task.max_retries}: {e}"
                )
                task.status = TaskStatus.PENDING
                # Возвращаем задачу в очередь для повтора
                try:
                    self._task_queue.put(task, timeout=1)
                except queue.Full:
                    task.status = TaskStatus.FAILED
                    self._stats["failed_tasks"] += 1
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                self._stats["failed_tasks"] += 1
                logger.error(f"❌ Задача провалена: {task.id} - {e}")

    def _cleanup_loop(self):
        """Цикл очистки старых задач"""
        while self._running:
            try:
                asyncio.sleep(300)  # Очистка каждые 5 минут

                with self._task_lock:
                    now = datetime.utcnow()
                    tasks_to_remove = []

                    for task_id, task in self._tasks.items():
                        # Удаляем завершенные задачи старше 1 часа
                        if (
                            task.status
                            in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                            and task.completed_at
                            and now - task.completed_at > timedelta(hours=1)
                        ):
                            tasks_to_remove.append(task_id)

                    for task_id in tasks_to_remove:
                        del self._tasks[task_id]

                    if tasks_to_remove:
                        logger.debug(f"🧹 Очищено {len(tasks_to_remove)} старых задач")

            except Exception as e:
                logger.error(f"❌ Ошибка очистки задач: {e}")


# Глобальный экземпляр процессора
async_processor = AsyncProcessor(max_workers=4)


# Декораторы для асинхронной обработки
def async_task(
    priority: TaskPriority = TaskPriority.NORMAL, max_retries: int = 3, ttl: Optional[int] = None
):
    """
    Декоратор для выполнения функции в фоновом режиме

    Args:
        priority: Приоритет задачи
        max_retries: Максимум попыток
        ttl: Время жизни задачи в секундах
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            task_id = async_processor.submit_task(
                func, *args, priority=priority, max_retries=max_retries, ttl=ttl, **kwargs
            )
            return task_id

        wrapper.original_func = func
        wrapper.task_id = None
        return wrapper

    return decorator


def high_priority_task(max_retries: int = 5):
    """Декоратор для высокоприоритетных задач"""
    return async_task(priority=TaskPriority.HIGH, max_retries=max_retries)


def low_priority_task(max_retries: int = 1):
    """Декоратор для низкоприоритетных задач"""
    return async_task(priority=TaskPriority.LOW, max_retries=max_retries)


# Специализированные функции для асинхронной обработки
class BackgroundTasks:
    """Класс для фоновых задач PandaPal"""

    @staticmethod
    @async_task(priority=TaskPriority.LOW)
    def cleanup_old_messages(user_id: int, older_than_days: int = 30):
        """Очистка старых сообщений пользователя"""
        from datetime import datetime, timedelta

        from bot.database import get_db
        from bot.models import ChatHistory

        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        with get_db() as db:
            deleted_count = (
                db.query(ChatHistory)
                .filter(
                    ChatHistory.user_telegram_id == user_id, ChatHistory.timestamp < cutoff_date
                )
                .delete()
            )

            db.commit()
            logger.info(f"🧹 Очищено {deleted_count} старых сообщений для пользователя {user_id}")

    @staticmethod
    @high_priority_task()
    def send_parent_notification(parent_id: int, message: str, child_id: int):
        """Отправка уведомления родителю"""
        # Здесь можно добавить отправку уведомления через Telegram API
        logger.info(f"📢 Уведомление родителю {parent_id}: {message} (ребенок: {child_id})")

    @staticmethod
    @async_task(priority=TaskPriority.NORMAL)
    def generate_analytics_report(user_id: int, period_days: int = 7):
        """Генерация аналитического отчета"""
        # Здесь можно добавить генерацию детального отчета
        logger.info(f"📊 Генерация отчета для пользователя {user_id} за {period_days} дней")

    @staticmethod
    @low_priority_task()
    def backup_user_data(user_id: int):
        """Резервное копирование данных пользователя"""
        # Здесь можно добавить создание бэкапа
        logger.info(f"💾 Создание резервной копии для пользователя {user_id}")


# Утилиты для работы с асинхронным процессором
async def wait_for_task(task_id: str, timeout: int = 300) -> Any:
    """
    Ожидание завершения задачи

    Args:
        task_id: ID задачи
        timeout: Таймаут ожидания в секундах

    Returns:
        Результат задачи

    Raises:
        TimeoutError: Если задача не завершилась в срок
    """
    start_time = datetime.utcnow()

    while True:
        status = async_processor.get_task_status(task_id)

        if status == TaskStatus.COMPLETED:
            return async_processor.get_task_result(task_id)
        elif status == TaskStatus.FAILED:
            return async_processor.get_task_result(task_id)  # Это вызовет исключение
        elif status == TaskStatus.CANCELLED:
            raise RuntimeError("Задача была отменена")

        if datetime.utcnow() - start_time > timedelta(seconds=timeout):
            raise TimeoutError(f"Задача {task_id} не завершилась в срок")

        await asyncio.sleep(1)


def get_processor_stats() -> Dict[str, Any]:
    """Получить статистику процессора"""
    return async_processor.get_stats()
