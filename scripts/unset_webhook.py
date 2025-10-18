import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')


async def unset_webhook():
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook removed successfully")

        webhook_info = await bot.get_webhook_info()
        print(f"\nWebhook Info:")
        print(f"URL: {webhook_info.url}")
    except Exception as e:
        print(f"❌ Error removing webhook: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(unset_webhook())
