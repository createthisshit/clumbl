import logging
import sys
import uuid
import hmac
import hashlib
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from urllib.parse import urlencode

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Настройки
TOKEN = "7241683107:AAEG6RCRM4Ar1sDYpTV8BsaHfGUj2WXobhI"  # Замени на токен от @BotFather
YOOMONEY_WALLET = "4100118178122985"  # Замени на номер кошелька YooMoney (41001...)
YOOMONEY_SECRET = "CoqQlgE3E5cTzyAKY1LSiLU1"  # Замени на секрет для уведомлений (из настроек YooMoney)
WEBHOOK_URL = "https://shocked-charin-createthisshit-620de28a.koyeb.app/"  # Замени на URL от Koyeb (например, https://your-app.koyeb.app/webhook)

# Инициализация бота
try:
    bot = Bot(token=TOKEN)
    logger.info("Бот инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации бота: {e}")
    sys.exit(1)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    try:
        user_id = str(message.from_user.id)
        logger.info(f"Получена команда /start от user_id={user_id}")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="Пополнить", callback_data="pay"))
        welcome_text = (
            "Тариф: фулл\n"
            "Стоимость: 500.00 🇷🇺RUB\n"
            "Срок действия: 1 месяц\n\n"
            "Вы получите доступ к следующим ресурсам:\n"
            "• Мой кайф (канал)"
        )
        await message.answer(welcome_text, reply_markup=keyboard)
        logger.info(f"Отправлен ответ на /start для user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("Произошла ошибка, попробуйте позже.")

# Обработчик команды /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    try:
        user_id = str(message.from_user.id)
        logger.info(f"Получена команда /help от user_id={user_id}")
        help_text = (
            "Доступные команды:\n"
            "/start - Начать и получить ссылку на оплату\n"
            "/help - Показать эту помощь\n"
            "/info - Информация о боте\n"
            "/pay - Создать платёж"
        )
        await message.answer(help_text)
        logger.info(f"Отправлен ответ на /help для user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /help: {e}")
        await message.answer("Произошла ошибка, попробуйте позже.")

# Обработчик команды /info
@dp.message_handler(commands=['info'])
async def info_command(message: types.Message):
    try:
        user_id = str(message.from_user.id)
        logger.info(f"Получена команда /info от user_id={user_id}")
        info_text = "Это бот для подписки на канал 'Мой кайф'. Используйте /start или /pay для оплаты."
        await message.answer(info_text)
        logger.info(f"Отправлен ответ на /info для user_id={user_id}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /info: {e}")
        await message.answer("Произошла ошибка, попробуйте позже.")

# Обработчик команды /pay и кнопки "Пополнить"
@dp.message_handler(commands=['pay'])
@dp.callback_query_handler(text="pay")
async def pay_command(message_or_callback: types.Message | types.CallbackQuery):
    try:
        if isinstance(message_or_callback, types.Message):
            user_id = str(message_or_callback.from_user.id)
            chat_id = message_or_callback.chat.id
        else:
            user_id = str(message_or_callback.from_user.id)
            chat_id = message_or_callback.message.chat.id

        logger.info(f"Получена команда /pay от user_id={user_id}")

        # Создание платёжной ссылки
        payment_label = str(uuid.uuid4())
        payment_params = {
            "quickpay-form": "shop",
            "paymentType": "AC",
            "targets": f"Оплата подписки для user_id={user_id}",
            "sum": 500.00,
            "label": payment_label,
            "receiver": YOOMONEY_WALLET,
            "successURL": "https://t.me/your_bot_username"  # Замени на ссылку на бота
        }
        payment_url = f"https://yoomoney.ru/quickpay/confirm.xml?{urlencode(payment_params)}"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="Оплатить", url=payment_url))
        await bot.send_message(chat_id, "Перейдите по ссылке для оплаты:", reply_markup=keyboard)
        logger.info(f"Отправлена ссылка на оплату для user_id={user_id}, label={payment_label}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /pay: {e}")
        await bot.send_message(chat_id, "Произошла ошибка при создании платежа, попробуйте позже.")

# Webhook для YooMoney уведомлений
@dp.message_handler(content_types=['webhook'])
async def handle_yoomoney_webhook(update: dict):
    try:
        # Проверка подписи
        notification_type = update.get("notification_type")
        amount = update.get("amount")
        label = update.get("label")
        datetime = update.get("datetime")
        sender = update.get("sender")
        codepro = update.get("codepro", "false")
        currency = update.get("currency")
        sha1_hash = update.get("sha1_hash")

        check_string = (
            f"{notification_type}&{amount}&{currency}&{label}&"
            f"{datetime}&{sender}&{codepro}&{YOOMONEY_WALLET}&{YOOMONEY_SECRET}"
        )
        calculated_hash = hmac.new(
            YOOMONEY_SECRET.encode(), check_string.encode(), hashlib.sha1
        ).hexdigest()

        if calculated_hash != sha1_hash:
            logger.error("Неверная подпись уведомления")
            return

        if notification_type == "p2p-incoming":
            user_id = None
            # Предполагаем, что label содержит user_id (можно улучшить)
            # В реальном проекте храни label:user_id в базе данных
            logger.info(f"Получено уведомление об оплате: amount={amount}, label={label}")
            await bot.send_message(user_id or 123456789, f"Оплата на сумму {amount} RUB получена! Доступ к каналу предоставлен.")
            logger.info(f"Отправлено уведомление об оплате для label={label}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике webhook: {e}")

# Запуск бота
async def on_shutdown(dp):
    logger.info("Закрытие бота")
    await bot.close()

def on_startup(_):
    logger.info("Бот запущен")

if __name__ == "__main__":
    try:
        logger.info("Запуск polling")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
    except Exception as e:
        logger.error(f"Ошибка запуска polling: {e}")
        sys.exit(1)
