import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

from models.database import Database
from middlewares.language_loader import LanguageMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware

from handlers import start_handler, sell_handler, admin_handler, support_handler, fallback_handler

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").split(",") if x.strip().isdigit()]
CHANNEL_ID = os.getenv('CHANNEL_ID', '@TeleTradeET')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data.db')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0)) if os.getenv('LOG_CHANNEL_ID') else None
BASE_URL = os.getenv('BASE_URL', '')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')

db_path = DATABASE_URL.replace('sqlite:///', '')
db = Database(db_path)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def on_startup():
    await db.init_db()
    logger.info("Database initialized")


async def on_shutdown():
    logger.info("Bot shutting down")


def setup_handlers(dp: Dispatcher, db, bot):
    dp.include_router(start_handler.router)
    dp.include_router(sell_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(support_handler.router)
    dp.include_router(fallback_handler.router)

    language_middleware = LanguageMiddleware(db)
    rate_limit_middleware = RateLimitMiddleware(rate_limit=1)
    error_middleware = ErrorHandlerMiddleware(bot, LOG_CHANNEL_ID)

    dp.message.middleware(language_middleware)
    dp.callback_query.middleware(language_middleware)

    dp.message.middleware(rate_limit_middleware)
    dp.callback_query.middleware(rate_limit_middleware)

    dp.message.middleware(error_middleware)
    dp.callback_query.middleware(error_middleware)

    dp['db'] = db
    dp['bot'] = bot


async def health_check(request):
    return web.Response(text="OK")


async def start_webhook():
    await on_startup()

    setup_handlers(dp, db, bot)

    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info(f"Webhook set to: {webhook_url}")

    app = web.Application()
    app.router.add_get('/health', health_check)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    return app


async def start_polling():
    await on_startup()

    setup_handlers(dp, db, bot)

    logger.info("Starting bot in polling mode...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown()


if __name__ == '__main__':
    if '--polling' in sys.argv:
        asyncio.run(start_polling())
    else:
        app = asyncio.run(start_webhook())
        port = int(os.getenv('PORT', 8080))
        web.run_app(app, host='0.0.0.0', port=port)
try:
    app = asyncio.run(start_webhook())
except RuntimeError:
    # Sometimes asyncio.run inside a running loop fails (like in Docker build), 
    # fallback to creating app manually
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(start_webhook())