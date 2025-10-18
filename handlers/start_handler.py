from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
import os
from typing import Dict
from config import ADMIN_ID
router = Router()

# --- Admin IDs (comma-separated in .env) ---

def is_admin(user_id: int) -> bool:
    print('the user is an admin so he need to do it.')
    print(user_id in ADMIN_ID)
    return user_id in ADMIN_ID


def get_main_keyboard(lang_data: Dict, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Returns the main menu keyboard, customized for regular users or admins.
    """

    # --- Base User Keyboard Structure ---
    user_keyboard_rows = [
        [
            KeyboardButton(text=lang_data['main_menu_home']),
            KeyboardButton(text=lang_data['main_menu_sell'])
        ],
        [
            KeyboardButton(text=lang_data['main_menu_submissions']),
            KeyboardButton(text=lang_data['main_menu_support'])
        ],
        [
            KeyboardButton(text=lang_data['main_menu_faq']),
            KeyboardButton(text=lang_data['main_menu_language'])
        ]
    ]

    if is_admin:
        # --- Admin Keyboard (Admin Panel added to the top row) ---
        admin_panel_button = KeyboardButton(
            text=lang_data.get('main_menu_admin_panel', '🔑 Admin Panel')
        )
        full_keyboard_rows = [[admin_panel_button]]
        full_keyboard_rows.extend(user_keyboard_rows)
        print('the users button are one the way niggae')
        return ReplyKeyboardMarkup(keyboard=full_keyboard_rows, resize_keyboard=True)
       

    return ReplyKeyboardMarkup(keyboard=user_keyboard_rows, resize_keyboard=True)



def get_admin_panel_keyboard(lang_data: Dict) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=lang_data['admin_manage_submissions']),
            KeyboardButton(text=lang_data['admin_payments']),
        ],
            [KeyboardButton(text=lang_data['admin_stats_btn']),
            KeyboardButton(text=lang_data['admin_export']),
            ],
            [
                KeyboardButton(text=lang_data['admin_broadcast']),
            KeyboardButton(text=lang_data['admin_back'])
            ]
        ],
        resize_keyboard=True
    )


# --- START COMMAND ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db, lang_data: dict):
    user = await db.get_user(message.from_user.id)

    if not user:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="English", callback_data="lang_en")],
            [InlineKeyboardButton(text="አማርኛ (Amharic)", callback_data="lang_am")]
        ])
        await message.answer(
            "Welcome! / እንኳን ደህና መጡ!\n\n" + lang_data['select_language'],
            reply_markup=keyboard
        )
    else:
        if not user.get('joined_channel'):
            channel_id = os.getenv('CHANNEL_ID', '@TeleTradeET')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=lang_data['join_channel_button'],
                    url=f"https://t.me/{channel_id.replace('@', '')}"
                )],
                [InlineKeyboardButton(
                    text=lang_data['verify_join_button'],
                    callback_data="verify_join"
                )]
            ])
            await message.answer(lang_data['join_channel_required'], reply_markup=keyboard)
        else:
            await message.answer(
                lang_data['welcome'],
                reply_markup=get_main_keyboard(lang_data, is_admin=is_admin(message.from_user.id))
            )


# --- LANGUAGE SELECTION ---
@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, db, lang_data: dict):
    lang_code = callback.data.split('_')[1]

    await db.create_user(
        callback.from_user.id,
        callback.from_user.username or str(callback.from_user.id),
        lang_code
    )

    await callback.answer()

    channel_id = os.getenv('CHANNEL_ID', '@TeleTradeET')

    from middlewares.language_loader import LanguageMiddleware
    middleware = LanguageMiddleware(db)
    lang_data = middleware.languages.get(lang_code, middleware.languages['en'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=lang_data['join_channel_button'],
            url=f"https://t.me/{channel_id.replace('@', '')}"
        )],
        [InlineKeyboardButton(
            text=lang_data['verify_join_button'],
            callback_data="verify_join"
        )]
    ])

    await callback.message.edit_text(lang_data['join_channel_required'], reply_markup=keyboard)


# --- VERIFY CHANNEL JOIN ---
@router.callback_query(F.data == "verify_join")
async def verify_channel_join(callback: CallbackQuery, db, bot, lang_data: dict):
    channel_id = os.getenv('CHANNEL_ID', '@TeleTradeET')

    try:
        member = await bot.get_chat_member(channel_id, callback.from_user.id)

        if member.status in ['member', 'administrator', 'creator']:
            await db.update_user_channel_status(callback.from_user.id, True)
            await callback.answer(lang_data['verified_success'], show_alert=True)
            await callback.message.delete()
            await callback.message.answer(
                lang_data['welcome'],
                reply_markup=get_main_keyboard(lang_data, is_admin=is_admin(callback.from_user.id))
            )
        else:
            await callback.answer(lang_data['not_joined_yet'], show_alert=True)
    except Exception:
        await callback.answer(lang_data['not_joined_yet'], show_alert=True)


# --- LANGUAGE COMMAND ---
@router.message(Command("language"))
@router.message(F.text.in_(['🌐 Language', '🌐 ቋንቋ']))
async def cmd_language(message: Message, db, lang_data: dict):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="change_lang_en")],
        [InlineKeyboardButton(text="አማርኛ (Amharic)", callback_data="change_lang_am")]
    ])
    await message.answer(lang_data['select_language'], reply_markup=keyboard)


@router.callback_query(F.data.startswith("change_lang_"))
async def change_language(callback: CallbackQuery, db):
    lang_code = callback.data.split('_')[-1]
    await db.update_user_language(callback.from_user.id, lang_code)

    from middlewares.language_loader import LanguageMiddleware
    middleware = LanguageMiddleware(db)
    lang_data = middleware.languages.get(lang_code, middleware.languages['en'])

    await callback.answer(lang_data['language_changed'], show_alert=True)
    await callback.message.delete()
    await callback.message.answer(
        lang_data['welcome'],
        reply_markup=get_main_keyboard(lang_data, is_admin=is_admin(callback.from_user.id))
    )


# --- HOME MENU ---
@router.message(F.text.in_(['🏠 Home', '🏠 መነሻ']))
async def home_menu(message: Message, lang_data: dict):
    await message.answer(
        lang_data['welcome'],
        reply_markup=get_main_keyboard(lang_data, is_admin=is_admin(message.from_user.id))
    )



@router.message(F.text.in_(['🔑 Admin Panel']))
async def open_admin_panel(message: Message, lang_data: dict):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ You are not authorized to access the admin panel.")
        return
    await message.answer("🛠 Admin Panel", reply_markup=get_admin_panel_keyboard(lang_data))

@router.message(F.text.in_(['⬅️ Back to Main']))
async def back_to_main(message: Message, lang_data: dict):
    await message.answer(
        lang_data['welcome'],
        reply_markup=get_main_keyboard(lang_data, is_admin=is_admin(message.from_user.id))
    )
