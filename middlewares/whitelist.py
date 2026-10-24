from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import settings
import logging

logger = logging.getLogger(__name__)


class WhitelistMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            admin_ids = settings.get_admin_ids()

            if user_id not in admin_ids:
                logger.warning(f"Access denied for user {user_id}")
                if isinstance(event, Message):
                    await event.answer("⛔ Доступ запрещён")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ Доступ запрещён", show_alert=True)
                return

        return await handler(event, data)
