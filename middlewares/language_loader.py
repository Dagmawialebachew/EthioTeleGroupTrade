from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
import json
import os


class LanguageMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.db = db
        self.languages = {}
        self.load_languages()

    def load_languages(self):
        lang_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lang')
        for lang_file in ['lang_en.json', 'lang_am.json']:
            lang_code = lang_file.split('_')[1].split('.')[0]
            with open(os.path.join(lang_dir, lang_file), 'r', encoding='utf-8') as f:
                self.languages[lang_code] = json.load(f)

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        user = await self.db.get_user(user_id)

        lang_code = 'en'
        if user and user.get('language'):
            lang_code = user['language']

        data['lang_data'] = self.languages.get(lang_code, self.languages['en'])
        data['lang_code'] = lang_code

        return await handler(event, data)
