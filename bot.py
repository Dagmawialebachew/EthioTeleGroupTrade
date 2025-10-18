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

# -------------------- Load config --------------------
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
PORT = int(os.getenv('PORT', 8080))

# -------------------- Initialize --------------------
db_path = DATABASE_URL.replace('sqlite:///', '')
db = Database(db_path)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# -------------------- Handlers & Middleware --------------------
def setup_handlers(dp: Dispatcher):
    dp.include_router(start_handler.router)
    dp.include_router(sell_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(support_handler.router)
    dp.include_router(fallback_handler.router)

    dp.message.middleware(LanguageMiddleware(db))
    dp.callback_query.middleware(LanguageMiddleware(db))
    dp.message.middleware(RateLimitMiddleware(rate_limit=1))
    dp.callback_query.middleware(RateLimitMiddleware(rate_limit=1))
    dp.message.middleware(ErrorHandlerMiddleware(bot, LOG_CHANNEL_ID))
    dp.callback_query.middleware(ErrorHandlerMiddleware(bot, LOG_CHANNEL_ID))

    dp['db'] = db
    dp['bot'] = bot

# -------------------- Startup / Shutdown --------------------
async def on_startup(app: web.Application):
    await db.init_db()
    logger.info("Database initialized")

    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info(f"Webhook set to: {webhook_url}")

async def on_shutdown(app: web.Application):
    await bot.session.close()
    logger.info("Bot session closed")

# -------------------- Health Check --------------------
async def health_check(request):
    return web.Response(text="OK")

# -------------------- ASGI App --------------------
def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_check)

    setup_handlers(dp)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_shutdown)

    return app

# -------------------- Polling Mode --------------------
async def start_polling():
    setup_handlers(dp)
    await db.init_db()
    logger.info("Starting bot in polling mode...")
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Polling stopped")

# -------------------- Entrypoint --------------------
if __name__ == "__main__":
    if "--polling" in sys.argv:
        asyncio.run(start_polling())
    else:
        app = create_app()
        web.run_app(app, host="0.0.0.0", port=PORT)
