from aiogram import Router, F
from aiogram.types import Message
from config import settings

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я личный бот для обзоров и напоминалок.\n\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/menu - Главное меню\n"
        "/help - Справка",
        parse_mode="HTML"
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "📖 Справка по боту\n\n"
        "Бот предназначен для двух администраторов.\n"
        "Основные функции:\n"
        "• Публикация обзоров в канал по расписанию\n"
        "• Напоминания о днях рождения\n"
        "• Управление делами\n"
        "• Напоминания о таблетках\n\n"
        "Все функции доступны через главное меню: /menu",
        parse_mode="HTML"
    )
