import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BASE_URL = os.getenv('BASE_URL')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')


async def set_webhook():
    bot = Bot(token=BOT_TOKEN)
    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"

    try:
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        print(f"✅ Webhook set successfully to: {webhook_url}")

        webhook_info = await bot.get_webhook_info()
        print(f"\nWebhook Info:")
        print(f"URL: {webhook_info.url}")
        print(f"Pending updates: {webhook_info.pending_update_count}")
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(set_webhook())
