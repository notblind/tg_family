from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from database.session import get_session
from database.models import Pill, PillLog
import json

router = Router()


class PillStates(StatesGroup):
    name = State()
    reminder_time = State()
    days_of_week = State()
    duration = State()
    end_date = State()


@router.message(F.text == "/add_pill")
async def cmd_add_pill(message: types.Message, state: FSMContext):
    await message.answer("Введите название лекарства:")
    await state.set_state(PillStates.name)


@router.message(PillStates.name)
async def process_pill_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите время приёма в формате ЧЧ:ММ (например, 09:00):")
    await state.set_state(PillStates.reminder_time)


@router.message(PillStates.reminder_time)
async def process_pill_reminder_time(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
        await state.update_data(reminder_time=message.text)
        
        keyboard = InlineKeyboardBuilder()
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, day in enumerate(days):
            keyboard.button(text=day, callback_data=f"day_{i}")
        keyboard.button(text="Готово", callback_data="days_done")
        keyboard.adjust(4)
        
        await message.answer(
            "Выберите дни недели для приёма (можно выбрать несколько, затем нажмите 'Готово'):",
            reply_markup=keyboard.as_markup()
        )
        await state.set_state(PillStates.days_of_week)
    except ValueError:
        await message.answer("Неверный формат времени. Используйте ЧЧ:ММ (например, 09:00):")


@router.callback_query(PillStates.days_of_week, F.data.startswith("day_"))
async def process_pill_day(callback: types.CallbackQuery, state: FSMContext):
    day_index = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected_days = data.get("selected_days", [])
    
    if day_index in selected_days:
        selected_days.remove(day_index)
    else:
        selected_days.append(day_index)
    
    await state.update_data(selected_days=selected_days)
    await callback.answer()


@router.callback_query(PillStates.days_of_week, F.data == "days_done")
async def process_pill_days_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_days = data.get("selected_days", [])
    
    if not selected_days:
        await callback.message.answer("Выберите хотя бы один день недели")
        await callback.answer()
        return
    
    await state.update_data(days_of_week=json.dumps(selected_days))
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Бессрочно", callback_data="duration_indefinite")
    keyboard.button(text="Указать дату окончания", callback_data="duration_limited")
    
    await callback.message.answer("Выберите длительность курса:", reply_markup=keyboard.as_markup())
    await state.set_state(PillStates.duration)
    await callback.answer()


@router.callback_query(PillStates.duration, F.data == "duration_indefinite")
async def process_pill_duration_indefinite(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(is_indefinite=True, end_date=None)
    data = await state.get_data()
    
    async with get_session() as session:
        pill = Pill(
            name=data['name'],
            reminder_time=data['reminder_time'],
            days_of_week=data['days_of_week'],
            is_indefinite=True
        )
        session.add(pill)
        await session.commit()
    
    days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
    selected_days_names = [days_map[i] for i in json.loads(data['days_of_week'])]
    
    await callback.message.answer(
        f"✅ Напоминание добавлено: {data['name']} в {data['reminder_time']}\n"
        f"Дни: {', '.join(selected_days_names)}\n"
        f"Бессрочно"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(PillStates.duration, F.data == "duration_limited")
async def process_pill_duration_limited(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(is_indefinite=False)
    await callback.message.answer("Введите дату окончания в формате ДД.ММ.ГГГГ (например, 25.12.2026):")
    await state.set_state(PillStates.end_date)
    await callback.answer()


@router.message(PillStates.end_date)
async def process_pill_end_date(message: types.Message, state: FSMContext):
    try:
        end_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        await state.update_data(end_date=end_date)
        data = await state.get_data()
        
        async with get_session() as session:
            pill = Pill(
                name=data['name'],
                reminder_time=data['reminder_time'],
                days_of_week=data['days_of_week'],
                is_indefinite=False,
                end_date=end_date
            )
            session.add(pill)
            await session.commit()
        
        days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
        selected_days_names = [days_map[i] for i in json.loads(data['days_of_week'])]
        
        await message.answer(
            f"✅ Напоминание добавлено: {data['name']} в {data['reminder_time']}\n"
            f"Дни: {', '.join(selected_days_names)}\n"
            f"До {end_date.strftime('%d.%m.%Y')}"
        )
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ (например, 25.12.2026):")


@router.message(F.text == "/pills")
async def cmd_pills(message: types.Message):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Pill).order_by(Pill.reminder_time))
        pills = result.scalars().all()
    
    if not pills:
        await message.answer("Список напоминаний о таблетках пуст")
        return
    
    text = "💊 Напоминания о таблетках:\n\n"
    days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
    
    for pill in pills:
        selected_days_names = [days_map[i] for i in json.loads(pill.days_of_week)]
        duration = "Бессрочно" if pill.is_indefinite else f"До {pill.end_date.strftime('%d.%m.%Y')}"
        text += f"💊 {pill.name} в {pill.reminder_time}\n"
        text += f"   Дни: {', '.join(selected_days_names)}\n"
        text += f"   {duration}\n\n"
    
    await message.answer(text)


@router.message(F.text == "/pill_log")
async def cmd_pill_log(message: types.Message):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(PillLog).order_by(PillLog.taken_at.desc()).limit(20)
        )
        logs = result.scalars().all()
    
    if not logs:
        await message.answer("Журнал приёмов пуст")
        return
    
    text = "📋 Журнал приёмов таблеток (последние 20 записей):\n\n"
    
    for log in logs:
        status = "✅ Принято" if log.is_taken else "❌ Не принято"
        text += f"{status} {log.pill.name} - {log.taken_at.strftime('%d.%m %H:%M')}\n"
    
    await message.answer(text)
