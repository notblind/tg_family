from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, date
from database.session import get_session
from database.models import Birthday, BirthdayCategory
from config import settings

router = Router()


class BirthdayStates(StatesGroup):
    name = State()
    date = State()
    category = State()
    note = State()


@router.message(F.text == "/add_birthday")
async def cmd_add_birthday(message: types.Message, state: FSMContext):
    await message.answer("Введите имя человека:")
    await state.set_state(BirthdayStates.name)


@router.message(BirthdayStates.name)
async def process_birthday_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите дату рождения в формате ДД.ММ (например, 15.05):")
    await state.set_state(BirthdayStates.date)


@router.message(BirthdayStates.date)
async def process_birthday_date(message: types.Message, state: FSMContext):
    try:
        day, month = map(int, message.text.split('.'))
        birthday_date = date(datetime.now().year, month, day)
        await state.update_data(date=birthday_date)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Семья", callback_data="category_family")
        keyboard.button(text="Друзья", callback_data="category_friends")
        await message.answer("Выберите категорию:", reply_markup=keyboard.as_markup())
        await state.set_state(BirthdayStates.category)
    except (ValueError, IndexError):
        await message.answer("Неверный формат даты. Используйте ДД.ММ (например, 15.05):")


@router.callback_query(BirthdayStates.category, F.data.startswith("category_"))
async def process_birthday_category(callback: types.CallbackQuery, state: FSMContext):
    category = "family" if callback.data == "category_family" else "friends"
    await state.update_data(category=category)
    await callback.message.answer("Добавьте заметку (или отправьте /skip для пропуска):")
    await state.set_state(BirthdayStates.note)
    await callback.answer()


@router.message(BirthdayStates.note)
async def process_birthday_note(message: types.Message, state: FSMContext):
    if message.text == "/skip":
        note = None
    else:
        note = message.text
    
    await state.update_data(note=note)
    data = await state.get_data()
    
    async with get_session() as session:
        birthday = Birthday(
            name=data['name'],
            date=data['date'],
            category=BirthdayCategory(data['category']),
            note=note
        )
        session.add(birthday)
        await session.commit()
    
    await message.answer(f"✅ День рождения добавлен: {data['name']} ({data['date'].strftime('%d.%m')})")
    await state.clear()


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
        category_emoji = "👨‍👩‍👧‍👦" if b.category == BirthdayCategory.FAMILY else "👥"
        text += f"{category_emoji} {b.name} - {b.date.strftime('%d.%m')}"
        if b.note:
            text += f" ({b.note})"
        text += "\n"
    
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
