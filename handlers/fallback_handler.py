from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def unknown_message(message: Message, lang_data: dict):
    await message.answer(lang_data['unknown_command'])
