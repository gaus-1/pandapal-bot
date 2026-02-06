"""
Сервис для работы с платежами через ЮKassa.

Обеспечивает создание платежей, обработку webhook уведомлений
и управление платежными транзакциями для Premium подписок.
"""

import asyncio
import hashlib
import hmac
import uuid

from loguru import logger
from yookassa import Configuration, Payment
from yookassa.domain.exceptions import ApiError

from bot.config import settings


class PaymentService:
    """
    Сервис управления платежами через ЮKassa.

    Обеспечивает:
    - Создание платежей для Premium подписок
    - Обработку webhook уведомлений от ЮKassa
    - Валидацию платежей и активацию подписок
    - Поддержку чеков для самозанятых
    """

    # Тарифный план (только месяц 299 ₽)
    PLANS = {
        "month": {"name": "Premium на месяц", "price": 299.00, "days": 30},
    }

    def __init__(self):
        """Инициализация сервиса платежей."""
        # Настройка ЮKassa (тестовый или продакшн режим)
        # ВАЖНО: Переинициализируем Configuration при каждом создании сервиса
        # чтобы использовать актуальные настройки (на случай изменения переменных окружения)
        self._update_configuration()

    def _update_configuration(self):
        """Обновить конфигурацию ЮKassa из настроек."""
        shop_id = settings.active_yookassa_shop_id
        secret_key = settings.active_yookassa_secret_key

        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key

        mode_text = "ТЕСТОВЫЙ" if settings.yookassa_test_mode else "ПРОДАКШН"
        logger.info(f"💳 ЮKassa инициализирован в режиме {mode_text}: shop_id={shop_id}")

        if not shop_id or not secret_key:
            logger.error(
                f"❌ ЮKassa не настроен ({mode_text}): "
                f"shop_id={'установлен' if shop_id else 'ОТСУТСТВУЕТ'}, "
                f"secret_key={'установлен' if secret_key else 'ОТСУТСТВУЕТ'}"
            )
            if settings.yookassa_test_mode:
                logger.error(
                    "❌ Для тестового режима нужны переменные окружения в Railway: "
                    "YOOKASSA_TEST_MODE=true, YOOKASSA_TEST_SHOP_ID=1242170, YOOKASSA_TEST_SECRET_KEY=<ключ из ЛК ЮKassa>"
                )
                logger.error(
                    "📋 Получить ключ: Личный кабинет ЮKassa → Настройки → Секретный ключ (для тестового магазина)"
                )

        # Timeout для YooKassa API вызовов (30 секунд)
        self._api_timeout = 30.0

    @staticmethod
    def verify_webhook_signature(request_body: str, signature: str | None) -> bool:
        """
        Верифицировать подпись webhook от ЮKassa.

        Args:
            request_body: Тело запроса (JSON строка)
            signature: Подпись из заголовка X-Yookassa-Signature

        Returns:
            bool: True если подпись валидна
        """
        # В тестовом режиме разрешаем webhook без подписи (для удобства тестирования)
        # В продакшене подпись обязательна!
        if settings.yookassa_test_mode and not signature:
            logger.warning(
                "⚠️ Webhook без подписи в ТЕСТОВОМ режиме. "
                "Разрешаем для тестирования, но рекомендуется включить подпись в ЛК ЮKassa."
            )
            return True  # Разрешаем в тестовом режиме

        if not signature:
            logger.error(
                "❌ Webhook без подписи в ПРОДАКШН режиме - ОТКЛОНЯЕМ! "
                "Проверь настройки webhook в личном кабинете YooKassa - должна быть включена подпись."
            )
            return False

        secret_key = settings.active_yookassa_secret_key
        if not secret_key:
            logger.error("❌ Secret key не настроен для верификации подписи")
            return False

        try:
            import base64

            # Вычисляем ожидаемую подпись
            # YooKassa использует HMAC-SHA256 с secret_key в качестве ключа
            # Подпись приходит в формате Base64 (по документации YooKassa)
            hmac_signature = hmac.new(
                secret_key.encode("utf-8"),
                request_body.encode("utf-8"),
                hashlib.sha256,
            ).digest()

            # Конвертируем в Base64 для сравнения
            expected_signature = base64.b64encode(hmac_signature).decode("utf-8")

            # Сравниваем подписи безопасным способом (case-sensitive)
            is_valid = hmac.compare_digest(expected_signature, signature)
            if not is_valid:
                logger.warning(
                    f"⚠️ Невалидная подпись webhook: получено={signature[:30]}..., "
                    f"ожидалось={expected_signature[:30]}... "
                    "Проверь, что YOOKASSA_TEST_SECRET_KEY (для тестового режима) "
                    "совпадает с ключом в личном кабинете YooKassa."
                )

            return is_valid
        except Exception as e:
            logger.error(f"❌ Ошибка верификации подписи: {e}", exc_info=True)
            return False

    async def create_payment(
        self,
        telegram_id: int,
        plan_id: str,
        user_email: str | None = None,
        user_phone: str | None = None,
    ) -> dict:
        """
        Создать платеж через ЮKassa.

        Args:
            telegram_id: Telegram ID пользователя
            plan_id: ID тарифного плана ('month')
            user_email: Email пользователя (для чека)
            user_phone: Телефон пользователя (для чека)

        Returns:
            dict: Данные платежа с confirmation_url (совместимость с существующим кодом)

        Raises:
            ValueError: Если plan_id невалидный
            ApiError: Если ошибка API ЮKassa
        """
        # Обновляем конфигурацию перед каждым запросом (на случай изменения настроек)
        self._update_configuration()

        if plan_id not in self.PLANS:
            raise ValueError(f"Invalid plan_id: {plan_id}")

        plan = self.PLANS[plan_id]

        # Генерируем уникальный idempotence_key для защиты от дубликатов
        idempotence_key = str(uuid.uuid4())

        # Формируем описание платежа
        description = f"PandaPal Premium: {plan['name']}"

        # Подготовка данных платежа
        payment_data = {
            "amount": {
                "value": f"{plan['price']:.2f}",
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url,
            },
            "capture": True,  # Автоматическое списание
            "description": description,
            "metadata": {
                "telegram_id": str(telegram_id),
                "plan_id": plan_id,
            },
            # merchant_customer_id используется для идентификации пользователя
            # Короткое имя магазина настраивается в личном кабинете ЮKassa
            "merchant_customer_id": str(telegram_id),
        }

        # Для подписки month - сохраняем метод оплаты для автоплатежа
        # В ТЕСТОВОМ РЕЖИМЕ автоплатежи работают автоматически (без активации менеджером)
        # В ПРОДАКШН режиме автоплатежи должны быть активированы менеджером ЮKassa
        if plan_id == "month":
            if settings.yookassa_test_mode:
                # В тестовом режиме автоплатежи работают автоматически
                payment_data["save_payment_method"] = True
                logger.info(
                    f"💳 ТЕСТОВЫЙ РЕЖИМ: Сохранение метода оплаты включено для плана {plan_id} "
                    f"(автоплатежи работают в тестовом режиме)"
                )
            elif settings.yookassa_recurring_enabled:
                # В продакшн режиме только если активировано
                payment_data["save_payment_method"] = True
                logger.info(
                    f"💳 ПРОДАКШН: Сохранение метода оплаты включено для плана {plan_id} "
                    f"(автоплатежи активированы)"
                )
            else:
                logger.info(
                    f"ℹ️ Сохранение метода оплаты отключено для плана {plan_id} "
                    f"(автоплатежи не активированы в ЮKassa)"
                )

        # Добавляем чек для самозанятого (если ИНН указан)
        if settings.yookassa_inn:
            # Для анонимных платежей (без email/phone) используем no-reply email
            # Это требование 54-ФЗ - чек должен быть отправлен
            customer_email = user_email or "no-reply@pandapal.ru"
            customer_phone = user_phone

            receipt_data = {
                "customer": {"email": customer_email},
                "items": [
                    {
                        "description": plan["name"],
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{plan['price']:.2f}",
                            "currency": "RUB",
                        },
                        "vat_code": 1,  # НДС не облагается (для самозанятых)
                    }
                ],
                "tax_system_code": 1,  # Общая система налогообложения (для самозанятых)
            }

            # Если есть телефон - добавляем и его
            if customer_phone:
                receipt_data["customer"]["phone"] = customer_phone

            payment_data["receipt"] = receipt_data

        try:
            # Создаем платеж через ЮKassa API с timeout
            payment = await asyncio.wait_for(
                asyncio.to_thread(Payment.create, payment_data, idempotence_key),
                timeout=self._api_timeout,
            )

            logger.info(
                f"✅ Платеж создан: payment_id={payment.id}, "
                f"user={telegram_id}, plan={plan_id}, amount={plan['price']} RUB"
            )

            return {
                "payment_id": payment.id,
                "status": payment.status,
                "confirmation_url": (
                    payment.confirmation.confirmation_url if payment.confirmation else None
                ),
                "amount": {
                    "value": float(payment.amount.value),
                    "currency": payment.amount.currency,
                },
            }

        except TimeoutError as e:
            logger.error(f"❌ Timeout при создании платежа ЮKassa (>{self._api_timeout}s)")
            raise TimeoutError(f"YooKassa API timeout after {self._api_timeout}s") from e
        except ApiError as e:
            # Логируем детали ошибки для отладки
            error_message = str(e)
            error_code = getattr(e, "code", None) or getattr(e, "status_code", None)

            # Детальное логирование для 401 ошибки
            if "401" in error_message or error_code == 401:
                logger.error(f"❌ Ошибка аутентификации ЮKassa (401): {error_message}")
                logger.error(
                    f"🔑 Проверь настройки: "
                    f"shop_id={settings.active_yookassa_shop_id}, "
                    f"secret_key={'установлен' if settings.active_yookassa_secret_key else 'ОТСУТСТВУЕТ'}"
                )
                if settings.yookassa_test_mode:
                    logger.error(
                        "🔑 Для тестового режима проверь переменные окружения: "
                        "YOOKASSA_TEST_MODE=true, YOOKASSA_TEST_SHOP_ID=1242170, YOOKASSA_TEST_SECRET_KEY=<ключ из ЛК ЮKassa>"
                    )
                raise ValueError(
                    "Ошибка аутентификации ЮKassa: проверь YOOKASSA_TEST_SECRET_KEY для тестового режима"
                ) from e
            elif "403" in error_message or error_code == 403 or "Forbidden" in error_message:
                logger.error(
                    f"❌ ЮKassa вернул 403 Forbidden. "
                    f"Возможные причины:\n"
                    f"  1. Автоплатежи не активированы (если plan={plan_id} и save_payment_method=True)\n"
                    f"  2. Неверные shop_id или secret_key\n"
                    f"  3. Магазин не настроен для приема платежей\n"
                    f"  Проверьте настройки в личном кабинете ЮKassa"
                )
            else:
                logger.error(f"❌ Ошибка создания платежа ЮKassa: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при создании платежа: {e}", exc_info=True)
            raise

    async def get_payment_status(self, payment_id: str) -> dict | None:
        """
        Получить статус платежа.

        Args:
            payment_id: ID платежа в ЮKassa

        Returns:
            dict: Данные платежа или None если не найден
        """
        try:
            # Получаем статус платежа через ЮKassa API с timeout
            payment = await asyncio.wait_for(
                asyncio.to_thread(Payment.find_one, payment_id),
                timeout=self._api_timeout,
            )

            return {
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": {
                    "value": float(payment.amount.value),
                    "currency": payment.amount.currency,
                },
                "payment_metadata": getattr(payment, "payment_metadata", None) or {},
            }

        except TimeoutError:
            logger.error(
                f"❌ Timeout при получении статуса платежа {payment_id} (>{self._api_timeout}s)"
            )
            return None
        except ApiError as e:
            logger.error(f"❌ Ошибка получения статуса платежа {payment_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при получении платежа: {e}", exc_info=True)
            return None

    def process_webhook(self, webhook_data: dict) -> dict | None:
        """
        Обработать webhook уведомление от ЮKassa.

        Args:
            webhook_data: Данные webhook от ЮKassa

        Returns:
            dict: Результат обработки или None если событие не требует обработки
        """
        try:
            event = webhook_data.get("event")
            payment_object = webhook_data.get("object", {})

            # Обрабатываем только события, требующие активации подписки
            # payment.waiting_for_capture - не активируем подписку (платеж еще не завершен)
            # payment.succeeded - активируем подписку
            # payment.canceled - не активируем подписку (платеж отменен)
            # refund.succeeded - не активируем подписку (это возврат, не платеж)
            if event not in ("payment.succeeded",):
                logger.info(f"ℹ️ Событие {event} не требует активации подписки (игнорируем)")
                return None

            payment_id = payment_object.get("id")
            metadata = payment_object.get("metadata", {})
            telegram_id_str = metadata.get("telegram_id")
            plan_id = metadata.get("plan_id")

            if not telegram_id_str or not plan_id:
                logger.warning(
                    f"⚠️ Отсутствуют telegram_id или plan_id в метаданных платежа {payment_id}"
                )
                return None

            telegram_id = int(telegram_id_str)

            logger.info(
                f"💰 Webhook: платеж успешен payment_id={payment_id}, "
                f"user={telegram_id}, plan={plan_id}"
            )

            return {
                "payment_id": payment_id,
                "telegram_id": telegram_id,
                "plan_id": plan_id,
                "amount": payment_object.get("amount", {}),
            }

        except (ValueError, KeyError) as e:
            logger.error(f"❌ Ошибка парсинга webhook данных: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка обработки webhook: {e}", exc_info=True)
            return None
