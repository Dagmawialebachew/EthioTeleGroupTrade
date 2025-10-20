from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def unknown_message(message: Message, lang_data: dict):
    # Ignore group/supergroup chatter
    if message.chat.type in ["group", "supergroup"]:
        return

    # In private chats, respond with fallback
    await message.answer(lang_data['unknown_command'])
