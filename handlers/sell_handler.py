from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from utils.validators import resolve_group, validate_group_link, validate_image
from utils.price_engine import calculate_price, get_month_name
from datetime import datetime
import os

router = Router()


class SellStates(StatesGroup):
    waiting_group_link = State()
    waiting_bot_admin = State()
    # --- MANUAL DATE INPUT STATES ---
    waiting_creation_year = State()
    waiting_creation_month = State()
    # --------------------------------
    waiting_screenshot = State()
    
    # --- NEW STATES FOR REUSABLE PAYMENT FLOW ---
    waiting_method_choice = State()  # User sees saved details, chooses to use or change
    waiting_new_method = State()     # User types in the payment method (e.g., "Telebirr")
    waiting_new_account = State()    # User types in the account number (e.g., "09xxxxxxxx")
    # --------------------------------------------


@router.message(Command("sell"))
@router.message(F.text.in_(['💰 Sell My Group', '💰 ግሩፕ ለመሸጥ']))
async def start_sell(message: Message, state: FSMContext, db, lang_data: dict):
    paused = await db.get_config('pause_accepting')
    if paused == 'true':
        await message.answer(lang_data['pause_accepting'])
        return

    await state.set_state(SellStates.waiting_group_link)
    await db.update_user_stage(message.from_user.id, 'waiting_group_link')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
    ])

    await message.answer(lang_data['sell_start'], reply_markup=keyboard)


@router.message(SellStates.waiting_group_link)
async def receive_group_link(message: Message, state: FSMContext, db, bot: Bot, lang_data: dict):
    # Step 1: Validate the string format
    is_valid, username = validate_group_link(message.text)
    if not is_valid:
        await message.answer(lang_data['invalid_group_link'])
        return

    # Step 2: Confirm with Telegram API that it's a group/supergroup
    ok, chat = await resolve_group(bot, username)
    if not ok:
        await message.answer(lang_data['not_a_group'])
        return

    # Step 3: Save clean data into FSM
    await state.update_data(
        group_link=message.text.strip(),
        group_username=username,
        group_title=chat.title or username
    )

    # Step 4: Update FSM state and DB stage
    await state.set_state(SellStates.waiting_bot_admin)
    await db.update_user_stage(message.from_user.id, 'waiting_bot_admin')

    # Step 5: Build inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_data['bot_admin_added'], callback_data="check_admin")],
        [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
    ])

    # Step 6: Prompt user to add bot as admin
    await message.answer(lang_data['add_bot_admin'], reply_markup=keyboard)

@router.callback_query(F.data == "check_admin")
async def check_admin_status(callback: CallbackQuery, state: FSMContext, bot: Bot, db, lang_data: dict):
    await callback.answer(lang_data['checking_group'])

    data = await state.get_data()
    group_username = data.get('group_username')
    if not group_username:
        # No username stored → ask again
        await state.set_state(SellStates.waiting_group_link)
        await db.update_user_stage(callback.from_user.id, 'waiting_group_link')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
        ])
        await callback.message.edit_text(lang_data['ask_group_link_again'], reply_markup=keyboard)
        return

    group_ref = f"@{group_username}"

    try:
        chat = await bot.get_chat(group_ref)
        bot_member = await bot.get_chat_member(chat.id, bot.id)

        if bot_member.status not in ['administrator', 'creator']:
            # Still not admin → stay in waiting_bot_admin
            await state.set_state(SellStates.waiting_bot_admin)
            await db.update_user_stage(callback.from_user.id, 'waiting_bot_admin')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=lang_data['bot_admin_added_again'], callback_data="check_admin")],
                [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
            ])
            await callback.message.edit_text(lang_data['not_admin_yet'], reply_markup=keyboard)
            return

        # Bot is admin → proceed
        try:
            member_count = await bot.get_chat_member_count(chat.id)
        except Exception:
            member_count = None

        await state.update_data(group_title=chat.title or group_username,
                                member_count=member_count)
        await state.set_state(SellStates.waiting_creation_year)
        await db.update_user_stage(callback.from_user.id, 'waiting_creation_year')

        current_year = datetime.now().year
        years = list(range(2018, current_year + 1))
        year_buttons = []
        for i in range(0, len(years), 4):
            row = [InlineKeyboardButton(text=str(y), callback_data=f"year_{y}") for y in years[i:i+4]]
            year_buttons.append(row)

        keyboard = InlineKeyboardMarkup(inline_keyboard=year_buttons + [
            [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
        ])
        await callback.message.edit_text(lang_data['ask_creation_year'], reply_markup=keyboard)

    except TelegramForbiddenError:
        # Bot is banned or can’t access → keep in waiting_bot_admin
        await state.set_state(SellStates.waiting_bot_admin)
        await db.update_user_stage(callback.from_user.id, 'waiting_bot_admin')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=lang_data['bot_admin_added_again'], callback_data="check_admin")],
            [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
        ])
        await callback.message.edit_text(lang_data['forbidden_group'], reply_markup=keyboard)

    except TelegramBadRequest as e:
        # Don’t reset to waiting_group_link here — just re‑prompt
        await state.set_state(SellStates.waiting_bot_admin)
        await db.update_user_stage(callback.from_user.id, 'waiting_bot_admin')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=lang_data['bot_admin_added'], callback_data="check_admin")],
            [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
        ])
        await callback.message.edit_text(lang_data['not_admin_yet'], reply_markup=keyboard)

    except Exception as e:
        await callback.message.answer(lang_data['unexpected_error'])

# --- Receive Creation Year ---
@router.callback_query(F.data.startswith("year_"), SellStates.waiting_creation_year)
async def receive_creation_year(callback: CallbackQuery, state: FSMContext, db, lang_data: dict):
    await callback.answer()
    year = int(callback.data.split("_")[1])
    await state.update_data(created_year=year)

    if year == datetime.now().year - 1:
        await state.set_state(SellStates.waiting_creation_month)
        await db.update_user_stage(callback.from_user.id, 'waiting_creation_month')
        
        month_buttons = []
        months = list(range(1, 13))
        for i in range(0, len(months), 4):
            row = [
                InlineKeyboardButton(
                    text=lang_data.get(f"month_{m}", get_month_name(m, lang_data)), 
                    callback_data=f"month_{m}"
                ) for m in months[i:i+4]
            ]
            month_buttons.append(row)

        keyboard = InlineKeyboardMarkup(inline_keyboard=month_buttons + [
            [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
        ])

        await callback.message.edit_text(lang_data['ask_creation_month'], reply_markup=keyboard)
    else:
        await state.update_data(created_month=0)
        await proceed_to_analysis(callback, state, db, lang_data)


# --- Receive Creation Month ---
@router.callback_query(F.data.startswith("month_"), SellStates.waiting_creation_month)
async def receive_creation_month(callback: CallbackQuery, state: FSMContext, db, lang_data: dict):
    await callback.answer()
    month = int(callback.data.split("_")[1])
    await state.update_data(created_month=month)

    await proceed_to_analysis(callback, state, db, lang_data)


# --- Unified analysis step (replaces waiting_username) ---
async def proceed_to_analysis(callback_or_message, state: FSMContext, db, lang_data: dict):
    data = await state.get_data()
    created_year = data['created_year']
    created_month = data['created_month']

    price, status_type = calculate_price(created_year, created_month)

    seller_username = callback_or_message.from_user.username or str(callback_or_message.from_user.id)

    await state.update_data(seller_username=seller_username, price=price, status_type=status_type)

    month_name = get_month_name(created_month, lang_data)

    analysis_text = lang_data['group_analysis'].format(
        title=data['group_title'],
        members=data['member_count'],
        month=month_name,
        year=created_year,
        price=price
    )

    target = callback_or_message.message if isinstance(callback_or_message, CallbackQuery) else callback_or_message

    if status_type == 'not_valid':
        await target.answer(lang_data['group_not_valid_2024'])
        await state.clear()
        await db.update_user_stage(callback_or_message.from_user.id, None)
        return

    if status_type == 'manual_review':
        await target.answer(analysis_text)
        await target.answer(lang_data['group_manual_review'])
    else:
        await target.answer(analysis_text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_data['upload_screenshot_button'], callback_data="upload_screenshot")],
        [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell")]
    ])

    await target.answer(lang_data['transfer_instructions'], reply_markup=keyboard)

    await state.set_state(SellStates.waiting_screenshot)
    await db.update_user_stage(callback_or_message.from_user.id, 'waiting_screenshot')


@router.callback_query(F.data == "upload_screenshot")
async def prompt_screenshot(callback: CallbackQuery, lang_data: dict):
    await callback.answer()
    # Note: The transfer instructions were already sent, but this confirms the state.
    # We can just update the message to remind the user to upload the photo.
    await callback.message.edit_text(lang_data['upload_photo_prompt'], reply_markup=None)


@router.message(SellStates.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext, db, bot: Bot, lang_data: dict):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)

    # Use a generic image validation (assuming max size is ok, and file_id check is enough)
    # The validate_image function is usually used for local file validation, using file_id is simpler here.
    # if not validate_image(file.file_size, 'image/jpeg'):
    #     await message.answer(lang_data['screenshot_invalid'])
    #     return

    data = await state.get_data()

    # Create submission without payment details yet
    submission_id = await db.create_submission(
        message.from_user.id,
        {
            'group_link': data['group_link'],
            'group_username': data['group_username'],
            'group_title': data['group_title'],
            'member_count': data['member_count'],
            'created_year': data['created_year'],
            'created_month': data['created_month'],
            'price': data['price']
        }
    )

    await db.update_submission(submission_id, {
        'transfer_screenshot_file_id': photo.file_id,
        'status': 'manual_review' if data['status_type'] == 'manual_review' else 'pending'
    })

    await message.answer(lang_data['screenshot_received'])

    # --- Admin Notification Logic ---
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if admin_id:
        try:
            # Load admin's language pack
            admin_user = await db.get_user(admin_id)
            admin_lang_code = (admin_user.get("language") if admin_user else "en") or "en"
            from middlewares.language_loader import LanguageMiddleware
            middleware = LanguageMiddleware(db)
            admin_lang_data = middleware.languages.get(admin_lang_code, middleware.languages["en"])

            # Build a clickable group reference
            group_display = data["group_title"] or data["group_username"]
            print('here is the group link', data['group_link'])
            if data['group_link']:
                group_display = f"<a href='{data['group_link']}'>{group_display}</a>"
            elif data.get("group_username"):
                group_display = f"@{data['group_username']}"

            # Format admin card (you can still call format_admin_card if you want)
            card_text = (
                f"📌 Submission #{submission_id}\n"
                f"👤 Seller: @{message.from_user.username or message.from_user.id}\n"
                f"👥 Group: {group_display}\n"
                f"🔗 Group Link: {data['group_link']}\n"
                f"👥 Members: {data['member_count']}\n"
                f"📅 Created: {data['created_month']}/{data['created_year']}\n"
                f"💵 Price: {data['price']} ETB\n"
                f"📊 Status: {'manual_review' if data['status_type']=='manual_review' else 'pending'}"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=admin_lang_data["admin_view_screenshot"], callback_data=f"view_screenshot_{submission_id}")],
                [InlineKeyboardButton(text=admin_lang_data["admin_confirm_transfer"], callback_data=f"confirm_transfer_{submission_id}")],
                [InlineKeyboardButton(text=admin_lang_data["admin_reject"], callback_data=f"reject_{submission_id}")]
            ])

            await bot.send_photo(
                admin_id,
                photo=photo.file_id,
                caption=card_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error sending submission to admin: {e}")
            pass
            
    # Clear state after successful submission
    await message.answer(lang_data['submission_sent_admin'])
    await state.clear()
    await db.update_user_stage(message.from_user.id, None)

# ----------------------------------------------------------------------
#                         NEW PAYMENT HANDLERS
# ----------------------------------------------------------------------

@router.callback_query(F.data.startswith("use_saved_payment_"), SellStates.waiting_method_choice)
async def use_saved_payment(callback: CallbackQuery, state: FSMContext, db, bot: Bot, lang_data: dict):
    await callback.answer(lang_data['using_saved_details'])
    await callback.message.edit_reply_markup(reply_markup=None) # Remove keyboard

    user_id = callback.from_user.id
    data = await state.get_data()
    submission_id = data.get('active_submission_id')
    
    # Fetch user's saved payment details
    user = await db.get_user(user_id)
    payment_method = user.get('payment_method')
    payment_account = user.get('payment_account')
    price = data.get('price') or (await db.get_submission(submission_id)).get('price')
    
    # 1. Update the submission in the database with the saved details
    await db.update_submission(submission_id, {
        'payment_method': payment_method,
        'payment_account': payment_account,
        'status': 'ready_for_payment'
    })

    # 2. Inform the user
    await callback.message.answer(lang_data['payment_info_received_saved'].format(
        method=payment_method, account=payment_account
    ))
  # 3. Notify the admin
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if admin_id:
        try:
            # Load admin's language pack
            admin_user = await db.get_user(admin_id)
            admin_lang_code = (admin_user.get("language") if admin_user else "en") or "en"

            from middlewares.language_loader import LanguageMiddleware
            middleware = LanguageMiddleware(db)
            admin_lang_data = middleware.languages.get(admin_lang_code, middleware.languages["en"])

            notification_text = admin_lang_data["admin_payment_notification"].format(
                id=submission_id,
                username=callback.from_user.username or str(callback.from_user.id),
                price=price,
                method=payment_method,
                account=payment_account,
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=admin_lang_data["admin_mark_as_paid"],
                    callback_data=f"mark_paid_{submission_id}"
                )]
            ])
            await bot.send_message(admin_id, notification_text, reply_markup=keyboard)

        except Exception as e:
            print(f"Error notifying admin after saved payment: {e}")
            pass

    # 4. Clear the state
    await state.clear()
    await db.update_user_stage(user_id, None)



@router.callback_query(F.data == "change_payment_details", SellStates.waiting_method_choice)
async def start_change_payment_details(callback: CallbackQuery, state: FSMContext, db, lang_data: dict):
    await callback.answer()
    
    # Move to the first text input state
    await state.set_state(SellStates.waiting_new_method)
    await db.update_user_stage(callback.from_user.id, 'waiting_new_method')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell_process")]
    ])

    await callback.message.edit_text(
        lang_data['ask_payment_method'],
        reply_markup=keyboard
    )


@router.message(SellStates.waiting_new_method)
async def receive_payment_method(message: Message, state: FSMContext, db, lang_data: dict):
    payment_method = message.text
    
    # Save method to FSM context
    await state.update_data(new_payment_method=payment_method)
    
    # Move to the next input state
    await state.set_state(SellStates.waiting_new_account)
    await db.update_user_stage(message.from_user.id, 'waiting_new_account')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_data['cancel_button'], callback_data="cancel_sell_process")]
    ])
    
    await message.answer(
        lang_data['ask_payment_account'],
        reply_markup=keyboard
    )


@router.message(SellStates.waiting_new_account)
async def receive_payment_account(message: Message, state: FSMContext, db, bot: Bot, lang_data: dict):
    payment_account = message.text
    user_id = message.from_user.id
    
    data = await state.get_data()
    submission_id = data.get('active_submission_id')
    payment_method = data.get('new_payment_method')

    if not submission_id or not payment_method:
        await message.answer(lang_data['error_occurred_no_data'])
        await state.clear()
        return

    # 1. Save new details to the user's profile for REUSE
    await db.update_user_payment(user_id, payment_method, payment_account)

    # 2. Update the submission with the new payment info and status
    await db.update_submission(submission_id, {
        'payment_method': payment_method,
        'payment_account': payment_account,
        'status': 'ready_for_payment'
    })
    
    # Retrieve price for notification
    submission = await db.get_submission(submission_id)
    price = submission.get('price', 'N/A')

    # 3. Inform the user
    await message.answer(lang_data['payment_info_received'])
    
    # 4. Notify the admin with inline button
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if admin_id:
        try:
            # Load admin's language pack
            admin_user = await db.get_user(admin_id)
            admin_lang_code = (admin_user.get("language") if admin_user else "en") or "en"

            from middlewares.language_loader import LanguageMiddleware
            middleware = LanguageMiddleware(db)
            admin_lang_data = middleware.languages.get(admin_lang_code, middleware.languages["en"])

            notification_text = admin_lang_data["admin_payment_notification"].format(
                id=submission_id,
                username=message.from_user.username or str(user_id),
                price=price,
                method=payment_method,
                account=payment_account,
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=admin_lang_data["admin_mark_as_paid"],
                    callback_data=f"mark_paid_{submission_id}"
                )]
            ])

            await bot.send_message(admin_id, notification_text, reply_markup=keyboard)

        except Exception as e:
            print(f"Error notifying admin after new payment: {e}")
            pass

    # 5. Clear the state
    await state.clear()
    await db.update_user_stage(user_id, None)


# ----------------------------------------------------------------------
#                       CANCEL HANDLERS
# ----------------------------------------------------------------------
@router.callback_query(F.data.in_(["cancel_sell", "cancel_sell_process"]))
async def cancel_sell(callback: CallbackQuery, state: FSMContext, db, lang_data: dict):
    # This handler now clears the state for both the initial flow ("cancel_sell")
    # and the specific payment flow ("cancel_sell_process").
    
    await state.clear()
    await db.update_user_stage(callback.from_user.id, None)
    await callback.answer(lang_data['process_cancelled'], show_alert=True)
    
    # Check if the message is the initial one that needs to be deleted/edited
    if callback.message.text:
        await callback.message.edit_text(lang_data['main_menu_return'], reply_markup=None)
    else:
        # If the message is a complex one (e.g., photo caption), just send a new message.
        await callback.message.answer(lang_data['main_menu_return'])

@router.message(Command("mysubmissions"))
@router.message(F.text.in_(['📤 My Submissions', '📤 ማስረከቢያዎቼ']))
async def my_submissions(message: Message, db, lang_data: dict):
    # Fetch last 10 submissions for this user
    submissions = await db.get_user_submissions(message.from_user.id, 10)

    if not submissions:
        await message.answer(lang_data['no_submissions'])
        return

    await message.answer(lang_data['submissions_list'])

    for sub in submissions:
        status_key = f"status_{sub['status']}"
        status_text = lang_data.get(status_key, sub['status'])
        date_str = sub['created_at'][:10] if sub['created_at'] else 'N/A'
        payment_info = f"{sub.get('payment_method', 'N/A')}: {sub.get('payment_account', 'N/A')}"

        caption = lang_data['submission_item'].format(
            id=sub['id'],
            title=sub['group_title'] or 'N/A',
            status=status_text,
            price=sub['price'],
            date=date_str,
            payment_info=payment_info
        )

        # Prefer sending with screenshot if available
        if sub.get('transfer_screenshot_file_id'):
            try:
                await message.answer_photo(
                    photo=sub['transfer_screenshot_file_id'],
                    caption=caption
                )
            except Exception:
                # fallback if file_id is invalid
                await message.answer(caption)
        else:
            await message.answer(caption)

        # If admin uploaded a confirmation screenshot, show it too
        if sub.get('admin_payment_screenshot'):
            try:
                await message.answer_photo(
                    photo=sub['admin_payment_screenshot'],
                    caption=lang_data.get('admin_proof_caption', '✅ Admin confirmation')
                )
            except Exception:
                await message.answer(lang_data.get('admin_proof_caption', '✅ Admin confirmation'))
