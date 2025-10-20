from aiogram import Router, F, Bot
from aiogram.filters import Command
from config import ADMIN_ID
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from handlers.sell_handler import SellStates
from handlers.start_handler import get_admin_panel_keyboard, get_main_keyboard
from utils.price_engine import get_month_name
import os
import csv
from datetime import datetime
from aiogram.fsm.storage.base import StorageKey # Already imported at the top!
router = Router()

import logging

logger = logging.getLogger(__name__)
class AdminStates(StatesGroup):
    waiting_rejection_reason = State()
    waiting_payment_screenshot = State()   # NEW


def format_admin_card(submission_id, username, title, members, month, year, price, status, lang_data):
    return lang_data['admin_submission_card'].format(
        id=submission_id,
        username=username,
        title=title,
        members=members,
        month=month,
        year=year,
        price=price,
        status=status
    )

print(f"Loaded ADMIN_IDS: {ADMIN_ID}")

def is_admin(user_id: int) -> bool:
    """
Check if a user is an admins.
    Supports multiple IDs from .env (ADMIN_IDS).
    """
    return user_id in ADMIN_ID
@router.message(Command("payments"))
async def list_ready_for_payment(message: Message, db, lang_data: dict):
    if not is_admin(message.from_user.id):
        return

    submissions = await db.get_submissions_by_status("ready_for_payment")

    if not submissions:
        await message.answer(lang_data["no_ready_for_payment"])
        return

    for sub in submissions:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=lang_data["admin_mark_as_paid"],
                callback_data=f"mark_paid_{sub['id']}"
            )]
        ])

        caption = (
            f"💰 Submission #{sub['id']}\n"
            f"👤 Seller: @{sub.get('seller_username', 'Unknown')}\n"
            f"💵 Price: {sub['price']} ETB\n"
            f"📌 Method: {sub.get('payment_method', '-')}\n"
            f"👤 Account: {sub.get('payment_account', '-')}\n"
        )

        # If seller uploaded a transfer screenshot, send it with caption
        if sub.get("transfer_screenshot_file_id"):
            try:
                await message.answer_photo(
                    photo=sub["transfer_screenshot_file_id"],
                    caption=caption,
                    reply_markup=kb
                )
            except Exception:
                # fallback if file_id is invalid
                await message.answer(caption, reply_markup=kb)
        else:
            # no screenshot, just send text
            await message.answer(caption, reply_markup=kb)

@router.message(Command("panel"))
async def admin_panel(message: Message, db, lang_data: dict):
    if not is_admin(message.from_user.id):
        return

    submissions = await db.get_pending_submissions(10)

    if not submissions:
        await message.answer(lang_data['admin_panel_title'] + "\n\n" + lang_data['admin_no_pending'])
        return

    response = lang_data['admin_panel_title']

    for sub in submissions[:5]:
        card = format_admin_card(
            sub['id'],
            sub['seller_username'],
            sub['group_title'],
            sub['member_count'],
            sub['created_month'],
            sub['created_year'],
            sub['price'],
            sub['status'],
            lang_data
        )
        response += card

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=lang_data['admin_view_screenshot'], callback_data=f"view_screenshot_{sub['id']}")],
            [
                InlineKeyboardButton(text=lang_data['admin_confirm_transfer'], callback_data=f"confirm_transfer_{sub['id']}"),
                InlineKeyboardButton(text=lang_data['admin_reject'], callback_data=f"reject_{sub['id']}")
            ],
            [InlineKeyboardButton(text=lang_data['admin_mark_paid'], callback_data=f"mark_paid_{sub['id']}")]
        ])

        await message.answer(card, reply_markup=keyboard)


@router.message(F.text.in_(['💰 Payments']))
async def payments_button(message: Message, db, lang_data: dict):
    # just call the same function as /payments
    await list_ready_for_payment(message, db, lang_data)

@router.message(F.text.in_(['📑 Manage Submissions']))
async def panel_button(message: Message, db, lang_data: dict):
    await admin_panel(message, db, lang_data)


@router.message(F.text.in_(['🔑 Admin Panel']))
async def open_admin_panel(message: Message, lang_data: dict):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ You are not authorized to access the admin panel.")
        return

    await message.answer(
        "🛠 Admin Panel",
        reply_markup=get_admin_panel_keyboard(lang_data)
    )


@router.message(F.text.in_(['⬅️ Back to Main']))
async def back_to_main(message: Message, lang_data: dict):
    await message.answer(
        lang_data['welcome'],
        reply_markup=get_main_keyboard(lang_data, is_admin=is_admin(message.from_user.id))
    )
    logging.getLogger(__name__)

# Helper: load target user's language pack
async def get_user_lang_data(db, user_id):
    user = await db.get_user(user_id)
    lang_code = (user.get("language") if user else "en") or "en"
    from middlewares.language_loader import LanguageMiddleware
    middleware = LanguageMiddleware(db)
    return middleware.languages.get(lang_code, middleware.languages["en"])


@router.callback_query(F.data.startswith("view_screenshot_"))
async def view_screenshot(callback: CallbackQuery, db, bot: Bot):
    submission_id = int(callback.data.split('_')[-1])
    submission = await db.get_submission(submission_id)

    if not submission or not submission.get("transfer_screenshot_file_id"):
        await callback.answer("Screenshot not found", show_alert=True)
        return

    await callback.answer()
    await bot.send_photo(
        callback.from_user.id,
        photo=submission["transfer_screenshot_file_id"],
        caption=f"Screenshot for submission #{submission_id}"
    )


@router.callback_query(F.data.startswith("confirm_transfer_"))
async def confirm_transfer(callback: CallbackQuery, db, bot: Bot, lang_data: dict, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    submission_id = int(callback.data.split('_')[-1])
    submission = await db.get_submission(submission_id)
    if not submission:
        await callback.answer("Submission not found", show_alert=True)
        return

    user_id = submission["user_id"]
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("User not found", show_alert=True)
        return

    # Update DB
    await db.update_submission(submission_id, {"status": "awaiting_payment_info"})
    await db.log_admin_action(callback.from_user.id, "confirm_transfer", submission_id)
    await callback.answer(lang_data["admin_transfer_confirmed"], show_alert=True)

    try:
        # Prepare FSM for seller
        user_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id, thread_id=None)
        user_state = FSMContext(storage=state.storage, key=user_key)
        await user_state.update_data(active_submission_id=submission_id)
        await user_state.set_state(SellStates.waiting_method_choice)
        await db.update_user_stage(user_id, "waiting_method_choice")

        # Load seller's language
        seller_lang = await get_user_lang_data(db, user_id)

        has_saved_details = user.get("payment_method") and user.get("payment_account")
        if has_saved_details:
            method, account = user["payment_method"], user["payment_account"]
            prompt_text = seller_lang["payment_method_choice_prompt"].format(
                price=submission["price"], method=method, account=account
            )
            user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=seller_lang["using_saved_details"], callback_data=f"use_saved_payment_{submission_id}")],
                [InlineKeyboardButton(text=seller_lang["change_payment_details"], callback_data="change_payment_details")],
                [InlineKeyboardButton(text=seller_lang["cancel_button"], callback_data="cancel_sell_process")]
            ])
        else:
            prompt_text = seller_lang["payment_enter_method_first"].format(price=submission["price"])
            user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=seller_lang["start_entering_details"], callback_data="change_payment_details")],
                [InlineKeyboardButton(text=seller_lang["cancel_button"], callback_data="cancel_sell_process")]
            ])

        await bot.send_message(user_id, prompt_text, reply_markup=user_keyboard)
    except Exception as e:
        logger.error(f"Error sending payment prompt to user {user_id}: {e}")

    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("reject_"))
async def start_reject(callback: CallbackQuery, state: FSMContext, lang_data: dict):
    if not is_admin(callback.from_user.id):
        return
    submission_id = int(callback.data.split('_')[-1])
    await state.update_data(reject_submission_id=submission_id)
    await state.set_state(AdminStates.waiting_rejection_reason)
    await callback.answer()
    await callback.message.answer(lang_data["admin_reject_reason"])


@router.message(AdminStates.waiting_rejection_reason)
async def receive_rejection_reason(message: Message, state: FSMContext, db, bot: Bot, lang_data: dict):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    submission_id = data.get("reject_submission_id")
    reason = message.text
    submission = await db.get_submission(submission_id)

    if submission:
        await db.update_submission(submission_id, {"status": "rejected", "admin_notes": reason})
        await db.log_admin_action(message.from_user.id, "reject", submission_id, reason)

        # Notify seller in their language
        seller_lang = await get_user_lang_data(db, submission["user_id"])
        try:
            await bot.send_message(
                submission["user_id"],
                seller_lang["submission_rejected"].format(reason=reason)
            )
        except Exception as e:
            logger.error(f"Error notifying seller of rejection: {e}")

        await message.answer(lang_data["admin_rejection_sent"])

    await state.clear()


@router.callback_query(F.data.startswith("mark_paid_"))
async def confirm_mark_paid(callback: CallbackQuery, db, lang_data: dict):
    if not is_admin(callback.from_user.id):
        return
    submission_id = int(callback.data.split('_')[-1])
    submission = await db.get_submission(submission_id)
    if not submission:
        await callback.answer("Submission not found", show_alert=True)
        return

    user = await db.get_user(submission["user_id"])
    username = user.get("username", "Unknown") if user else "Unknown"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=lang_data["admin_yes"], callback_data=f"confirm_paid_{submission_id}"),
        InlineKeyboardButton(text=lang_data["admin_no"], callback_data=f"cancel_paid_{submission_id}")
    ]])

    await callback.message.answer(
        lang_data["admin_confirm_payment"].format(id=submission_id, price=submission["price"], username=username),
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_paid_"))
async def mark_as_paid(callback: CallbackQuery, state: FSMContext, db, lang_data: dict):
    if not is_admin(callback.from_user.id):
        return
    submission_id = int(callback.data.split('_')[-1])
    submission = await db.get_submission(submission_id)
    if not submission:
        await callback.answer("Submission not found", show_alert=True)
        return

    await state.update_data(payment_submission_id=submission_id)
    await state.set_state(AdminStates.waiting_payment_screenshot)
    await callback.message.answer(lang_data["admin_upload_payment_proof"])
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_paid_"))
async def cancel_mark_paid(callback: CallbackQuery):
    await callback.answer("Cancelled", show_alert=True)
    await callback.message.delete()


@router.message(AdminStates.waiting_payment_screenshot, F.photo)
async def receive_payment_screenshot(message: Message, state: FSMContext, db, bot: Bot, lang_data: dict):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    submission_id = data.get("payment_submission_id")
    file_id = message.photo[-1].file_id

    await db.update_submission(submission_id, {"status": "paid", "admin_payment_screenshot": file_id})
    await db.log_admin_action(message.from_user.id, "mark_paid", submission_id, "Payment screenshot uploaded")

    submission = await db.get_submission(submission_id)
    if submission:
        seller_lang = await get_user_lang_data(db, submission["user_id"])
        try:
            await bot.send_message(
                submission["user_id"],
                seller_lang["payment_completed_with_proof"].format(price=submission["price"])
            )
            await bot.send_photo(
                submission["user_id"],
                file_id,
                caption=seller_lang["payment_proof_caption"]
            )
        except Exception as e:
            logger.error(f"Error notifying seller of payment: {e}")

    await message.answer(lang_data["admin_payment_marked"])
    await state.clear()


@router.message(Command("stats"))
async def admin_stats(message: Message, db, lang_data: dict):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_stats()

    response = lang_data['admin_stats'].format(
        total=stats['total_submissions'],
        pending=stats['pending'],
        approved=stats['approved'],
        paid=stats['paid'],
        total_birr=stats['total_birr_paid']
    )

    await message.answer(response)


@router.message(Command("export"))
async def export_submissions(message: Message, db, lang_data: dict):
    if not is_admin(message.from_user.id):
        return

    submissions = await db.get_pending_submissions(1000)

    csv_file = f'/tmp/submissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'user_id', 'username', 'group_title', 'group_link',
            'member_count', 'created_year', 'created_month', 'price',
            'status', 'payment_account', 'created_at'
        ])
        writer.writeheader()

        for sub in submissions:
            writer.writerow({
                'id': sub['id'],
                'user_id': sub['user_id'],
                'username': sub.get('seller_username', ''),
                'group_title': sub['group_title'],
                'group_link': sub['group_link'],
                'member_count': sub['member_count'],
                'created_year': sub['created_year'],
                'created_month': sub['created_month'],
                'price': sub['price'],
                'status': sub['status'],
                'payment_account': sub.get('payment_account', ''),
                'created_at': sub['created_at']
            })

    await message.answer_document(FSInputFile(csv_file), caption="Submissions Export")
    os.remove(csv_file)

# Handle "📊 Stats" button from reply keyboard
@router.message(F.text.in_(['📊 Stats', '📊 ስታቲስቲክስ']))
async def stats_button(message: Message, db, lang_data: dict):
    await admin_stats(message, db, lang_data)


# Handle "⬇️ Export" button if you add one to the panel
@router.message(F.text.in_(['⬇️ Export', '⬇️ ኤክስፖርት']))
async def export_button(message: Message, db, lang_data: dict):
    await export_submissions(message, db, lang_data)


@router.message(Command("pause"))
async def pause_accepting(message: Message, db):
    if not is_admin(message.from_user.id):
        return

    current = await db.get_config('pause_accepting')
    new_value = 'false' if current == 'true' else 'true'
    await db.set_config('pause_accepting', new_value)

    status = "paused" if new_value == 'true' else "resumed"
    await message.answer(f"Bot submissions {status}")


