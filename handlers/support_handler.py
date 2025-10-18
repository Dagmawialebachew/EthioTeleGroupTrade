from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os

router = Router()


@router.message(Command("support"))
@router.message(F.text.in_(['💬 Support', '💬 ድጋፍ']))
async def support_menu(message: Message, lang_data: dict):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_data['contact_admin_button'], url="https://t.me/ethioteletrader")]
    ])
    await message.answer(lang_data['support_message'], reply_markup=keyboard)


@router.message(Command("faq"))
@router.message(F.text.in_(['❓ FAQ', '❓ ጥያቄዎች']))
async def faq_menu(message: Message, lang_data: dict):
    faq_text = lang_data['faq_title']
    faq_text += lang_data['faq_pricing']
    faq_text += lang_data['faq_transfer']
    faq_text += lang_data['faq_payout']
    faq_text += lang_data['faq_contact']

    await message.answer(faq_text)
