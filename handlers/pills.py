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
    add_pill = State()


@router.message(F.text == "/add_pill")
async def cmd_add_pill(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_pill")
    keyboard.adjust(1)

    await message.answer(
        "Введите напоминание в формате:\n"
        "Название - ЧЧ:ММ\n"
        "или\n"
        "Название - ЧЧ:ММ - Дни недели\n\n"
        "Примеры:\n"
        "Витамин C - 09:00 (ежедневно)\n"
        "Витамин C - 09:00 - Пн Вт Ср Чт Пт (рабочие дни)\n\n"
        "Дни недели: Пн Вт Ср Чт Пт Сб Вс (через пробел)",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(PillStates.add_pill)


@router.callback_query(F.data == "cancel_add_pill")
async def cancel_add_pill(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Добавление напоминания отменено")
    await callback.answer()


@router.message(PillStates.add_pill)
async def process_add_pill(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split(' - ')
        if len(parts) < 2:
            await message.answer(
                "Неверный формат. Используйте: Название - ЧЧ:ММ\n"
                "или Название - ЧЧ:ММ - Дни недели\n\n"
                "Примеры:\n"
                "Витамин C - 09:00 (ежедневно)\n"
                "Витамин C - 09:00 - Пн Вт Ср Чт Пт (рабочие дни)"
            )
            return

        name = parts[0].strip()
        time_str = parts[1].strip()

        # Parse time
        datetime.strptime(time_str, "%H:%M")

        # Parse days (optional)
        day_map = {
            "Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3, "Пт": 4, "Сб": 5, "Вс": 6
        }
        days_of_week = []

        if len(parts) >= 3:
            days_str = parts[2].strip()
            days_input = days_str.split()

            for day in days_input:
                if day in day_map:
                    days_of_week.append(day_map[day])

        # If no days specified, assume daily (all days)
        if not days_of_week:
            days_of_week = [0, 1, 2, 3, 4, 5, 6]  # All days

        async with get_session() as session:
            pill = Pill(
                name=name,
                reminder_time=time_str,
                days_of_week=json.dumps(days_of_week),
                is_indefinite=True
            )
            session.add(pill)
            await session.commit()

        days_count = len(days_of_week)
        if days_count == 7:
            days_text = "ежедневно"
        else:
            days_text = f"{days_count} дн. в неделю"

        await message.answer(f"✅ Напоминание добавлено: {name} в {time_str} ({days_text})")
        await state.clear()
    except ValueError:
        await message.answer(
            "Неверный формат времени. Используйте ЧЧ:ММ (например, 09:00)"
        )
    except Exception as e:
        await message.answer(
            "Неверный формат. Используйте: Название - ЧЧ:ММ\n"
            "или Название - ЧЧ:ММ - Дни недели\n\n"
            "Примеры:\n"
            "Витамин C - 09:00 (ежедневно)\n"
            "Витамин C - 09:00 - Пн Вт Ср Чт Пт (рабочие дни)"
        )


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


@router.callback_query(F.data.startswith("pill_taken_"))
async def callback_pill_taken(callback: types.CallbackQuery):
    pill_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Pill).where(Pill.id == pill_id))
        pill = result.scalar_one_or_none()
        
        if pill:
            log = PillLog(pill_id=pill_id, is_taken=True)
            session.add(log)
            await session.commit()
            await callback.message.edit_text(f"✅ Записано: {pill.name} принят")
        else:
            await callback.message.edit_text("Ошибка: напоминание не найдено")
    
    await callback.answer()


@router.callback_query(F.data.startswith("pill_postpone_"))
async def callback_pill_postpone(callback: types.CallbackQuery):
    pill_id = int(callback.data.split("_")[2])
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Pill).where(Pill.id == pill_id))
        pill = result.scalar_one_or_none()
        
        if pill:
            from config import settings
            interval = settings.pill_reminder_interval
            
            # Schedule reminder after interval
            from scheduler.scheduler import scheduler
            from scheduler.jobs import check_pill_reminders
            from datetime import datetime, timedelta
            
            reminder_time = (datetime.now() + timedelta(minutes=interval)).strftime("%H:%M")
            
            scheduler.add_job(
                check_pill_reminders,
                'date',
                run_date=datetime.now() + timedelta(minutes=interval),
                id=f"pill_postpone_{pill_id}_{datetime.now().timestamp()}",
                replace_existing=True
            )
            
            await callback.message.edit_text(
                f"⏰ Напоминание отложено на {interval} минут ({reminder_time})"
            )
        else:
            await callback.message.edit_text("Ошибка: напоминание не найдено")
    
    await callback.answer()
