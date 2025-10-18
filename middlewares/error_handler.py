from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ErrorEvent
from typing import Callable, Dict, Any, Awaitable
import logging
import traceback
import os


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    def __init__(self, bot, log_channel_id: int = None):
        self.bot = bot
        self.log_channel_id = log_channel_id

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error handling update: {e}", exc_info=True)

            error_msg = f"Error: {str(e)}\n\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"

            if self.log_channel_id:
                try:
                    user_info = f"User: {event.from_user.id}"
                    if event.from_user.username:
                        user_info += f" (@{event.from_user.username})"

                    await self.bot.send_message(
                        self.log_channel_id,
                        f"⚠️ Error occurred:\n\n{user_info}\n\n{error_msg[:3000]}"
                    )
                except Exception as log_error:
                    logger.error(f"Failed to log error to channel: {log_error}")

            lang_data = data.get('lang_data', {})
            error_response = lang_data.get('error_occurred', 'An error occurred. Please try again.')

            try:
                if isinstance(event, Message):
                    await event.answer(error_response)
                elif isinstance(event, CallbackQuery):
                    await event.answer(error_response, show_alert=True)
            except Exception:
                pass
