from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, date
from database.session import get_session
from database.models import Birthday

router = Router()


class BirthdayStates(StatesGroup):
    add_birthday = State()


@router.message(F.text == "/add_birthday")
async def cmd_add_birthday(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_birthday")
    keyboard.adjust(1)

    await message.answer(
        "Введите день рождения в формате:\n"
        "Имя - ДД.ММ\n\n"
        "Пример: Иван - 15.05",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(BirthdayStates.add_birthday)


@router.callback_query(F.data == "cancel_add_birthday")
async def cancel_add_birthday(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Добавление дня рождения отменено")
    await callback.answer()


@router.message(BirthdayStates.add_birthday)
async def process_add_birthday(message: types.Message, state: FSMContext):
    try:
        # Parse format: "Имя - ДД.ММ"
        parts = message.text.split(' - ')
        if len(parts) < 2:
            await message.answer(
                "Неверный формат. Используйте: Имя - ДД.ММ\n\n"
                "Пример: Иван - 15.05"
            )
            return
        
        name = parts[0].strip()
        date_str = parts[1].strip()
        
        # Parse date
        day, month = map(int, date_str.split('.'))
        birthday_date = date(datetime.now().year, month, day)
        
        async with get_session() as session:
            birthday = Birthday(
                name=name,
                date=birthday_date
            )
            session.add(birthday)
            await session.commit()
        
        await message.answer(f"✅ День рождения добавлен: {name} ({birthday_date.strftime('%d.%m')})")
        await state.clear()
    except (ValueError, IndexError):
        await message.answer(
            "Неверный формат. Используйте: Имя - ДД.ММ\n\n"
            "Пример: Иван - 15.05"
        )


@router.message(F.text == "/birthdays")
async def cmd_birthdays(message: types.Message):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Birthday).order_by(Birthday.date))
        birthdays = result.scalars().all()
    
    if not birthdays:
        await message.answer("Список дней рождения пуст")
        return
    
    text = "📅 Дни рождения:\n\n"
    for b in birthdays:
        text += f"🎂 {b.name} - {b.date.strftime('%d.%m')}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/upcoming_birthdays")
async def cmd_upcoming_birthdays(message: types.Message):
    today = date.today()
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Birthday).order_by(Birthday.date))
        birthdays = result.scalars().all()

    # Find birthdays in next 30 days
    upcoming = []
    for b in birthdays:
        birthday_this_year = date(today.year, b.date.month, b.date.day)
        if birthday_this_year < today:
            birthday_this_year = date(today.year + 1, b.date.month, b.date.day)

        days_until = (birthday_this_year - today).days
        if 0 <= days_until <= 30:
            upcoming.append((b, days_until))

    upcoming.sort(key=lambda x: x[1])

    if not upcoming:
        await message.answer("Ближайших дней рождения нет (в ближайшие 30 дней)")
        return

    text = "📅 Ближайшие дни рождения:\n\n"
    for b, days in upcoming:
        if days == 0:
            text += f"🎉 {b.name} - СЕГОДНЯ!\n"
        elif days == 1:
            text += f"🎂 {b.name} - Завтра\n"
        else:
            text += f"📅 {b.name} - через {days} дней\n"

    await message.answer(text)
